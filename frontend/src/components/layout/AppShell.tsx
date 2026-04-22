import { Link, Outlet, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  List,
  Send,
  BarChart2,
  Settings,
  LogOut,
  Server,
  Moon,
  Sun,
} from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { useState } from 'react'
import { cn } from '@/lib/utils'

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/jobs', label: 'Jobs', icon: List },
  { to: '/submit', label: 'Submit Job', icon: Send },
  { to: '/analytics', label: 'Analytics', icon: BarChart2 },
]

const adminItems = [
  { to: '/admin', label: 'Admin', icon: Settings },
]

export default function AppShell() {
  const { logout, isAdmin, username } = useAuth()
  const location = useLocation()
  const [dark, setDark] = useState(() =>
    document.documentElement.classList.contains('dark')
  )

  function toggleDark() {
    document.documentElement.classList.toggle('dark')
    setDark((d) => !d)
  }

  return (
    <div className="flex h-screen bg-background text-foreground">
      {/* Sidebar */}
      <aside className="w-56 flex-shrink-0 border-r border-border flex flex-col">
        {/* Logo */}
        <div className="h-14 flex items-center px-4 border-b border-border font-bold text-lg tracking-tight">
          <Server className="w-5 h-5 mr-2 text-primary" />
          slurm++
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-1">
          {navItems.map(({ to, label, icon: Icon }) => (
            <Link
              key={to}
              to={to}
              className={cn(
                'flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                location.pathname === to
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
              )}
            >
              <Icon className="w-4 h-4" />
              {label}
            </Link>
          ))}

          {isAdmin && (
            <>
              <div className="pt-3 pb-1 px-3 text-xs text-muted-foreground uppercase tracking-wide">Admin</div>
              {adminItems.map(({ to, label, icon: Icon }) => (
                <Link
                  key={to}
                  to={to}
                  className={cn(
                    'flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                    location.pathname.startsWith(to)
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                  )}
                >
                  <Icon className="w-4 h-4" />
                  {label}
                </Link>
              ))}
            </>
          )}
        </nav>

        {/* Footer */}
        <div className="border-t border-border px-4 py-3 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground truncate">{username}</span>
            <div className="flex items-center gap-1">
              <button
                onClick={toggleDark}
                className="p-1 rounded hover:bg-accent"
                title="Toggle theme"
              >
                {dark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
              </button>
              <button
                onClick={logout}
                className="p-1 rounded hover:bg-accent text-muted-foreground"
                title="Logout"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
