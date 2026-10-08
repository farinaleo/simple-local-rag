import { useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import type { AdminTokenData, AdminUser } from '@/hooks/auth'
import {
  useAdminTokens,
  useAdminUsers,
  useChangePassword,
  useCreateAdminUser,
  useDeleteAdminToken,
  useDeleteAdminUser,
  useSession,
  useUpdateAdminToken,
  useUpdateAdminUser,
} from '@/hooks/auth'

function UserAvatar({ user, size = 'md' }: { user: AdminUser; size?: 'md' | 'lg' }) {
  const dimension = size === 'lg' ? 'h-11 w-11' : 'h-9 w-9'
  if (user.avatar_url) {
    return <img src={user.avatar_url} alt="" className={`${dimension} rounded-full object-cover`} />
  }
  return (
    <div
      className={`${dimension} flex shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-violet-600 to-fuchsia-600 text-xs font-bold uppercase text-white`}
    >
      {user.username.slice(0, 2)}
    </div>
  )
}

function sortTokens(tokens: AdminTokenData[], sort: string) {
  const statusOrder: Record<string, number> = { active: 0, paused: 1, expired: 2 }
  return [...tokens].sort((a, b) => {
    if (sort === 'status') return (statusOrder[a.status] ?? 3) - (statusOrder[b.status] ?? 3)
    if (sort === 'user') return a.user.localeCompare(b.user)
    return 0
  })
}

function AdminPage() {
  const { data: session } = useSession()
  const isAdmin = session?.role === 'admin'
  const { data: users, isLoading } = useAdminUsers(isAdmin)
  const { data: tokens, isLoading: tokensLoading } = useAdminTokens(isAdmin)
  const createUser = useCreateAdminUser()
  const updateUser = useUpdateAdminUser()
  const deleteUser = useDeleteAdminUser()
  const changePassword = useChangePassword()
  const updateToken = useUpdateAdminToken()
  const deleteToken = useDeleteAdminToken()
  const [newUsername, setNewUsername] = useState('')
  const [userSearch, setUserSearch] = useState('')
  const [showOwnPassword, setShowOwnPassword] = useState(false)
  const [newPassword, setNewPassword] = useState('')
  const [tokenSearch, setTokenSearch] = useState('')
  const [tokenSort, setTokenSort] = useState('status')

  const filteredUsers = useMemo(() => {
    const query = userSearch.trim().toLowerCase()
    const list = users ?? []
    if (!query) return list
    return list.filter(
      (user) =>
        user.username.toLowerCase().includes(query) ||
        user.display_name.toLowerCase().includes(query),
    )
  }, [users, userSearch])

  const filteredTokens = useMemo(() => {
    const query = tokenSearch.trim().toLowerCase()
    const list = tokens ?? []
    const matched = query
      ? list.filter(
          (token) =>
            token.name.toLowerCase().includes(query) || token.user.toLowerCase().includes(query),
        )
      : list
    return sortTokens(matched, tokenSort)
  }, [tokens, tokenSearch, tokenSort])

  const submitNewUser = async () => {
    const username = newUsername.trim()
    if (!username) return
    try {
      const result = await createUser.mutateAsync({ username, role: 'user' })
      toast.success(
        `Compte ${username} créé — mot de passe temporaire : ${result.temporary_password}`,
      )
      setNewUsername('')
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Erreur inconnue')
    }
  }

  const submitOwnPassword = async () => {
    if (newPassword.length < 8) {
      toast.error('Le mot de passe doit faire au moins 8 caractères')
      return
    }
    try {
      await changePassword.mutateAsync({ new_password: newPassword })
      toast.success('Mot de passe mis à jour')
      setShowOwnPassword(false)
      setNewPassword('')
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Erreur inconnue')
    }
  }

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
      >
        <h2 className="bg-gradient-to-r from-violet-400 to-fuchsia-400 bg-clip-text text-3xl font-bold tracking-tight text-transparent">
          Administration
        </h2>
        <p className="mt-1 text-sm text-zinc-400">Gérez les comptes utilisateurs de votre RAG.</p>
      </motion.div>

      {session?.must_change_password && !showOwnPassword && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-4"
        >
          <p className="text-sm text-amber-200">
            Votre mot de passe est temporaire. Changez-le maintenant.
          </p>
          <Button size="sm" className="mt-2" onClick={() => setShowOwnPassword(true)}>
            Changer mon mot de passe
          </Button>
        </motion.div>
      )}

      {showOwnPassword && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur"
        >
          <div className="flex gap-2">
            <Input
              type="password"
              className="rounded-xl border-white/10 bg-zinc-900/60 text-zinc-100"
              placeholder="Nouveau mot de passe (min. 8 caractères)"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
            />
            <Button
              className="rounded-xl bg-gradient-to-r from-violet-600 to-fuchsia-600"
              onClick={submitOwnPassword}
            >
              Valider
            </Button>
          </div>
        </motion.div>
      )}

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, delay: 0.08 }}
        className="rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur"
      >
        <div className="flex gap-2">
          <Input
            className="rounded-xl border-white/10 bg-zinc-900/60 text-zinc-100"
            placeholder="Nom du nouveau compte utilisateur"
            value={newUsername}
            onChange={(e) => setNewUsername(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && submitNewUser()}
          />
          <Button
            className="rounded-xl bg-gradient-to-r from-violet-600 to-fuchsia-600"
            onClick={submitNewUser}
            disabled={createUser.isPending}
          >
            + Créer
          </Button>
        </div>
        <p className="mt-2 text-xs text-zinc-500">
          Le mot de passe temporaire s'affiche une seule fois ; l'utilisateur le changera à sa
          première connexion.
        </p>
      </motion.div>

      <div className="flex items-center gap-2">
        <Input
          className="max-w-xs rounded-xl border-white/10 bg-zinc-900/60 text-zinc-100"
          placeholder="Rechercher un compte…"
          value={userSearch}
          onChange={(e) => setUserSearch(e.target.value)}
        />
        {userSearch && (
          <span className="text-xs text-zinc-500">
            {filteredUsers.length} résultat{filteredUsers.length > 1 ? 's' : ''}
          </span>
        )}
      </div>

      <div className="space-y-2">
        {isLoading && <p className="text-sm text-zinc-500">Chargement…</p>}
        {filteredUsers.map((user, i) => (
          <motion.div
            key={user.id}
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25, delay: i * 0.03 }}
            className="group flex items-center gap-4 rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur transition-all hover:border-violet-500/40"
          >
            <UserAvatar user={user} />
            <div className="min-w-0 flex-1">
              <p className="truncate font-medium text-zinc-100">{user.display_name}</p>
              <p className="mt-0.5 text-xs text-zinc-400">
                @{user.username} · {user.role === 'admin' ? 'Administrateur' : 'Utilisateur'}
                {!user.is_active && ' · bloqué'}
                {user.must_change_password && ' · mot de passe temporaire'}
              </p>
            </div>
            {user.role !== 'admin' && (
              <>
                <Button
                  variant="ghost"
                  size="sm"
                  className="rounded-lg text-zinc-400 hover:bg-white/10 hover:text-zinc-100"
                  onClick={() =>
                    updateUser
                      .mutateAsync({ id: user.id, reset_password: true })
                      .then((result) =>
                        toast.success(
                          `Nouveau mot de passe temporaire : ${result.temporary_password}`,
                        ),
                      )
                      .catch((error) => toast.error(error.message))
                  }
                >
                  Réinitialiser
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="rounded-lg text-zinc-400 hover:bg-amber-500/15 hover:text-amber-300"
                  onClick={() =>
                    updateUser
                      .mutateAsync({ id: user.id, is_active: !user.is_active })
                      .catch((error) => toast.error(error.message))
                  }
                >
                  {user.is_active ? 'Bloquer' : 'Débloquer'}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="rounded-lg text-zinc-400 hover:bg-red-500/15 hover:text-red-400"
                  onClick={() => {
                    if (!window.confirm(`Supprimer le compte ${user.username} ?`)) return
                    deleteUser.mutateAsync(user.id).catch((error) => toast.error(error.message))
                  }}
                >
                  Supprimer
                </Button>
              </>
            )}
          </motion.div>
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, delay: 0.12 }}
        className="mt-10"
      >
        <h3 className="px-1 text-xs font-semibold uppercase tracking-wider text-zinc-500">
          Tokens API de tous les utilisateurs
        </h3>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <Input
            className="max-w-xs rounded-xl border-white/10 bg-zinc-900/60 text-zinc-100"
            placeholder="Rechercher par token ou utilisateur…"
            value={tokenSearch}
            onChange={(e) => setTokenSearch(e.target.value)}
          />
          <Button
            variant="outline"
            size="sm"
            className="rounded-xl"
            onClick={() => setTokenSort((sort) => (sort === 'status' ? 'user' : 'status'))}
          >
            Tri : {tokenSort === 'status' ? 'statut' : 'créateur'}
          </Button>
        </div>
      </motion.div>
      <div className="mt-2 space-y-2">
        {tokensLoading && <p className="text-sm text-zinc-500">Chargement…</p>}
        {!tokensLoading && filteredTokens.length === 0 && (
          <p className="rounded-2xl border border-dashed border-white/15 p-6 text-center text-sm text-zinc-500">
            Aucun token API ne correspond.
          </p>
        )}
        {filteredTokens.map((token) => (
          <motion.div
            key={token.id}
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25 }}
            className="group flex items-center gap-4 rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur transition-all hover:border-violet-500/40"
          >
            <div className="min-w-0 flex-1">
              <p className="truncate font-medium text-zinc-100">
                {token.name}{' '}
                <span className="text-xs font-normal text-zinc-500">— {token.user}</span>
              </p>
              <p className="mt-0.5 text-xs text-zinc-400">
                {token.scopes.join(', ')} · {token.status}
                {token.last_used_at && ` · dernière utilisation : ${token.last_used_at}`}
              </p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="rounded-lg text-zinc-400 hover:bg-amber-500/15 hover:text-amber-300"
              onClick={() =>
                updateToken
                  .mutateAsync({ id: token.id, is_active: !token.is_active })
                  .catch((error) => toast.error(error.message))
              }
            >
              {token.is_active ? 'Mettre en pause' : 'Reprendre'}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="rounded-lg text-zinc-400 hover:bg-red-500/15 hover:text-red-400"
              onClick={() => {
                if (!window.confirm(`Révoquer le token ${token.name} de ${token.user} ?`)) return
                deleteToken.mutateAsync(token.id).catch((error) => toast.error(error.message))
              }}
            >
              Révoquer
            </Button>
          </motion.div>
        ))}
      </div>
    </div>
  )
}

export default AdminPage
