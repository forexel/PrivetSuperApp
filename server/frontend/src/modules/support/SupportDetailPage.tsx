import { useParams, useNavigate } from 'react-router-dom'
import { createPortal } from 'react-dom'
import { useEffect, useMemo, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../shared/api'
import ClipIcon from '../../assets/icons/clip.svg?react'
import '../../styles/tickets.css'
import '../../styles/forms.css'

type SupportTicketOut = {
  id: string;
  user_id: string;
  subject: string;
  status: 'open' | 'in_progress' | 'closed' | 'rejected' | 'new' | 'pending' | 'completed' | 'reject';
  created_at: string;
};

type SupportMessageOut = {
  id: string;
  ticket_id: string;
  author: 'user' | 'support';
  body: string | null;
  file_url?: string | null;
  created_at: string;
};

export default function SupportDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [body, setBody] = useState('')
  const [err, setErr] = useState('')
  const [attachBusy, setAttachBusy] = useState(false)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)

  // Все хуки — без условий, порядок стабилен
  const ticketQ = useQuery({
    queryKey: ['support', id],
    enabled: !!id,
    queryFn: () => api.get<SupportTicketOut>(`/support/${id}`),
    retry: false,
  })

  const msgsQ = useQuery({
    queryKey: ['support', id, 'messages'],
    enabled: !!id,
    queryFn: () => api.get<SupportMessageOut[]>(`/support/${id}/messages`),
    retry: false,
  })

  const t = ticketQ.data as SupportTicketOut | undefined
  const messages = msgsQ.data ?? []

  const ui = useMemo(() => {
    const toUiStatus = (raw: SupportTicketOut['status']): 'new'|'in_progress'|'completed'|'reject' => {
      switch (raw) {
        case 'open': return 'new'
        case 'pending': return 'in_progress'
        case 'closed': return 'completed'
        case 'rejected': return 'reject'
        default: return (raw as any)
      }
    }
    const labels: Record<'new'|'in_progress'|'completed'|'reject', string> = {
      new: 'New', in_progress: 'In progress', completed: 'Done', reject: 'Rejected'
    }
    return { toUiStatus, labels }
  }, [])

  const sendMutation = useMutation({
    mutationFn: async (payload?: { body?: string; file_key?: string }) => {
      setErr('')
      await api.post(`/support/${id}/messages/user`, payload ?? { body })
    },
    onSuccess: () => {
      setBody('')
      qc.invalidateQueries({ queryKey: ['support', id, 'messages'] })
    },
    onError: () => setErr('Не удалось отправить сообщение')
  })
  const uploadPhoto = async (file: File) => {
    const form = new FormData()
    form.append('file', file, file.name)
    const send = async (token?: string | null) => {
      return fetch('/api/v1/uploads/direct', {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        body: form,
      })
    }
    let token = localStorage.getItem('access_token')
    let res: Response
    try {
      res = await send(token)
    } catch (error) {
      setErr(typeof navigator !== 'undefined' && !navigator.onLine
        ? 'Нет соединения с интернетом'
        : 'Не удалось загрузить файл')
      throw error
    }
    if (res.status === 401) {
      const refresh = localStorage.getItem('refresh_token')
      if (refresh) {
        const refreshRes = await fetch('/api/v1/auth/refresh', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refresh }),
        })
        if (refreshRes.ok) {
          const data = await refreshRes.json()
          if (data?.access_token) {
            localStorage.setItem('access_token', data.access_token)
            if (data?.refresh_token) localStorage.setItem('refresh_token', data.refresh_token)
            token = data.access_token
            try {
              res = await send(token)
            } catch (error) {
              setErr(typeof navigator !== 'undefined' && !navigator.onLine
                ? 'Нет соединения с интернетом'
                : 'Не удалось загрузить файл')
              throw error
            }
          }
        }
      }
    }
    if (!res.ok) {
      setErr('Не удалось загрузить файл')
      throw new Error('upload failed')
    }
    const json = await res.json()
    return json.file_key as string
  }
  const sendAttachment = async (file: File) => {
    setAttachBusy(true)
    try {
      const key = await uploadPhoto(file)
      await sendMutation.mutateAsync({ file_key: key })
    } catch {
      setErr((prev) => prev || 'Не удалось отправить сообщение')
    } finally {
      setAttachBusy(false)
    }
  }

  // Auto-grow textarea (1–4 lines) + button height sync
  const taRef = useRef<HTMLTextAreaElement | null>(null)
  const pageRef = useRef<HTMLDivElement | null>(null)
  const inputWrapRef = useRef<HTMLDivElement | null>(null)
  const [taH, setTaH] = useState<number>(40)
  const measureChat = () => {
    const h = inputWrapRef.current?.offsetHeight ?? 0
    // прокинем паддинг под фиксированный инпут
    if (pageRef.current) pageRef.current.style.setProperty('--chat-pad', h + 'px')
  }
  const autoSize = () => {
    const el = taRef.current
    if (!el) return
    el.style.height = 'auto'
    const maxH = Math.max(Math.floor(window.innerHeight * 0.4), 120) // до 40% высоты
    const next = Math.min(Math.max(el.scrollHeight, 40), maxH)
    el.style.height = next + 'px'
    setTaH(next)
    measureChat()
  }
  useEffect(() => { autoSize(); measureChat() }, [])
  useEffect(() => { autoSize() }, [body])
  useEffect(() => {
    const onResize = () => { measureChat() }
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])

  // Прокрутка к последнему сообщению
  const listEndRef = useRef<HTMLDivElement | null>(null)
  const scrollToEnd = () => {
    // 1) попробуем классическим способом
    listEndRef.current?.scrollIntoView({ block: 'end', behavior: 'auto' })
    // 2) если родительский скролл — это .app-content, дёрнем его явно
    const scroller = document.querySelector('.app-content') as HTMLElement | null
    if (scroller) scroller.scrollTo({ top: scroller.scrollHeight, behavior: 'auto' })
  }
  useEffect(() => {
    // даём макету дорендериться (авто-рост textarea/измерение paddings)
    const id = setTimeout(scrollToEnd, 0)
    return () => clearTimeout(id)
  }, [messages.length])

  useEffect(() => {
    const scroller = document.querySelector('.app-content') as HTMLElement | null
    scroller?.classList.add('app-content--no-scroll')
    return () => scroller?.classList.remove('app-content--no-scroll')
  }, [])

  useEffect(() => {
    if (!id || messages.length === 0) return
    const last = messages[messages.length - 1]?.created_at
    if (!last) return
    try {
      localStorage.setItem(`support_last_read_${id}`, last)
    } catch {}
    qc.invalidateQueries({ queryKey: ['support', 'unread'] })
  }, [id, messages])

  // Отрисовываем понятные состояния без риска нарушить порядок хуков
  if (!id || ticketQ.isLoading) {
    return <div className="page-white"><div className="dashboard"><p>Загрузка…</p></div></div>
  }
  if (ticketQ.isError || !t) {
    return (
      <div className="page-white">
        <div className="dashboard">
          <p>Не удалось загрузить обращение.</p>
          <button className="btn btn-primary" onClick={() => navigate(-1)}>Назад</button>
        </div>
      </div>
    )
  }

  const statusKey = ui.toUiStatus(t.status)

  return (
    <div className="page-white">
      <div ref={pageRef} className="ticket-detail page-content chat-page">
        <div className="page-header">
          <button className="back-btn" aria-label="Назад" onClick={() => navigate('/support')}>
            ←
          </button>
          <h2 className="page-title">Обращение</h2>
        </div>

        <div className="detail-title-row" style={{ marginTop: 4 }}>
          <div className="detail-title">{t.subject}</div>
          <span className={`status-badge status-${statusKey}`}>{ui.labels[statusKey]}</span>
        </div>
        <div className="detail-updated">создано {new Date(t.created_at).toLocaleString('ru-RU')}</div>

        <div className="detail-section detail-section--messages">
          <div className="detail-section-title">Сообщения</div>
          <div className="chat-scroll">
            {msgsQ.isLoading && <div className="detail-desc">Загрузка…</div>}
            {!msgsQ.isLoading && messages.length === 0 && (
              <div className="detail-desc">Пока нет сообщений</div>
            )}
            {!msgsQ.isLoading && messages.length > 0 && (
              <>
                <div className="chat">
                  {messages.map((m) => {
                    const isMine = m.author === 'user'
                    const who = isMine ? 'Вы' : 'Поддержка'
                    return (
                      <div key={m.id} className={`msg ${isMine ? 'msg--mine' : 'msg--their'}`}>
                        <div className="meta">
                          <span className="history-date">{new Date(m.created_at).toLocaleString('ru-RU')}</span>
                          {' · '}{who}
                        </div>
                        <div className="bubble">
                          {m.body ? <div className="bubble-text">{m.body}</div> : null}
                          {m.file_url ? (
                            <img
                              className="bubble-image"
                              src={m.file_url}
                              alt="Вложение"
                              onClick={() => setPreviewUrl(m.file_url || null)}
                              role="button"
                            />
                          ) : null}
                        </div>
                      </div>
                    )
                  })}
                </div>
                <div ref={listEndRef} />
              </>
            )}
          </div>
        </div>

        {/* Фиксированный низ */}
      </div>
      {createPortal(
        <div ref={inputWrapRef} className="chat-input-fixed">
          <div className="chat-input">
            {err && <div className="error" role="alert">{err}</div>}
            <label className="chat-attach">
              <input
                type="file"
                accept="image/*"
                onChange={(e) => {
                  const file = e.target.files?.[0]
                  if (file) sendAttachment(file)
                  e.target.value = ''
                }}
                disabled={attachBusy}
              />
              <ClipIcon />
            </label>
            <div className="input-wrap">
              <div className={`input-placeholder${body.trim().length > 0 ? ' is-hidden' : ''}`}>
                Напишите сообщение...
              </div>
              <textarea
                ref={taRef}
                className="input input-area auto-grow"
                rows={1}
                aria-label="Сообщение"
                value={body}
                onChange={(e) => setBody(e.target.value)}
                onInput={autoSize}
                style={{ height: taH, overflow: 'hidden' }}
              />
            </div>
            <button
              className="btn-send"
              style={{ height: taH, width: taH }}
              aria-label="Отправить"
              disabled={sendMutation.isPending || !body.trim()}
              onClick={() => sendMutation.mutate({ body })}
            >
              ↑
            </button>
          </div>
        </div>,
        document.body
      )}
      {previewUrl ? (
        <div className="image-preview" onClick={() => setPreviewUrl(null)} role="presentation">
          <img src={previewUrl} alt="Фото" />
        </div>
      ) : null}
    </div>
  )
}
