"""Popula dados FICTÍCIOS para a demonstração do AvalIA.
Uso: python -m app.seed  (com o venv ativo e DATABASE_URL configurado)
"""
from __future__ import annotations

from decimal import Decimal

from app.config import get_settings
from app.db import Base, SessionLocal, engine
from app.models import Answer, Assessment, AssessmentStatus, Question, Role, Rubric, RubricCriterion, User
from app.security import hash_password

settings = get_settings()


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == settings.seed_professor_email).first()
        if existing:
            print(f"Seed já aplicado (usuário {settings.seed_professor_email} existe). Nada a fazer.")
            return

        professor = User(
            email=settings.seed_professor_email,
            password_hash=hash_password(settings.seed_professor_password),
            role=Role.PROFESSOR,
            is_active=True,
        )
        db.add(professor)
        db.flush()

        assessment = Assessment(
            title="Estruturas de Dados — Avaliação 1", owner_id=professor.id, status=AssessmentStatus.RASCUNHO,
        )
        db.add(assessment)
        db.flush()

        question = Question(
            assessment_id=assessment.id,
            statement="Explique a diferença entre pilha e fila.",
            reference_answer=(
                "Pilha (stack) segue o princípio LIFO (Last In, First Out): o último "
                "elemento inserido é o primeiro a ser removido. Fila (queue) segue o "
                "princípio FIFO (First In, First Out): o primeiro elemento inserido é "
                "o primeiro a ser removido. A pilha tem operações push/pop em uma única "
                "extremidade; a fila tem enqueue no final e dequeue no início."
            ),
            max_score=Decimal("6.00"),
        )
        db.add(question)
        db.flush()

        rubric = Rubric(question_id=question.id, version=1, is_published=False)
        db.add(rubric)
        db.flush()

        criteria = [
            ("Identifica LIFO na pilha", "Reconhece que a pilha segue Last In, First Out.", Decimal("1.50")),
            ("Identifica FIFO na fila", "Reconhece que a fila segue First In, First Out.", Decimal("1.50")),
            (
                "Diferenciação clara",
                "Contrasta explicitamente pilha e fila (não apenas define isoladamente).",
                Decimal("1.50"),
            ),
            ("Clareza e precisão", "Texto claro, correto tecnicamente, sem ambiguidade.", Decimal("1.50")),
        ]
        for name, desc, max_score in criteria:
            db.add(RubricCriterion(rubric_id=rubric.id, name=name, description=desc, max_score=max_score))
        db.flush()

        # Publicar diretamente no seed para já ter uma questão pronta pra correção na demo
        rubric.is_published = True
        assessment.status = AssessmentStatus.PUBLICADA

        answers = [
            (
                "Aluno Ficticio A (resposta correta)",
                "Pilha segue LIFO: o último item inserido é o primeiro a sair, como "
                "uma pilha de pratos. Fila segue FIFO: o primeiro item inserido é o "
                "primeiro a sair, como uma fila de banco. Na pilha usamos push e pop "
                "na mesma extremidade; na fila inserimos no final (enqueue) e "
                "removemos no início (dequeue).",
            ),
            (
                "Aluno Ficticio B (resposta parcial)",
                "Pilha é LIFO, o último que entra é o primeiro que sai. Fila eu não "
                "lembro bem a ordem, acho que também tem a ver com a ordem de "
                "chegada dos elementos.",
            ),
            (
                "Aluno Ficticio C (resposta conceitualmente errada)",
                "Pilha e fila são a mesma coisa, só mudam o nome dependendo da "
                "linguagem de programação. Os dois inserem e removem elementos do "
                "início da estrutura.",
            ),
        ]
        for student_name, text in answers:
            db.add(Answer(question_id=question.id, student_name_fake=student_name, text=text))

        db.commit()
        print("Seed aplicado com sucesso:")
        print(f"  Professor: {settings.seed_professor_email} / senha em SEED_PROFESSOR_PASSWORD")
        print(f"  Avaliação: {assessment.id} — {assessment.title}")
        print(f"  Questão: {question.id}")
        print(f"  Rubrica publicada: {rubric.id} (4 critérios, soma 6.00 = valor da questão)")
        print(f"  {len(answers)} respostas fictícias inseridas (correta/parcial/errada).")
    finally:
        db.close()


if __name__ == "__main__":
    run()
