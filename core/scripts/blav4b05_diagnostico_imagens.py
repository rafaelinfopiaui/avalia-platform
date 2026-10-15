"""BL-AV-4B-05 (ACD-13) — diagnóstico de divergências entre storage e registros de imagem.

Rotina sob demanda, fora da aplicação e SOMENTE LEITURA: compara o diretório de
armazenamento de imagens de resposta com a tabela `answer_images` e relata, sem
corrigir nada:

- (a) registro ATIVO (`deleted_at IS NULL`) apontando para arquivo ausente;
- (b) arquivo sem registro ativo, em duas classes:
  - `orphan_files`: arquivo sem nenhum registro;
  - `retained_deleted_files`: arquivo de imagem excluída logicamente, mantido
    por desenho (D1 — sem remoção física nesta fatia); esperado, não divergência;
- registro excluído logicamente cujo arquivo já não existe
  (`deleted_missing_file`): a restauração dessa imagem não será possível.

Garantias de leitura: a conexão é aberta em modo somente leitura no próprio
banco (PostgreSQL: transação READ ONLY; SQLite: `PRAGMA query_only`), só há
consultas SELECT e o diretório é apenas listado. Imagens são identificadas por
id; arquivos órfãos, pelo nome gerado pelo servidor. Nunca imprime nome
original, hash ou conteúdo.

Uso (banco e diretório SEMPRE explícitos; não há valor padrão):

    python scripts/blav4b05_diagnostico_imagens.py \\
        --database-url postgresql+psycopg2://localhost:5432/<banco> \\
        --storage-dir var/answer_images

Código de saída: 0 sem divergências; 1 se houver (a) ou arquivo órfão.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

_QUERY = text("SELECT id, storage_filename, deleted_at FROM answer_images ORDER BY id")


def _read_records(database_url: str) -> list[tuple[str, str, bool]]:
    engine = create_engine(database_url, future=True)
    try:
        with engine.connect() as conn:
            if engine.dialect.name == "postgresql":
                conn = conn.execution_options(postgresql_readonly=True)
            elif engine.dialect.name == "sqlite":
                conn.exec_driver_sql("PRAGMA query_only = ON")
            rows = conn.execute(_QUERY).all()
            conn.rollback()
    finally:
        engine.dispose()
    return [(row.id, row.storage_filename, row.deleted_at is not None) for row in rows]


def _stored_files(storage_dir: Path) -> set[str]:
    if not storage_dir.is_dir():
        return set()
    return {entry.name for entry in storage_dir.iterdir() if entry.is_file()}


def diagnose(database_url: str, storage_dir: Path) -> dict:
    storage_dir = Path(storage_dir).resolve()
    files = _stored_files(storage_dir)
    records = _read_records(database_url)

    referenced: set[str] = set()
    active_missing: list[str] = []
    deleted_missing: list[str] = []
    retained_deleted: list[str] = []
    for image_id, storage_filename, deleted in records:
        # Mesmo critério do download: o arquivo precisa estar diretamente no diretório.
        inside = (storage_dir / storage_filename).resolve().parent == storage_dir
        present = inside and storage_filename in files
        if inside:
            referenced.add(storage_filename)
        if deleted:
            (retained_deleted if present else deleted_missing).append(image_id)
        elif not present:
            active_missing.append(image_id)

    orphan_files = sorted(files - referenced)
    return {
        "storage_dir_exists": storage_dir.is_dir(),
        "records": len(records),
        "files": len(files),
        "active_missing_file": sorted(active_missing),
        "orphan_files": orphan_files,
        "retained_deleted_files": sorted(retained_deleted),
        "deleted_missing_file": sorted(deleted_missing),
        "divergences": len(active_missing) + len(orphan_files),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--storage-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    report = diagnose(args.database_url, args.storage_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["divergences"] else 0


if __name__ == "__main__":
    sys.exit(main())
