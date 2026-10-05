import { motion } from 'framer-motion'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'

import { useLogout, useSession } from '@/hooks/auth'
import { useDocuments } from '@/hooks/documents'

const navItems = [
  { to: '/documents', label: 'Documents', icon: '📄' },
  { to: '/chat', label: 'Chats', icon: '💬' },
]
const adminNavItems = [{ to: '/admin', label: 'Administration', icon: '🛡️' }]

export default function Layout() {
  const { data: documents } = useDocuments()
  const { data: session } = useSession()
  const items = session?.role === 'admin' ? [...navItems, ...adminNavItems] : navItems
  const logout = useLogout()
  const navigate = useNavigate()
  const indexedCount = (documents ?? []).filter((d) => d.status === 'indexed').length

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      {/* halo décoratif */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-40 left-1/4 h-96 w-96 rounded-full bg-violet-600/20 blur-[128px]" />
        <div className="absolute -bottom-40 right-1/4 h-96 w-96 rounded-full bg-fuchsia-600/15 blur-[128px]" />
      </div>

      <div className="relative flex">
        <aside className="sticky top-0 flex h-screen w-60 shrink-0 flex-col border-r border-white/10 bg-zinc-900/40 p-5 backdrop-blur">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-violet-600 to-fuchsia-600 text-lg shadow-lg shadow-violet-600/30">
              📚
            </div>
            <div>
              <p className="font-bold tracking-tight">Mon RAG</p>
              <p className="text-[11px] text-zinc-500">Workspace</p>
            </div>
          </div>

          <nav className="mt-8 space-y-1.5">
            {items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex w-full items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-gradient-to-r from-violet-600/25 to-fuchsia-600/25 text-white shadow-inner ring-1 ring-violet-500/30'
                      : 'text-zinc-400 hover:bg-white/5 hover:text-zinc-200'
                  }`
                }
              >
                <span className="text-base">{item.icon}</span>
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="mt-auto space-y-2">
            {session && (
              <div className="flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 p-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-violet-600 to-fuchsia-600 text-xs font-bold uppercase text-white">
                  {session.username.slice(0, 2)}
                </div>
                <p className="min-w-0 flex-1 truncate text-xs font-medium text-zinc-200">
                  {session.username}
                </p>
                <button
                  type="button"
                  className="text-xs text-zinc-400 transition-colors hover:text-red-400"
                  onClick={() =>
                    logout.mutate(undefined, {
                      onSuccess: () => navigate('/login'),
                    })
                  }
                >
                  Quitter
                </button>
              </div>
            )}
            <div className="rounded-2xl border border-white/10 bg-white/5 p-3.5">
              <p className="text-[11px] leading-relaxed text-zinc-400">
                <span className="font-semibold text-zinc-200">
                  {indexedCount} fichier{indexedCount > 1 ? 's' : ''}
                </span>{' '}
                indexé{indexedCount > 1 ? 's' : ''} dans votre base. Vos conversations s'appuient
                sur ces documents.
              </p>
            </div>
          </div>
        </aside>

        <main className="min-w-0 flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export function PageTransition({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.25 }}
    >
      {children}
    </motion.div>
  )
}

export function PageHeader({
  title,
  subtitle,
  action,
}: {
  title: string
  subtitle: string
  action?: React.ReactNode
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="flex items-end justify-between"
    >
      <div>
        <h1 className="bg-gradient-to-r from-violet-400 to-fuchsia-400 bg-clip-text text-3xl font-bold tracking-tight text-transparent">
          {title}
        </h1>
        <p className="mt-1 text-sm text-zinc-400">{subtitle}</p>
      </div>
      {action}
    </motion.div>
  )
}
