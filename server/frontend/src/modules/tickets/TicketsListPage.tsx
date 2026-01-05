import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../shared/api'
import { useNavigate } from 'react-router-dom'
import '../../styles/tickets.css'

type TicketListItem = {
  id: string
  title: string
  status: 'new' | 'in_progress' | 'completed' | 'done' | 'reject'
  created_at: string
  updated_at?: string
}

const statusLabel: Record<TicketListItem['status'], string> = {
  new: 'New',
  in_progress: 'In progress',   // или 'In progress'
  completed: 'Done',
  done: 'Done',
  reject: 'Rejected',
}

const toUiStatus = (raw: string) =>
  (raw ?? 'new').replace(/\s+/g, '_').toLowerCase() as TicketListItem['status'];

export function TicketsListPage() {
  const navigate = useNavigate()
  const [showRate, setShowRate] = useState(false)
  const [rateTicketId, setRateTicketId] = useState<string | null>(null)
  const [selectedStars, setSelectedStars] = useState(0)
  const [comment, setComment] = useState('')
  const [ratingRefresh, setRatingRefresh] = useState(0)

  const { data, isLoading, error } = useQuery({
    queryKey: ['tickets', 'my'],
    queryFn: () => api.get<TicketListItem[]>('/tickets/'),
    retry: false,
  })
  const { data: activeSub } = useQuery({
    queryKey: ['active-subscription', 'tickets'],
    queryFn: () => api.get<{ plan?: string | null }>('/subscriptions/active'),
  })
  const hasSubscription = !!activeSub?.plan

  const storedRating = useMemo(() => {
    if (!rateTicketId) return null
    try {
      const raw = localStorage.getItem(`ticket_rating_${rateTicketId}`)
      return raw ? (JSON.parse(raw) as { stars: number; comment?: string }) : null
    } catch {
      return null
    }
  }, [rateTicketId, ratingRefresh])

  const ratingStars = storedRating?.stars ?? 0

  return (
    <div className="dashboard">
      <h1>Вызов Мастера</h1>

      {isLoading && (
        <div className="empty-state">
          <div className="empty-box">Загрузка…</div>
        </div>
      )}

      {!isLoading && error && (
        <div className="empty-state">
          <div className="empty-box">
            <div className="empty-title" style={{ color: 'red' }}>Ошибка</div>
            <div className="empty-text">{(error as any)?.message ?? 'Неизвестная ошибка'}</div>
          </div>
        </div>
      )}

      {!isLoading && !error && (data ?? []).length === 0 && (
        <div className="empty-state">
          <div className="empty-box">
            <div className="empty-title">Пока тут пусто</div>
            <div className="empty-text">Вы пока не вызывали мастера</div>
          </div>
        </div>
      )}

      {!isLoading && !error && (data ?? []).length > 0 && (
        <ul className="req-list">
          {(data ?? []).map((t) => {
            const when = new Date((t as any).updated_at ?? t.created_at).toLocaleString('ru-RU', {
              day: '2-digit', month: '2-digit', year: 'numeric',
              hour: '2-digit', minute: '2-digit'
            })
            const uiStatus = toUiStatus((t as any).status);
            const ratingKey = `ticket_rating_${t.id}`
            const ticketRating = (() => {
              try {
                const raw = localStorage.getItem(ratingKey)
                return raw ? (JSON.parse(raw) as { stars: number; comment?: string }) : null
              } catch {
                return null
              }
            })()
            const ticketStars = ticketRating?.stars ?? 0
            const showStars = uiStatus === 'completed' || uiStatus === 'done'
            return (
              <li
                key={t.id}
                className="req-item"
                onClick={() => navigate(`/tickets/${t.id}`)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') navigate(`/tickets/${t.id}`) }}
                style={{ cursor: 'pointer' }}
              >
                <div className="req-avatar" />
                <div>
                  <div className="req-title-row">
                    <div className="req-title">{t.title}</div>
                    <span className={`req-badge st-${uiStatus}`}>{statusLabel[uiStatus]}</span>
                  </div>
                  <div className="req-meta">{when}</div>
                  {showStars ? (
                    <div className={`req-rating ${ticketStars ? 'req-rating--locked' : ''}`}>
                      {Array.from({ length: 5 }).map((_, idx) => (
                        <button
                          key={idx}
                          type="button"
                          className={`rating-star ${idx < ticketStars ? 'rating-star--active' : ''}`}
                          onClick={(event) => {
                            event.stopPropagation()
                            if (ticketStars) return
                            setRateTicketId(t.id)
                            setSelectedStars(idx + 1)
                            setComment('')
                            setShowRate(true)
                          }}
                          aria-label={`Поставить ${idx + 1} звезд`}
                          disabled={ticketStars > 0}
                        >
                          ★
                        </button>
                      ))}
                    </div>
                  ) : null}
                </div>
              </li>
            )
          })}
        </ul>
      )}

      <div className="req-fab">
        <button
          className="btn-fab"
          onClick={() => hasSubscription && navigate('/tickets/new')}
          disabled={!hasSubscription}
        >
          Вызвать
        </button>
      </div>

      {showRate && rateTicketId ? (
        <div className="ticket-popup-overlay">
          <div className="ticket-popup-header">
            <h3>Оценить работу</h3>
            <button className="ticket-popup-close" aria-label="Закрыть" onClick={() => setShowRate(false)}>×</button>
          </div>
          <div className="ticket-popup-card">
            <div className="ticket-popup-body">
              <div className="rating-stars">
                {Array.from({ length: 5 }).map((_, idx) => (
                  <button
                    key={idx}
                    type="button"
                    className={`rating-star ${idx < selectedStars ? 'rating-star--active' : ''}`}
                    onClick={() => setSelectedStars(idx + 1)}
                    aria-label={`Поставить ${idx + 1} звезд`}
                  >
                    ★
                  </button>
                ))}
              </div>
              <div className="rating-label">Комментарий</div>
              <textarea
                className="rating-textarea"
                value={comment}
                placeholder="Напишите комментарий"
                onChange={(event) => setComment(event.target.value)}
              />
              {ratingStars > 0 ? (
                <div className="rating-comment">{comment || '—'}</div>
              ) : null}
            </div>
            <div className="ticket-popup-footer">
              <button
                className="btn btn-primary rating-submit"
                type="button"
                onClick={() => {
                  if (!rateTicketId || selectedStars === 0) return
                  localStorage.setItem(`ticket_rating_${rateTicketId}`, JSON.stringify({ stars: selectedStars, comment }))
                  setRatingRefresh((prev) => prev + 1)
                  setShowRate(false)
                }}
              >
                Отправить
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}

export default TicketsListPage
