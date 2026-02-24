"""
finflow/db.py — Acesso ao Supabase
"""
from __future__ import annotations
import time as time_module
import streamlit as st
from supabase import create_client, Client
from datetime import date
from typing import Optional
import pandas as pd

@st.cache_resource
def get_client() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

def _retry(fn, retries=3, delay=1.5):
    last_err = None
    for attempt in range(retries):
        try:
            return fn()
        except Exception as e:
            last_err = e
            if attempt < retries - 1:
                time_module.sleep(delay)
    raise last_err

# ── Categorias ─────────────────────────────────────────────────────────────

def listar_categorias(tipo: Optional[str] = None) -> pd.DataFrame:
    client = get_client()
    def _q():
        q = client.table("categorias").select("*").order("nome")
        if tipo:
            q = q.eq("tipo", tipo)
        return q.execute()
    resp = _retry(_q)
    return pd.DataFrame(resp.data) if resp.data else pd.DataFrame(
        columns=["id","nome","tipo","icone","cor","created_at"])

def salvar_categoria(nome: str, tipo: str, icone: str, cor: str) -> dict:
    client = get_client()
    payload = {"nome": nome.strip(), "tipo": tipo, "icone": icone, "cor": cor}
    resp = _retry(lambda: client.table("categorias").upsert(payload, on_conflict="nome").execute())
    return resp.data[0] if resp.data else payload

def excluir_categoria(cat_id: int) -> None:
    client = get_client()
    _retry(lambda: client.table("categorias").delete().eq("id", cat_id).execute())

# ── Transações ─────────────────────────────────────────────────────────────

def listar_transacoes(mes: Optional[str] = None, tipo: Optional[str] = None) -> pd.DataFrame:
    client = get_client()
    def _q():
        q = (client.table("transacoes")
             .select("*")
             .order("data", desc=True))
        if mes:
            y, m = int(mes[:4]), int(mes[5:])
            fim = f"{y+1}-01-01" if m == 12 else f"{y}-{m+1:02d}-01"
            q = q.gte("data", f"{mes}-01").lt("data", fim)
        if tipo:
            q = q.eq("tipo", tipo)
        return q.execute()
    resp = _retry(_q)
    if not resp.data:
        return pd.DataFrame(columns=["id","data","descricao","valor","tipo",
                                      "categoria_id","observacao",
                                      "categoria_nome","categoria_icone"])
    df = pd.DataFrame(resp.data)

    # Garante que categoria_id seja numérico para o merge
    df["categoria_id"] = pd.to_numeric(df["categoria_id"], errors="coerce")

    # Busca categorias e faz merge
    try:
        cats = listar_categorias()
        if not cats.empty:
            cats["id"] = pd.to_numeric(cats["id"], errors="coerce")
            merged = df.merge(
                cats[["id","nome","icone"]].rename(columns={
                    "id": "categoria_id",
                    "nome": "categoria_nome",
                    "icone": "categoria_icone"
                }),
                on="categoria_id", how="left"
            )
            merged["categoria_nome"] = merged["categoria_nome"].fillna("—")
            merged["categoria_icone"] = merged["categoria_icone"].fillna("")
            return merged
    except Exception:
        pass

    # Fallback sem categorias
    df["categoria_nome"] = "—"
    df["categoria_icone"] = ""
    return df

def buscar_transacao(trans_id: int) -> Optional[dict]:
    client = get_client()
    resp = _retry(lambda: client.table("transacoes").select("*").eq("id", trans_id).execute())
    return resp.data[0] if resp.data else None

def salvar_transacao(
    data: date, descricao: str, valor: float, tipo: str,
    categoria_id: Optional[int], observacao: str = "", trans_id: Optional[int] = None
) -> dict:
    client = get_client()
    payload = {
        "data": str(data), "descricao": descricao.strip(),
        "valor": round(float(valor), 2), "tipo": tipo,
        "categoria_id": categoria_id, "observacao": observacao or None,
    }
    if trans_id:
        payload["id"] = trans_id
        resp = _retry(lambda: client.table("transacoes").upsert(payload).execute())
    else:
        resp = _retry(lambda: client.table("transacoes").insert(payload).execute())
    return resp.data[0] if resp.data else payload

def excluir_transacao(trans_id: int) -> None:
    client = get_client()
    _retry(lambda: client.table("transacoes").delete().eq("id", trans_id).execute())

def excluir_todas_transacoes() -> None:
    client = get_client()
    _retry(lambda: client.table("transacoes").delete().neq("id", 0).execute())
