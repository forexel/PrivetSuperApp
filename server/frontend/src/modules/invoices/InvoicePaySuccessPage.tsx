import { useNavigate } from 'react-router-dom'
import '../../styles/forms.css'

export default function InvoicePaySuccessPage() {
  const nav = useNavigate()
  return (
    <div className="page-full page-blue">
      <div className="modal-wrap modal-wrap--wide">
        <div className="card auth-card auth-card--center">
          <h1 className="card-title">Счёт оплачен</h1>
          <p className="success-text">Оплата прошла успешно. Счета исчезли из списка.</p>
          <button className="btn btn-primary" onClick={() => nav('/', { replace: true })}>
            Вернуться
          </button>
        </div>
      </div>
    </div>
  )
}
