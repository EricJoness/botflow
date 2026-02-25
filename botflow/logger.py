"""
Logging estruturado para o botflow.
Emite logs em JSON com correlation-id e contexto de step.
"""
from __future__ import annotations

import json
import logging
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Optional


def _formatar_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


class JsonFormatter(logging.Formatter):
    """Formata logs como JSON de uma linha (ndjson)."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": _formatar_timestamp(),
            "nivel": record.levelname,
            "modulo": record.module,
            "mensagem": record.getMessage(),
        }
        # campos extras passados via extra={}
        for chave, valor in record.__dict__.items():
            if chave.startswith("bf_"):
                payload[chave[3:]] = valor

        if record.exc_info:
            payload["excecao"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def criar_logger(
    nome: str = "botflow",
    nivel: int = logging.DEBUG,
    correlation_id: Optional[str] = None,
) -> "BotflowLogger":
    """
    Cria e retorna um logger configurado para o botflow.

    Args:
        nome: Nome do logger.
        nivel: Nível mínimo de log (ex.: logging.INFO).
        correlation_id: ID de correlação da execução atual.

    Returns:
        Instância de BotflowLogger.
    """
    return BotflowLogger(nome=nome, nivel=nivel, correlation_id=correlation_id)


class BotflowLogger:
    """
    Logger estruturado em JSON para o botflow.

    Adiciona automaticamente `correlation_id` a cada mensagem.

    Exemplo::

        logger = criar_logger()
        logger.info("Step iniciado", step="LoginStep", tentativa=1)
    """

    def __init__(
        self,
        nome: str = "botflow",
        nivel: int = logging.DEBUG,
        correlation_id: Optional[str] = None,
    ) -> None:
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self._logger = logging.getLogger(f"{nome}.{self.correlation_id[:8]}")
        self._logger.setLevel(nivel)

        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(JsonFormatter())
            self._logger.addHandler(handler)
            self._logger.propagate = False

    def _extra(self, kwargs: dict) -> dict:
        base = {"bf_correlation_id": self.correlation_id}
        for k, v in kwargs.items():
            base[f"bf_{k}"] = v
        return {"extra": base}

    def debug(self, mensagem: str, **kwargs: Any) -> None:
        self._logger.debug(mensagem, **self._extra(kwargs))

    def info(self, mensagem: str, **kwargs: Any) -> None:
        self._logger.info(mensagem, **self._extra(kwargs))

    def warning(self, mensagem: str, **kwargs: Any) -> None:
        self._logger.warning(mensagem, **self._extra(kwargs))

    def error(self, mensagem: str, **kwargs: Any) -> None:
        self._logger.error(mensagem, **self._extra(kwargs))

    def critical(self, mensagem: str, **kwargs: Any) -> None:
        self._logger.critical(mensagem, **self._extra(kwargs))
