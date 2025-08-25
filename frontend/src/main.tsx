import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { useMutation, QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App.tsx'
const queryClient = new QueryClient();

// Wrapper to provide QueryClient

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
    <App />
    </QueryClientProvider>
  </StrictMode>,
)
