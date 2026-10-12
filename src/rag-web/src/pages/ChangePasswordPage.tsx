import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useChangePassword, useSession } from '@/hooks/auth'

export default function ChangePasswordPage() {
  const { data: session } = useSession()
  const changePassword = useChangePassword()
  const navigate = useNavigate()
  const [newPassword, setNewPassword] = useState('')
  const [confirm, setConfirm] = useState('')

  const submit = async () => {
    if (newPassword.length < 8) {
      toast.error('Le mot de passe doit faire au moins 8 caractères')
      return
    }
    if (newPassword !== confirm) {
      toast.error('Les mots de passe ne correspondent pas')
      return
    }
    try {
      await changePassword.mutateAsync({ new_password: newPassword })
      toast.success('Mot de passe mis à jour')
      navigate('/documents')
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Erreur inconnue')
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4 text-foreground">
      <div className="w-full max-w-md rounded-lg border bg-card p-6 shadow-xs">
        <h1 className="text-xl font-semibold tracking-tight">Changez votre mot de passe</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          {session?.username
            ? `${session.username}, votre mot de passe est temporaire.`
            : 'Votre mot de passe est temporaire.'}{' '}
          Choisissez-en un nouveau pour continuer à utiliser Mon RAG.
        </p>
        <div className="mt-6 space-y-3">
          <Input
            type="password"
            className=""
            placeholder="Nouveau mot de passe (min. 8)"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && submit()}
          />
          <Input
            type="password"
            className=""
            placeholder="Confirmez le mot de passe"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && submit()}
          />
        </div>
        <Button
          className="mt-4 w-full rounded-lg "
          onClick={submit}
          disabled={changePassword.isPending}
        >
          Valider mon nouveau mot de passe
        </Button>
      </div>
    </div>
  )
}
