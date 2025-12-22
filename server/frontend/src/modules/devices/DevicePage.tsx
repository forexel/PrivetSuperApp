import { useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../shared/api'
import '../../styles/devices.css'

type Device = {
  id: string
  user_id: string
  title: string
  brand?: string
  model?: string
  serial_number?: string
  purchase_date?: string
  warranty_until?: string
  created_at: string
  updated_at: string
  photos?: Array<{ id: string; file_url: string; created_at: string }>
}

export function DevicePage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [selectedPhoto, setSelectedPhoto] = useState<string | null>(null)
  const { data, isLoading, error } = useQuery({
    queryKey: ['device', id],
    queryFn: () => api.get<Device>(`/devices/${id}`),
    enabled: !!id,
    retry: false,
  })

  const photos = useMemo(() => {
    return (data?.photos ?? []).slice().sort((a, b) => {
      const ta = new Date(a.created_at || 0).getTime()
      const tb = new Date(b.created_at || 0).getTime()
      return tb - ta
    })
  }, [data?.photos])

  const resolvePhotoUrl = (raw: string) => {
    if (!raw) return ''
    try {
      const url = new URL(raw, window.location.origin)
      if (url.searchParams.has('X-Amz-Signature') || url.searchParams.has('X-Amz-Algorithm')) {
        return url.toString()
      }
      const badHosts = new Set(['localhost', '127.0.0.1', 'infra-minio'])
      if (badHosts.has(url.hostname)) {
        url.hostname = window.location.hostname
      }
      return url.toString()
    } catch {
      return raw
    }
  }

  const resolvedPhotos = useMemo(() => {
    return photos
      .map((p) => ({ ...p, url: resolvePhotoUrl(p.file_url) }))
      .filter((p) => p.url)
  }, [photos])

  const registeredDate = useMemo(() => {
    const raw = data?.created_at
    if (!raw) return '—'
    let d = new Date(raw)
    if (Number.isNaN(d.getTime())) {
      const normalized = raw.replace(' ', 'T')
      d = new Date(normalized)
      if (Number.isNaN(d.getTime()) && !/[zZ]|[+-]\d{2}:\d{2}$/.test(normalized)) {
        d = new Date(`${normalized}Z`)
      }
    }
    return Number.isNaN(d.getTime()) ? '—' : d.toLocaleDateString('ru-RU')
  }, [data?.created_at])

  if (isLoading) {
    return (
      <div className="dashboard device-detail">
        <div className="device-header">
          <button className="device-back" aria-label="Назад" onClick={() => navigate('/devices')} />
          <h1>Описание устройства</h1>
        </div>
        <div className="device-loading">Загрузка…</div>
      </div>
    )
  }
  if (error) {
    return (
      <div className="dashboard device-detail">
        <div className="device-header">
          <button className="device-back" aria-label="Назад" onClick={() => navigate('/devices')} />
          <h1>Описание устройства</h1>
        </div>
        <div className="device-error">Ошибка загрузки</div>
      </div>
    )
  }
  if (!data) {
    return (
      <div className="dashboard device-detail">
        <div className="device-header">
          <button className="device-back" aria-label="Назад" onClick={() => navigate('/devices')} />
          <h1>Описание устройства</h1>
        </div>
        <div className="device-error">Устройство не найдено</div>
      </div>
    )
  }

  return (
    <div className="dashboard device-detail">
      <div className="device-header">
        <button className="device-back" aria-label="Назад" onClick={() => navigate('/devices')} />
        <h1>Описание устройства</h1>
      </div>
      <div className="device-divider" />
      <div className="device-title-lg">{data.title}</div>
      <div className="device-registered">
        Зарегистрирован {registeredDate}
      </div>

      {resolvedPhotos.length > 0 && (
        <div className="device-photos">
          {resolvedPhotos.map((photo) => (
            <button
              key={photo.id}
              type="button"
              className="device-photo-thumb"
              onClick={() => setSelectedPhoto(photo.url)}
            >
              <img src={photo.url} alt="Фото устройства" />
            </button>
          ))}
        </div>
      )}

      <div className="device-description">
        {data.brand && data.model && (
          <div>Модель: {data.brand} {data.model}</div>
        )}
        {data.serial_number && (
          <div>Серийный номер {data.serial_number}</div>
        )}
        {data.purchase_date && (
          <div>Куплен {new Date(data.purchase_date).toLocaleDateString('ru-RU')}</div>
        )}
        {data.warranty_until && (
          <div>Гарантия до {new Date(data.warranty_until).toLocaleDateString('ru-RU')}</div>
        )}
      </div>

      {selectedPhoto && (
        <div
          className="device-photo-modal"
          role="dialog"
          aria-modal="true"
          onClick={(e) => {
            if (e.target === e.currentTarget) setSelectedPhoto(null)
          }}
        >
          <div className="device-photo-modal-inner">
            <button
              type="button"
              className="device-photo-close"
              aria-label="Закрыть"
              onClick={() => setSelectedPhoto(null)}
            />
            <img src={selectedPhoto} alt="Фото устройства" />
          </div>
        </div>
      )}
    </div>
  )
}
