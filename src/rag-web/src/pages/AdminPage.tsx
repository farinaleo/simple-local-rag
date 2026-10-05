import { useState } from 'react'
import { motion } from 'framer-motion'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  useAdminUsers,
  useChangePassword,
  useCreateAdminUser,
  useDeleteAdminUser,
  useUpdateAdminUser,
} from '@/hooks/auth'
import { useSession } from '@/hooks/auth'

function AdminPage() {
  const { data: session } = useSession()
  const { data: users, isLoading } = useAdminUsers(session?.role === 'admin')
  const createUser = useCreateAdminUser()
  const updateUser = useUpdateAdminUser()
  const deleteUser = useDeleteAdminUser()
  const changePassword = useChangePassword()
  const [newUsername, setNewUsername] = useState('')
  const [showOwnPassword, setShowOwnPassword] = useState(false)
  const [newPassword, setNewPassword] = useState('')

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

      <div className="space-y-2">
        {isLoading && <p className="text-sm text-zinc-500">Chargement…</p>}
        {users?.map((user, i) => (
          <motion.div
            key={user.id}
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25, delay: i * 0.03 }}
            className="group flex items-center gap-4 rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur transition-all hover:border-violet-500/40"
          >
            <div className="min-w-0 flex-1">
              <p className="truncate font-medium text-zinc-100">{user.username}</p>
              <p className="mt-0.5 text-xs text-zinc-400">
                {user.role === 'admin' ? 'Administrateur' : 'Utilisateur'}
                {!user.is_active && ' · bloqué'}
                {user.must_change_password && ' · mot de passe temporaire'}
              </p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="rounded-lg text-zinc-400 hover:bg-white/10 hover:text-zinc-100"
              onClick={() =>
                updateUser
                  .mutateAsync({ id: user.id, reset_password: true })
                  .then((result) =>
                    toast.success(`Nouveau mot de passe temporaire : ${result.temporary_password}`),
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
          </motion.div>
        ))}
      </div>
    </div>
  )
}

export default AdminPage
