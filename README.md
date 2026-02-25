# botflow

> Orquestrador de automações em Python — encadeie steps, configure retries, hooks e plugins com uma API limpa e expressiva.

[![CI](https://github.com/seu-usuario/botflow/actions/workflows/ci.yml/badge.svg)](https://github.com/seu-usuario/botflow/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## O problema

À medida que automações crescem, o código vira um emaranhado de `try/except`, flags de controle e retries espalhados por todo lugar. Manter, testar e entender esse código torna-se um pesadelo.

**botflow** resolve isso oferecendo uma estrutura declarativa, testável e extensível para orquestrar qualquer automação Python.

---

## Instalação

```bash
pip install botflow
```

Ou em modo de desenvolvimento:

```bash
git clone https://github.com/seu-usuario/botflow.git
cd botflow
pip install -e ".[dev]"
```

---

## Conceitos fundamentais

| Conceito | Descrição |
|---|---|
| `Flow` | O orquestrador. Encadeia e executa steps em ordem. |
| `BaseStep` | Unidade de trabalho. Implemente `executar()`. |
| `RetryPolicy` | Estratégia de retry: `FixedDelay` ou `ExponentialBackoff`. |
| `HookManager` | Callbacks `antes_do_step` / `apos_o_step`. |
| `BotflowPlugin` | Extensão com ciclo de vida completo do flow. |

---

## Uso rápido

```python
from botflow import Flow, BaseStep, ExponentialBackoff


class LoginStep(BaseStep):
    nome = "Login"

    def executar(self, contexto):
        # sua lógica aqui
        return {"usuario": "admin"}


class BaixarRelatorioStep(BaseStep):
    nome = "Download"

    def executar(self, contexto):
        usuario = contexto["Login"]["usuario"]
        return {"arquivo": "relatorio.csv"}


class EnviarEmailStep(BaseStep):
    nome = "E-mail"

    def executar(self, contexto):
        arquivo = contexto["Download"]["arquivo"]
        print(f"Enviando {arquivo}...")


flow = (
    Flow(nome="Relatório Mensal")
    .step(LoginStep())
    .step(
        BaixarRelatorioStep(),
        retry=ExponentialBackoff(max_tentativas=3),  # retry automático
    )
    .step(EnviarEmailStep())
)

resultados = flow.executar()
```

---

## Retry automático

```python
from botflow import ExponentialBackoff, FixedDelay

# Backoff exponencial com jitter (recomendado para web)
retry = ExponentialBackoff(
    max_tentativas=5,
    base_segundos=0.5,
    max_espera_segundos=30.0,
    jitter=True,
)

# Intervalo fixo (simples)
retry = FixedDelay(max_tentativas=3, espera_segundos=2.0)

flow.step(MeuStep(), retry=retry)
```

---

## Hooks (before/after)

```python
flow = Flow()

@flow.hooks.antes_do_step
def log_inicio(step, contexto):
    print(f"⏳ Iniciando: {step.nome}")

@flow.hooks.apos_o_step
def log_fim(step, resultado, contexto):
    icone = "✅" if resultado.teve_sucesso else "❌"
    print(f"{icone} {step.nome} — {resultado.duracao_segundos:.2f}s")
```

---

## Plugin system

```python
from botflow.plugins import BotflowPlugin
import time


class MetricasPlugin(BotflowPlugin):
    nome = "metricas"

    def ao_iniciar_flow(self, flow):
        self._inicio = time.monotonic()

    def ao_finalizar_flow(self, flow, resultados):
        total = time.monotonic() - self._inicio
        sucesso = sum(1 for r in resultados if r.teve_sucesso)
        print(f"Flow '{flow.nome}': {sucesso}/{len(resultados)} OK em {total:.2f}s")


flow = Flow().usar_plugin(MetricasPlugin())
```

---

## Executar os testes

```bash
pytest tests/ -v --cov=botflow
```

---

## Estrutura do projeto

```
botflow/
├── botflow/
│   ├── flow.py       # Flow e FlowRunner
│   ├── step.py       # BaseStep, StepResult, StepStatus
│   ├── retry.py      # FixedDelay, ExponentialBackoff
│   ├── hooks.py      # HookManager
│   ├── logger.py     # Logging estruturado JSON
│   └── plugins.py    # BotflowPlugin, PluginManager
├── tests/
│   ├── test_flow.py
│   ├── test_retry.py
│   └── test_hooks.py
└── examples/
    └── exemplo_basico.py
```

---

## Roadmap

- [ ] Execução assíncrona (`asyncio`)
- [ ] Step condicional baseado em resultado anterior
- [ ] Serialização do estado do flow (checkpoint/resume)
- [ ] Plugin de observabilidade com Prometheus
- [ ] CLI para executar flows via terminal

---

## Licença

MIT © Seu Nome
