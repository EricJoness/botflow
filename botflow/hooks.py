"""
Sistema de hooks (before/after) para steps do botflow.
"""
from __future__ import annotations

from typing import Callable, Any


HookFn = Callable[..., None]


class HookManager:
    """
    Gerencia hooks que são chamados antes e depois de cada step.

    Exemplo::

        hooks = HookManager()

        @hooks.antes_do_step
        def log_inicio(step, contexto):
            print(f"Iniciando: {step.nome}")

        @hooks.apos_o_step
        def log_fim(step, resultado, contexto):
            print(f"Finalizado: {step.nome} → {resultado.status.value}")
    """

    def __init__(self) -> None:
        self._antes: list[HookFn] = []
        self._apos: list[HookFn] = []

    def antes_do_step(self, fn: HookFn) -> HookFn:
        """Registra um hook chamado ANTES de cada step."""
        self._antes.append(fn)
        return fn

    def apos_o_step(self, fn: HookFn) -> HookFn:
        """Registra um hook chamado APÓS cada step."""
        self._apos.append(fn)
        return fn

    def disparar_antes(self, step: Any, contexto: dict) -> None:
        for hook in self._antes:
            hook(step, contexto)

    def disparar_apos(self, step: Any, resultado: Any, contexto: dict) -> None:
        for hook in self._apos:
            hook(step, resultado, contexto)

    def registrar_antes(self, fn: HookFn) -> None:
        """Registra um hook antes_do_step via método direto."""
        self._antes.append(fn)

    def registrar_apos(self, fn: HookFn) -> None:
        """Registra um hook apos_o_step via método direto."""
        self._apos.append(fn)
