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

  const onPay = async () => {
    if (!plan || !period) return
    try {
      setBusy(true)
      const resp = await api.post<{ redirect_url: string }>('/payments/yookassa/subscription', { plan, period })
      if (resp?.redirect_url) {
        window.location.assign(resp.redirect_url)
        return
      }
      throw new Error('redirect_url missing')
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
          <h1 className="card-title">Перейти к оплате</h1>
          <p className="success-text">
            {PLAN_TITLES[plan]} • {PERIOD_TITLES[period]}
          </p>
          <p className="success-text">К оплате: {amount.toLocaleString('ru-RU')} ₽</p>
          <button className="btn btn-primary" onClick={onPay} disabled={busy}>
            Перейти к оплате
          </button>
          <button className="btn btn-secondary" onClick={() => nav('/subscriptions', { replace: true })} disabled={busy}>
            Вернуться
          </button>
        </div>
      </div>
    </div>
  )
}
