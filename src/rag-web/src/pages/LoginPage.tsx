import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useLogin } from '@/hooks/auth'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const login = useLogin()
  const navigate = useNavigate()
  const submit = async () => {
    if (!username.trim() || !password.trim()) return
    try {
      await login.mutateAsync({ username, password })
      toast.success(`Bienvenue ${username} !`)
      navigate('/documents')
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Erreur inconnue')
    }
  }
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4 text-foreground">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex size-11 items-center justify-center rounded-xl bg-primary text-base font-bold text-primary-foreground">
            R
          </div>
          <h1 className="text-[22px] font-semibold tracking-tight">Mon RAG</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Vos documents, vos questions — en local.
          </p>
        </div>
        <form
          className="space-y-4 rounded-xl border bg-card p-6 shadow-xs"
          onSubmit={(event) => {
            event.preventDefault()
            void submit()
          }}
        >
          <label className="block space-y-1.5">
            <span className="text-xs font-medium text-foreground">Nom d&apos;utilisateur</span>
            <Input
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              autoFocus
              autoComplete="username"
            />
          </label>
          <label className="block space-y-1.5">
            <span className="text-xs font-medium text-foreground">Mot de passe</span>
            <Input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
            />
          </label>
          <Button type="submit" className="w-full" disabled={login.isPending}>
            Se connecter
          </Button>
        </form>
        <p className="mt-4 text-center text-xs text-muted-foreground">
          Les comptes sont créés par un administrateur.
        </p>
      </div>
    </div>
  )
}
