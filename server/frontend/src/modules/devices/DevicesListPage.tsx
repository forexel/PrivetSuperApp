import { useQuery } from '@tanstack/react-query'
import { api } from '../../shared/api'
import '../../styles/dashboard.css'
import '../../styles/devices.css'

type DeviceListItem = { id: string; title: string; created_at?: string }

export function DevicesListPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['devices', 'list'],
    queryFn: () => api.get<DeviceListItem[]>('/devices/my'),
    retry: false,
  })

  return (
    <div className="dashboard">
      <h1>Моя техника</h1>

      {isLoading && (
        <div className="empty-state">
          <div className="empty-box">Загрузка…</div>
        </div>
      )}

      {!isLoading && error && (
        <div className="empty-state">
          <div className="empty-box">
            <div className="empty-title" style={{ color: 'red' }}>Ошибка</div>
            <div className="empty-text">{(error as any).message}</div>
          </div>
        </div>
      )}

      {!isLoading && !error && (data ?? []).length === 0 && (
        <div className="empty-state">
          <div className="empty-box">
            <div className="empty-title">Пока тут пусто</div>
            <div className="empty-text">
              Тут появятся ваши устройства, когда их зарегистрируем
            </div>
          </div>
        </div>
      )}

      {!isLoading && !error && (data ?? []).length > 0 && (
        <div className="device-list">
          {(data ?? []).map((d) => (
            <button
              type="button"
              key={d.id}
              className="device-card"
              onClick={() => window.location.assign(`/devices/${d.id}`)}
            >
              <div className="device-title">{d.title}</div>
              <div className="device-meta">
                зарегистрирован {d.created_at ? new Date(d.created_at).toLocaleDateString('ru-RU') : '—'}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
