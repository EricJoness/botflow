"""Testes das políticas de retry."""
import pytest
from botflow.retry import FixedDelay, ExponentialBackoff, executar_com_retry


# ── FixedDelay ─────────────────────────────────────────────────────────────

def test_fixed_delay_espera_constante():
    policy = FixedDelay(max_tentativas=3, espera_segundos=5.0)
    assert policy.calcular_espera(1) == 5.0
    assert policy.calcular_espera(2) == 5.0


def test_fixed_delay_deve_tentar():
    policy = FixedDelay(max_tentativas=3)
    assert policy.deve_tentar_novamente(1, ValueError()) is True
    assert policy.deve_tentar_novamente(3, ValueError()) is False


# ── ExponentialBackoff ─────────────────────────────────────────────────────

def test_exponential_cresce():
    policy = ExponentialBackoff(base_segundos=1.0, jitter=False)
    assert policy.calcular_espera(1) == 2.0
    assert policy.calcular_espera(2) == 4.0
    assert policy.calcular_espera(3) == 8.0


def test_exponential_respeita_maximo():
    policy = ExponentialBackoff(
        base_segundos=10.0,
        max_espera_segundos=15.0,
        jitter=False,
    )
    assert policy.calcular_espera(5) == 15.0


def test_exponential_jitter_nao_excede_maximo():
    policy = ExponentialBackoff(
        base_segundos=1.0,
        max_espera_segundos=100.0,
        jitter=True,
        max_tentativas=5,
    )
    for tentativa in range(1, 6):
        espera = policy.calcular_espera(tentativa)
        assert espera <= policy.max_espera_segundos


# ── executar_com_retry ─────────────────────────────────────────────────────

def test_retry_sucede_na_primeira():
    contador = {"n": 0}

    def fn():
        contador["n"] += 1
        return "ok"

    resultado, tentativas = executar_com_retry(fn, FixedDelay(espera_segundos=0))
    assert resultado == "ok"
    assert tentativas == 1


def test_retry_sucede_depois_de_falhas():
    contador = {"n": 0}

    def fn():
        contador["n"] += 1
        if contador["n"] < 3:
            raise RuntimeError("ainda não")
        return "pronto"

    resultado, tentativas = executar_com_retry(
        fn, FixedDelay(max_tentativas=5, espera_segundos=0)
    )
    assert resultado == "pronto"
    assert tentativas == 3


def test_retry_lanca_excecao_apos_esgotar():
    def fn():
        raise ValueError("sempre falha")

    with pytest.raises(ValueError, match="sempre falha"):
        executar_com_retry(fn, FixedDelay(max_tentativas=3, espera_segundos=0))


def test_retry_filtra_excecao():
    """Deve parar imediatamente se erro não está na lista de excecoes."""
    policy = FixedDelay(max_tentativas=5, espera_segundos=0, excecoes=(TypeError,))

    def fn():
        raise ValueError("não coberto")

    with pytest.raises(ValueError):
        executar_com_retry(fn, policy)
