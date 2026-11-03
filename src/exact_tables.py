"""Limite operacional explícito para o cálculo exato de tabelas 2×2."""
from inference import scientific_stats


FISHER_MAX_TOTAL = 1_000_000


def fisher_probability(table, alternative='two-sided'):
    if sum(sum(row) for row in table) > FISHER_MAX_TOTAL:
        return None
    return float(scientific_stats().fisher_exact(table, alternative=alternative).pvalue)
