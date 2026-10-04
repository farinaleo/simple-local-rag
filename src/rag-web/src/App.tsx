import { Route, Routes } from 'react-router-dom'
import Layout from '@/components/Layout'
import ChatPage from '@/pages/ChatPage'
import DocumentsPage from '@/pages/DocumentsPage'
import StyleDemoPage from '@/pages/StyleDemoPage'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<DocumentsPage />} />
        <Route path="/documents" element={<DocumentsPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/style-demo" element={<StyleDemoPage />} />
      </Route>
    </Routes>
  )
}
