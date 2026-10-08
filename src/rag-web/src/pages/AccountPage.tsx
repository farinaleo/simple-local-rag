import { useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  useChangePasswordSecure,
  useCreateToken,
  useDeleteToken,
  useProfile,
  useSession,
  useTokens,
  useUpdateProfile,
  useUpdateToken,
} from '@/hooks/auth'

function TokenRow({ token }: { token: TokenEntry }) {
  const updateToken = useUpdateToken()
  const deleteToken = useDeleteToken()
  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-center gap-4 rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur"
    >
      <div className="min-w-0 flex-1">
        <p className="truncate font-medium text-zinc-100">{token.name}</p>
        <p className="mt-0.5 text-xs text-zinc-400">
          {token.scopes.join(' · ')} · {token.status}
          {token.last_used_at &&
            ` · utilisé ${new Date(token.last_used_at).toLocaleString('fr-FR')}`}
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
          if (!window.confirm(`Révoquer le token ${token.name} ?`)) return
          deleteToken.mutateAsync(token.id).catch((error) => toast.error(error.message))
        }}
      >
        Révoquer
      </Button>
    </motion.div>
  )
}

interface TokenEntry {
  id: number
  name: string
  scopes: string[]
  created_at: string
  last_used_at: string | null
  is_active: boolean
  expires_at: string | null
  expired: boolean
  status: string
}

function AccountPage() {
  const { data: session } = useSession()
  const { data: profile } = useProfile(!!session)
  const updateProfile = useUpdateProfile()
  const changePassword = useChangePasswordSecure()
  const { data: tokens } = useTokens(!!session)
  const createToken = useCreateToken()
  const [displayName, setDisplayName] = useState('')
  const [oldPassword, setOldPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [tokenName, setTokenName] = useState('')
  const fileInput = useRef<HTMLInputElement>(null)

  const saveDisplayName = async () => {
    try {
      await updateProfile.mutateAsync({ display_name: displayName })
      toast.success('Nom affiché mis à jour')
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Erreur inconnue')
    }
  }

  const uploadAvatar = async (file: File) => {
    try {
      await updateProfile.mutateAsync({ avatar: file })
      toast.success('Photo de profil mise à jour')
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Erreur inconnue')
    }
  }

  const submitPassword = async () => {
    if (newPassword.length < 8) {
      toast.error('Le nouveau mot de passe doit faire au moins 8 caractères')
      return
    }
    try {
      await changePassword.mutateAsync({ old_password: oldPassword, new_password: newPassword })
      toast.success('Mot de passe mis à jour — autres sessions déconnectées')
      setOldPassword('')
      setNewPassword('')
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Erreur inconnue')
    }
  }

  const submitToken = async () => {
    const name = tokenName.trim()
    if (!name) return
    try {
      const result = await createToken.mutateAsync({ name, scopes: ['documents:read', 'query'] })
      toast.success(`Token créé — copiez-le maintenant : ${result.token}`)
      setTokenName('')
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
          Mon compte
        </h2>
        <p className="mt-1 text-sm text-zinc-400">
          Gérez votre profil, votre mot de passe et vos tokens API.
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, delay: 0.08 }}
        className="rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur"
      >
        <div className="flex items-center gap-4">
          {profile?.avatar_url ? (
            <img
              src={profile.avatar_url}
              alt="avatar"
              className="h-16 w-16 rounded-2xl object-cover"
            />
          ) : (
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-600 to-fuchsia-600 text-xl font-bold uppercase text-white">
              {(profile?.username ?? '?').slice(0, 2)}
            </div>
          )}
          <div className="min-w-0 flex-1">
            <p className="font-semibold text-zinc-100">
              {profile?.display_name ?? session?.username}
            </p>
            <p className="text-xs text-zinc-400">
              @{profile?.username} · {profile?.role === 'admin' ? 'Administrateur' : 'Utilisateur'}
            </p>
          </div>
          <input
            ref={fileInput}
            type="file"
            accept="image/png,image/jpeg"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) uploadAvatar(file)
            }}
          />
          <Button
            variant="outline"
            size="sm"
            className="rounded-xl"
            onClick={() => fileInput.current?.click()}
          >
            Changer la photo
          </Button>
        </div>
      </motion.div>

      <div className="grid gap-6 md:grid-cols-2">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, delay: 0.12 }}
          className="rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur"
        >
          <h3 className="font-semibold text-zinc-100">Édition du profil</h3>
          <div className="mt-3 flex gap-2">
            <Input
              className="rounded-xl border-white/10 bg-zinc-900/60 text-zinc-100"
              placeholder="Nom affiché"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && saveDisplayName()}
            />
            <Button
              className="shrink-0 rounded-xl bg-gradient-to-r from-violet-600 to-fuchsia-600"
              onClick={saveDisplayName}
              disabled={updateProfile.isPending}
            >
              Enregistrer
            </Button>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, delay: 0.16 }}
          className="rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur"
        >
          <h3 className="font-semibold text-zinc-100">Changer mon mot de passe</h3>
          <div className="mt-3 space-y-2">
            <Input
              type="password"
              className="rounded-xl border-white/10 bg-zinc-900/60 text-zinc-100"
              placeholder="Mot de passe actuel"
              value={oldPassword}
              onChange={(e) => setOldPassword(e.target.value)}
            />
            <Input
              type="password"
              className="rounded-xl border-white/10 bg-zinc-900/60 text-zinc-100"
              placeholder="Nouveau mot de passe (min. 8)"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && submitPassword()}
            />
            <Button
              className="w-full rounded-xl bg-gradient-to-r from-violet-600 to-fuchsia-600"
              onClick={submitPassword}
              disabled={changePassword.isPending}
            >
              Mettre à jour
            </Button>
          </div>
        </motion.div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, delay: 0.2 }}
        className="rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur"
      >
        <h3 className="font-semibold text-zinc-100">Tokens API</h3>
        <p className="mt-1 text-xs text-zinc-500">
          Donnez à un client externe un accès limité à vos données (lecture des documents + chat).
        </p>
        <div className="mt-3 flex gap-2">
          <Input
            className="rounded-xl border-white/10 bg-zinc-900/60 text-zinc-100"
            placeholder="Nom du token (ex : mon-cli)"
            value={tokenName}
            onChange={(e) => setTokenName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && submitToken()}
          />
          <Button
            className="shrink-0 rounded-xl bg-gradient-to-r from-violet-600 to-fuchsia-600"
            onClick={submitToken}
          >
            + Créer
          </Button>
        </div>
        <div className="mt-3 space-y-2">
          {tokens?.map((token) => (
            <TokenRow key={token.id} token={token} />
          ))}
        </div>
      </motion.div>
    </div>
  )
}

export default AccountPage
