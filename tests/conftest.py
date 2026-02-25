"""Configuração do pytest para o botflow."""
import pytest


@pytest.fixture
def contexto_vazio():
    """Retorna um contexto limpo para uso nos testes."""
    return {}
