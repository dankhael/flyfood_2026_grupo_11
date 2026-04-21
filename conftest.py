"""Configuração do pytest: logs didáticos de sessão para a suite do FlyFood."""

import time

_inicio = None


def pytest_sessionstart(session):
    global _inicio
    _inicio = time.perf_counter()


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    if _inicio is None:
        return
    duracao_ms = (time.perf_counter() - _inicio) * 1000
    stats = terminalreporter.stats
    passou = len(stats.get("passed", []))
    falhou = len(stats.get("failed", []))
    terminalreporter.write_sep("=", "FlyFood — resumo da suite")
    terminalreporter.write_line(
        f"[LOG] {passou} passaram, {falhou} falharam em {duracao_ms:.2f} ms"
    )
