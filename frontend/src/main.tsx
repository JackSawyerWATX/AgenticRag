import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import KnowledgeApp from './KnowledgeApp.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <KnowledgeApp />
  </StrictMode>,
)

