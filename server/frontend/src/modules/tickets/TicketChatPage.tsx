import { createPortal } from 'react-dom'
import { useEffect, useMemo, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../../shared/api'
import ClipIcon from '../../assets/icons/clip.svg?react'
import '../../styles/tickets.css'

type TicketDetail = {
  id: string
  title: string
  created_at: string
  status: 'new' | 'in_progress' | 'completed' | 'reject'
  master_name?: string | null
}

type Message = {
  id: string
  author: 'user' | 'master'
  body: string | null
  file_url: string | null
  created_at: string
}

function formatDateTime(value: string) {
  return new Date(value).toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

function getShortId(id?: string | null) {
  if (!id) return ''
  const hex = id.replace(/-/g, '')
  let hash = 0
  for (let i = 0; i < hex.length; i += 1) {
    hash = (hash * 31 + hex.charCodeAt(i)) >>> 0
  }
  const num = (hash % 9000000) + 1000000
  return String(num)
}

export default function TicketChatPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [text, setText] = useState('')
  const [err, setErr] = useState('')
  const [attachBusy, setAttachBusy] = useState(false)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)

  const ticketQ = useQuery({
    queryKey: ['ticket', id],
    enabled: !!id,
    queryFn: () => api.get<TicketDetail>(`/tickets/${id}`),
    retry: false,
  })

  const messagesQ = useQuery({
    queryKey: ['ticket', id, 'messages'],
    enabled: !!id,
    queryFn: () => api.get<Message[]>(`/tickets/${id}/messages`),
    retry: false,
  })

  const detail = ticketQ.data
  const messages = messagesQ.data ?? []
  const otherName = detail?.master_name || 'Мастер'
  const canSend = detail?.status === 'in_progress'

  const sendMutation = useMutation({
    mutationFn: (payload: { body?: string; file_key?: string }) =>
      api.post<Message>(`/tickets/${id}/messages`, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['ticket', id, 'messages'] })
    },
    onError: () => setErr('Не удалось отправить сообщение'),
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

  const sendText = async () => {
    if (!text.trim()) return
    setErr('')
    await sendMutation.mutateAsync({ body: text.trim() })
    setText('')
  }

  const sendAttachment = async (file: File) => {
    setErr('')
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

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!sendMutation.isPending) {
      sendText()
    }
  }

  // Auto-grow textarea (1–4 lines) + button height sync
  const taRef = useRef<HTMLTextAreaElement | null>(null)
  const pageRef = useRef<HTMLDivElement | null>(null)
  const inputWrapRef = useRef<HTMLDivElement | null>(null)
  const [taH, setTaH] = useState<number>(40)
  const measureChat = () => {
    const h = inputWrapRef.current?.offsetHeight ?? 0
    if (pageRef.current) pageRef.current.style.setProperty('--chat-pad', h + 'px')
  }
  const autoSize = () => {
    const el = taRef.current
    if (!el) return
    el.style.height = 'auto'
    const maxH = Math.max(Math.floor(window.innerHeight * 0.4), 120)
    const next = Math.min(Math.max(el.scrollHeight, 40), maxH)
    el.style.height = next + 'px'
    setTaH(next)
    measureChat()
  }
  useEffect(() => { autoSize(); measureChat() }, [])
  useEffect(() => { autoSize() }, [text])
  useEffect(() => {
    const onResize = () => { measureChat() }
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])

  const listEndRef = useRef<HTMLDivElement | null>(null)
  const scrollToEnd = () => {
    listEndRef.current?.scrollIntoView({ block: 'end', behavior: 'auto' })
    const scroller = document.querySelector('.app-content') as HTMLElement | null
    if (scroller) scroller.scrollTo({ top: scroller.scrollHeight, behavior: 'auto' })
  }
  useEffect(() => {
    const timer = setTimeout(scrollToEnd, 0)
    return () => clearTimeout(timer)
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
      localStorage.setItem(`ticket_last_read_${id}`, last)
    } catch {}
  }, [id, messages])

  const shortId = useMemo(() => getShortId(detail?.id || id), [detail?.id, id])

  if (!id || ticketQ.isLoading) {
    return <div className="page-white"><div className="dashboard"><p>Загрузка…</p></div></div>
  }
  if (ticketQ.isError || !detail) {
    return (
      <div className="page-white">
        <div className="dashboard">
          <p>Не удалось загрузить заявку.</p>
          <button className="btn btn-primary" onClick={() => navigate(-1)}>Назад</button>
        </div>
      </div>
    )
  }

  return (
    <div className="page-white">
      <div ref={pageRef} className="ticket-detail page-content chat-page">
        <div className="page-header">
          <button className="back-btn" aria-label="Назад" onClick={() => navigate(-1)}>
            ←
          </button>
          <h2 className="page-title">{shortId ? `ЗАЯВКА ${shortId}` : 'ЗАЯВКА'}</h2>
          <span className="page-action-placeholder" aria-hidden />
        </div>

        <div className="detail-section">
          {detail.master_name ? (
            <div className="detail-desc">
              <strong>Исполнитель</strong>
              <div>{detail.master_name}</div>
            </div>
          ) : null}
          <div className="detail-desc" style={{ marginTop: detail.master_name ? 10 : 0 }}>
            <strong>Короткое описание</strong>
            <div>{detail.title}</div>
          </div>
        </div>

        <div className="detail-section detail-section--messages">
          <div className="detail-section-title">Сообщения</div>
          <div className="chat-scroll">
            {messagesQ.isLoading && <div className="detail-desc">Загрузка…</div>}
            {messagesQ.isError && <div className="detail-desc">Не удалось загрузить сообщения.</div>}
            {!messagesQ.isLoading && messages.length === 0 && (
              <div className="detail-desc">Сообщений пока нет.</div>
            )}
            {!messagesQ.isLoading && messages.length > 0 && (
              <>
                <div className="chat">
                  {messages.map((msg) => {
                    const isMine = msg.author === 'user'
                    return (
                      <div key={msg.id} className={`msg ${isMine ? 'msg--mine' : 'msg--their'}`}>
                        <div className="meta">
                          {formatDateTime(msg.created_at)} - {isMine ? 'Вы' : otherName}
                        </div>
                        <div className="bubble">
                          {msg.body ? <div className="bubble-text">{msg.body}</div> : null}
                          {msg.file_url ? (
                            <img
                              className="bubble-image"
                              src={msg.file_url}
                              alt="Вложение"
                              onClick={() => setPreviewUrl(msg.file_url || null)}
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
      </div>

      {createPortal(
        canSend ? (
          <div ref={inputWrapRef} className="chat-input-fixed">
            <form className="chat-input" onSubmit={onSubmit}>
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
                <div className={`input-placeholder${text.trim().length > 0 ? ' is-hidden' : ''}`}>
                  Напишите сообщение
                </div>
                <textarea
                  ref={taRef}
                  className="input input-area auto-grow"
                  rows={1}
                  aria-label="Сообщение"
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  onInput={autoSize}
                  style={{ height: taH, overflow: 'hidden' }}
                />
              </div>
              <button
                className="btn-send"
                style={{ height: taH, width: taH }}
                aria-label="Отправить"
                disabled={sendMutation.isPending || !text.trim()}
                type="submit"
              >
                ↑
              </button>
            </form>
          </div>
        ) : (
          <div className="chat-closed">Заявка закрыта</div>
        ),
        document.body
      )}
      {previewUrl ? (
        <div className="image-preview" onClick={() => setPreviewUrl(null)} role="presentation">
          <button
            type="button"
            className="image-preview__close"
            aria-label="Закрыть"
            onClick={() => setPreviewUrl(null)}
          >
            ×
          </button>
          <img src={previewUrl} alt="Фото" />
        </div>
      ) : null}
    </div>
  )
}
