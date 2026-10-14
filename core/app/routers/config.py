"""Endpoint público de capacidades do Core (BL-AV-S03B-01).

Fonte ÚNICA de verdade sobre quais módulos opcionais estão ligados. O frontend
consulta este endpoint em vez de reimplementar o parsing de variável de ambiente
(`VITE_ACADEMIC_MODULE_ENABLED`), que era a causa raiz de `DEBT-AV-012`: duas
configurações independentes podiam divergir em operação (ex.: módulo ligado só
no backend), fazendo a UI permitir o que o backend rejeita, ou vice-versa.

NOTA (contrato/segurança): o endpoint é público (sem autenticação) por ser
configuração de produto, não dado de usuário — expõe apenas booleans de
capacidade, nenhum segredo, nenhuma informação sobre contas ou turmas. A
decisão de publicar capacidades NÃO afrouxa autorização: a flag não substitui
as regras de vínculo professor↔turma e de propriedade de avaliação já
homologadas em `DEC-AV-023`/`DEC-AV-027` e aplicadas em
`core/app/routers/academic.py`. Ligar o módulo não concede acesso a nada; o
enforcement real permanece nos endpoints de domínio.
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_settings

router = APIRouter(prefix="/v1/config", tags=["config"])


class CapabilitiesOut(BaseModel):
    academic_module_enabled: bool


@router.get("/capabilities", response_model=CapabilitiesOut)
def get_capabilities() -> CapabilitiesOut:
    # Lê diretamente de Settings: a lógica de parsing da env var
    # ACADEMIC_MODULE_ENABLED existe em um único lugar (app/config.py) e não é
    # replicada aqui nem no frontend.
    return CapabilitiesOut(academic_module_enabled=get_settings().academic_module_enabled)
