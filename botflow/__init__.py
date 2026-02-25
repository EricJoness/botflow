"""
botflow — Orquestrador de automações em Python.

Permite encadear steps, configurar retries, hooks e plugins
de forma simples e declarativa.
"""

from botflow.flow import Flow
from botflow.step import BaseStep, StepResult, StepStatus
from botflow.retry import RetryPolicy, ExponentialBackoff, FixedDelay
from botflow.hooks import HookManager
from botflow.plugins import PluginManager

__version__ = "0.1.0"
__author__ = "Seu Nome"

__all__ = [
    "Flow",
    "BaseStep",
    "StepResult",
    "StepStatus",
    "RetryPolicy",
    "ExponentialBackoff",
    "FixedDelay",
    "HookManager",
    "PluginManager",
]
