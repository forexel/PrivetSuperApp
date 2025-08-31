import { useNavigate } from 'react-router-dom'
import AvatarIcon from '../../assets/profile/avatar.svg'
import PencilIcon from '../../assets/icons/pencil.svg?react'
import '../../styles/profile.css'

export function ProfilePage() {
  const navigate = useNavigate()

  // TODO: когда подключишь API — подставь реальные данные пользователя
  const user = {
    name: 'Иван Иванов',
    email: 'ivanoff@mail.ru',
    phone: '+7(077)123-23-23',
    plan: 'Все просто',
    paidUntil: '1 Апреля 2025',
  }

  const onLogout = () => {
    try {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    } catch {}
    navigate('/login')
  }

  return (
    <div className="dashboard profile">
      {/* Header */}
      <div className="profile-header">
        <div className="profile-avatar">
          <img src={AvatarIcon} alt="Аватар" />
        </div>
        <div className="profile-name">{user.name}</div>
        <div className="profile-email">{user.email}</div>
      </div>

      {/* Cards */}
      <div className="info-list">
        <div className="info-item">
          <div className="text">
            <div className="info-title">Имя Фамилия</div>
            <div className="info-subtitle">{user.name}</div>
          </div>
          <a href="#" className="info-edit" aria-label="Редактировать имя">
            <PencilIcon className="pencil-icon" />
          </a>
        </div>

        <div className="info-item">
          <div className="text">
            <div className="info-title">Телефон</div>
            <div className="info-subtitle">{user.phone}</div>
          </div>
        </div>

        <div className="info-item">
          <div className="text">
            <div className="info-title">Email</div>
            <div className="info-subtitle">{user.email}</div>
          </div>
          <a href="#" className="info-edit" aria-label="Редактировать email">
            <PencilIcon className="pencil-icon" />
          </a>
        </div>

        <div className="info-item">
          <div className="text">
            <div className="info-title">Тариф</div>
            <div className="info-subtitle">{user.plan}</div>
          </div>
        </div>

        <div className="info-item">
          <div className="text">
            <div className="info-title">Оплачен до</div>
            <div className="info-subtitle">{user.paidUntil}</div>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="profile-actions">
        <button className="btn btn-primary profile-logout" onClick={onLogout}>
          Выйти
        </button>
        <div className="profile-danger">Удалить аккаунт</div>
      </div>
    </div>
  )
}

export default ProfilePage