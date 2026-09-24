import { useEffect } from 'react'
import { createBrowserRouter, Navigate, Outlet, RouterProvider, useLocation, useNavigate } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Spinner } from './components/Spinner'
import { AuthProvider, useAuth } from './context/AuthContext'
import { AnswerPage } from './pages/AnswerPage'
import { AssessmentEditorPage } from './pages/AssessmentEditorPage'
import { AssessmentsPage } from './pages/AssessmentsPage'
import { CorrectionPage } from './pages/CorrectionPage'
import { ErrorPage } from './pages/ErrorPage'
import { LoginPage } from './pages/LoginPage'
import { ReviewPage } from './pages/ReviewPage'

function SessionGuard() { const { user, loading } = useAuth(); const location = useLocation(); const navigate = useNavigate(); useEffect(() => { const handler = () => navigate('/login', { replace: true, state: { from: location.pathname + location.search } }); window.addEventListener('avalia:unauthorized', handler); return () => window.removeEventListener('avalia:unauthorized', handler) }, [location.pathname, location.search, navigate]); if (loading) return <main className="center-page"><Spinner label="Verificando sessão…" /></main>; return user ? <Outlet /> : <Navigate to="/login" replace state={{ from: location.pathname + location.search }} /> }
const router = createBrowserRouter([{ path: '/login', element: <LoginPage />, errorElement: <ErrorPage /> }, { element: <SessionGuard />, children: [{ element: <Layout />, children: [{ path: '/', element: <Navigate to="/avaliacoes" replace /> }, { path: '/avaliacoes', element: <AssessmentsPage /> }, { path: '/avaliacoes/nova', element: <AssessmentEditorPage /> }, { path: '/avaliacoes/:id', element: <AssessmentEditorPage /> }, { path: '/avaliacoes/:id/resposta', element: <AnswerPage /> }, { path: '/correcoes/:id', element: <CorrectionPage /> }, { path: '/correcoes/:id/revisao', element: <ReviewPage /> }] }] }, { path: '*', element: <Navigate to="/avaliacoes" replace /> }])
export default function App() { return <AuthProvider><RouterProvider router={router} /></AuthProvider> }
