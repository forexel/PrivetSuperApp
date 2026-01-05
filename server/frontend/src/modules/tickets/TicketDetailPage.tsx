import { useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../shared/api'
import ChatIcon from '../../assets/icons/chats.svg?react'
import CloseIcon from '../../assets/icons/close.svg?react'
import '../../styles/tickets.css'

type HistoryItem = { status: 'new'|'in_progress'|'completed'|'reject'; at: string }
type TicketDetail = {
  id: string
  title: string
  description?: string | null
  created_at: string
  updated_at?: string | null
  status: 'new'|'in_progress'|'completed'|'reject'
  status_history: HistoryItem[]
  attachment_urls?: string[]
  work_report?: {
    summary: string
    details: string
    photos: string[]
  } | null
}
type TicketMessage = {
  id: string
  author: 'user' | 'master'
  created_at: string
}

const statusLabels: Record<HistoryItem['status'], string> = {
  new: 'New',
  in_progress: 'In progress',
  completed: 'Done',
  reject: 'Rejected',
}

function formatDate(iso?: string | null) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleString('ru-RU', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
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

export default function TicketDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [showRate, setShowRate] = useState(false)
  const [showReport, setShowReport] = useState(false)
  const [rateMode, setRateMode] = useState<'new' | 'view'>('new')
  const [selectedStars, setSelectedStars] = useState(0)
  const [comment, setComment] = useState('')
  const { data, isLoading, isError } = useQuery({
    queryKey: ['ticket', id],
    queryFn: () => api.get<TicketDetail>(`/tickets/${id}`),
    enabled: !!id,
  })
  const { data: messages } = useQuery({
    queryKey: ['ticket', id, 'messages'],
    queryFn: () => api.get<TicketMessage[]>(`/tickets/${id}/messages`),
    enabled: !!id,
    staleTime: 20_000,
  })

  const storedRating = useMemo(() => {
    if (!data?.id) return null
    try {
      const raw = localStorage.getItem(`ticket_rating_${data.id}`)
      return raw ? JSON.parse(raw) as { stars: number; comment?: string } : null
    } catch {
      return null
    }
  }, [data?.id])
  const hasUnread = useMemo(() => {
    if (!id || !messages?.length) return false
    const lastReadRaw = localStorage.getItem(`ticket_last_read_${id}`)
    const lastRead = lastReadRaw ? new Date(lastReadRaw).getTime() : 0
    const lastFromMaster = messages
      .filter((m) => m.author === 'master')
      .map((m) => new Date(m.created_at).getTime())
      .reduce((acc, t) => Math.max(acc, t), 0)
    if (!lastFromMaster) return false
    return lastFromMaster > lastRead
  }, [id, messages])
  const ratingStars = storedRating?.stars ?? 0
  const report = data?.work_report ?? null

  if (isLoading) return <div className="page-blue"><div className="card auth-card">Загрузка…</div></div>
  if (isError || !data) return <div className="page-blue"><div className="card auth-card">Не удалось загрузить заявку</div></div>

  const updated = data.updated_at ?? data.created_at
  const canChat = data.status === 'in_progress' || data.status === 'completed'

  const shortId = getShortId(data.id)

  return (
    <div className="page-white">
      <div className="ticket-detail page-content">
        <div className="page-header">
          <button className="back-btn" aria-label="Назад" onClick={() => window.location.assign('/tickets')}>
            ←
          </button>
          <h2 className="page-title">{shortId ? `ЗАЯВКА ${shortId}` : 'ЗАЯВКА'}</h2>
          {canChat ? (
            <button
              className="page-action"
              aria-label="Чат"
              onClick={() => navigate(`/tickets/${data.id}/chat`)}
            >
              <ChatIcon />
              {hasUnread ? <span className="page-action-dot" /> : null}
            </button>
          ) : (
            <span className="page-action-placeholder" aria-hidden />
          )}
        </div>

        {/* Короткое описание проблемы + актуальный статус */}
        <div className="detail-title-row">
          <div className="detail-title">{data.title}</div>
          <span className={`status-badge status-${data.status}`}>{statusLabels[data.status]}</span>
        </div>
        <div className="detail-updated">обновлено {formatDate(updated)}</div>

        {/* Подробное описание */}
        {data.description ? (
          <div className="detail-section">
            <div className="detail-desc">{data.description}</div>
          </div>
        ) : null}

        {data.attachment_urls?.length ? (
          <div className="detail-section">
            <div className="detail-section-title">Фото при наличии</div>
            <div className="detail-photos">
              {data.attachment_urls.map((url, index) => (
                <img key={`${url}-${index}`} src={url} alt="Фото заявки" />
              ))}
            </div>
          </div>
        ) : null}

        {data.status === 'completed' && data.work_report ? (
          <div className="detail-section report-actions">
            <button className="btn btn-secondary report-btn" onClick={() => setShowReport(true)}>
              Отчет
            </button>
            <div className={`report-rating ${ratingStars ? 'report-rating--locked' : ''}`}>
              {Array.from({ length: 5 }).map((_, idx) => (
                <button
                  key={idx}
                  type="button"
                  className={`rating-star rating-star--small ${idx < ratingStars ? 'rating-star--active' : ''}`}
                  onClick={() => {
                    setRateMode(ratingStars ? 'view' : 'new')
                    setSelectedStars(ratingStars ? ratingStars : idx + 1)
                    setComment(storedRating?.comment || '')
                    setShowRate(true)
                  }}
                  aria-label={`Поставить ${idx + 1} звезд`}
                >
                  ★
                </button>
              ))}
            </div>
          </div>
        ) : null}
      </div>

      {showReport && report ? (
        <div className="ticket-popup-overlay">
          <div className="ticket-popup-header">
            <h3>Отчет</h3>
            <button className="ticket-popup-close" aria-label="Закрыть" onClick={() => setShowReport(false)}>
              <CloseIcon aria-hidden="true" />
            </button>
          </div>
          <div className="ticket-popup-card">
            <div className="ticket-popup-body">
              <div className="report-field">
                <div className="report-label">Описание работ</div>
                <div className="report-value">{report.summary}</div>
              </div>
              <div className="report-field">
                <div className="report-label">Подробно что сделано</div>
                <div className="report-value">{report.details}</div>
              </div>
              {report.photos?.length ? (
                <div className="report-photos">
                  {report.photos.map((url, index) => (
                    <img key={`${url}-${index}`} src={url} alt="Фото работ" />
                  ))}
                </div>
              ) : null}
            </div>
            <div className="ticket-popup-footer">
              <button className="btn btn-primary" type="button" onClick={() => setShowReport(false)}>
                Понятно
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {showRate ? (
        <div className="ticket-popup-overlay">
          <div className="ticket-popup-header">
            <h3>{rateMode === 'view' ? 'Оценка' : 'Оценить работу'}</h3>
            <button className="ticket-popup-close" aria-label="Закрыть" onClick={() => setShowRate(false)}>
              <CloseIcon aria-hidden="true" />
            </button>
          </div>
          <div className="ticket-popup-card">
            <div className="ticket-popup-body">
              <div className="rating-stars">
                {Array.from({ length: 5 }).map((_, idx) => (
                  <button
                    key={idx}
                    type="button"
                    className={`rating-star ${idx < selectedStars ? 'rating-star--active' : ''}`}
                    onClick={() => rateMode === 'new' && setSelectedStars(idx + 1)}
                    aria-label={`Поставить ${idx + 1} звезд`}
                    disabled={rateMode === 'view'}
                  >
                    ★
                  </button>
                ))}
              </div>
              <div className="rating-label">Комментарий</div>
              {rateMode === 'view' ? (
                <div className="rating-comment">{comment || '—'}</div>
              ) : (
                <textarea
                  className="rating-textarea"
                  placeholder="Комментарий"
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                />
              )}
            </div>
            {rateMode === 'new' ? (
              <div className="ticket-popup-footer">
                <button
                  className="btn btn-primary rating-submit"
                  type="button"
                  onClick={() => {
                    if (!data?.id || selectedStars === 0) return
                    localStorage.setItem(`ticket_rating_${data.id}`, JSON.stringify({ stars: selectedStars, comment }))
                    setShowRate(false)
                  }}
                >
                  Отправить
                </button>
              </div>
            ) : null}
          </div>
        </div>
      ) : null}
    </div>
  )
}
