import { useState } from 'react'
import { motion } from 'framer-motion'
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
    <div className="flex min-h-screen items-center justify-center bg-zinc-950 text-zinc-100">
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-40 left-1/3 h-96 w-96 rounded-full bg-violet-600/20 blur-[128px]" />
        <div className="absolute -bottom-40 right-1/3 h-96 w-96 rounded-full bg-fuchsia-600/15 blur-[128px]" />
      </div>
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
        className="relative w-full max-w-md rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur"
      >
        <h1 className="bg-gradient-to-r from-violet-400 to-fuchsia-400 bg-clip-text text-2xl font-bold tracking-tight text-transparent">
          Changez votre mot de passe
        </h1>
        <p className="mt-2 text-sm text-zinc-400">
          {session?.username
            ? `${session.username}, votre mot de passe est temporaire.`
            : 'Votre mot de passe est temporaire.'}{' '}
          Choisissez-en un nouveau pour continuer à utiliser Mon RAG.
        </p>
        <div className="mt-6 space-y-3">
          <Input
            type="password"
            className="rounded-xl border-white/10 bg-zinc-900/60 text-zinc-100"
            placeholder="Nouveau mot de passe (min. 8 caractères)"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && submit()}
          />
          <Input
            type="password"
            className="rounded-xl border-white/10 bg-zinc-900/60 text-zinc-100"
            placeholder="Confirmez le mot de passe"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && submit()}
          />
        </div>
        <Button
          className="mt-4 w-full rounded-xl bg-gradient-to-r from-violet-600 to-fuchsia-600"
          onClick={submit}
          disabled={changePassword.isPending}
        >
          Valider mon nouveau mot de passe
        </Button>
      </motion.div>
    </div>
  )
}
