"""
Exemplo básico de uso do botflow.

Simula um fluxo de automação com login, download de relatório e envio de e-mail.
Execute com: python examples/exemplo_basico.py
"""
from botflow import Flow, BaseStep, ExponentialBackoff


# ── Steps ──────────────────────────────────────────────────────────────────

class LoginStep(BaseStep):
    nome = "Login no sistema"
    descricao = "Efetua login com credenciais configuradas"

    def executar(self, contexto):
        print("  → Autenticando usuário...")
        # Aqui entraria a lógica real de automação
        return {"usuario": "admin", "autenticado": True}


class BaixarRelatorioStep(BaseStep):
    nome = "Download do relatório"
    descricao = "Baixa o relatório mensal em CSV"

    def executar(self, contexto):
        usuario = contexto.get("Login no sistema", {}).get("usuario", "?")
        print(f"  → Baixando relatório para o usuário '{usuario}'...")
        return {"arquivo": "relatorio_fevereiro.csv", "linhas": 1523}


class EnviarEmailStep(BaseStep):
    nome = "Enviar e-mail"
    descricao = "Envia o relatório por e-mail"

    def executar(self, contexto):
        relatorio = contexto.get("Download do relatório", {})
        arquivo = relatorio.get("arquivo", "desconhecido")
        print(f"  → Enviando '{arquivo}' por e-mail...")
        return {"destinatarios": ["time@empresa.com"], "enviado": True}


# ── Execução ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    flow = (
        Flow(nome="Relatório Mensal", parar_na_falha=True)
        .step(LoginStep())
        .step(
            BaixarRelatorioStep(),
            retry=ExponentialBackoff(max_tentativas=3, base_segundos=0.1),
        )
        .step(EnviarEmailStep())
    )

    print(f"\n{'='*50}")
    print(f"  Executando: {flow.nome}")
    print(f"{'='*50}\n")

    resultados = flow.executar()

    print(f"\n{'='*50}")
    print("  Resumo da execução:")
    for r in resultados:
        icone = "✅" if r.teve_sucesso else "❌"
        print(f"  {icone} {r.status.value.upper()} — {r.duracao_segundos:.3f}s")
    print(f"{'='*50}\n")
