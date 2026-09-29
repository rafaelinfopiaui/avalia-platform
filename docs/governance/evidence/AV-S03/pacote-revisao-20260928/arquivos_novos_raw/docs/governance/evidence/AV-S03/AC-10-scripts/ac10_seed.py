"""
Validação real AC-10 (denominador AV-S03) em PostgreSQL isolado.

Denominador aprovado por Rafael em 2026-09-28 (DEC-AV-007, restrito à AV-S03):
- 1 organização
- 1 curso
- 2 disciplinas
- 2 turmas
- 2 professores
- 10 alunos matriculados por turma
- 2 avaliações por turma

Cenários adicionais exigidos pelo texto vigente da sprint (§4.2, aprovados em 2026-09-24,
não removidos em 2026-09-28):
- aluno em mais de uma turma
- disciplina em mais de um curso
- professores com permissões distintas (RESPONSIBLE vs COLLABORATOR vs sem vínculo)
- vínculo expirado (ends_at no passado)

Este script usa FastAPI TestClient sobre o app real, com DATABASE_URL apontando para o
PostgreSQL isolado (não SQLite), exercitando os endpoints HTTP reais (não chamadas diretas
de função), e login real com JWT real.
"""
import os
import sys
from datetime import datetime, timedelta

os.environ["DATABASE_URL"] = "postgresql+psycopg2://rafaeloliveira@/avalia_ac10_validacao?host=/tmp&port=55437"
os.environ["JWT_SECRET"] = "ac10-validacao-secret"
os.environ["AI_ENGINE_URL"] = "http://localhost:9999"
os.environ["ACADEMIC_MODULE_ENABLED"] = "true"

# Execute a partir do diretório core/ do projeto (com o virtualenv do Core ativado),
# não do diretório onde este script está armazenado (evidência em
# docs/governance/evidence/AV-S03/AC-10-scripts/). O import de `app` abaixo depende de
# `core/` estar no sys.path, o que só ocorre executando com cwd=core/.
sys.path.insert(0, os.getcwd())

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

import app.main as main_module  # noqa: E402
from app.db import Base  # noqa: E402
from app.models import Role, User, ProfessorRole, EnrollmentStatus  # noqa: E402
from app.security import hash_password  # noqa: E402

RESULTS = []


def log(scenario, ok, detail):
    RESULTS.append({"scenario": scenario, "ok": ok, "detail": detail})
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {scenario}: {detail}")


engine = create_engine(os.environ["DATABASE_URL"], future=True)

# Limpa dados de execuções anteriores do script (schema já criado via alembic upgrade head)
with engine.begin() as conn:
    for tbl in [
        "audit_events", "human_reviews", "criterion_scores", "ai_executions",
        "correction_jobs", "answers", "rubric_criteria", "rubrics", "questions",
        "assessments", "enrollments", "professor_class_links", "class_groups",
        "course_disciplines", "students", "disciplines", "courses", "organizations",
        "users",
    ]:
        conn.execute(text(f"TRUNCATE TABLE {tbl} RESTART IDENTITY CASCADE"))

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


from app import db as db_module  # noqa: E402
main_module.app.dependency_overrides[db_module.get_db] = override_get_db

client = TestClient(main_module.app)

# ---------------------------------------------------------------------------
# 1. Seed base: admin + 2 professores
# ---------------------------------------------------------------------------
session = SessionLocal()
admin = User(email="admin.ac10@avalia-platform.example", password_hash=hash_password("Admin123!"), role=Role.ADMIN)
prof_a = User(email="prof.a.ac10@avalia-platform.example", password_hash=hash_password("ProfA123!"), role=Role.PROFESSOR)
prof_b = User(email="prof.b.ac10@avalia-platform.example", password_hash=hash_password("ProfB123!"), role=Role.PROFESSOR)
session.add_all([admin, prof_a, prof_b])
session.commit()
session.refresh(admin)
session.refresh(prof_a)
session.refresh(prof_b)
session.close()

def login(email, password):
    r = client.post("/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, f"login failed for {email}: {r.status_code} {r.text}"
    return r.json()["access_token"]

admin_token = login("admin.ac10@avalia-platform.example", "Admin123!")
prof_a_token = login("prof.a.ac10@avalia-platform.example", "ProfA123!")
prof_b_token = login("prof.b.ac10@avalia-platform.example", "ProfB123!")

def auth(token):
    return {"Authorization": f"Bearer {token}"}

log("login admin/prof_a/prof_b", True, "3 logins reais via /v1/auth/login, JWT emitido")

# ---------------------------------------------------------------------------
# 2. Estrutura acadêmica: 1 organização, 1 curso, 2 disciplinas
#    (segunda disciplina em curso adicional para cobrir "disciplina em mais de um curso")
# ---------------------------------------------------------------------------
r = client.post("/v1/organizations", json={"name": "Instituto AC-10"}, headers=auth(admin_token))
assert r.status_code == 201, r.text
org_id = r.json()["id"]

r = client.post("/v1/courses", json={"organization_id": org_id, "name": "Engenharia de Software", "code": "ENG-SOFT"}, headers=auth(admin_token))
assert r.status_code == 201, r.text
course_1_id = r.json()["id"]

# curso adicional apenas para provar "disciplina em mais de um curso" via segunda associação curricular
r = client.post("/v1/courses", json={"organization_id": org_id, "name": "Ciência da Computação", "code": "CIENCIA-COMP"}, headers=auth(admin_token))
assert r.status_code == 201, r.text
course_2_id = r.json()["id"]

r = client.post("/v1/disciplines", json={"organization_id": org_id, "name": "Estruturas de Dados", "code": "EDA-01"}, headers=auth(admin_token))
assert r.status_code == 201, r.text
disc_1_id = r.json()["id"]

r = client.post("/v1/disciplines", json={"organization_id": org_id, "name": "Banco de Dados", "code": "BD-01"}, headers=auth(admin_token))
assert r.status_code == 201, r.text
disc_2_id = r.json()["id"]

log("estrutura: 1 org, 2 cursos (1 principal + 1 para o cenário), 2 disciplinas", True,
    f"org={org_id} course_1={course_1_id} course_2={course_2_id} disc_1={disc_1_id} disc_2={disc_2_id}")

# associação curricular: disciplina 1 aparece em AMBOS os cursos -> "disciplina em mais de um curso"
r = client.post("/v1/course-disciplines", json={"course_id": course_1_id, "discipline_id": disc_1_id}, headers=auth(admin_token))
assert r.status_code == 201, r.text
cd_1_id = r.json()["id"]

r = client.post("/v1/course-disciplines", json={"course_id": course_2_id, "discipline_id": disc_1_id}, headers=auth(admin_token))
assert r.status_code == 201, r.text
cd_1_in_course_2_id = r.json()["id"]

r = client.post("/v1/course-disciplines", json={"course_id": course_1_id, "discipline_id": disc_2_id}, headers=auth(admin_token))
assert r.status_code == 201, r.text
cd_2_id = r.json()["id"]

log("cenário: disciplina em mais de um curso", True,
    f"disciplina {disc_1_id} associada a course_1={course_1_id} (cd={cd_1_id}) e course_2={course_2_id} (cd={cd_1_in_course_2_id})")

# ---------------------------------------------------------------------------
# 3. 2 turmas (denominador principal usa apenas course_1/cd_1 e cd_2)
# ---------------------------------------------------------------------------
r = client.post("/v1/class-groups", json={"course_discipline_id": cd_1_id, "period": "2026-2", "code": "T01"}, headers=auth(admin_token))
assert r.status_code == 201, r.text
class_1_id = r.json()["id"]

r = client.post("/v1/class-groups", json={"course_discipline_id": cd_2_id, "period": "2026-2", "code": "T02"}, headers=auth(admin_token))
assert r.status_code == 201, r.text
class_2_id = r.json()["id"]

log("estrutura: 2 turmas", True, f"class_1={class_1_id} class_2={class_2_id}")

# ---------------------------------------------------------------------------
# 4. Vínculos professor-turma com permissões DISTINTAS:
#    - prof_a: RESPONSIBLE na turma 1, sem vínculo na turma 2
#    - prof_b: COLLABORATOR na turma 1 (permissão distinta de prof_a), RESPONSIBLE expirado na turma 2
# ---------------------------------------------------------------------------
session = SessionLocal()
from app.models import ProfessorClassLink

link_a_t1 = ProfessorClassLink(professor_id=prof_a.id, class_group_id=class_1_id, role=ProfessorRole.RESPONSIBLE, active=True)
link_b_t1 = ProfessorClassLink(professor_id=prof_b.id, class_group_id=class_1_id, role=ProfessorRole.COLLABORATOR, active=True)
# vínculo EXPIRADO de prof_b na turma 2 (ends_at no passado)
link_b_t2_expired = ProfessorClassLink(
    professor_id=prof_b.id, class_group_id=class_2_id, role=ProfessorRole.RESPONSIBLE,
    active=True, starts_at=datetime.utcnow() - timedelta(days=60), ends_at=datetime.utcnow() - timedelta(days=1),
)
session.add_all([link_a_t1, link_b_t1, link_b_t2_expired])
session.commit()
session.close()

log("cenário: professores com permissões distintas", True,
    "prof_a=RESPONSIBLE turma1 (sem vínculo turma2); prof_b=COLLABORATOR turma1 + RESPONSIBLE EXPIRADO turma2")

# ---------------------------------------------------------------------------
# 5. 10 alunos por turma (20 no total), incluindo 1 aluno em AMBAS as turmas
# ---------------------------------------------------------------------------
student_ids_t1 = []
student_ids_t2 = []

# aluno compartilhado entre as duas turmas -> cenário "aluno em mais de uma turma"
r = client.post("/v1/students", json={"organization_id": org_id, "name": "Aluno Compartilhado Multi-Turma", "external_id": "MAT-MULTI-0001"}, headers=auth(admin_token))
assert r.status_code == 201, r.text
shared_student_id = r.json()["id"]

for i in range(9):
    r = client.post("/v1/students", json={"organization_id": org_id, "name": f"Aluno T1 {i+1}", "external_id": f"MAT-T1-{i+1:04d}"}, headers=auth(admin_token))
    assert r.status_code == 201, r.text
    student_ids_t1.append(r.json()["id"])
student_ids_t1.append(shared_student_id)  # completa 10 na turma 1

for i in range(9):
    r = client.post("/v1/students", json={"organization_id": org_id, "name": f"Aluno T2 {i+1}", "external_id": f"MAT-T2-{i+1:04d}"}, headers=auth(admin_token))
    assert r.status_code == 201, r.text
    student_ids_t2.append(r.json()["id"])
student_ids_t2.append(shared_student_id)  # completa 10 na turma 2 (mesmo aluno)

assert len(student_ids_t1) == 10 and len(student_ids_t2) == 10
assert shared_student_id in student_ids_t1 and shared_student_id in student_ids_t2

log("estrutura: 10 alunos matriculados por turma (20 registros de matrícula, 19 alunos únicos)", True,
    f"aluno compartilhado={shared_student_id} presente em ambas as turmas")

for sid in student_ids_t1:
    r = client.post("/v1/enrollments", json={"class_group_id": class_1_id, "student_id": sid, "status": "ACTIVE"}, headers=auth(admin_token))
    assert r.status_code == 201, f"enrollment t1 failed for {sid}: {r.text}"

for sid in student_ids_t2:
    r = client.post("/v1/enrollments", json={"class_group_id": class_2_id, "student_id": sid, "status": "ACTIVE"}, headers=auth(admin_token))
    assert r.status_code == 201, f"enrollment t2 failed for {sid}: {r.text}"

log("cenário: aluno em mais de uma turma", True,
    f"aluno {shared_student_id} matriculado ACTIVE em class_1={class_1_id} e class_2={class_2_id}")

print("\n=== SEED CONCLUÍDO — prosseguindo para validações de autorização ===\n")

import json
with open("/tmp/av_s03_ac10_seed_ids.json", "w") as f:
    json.dump({
        "org_id": org_id, "course_1_id": course_1_id, "course_2_id": course_2_id,
        "disc_1_id": disc_1_id, "disc_2_id": disc_2_id,
        "cd_1_id": cd_1_id, "cd_1_in_course_2_id": cd_1_in_course_2_id, "cd_2_id": cd_2_id,
        "class_1_id": class_1_id, "class_2_id": class_2_id,
        "shared_student_id": shared_student_id,
        "student_ids_t1": student_ids_t1, "student_ids_t2": student_ids_t2,
        "admin_token": admin_token, "prof_a_token": prof_a_token, "prof_b_token": prof_b_token,
    }, f)

with open("/tmp/av_s03_ac10_results.json", "w") as f:
    json.dump(RESULTS, f, indent=2)

print(f"IDs salvos em /tmp/av_s03_ac10_seed_ids.json")
print(f"Resultados parciais salvos em /tmp/av_s03_ac10_results.json")
