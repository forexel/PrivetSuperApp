import { Link } from 'react-router-dom'
import { useState } from 'react'

export function ForgotPasswordPage() {
  const [sent, setSent] = useState(false)
  const [loading, setLoading] = useState(false)

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const form = e.currentTarget
    const email = new FormData(form).get('email') as string
    if (!email || sent) return
    try {
      setLoading(true)
      await fetch('/api/v1/auth/forgot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      })
      setSent(true)
    } catch (_) {
      // Даже при ошибке не раскрываем детали: показываем такое же сообщение
      setSent(true)
    } finally {
      setLoading(false)
    }
  }
  return (
    <div className="page-full page-blue">
      <h1 className="auth-hero-title">Привет, супер</h1>

      <div className="card auth-card">
        <h1 className="card-title">Восстановление пароля</h1>

        {!sent ? (
          <form className="form" onSubmit={onSubmit}>
            <div className="form-field">
              <label className="label">Email</label>
              <input name="email" className="input" type="email" placeholder="Email" disabled={loading} />
            </div>

            <button className="btn btn-primary" type="submit" disabled={loading}>Восстановить</button>
          </form>
        ) : (
          <div className="success-text">Письмо с новым паролем отправлено</div>
        )}

        <div className="auth-footer">
          <div>
            <Link to="/login">АВТОРИЗАЦИЯ</Link>
          </div>
        </div>
      </div>
    </div>
  )
}
