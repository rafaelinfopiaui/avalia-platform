"""Gate global de inferência do Core (AV-S07B, lacuna C).

Extração por visão (/transcription/extract) e análise textual
(run_correction_job) usam o MESMO Ollama local; rodando juntas, disputam a
memória da máquina. Este gate serializa as duas: no máximo UMA inferência por
vez, independentemente de qual resposta está sendo processada (o bloqueio por
resposta continua existindo à parte).

Comportamento escolhido (espera com timeout, depois rejeição explícita):
- quem chega com o gate ocupado ESPERA até ``wait_timeout`` segundos;
- esgotado o prazo, recebe ``InferenceBusyError`` (código INFERENCE_BUSY) —
  a extração vira 409 para a UI, a análise vira job FALHA com mensagem clara;
  nada fica "processando" indefinidamente;
- o gate é SEMPRE liberado no ``finally`` (sucesso, falha, timeout ou cancelamento).

LIMITAÇÃO: trava em memória (asyncio.Lock) — vale só para UM processo
(uvicorn com um único worker, que é o modo de execução local do AvalIA). Com
vários workers/processos ou máquinas cada um teria o próprio gate; isto NÃO
substitui coordenação distribuída (fila/Redis), que está fora do escopo.
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

INFERENCE_BUSY = "INFERENCE_BUSY"
# Extração é síncrona (o usuário está esperando a resposta HTTP): espera curta.
EXTRACTION_WAIT_SECONDS = 10.0
# Análise roda em background (a UI acompanha o job por polling): pode esperar
# uma extração inteira (timeout de 150 s no Core) antes de desistir.
CORRECTION_WAIT_SECONDS = 180.0


class InferenceBusyError(Exception):
    """O gate continuou ocupado por outra inferência até o fim da espera."""

    code = INFERENCE_BUSY

    def __init__(self, operation: str, busy_with: str | None, waited_seconds: float):
        self.operation = operation
        self.busy_with = busy_with
        self.waited_seconds = waited_seconds
        super().__init__(
            f"Motor de IA local ocupado ({busy_with or 'outra inferência'}); "
            f"'{operation}' esperou {waited_seconds:.0f}s e não foi iniciada."
        )


class InferenceGate:
    def __init__(self) -> None:
        self._lock: asyncio.Lock | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self.busy_with: str | None = None

    def _get_lock(self) -> asyncio.Lock:
        # asyncio.Lock fica preso ao event loop em que houve disputa; um loop
        # novo (ex.: reinício do servidor nos testes) recebe uma trava nova.
        loop = asyncio.get_running_loop()
        if self._lock is None or (self._loop is not loop and not self._lock.locked()):
            self._lock = asyncio.Lock()
            self._loop = loop
        return self._lock

    @asynccontextmanager
    async def hold(self, operation: str, wait_timeout: float):
        lock = self._get_lock()
        try:
            await asyncio.wait_for(lock.acquire(), timeout=wait_timeout)
        except asyncio.TimeoutError:
            raise InferenceBusyError(operation, self.busy_with, wait_timeout) from None
        self.busy_with = operation
        try:
            yield
        finally:
            self.busy_with = None
            lock.release()


# Instância única do processo (ver LIMITAÇÃO acima).
inference_gate = InferenceGate()
