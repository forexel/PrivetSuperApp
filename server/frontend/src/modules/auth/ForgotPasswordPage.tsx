import { Link } from 'react-router-dom'

export function ForgotPasswordPage() {
  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const form = e.currentTarget
    const email = new FormData(form).get('email') as string
    if (!email) return
    try {
      await fetch('/api/v1/auth/forgot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      })
      alert('Если такой email существует, на него отправлено письмо с инструкциями.')
    } catch (_) {}
  }
  return (
    <div className="page-full page-blue">
      <h1 className="auth-hero-title">Привет, супер</h1>

      <div className="card auth-card">
        <h1 className="card-title">Восстановление пароля</h1>

        <form className="form" onSubmit={onSubmit}>
          <div className="form-field">
            <label className="label">Email</label>
            <input name="email" className="input" type="email" placeholder="Email" />
          </div>

          <button className="btn btn-primary" type="submit">Восстановить</button>
        </form>

        <div className="auth-footer">
          <div>
            <Link to="/login">АВТОРИЗАЦИЯ</Link>
          </div>
        </div>
      </div>
    </div>
  )
}