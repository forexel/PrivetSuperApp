import { useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { api } from '../../shared/api'
import { PLAN_TITLES, PERIOD_TITLES } from '../../shared/subscriptions'
import '../../styles/forms.css'

const PRICES = {
  month: { simple: 3999, medium: 7999, premium: 13999 },
  year: { simple: 39990, medium: 79990, premium: 139990 },
}

type LocationState = { plan?: 'simple' | 'medium' | 'premium'; period?: 'month' | 'year' }

export default function SubscriptionPayPage() {
  const nav = useNavigate()
  const { state } = useLocation()
  const [busy, setBusy] = useState(false)

  const { plan, period } = (state as LocationState) || {}

  const amount = useMemo(() => {
    if (!plan || !period) return 0
    return PRICES[period][plan]
  }, [plan, period])

  const onSuccess = async () => {
    if (!plan || !period) return
    try {
      setBusy(true)
      await api.post('/subscriptions/create', { plan, period })
      nav('/subscriptions/success', { replace: true })
    } catch {
      nav('/subscriptions/denied', { replace: true })
    } finally {
      setBusy(false)
    }
  }

  if (!plan || !period) {
    return (
      <div className="page-full page-blue">
        <div className="modal-wrap modal-wrap--wide">
          <div className="card auth-card auth-card--center">
            <h1 className="card-title">Выбор тарифа</h1>
            <p className="success-text">Сначала выберите тариф.</p>
            <button className="btn btn-primary" onClick={() => nav('/subscriptions', { replace: true })}>
              К тарифам
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="page-full page-blue">
      <div className="modal-wrap modal-wrap--wide">
        <div className="card auth-card auth-card--center">
          <h1 className="card-title">Процесс оплаты</h1>
          <p className="success-text">
            {PLAN_TITLES[plan]} • {PERIOD_TITLES[period]}
          </p>
          <p className="success-text">К оплате: {amount.toLocaleString('ru-RU')} ₽</p>
          <button className="btn btn-primary" onClick={onSuccess} disabled={busy}>
            Успешная оплата
          </button>
          <button className="btn btn-secondary" onClick={() => nav('/subscriptions/denied', { replace: true })} disabled={busy}>
            Неуспешная оплата
          </button>
        </div>
      </div>
    </div>
  )
}
