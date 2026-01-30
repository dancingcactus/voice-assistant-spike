import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import './index.css'
import App from './App.tsx'
import { Dashboard } from './components/Dashboard'
import { SimpleTest } from './components/SimpleTest'

// Create React Query client with optimized caching
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Performance optimizations
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30000, // Data is fresh for 30 seconds
      gcTime: 300000, // Keep unused data in cache for 5 minutes

      // UX improvements
      refetchOnReconnect: true,
      networkMode: 'online',
    },
    mutations: {
      retry: 1,
      networkMode: 'online',
    },
  },
})

function Root() {
  const isObservabilityPath = window.location.pathname.startsWith('/observability');

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {!isObservabilityPath && (
          <div style={{
            position: 'fixed',
            top: 10,
            right: 10,
            zIndex: 1000,
            background: '#1a1a1a',
            padding: '0.5rem 1rem',
            borderRadius: '4px',
            border: '1px solid #333'
          }}>
            <Link
              to="/observability"
              style={{
                color: '#4a90e2',
                textDecoration: 'none',
                fontSize: '0.875rem'
              }}
            >
              🔧 Observability Dashboard
            </Link>
          </div>
        )}
        <Routes>
          <Route path="/" element={<App />} />
          <Route path="/observability" element={<Dashboard />} />
          <Route path="/test" element={<SimpleTest />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Root />
  </StrictMode>,
)
