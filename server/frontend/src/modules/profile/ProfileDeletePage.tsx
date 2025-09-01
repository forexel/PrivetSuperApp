import { useNavigate } from 'react-router-dom'
import '../../styles/forms.css'

export default function ProfileDeletePage() {
  const nav = useNavigate()

  const onDelete = async () => {
    try {
      await fetch('/api/v1/user', { method: 'DELETE', headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}` } })
    } catch {}
    try {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    } catch {}
    nav('/login', { replace: true })
  }

  return (
    <div className="page-full page-blue">
      <div className="card auth-card" style={{ textAlign: 'center' }}>
        <h1 className="card-title">Удаление аккаунта</h1>
        <p className="success-text" style={{ marginTop: 8 }}>
          Вы точно хотите удалить аккаунт? Восстановление будет невозможно
        </p>
        <button className="btn btn-primary" onClick={() => nav('/profile')}>Вернуться</button>
        <div className="auth-footer" style={{ marginTop: 8 }}>
          <button onClick={onDelete} className="btn" style={{ background: 'transparent', color: '#6b7280' }}>
            Всё равно удалить
          </button>
        </div>
      </div>
    </div>
  )
}

