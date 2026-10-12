import { FileText, LogOut, MessageSquare, Menu, Shield, X } from 'lucide-react'
import { AnimatePresence, motion } from 'framer-motion'
import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useLogout, useProfile, useSession } from '@/hooks/auth'
import { useDocuments } from '@/hooks/documents'

const navItems = [
  { to: '/documents', label: 'Documents', icon: FileText },
  { to: '/chat', label: 'Chats', icon: MessageSquare },
]

const adminNavItems = [{ to: '/admin', label: 'Administration', icon: Shield }]

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
      className={`${size} flex shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold uppercase text-primary`}
    >
      {name.slice(0, 2)}
    </div>
  )
}

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const { data: session } = useSession()
  const items = [...navItems, ...(session?.role === 'admin' ? adminNavItems : [])]
  return (
    <nav className="flex flex-col space-y-1">
      {items.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          title={item.label}
          onClick={onNavigate}
          className={({ isActive }) =>
            `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              isActive
                ? 'bg-accent text-accent-foreground'
                : 'text-muted-foreground hover:bg-muted hover:text-foreground'
            }`
          }
        >
          <item.icon className="size-4 shrink-0" aria-hidden />
          <span>{item.label}</span>
        </NavLink>
      ))}
    </nav>
  )
}

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const { data: session } = useSession()
  const { data: profile } = useProfile(!!session)
  const { data: documents } = useDocuments()
  const logout = useLogout()
  const navigate = useNavigate()
  const indexedCount = (documents ?? []).filter((d) => d.status === 'indexed').length
  return (
    <div className="flex h-full flex-col gap-6 p-4">
      <div className="flex items-center gap-2.5 px-1">
        <div className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-primary text-sm font-bold text-primary-foreground">
          R
        </div>
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold tracking-tight">Mon RAG</p>
          <p className="text-[11px] text-muted-foreground">100 % local</p>
        </div>
      </div>
      <NavLinks onNavigate={onNavigate} />
      <p className="mt-auto px-1 text-[11px] leading-relaxed text-muted-foreground">
        <span className="font-semibold text-foreground">
          {indexedCount} fichier{indexedCount > 1 ? 's' : ''}
        </span>{' '}
        indexé{indexedCount > 1 ? 's' : ''} dans votre base.
      </p>
      {session && (
        <div className="flex items-center gap-2 border-t pt-3">
          <button
            type="button"
            className="flex min-w-0 flex-1 items-center gap-2.5 rounded-lg px-1.5 py-1.5 text-left transition-colors hover:bg-muted"
            onClick={() => {
              onNavigate?.()
              navigate('/account')
            }}
          >
            <Avatar
              url={profile?.avatar_url ?? null}
              name={profile?.username ?? session.username}
            />
            <span className="min-w-0 flex-1 truncate text-xs font-medium">
              {profile?.display_name ?? session.username}
            </span>
          </button>
          <button
            type="button"
            className="shrink-0 rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-destructive"
            title="Quitter"
            onClick={() => logout.mutate(undefined, { onSuccess: () => navigate('/login') })}
          >
            <LogOut className="size-4" aria-label="Quitter" />
          </button>
        </div>
      )}
    </div>
  )
}

export default function Layout() {
  const [drawerOpen, setDrawerOpen] = useState(false)
  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="flex">
        {/* Desktop sidebar */}
        <aside className="sticky top-0 hidden h-screen w-60 shrink-0 border-r bg-sidebar lg:block">
          <SidebarContent />
        </aside>
        {/* Mobile drawer */}
        <div className="flex min-w-0 flex-1 flex-col lg:hidden">
          <header className="sticky top-0 z-30 flex items-center justify-between border-b bg-background/95 px-4 py-2.5 backdrop-blur">
            <button
              type="button"
              className="flex items-center gap-2.5 rounded-lg px-1 py-1"
              onClick={() => setDrawerOpen(true)}
              aria-label="Ouvrir le menu"
            >
              <Menu className="size-5" />
            </button>
            <p className="text-sm font-semibold tracking-tight">Mon RAG</p>
            <div className="size-5" aria-hidden />
          </header>
          <main className="min-w-0 flex-1 px-4 py-5">
            <Outlet />
          </main>
        </div>
        {/* Desktop main */}
        <main className="hidden min-w-0 flex-1 px-8 py-6 lg:block">
          <Outlet />
        </main>
      </div>
      <AnimatePresence>
        {drawerOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.15 }}
              className="fixed inset-0 z-40 bg-foreground/20 lg:hidden"
              onClick={() => setDrawerOpen(false)}
            />
            <motion.aside
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ duration: 0.15, ease: 'easeOut' }}
              className="fixed inset-y-0 left-0 z-50 w-64 border-r bg-background shadow-lg lg:hidden"
            >
              <button
                type="button"
                className="absolute right-3 top-3 rounded-lg p-1.5 text-muted-foreground hover:bg-muted"
                onClick={() => setDrawerOpen(false)}
                aria-label="Fermer le menu"
              >
                <X className="size-4" />
              </button>
              <SidebarContent onNavigate={() => setDrawerOpen(false)} />
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}

export function PageTransition({ children }: { children: React.ReactNode }) {
  return <div className="animate-in fade-in duration-150">{children}</div>
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
    <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
      <div className="min-w-0">
        <h1 className="text-base font-semibold tracking-tight">{title}</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">{subtitle}</p>
      </div>
      {action}
    </div>
  )
}
