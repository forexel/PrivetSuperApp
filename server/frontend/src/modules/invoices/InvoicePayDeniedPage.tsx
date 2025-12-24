import { useNavigate } from 'react-router-dom'
import '../../styles/forms.css'

export default function InvoicePayDeniedPage() {
  const nav = useNavigate()
  return (
    <div className="page-full page-blue">
      <div className="modal-wrap modal-wrap--wide">
        <div className="card auth-card auth-card--center" style={{ maxWidth: 360 }}>
          <h1 className="card-title">Счёт не оплачен</h1>
          <p className="success-text">Произошла ошибка оплаты. Счета остались в списке.</p>
          <button className="btn btn-primary" onClick={() => nav('/invoices/pay', { replace: true })}>
            Вернуться к счетам
          </button>
        </div>
      </div>
    </div>
  )
}
