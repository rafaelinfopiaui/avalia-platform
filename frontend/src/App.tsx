import { useEffect } from 'react'
import { createBrowserRouter, Navigate, Outlet, RouterProvider, useLocation, useNavigate } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Spinner } from './components/Spinner'
import { AuthProvider, useAuth } from './context/AuthContext'
import { CapabilitiesProvider } from './context/CapabilitiesContext'
import { AcademicPage } from './pages/AcademicPage'
import { AnswerPage } from './pages/AnswerPage'
import { AssessmentEditorPage } from './pages/AssessmentEditorPage'
import { AssessmentsPage } from './pages/AssessmentsPage'
import { CorrectionPage } from './pages/CorrectionPage'
import { ErrorPage } from './pages/ErrorPage'
import { ImageAnswerPage } from './pages/ImageAnswerPage'
import { LoginPage } from './pages/LoginPage'
import { ReviewPage } from './pages/ReviewPage'

function SessionGuard() { const { user, loading } = useAuth(); const location = useLocation(); const navigate = useNavigate(); useEffect(() => { const handler = () => navigate('/login', { replace: true, state: { from: location.pathname + location.search } }); window.addEventListener('avalia:unauthorized', handler); return () => window.removeEventListener('avalia:unauthorized', handler) }, [location.pathname, location.search, navigate]); if (loading) return <main className="center-page"><Spinner label="Verificando sessão…" /></main>; return user ? <Outlet /> : <Navigate to="/login" replace state={{ from: location.pathname + location.search }} /> }
const router = createBrowserRouter([{ path: '/login', element: <LoginPage />, errorElement: <ErrorPage /> }, { element: <SessionGuard />, children: [{ element: <Layout />, children: [{ path: '/', element: <Navigate to="/avaliacoes" replace /> }, { path: '/avaliacoes', element: <AssessmentsPage /> }, { path: '/avaliacoes/nova', element: <AssessmentEditorPage /> }, { path: '/avaliacoes/:id', element: <AssessmentEditorPage /> }, { path: '/avaliacoes/:id/resposta', element: <AnswerPage /> }, { path: '/respostas/foto', element: <ImageAnswerPage /> }, { path: '/correcoes/:id', element: <CorrectionPage /> }, { path: '/correcoes/:id/revisao', element: <ReviewPage /> }, { path: '/academico', element: <AcademicPage /> }] }] }, { path: '*', element: <Navigate to="/avaliacoes" replace /> }])

// CapabilitiesProvider envolve TODAS as rotas (BL-AV-S03B-02): tanto o menu
// (Layout.tsx) quanto as páginas guardadas (/academico) e o editor de avaliação
// leem a capacidade do mesmo contexto, consultado uma única vez do backend em
// GET /v1/config/capabilities. Fica dentro de AuthProvider apenas por ordem de
// composição; a consulta de capacidades é pública e não depende de sessão.
export default function App() { return <AuthProvider><CapabilitiesProvider><RouterProvider router={router} /></CapabilitiesProvider></AuthProvider> }
