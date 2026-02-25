"""
Políticas de retry para steps do botflow.

Suporta: fixo, exponencial com jitter.
"""
from __future__ import annotations

import abc
import random
import time
from dataclasses import dataclass, field
from typing import Type


class RetryPolicy(abc.ABC):
    """Interface base para políticas de retry."""

    max_tentativas: int = 3
    excecoes: tuple[Type[Exception], ...] = (Exception,)

    @abc.abstractmethod
    def calcular_espera(self, tentativa: int) -> float:
        """Retorna quantos segundos esperar antes da próxima tentativa."""
        ...

    def deve_tentar_novamente(self, tentativa: int, erro: Exception) -> bool:
        """Retorna True se deve tentar novamente com base na tentativa e erro."""
        if tentativa >= self.max_tentativas:
            return False
        return isinstance(erro, self.excecoes)


@dataclass
class FixedDelay(RetryPolicy):
    """
    Retry com intervalo fixo entre tentativas.

    Exemplo::

        policy = FixedDelay(max_tentativas=3, espera_segundos=2.0)
    """

    max_tentativas: int = 3
    espera_segundos: float = 1.0
    excecoes: tuple[Type[Exception], ...] = field(default_factory=lambda: (Exception,))

    def calcular_espera(self, tentativa: int) -> float:
        return self.espera_segundos


@dataclass
class ExponentialBackoff(RetryPolicy):
    """
    Retry com backoff exponencial e jitter opcional.

    Fórmula: espera = base * (2 ** tentativa) ± jitter

    Exemplo::

        policy = ExponentialBackoff(
            max_tentativas=5,
            base_segundos=0.5,
            max_espera_segundos=30.0,
            jitter=True,
        )
    """

    max_tentativas: int = 5
    base_segundos: float = 0.5
    max_espera_segundos: float = 60.0
    jitter: bool = True
    excecoes: tuple[Type[Exception], ...] = field(default_factory=lambda: (Exception,))

    def calcular_espera(self, tentativa: int) -> float:
        espera = self.base_segundos * (2 ** tentativa)
        if self.jitter:
            espera += random.uniform(0, espera * 0.1)
        return min(espera, self.max_espera_segundos)


def executar_com_retry(
    funcao,
    policy: RetryPolicy,
    *args,
    **kwargs,
):
    """
    Executa `funcao` aplicando a política de retry.

    Args:
        funcao: Callable a ser executado.
        policy: Instância de RetryPolicy.
        *args, **kwargs: Argumentos repassados para `funcao`.

    Returns:
        Resultado de `funcao` em caso de sucesso.

    Raises:
        Exception: Última exceção capturada ao esgotar as tentativas.
    """
    ultimo_erro: Exception = RuntimeError("Sem tentativas")

    for tentativa in range(1, policy.max_tentativas + 1):
        try:
            return funcao(*args, **kwargs), tentativa
        except Exception as erro:
            ultimo_erro = erro
            if not policy.deve_tentar_novamente(tentativa, erro):
                break
            espera = policy.calcular_espera(tentativa)
            time.sleep(espera)

    raise ultimo_erro
