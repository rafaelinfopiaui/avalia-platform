"""AV-S07B — lacunas A e C do fluxo de extração OCR experimental.

A) GET /v1/answers/{id}/transcription/extractions: retomada após reload, só
   leitura; distingue saída bruta do OCR, rascunho humano e confirmada.
C) Gate global de inferência: extração (visão) e análise (texto) sobre
   respostas DIFERENTES não rodam ao mesmo tempo no Ollama; ocupado além do
   limite = rejeição explícita (409 INFERENCE_BUSY / job FALHA); o gate é
   liberado mesmo após falha.

Sem Ollama real: AI Engine substituído por stubs; imagens sintéticas.
"""
# Fixtures importadas de outro módulo de teste são reusadas como parâmetros.
# ruff: noqa: F811
from __future__ import annotations

import asyncio
import time
from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import sessionmaker

import app.main as main_module
import app.services.correction as correction_module
from app.models import (
    Answer,
    AnswerImage,
    AnswerSource,
    CorrectionJob,
    JobStatus,
    Question,
    TranscriptionExtraction,
    TranscriptionStatus,
)
from app.services import inference_gate as gate_module
from app.services.inference_gate import InferenceBusyError, InferenceGate

# Fixtures e utilitários compartilhados com a suíte principal da extração.
from app.tests.test_transcription_extraction import (  # noqa: F401
    EXTRACTED,
    _current,
    _extract,
    _headers,
    _ok,
    answer_id,
    engine,
    question_id,
    storage_dir,
)


def _state(client, token, answer_id):
    return client.get(f"/v1/answers/{answer_id}/transcription/extractions", headers=_headers(token))


def _save_draft(client, token, answer_id, text, version):
    response = client.patch(
        f"/v1/answers/{answer_id}/manual-transcription/draft",
        json={"text": text, "expected_version": version},
        headers=_headers(token),
    )
    assert response.status_code == 200, response.text
    return response


def _snapshot(db_session, answer_id) -> tuple:
    answer = _current(db_session, answer_id)
    return (
        answer.manual_transcription_draft,
        answer.transcription_version,
        answer.text,
        answer.transcription_status,
    )


# =============================== Lacuna A ===============================
def test_recovery_after_reload_returns_latest_extraction_and_ocr_origin(
    client, db_session, professor_token, answer_id, engine
):
    engine(_ok())
    extracted = _extract(client, professor_token, answer_id).json()
    before = _snapshot(db_session, answer_id)

    # "Reload": requisição nova, sem nenhum estado do cliente.
    response = _state(client, professor_token, answer_id)

    assert response.status_code == 200, response.text
    body = response.json()
    latest = body["latest_extraction"]
    assert latest["extraction_id"] == extracted["extraction_id"]
    assert latest["status"] == "ok"
    assert latest["model"] == "qwen2.5vl:3b"
    assert latest["image_id"] == extracted["answer_image_id"]
    assert latest["has_raw_output"] is True
    assert latest["raw_text"] == EXTRACTED
    assert latest["raw_text_truncated"] is False
    assert latest["created_at"]
    assert body["text_state"] == "RASCUNHO"
    assert body["draft_origin"] == "OCR"
    assert body["draft_source_extraction_id"] == extracted["extraction_id"]
    assert body["draft_source_raw_text"] == EXTRACTED
    assert body["transcription_version"] == 1
    # Leitura não altera nada.
    assert _snapshot(db_session, answer_id) == before


def test_human_edit_is_labeled_edited_and_never_overwritten(
    client, db_session, professor_token, answer_id, engine
):
    engine(_ok())
    first = _extract(client, professor_token, answer_id).json()
    edited = "A pilha é LIFO e a fila é FIFO."  # professor corrigiu a leitura
    _save_draft(client, professor_token, answer_id, edited, 1)

    body = _state(client, professor_token, answer_id).json()
    assert body["draft_origin"] == "OCR_EDITADO"  # nunca "puramente automático"
    assert body["draft_source_extraction_id"] == first["extraction_id"]
    assert body["draft_source_raw_text"] == EXTRACTED

    # Nova extração (resposta "tardia") não sobrescreve a edição humana.
    engine(_ok("Leitura posterior diferente."))
    second = _extract(client, professor_token, answer_id).json()
    assert second["draft_updated"] is False
    for _ in range(2):  # recuperações repetidas
        body = _state(client, professor_token, answer_id).json()
        assert body["latest_extraction"]["extraction_id"] == second["extraction_id"]
        assert body["latest_extraction"]["raw_text"] == "Leitura posterior diferente."
        assert body["draft_origin"] == "OCR_EDITADO"
        assert body["draft_source_extraction_id"] == first["extraction_id"]
    answer = _current(db_session, answer_id)
    assert answer.manual_transcription_draft == edited
    assert answer.transcription_version == 2


def test_manual_draft_without_extraction_is_manual(client, professor_token, answer_id):
    _save_draft(client, professor_token, answer_id, "Digitado à mão.", 0)

    body = _state(client, professor_token, answer_id).json()

    assert body["text_state"] == "RASCUNHO"
    assert body["draft_origin"] == "MANUAL"
    assert body["draft_source_extraction_id"] is None
    assert body["latest_extraction"] is None


def test_manual_draft_matching_historic_raw_is_still_manual(
    client, db_session, professor_token, answer_id, storage_dir, engine
):
    # ALTA-4/5 (regressão): a origem é por VERSÃO, não por coincidência de texto.
    # Uma extração histórica que NÃO preencheu o rascunho (porque a imagem foi
    # excluída, virando falha/sem draft) não pode fazer um rascunho digitado à
    # mão, mesmo idêntico ao raw_output, ser rotulado como OCR.
    image = db_session.query(AnswerImage).filter_by(answer_id=answer_id).one()
    historic = TranscriptionExtraction(
        answer_id=answer_id,
        answer_image_id=image.id,
        engine="ollama-vision",
        model="qwen2.5vl:3b",
        config_json="{}",
        status="ok",
        raw_output="texto idêntico ao que será digitado",
        duration_ms=10,
        resulting_transcription_version=None,  # NÃO preencheu o rascunho
    )
    db_session.add(historic)
    db_session.commit()

    # Professor digita um rascunho idêntico ao raw_output histórico.
    _save_draft(client, professor_token, answer_id, "texto idêntico ao que será digitado", 0)

    body = _state(client, professor_token, answer_id).json()
    assert body["text_state"] == "RASCUNHO"
    # Coincidência de texto NÃO conta como OCR — é MANUAL.
    assert body["draft_origin"] == "MANUAL"
    assert body["draft_source_extraction_id"] is None


def test_empty_answer_without_extraction(client, professor_token, answer_id):
    body = _state(client, professor_token, answer_id).json()
    assert body["text_state"] == "VAZIO"
    assert body["draft_origin"] is None
    assert body["latest_extraction"] is None


def test_confirmed_transcription_is_not_altered_by_recovery(
    client, db_session, professor_token, answer_id, engine
):
    engine(_ok())
    _extract(client, professor_token, answer_id)
    confirmed = client.post(
        f"/v1/answers/{answer_id}/manual-transcription/confirm",
        json={"text": "Texto conferido e confirmado.", "expected_version": 1},
        headers=_headers(professor_token),
    )
    assert confirmed.status_code == 200, confirmed.text
    before = _snapshot(db_session, answer_id)

    body = _state(client, professor_token, answer_id).json()

    assert body["text_state"] == "CONFIRMADA"
    assert body["transcription_status"] == "TRANSCRICAO_CONFIRMADA"
    assert body["draft_origin"] is None
    # A saída bruta continua visível, separada do texto confirmado.
    assert body["latest_extraction"]["raw_text"] == EXTRACTED
    assert _snapshot(db_session, answer_id) == before
    assert before[2] == "Texto conferido e confirmado."


def test_image_deleted_between_selection_and_use_fails_without_calling_engine(
    client, db_session, professor_token, answer_id, engine, monkeypatch
):
    # ALTA-2: se a imagem deixa de estar ativa entre a seleção e o uso, a
    # extração vira 'falha' (IMAGE_NO_LONGER_ACTIVE) SEM chamar o motor.
    stub = engine(_ok())
    image = db_session.query(AnswerImage).filter_by(answer_id=answer_id).one()

    real_query = main_module._active_images_query
    state = {"calls": 0}

    def flaky_query(db, aid):
        # 1ª chamada (seleção) enxerga a imagem; a partir da 2ª (revalidação)
        # simula que ela foi excluída por outra sessão: nenhum ativo.
        state["calls"] += 1
        q = real_query(db, aid)
        if state["calls"] == 1:
            return q
        return q.filter(AnswerImage.id == "inexistente-para-forcar-vazio")

    monkeypatch.setattr(main_module, "_active_images_query", flaky_query)

    resp = _extract(client, professor_token, answer_id)
    assert resp.status_code == 200, resp.text  # registro criado, mas status falha
    body = resp.json()
    assert body["status"] == "falha"
    assert stub.calls == []  # motor NUNCA chamado
    assert _current(db_session, answer_id).manual_transcription_draft is None
    latest = _state(client, professor_token, answer_id).json()["latest_extraction"]
    assert latest["status"] == "falha"
    assert latest["error_detail"] == "IMAGE_NO_LONGER_ACTIVE"
    assert image.deleted_at is None  # o teste não mexeu no banco de fato


def test_failed_extraction_is_recoverable_without_text(client, professor_token, answer_id, engine):
    engine({"status": "falha", "text": "", "model": "qwen2.5vl:3b", "duration_ms": 0, "error_detail": "Timeout"})
    _extract(client, professor_token, answer_id)

    latest = _state(client, professor_token, answer_id).json()["latest_extraction"]

    assert latest["status"] == "falha"
    assert latest["has_raw_output"] is False
    assert latest["raw_text"] == ""
    assert latest["error_detail"] == "Timeout"


def test_large_raw_output_is_truncated(client, professor_token, answer_id, engine, monkeypatch):
    engine(_ok("X" * 50))
    _extract(client, professor_token, answer_id)
    monkeypatch.setattr(main_module, "_EXTRACTION_RAW_TEXT_LIMIT", 10)

    latest = _state(client, professor_token, answer_id).json()["latest_extraction"]

    assert latest["raw_text"] == "X" * 10
    assert latest["raw_text_truncated"] is True
    assert latest["has_raw_output"] is True


def test_read_is_authorized_by_ownership_without_mutation(
    client, professor_token, second_professor_token, admin_token, answer_id, monkeypatch
):
    assert _state(client, second_professor_token, answer_id).status_code == 403
    assert _state(client, admin_token, answer_id).status_code == 200
    assert client.get(f"/v1/answers/{answer_id}/transcription/extractions").status_code == 401
    assert _state(client, professor_token, "inexistente").status_code == 404

    # Leitura NÃO exige vínculo ativo (mutação): mesmo com a mutação negada, lê.
    def deny(*args, **kwargs):
        raise HTTPException(status_code=403, detail="Sem vínculo ativo.")

    monkeypatch.setattr(main_module, "require_assessment_mutation", deny)
    assert _state(client, professor_token, answer_id).status_code == 200
    assert _extract(client, professor_token, answer_id).status_code == 403


# =============================== Lacuna C ===============================
@pytest.fixture()
def fresh_gate(monkeypatch):
    gate = InferenceGate()
    monkeypatch.setattr(gate_module, "inference_gate", gate)
    return gate


def test_gate_serializes_concurrent_holders():
    gate = InferenceGate()
    intervals: list[tuple[float, float]] = []

    async def work(name):
        async with gate.hold(name, wait_timeout=2):
            start = time.perf_counter()
            await asyncio.sleep(0.05)
            intervals.append((start, time.perf_counter()))

    async def main():
        await asyncio.gather(work("visão"), work("texto"))

    asyncio.run(main())

    (s1, e1), (s2, e2) = sorted(intervals)
    assert e1 <= s2  # sem sobreposição temporal


def test_gate_times_out_with_explicit_error_and_releases_after_failure():
    gate = InferenceGate()

    async def main():
        async with gate.hold("extração de texto (visão)", wait_timeout=1):
            with pytest.raises(InferenceBusyError) as excinfo:
                async with gate.hold("análise textual", wait_timeout=0.05):
                    pass
            assert excinfo.value.code == "INFERENCE_BUSY"
            assert excinfo.value.busy_with == "extração de texto (visão)"
        # Falha dentro do bloco: o gate é liberado mesmo assim.
        with pytest.raises(RuntimeError):
            async with gate.hold("análise textual", wait_timeout=1):
                raise RuntimeError("motor caiu")
        assert gate.busy_with is None
        async with gate.hold("extração de texto (visão)", wait_timeout=0.05):
            pass

    asyncio.run(main())


def _hold_from_outside(gate: InferenceGate, operation: str) -> asyncio.Lock:
    """Ocupa o gate como se outra inferência estivesse em curso."""

    async def acquire():
        lock = gate._get_lock()
        await lock.acquire()
        return lock

    lock = asyncio.run(acquire())
    gate.busy_with = operation
    return lock


def test_extraction_rejected_with_409_when_gate_busy_and_nothing_left_pending(
    client, db_session, professor_token, answer_id, engine, fresh_gate, monkeypatch
):
    stub = engine(_ok())
    monkeypatch.setattr(gate_module, "EXTRACTION_WAIT_SECONDS", 0.05)
    lock = _hold_from_outside(fresh_gate, "análise textual")

    response = _extract(client, professor_token, answer_id)

    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "INFERENCE_BUSY"
    assert "ocupado" in body["message"]
    assert body["details"]["busy_with"] == "análise textual"
    assert stub.calls == []
    db_session.expire_all()
    assert db_session.query(TranscriptionExtraction).filter_by(answer_id=answer_id).count() == 0
    assert _current(db_session, answer_id).manual_transcription_draft is None

    # Liberado o gate, a extração segue normalmente.
    fresh_gate.busy_with = None
    lock.release()
    assert _extract(client, professor_token, answer_id).status_code == 200
    assert not fresh_gate._lock.locked()


def _confirmed_text_job(db_session, question_id) -> str:
    question = db_session.get(Question, question_id)
    rubric = next(r for r in question.rubrics if r.is_published)
    answer = Answer(
        question_id=question_id,
        student_name_fake="Aluno texto",
        text="A pilha é LIFO.",
        source=AnswerSource.TEXT,
        transcription_status=TranscriptionStatus.TRANSCRICAO_CONFIRMADA,
    )
    db_session.add(answer)
    db_session.flush()
    job = CorrectionJob(answer_id=answer.id, rubric_id=rubric.id, status=JobStatus.PENDENTE, attempt=1)
    db_session.add(job)
    db_session.commit()
    return job.id


class _Recorder:
    def __init__(self):
        self.intervals: dict[str, tuple[float, float]] = {}
        self.active = 0
        self.max_active = 0

    async def run(self, name: str, seconds: float = 0.15):
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        start = time.perf_counter()
        try:
            await asyncio.sleep(seconds)
        finally:
            self.active -= 1
            self.intervals[name] = (start, time.perf_counter())


def _fake_analyze_client(recorder: _Recorder, *, fail: bool = False, calls: list | None = None):
    class FakeResponse:
        status_code = 200

        @staticmethod
        def raise_for_status():
            return None

        @staticmethod
        def json():
            return {"engine_mode": "real", "model": "fake", "criterion_scores": []}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def post(self, url, json):
            if calls is not None:
                calls.append(url)
            await recorder.run("analise")
            if fail:
                raise httpx.ConnectError("AI Engine fora do ar")
            return FakeResponse()

    return SimpleNamespace(AsyncClient=FakeClient)


def test_extraction_and_correction_on_different_answers_never_overlap(
    client, db_session, test_engine, professor_token, question_id, answer_id, fresh_gate, monkeypatch
):
    job_id = _confirmed_text_job(db_session, question_id)
    recorder = _Recorder()

    async def fake_extract(image_base64, mime_type):
        await recorder.run("extracao")
        return _ok()

    monkeypatch.setattr(main_module, "_call_ai_engine_extract", fake_extract)
    session_factory = sessionmaker(bind=test_engine, autoflush=False, autocommit=False, future=True)

    async def main():
        transport = httpx.ASGITransport(app=main_module.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://core") as api:
            # Só o módulo de correção vê o cliente falso do AI Engine.
            monkeypatch.setattr(correction_module, "httpx", _fake_analyze_client(recorder))
            extraction, _ = await asyncio.gather(
                api.post(f"/v1/answers/{answer_id}/transcription/extract", headers=_headers(professor_token)),
                correction_module.run_correction_job(job_id, session_factory),
            )
        return extraction

    extraction = asyncio.run(main())

    assert extraction.status_code == 200, extraction.text
    assert extraction.json()["status"] == "ok"
    assert set(recorder.intervals) == {"extracao", "analise"}
    assert recorder.max_active == 1
    (s1, e1), (s2, e2) = sorted(recorder.intervals.values())
    assert e1 <= s2
    db_session.expire_all()
    assert db_session.get(CorrectionJob, job_id).status == JobStatus.SUGERIDA
    assert fresh_gate.busy_with is None and not fresh_gate._lock.locked()


def test_correction_waits_then_fails_clearly_when_gate_stays_busy(
    db_session, test_engine, question_id, fresh_gate, monkeypatch
):
    job_id = _confirmed_text_job(db_session, question_id)
    calls: list[str] = []
    monkeypatch.setattr(correction_module, "httpx", _fake_analyze_client(_Recorder(), calls=calls))
    monkeypatch.setattr(gate_module, "CORRECTION_WAIT_SECONDS", 0.05)
    lock = _hold_from_outside(fresh_gate, "extração de texto (visão)")
    session_factory = sessionmaker(bind=test_engine, autoflush=False, autocommit=False, future=True)

    asyncio.run(correction_module.run_correction_job(job_id, session_factory))

    db_session.expire_all()
    job = db_session.get(CorrectionJob, job_id)
    assert job.status == JobStatus.FALHA  # nunca fica "processando" indefinidamente
    assert "ocupado" in job.error_message
    assert calls == []  # o AI Engine não foi chamado
    lock.release()


def test_gate_is_released_after_correction_failure(
    client, db_session, test_engine, professor_token, question_id, answer_id, engine, fresh_gate, monkeypatch
):
    job_id = _confirmed_text_job(db_session, question_id)
    monkeypatch.setattr(correction_module, "httpx", _fake_analyze_client(_Recorder(), fail=True))
    session_factory = sessionmaker(bind=test_engine, autoflush=False, autocommit=False, future=True)

    asyncio.run(correction_module.run_correction_job(job_id, session_factory))

    db_session.expire_all()
    assert db_session.get(CorrectionJob, job_id).status == JobStatus.FALHA
    assert fresh_gate.busy_with is None and not fresh_gate._lock.locked()
    # A extração seguinte (outra resposta) não fica bloqueada.
    monkeypatch.setattr(gate_module, "EXTRACTION_WAIT_SECONDS", 0.05)
    engine(_ok())
    assert _extract(client, professor_token, answer_id).status_code == 200
