import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import HomeIcon from './assets/icons/home.svg?react'
import DeviceIcon from './assets/icons/televizor.svg?react'
import TicketsIcon from './assets/icons/calendar.svg?react'
import SupportIcon from './assets/icons/support.svg?react'
import ProfileIcon from './assets/icons/profile.svg?react'
import './styles/dashboard.css'  // чтобы стили navbar были доступны везде
import { api } from './shared/api'

type SupportItem = {
  id: string
}
type SupportMessage = {
  author: 'user' | 'support'
  created_at: string
}

export default function App() {
  const { pathname } = useLocation()
  const hideNav = (
    pathname.startsWith('/login') ||
    pathname.startsWith('/register') ||
    pathname.startsWith('/forgot-password') ||
    pathname.startsWith('/tickets/new') ||
    pathname.startsWith('/tickets/success') ||
    pathname.startsWith('/tickets/') || // деталка заявки мастера
    pathname.startsWith('/support/new') ||
    pathname.startsWith('/support/success') ||
    pathname.startsWith('/support/') ||    // деталка обращения
    pathname.startsWith('/profile/delete') || // экран удаления аккаунта
    pathname.startsWith('/subscriptions/pay') ||
    pathname.startsWith('/subscriptions/success') ||
    pathname.startsWith('/subscriptions/denied') ||
    pathname.startsWith('/invoices/pay') ||
    pathname.startsWith('/invoices/success') ||
    pathname.startsWith('/invoices/denied')
  )

  const { data: hasSupportUnread } = useQuery({
    queryKey: ['support', 'unread'],
    queryFn: async () => {
      try {
        const tickets = await api.get<SupportItem[]>('/support/')
        if (!tickets.length) return false
        const results = await Promise.all(
          tickets.map(async (t) => {
            const messages = await api.get<SupportMessage[]>(`/support/${t.id}/messages`)
            const lastSupport = messages
              .filter((m) => m.author === 'support')
              .map((m) => new Date(m.created_at).getTime())
              .reduce((acc, t) => Math.max(acc, t), 0)
            if (!lastSupport) return false
            const lastReadRaw = localStorage.getItem(`support_last_read_${t.id}`)
            const lastRead = lastReadRaw ? new Date(lastReadRaw).getTime() : 0
            return lastSupport > lastRead
          })
        )
        return results.some(Boolean)
      } catch {
        return false
      }
    },
    staleTime: 20_000,
    enabled: !hideNav,
  })

  return (
    <div className={`app${hideNav ? ' app--no-nav' : ''}`}>
      <div className="app-content">
        <Outlet />
      </div>

      {!hideNav && (
      <nav className="navbar-bottom">
        <div className="inner">
          <NavLink to="/" end className={({isActive}) => `item${isActive ? ' active' : ''}`}>
            <HomeIcon className="icon" />
            <span>Главная</span>
          </NavLink>

          <NavLink to="/devices" className={({isActive}) => `item${isActive ? ' active' : ''}`}>
            <DeviceIcon className="icon" />
            <span>Техника</span>
          </NavLink>

          <NavLink to="/tickets" className={({isActive}) => `item${isActive ? ' active' : ''}`}>
            <TicketsIcon className="icon" />
            <span>Заявки</span>
          </NavLink>

          <NavLink to="/support" className={({isActive}) => `item${isActive ? ' active' : ''}`}>
            <span className="nav-icon">
              <SupportIcon className="icon" />
              {hasSupportUnread ? <span className="nav-badge" /> : null}
            </span>
            <span>Поддержка</span>
          </NavLink>

          <NavLink to="/profile" className={({isActive}) => `item${isActive ? ' active' : ''}`}>
            <ProfileIcon className="icon" />
            <span>Профиль</span>
          </NavLink>
        </div>
      </nav>
      )}
    </div>
  )
}
