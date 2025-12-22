import { useNavigate } from 'react-router-dom'
import { CloseFloating } from '../../shared/ui/CloseFloating'
import '../../styles/forms.css'

export default function InvoicePaySuccessPage() {
  const nav = useNavigate()
  return (
    <div className="page-full page-blue">
      <div className="modal-wrap modal-wrap--wide">
        <CloseFloating onClick={() => (window.history.length > 1 ? nav(-1) : nav('/', { replace: true }))} />
        <div className="card auth-card" style={{ maxWidth: 360 }}>
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
