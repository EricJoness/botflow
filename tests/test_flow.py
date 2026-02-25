"""Testes do módulo flow.py do botflow."""
import pytest
from botflow import Flow, BaseStep, ExponentialBackoff, FixedDelay
from botflow.step import StepStatus
from botflow.flow import FlowError


# ── Helpers ────────────────────────────────────────────────────────────────

class StepSucesso(BaseStep):
    nome = "Step OK"
    def executar(self, contexto):
        return {"ok": True}


class StepFalha(BaseStep):
    nome = "Step Falha"
    def executar(self, contexto):
        raise ValueError("falha proposital")


class StepPulado(BaseStep):
    nome = "Step Pulado"
    def deve_pular(self, contexto):
        return True
    def executar(self, contexto):
        return {}


class StepContador(BaseStep):
    nome = "Contador"
    def __init__(self):
        super().__init__()
        self.chamadas = 0

    def executar(self, contexto):
        self.chamadas += 1
        if self.chamadas < 3:
            raise RuntimeError(f"tentativa {self.chamadas}")
        return {"chamadas": self.chamadas}


# ── Testes ─────────────────────────────────────────────────────────────────

def test_flow_basico_sucesso():
    flow = Flow(nome="Teste")
    flow.step(StepSucesso())
    resultados = flow.executar()

    assert len(resultados) == 1
    assert resultados[0].status == StepStatus.SUCESSO
    assert resultados[0].dados == {"ok": True}


def test_flow_dois_steps():
    flow = Flow()
    flow.step(StepSucesso())
    flow.step(StepSucesso())
    resultados = flow.executar()

    assert len(resultados) == 2
    assert all(r.teve_sucesso for r in resultados)


def test_flow_parar_na_falha():
    flow = Flow(parar_na_falha=True)
    flow.step(StepSucesso())
    flow.step(StepFalha())
    flow.step(StepSucesso())

    with pytest.raises(FlowError) as exc_info:
        flow.executar()

    assert "Step Falha" in str(exc_info.value)


def test_flow_nao_parar_na_falha():
    flow = Flow(parar_na_falha=False)
    flow.step(StepSucesso())
    flow.step(StepFalha())
    flow.step(StepSucesso())

    resultados = flow.executar()

    assert len(resultados) == 3
    assert resultados[1].status == StepStatus.FALHA
    assert resultados[2].status == StepStatus.SUCESSO


def test_step_pulado():
    flow = Flow()
    flow.step(StepPulado())
    resultados = flow.executar()

    assert resultados[0].status == StepStatus.PULADO


def test_retry_sucede_na_terceira_tentativa():
    step = StepContador()
    flow = Flow(parar_na_falha=True)
    flow.step(step, retry=FixedDelay(max_tentativas=5, espera_segundos=0.0))

    resultados = flow.executar()

    assert resultados[0].teve_sucesso
    assert resultados[0].tentativas == 3


def test_retry_esgota_tentativas():
    flow = Flow(parar_na_falha=True)
    flow.step(StepFalha(), retry=FixedDelay(max_tentativas=2, espera_segundos=0.0))

    with pytest.raises(FlowError):
        flow.executar()


def test_contexto_compartilhado():
    class StepA(BaseStep):
        nome = "A"
        def executar(self, ctx):
            return {"valor": 42}

    class StepB(BaseStep):
        nome = "B"
        def executar(self, ctx):
            assert ctx["A"]["valor"] == 42
            return {}

    flow = Flow()
    flow.step(StepA())
    flow.step(StepB())
    resultados = flow.executar()
    assert all(r.teve_sucesso for r in resultados)


def test_encadeamento_fluente():
    flow = (
        Flow(nome="Fluente")
        .step(StepSucesso())
        .step(StepSucesso())
        .step(StepSucesso())
    )
    resultados = flow.executar()
    assert len(resultados) == 3
