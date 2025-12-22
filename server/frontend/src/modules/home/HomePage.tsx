import { useQuery } from '@tanstack/react-query'
// ⚠️ Проверь путь к твоему axios-инстансу:
import { api } from '../../shared/api'
import { PLAN_TITLES, PERIOD_TITLES } from '../../shared/subscriptions'
import '../../styles/dashboard.css'
import '../../styles/invoices.css'

type Ticket = {
  id: string
  title: string
  description?: string
  status: 'new' | 'in_progress' | 'completed' | 'reject'
  updated_at?: string
}

type Invoice = {
  id: string
  amount: number
  description?: string | null
  contract_number?: string | null
  due_date?: string | null
  status: string
}

// Универсальный фетчер: забираем список заявок
async function fetchTickets(): Promise<Ticket[]> {
  const data = await api.get<Ticket[] | { items: Ticket[] } | { results: Ticket[] }>('/tickets/')
  if (Array.isArray(data)) return data
  if ('items' in data && Array.isArray(data.items)) return data.items
  if ('results' in data && Array.isArray(data.results)) return data.results
  return []
}

export function HomePage() {
  // План/техника — пока статичные подписи как были
  const devicesMeta = 'зарегистрировано 0 устройств'

  // Тянем заявки
  const { data: tickets = [], isLoading } = useQuery({
    queryKey: ['tickets','home-summary'],
    queryFn: fetchTickets,
  })

  // 1) счётчики поддержки из /support/meta
  const { data: supportMeta } = useQuery({
    queryKey: ['supportMeta'],
    queryFn: () => api.get<{ active: number; total: number }>('/support/meta'),
  });

  // 2) активная подписка из /subscriptions/active
  const { data: activeSub } = useQuery({
    queryKey: ['active-subscription'],
    queryFn: () => api.get<{ plan?: string|null; period?: string|null; paid_until?: string|null }>('/subscriptions/active'),
  });

  // 4) счета пользователя
  const { data: invoicesAll = [] } = useQuery({
    queryKey: ['invoices', 'my', 'all'],
    queryFn: () => api.get<Invoice[]>('/invoices/my?include_paid=true'),
  })

  // 3) мой адрес
  const { data: me } = useQuery({
    queryKey: ['me'],
    queryFn: () => api.get<{ address?: string | null }>('/user/me'),
  });
  const localAddress = (typeof localStorage !== 'undefined' ? localStorage.getItem('user_address') : null) || undefined
  const displayAddress = (me?.address ?? localAddress) || 'Адрес не указан'

  // Мэппинг статусов: активные = new + in_progress; всего = все
  const activeTickets = tickets.filter(t => t.status === 'new' || t.status === 'in_progress').length
  const totalTickets  = tickets.length

  // Если хочешь красиво показывать «0 активных / 0 всего» до загрузки:
  const activeText = isLoading ? '—' : String(activeTickets)
  const totalText  = isLoading ? '—' : String(totalTickets)

  const activeSupportText = String(supportMeta?.active ?? 0)
  const totalSupportText  = String(supportMeta?.total  ?? 0)

  const invoicesToPay = invoicesAll.filter((inv) => String(inv.status).toLowerCase() !== 'paid')

  // Заглушка для поддержки (позже можно сделать аналогичный запрос)

  return (
    <div className="dashboard">
      <div className="dashboard-title">
        <h1>Главная</h1>
      </div>

      <div className="summary-cards">
        <div className="summary-card">
          <div className="title">Мой адрес</div>
          <div className="meta">{displayAddress}</div>
        </div>
        <div className="summary-card">
          <div className="title">Тариф</div>
          <div className="meta">
            {activeSub?.plan
              ? `Тариф: ${PLAN_TITLES[activeSub.plan as keyof typeof PLAN_TITLES] ?? activeSub.plan} • ${activeSub.period ? (PERIOD_TITLES[activeSub.period as keyof typeof PERIOD_TITLES] ?? activeSub.period) : ''}`
              : 'Нет активной подписки'}
          </div>
          {activeSub?.paid_until && (
            <div className="meta">Активна до: {new Date(activeSub.paid_until as any).toLocaleDateString('ru-RU')}</div>
          )}
      </div>

        <div className="summary-card">
          <div className="title">Моя техника</div>
          <div className="meta">{devicesMeta}</div>
        </div>

        <div className="summary-card">
          <div className="title">Вызовы мастеров</div>
          <div className="meta meta-inline">Активных: {activeText} / Всего: {totalText}</div>
        </div>

        <div className="summary-card">
          <div className="title">Обращения в поддержку</div>
          <div className="meta meta-inline">Активных: {activeSupportText} / Всего: {totalSupportText}</div>
        </div>

        <div className="summary-card invoice-card">
          <div className="title">Счета</div>
          <div className="meta meta-inline">
            К оплате: {invoicesToPay.length} / Всего: {invoicesAll.length}
          </div>
          {invoicesToPay.length > 0 && (
            <button className="btn-invoice" onClick={() => window.location.assign('/invoices/pay')}>
              Оплатить
            </button>
          )}
        </div>
      </div>

      {!activeSub?.plan && (
        <div className="cta">
          <button className="btn-choose-plan" onClick={() => window.location.assign('/subscriptions')}>
            Выбрать тариф
          </button>
        </div>
      )}
    </div>
  );
}
