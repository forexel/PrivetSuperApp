import '../../styles/forms.css'
import { CloseFloating } from '../../shared/ui/CloseFloating'
import { useNavigate } from 'react-router-dom'

export function SupportSuccessPage() {
  const navigate = useNavigate()
  return (
    <div className="page-blue">
      <CloseFloating onClick={() => navigate(-1)} />

      <div className="card auth-card">
        <h2 className="card-title">Обращение отправлено</h2>
        <p style={{ textAlign: 'center' }}>
          Мы получили ваше сообщение. Оператор свяжется с вами, чтобы уточнить детали.
        </p>
        <button className="btn btn-primary" onClick={() => navigate('/support')}>
          Вернуться
        </button>
      </div>
    </div>
  )
}

export default SupportSuccessPage