import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from '@/components/Layout'
import { useSession } from '@/hooks/auth'
import ChatPage from '@/pages/ChatPage'
import DocumentsPage from '@/pages/DocumentsPage'
import LoginPage from '@/pages/LoginPage'

function RequireSession({ children }: { children: React.ReactElement }) {
  const { data: session, isLoading } = useSession()
  if (isLoading) return null
  if (!session) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <RequireSession>
            <Layout />
          </RequireSession>
        }
      >
        <Route path="/" element={<DocumentsPage />} />
        <Route path="/documents" element={<DocumentsPage />} />
        <Route path="/chat" element={<ChatPage />} />
      </Route>
    </Routes>
  )
}
