import { Outlet, NavLink } from 'react-router-dom'
import HomeIcon from './assets/icons/home.svg?react'
import DeviceIcon from './assets/icons/televizor.svg?react'
import TicketsIcon from './assets/icons/calendar.svg?react'
import SupportIcon from './assets/icons/support.svg?react'
import ProfileIcon from './assets/icons/profile.svg?react'
import './styles/dashboard.css'  // чтобы стили navbar были доступны везде

export default function App() {
  return (
    <div className="app">
      <div className="app-content">
        <Outlet />
      </div>

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
            <SupportIcon className="icon" />
            <span>Поддержка</span>
          </NavLink>

          <NavLink to="/profile" className={({isActive}) => `item${isActive ? ' active' : ''}`}>
            <ProfileIcon className="icon" />
            <span>Профиль</span>
          </NavLink>
        </div>
      </nav>
    </div>
  )
}
