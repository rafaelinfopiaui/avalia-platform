import pytest
from typing import List
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import RubricCriterionInput


@pytest.fixture
def sample_rubric() -> List[dict]:
    return [
        {
            "criterion_id": "crit_lifo",
            "name": "Conceito de Pilha (LIFO)",
            "description": "Explicação correta de que a pilha opera no modelo Last-In, First-Out (o último a entrar é o primeiro a sair).",
            "max_score": 2.5,
        },
        {
            "criterion_id": "crit_fifo",
            "name": "Conceito de Fila (FIFO)",
            "description": "Explicação correta de que a fila opera no modelo First-In, First-Out (o primeiro a entrar é o primeiro a sair).",
            "max_score": 2.5,
        },
    ]


@pytest.fixture
def sample_payload(sample_rubric) -> dict:
    return {
        "question_statement": "Explique a diferença fundamental entre as estruturas de dados Pilha e Fila, mencionando suas políticas de acesso (LIFO e FIFO).",
        "reference_answer": "A Pilha opera com a política LIFO (Last-In, First-Out), onde o último elemento inserido é o primeiro a ser removido (ex.: pilha de pratos). A Fila opera com FIFO (First-In, First-Out), onde o primeiro elemento inserido é o primeiro a ser removido (ex.: fila de banco).",
        "rubric": sample_rubric,
        "answer_text": "A pilha é uma estrutura LIFO em que o último que entra é o primeiro a sair. Já a fila é FIFO, onde o primeiro que entra é o primeiro que sai.",
    }


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
