import { useEffect, useState, type FormEvent } from 'react'
import { Alert } from '../components/Alert'
import { Spinner } from '../components/Spinner'
import { useAuth } from '../context/AuthContext'
import {
  createClassGroup,
  createCourse,
  createCourseDiscipline,
  createDiscipline,
  createEnrollment,
  createOrganization,
  createStudent,
  listClassGroups,
  listCourseDisciplines,
  listCourses,
  listDisciplines,
  listEnrollments,
  listOrganizations,
  listStudents,
} from '../services/api'
import type {
  ClassGroup,
  Course,
  CourseDiscipline,
  Discipline,
  Enrollment,
  EnrollmentStatus,
  Organization,
  Student,
} from '../types'

type AcademicTab = 'classes' | 'students' | 'enrollments' | 'courses' | 'disciplines' | 'organizations'

export function AcademicPage() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  const isProfessor = user?.role === 'professor'

  const [activeTab, setActiveTab] = useState<AcademicTab>('classes')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // List data
  const [organizations, setOrganizations] = useState<Organization[]>([])
  const [courses, setCourses] = useState<Course[]>([])
  const [disciplines, setDisciplines] = useState<Discipline[]>([])
  const [courseDisciplines, setCourseDisciplines] = useState<CourseDiscipline[]>([])
  const [classGroups, setClassGroups] = useState<ClassGroup[]>([])
  const [students, setStudents] = useState<Student[]>([])
  const [enrollments, setEnrollments] = useState<Enrollment[]>([])

  // Form states - Organization
  const [orgName, setOrgName] = useState('')

  // Form states - Course
  const [courseOrgId, setCourseOrgId] = useState('')
  const [courseName, setCourseName] = useState('')
  const [courseCode, setCourseCode] = useState('')

  // Form states - Discipline
  const [discOrgId, setDiscOrgId] = useState('')
  const [discName, setDiscName] = useState('')
  const [discCode, setDiscCode] = useState('')

  // Form states - ClassGroup
  const [classCourseId, setClassCourseId] = useState('')
  const [classDisciplineId, setClassDisciplineId] = useState('')
  const [classPeriod, setClassPeriod] = useState('')
  const [classCode, setClassCode] = useState('')

  // Form states - Student (Global)
  const [studentOrgId, setStudentOrgId] = useState('')
  const [studentName, setStudentName] = useState('')
  const [studentExternalId, setStudentExternalId] = useState('')

  // Form states - Enrollment (Class link)
  const [enrollmentClassId, setEnrollmentClassId] = useState('')
  const [enrollmentStudentId, setEnrollmentStudentId] = useState('')
  const [enrollmentStatus, setEnrollmentStatus] = useState<EnrollmentStatus>('ACTIVE')

  async function loadData() {
    setLoading(true)
    setError('')
    const errors: string[] = []
    try {
      const [orgsRes, crsRes, discsRes, cdsRes, cgsRes, stdsRes, enrsRes] = await Promise.allSettled([
        listOrganizations(),
        listCourses(),
        listDisciplines(),
        listCourseDisciplines(),
        listClassGroups(),
        listStudents(),
        listEnrollments(),
      ])

      if (orgsRes.status === 'fulfilled') {
        setOrganizations(orgsRes.value)
      } else {
        const msg = orgsRes.reason instanceof Error ? orgsRes.reason.message : 'Erro ao carregar'
        errors.push(`Organizações (${msg})`)
      }

      if (crsRes.status === 'fulfilled') {
        setCourses(crsRes.value)
      } else {
        const msg = crsRes.reason instanceof Error ? crsRes.reason.message : 'Erro ao carregar'
        errors.push(`Cursos (${msg})`)
      }

      if (discsRes.status === 'fulfilled') {
        setDisciplines(discsRes.value)
      } else {
        const msg = discsRes.reason instanceof Error ? discsRes.reason.message : 'Erro ao carregar'
        errors.push(`Disciplinas (${msg})`)
      }

      if (cdsRes.status === 'fulfilled') {
        setCourseDisciplines(cdsRes.value)
      } else {
        const msg = cdsRes.reason instanceof Error ? cdsRes.reason.message : 'Erro ao carregar'
        errors.push(`Vínculos Curso-Disciplina (${msg})`)
      }

      if (cgsRes.status === 'fulfilled') {
        setClassGroups(cgsRes.value)
      } else {
        const msg = cgsRes.reason instanceof Error ? cgsRes.reason.message : 'Erro ao carregar'
        errors.push(`Turmas (${msg})`)
      }

      if (stdsRes.status === 'fulfilled') {
        setStudents(stdsRes.value)
      } else {
        const msg = stdsRes.reason instanceof Error ? stdsRes.reason.message : 'Erro ao carregar'
        errors.push(`Alunos (${msg})`)
      }

      if (enrsRes.status === 'fulfilled') {
        setEnrollments(enrsRes.value)
      } else {
        const msg = enrsRes.reason instanceof Error ? enrsRes.reason.message : 'Erro ao carregar'
        errors.push(`Matrículas (${msg})`)
      }

      if (errors.length > 0) {
        setError(`Falha ao carregar alguns recursos acadêmicos: ${errors.join('; ')}`)
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Falha ao carregar dados acadêmicos.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadData()
  }, [])

  // Lookup helpers
  const getOrgName = (id: string) => organizations.find(o => o.id === id)?.name || id
  const getCourseName = (id: string) => courses.find(c => c.id === id)?.name || id
  const getDisciplineName = (id: string) => disciplines.find(d => d.id === id)?.name || id
  const getCourseDisciplineLabel = (cdId: string) => {
    const cd = courseDisciplines.find(c => c.id === cdId)
    if (!cd) return cdId
    return `${getCourseName(cd.course_id)} / ${getDisciplineName(cd.discipline_id)}`
  }
  const getStudentLabel = (id: string) => {
    const s = students.find(item => item.id === id)
    return s ? `${s.name} (${s.external_id})` : id
  }
  const getClassGroupLabel = (id: string) => {
    const cg = classGroups.find(c => c.id === id)
    if (!cg) return id
    return `Turma ${cg.code} (${cg.period}) — ${getCourseDisciplineLabel(cg.course_discipline_id)}`
  }

  // Submit handlers
  async function handleCreateOrganization(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setBusy(true)
    try {
      const created = await createOrganization({ name: orgName.trim() })
      setOrganizations(prev => [...prev, created])
      setOrgName('')
      setSuccess(`Organização "${created.name}" cadastrada com sucesso!`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível cadastrar a organização.')
    } finally {
      setBusy(false)
    }
  }

  async function handleCreateCourse(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setBusy(true)
    try {
      const created = await createCourse({
        organization_id: courseOrgId,
        name: courseName.trim(),
        code: courseCode.trim(),
      })
      setCourses(prev => [...prev, created])
      setCourseName('')
      setCourseCode('')
      setSuccess(`Curso "${created.name}" (${created.code}) cadastrado com sucesso!`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível cadastrar o curso.')
    } finally {
      setBusy(false)
    }
  }

  async function handleCreateDiscipline(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setBusy(true)
    try {
      const created = await createDiscipline({
        organization_id: discOrgId,
        name: discName.trim(),
        code: discCode.trim(),
      })
      setDisciplines(prev => [...prev, created])
      setDiscName('')
      setDiscCode('')
      setSuccess(`Disciplina "${created.name}" (${created.code}) cadastrada com sucesso!`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível cadastrar a disciplina.')
    } finally {
      setBusy(false)
    }
  }

  async function handleCreateClassGroup(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setBusy(true)
    try {
      let assoc = courseDisciplines.find(
        cd => cd.course_id === classCourseId && cd.discipline_id === classDisciplineId
      )
      if (!assoc) {
        assoc = await createCourseDiscipline({
          course_id: classCourseId,
          discipline_id: classDisciplineId,
        })
        setCourseDisciplines(prev => [...prev, assoc!])
      }
      const created = await createClassGroup({
        course_discipline_id: assoc.id,
        period: classPeriod.trim(),
        code: classCode.trim(),
      })
      setClassGroups(prev => [...prev, created])
      setClassPeriod('')
      setClassCode('')
      setSuccess(`Turma "${created.code}" (${created.period}) cadastrada com sucesso!`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível cadastrar a turma.')
    } finally {
      setBusy(false)
    }
  }

  async function handleCreateStudent(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setBusy(true)
    try {
      const created = await createStudent({
        organization_id: studentOrgId,
        name: studentName.trim(),
        external_id: studentExternalId.trim(),
      })
      setStudents(prev => [...prev, created])
      setStudentName('')
      setStudentExternalId('')
      setSuccess(`Aluno(a) "${created.name}" (${created.external_id}) cadastrado(a) globalmente com sucesso!`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível cadastrar o aluno.')
    } finally {
      setBusy(false)
    }
  }

  async function handleCreateEnrollment(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setBusy(true)
    try {
      const created = await createEnrollment({
        class_group_id: enrollmentClassId,
        student_id: enrollmentStudentId,
        status: enrollmentStatus,
      })
      setEnrollments(prev => [...prev, created])
      setSuccess('Matrícula efetuada com sucesso!')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível realizar a matrícula.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Gestão Acadêmica</p>
          <h1>Estrutura Acadêmica e Turmas</h1>
          <p>Gerencie turmas, dados cadastrais de alunos e matrículas no AvalIA.</p>
        </div>
        <div className="user-area">
          <span className="status status--published">
            {isAdmin ? 'Perfil: Administrador' : isProfessor ? 'Perfil: Professor' : 'Perfil: Usuário'}
          </span>
        </div>
      </div>

      {error && <Alert>{error}</Alert>}
      {success && <Alert type="success">{success}</Alert>}

      <div className="button-row" style={{ marginBottom: '1.5rem' }}>
        <button
          type="button"
          className={`button ${activeTab === 'classes' ? 'button--primary' : 'button--secondary'}`}
          onClick={() => { setActiveTab('classes'); setError(''); setSuccess('') }}
        >
          Turmas ({classGroups.length})
        </button>
        <button
          type="button"
          className={`button ${activeTab === 'students' ? 'button--primary' : 'button--secondary'}`}
          onClick={() => { setActiveTab('students'); setError(''); setSuccess('') }}
        >
          Alunos — Dados Globais ({students.length})
        </button>
        <button
          type="button"
          className={`button ${activeTab === 'enrollments' ? 'button--primary' : 'button--secondary'}`}
          onClick={() => { setActiveTab('enrollments'); setError(''); setSuccess('') }}
        >
          Matrículas ({enrollments.length})
        </button>
        <button
          type="button"
          className={`button ${activeTab === 'courses' ? 'button--primary' : 'button--secondary'}`}
          onClick={() => { setActiveTab('courses'); setError(''); setSuccess('') }}
        >
          Cursos ({courses.length})
        </button>
        <button
          type="button"
          className={`button ${activeTab === 'disciplines' ? 'button--primary' : 'button--secondary'}`}
          onClick={() => { setActiveTab('disciplines'); setError(''); setSuccess('') }}
        >
          Disciplinas ({disciplines.length})
        </button>
        <button
          type="button"
          className={`button ${activeTab === 'organizations' ? 'button--primary' : 'button--secondary'}`}
          onClick={() => { setActiveTab('organizations'); setError(''); setSuccess('') }}
        >
          Organizações ({organizations.length})
        </button>
      </div>

      {loading ? (
        <Spinner label="Carregando dados acadêmicos…" />
      ) : (
        <>
          {/* TAB 1: TURMAS */}
          {activeTab === 'classes' && (
            <div className="editor-layout">
              {isAdmin && (
                <section className="panel">
                  <h2>Cadastrar Nova Turma</h2>
                  <p>Uma turma reúne um curso e uma disciplina em um período letivo específico.</p>
                  <form onSubmit={handleCreateClassGroup} className="form-stack">
                    <label>
                      Curso
                      <select
                        required
                        value={classCourseId}
                        onChange={e => setClassCourseId(e.target.value)}
                      >
                        <option value="">Selecione o curso...</option>
                        {courses.map(c => (
                          <option key={c.id} value={c.id}>
                            {c.name} ({c.code})
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Disciplina
                      <select
                        required
                        value={classDisciplineId}
                        onChange={e => setClassDisciplineId(e.target.value)}
                      >
                        <option value="">Selecione a disciplina...</option>
                        {disciplines.map(d => (
                          <option key={d.id} value={d.id}>
                            {d.name} ({d.code})
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Período Letivo
                      <input
                        required
                        placeholder="Ex.: 2026-2"
                        value={classPeriod}
                        onChange={e => setClassPeriod(e.target.value)}
                      />
                    </label>
                    <label>
                      Código da Turma
                      <input
                        required
                        placeholder="Ex.: T01"
                        value={classCode}
                        onChange={e => setClassCode(e.target.value)}
                      />
                    </label>
                    <div>
                      <button className="button button--primary" disabled={busy}>
                        {busy ? 'Cadastrando…' : 'Cadastrar Turma'}
                      </button>
                    </div>
                  </form>
                </section>
              )}

              {isProfessor && (
                <div className="alert alert--info">
                  Como professor, você visualiza as turmas em que possui vínculo atribuído.
                </div>
              )}

              <section className="panel">
                <h2>Turmas Cadastradas ({classGroups.length})</h2>
                {classGroups.length === 0 ? (
                  <p>Nenhuma turma encontrada.</p>
                ) : (
                  <div className="table-responsive">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Código</th>
                          <th>Período</th>
                          <th>Curso / Disciplina</th>
                          <th>ID</th>
                        </tr>
                      </thead>
                      <tbody>
                        {classGroups.map(cg => (
                          <tr key={cg.id}>
                            <td><strong>Turma {cg.code}</strong></td>
                            <td>{cg.period}</td>
                            <td>{getCourseDisciplineLabel(cg.course_discipline_id)}</td>
                            <td><small>{cg.id}</small></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>
            </div>
          )}

          {/* TAB 2: ALUNOS (DADOS GLOBAIS) */}
          {activeTab === 'students' && (
            <div className="editor-layout">
              <div className="alert alert--info">
                <strong>Separação de Domínio (Student vs. Enrollment):</strong> O cadastro de Aluno
                contém apenas os dados cadastrais globais da pessoa na instituição de ensino (nome e
                identificador institucional). O aluno pode existir antes de ser matriculado. Para associá-lo
                a uma turma, acesse a aba <strong>Matrículas</strong>.
              </div>

              {isAdmin && (
                <section className="panel">
                  <h2>Cadastrar Aluno (Registro Global)</h2>
                  <p>Cadastre os dados institucionais do estudante. Não vincula diretamente a turmas.</p>
                  <form onSubmit={handleCreateStudent} className="form-stack">
                    <label>
                      Organização
                      <select
                        required
                        value={studentOrgId}
                        onChange={e => setStudentOrgId(e.target.value)}
                      >
                        <option value="">Selecione a organização...</option>
                        {organizations.map(o => (
                          <option key={o.id} value={o.id}>
                            {o.name}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Nome Completo
                      <input
                        required
                        placeholder="Ex.: Lucas Mendes de Souza"
                        value={studentName}
                        onChange={e => setStudentName(e.target.value)}
                      />
                    </label>
                    <label>
                      Identificador / Matrícula Institucional Externa
                      <input
                        required
                        placeholder="Ex.: MAT-2026-0042"
                        value={studentExternalId}
                        onChange={e => setStudentExternalId(e.target.value)}
                      />
                    </label>
                    <div>
                      <button className="button button--primary" disabled={busy}>
                        {busy ? 'Cadastrando…' : 'Cadastrar Aluno Global'}
                      </button>
                    </div>
                  </form>
                </section>
              )}

              {isProfessor && (
                <div className="alert alert--info">
                  Professores visualizam os alunos matriculados nas suas turmas ativas. O cadastro de novos
                  alunos institucionais é restrito a administradores.
                </div>
              )}

              <section className="panel">
                <h2>Alunos Cadastrados ({students.length})</h2>
                {students.length === 0 ? (
                  <p>Nenhum aluno encontrado.</p>
                ) : (
                  <div className="table-responsive">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Nome</th>
                          <th>Identificador Externo</th>
                          <th>Organização</th>
                          <th>ID</th>
                        </tr>
                      </thead>
                      <tbody>
                        {students.map(s => (
                          <tr key={s.id}>
                            <td><strong>{s.name}</strong></td>
                            <td><code>{s.external_id}</code></td>
                            <td>{getOrgName(s.organization_id)}</td>
                            <td><small>{s.id}</small></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>
            </div>
          )}

          {/* TAB 3: MATRÍCULAS (VÍNCULO TURMA-ALUNO) */}
          {activeTab === 'enrollments' && (
            <div className="editor-layout">
              <div className="alert alert--info">
                <strong>Matrícula em Turma (Enrollment):</strong> Vincula um aluno previamente cadastrado
                a uma turma específica de um período letivo. Professores responsáveis podem matricular
                alunos diretamente em suas turmas.
              </div>

              <section className="panel">
                <h2>Realizar Matrícula</h2>
                <p>Selecione a turma e o aluno pré-cadastrado para criar o vínculo de matrícula.</p>
                <form onSubmit={handleCreateEnrollment} className="form-stack">
                  <label>
                    Turma
                    <select
                      required
                      value={enrollmentClassId}
                      onChange={e => setEnrollmentClassId(e.target.value)}
                    >
                      <option value="">Selecione a turma...</option>
                      {classGroups.map(cg => (
                        <option key={cg.id} value={cg.id}>
                          {getClassGroupLabel(cg.id)}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Aluno
                    <select
                      required
                      value={enrollmentStudentId}
                      onChange={e => setEnrollmentStudentId(e.target.value)}
                    >
                      <option value="">Selecione o aluno...</option>
                      {students.map(s => (
                        <option key={s.id} value={s.id}>
                          {s.name} ({s.external_id})
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Status da Matrícula
                    <select
                      value={enrollmentStatus}
                      onChange={e => setEnrollmentStatus(e.target.value as EnrollmentStatus)}
                    >
                      <option value="ACTIVE">Ativa (ACTIVE)</option>
                      <option value="SUSPENDED">Trancada / Suspensa (SUSPENDED)</option>
                      <option value="WITHDRAWN">Desistência / Cancelada (WITHDRAWN)</option>
                      <option value="COMPLETED">Concluída (COMPLETED)</option>
                    </select>
                  </label>
                  <div>
                    <button className="button button--primary" disabled={busy}>
                      {busy ? 'Matriculando…' : 'Matricular Aluno na Turma'}
                    </button>
                  </div>
                </form>
              </section>

              <section className="panel">
                <h2>Matrículas Registradas ({enrollments.length})</h2>
                {enrollments.length === 0 ? (
                  <p>Nenhuma matrícula registrada.</p>
                ) : (
                  <div className="table-responsive">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Aluno</th>
                          <th>Turma</th>
                          <th>Status</th>
                          <th>Data Matrícula</th>
                          <th>ID</th>
                        </tr>
                      </thead>
                      <tbody>
                        {enrollments.map(enr => (
                          <tr key={enr.id}>
                            <td><strong>{getStudentLabel(enr.student_id)}</strong></td>
                            <td>{getClassGroupLabel(enr.class_group_id)}</td>
                            <td>
                              <span className={`badge ${enr.status === 'ACTIVE' ? 'status--published' : ''}`}>
                                {enr.status}
                              </span>
                            </td>
                            <td>{new Date(enr.enrolled_at).toLocaleDateString('pt-BR')}</td>
                            <td><small>{enr.id}</small></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>
            </div>
          )}

          {/* TAB 4: CURSOS */}
          {activeTab === 'courses' && (
            <div className="editor-layout">
              {isAdmin && (
                <section className="panel">
                  <h2>Cadastrar Curso</h2>
                  <form onSubmit={handleCreateCourse} className="form-stack">
                    <label>
                      Organização
                      <select
                        required
                        value={courseOrgId}
                        onChange={e => setCourseOrgId(e.target.value)}
                      >
                        <option value="">Selecione a organização...</option>
                        {organizations.map(o => (
                          <option key={o.id} value={o.id}>
                            {o.name}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Nome do Curso
                      <input
                        required
                        placeholder="Ex.: Engenharia de Software"
                        value={courseName}
                        onChange={e => setCourseName(e.target.value)}
                      />
                    </label>
                    <label>
                      Código do Curso
                      <input
                        required
                        placeholder="Ex.: ENG-SOFT"
                        value={courseCode}
                        onChange={e => setCourseCode(e.target.value)}
                      />
                    </label>
                    <div>
                      <button className="button button--primary" disabled={busy}>
                        {busy ? 'Cadastrando…' : 'Cadastrar Curso'}
                      </button>
                    </div>
                  </form>
                </section>
              )}

              {isProfessor && (
                <div className="alert alert--info">
                  Professores têm acesso de consulta aos cursos associados às suas turmas.
                </div>
              )}

              <section className="panel">
                <h2>Cursos Cadastrados ({courses.length})</h2>
                {courses.length === 0 ? (
                  <p>Nenhum curso encontrado.</p>
                ) : (
                  <div className="table-responsive">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Nome</th>
                          <th>Código</th>
                          <th>Organização</th>
                          <th>ID</th>
                        </tr>
                      </thead>
                      <tbody>
                        {courses.map(c => (
                          <tr key={c.id}>
                            <td><strong>{c.name}</strong></td>
                            <td><code>{c.code}</code></td>
                            <td>{getOrgName(c.organization_id)}</td>
                            <td><small>{c.id}</small></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>
            </div>
          )}

          {/* TAB 5: DISCIPLINAS */}
          {activeTab === 'disciplines' && (
            <div className="editor-layout">
              {isAdmin && (
                <section className="panel">
                  <h2>Cadastrar Disciplina</h2>
                  <form onSubmit={handleCreateDiscipline} className="form-stack">
                    <label>
                      Organização
                      <select
                        required
                        value={discOrgId}
                        onChange={e => setDiscOrgId(e.target.value)}
                      >
                        <option value="">Selecione a organização...</option>
                        {organizations.map(o => (
                          <option key={o.id} value={o.id}>
                            {o.name}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Nome da Disciplina
                      <input
                        required
                        placeholder="Ex.: Estruturas de Dados e Algoritmos"
                        value={discName}
                        onChange={e => setDiscName(e.target.value)}
                      />
                    </label>
                    <label>
                      Código da Disciplina
                      <input
                        required
                        placeholder="Ex.: EDA-01"
                        value={discCode}
                        onChange={e => setDiscCode(e.target.value)}
                      />
                    </label>
                    <div>
                      <button className="button button--primary" disabled={busy}>
                        {busy ? 'Cadastrando…' : 'Cadastrar Disciplina'}
                      </button>
                    </div>
                  </form>
                </section>
              )}

              {isProfessor && (
                <div className="alert alert--info">
                  Professores têm acesso de consulta às disciplinas associadas às suas turmas.
                </div>
              )}

              <section className="panel">
                <h2>Disciplinas Cadastradas ({disciplines.length})</h2>
                {disciplines.length === 0 ? (
                  <p>Nenhuma disciplina encontrada.</p>
                ) : (
                  <div className="table-responsive">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Nome</th>
                          <th>Código</th>
                          <th>Organização</th>
                          <th>ID</th>
                        </tr>
                      </thead>
                      <tbody>
                        {disciplines.map(d => (
                          <tr key={d.id}>
                            <td><strong>{d.name}</strong></td>
                            <td><code>{d.code}</code></td>
                            <td>{getOrgName(d.organization_id)}</td>
                            <td><small>{d.id}</small></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>
            </div>
          )}

          {/* TAB 6: ORGANIZAÇÕES */}
          {activeTab === 'organizations' && (
            <div className="editor-layout">
              {isAdmin && (
                <section className="panel">
                  <h2>Cadastrar Organização</h2>
                  <form onSubmit={handleCreateOrganization} className="form-stack">
                    <label>
                      Nome da Organização / Instituição
                      <input
                        required
                        placeholder="Ex.: Instituto de Tecnologia e Educação"
                        value={orgName}
                        onChange={e => setOrgName(e.target.value)}
                      />
                    </label>
                    <div>
                      <button className="button button--primary" disabled={busy}>
                        {busy ? 'Cadastrando…' : 'Cadastrar Organização'}
                      </button>
                    </div>
                  </form>
                </section>
              )}

              {isProfessor && (
                <div className="alert alert--info">
                  Professores têm acesso de consulta à organização associada às suas turmas.
                </div>
              )}

              <section className="panel">
                <h2>Organizações Cadastradas ({organizations.length})</h2>
                {organizations.length === 0 ? (
                  <p>Nenhuma organização encontrada.</p>
                ) : (
                  <div className="table-responsive">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Nome da Organização</th>
                          <th>ID</th>
                        </tr>
                      </thead>
                      <tbody>
                        {organizations.map(o => (
                          <tr key={o.id}>
                            <td><strong>{o.name}</strong></td>
                            <td><small>{o.id}</small></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>
            </div>
          )}
        </>
      )}
    </>
  )
}
