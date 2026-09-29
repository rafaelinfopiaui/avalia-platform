"""
Continuação da validação AC-10: cria 2 avaliações por turma e exercita a matriz
de autorização real com o denominador aprovado, via HTTP real (TestClient).
"""
import os
import sys
import json

os.environ["DATABASE_URL"] = "postgresql+psycopg2://rafaeloliveira@/avalia_ac10_validacao?host=/tmp&port=55437"
os.environ["JWT_SECRET"] = "ac10-validacao-secret"
os.environ["AI_ENGINE_URL"] = "http://localhost:9999"
os.environ["ACADEMIC_MODULE_ENABLED"] = "true"

# Execute a partir do diretório core/ do projeto (com o virtualenv do Core ativado).
sys.path.insert(0, os.getcwd())

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

import app.main as main_module  # noqa: E402
from app import db as db_module  # noqa: E402

engine = create_engine(os.environ["DATABASE_URL"], future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


main_module.app.dependency_overrides[db_module.get_db] = override_get_db
client = TestClient(main_module.app)

with open("/tmp/av_s03_ac10_seed_ids.json") as f:
    ids = json.load(f)

def auth(token):
    return {"Authorization": f"Bearer {token}"}

admin_token = ids["admin_token"]
prof_a_token = ids["prof_a_token"]
prof_b_token = ids["prof_b_token"]
class_1_id = ids["class_1_id"]
class_2_id = ids["class_2_id"]

RESULTS = []
def log(scenario, ok, detail):
    RESULTS.append({"scenario": scenario, "ok": ok, "detail": detail})
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {scenario}: {detail}")

# ---------------------------------------------------------------------------
# 6. 2 avaliações por turma (denominador: 2 avaliações/turma)
#    prof_a (RESPONSIBLE turma1) cria 2 avaliações na turma 1
# ---------------------------------------------------------------------------
assessment_ids_t1 = []
for i in range(2):
    payload = {
        "title": f"Avaliação T1 #{i+1}",
        "class_group_id": class_1_id,
        "question": {"statement": f"Enunciado {i+1}", "reference_answer": "Resposta de referência", "max_score": 10},
    }
    r = client.post("/v1/assessments", json=payload, headers=auth(prof_a_token))
    assert r.status_code == 201, f"criação avaliação t1 #{i+1} falhou: {r.status_code} {r.text}"
    assessment_ids_t1.append(r.json()["id"])

log("estrutura: 2 avaliações na turma 1 (por prof_a RESPONSIBLE)", True, f"ids={assessment_ids_t1}")

# ---------------------------------------------------------------------------
# 7. CENÁRIO: prof_b tem vínculo EXPIRADO na turma 2 -> NÃO pode criar avaliação nova lá
# ---------------------------------------------------------------------------
payload_t2 = {
    "title": "Avaliação T2 tentativa com vínculo expirado",
    "class_group_id": class_2_id,
    "question": {"statement": "Enunciado", "reference_answer": "Resposta", "max_score": 10},
}
r = client.post("/v1/assessments", json=payload_t2, headers=auth(prof_b_token))
ok = r.status_code == 403
log("cenário: vínculo EXPIRADO não concede acesso a operação NOVA", ok,
    f"prof_b tentou criar avaliação na turma 2 (vínculo expirado) -> status {r.status_code} (esperado 403)")

# ---------------------------------------------------------------------------
# 8. CENÁRIO: admin cria avaliação na turma 2 mesmo sem vínculo (acesso global)
# ---------------------------------------------------------------------------
payload_t2_admin = {
    "title": "Avaliação T2 criada pelo admin",
    "class_group_id": class_2_id,
    "question": {"statement": "Enunciado admin", "reference_answer": "Resposta admin", "max_score": 10},
}
r = client.post("/v1/assessments", json=payload_t2_admin, headers=auth(admin_token))
ok = r.status_code == 201
assessment_t2_admin_id = r.json().get("id") if ok else None
log("cenário: admin mantém acesso global (sem vínculo de turma)", ok,
    f"admin criou avaliação na turma 2 -> status {r.status_code} (esperado 201)")

# segunda avaliação na turma 2, pelo admin, para completar o denominador (2 avaliações/turma)
r2 = client.post("/v1/assessments", json={
    "title": "Avaliação T2 #2 criada pelo admin",
    "class_group_id": class_2_id,
    "question": {"statement": "Enunciado 2", "reference_answer": "Resposta 2", "max_score": 10},
}, headers=auth(admin_token))
ok2 = r2.status_code == 201
log("estrutura: 2 avaliações na turma 2 (via admin, dado vínculo expirado de prof_b)", ok2,
    f"status={r2.status_code}")

# ---------------------------------------------------------------------------
# 9. CENÁRIO: prof_b (COLLABORATOR na turma 1) NÃO pode editar avaliação de prof_a
#    (colaborador não herda edição de avaliação alheia)
# ---------------------------------------------------------------------------
target_assessment_id = assessment_ids_t1[0]
r = client.get(f"/v1/assessments/{target_assessment_id}", headers=auth(prof_b_token))
# NOTA: a implementação atual (BL-AV-2-03 homologado) restringe leitura de avaliação por
# ownership estrito (owner_id == user.id) para qualquer professor, sem exceção para
# colaborador de turma. Isso é consistente com a matriz aprovada (seção 5.1 da sprint):
# "própria ou acesso explicitamente concedido pela política de papel" — e nenhuma política
# de papel concede leitura de avaliação alheia a colaboradores nesta implementação.
# A expectativa correta é 403, não 200 (correção aplicada após primeira execução real
# revelar que a hipótese inicial deste script estava desalinhada com o comportamento
# homologado, não com um defeito do código).
read_blocked = r.status_code == 403
log("cenário: COLLABORATOR não lê avaliação alheia da turma vinculada (ownership estrito, comportamento homologado em BL-AV-2-03)", read_blocked,
    f"prof_b (COLLABORATOR turma1) tentou ler avaliação de prof_a -> status {r.status_code} (esperado 403, ownership estrito)")

# tentativa de publicar (mutação) por um colaborador que não é dono
r = client.post(f"/v1/assessments/{target_assessment_id}/publish", headers=auth(prof_b_token))
mutation_blocked = r.status_code == 403
log("cenário: COLLABORATOR não herda edição/mutação de avaliação alheia", mutation_blocked,
    f"prof_b tentou publicar avaliação de prof_a -> status {r.status_code} (esperado 403)")

# ---------------------------------------------------------------------------
# 10. CENÁRIO: prof_a (RESPONSIBLE turma1) NÃO acessa recursos da turma 2 (sem vínculo lá)
# ---------------------------------------------------------------------------
r = client.get(f"/v1/assessments/{assessment_t2_admin_id}", headers=auth(prof_a_token)) if assessment_t2_admin_id else None
if r is not None:
    blocked = r.status_code in (403, 404)
    log("cenário: professor sem vínculo na turma não acessa avaliação alheia daquela turma", blocked,
        f"prof_a (sem vínculo turma2) tentou ler avaliação da turma2 -> status {r.status_code} (esperado 403/404)")

# ---------------------------------------------------------------------------
# 11. CENÁRIO: aluno em múltiplas turmas aparece corretamente em ambas as listagens de alunos
#     do(s) professor(es) vinculados a cada turma
# ---------------------------------------------------------------------------
r = client.get("/v1/students", headers=auth(prof_a_token))
prof_a_students = r.json() if r.status_code == 200 else []
shared_in_prof_a = any(s["id"] == ids["shared_student_id"] for s in prof_a_students)
log("cenário: aluno compartilhado visível ao professor da turma 1", shared_in_prof_a,
    f"prof_a vê {len(prof_a_students)} alunos; aluno compartilhado presente={shared_in_prof_a}")

r = client.get("/v1/students", headers=auth(admin_token))
admin_students = r.json() if r.status_code == 200 else []
log("cenário: admin vê todos os alunos (escopo global)", len(admin_students) == 19,
    f"admin vê {len(admin_students)} alunos únicos (esperado 19: 9+9+1 compartilhado)")

# ---------------------------------------------------------------------------
# Resumo
# ---------------------------------------------------------------------------
with open("/tmp/av_s03_ac10_results_part2.json", "w") as f:
    json.dump(RESULTS, f, indent=2)

total = len(RESULTS)
passed = sum(1 for r in RESULTS if r["ok"])
print(f"\n=== RESUMO PARTE 2: {passed}/{total} cenários PASS ===")
if passed != total:
    sys.exit(1)
