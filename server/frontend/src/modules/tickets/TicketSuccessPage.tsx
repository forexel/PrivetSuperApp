import { useNavigate } from 'react-router-dom'
import '../../styles/forms.css'
import { CloseFloating } from '../../shared/ui/CloseFloating'

export default function TicketSuccessPage() {
  const navigate = useNavigate()

  return (
    <div className="page-blue">
      <CloseFloating onClick={() => navigate(-1)} />

      <div className="card auth-card">
        <h2 className="card-title">Заявка отправлена</h2>
        <p className="success-text">
          Мы приняли вашу заявку и уже начали обработку.
          Статус можно посмотреть в разделе «Заявки».
        </p>

        <div className="cta">
          <button className="btn btn-primary" onClick={() => navigate('/tickets')}>
            Перейти к заявкам
          </button>
        </div>
      </div>
    </div>
  )
}