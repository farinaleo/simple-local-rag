import { motion } from 'framer-motion'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'

import { useLogout, useProfile, useSession } from '@/hooks/auth'
import { useDocuments } from '@/hooks/documents'

const navItems = [
  { to: '/documents', label: 'Documents', icon: '📄' },
  { to: '/chat', label: 'Chats', icon: '💬' },
]
const adminNavItems = [{ to: '/admin', label: 'Administration', icon: '🛡️' }]

function Avatar({
  url,
  name,
  size = 'h-8 w-8',
}: {
  url: string | null
  name: string
  size?: string
}) {
  if (url) {
    return <img src={url} alt="avatar" className={`${size} shrink-0 rounded-full object-cover`} />
  }
  return (
    <div
      className={`${size} flex shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-violet-600 to-fuchsia-600 text-xs font-bold uppercase text-white`}
    >
      {name.slice(0, 2)}
    </div>
  )
}

export default function Layout() {
  const { data: documents } = useDocuments()
  const { data: session } = useSession()
  const { data: profile } = useProfile(!!session)
  const items = [...navItems, ...(session?.role === 'admin' ? adminNavItems : [])]
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

      <div className="relative flex flex-col lg:flex-row">
        <aside className="sticky top-0 z-20 flex shrink-0 items-center justify-between gap-2 border-b border-white/10 bg-zinc-900/60 p-3 backdrop-blur lg:h-screen lg:w-60 lg:flex-col lg:items-stretch lg:justify-start lg:border-b-0 lg:border-r lg:bg-zinc-900/40 lg:p-5">
          <div className="flex shrink-0 items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-violet-600 to-fuchsia-600 text-lg shadow-lg shadow-violet-600/30">
              📚
            </div>
            <div className="hidden lg:block">
              <p className="font-bold tracking-tight">Mon RAG</p>
              <p className="text-[11px] text-zinc-500">Workspace</p>
            </div>
          </div>

          <nav className="flex items-center gap-1 lg:mt-8 lg:flex-col lg:space-y-1.5">
            {items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                title={item.label}
                className={({ isActive }) =>
                  `flex shrink-0 items-center justify-center gap-3 rounded-xl px-3 py-2 text-base transition-all lg:w-full lg:justify-start lg:px-3.5 lg:py-2.5 lg:text-sm lg:font-medium ${
                    isActive
                      ? 'bg-gradient-to-r from-violet-600/25 to-fuchsia-600/25 text-white shadow-inner ring-1 ring-violet-500/30'
                      : 'text-zinc-400 hover:bg-white/5 hover:text-zinc-200'
                  }`
                }
              >
                <span>{item.icon}</span>
                <span className="hidden lg:inline">{item.label}</span>
              </NavLink>
            ))}
          </nav>

          <div className="flex shrink-0 items-center gap-1 lg:mt-auto lg:block lg:space-y-2">
            {session && (
              <>
                <button
                  type="button"
                  className="flex items-center rounded-full transition-transform hover:scale-105 lg:min-w-0 lg:flex-1"
                  title={profile?.display_name ?? session.username}
                  onClick={() => navigate('/account')}
                >
                  <Avatar
                    url={profile?.avatar_url ?? null}
                    name={profile?.username ?? session.username}
                  />
                </button>
                <button
                  type="button"
                  className="rounded-lg px-2 py-1 text-xs text-zinc-400 transition-colors hover:text-red-400 lg:hidden"
                  title="Quitter"
                  onClick={() =>
                    logout.mutate(undefined, {
                      onSuccess: () => navigate('/login'),
                    })
                  }
                >
                  ⎋
                </button>
                <div className="mt-2 hidden items-center gap-2 rounded-2xl border border-white/10 bg-white/5 p-2.5 lg:flex">
                  <button
                    type="button"
                    className="flex min-w-0 flex-1 items-center gap-2 rounded-xl px-1 py-1 text-left transition-colors hover:bg-white/5"
                    title="Mon profil"
                    onClick={() => navigate('/account')}
                  >
                    <Avatar
                      url={profile?.avatar_url ?? null}
                      name={profile?.username ?? session.username}
                    />
                    <span className="min-w-0 flex-1 truncate text-xs font-medium text-zinc-200">
                      {profile?.display_name ?? session.username}
                    </span>
                  </button>
                  <button
                    type="button"
                    className="shrink-0 rounded-lg px-1.5 py-1 text-xs text-zinc-400 transition-colors hover:text-red-400"
                    title="Quitter"
                    onClick={() =>
                      logout.mutate(undefined, {
                        onSuccess: () => navigate('/login'),
                      })
                    }
                  >
                    Quitter
                  </button>
                </div>
              </>
            )}
            <div className="hidden rounded-2xl border border-white/10 bg-white/5 p-3.5 lg:mt-2 lg:block">
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

        <main className="min-w-0 flex-1 p-4 sm:p-6">
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
      className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between"
    >
      <div className="min-w-0">
        <h1 className="bg-gradient-to-r from-violet-400 to-fuchsia-400 bg-clip-text text-2xl font-bold tracking-tight text-transparent sm:text-3xl">
          {title}
        </h1>
        <p className="mt-1 text-sm text-zinc-400">{subtitle}</p>
      </div>
      {action}
    </motion.div>
  )
}
