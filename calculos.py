"""
pontoflow/calculos.py
Toda a lógica de negócio: horas trabalhadas, diferenças, banco de horas.
"""
from __future__ import annotations

from datetime import time, timedelta, date
from typing import Optional
import pandas as pd


# ── Conversões ─────────────────────────────────────────────────────────────

def time_to_minutes(t) -> Optional[int]:
    """'HH:MM' ou time → minutos desde meia-noite. None se inválido."""
    if t is None:
        return None
    if isinstance(t, time):
        return t.hour * 60 + t.minute
    try:
        h, m = str(t)[:5].split(":")
        return int(h) * 60 + int(m)
    except Exception:
        return None


def minutes_to_hhmm(minutes: int) -> str:
    """Inteiro de minutos → 'Xh YYm' (suporta negativos)."""
    neg = minutes < 0
    minutes = abs(minutes)
    h = minutes // 60
    m = minutes % 60
    s = f"{h}h {m:02d}m"
    return f"-{s}" if neg else s


def minutes_to_delta(minutes: int) -> str:
    """Inteiro → '+Xh YYm' ou '-Xh YYm'."""
    prefix = "+" if minutes >= 0 else ""
    return prefix + minutes_to_hhmm(minutes)


# ── Cálculo de jornada ─────────────────────────────────────────────────────

def calcular_trabalhado(row: dict | pd.Series) -> Optional[int]:
    """
    Retorna minutos trabalhados no dia ou None se dados insuficientes.
    Desconta intervalo de almoço quando ambos os campos estão preenchidos.
    """
    entrada = time_to_minutes(row.get("entrada"))
    saida = time_to_minutes(row.get("saida"))

    if entrada is None or saida is None:
        return None

    total = saida - entrada

    sa = time_to_minutes(row.get("saida_almoco"))
    ra = time_to_minutes(row.get("retorno_almoco"))
    if sa is not None and ra is not None and ra > sa:
        total -= (ra - sa)

    return max(total, 0)


DIAS_PT = {"Mon":"Seg","Tue":"Ter","Wed":"Qua","Thu":"Qui","Fri":"Sex","Sat":"Sáb","Sun":"Dom"}

def enriquecer_df(df: pd.DataFrame, carga_min: int) -> pd.DataFrame:
    """
    Adiciona colunas calculadas ao DataFrame:
    trabalhado_min, diferenca_min, trabalhado_fmt, diferenca_fmt, dia_semana
    """
    if df.empty:
        return df

    df = df.copy()
    df["trabalhado_min"] = df.apply(calcular_trabalhado, axis=1)
    df["diferenca_min"] = df["trabalhado_min"].apply(
        lambda t: t - carga_min if t is not None else None
    )
    df["trabalhado_fmt"] = df["trabalhado_min"].apply(
        lambda t: minutes_to_hhmm(t) if t is not None else "—"
    )
    df["diferenca_fmt"] = df["diferenca_min"].apply(
        lambda d: minutes_to_delta(d) if d is not None else "—"
    )
    # Converte data para datetime de forma segura independente do dtype
    try:
        datas = pd.to_datetime(df["data"].astype(str), errors="coerce")
        df["dia_semana"] = datas.dt.strftime("%a").map(DIAS_PT).fillna("—")
    except Exception:
        df["dia_semana"] = "—"

    return df


# ── Banco de horas ─────────────────────────────────────────────────────────

def calcular_banco(df: pd.DataFrame, carga_min: int) -> dict:
    """
    Retorna dict com:
      total_trabalhado, total_extras, total_faltas, saldo, saldo_acumulado_series
    """
    df = enriquecer_df(df, carga_min)
    validos = df[df["trabalhado_min"].notna()].copy()

    total_trab = int(validos["trabalhado_min"].sum())
    extras = int(validos[validos["diferenca_min"] > 0]["diferenca_min"].sum())
    faltas = int(validos[validos["diferenca_min"] < 0]["diferenca_min"].abs().sum())
    saldo = extras - faltas

    # Saldo acumulado dia a dia (ordem cronológica)
    validos_sorted = validos.sort_values("data")
    validos_sorted["saldo_acum"] = validos_sorted["diferenca_min"].cumsum()

    return {
        "total_trabalhado": total_trab,
        "total_extras": extras,
        "total_faltas": faltas,
        "saldo": saldo,
        "df_acumulado": validos_sorted[["data","trabalhado_min","diferenca_min","saldo_acum","trabalhado_fmt","diferenca_fmt"]],
    }


# ── Resumo semanal ─────────────────────────────────────────────────────────

def resumo_semanal(df: pd.DataFrame, carga_min: int, dias_semana: int) -> pd.DataFrame:
    """Agrega minutos trabalhados por semana ISO."""
    if df.empty:
        return pd.DataFrame()
    df = enriquecer_df(df, carga_min).copy()
    df["semana"] = pd.to_datetime(df["data"]).dt.to_period("W").apply(lambda p: str(p.start_time.date()))
    meta_semana = carga_min * dias_semana
    agg = df.groupby("semana")["trabalhado_min"].sum().reset_index()
    agg["meta"] = meta_semana
    agg["diferenca"] = agg["trabalhado_min"] - meta_semana
    agg["trabalhado_fmt"] = agg["trabalhado_min"].apply(minutes_to_hhmm)
    return agg.sort_values("semana")


# ── Resumo mensal ──────────────────────────────────────────────────────────

def resumo_mensal(df: pd.DataFrame, carga_min: int) -> pd.DataFrame:
    """Agrega por mês."""
    if df.empty:
        return pd.DataFrame()
    df = enriquecer_df(df, carga_min).copy()
    df["mes"] = pd.to_datetime(df["data"]).dt.to_period("M").astype(str)
    agg = df.groupby("mes").agg(
        dias=("trabalhado_min", "count"),
        total_min=("trabalhado_min", "sum"),
        extras_min=("diferenca_min", lambda x: x[x > 0].sum()),
        faltas_min=("diferenca_min", lambda x: x[x < 0].abs().sum()),
    ).reset_index()
    agg["meta_min"] = agg["dias"] * carga_min
    agg["saldo_min"] = agg["total_min"] - agg["meta_min"]
    return agg.sort_values("mes", ascending=False)
