import { useNavigate } from 'react-router-dom'

export default function SubscriptionSuccess() {
  const nav = useNavigate()
  return (
    <div className="page-full page-blue">
      <div className="card auth-card" style={{ maxWidth: 360 }}>
        <h1 className="card-title">Подписка оформлена</h1>
        <p style={{textAlign:'center', margin:'8px 0 16px'}}>
          Спасибо! Подписка активирована.
        </p>
        <button className="btn btn-primary" onClick={() => nav('/', { replace:true })}>
          Вернуться
        </button>
      </div>
    </div>
  )
}