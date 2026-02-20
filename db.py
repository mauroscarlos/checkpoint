"""
pontoflow/db.py
Camada de acesso ao Supabase — todas as operações de banco ficam aqui.
"""
from __future__ import annotations

import time as time_module
import streamlit as st
from supabase import create_client, Client
from datetime import date, time
from typing import Optional
import pandas as pd


# ── Conexão ────────────────────────────────────────────────────────────────

@st.cache_resource
def get_client() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)


TABLE = "pontos"


# ── Retry helper ───────────────────────────────────────────────────────────

def _retry(fn, retries=3, delay=1.5):
    """Executa fn com até `retries` tentativas em caso de erro de rede."""
    last_err = None
    for attempt in range(retries):
        try:
            return fn()
        except Exception as e:
            last_err = e
            if attempt < retries - 1:
                time_module.sleep(delay)
    raise last_err


# ── Helpers ────────────────────────────────────────────────────────────────

def _to_str(t) -> Optional[str]:
    """Converte time/string para 'HH:MM' ou None."""
    if t is None:
        return None
    if isinstance(t, time):
        return t.strftime("%H:%M")
    return str(t)[:5] if t else None


# ── CRUD ───────────────────────────────────────────────────────────────────

def listar_pontos(mes: Optional[str] = None) -> pd.DataFrame:
    client = get_client()

    def _query():
        q = client.table(TABLE).select("*").order("data", desc=True)
        if mes:
            inicio = f"{mes}-01"
            y, m = int(mes[:4]), int(mes[5:])
            fim = f"{y+1}-01-01" if m == 12 else f"{y}-{m+1:02d}-01"
            q = q.gte("data", inicio).lt("data", fim)
        return q.execute()

    resp = _retry(_query)
    df = pd.DataFrame(resp.data) if resp.data else pd.DataFrame(
        columns=["id","data","entrada","saida_almoco","retorno_almoco","saida","obs","created_at","updated_at"]
    )
    return df


def buscar_ponto(data: date) -> Optional[dict]:
    client = get_client()
    resp = _retry(lambda: client.table(TABLE).select("*").eq("data", str(data)).execute())
    return resp.data[0] if resp.data else None


def salvar_ponto(
    data: date,
    entrada: Optional[time],
    saida_almoco: Optional[time],
    retorno_almoco: Optional[time],
    saida: Optional[time],
    obs: str = "",
) -> dict:
    client = get_client()
    payload = {
        "data": str(data),
        "entrada": _to_str(entrada),
        "saida_almoco": _to_str(saida_almoco),
        "retorno_almoco": _to_str(retorno_almoco),
        "saida": _to_str(saida),
        "obs": obs or None,
    }
    resp = _retry(lambda: client.table(TABLE).upsert(payload, on_conflict="data").execute())
    return resp.data[0] if resp.data else payload


def excluir_ponto(registro_id: int) -> None:
    client = get_client()
    _retry(lambda: client.table(TABLE).delete().eq("id", registro_id).execute())


def excluir_todos() -> None:
    client = get_client()
    _retry(lambda: client.table(TABLE).delete().neq("id", 0).execute())
