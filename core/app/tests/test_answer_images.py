"""AV-S06B — recebimento, armazenamento e recuperação de imagens de resposta."""
from __future__ import annotations

import ast
import hashlib
import io
import os
import re
from decimal import Decimal
from pathlib import Path

import pytest
from PIL import Image
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from starlette.routing import Mount

import app.main as main_module
from app.config import get_settings
from app.models import (
    Answer,
    AnswerImage,
    Assessment,
    AssessmentStatus,
    ClassGroup,
    CorrectionJob,
    Course,
    CourseDiscipline,
    Discipline,
    Organization,
    ProfessorClassLink,
    ProfessorRole,
    Question,
    User,
)
from app.routers import images as images_module

_SERVER_NAME = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\.(jpg|png)$"
)


def _headers(token: str | None) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"} if token else {}


def _image_bytes(fmt: str = "PNG", size: tuple[int, int] = (32, 32)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, color=(200, 30, 30)).save(buffer, format=fmt)
    return buffer.getvalue()


def _upload(
    client,
    token,
    answer_id,
    content: bytes,
    *,
    filename: str = "resposta.png",
    content_type: str = "image/png",
):
    return client.post(
        f"/v1/answers/{answer_id}/images",
        files={"file": (filename, content, content_type)},
        headers=_headers(token),
    )


def _stored_files(path: Path) -> list[Path]:
    return sorted(p for p in path.rglob("*") if p.is_file()) if path.exists() else []


def _count(db_session, model) -> int:
    db_session.rollback()  # garante leitura do estado gravado pela requisição
    return db_session.query(model).count()


def _owner(db_session) -> User:
    return db_session.query(User).filter_by(email="professor@example.com").one()


def _answer_for(db_session, assessment: Assessment) -> str:
    db_session.add(assessment)
    db_session.flush()
    question = Question(
        assessment_id=assessment.id,
        statement="Descreva o ciclo da água.",
        reference_answer="Evaporação, condensação e precipitação.",
        max_score=Decimal("10.00"),
    )
    db_session.add(question)
    db_session.flush()
    answer = Answer(
        question_id=question.id,
        student_name_fake="Aluno fictício",
        text="Resposta manuscrita (imagem anexada).",
    )
    db_session.add(answer)
    db_session.commit()
    return answer.id


@pytest.fixture()
def storage_dir(tmp_path, monkeypatch):
    path = tmp_path / "answer_images"
    monkeypatch.setattr(get_settings(), "answer_images_storage_dir", str(path))
    return path


@pytest.fixture()
def owned_answer(db_session, professor_token):
    owner = _owner(db_session)
    return _answer_for(
        db_session,
        Assessment(title="Avaliação com imagem", owner_id=owner.id, status=AssessmentStatus.PUBLICADA),
    )


# ---------------- AC-01: upload válido ----------------
def test_owner_uploads_valid_png_with_correct_metadata(
    client, db_session, professor_token, owned_answer, storage_dir
):
    content = _image_bytes("PNG")
    resp = _upload(client, professor_token, owned_answer, content)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["answer_id"] == owned_answer
    assert body["content_type"] == "image/png"
    assert body["size_bytes"] == len(content)
    assert body["sha256_hash"] == hashlib.sha256(content).hexdigest()
    assert body["original_filename"] == "resposta.png"
    assert body["uploaded_by_id"] == _owner(db_session).id
    assert "storage_filename" not in body

    files = _stored_files(storage_dir)
    assert len(files) == 1
    assert _SERVER_NAME.match(files[0].name)
    assert files[0].read_bytes() == content
    record = db_session.get(AnswerImage, body["id"])
    assert record.storage_filename == files[0].name


def test_owner_uploads_valid_jpeg(client, professor_token, owned_answer, storage_dir):
    content = _image_bytes("JPEG")
    resp = _upload(
        client, professor_token, owned_answer, content, filename="foto.jpg", content_type="image/jpeg"
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["content_type"] == "image/jpeg"
    [stored] = _stored_files(storage_dir)
    assert stored.suffix == ".jpg"


def test_admin_can_upload(client, admin_token, owned_answer, storage_dir):
    resp = _upload(client, admin_token, owned_answer, _image_bytes("PNG"))
    assert resp.status_code == 201, resp.text


def test_upload_to_missing_answer_returns_404(client, professor_token, storage_dir):
    resp = _upload(client, professor_token, "inexistente", _image_bytes("PNG"))
    assert resp.status_code == 404


# ---------------- AC-02/03: autorização ----------------
def test_other_professor_cannot_upload(
    client, db_session, owned_answer, second_professor_token, storage_dir
):
    resp = _upload(client, second_professor_token, owned_answer, _image_bytes("PNG"))
    assert resp.status_code == 403
    assert _count(db_session, AnswerImage) == 0
    assert _stored_files(storage_dir) == []


def test_upload_without_token_returns_401(client, db_session, owned_answer, storage_dir):
    resp = _upload(client, None, owned_answer, _image_bytes("PNG"))
    assert resp.status_code == 401
    assert _count(db_session, AnswerImage) == 0


def test_class_assessment_requires_active_link(client, db_session, professor_token, storage_dir):
    owner = _owner(db_session)
    organization = Organization(name="Org imagens")
    db_session.add(organization)
    db_session.flush()
    course = Course(organization_id=organization.id, name="Curso", code="CUR-IMG")
    discipline = Discipline(organization_id=organization.id, name="Disciplina", code="DISC-IMG")
    db_session.add_all([course, discipline])
    db_session.flush()
    course_discipline = CourseDiscipline(course_id=course.id, discipline_id=discipline.id)
    db_session.add(course_discipline)
    db_session.flush()
    class_group = ClassGroup(course_discipline_id=course_discipline.id, period="2026-2", code="T-IMG")
    db_session.add(class_group)
    db_session.flush()
    answer_id = _answer_for(
        db_session,
        Assessment(
            title="Avaliação de turma",
            owner_id=owner.id,
            class_group_id=class_group.id,
            status=AssessmentStatus.PUBLICADA,
        ),
    )

    resp = _upload(client, professor_token, answer_id, _image_bytes("PNG"))
    assert resp.status_code == 403

    db_session.add(
        ProfessorClassLink(
            professor_id=owner.id, class_group_id=class_group.id, role=ProfessorRole.RESPONSIBLE
        )
    )
    db_session.commit()
    resp = _upload(client, professor_token, answer_id, _image_bytes("PNG"))
    assert resp.status_code == 201, resp.text


# ---------------- AC-04: conteúdo real ----------------
@pytest.mark.parametrize(
    "content",
    [
        os.urandom(2048),
        b"%PDF-1.4\n1 0 obj << /Type /Catalog >> endobj\ntrailer << /Root 1 0 R >>\n%%EOF\n",
        b"MZ\x90\x00" + b"\x00" * 512,  # cabeçalho de executável renomeado
    ],
    ids=["random-bytes", "pdf", "executable"],
)
def test_forged_image_content_type_is_rejected(
    client, db_session, professor_token, owned_answer, storage_dir, content
):
    resp = _upload(
        client, professor_token, owned_answer, content, filename="foto.jpg", content_type="image/jpeg"
    )
    assert resp.status_code == 422, resp.text
    assert _count(db_session, AnswerImage) == 0
    assert _stored_files(storage_dir) == []


def test_declared_type_diverging_from_content_is_rejected(
    client, db_session, professor_token, owned_answer, storage_dir
):
    resp = _upload(
        client,
        professor_token,
        owned_answer,
        _image_bytes("PNG"),
        filename="foto.jpg",
        content_type="image/jpeg",
    )
    assert resp.status_code == 422
    assert _stored_files(storage_dir) == []


def test_real_gif_is_rejected_even_when_declared_as_png(
    client, professor_token, owned_answer, storage_dir
):
    resp = _upload(client, professor_token, owned_answer, _image_bytes("GIF"))
    assert resp.status_code == 422
    resp = _upload(
        client, professor_token, owned_answer, _image_bytes("GIF"), filename="a.gif", content_type="image/gif"
    )
    assert resp.status_code == 422
    assert _stored_files(storage_dir) == []


def test_empty_or_missing_file_is_rejected(client, professor_token, owned_answer, storage_dir):
    assert _upload(client, professor_token, owned_answer, b"").status_code == 422
    resp = client.post(
        f"/v1/answers/{owned_answer}/images",
        data={"outro": "campo"},
        headers=_headers(professor_token),
    )
    assert resp.status_code == 422
    assert _stored_files(storage_dir) == []


# ---------------- AC-05: limite de tamanho ----------------
def test_oversized_upload_rejected_by_content_length(
    client, db_session, professor_token, owned_answer, storage_dir, monkeypatch
):
    monkeypatch.setattr(get_settings(), "answer_image_max_bytes", 1024)
    resp = _upload(client, professor_token, owned_answer, b"\x89PNG" + b"\x00" * 200_000)
    assert resp.status_code == 413
    assert _count(db_session, AnswerImage) == 0
    assert _stored_files(storage_dir) == []


def test_oversized_upload_rejected_while_streaming(
    client, db_session, professor_token, owned_answer, storage_dir, monkeypatch
):
    # Content-Length fica dentro da folga multipart: só a contagem real dos
    # bytes lidos (segunda defesa) barra o arquivo, e o temporário é removido.
    monkeypatch.setattr(get_settings(), "answer_image_max_bytes", 1024)
    resp = _upload(client, professor_token, owned_answer, b"\x89PNG" + b"\x00" * 2000)
    assert resp.status_code == 413
    assert _count(db_session, AnswerImage) == 0
    assert _stored_files(storage_dir) == []


# ---------------- AC-06: nome adversarial ----------------
def test_adversarial_filename_is_metadata_only(
    client, db_session, professor_token, owned_answer, storage_dir, tmp_path
):
    content = _image_bytes("PNG")
    resp = _upload(
        client, professor_token, owned_answer, content, filename="../../../etc/passwd\x1b‮.png"
    )
    assert resp.status_code == 201, resp.text
    original = resp.json()["original_filename"]
    assert "\x1b" not in original and "‮" not in original
    assert "etc/passwd" in original

    [stored] = _stored_files(storage_dir)
    assert _SERVER_NAME.match(stored.name)
    assert stored.resolve().parent == storage_dir.resolve()
    assert not (storage_dir / "../../../etc/passwd.png").resolve().exists()
    outside = [
        p
        for p in tmp_path.rglob("*")
        if p.is_file() and storage_dir not in p.parents and not p.name.startswith("test.db")
    ]
    assert outside == []


def test_sanitize_original_filename():
    sanitize = images_module._sanitize_original_filename
    assert sanitize("\x00a\nb\tc​\x7f.png") == "abc.png"
    assert sanitize("  \x01  ") == "sem-nome"
    assert sanitize(None) == "sem-nome"
    assert len(sanitize("x" * 1000)) == 255


# ---------------- AC-07: falha de armazenamento ----------------
def test_unavailable_storage_dir_leaves_no_record(
    client, db_session, professor_token, owned_answer, tmp_path, monkeypatch
):
    blocker = tmp_path / "not-a-directory"
    blocker.write_text("ocupa o caminho do diretório")
    monkeypatch.setattr(get_settings(), "answer_images_storage_dir", str(blocker))
    resp = _upload(client, professor_token, owned_answer, _image_bytes("PNG"))
    assert resp.status_code == 500
    assert str(blocker) not in resp.text
    assert _count(db_session, AnswerImage) == 0


def test_failure_finalizing_file_leaves_no_record_and_no_file(
    client, db_session, professor_token, owned_answer, storage_dir, monkeypatch
):
    def fail_replace(*_args, **_kwargs):
        raise OSError("disco cheio simulado")

    monkeypatch.setattr(images_module.os, "replace", fail_replace)
    resp = _upload(client, professor_token, owned_answer, _image_bytes("PNG"))
    assert resp.status_code == 500
    assert _count(db_session, AnswerImage) == 0
    assert _stored_files(storage_dir) == []


def test_commit_failure_removes_stored_file(
    client, db_session, professor_token, owned_answer, storage_dir, monkeypatch
):
    def fail_commit(_self):
        raise OperationalError("COMMIT", {}, Exception("banco indisponível simulado"))

    with monkeypatch.context() as patch:
        patch.setattr(Session, "commit", fail_commit)
        resp = _upload(client, professor_token, owned_answer, _image_bytes("PNG"))
    assert resp.status_code == 500
    assert _count(db_session, AnswerImage) == 0
    assert _stored_files(storage_dir) == []


# ---------------- AC-08: recuperação autorizada ----------------
def test_owner_downloads_original_bytes(client, professor_token, owned_answer, storage_dir):
    content = _image_bytes("JPEG")
    image_id = _upload(
        client, professor_token, owned_answer, content, filename="f.jpg", content_type="image/jpeg"
    ).json()["id"]
    resp = client.get(f"/v1/answer-images/{image_id}/download", headers=_headers(professor_token))
    assert resp.status_code == 200
    assert resp.content == content
    assert resp.headers["content-type"].startswith("image/jpeg")
    assert resp.headers["x-content-type-options"] == "nosniff"


def test_other_professor_cannot_download_or_list(
    client, professor_token, second_professor_token, owned_answer, storage_dir
):
    image_id = _upload(client, professor_token, owned_answer, _image_bytes("PNG")).json()["id"]
    headers = _headers(second_professor_token)
    assert client.get(f"/v1/answer-images/{image_id}/download", headers=headers).status_code == 403
    assert client.get(f"/v1/answers/{owned_answer}/images", headers=headers).status_code == 403


def test_list_returns_newest_first(client, professor_token, owned_answer, storage_dir):
    first = _upload(client, professor_token, owned_answer, _image_bytes("PNG")).json()["id"]
    second = _upload(client, professor_token, owned_answer, _image_bytes("PNG", (16, 16))).json()["id"]
    resp = client.get(f"/v1/answers/{owned_answer}/images", headers=_headers(professor_token))
    assert resp.status_code == 200
    assert [item["id"] for item in resp.json()] == [second, first]
    assert len(_stored_files(storage_dir)) == 2  # reenvio preserva o original anterior


# ---------------- AC-09: sem exposição pública ----------------
def test_images_are_never_public(client, professor_token, owned_answer, storage_dir):
    image_id = _upload(client, professor_token, owned_answer, _image_bytes("PNG")).json()["id"]
    assert client.get(f"/v1/answer-images/{image_id}/download").status_code == 401
    assert client.get(f"/v1/answers/{owned_answer}/images").status_code == 401
    assert not any(isinstance(route, Mount) for route in main_module.app.routes)


# ---------------- AC-10: sem OCR e sem correção ----------------
def test_upload_does_not_create_correction_job(
    client, db_session, professor_token, owned_answer, storage_dir
):
    assert _upload(client, professor_token, owned_answer, _image_bytes("PNG")).status_code == 201
    assert _count(db_session, CorrectionJob) == 0


def test_images_module_has_no_ocr_or_correction_references():
    tree = ast.parse(Path(images_module.__file__).read_text(encoding="utf-8"))
    identifiers: set[str] = set()
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            identifiers.add(node.id)
        elif isinstance(node, ast.Attribute):
            identifiers.add(node.attr)
        elif isinstance(node, ast.alias):
            identifiers.add(node.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
    forbidden = {
        "run_correction_job",
        "request_correction",
        "CorrectionJob",
        "AIExecution",
        "BackgroundTasks",
        "ai_engine_url",
        "httpx",
    }
    assert identifiers.isdisjoint(forbidden)
    assert not any(
        word in module.lower() for module in modules for word in ("ocr", "tesseract", "correction", "httpx")
    )
