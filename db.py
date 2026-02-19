"""
pontoflow/db.py
Camada de acesso ao Supabase — todas as operações de banco ficam aqui.
"""
from __future__ import annotations

import streamlit as st
from supabase import create_client, Client
from datetime import date, time
from typing import Optional
import pandas as pd


# ── Conexão (singleton via cache) ──────────────────────────────────────────

@st.cache_resource
def get_client() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)


TABLE = "pontos"


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
    """
    Retorna todos os registros (ou filtra por mês 'YYYY-MM').
    Colunas: id, data, entrada, saida_almoco, retorno_almoco, saida, obs, created_at, updated_at
    """
    client = get_client()
    q = client.table(TABLE).select("*").order("data", desc=True)

    if mes:
        inicio = f"{mes}-01"
        # último dia do mês
        y, m = int(mes[:4]), int(mes[5:])
        if m == 12:
            fim = f"{y+1}-01-01"
        else:
            fim = f"{y}-{m+1:02d}-01"
        q = q.gte("data", inicio).lt("data", fim)

    resp = q.execute()
    df = pd.DataFrame(resp.data) if resp.data else pd.DataFrame(
        columns=["id","data","entrada","saida_almoco","retorno_almoco","saida","obs","created_at","updated_at"]
    )
    if not df.empty:
        df["data"] = pd.to_datetime(df["data"]).dt.date
    return df


def buscar_ponto(data: date) -> Optional[dict]:
    """Retorna o registro de um dia específico ou None."""
    client = get_client()
    resp = client.table(TABLE).select("*").eq("data", str(data)).execute()
    return resp.data[0] if resp.data else None


def salvar_ponto(
    data: date,
    entrada: Optional[time],
    saida_almoco: Optional[time],
    retorno_almoco: Optional[time],
    saida: Optional[time],
    obs: str = "",
) -> dict:
    """
    Insere ou atualiza (upsert) um registro de ponto.
    Retorna o registro salvo.
    """
    client = get_client()
    payload = {
        "data": str(data),
        "entrada": _to_str(entrada),
        "saida_almoco": _to_str(saida_almoco),
        "retorno_almoco": _to_str(retorno_almoco),
        "saida": _to_str(saida),
        "obs": obs or None,
    }
    resp = client.table(TABLE).upsert(payload, on_conflict="data").execute()
    return resp.data[0] if resp.data else payload


def excluir_ponto(registro_id: int) -> None:
    """Exclui um registro pelo ID."""
    client = get_client()
    client.table(TABLE).delete().eq("id", registro_id).execute()


def excluir_todos() -> None:
    """Remove TODOS os registros (use com cuidado!)."""
    client = get_client()
    client.table(TABLE).delete().neq("id", 0).execute()
