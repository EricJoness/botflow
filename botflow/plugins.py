"""
Sistema de plugins para o botflow.
"""
from __future__ import annotations

from typing import Any, Callable, Type


class BotflowPlugin:
    """
    Classe base para plugins do botflow.

    Subclasse pode sobrescrever qualquer método de ciclo de vida.

    Exemplo::

        class MetricasPlugin(BotflowPlugin):
            nome = "metricas"

            def ao_iniciar_flow(self, flow):
                self._inicio = time.monotonic()

            def ao_finalizar_flow(self, flow, resultados):
                duracao = time.monotonic() - self._inicio
                print(f"Flow concluído em {duracao:.2f}s")
    """

    nome: str = ""

    def ao_iniciar_flow(self, flow: Any) -> None:
        """Chamado antes do flow começar."""

    def ao_finalizar_flow(self, flow: Any, resultados: list) -> None:
        """Chamado depois que todos os steps terminam."""

    def ao_iniciar_step(self, step: Any, contexto: dict) -> None:
        """Chamado antes de cada step."""

    def ao_finalizar_step(self, step: Any, resultado: Any, contexto: dict) -> None:
        """Chamado após cada step."""

    def ao_falhar_step(self, step: Any, erro: Exception, contexto: dict) -> None:
        """Chamado quando um step lança exceção (antes do retry)."""


class PluginManager:
    """
    Gerencia o ciclo de vida dos plugins registrados.

    Exemplo::

        pm = PluginManager()
        pm.registrar(MetricasPlugin())
        pm.registrar(ObservabilidadePlugin())
    """

    def __init__(self) -> None:
        self._plugins: list[BotflowPlugin] = []

    def registrar(self, plugin: BotflowPlugin) -> "PluginManager":
        """Adiciona um plugin ao gerenciador. Retorna self para encadeamento."""
        self._plugins.append(plugin)
        return self

    def _disparar(self, evento: str, *args, **kwargs) -> None:
        for plugin in self._plugins:
            metodo = getattr(plugin, evento, None)
            if callable(metodo):
                metodo(*args, **kwargs)

    def ao_iniciar_flow(self, flow: Any) -> None:
        self._disparar("ao_iniciar_flow", flow)

    def ao_finalizar_flow(self, flow: Any, resultados: list) -> None:
        self._disparar("ao_finalizar_flow", flow, resultados)

    def ao_iniciar_step(self, step: Any, contexto: dict) -> None:
        self._disparar("ao_iniciar_step", step, contexto)

    def ao_finalizar_step(self, step: Any, resultado: Any, contexto: dict) -> None:
        self._disparar("ao_finalizar_step", step, resultado, contexto)

    def ao_falhar_step(self, step: Any, erro: Exception, contexto: dict) -> None:
        self._disparar("ao_falhar_step", step, erro, contexto)
