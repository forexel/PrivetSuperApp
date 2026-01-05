// @ts-ignore react-hook-form types mismatch; rely on runtime export
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { api } from '../../shared/api'
import { setAppStatus } from '../../shared/appStatus'
import '../../styles/forms.css'
import { CloseFloating } from '../../shared/ui/CloseFloating'

const schema = z.object({
  title: z.string().min(1, 'Укажите тему'),
  description: z.string().optional(),
})
type FormValues = z.infer<typeof schema>

export function TicketCreatePage() {
  const { register, handleSubmit, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { title: '', description: '' },
  })
  const [photos, setPhotos] = useState<File[]>([])
  const [uploadError, setUploadError] = useState('')

  const navigate = useNavigate()
  const qc = useQueryClient()

  // API-вызов создания
  type CreatedTicket = {
    id: string
    title: string
    status: 'new' | 'in_progress' | 'completed' | 'reject'
    created_at: string
  }
  const createTicket = async (payload: FormValues & { attachment_urls: string[] }) => {
    const created = await api.post<CreatedTicket>('/tickets/', payload)
    return created
  }

  // Мутация + обновление кэша
  const mutation = useMutation({
    mutationFn: createTicket,
    onSuccess: (created) => {
      // мгновенно подставляем в список пользователя
      qc.setQueryData<any[]>(['tickets', 'my'], (old) =>
        old ? [created, ...old] : [created]
      )

      // а затем всё равно перезагрузим оба ключа
      qc.invalidateQueries({ queryKey: ['tickets', 'my'] })
      qc.invalidateQueries({ queryKey: ['tickets'] })

      navigate('/tickets/success', { replace: true })
    },
  })

  const uploadPhoto = async (file: File) => {
    const form = new FormData()
    form.append('file', file, file.name)
    const send = async (token?: string | null) => {
      return fetch('/api/v1/uploads/direct', {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        body: form,
      })
    }
    let token = localStorage.getItem('access_token')
    let res: Response
    try {
      res = await send(token)
    } catch (error) {
      if (typeof navigator !== 'undefined' && !navigator.onLine) {
        setAppStatus('offline')
      } else {
        setAppStatus('server')
      }
      throw error
    }
    if (res.status === 401) {
      const refresh = localStorage.getItem('refresh_token')
      if (refresh) {
        const refreshRes = await fetch('/api/v1/auth/refresh', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refresh }),
        })
        if (refreshRes.ok) {
          const data = await refreshRes.json()
          if (data?.access_token) {
            localStorage.setItem('access_token', data.access_token)
            if (data?.refresh_token) localStorage.setItem('refresh_token', data.refresh_token)
            token = data.access_token
            try {
              res = await send(token)
            } catch (error) {
              if (typeof navigator !== 'undefined' && !navigator.onLine) {
                setAppStatus('offline')
              } else {
                setAppStatus('server')
              }
              throw error
            }
          }
        }
      }
    }
    if (!res.ok) {
      if (res.status >= 500) setAppStatus('server')
      throw new Error('upload failed')
    }
    const json = await res.json()
    return json.file_key as string
  }

  const onSelectPhotos = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    const next = [...photos, ...files].slice(0, 2)
    setPhotos(next)
    e.target.value = ''
  }

  const removePhoto = (index: number) => {
    setPhotos((prev) => prev.filter((_, i) => i !== index))
  }

  const onSubmit = async (data: FormValues) => {
    setUploadError('')
    try {
      const attachment_urls: string[] = []
      for (const file of photos) {
        const key = await uploadPhoto(file)
        attachment_urls.push(key)
      }
      mutation.mutate({ ...data, attachment_urls })
    } catch {
      setUploadError('Не удалось загрузить фото')
    }
  }

  return (
    <div className="page-blue page-blue--ticket">
      <div className="modal-wrap modal-wrap--ticket">
        <div className="ticket-create-header">
          <span className="ticket-create-spacer" aria-hidden />
          <h2 className="ticket-create-title">Оформление заявки</h2>
          <CloseFloating
            className="ticket-create-close"
            onClick={() => (window.history.length > 1 ? navigate(-1) : navigate('/tickets', { replace: true }))}
          />
        </div>

        <div className="card auth-card">

          <form className="form form--wide ticket-form" onSubmit={handleSubmit(onSubmit)}>
          <div className="form-field">
            <div className="label">Что сломалось?</div>
            <input
              className="input"
              placeholder="Укажи кратко в чем проблема?"
              aria-invalid={!!errors.title}
              {...register('title', { required: 'Укажите тему' })}
            />
            {errors.title && (
              <p className="error" role="alert">{errors.title.message}</p>
            )}
          </div>

          <div className="form-field">
            <div className="label">Подробное описание</div>
            <textarea
              className="input input-area"
              placeholder="Опишите подробно"
              rows={5}
              aria-invalid={!!errors.description}
              {...register('description')}
            />
            {errors.description && (
              <p className="error" role="alert">{errors.description.message}</p>
            )}
          </div>

          <div className="form-field">
            <div className="label">Фото при наличии</div>
            <div className="ticket-photos">
              {photos.map((file, idx) => (
                <div className="ticket-photo" key={`${file.name}-${idx}`}>
                  <img src={URL.createObjectURL(file)} alt="Фото" />
                  <button type="button" onClick={() => removePhoto(idx)}>×</button>
                </div>
              ))}
              {photos.length < 2 && (
                <label className="ticket-photo-add">
                  <input type="file" accept="image/*" onChange={onSelectPhotos} />
                  <span>+</span>
                  <small>Добавить фото</small>
                </label>
              )}
            </div>
            {uploadError && <p className="error" role="alert">{uploadError}</p>}
          </div>

          <button className="btn btn-primary" disabled={mutation.isPending}>
            Отправить заявку
          </button>

          {mutation.isError && (
            <p className="error" role="alert">
              Не удалось создать заявку. Попробуйте ещё раз.
            </p>
          )}
        </form>
      </div>
      </div>
    </div>
  )
}
