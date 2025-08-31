import React, { useEffect, useRef, useState } from 'react'
// @ts-ignore react-hook-form types mismatch; rely on runtime export
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { useNavigate, Link } from 'react-router-dom'

// lightweight fetch client with auth header
const api = {
  async post<T = any>(url: string, body: any): Promise<{ data: T }> {
    const token = typeof localStorage !== 'undefined' ? localStorage.getItem('access_token') : null
    const r = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(body ?? {}),
    })
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    return { data: (await r.json()) as T }
  },
}

// === phone helpers ===
const onlyDigits = (s: string) => s.replace(/\D/g, '')
function clamp10(d: string) { return d.slice(0, 10) }
function normalizeTo10(raw: string) {
  let d = onlyDigits(raw)
  if (d.startsWith('8')) d = d.slice(1)
  else if (d.startsWith('7')) d = d.slice(1)
  return clamp10(d)
}
function formatFromDigits(d: string) {
  d = clamp10(d)
  const a = d.slice(0, 3)
  const b = d.slice(3, 6)
  const c = d.slice(6, 8)
  const e = d.slice(8, 10)
  let out = '+7(' + a
  if (d.length >= 3) out += ')'
  if (b) out += b
  if (c) out += '-' + c
  if (e) out += '-' + e
  return out
}

const schema = z.object({
  name: z.string().min(1, 'Введите имя'),
  email: z.string().email('Введите корректный email'),
  phone: z.string().min(10, 'Введите телефон'),
  password: z.string().min(8, 'Минимум 8 символов'),
})

type FormValues = z.infer<typeof schema>

export function RegisterPage() {
  const navigate = useNavigate()
  const { register, handleSubmit, setValue, setError, clearErrors, formState: { errors, isSubmitting, isSubmitted } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    mode: 'onSubmit',
    reValidateMode: 'onChange',
    defaultValues: { name: '', email: '', phone: '', password: '' },
  })

  const [submitError, setSubmitError] = useState<string>('')

  const [digits, setDigits] = useState<string>('')
  const inputRef = useRef<HTMLInputElement | null>(null)
  const uiPhone = formatFromDigits(digits)

  useEffect(() => {
    setValue('phone', digits, { shouldValidate: isSubmitted, shouldDirty: true })
  }, [digits, setValue, isSubmitted])

  const onPhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const nextDigits = normalizeTo10(e.target.value)
    setDigits(nextDigits)
  }

  const onPhoneKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace') {
      const el = inputRef.current
      if (!el) return
      const selStart = el.selectionStart ?? uiPhone.length
      const selEnd = el.selectionEnd ?? uiPhone.length
      if (selStart === selEnd && selEnd === uiPhone.length) {
        e.preventDefault()
        if (digits.length > 0) setDigits(digits.slice(0, -1))
      }
    }
  }

  const onSubmit = async (data: FormValues) => {
    setSubmitError('')
    clearErrors()
    const payload = { name: data.name, email: data.email, phone: digits, password: data.password }
    try {
      // регистрируем
      await api.post('/api/v1/auth/register', payload)
      // логинимся сразу после регистрации
      const loginResp = await api.post('/api/v1/auth/login', {
        phone: digits,
        password: data.password,
      })
      const token = (loginResp as any)?.data?.access_token || (loginResp as any)?.data?.token || (loginResp as any)?.data?.accessToken
      if (!token) throw new Error('Нет access_token в ответе')
      localStorage.setItem('access_token', token)
      navigate('/')
    } catch (e: any) {
      console.error('Registration error', e)
      const detail = e?.response?.data?.detail

      const pushFieldError = (field: keyof FormValues, msg: string) => {
        setError(field, { type: 'server', message: msg })
      }

      let fallback: string | null = null

      if (typeof detail === 'string') {
        fallback = detail
      } else if (Array.isArray(detail)) {
        let anyField = false
        for (const it of detail) {
          const msg = it?.msg || 'некорректное значение'
          const loc: any[] = Array.isArray(it?.loc) ? it.loc : []
          const field = (loc[1] as string) || ''
          if (field === 'name') { anyField = true; pushFieldError('name', msg) }
          else if (field === 'email') { anyField = true; pushFieldError('email', msg) }
          else if (field === 'phone') { anyField = true; pushFieldError('phone', msg) }
          else if (field === 'password') { anyField = true; pushFieldError('password', msg) }
        }
        if (!anyField) {
          fallback = detail.map((it: any) => it?.msg || 'Ошибка').join('\n')
        }
      } else if (detail && typeof detail === 'object') {
        fallback = (detail as any).msg || JSON.stringify(detail)
      } else if (e?.message) {
        fallback = e.message
      }

      if (fallback) setSubmitError(fallback)
    }
  }

  return (
    <div className="page-full page-blue">
      <h1 className="auth-hero-title">Привет, Супер</h1>
      <div className="card auth-card">
        <h1 className="card-title">Регистрация</h1>
        {submitError && (
          <div style={{ color: 'red', marginBottom: 12, textAlign: 'center' }}>{submitError}</div>
        )}
        <form onSubmit={handleSubmit(onSubmit)} className="form">
          <div className="form-field">
            <label className="label">Имя</label>
            <input className="input" placeholder="Иван" {...register('name')} />
            {errors.name && <small style={{ color: 'red' }}>{errors.name.message}</small>}
          </div>
          <div className="form-field">
            <label className="label">Телефон</label>
            <input
              {...register('phone')}
              ref={inputRef}
              className="input"
              type="tel"
              data-phone="ru"
              autoComplete="tel"
              placeholder="+7("
              value={uiPhone}
              onChange={onPhoneChange}
              onKeyDown={onPhoneKeyDown}
            />
            {errors.phone && <small style={{ color: 'red' }}>{errors.phone.message}</small>}
          </div>
          <div className="form-field">
            <label className="label">Email</label>
            <input className="input" placeholder="Email" {...register('email')} />
            {errors.email && <small style={{ color: 'red' }}>{errors.email.message}</small>}
          </div>
          <div className="form-field">
            <label className="label">Пароль</label>
            <input className="input" type="password" placeholder="Минимум 8 символов" {...register('password')} />
            {errors.password && <small style={{ color: 'red' }}>{errors.password.message}</small>}
          </div>
          <button className="btn btn-primary" disabled={isSubmitting}>Зарегистрироваться</button>
        </form>
        <div className="auth-footer">
          <div>
            Уже есть аккаунт? <Link to="/login">Войти</Link>
          </div>
        </div>
      </div>
    </div>
  )
}