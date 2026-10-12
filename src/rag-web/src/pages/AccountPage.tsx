import { useRef, useState } from 'react'
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
    <div className="flex items-center gap-4 rounded-lg border bg-card p-4">
      <div className="min-w-0 flex-1">
        <p className="truncate font-medium text-foreground">{token.name}</p>
        <p className="mt-0.5 text-xs text-muted-foreground">
          {token.scopes.join(' · ')} · {token.status}
          {token.last_used_at &&
            ` · utilisé ${new Date(token.last_used_at).toLocaleString('fr-FR')}`}
        </p>
      </div>
      <Button
        variant="ghost"
        size="sm"
        className="rounded-lg text-muted-foreground hover:bg-amber-600/10 hover:text-amber-700"
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
        className="rounded-lg text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
        onClick={() => {
          if (!window.confirm(`Révoquer le token ${token.name} ?`)) return
          deleteToken.mutateAsync(token.id).catch((error) => toast.error(error.message))
        }}
      >
        Révoquer
      </Button>
    </div>
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
      <div>
        <h2 className="text-xl font-semibold tracking-tight">Mon compte</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Gérez votre profil, votre mot de passe et vos tokens API.
        </p>
      </div>

      <div className="rounded-lg border bg-card p-5">
        <div className="flex items-center gap-4">
          <div className="min-w-0 flex-1">
            <p className="font-semibold text-foreground">
              {profile?.display_name ?? session?.username}
            </p>
            <p className="text-xs text-muted-foreground">
              @{profile?.username} · {profile?.role === 'admin' ? 'Administrateur' : 'Utilisateur'}
            </p>
          </div>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-lg border bg-card p-5">
          <h3 className="font-semibold text-foreground">Édition du profil</h3>
          <div className="mt-3 flex items-center gap-3">
            {profile?.avatar_url ? (
              <img
                src={profile.avatar_url}
                alt="avatar"
                className="h-12 w-12 shrink-0 rounded-lg object-cover"
              />
            ) : (
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-sm font-semibold uppercase text-primary">
                {(profile?.username ?? '?').slice(0, 2)}
              </div>
            )}
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
              className="rounded-lg"
              onClick={() => fileInput.current?.click()}
              disabled={updateProfile.isPending}
            >
              Changer la photo
            </Button>
          </div>
          <div className="mt-3 flex gap-2">
            <Input
              className=""
              placeholder="Nom affiché"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && saveDisplayName()}
            />
            <Button
              className="shrink-0 rounded-lg "
              onClick={saveDisplayName}
              disabled={updateProfile.isPending}
            >
              Enregistrer
            </Button>
          </div>
        </div>

        <div className="rounded-lg border bg-card p-5">
          <h3 className="font-semibold text-foreground">Changer mon mot de passe</h3>
          <div className="mt-3 space-y-2">
            <Input
              type="password"
              className=""
              placeholder="Mot de passe actuel"
              value={oldPassword}
              onChange={(e) => setOldPassword(e.target.value)}
            />
            <Input
              type="password"
              className=""
              placeholder="Nouveau mot de passe (min. 8)"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && submitPassword()}
            />
            <Button
              className="w-full rounded-lg "
              onClick={submitPassword}
              disabled={changePassword.isPending}
            >
              Mettre à jour
            </Button>
          </div>
        </div>
      </div>

      <div className="rounded-lg border bg-card p-5">
        <h3 className="font-semibold text-foreground">Tokens API</h3>
        <p className="mt-1 text-xs text-muted-foreground">
          Donnez à un client externe un accès limité à vos données (lecture des documents + chat).
        </p>
        <div className="mt-3 flex gap-2">
          <Input
            className=""
            placeholder="Nom du token (ex : mon-cli)"
            value={tokenName}
            onChange={(e) => setTokenName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && submitToken()}
          />
          <Button className="shrink-0 rounded-lg " onClick={submitToken}>
            + Créer
          </Button>
        </div>
        <div className="mt-3 space-y-2">
          {tokens?.map((token) => (
            <TokenRow key={token.id} token={token} />
          ))}
        </div>
      </div>
    </div>
  )
}

export default AccountPage
