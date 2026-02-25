"""Testes dos hooks e plugins do botflow."""
import pytest
from botflow import Flow, BaseStep
from botflow.hooks import HookManager
from botflow.plugins import BotflowPlugin, PluginManager
from botflow.step import StepStatus


class StepSimples(BaseStep):
    nome = "Simples"
    def executar(self, ctx):
        return {"x": 1}


# ── HookManager ────────────────────────────────────────────────────────────

def test_hook_antes_chamado():
    chamados = []
    hooks = HookManager()

    @hooks.antes_do_step
    def antes(step, ctx):
        chamados.append(f"antes:{step.nome}")

    flow = Flow()
    flow.hooks = hooks
    flow.step(StepSimples())
    flow.executar()

    assert "antes:Simples" in chamados


def test_hook_apos_chamado():
    chamados = []
    hooks = HookManager()

    @hooks.apos_o_step
    def apos(step, resultado, ctx):
        chamados.append(f"apos:{step.nome}:{resultado.status.value}")

    flow = Flow()
    flow.hooks = hooks
    flow.step(StepSimples())
    flow.executar()

    assert "apos:Simples:sucesso" in chamados


# ── PluginManager ──────────────────────────────────────────────────────────

def test_plugin_ciclo_de_vida():
    eventos = []

    class MeuPlugin(BotflowPlugin):
        nome = "teste"

        def ao_iniciar_flow(self, flow):
            eventos.append("iniciar_flow")

        def ao_finalizar_flow(self, flow, resultados):
            eventos.append("finalizar_flow")

        def ao_iniciar_step(self, step, ctx):
            eventos.append(f"iniciar_step:{step.nome}")

        def ao_finalizar_step(self, step, resultado, ctx):
            eventos.append(f"finalizar_step:{step.nome}")

    flow = Flow()
    flow.usar_plugin(MeuPlugin())
    flow.step(StepSimples())
    flow.executar()

    assert eventos == [
        "iniciar_flow",
        "iniciar_step:Simples",
        "finalizar_step:Simples",
        "finalizar_flow",
    ]


def test_plugin_ao_falhar_step():
    falhas = []

    class PluginFalha(BotflowPlugin):
        def ao_falhar_step(self, step, erro, ctx):
            falhas.append(str(erro))

    class StepRuim(BaseStep):
        nome = "Ruim"
        def executar(self, ctx):
            raise RuntimeError("boom")

    flow = Flow(parar_na_falha=False)
    flow.usar_plugin(PluginFalha())
    flow.step(StepRuim())
    flow.executar()

    assert "boom" in falhas[0]
