import { motion } from 'framer-motion'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useLogin, useRegister } from '@/hooks/auth'

export default function LoginPage() {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const login = useLogin()
  const register = useRegister()
  const navigate = useNavigate()

  const submit = async () => {
    if (!username.trim() || !password.trim()) return
    try {
      if (mode === 'login') {
        await login.mutateAsync({ username, password })
        toast.success(`Bienvenue ${username} !`)
      } else {
        await register.mutateAsync({ username, password })
        toast.success(`Compte ${username} créé !`)
      }
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
        className="relative w-full max-w-sm rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur"
      >
        <div className="mb-6 flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-violet-600 to-fuchsia-600 text-xl shadow-lg shadow-violet-600/30">
            📚
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight">Mon RAG</h1>
            <p className="text-xs text-zinc-500">
              {mode === 'login' ? 'Connectez-vous' : 'Créez votre compte'}
            </p>
          </div>
        </div>

        <form
          className="space-y-3"
          onSubmit={(event) => {
            event.preventDefault()
            void submit()
          }}
        >
          <Input
            className="rounded-xl border-white/10 bg-zinc-900/60 text-zinc-100 placeholder:text-zinc-500 focus-visible:ring-violet-500/50"
            placeholder="Nom d'utilisateur"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            autoFocus
          />
          <Input
            className="rounded-xl border-white/10 bg-zinc-900/60 text-zinc-100 placeholder:text-zinc-500 focus-visible:ring-violet-500/50"
            type="password"
            placeholder="Mot de passe"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
          <Button
            type="submit"
            className="w-full rounded-xl bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white shadow-lg shadow-violet-600/25 transition-transform hover:scale-[1.02] hover:from-violet-500 hover:to-fuchsia-500"
            disabled={login.isPending || register.isPending}
          >
            {mode === 'login' ? 'Se connecter' : 'Créer mon compte'}
          </Button>
        </form>

        <button
          type="button"
          className="mt-4 w-full text-center text-xs text-zinc-400 transition-colors hover:text-zinc-200"
          onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
        >
          {mode === 'login' ? 'Pas de compte ? Créez-en un' : 'Déjà un compte ? Connectez-vous'}
        </button>
      </motion.div>
    </div>
  )
}
