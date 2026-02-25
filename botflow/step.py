"""
Define a estrutura base de um Step no botflow.
"""
from __future__ import annotations

import abc
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class StepStatus(str, Enum):
    """Status possíveis de um step após execução."""

    SUCESSO = "sucesso"
    FALHA = "falha"
    PULADO = "pulado"


@dataclass
class StepResult:
    """Resultado da execução de um step."""

    status: StepStatus
    dados: Any = None
    erro: Optional[Exception] = None
    duracao_segundos: float = 0.0
    tentativas: int = 1
    mensagem: str = ""

    @property
    def teve_sucesso(self) -> bool:
        return self.status == StepStatus.SUCESSO

    def __repr__(self) -> str:
        return (
            f"StepResult(status={self.status.value!r}, "
            f"tentativas={self.tentativas}, "
            f"duracao={self.duracao_segundos:.2f}s)"
        )


class BaseStep(abc.ABC):
    """
    Classe base para todos os steps do botflow.

    Subclasse deve implementar o método `executar`.

    Exemplo::

        class LoginStep(BaseStep):
            nome = "Login no sistema"

            def executar(self, contexto):
                # lógica de login
                return {"usuario": "admin"}
    """

    nome: str = ""
    descricao: str = ""

    def __init__(self) -> None:
        if not self.nome:
            self.nome = self.__class__.__name__

    @abc.abstractmethod
    def executar(self, contexto: dict[str, Any]) -> Any:
        """
        Lógica principal do step.

        Args:
            contexto: Dicionário compartilhado entre todos os steps do flow.

        Returns:
            Dados a serem armazenados no contexto (opcional).
        """
        ...

    def deve_pular(self, contexto: dict[str, Any]) -> bool:
        """
        Retorna True se o step deve ser pulado.

        Sobrescreva para adicionar lógica condicional.
        """
        return False

    def _executar_com_medicao(self, contexto: dict[str, Any]) -> tuple[Any, float]:
        inicio = time.monotonic()
        resultado = self.executar(contexto)
        duracao = time.monotonic() - inicio
        return resultado, duracao

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(nome={self.nome!r})"
