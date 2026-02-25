"""
Núcleo do botflow: Flow e FlowRunner.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from botflow.hooks import HookManager
from botflow.logger import BotflowLogger, criar_logger
from botflow.plugins import PluginManager
from botflow.retry import RetryPolicy, ExponentialBackoff, executar_com_retry
from botflow.step import BaseStep, StepResult, StepStatus


class FlowError(Exception):
    """Lançada quando um step falha e o flow é interrompido."""

    def __init__(self, step: BaseStep, resultado: StepResult) -> None:
        self.step = step
        self.resultado = resultado
        super().__init__(
            f"Step '{step.nome}' falhou após {resultado.tentativas} tentativa(s): "
            f"{resultado.erro}"
        )


class Flow:
    """
    Orquestrador de steps de automação.

    Permite encadear steps, configurar retry, hooks e plugins.

    Exemplo::

        flow = Flow(nome="Relatório Diário")
        flow.step(LoginStep())
        flow.step(BaixarRelatorioStep(), retry=ExponentialBackoff(max_tentativas=3))
        flow.step(EnviarEmailStep())
        resultados = flow.executar()

    Args:
        nome: Nome descritivo do flow.
        parar_na_falha: Se True (padrão), interrompe o flow quando um step falha.
        retry_padrao: Política de retry aplicada a todos os steps sem retry próprio.
        logger: Logger customizado (cria um automaticamente se não fornecido).
    """

    def __init__(
        self,
        nome: str = "Flow",
        parar_na_falha: bool = True,
        retry_padrao: Optional[RetryPolicy] = None,
        logger: Optional[BotflowLogger] = None,
    ) -> None:
        self.nome = nome
        self.parar_na_falha = parar_na_falha
        self.retry_padrao = retry_padrao
        self.logger = logger or criar_logger(nome)
        self.hooks = HookManager()
        self.plugins = PluginManager()

        self._steps: list[tuple[BaseStep, Optional[RetryPolicy]]] = []

    # ------------------------------------------------------------------
    # Configuração
    # ------------------------------------------------------------------

    def step(
        self,
        step: BaseStep,
        retry: Optional[RetryPolicy] = None,
    ) -> "Flow":
        """
        Adiciona um step ao flow.

        Args:
            step: Instância de BaseStep.
            retry: Política de retry específica para este step.
                   Se None, usa `retry_padrao` do flow.

        Returns:
            O próprio flow (permite encadeamento).
        """
        self._steps.append((step, retry))
        return self

    def usar_plugin(self, plugin) -> "Flow":
        """Registra um plugin. Retorna self para encadeamento."""
        self.plugins.registrar(plugin)
        return self

    # ------------------------------------------------------------------
    # Execução
    # ------------------------------------------------------------------

    def executar(self, contexto: Optional[dict[str, Any]] = None) -> list[StepResult]:
        """
        Executa todos os steps em ordem.

        Args:
            contexto: Dicionário inicial compartilhado entre steps.
                      Se None, cria um dicionário vazio.

        Returns:
            Lista de StepResult, um por step executado.

        Raises:
            FlowError: Quando um step falha e `parar_na_falha` é True.
        """
        ctx: dict[str, Any] = contexto or {}
        resultados: list[StepResult] = []

        self.logger.info("Iniciando flow", flow=self.nome, total_steps=len(self._steps))
        self.plugins.ao_iniciar_flow(self)

        for idx, (step, retry_step) in enumerate(self._steps, start=1):
            policy = retry_step or self.retry_padrao

            # --- verificar se deve pular ---
            if step.deve_pular(ctx):
                resultado = StepResult(
                    status=StepStatus.PULADO,
                    mensagem=f"Step '{step.nome}' pulado por condição.",
                )
                resultados.append(resultado)
                self.logger.info(
                    "Step pulado",
                    step=step.nome,
                    indice=idx,
                )
                continue

            # --- disparar hooks / plugins antes ---
            self.hooks.disparar_antes(step, ctx)
            self.plugins.ao_iniciar_step(step, ctx)
            self.logger.info("Executando step", step=step.nome, indice=idx)

            # --- executar com ou sem retry ---
            resultado = self._executar_step(step, ctx, policy, idx)
            resultados.append(resultado)

            # --- disparar hooks / plugins após ---
            self.hooks.disparar_apos(step, resultado, ctx)
            self.plugins.ao_finalizar_step(step, resultado, ctx)

            if resultado.teve_sucesso:
                self.logger.info(
                    "Step concluído",
                    step=step.nome,
                    duracao=f"{resultado.duracao_segundos:.2f}s",
                    tentativas=resultado.tentativas,
                )
                # Armazenar dados do step no contexto
                if resultado.dados is not None:
                    ctx[step.nome] = resultado.dados
            else:
                self.logger.error(
                    "Step falhou",
                    step=step.nome,
                    erro=str(resultado.erro),
                    tentativas=resultado.tentativas,
                )
                if self.parar_na_falha:
                    self.plugins.ao_finalizar_flow(self, resultados)
                    raise FlowError(step, resultado)

        self.plugins.ao_finalizar_flow(self, resultados)
        self.logger.info(
            "Flow finalizado",
            flow=self.nome,
            steps_executados=len(resultados),
        )
        return resultados

    # ------------------------------------------------------------------
    # Interno
    # ------------------------------------------------------------------

    def _executar_step(
        self,
        step: BaseStep,
        ctx: dict[str, Any],
        policy: Optional[RetryPolicy],
        indice: int,
    ) -> StepResult:
        try:
            if policy:
                (dados, duracao), tentativas = executar_com_retry(
                    step._executar_com_medicao,
                    policy,
                    ctx,
                )
            else:
                dados, duracao = step._executar_com_medicao(ctx)
                tentativas = 1

            return StepResult(
                status=StepStatus.SUCESSO,
                dados=dados,
                duracao_segundos=duracao,
                tentativas=tentativas,
            )
        except Exception as erro:
            self.plugins.ao_falhar_step(step, erro, ctx)
            return StepResult(
                status=StepStatus.FALHA,
                erro=erro,
                tentativas=policy.max_tentativas if policy else 1,
                mensagem=str(erro),
            )

    def __repr__(self) -> str:
        return f"Flow(nome={self.nome!r}, steps={len(self._steps)})"
