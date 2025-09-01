import { useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../../shared/api'
import { PLAN_TITLES } from '../../shared/subscriptions'
import AvatarIcon from '../../assets/profile/avatar.svg'
import PencilIcon from '../../assets/icons/pencil.svg?react'
import AcceptIcon from '../../assets/icons/accept.svg?react'
import CancelIcon from '../../assets/icons/cross.svg?react'
import '../../styles/profile.css'

export function ProfilePage() {
  const navigate = useNavigate()

  type Me = { id: string; name?: string|null; email?: string|null; phone: string; address?: string|null }
  const { data: me } = useQuery({
    queryKey: ['me'],
    queryFn: () => api.get<Me>('/api/v1/user/me'),
  })

  // активная подписка
  type ActiveSub = { plan?: string|null; period?: 'month'|'year'|null; paid_until?: string|null }
  const { data: activeSub } = useQuery({
    queryKey: ['active-subscription'],
    queryFn: () => api.get<ActiveSub | null>('/api/v1/subscriptions/active'),
  })

  // редакторы
  const qc = useQueryClient()
  const [editName, setEditName] = useState(false)
  const [nameValue, setNameValue] = useState('')
  const [editEmail, setEditEmail] = useState(false)
  const [emailValue, setEmailValue] = useState('')
  const [editPwd, setEditPwd] = useState(false)
  const [oldPwd, setOldPwd] = useState('')
  const [newPwd, setNewPwd] = useState('')
  const [pwdError, setPwdError] = useState<string>('')

  // Отвечает за то, чтобы в один момент редактировался только один блок
  const openEdit = (section: 'name' | 'email' | 'pwd') => {
    setEditName(section === 'name')
    setEditEmail(section === 'email')
    setEditPwd(section === 'pwd')
    // Сброс временных значений и ошибок из других блоков
    setNameValue((me?.name || '').trim())
    setEmailValue((me?.email || '').trim())
    setOldPwd('')
    setNewPwd('')
    setPwdError('')
  }

  useEffect(() => {
    if (me) {
      setNameValue(me.name || '')
      setEmailValue(me.email || '')
    }
  }, [me])

  const mutation = useMutation({
    mutationFn: async (payload: Partial<Pick<Me, 'name'|'email'>>) => {
      const body: any = {}
      if (typeof payload.name !== 'undefined') body.name = payload.name?.trim() || undefined
      if (typeof payload.email !== 'undefined') body.email = (payload.email?.trim() || null) // null = очистить email
      return api.put<Me>('/api/v1/user', body)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['me'] })
      setEditName(false)
      setEditEmail(false)
    },
  })

  const pwdMutation = useMutation({
    mutationFn: async (payload: { old_password: string; new_password: string }) => {
      setPwdError('')
      return api.post<null>('/api/v1/user/change-password', payload as any)
    },
    onSuccess: () => {
      setEditPwd(false)
      setOldPwd('')
      setNewPwd('')
    },
    onError: (e: any) => {
      const msg = e?.status === 400 ? 'Старый пароль неверный' : 'Не удалось сменить пароль'
      setPwdError(msg)
    },
  })

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
        <div className="profile-name">{me?.name || '—'}</div>
        <div className="profile-email">{me?.email || '—'}</div>
      </div>

      {/* Cards */}
      <div className="info-list">
        <div className="info-item">
          <div className="text" style={{ flex: 1 }}>
            <div className="info-title">Имя Фамилия</div>
            {!editName ? (
              <div className="info-subtitle">{me?.name || '—'}</div>
            ) : (
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <input className="input" value={nameValue} onChange={(e) => setNameValue(e.target.value)} placeholder="Иван Иванов" />
                <button
                  className="info-edit icon-round accept"
                  title="Сохранить"
                  aria-label="Сохранить"
                  onClick={() => mutation.mutate({ name: nameValue })}
                  disabled={mutation.isPending}
                >
                  <AcceptIcon />
                </button>
                <button
                  className="info-edit icon-round cancel"
                  title="Отмена"
                  aria-label="Отмена"
                  onClick={() => { setEditName(false); setNameValue(me?.name || '') }}
                >
                  <CancelIcon />
                </button>
              </div>
            )}
          </div>
          {!editName && (
            <button className="info-edit" aria-label="Редактировать имя" onClick={() => openEdit('name')}>
              <PencilIcon className="pencil-icon" />
            </button>
          )}
        </div>

        <div className="info-item">
          <div className="text">
            <div className="info-title">Телефон</div>
            <div className="info-subtitle">{formatPhone10(me?.phone || '')}</div>
          </div>
        </div>

        <div className="info-item">
          <div className="text" style={{ flex: 1 }}>
            <div className="info-title">Email</div>
            {!editEmail ? (
              <div className="info-subtitle">{me?.email || '—'}</div>
            ) : (
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <input className="input" value={emailValue} onChange={(e) => setEmailValue(e.target.value)} placeholder="email@domain.ru" />
                <button
                  className="info-edit icon-round accept"
                  title="Сохранить"
                  aria-label="Сохранить"
                  onClick={() => mutation.mutate({ email: emailValue })}
                  disabled={mutation.isPending}
                >
                  <AcceptIcon />
                </button>
                <button
                  className="info-edit icon-round cancel"
                  title="Отмена"
                  aria-label="Отмена"
                  onClick={() => { setEditEmail(false); setEmailValue(me?.email || '') }}
                >
                  <CancelIcon />
                </button>
              </div>
            )}
          </div>
          {!editEmail && (
            <button className="info-edit" aria-label="Редактировать email" onClick={() => openEdit('email')}>
              <PencilIcon className="pencil-icon" />
            </button>
          )}
        </div>

        {/* Смена пароля */}
        <div className="info-item">
          <div className="text" style={{ flex: 1 }}>
            <div className="info-title">Смена пароля</div>
            {!editPwd ? (
              <div className="info-subtitle">••••••••</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <input
                  className="input"
                  type="password"
                  placeholder="Старый пароль"
                  value={oldPwd}
                  onChange={(e) => setOldPwd(e.target.value)}
                />
                <input
                  className="input"
                  type="password"
                  placeholder="Минимум 8 символов"
                  value={newPwd}
                  onChange={(e) => setNewPwd(e.target.value)}
                />
                {pwdError && <div className="error" role="alert">{pwdError}</div>}
                <div style={{ display: 'flex', gap: 8 }}>
                  <button
                    className="info-edit icon-round accept"
                    title="Сохранить"
                    aria-label="Сохранить"
                    onClick={() => pwdMutation.mutate({ old_password: oldPwd, new_password: newPwd })}
                    disabled={pwdMutation.isPending || newPwd.length < 8 || !oldPwd}
                  >
                    <AcceptIcon />
                  </button>
                  <button
                    className="info-edit icon-round cancel"
                    title="Отмена"
                    aria-label="Отмена"
                    onClick={() => { setEditPwd(false); setOldPwd(''); setNewPwd(''); setPwdError('') }}
                  >
                    <CancelIcon />
                  </button>
                </div>
              </div>
            )}
          </div>
          {!editPwd && (
            <button className="info-edit" aria-label="Сменить пароль" onClick={() => openEdit('pwd')}>
              <PencilIcon className="pencil-icon" />
            </button>
          )}
        </div>

        <div className="info-item">
          <div className="text">
            <div className="info-title">Тариф</div>
            <div className="info-subtitle">
              {activeSub?.plan ? (PLAN_TITLES[activeSub.plan as keyof typeof PLAN_TITLES] ?? activeSub.plan) : '—'}
            </div>
          </div>
        </div>

        <div className="info-item">
          <div className="text">
            <div className="info-title">Оплачен до</div>
            <div className="info-subtitle">{activeSub?.paid_until ? new Date(activeSub.paid_until).toLocaleDateString('ru-RU') : '—'}</div>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="profile-actions">
        <button className="btn btn-primary profile-logout" onClick={onLogout}>
          Выйти
        </button>
        <button className="profile-danger" onClick={() => navigate('/profile/delete')} style={{ background:'transparent', border:0, cursor:'pointer' }}>
          Удалить аккаунт
        </button>
      </div>
    </div>
  )
}

export default ProfilePage
// локальная маска для 10-значного номера (без 8/7 в хранилище)
function formatPhone10(digits: string): string {
  const d = (digits || '').replace(/\D/g, '').slice(0, 10)
  if (!d) return '—'
  const a = d.slice(0, 3)
  const b = d.slice(3, 6)
  const c = d.slice(6, 8)
  const e = d.slice(8, 10)
  let out = '+7(' + a + ')'
  if (b) out += b
  if (c) out += '-' + c
  if (e) out += '-' + e
  return out
}
