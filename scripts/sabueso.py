#!/usr/bin/env python3
"""
sabueso.py — Agente 1 del sistema GVB @byduvan_ai
Lee Competidores + Referentes + Mis Ideas (Viral/Explorar) desde Notion
→ Scraping con Apify → Filtra outliers → Clasifica patrón GVB → Escribe Hooks DB

Uso:
    python3 sabueso.py
    python3 sabueso.py --dry-run
    python3 sabueso.py --source competidores
    python3 sabueso.py --source referentes
    python3 sabueso.py --source viral
    python3 sabueso.py --limit 5
"""

import os
import re
import sys
import time
import json
import argparse
import requests
from datetime import datetime, date
from dotenv import load_dotenv

load_dotenv()

# ─── CONFIGURACIÓN ────────────────────────────────────────────────────────────

NOTION_API_KEY   = os.getenv("NOTION_API_KEY")
APIFY_API_TOKEN  = os.getenv("APIFY_API_TOKEN")

NOTION_VERSION   = "2022-06-28"
NOTION_BASE      = "https://api.notion.com/v1"
APIFY_BASE       = "https://api.apify.com/v2"

# IDs de colección Notion
COMPETIDORES_DB  = "6d44cbde-c6cb-470a-9bd4-c2100562de56"
REFERENTES_DB    = "c08bdc84-071a-4032-83a0-860b0e36f118"
MIS_IDEAS_DB     = "9ed953db-9a49-4d3c-b786-6dec10264490"
HOOKS_DB         = "ec06af9a-f1fb-4fd0-83f0-1cdf9fe941a5"

# Apify actors
ACTOR_CANAL      = "sian.agency~instagram-ai-transcript-extractor"
ACTOR_URLS       = "apify~instagram-scraper"

OUTLIER_UMBRAL   = 3.0
REELS_POR_CANAL  = 10

# ─── NOTION HELPERS ───────────────────────────────────────────────────────────

def notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

def notion_query(database_id: str, filter_body: dict = None) -> list:
    url = f"{NOTION_BASE}/databases/{database_id}/query"
    payload = {"page_size": 100}
    if filter_body:
        payload["filter"] = filter_body
    rows = []
    while True:
        resp = requests.post(url, headers=notion_headers(), json=payload)
        resp.raise_for_status()
        data = resp.json()
        rows.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        payload["start_cursor"] = data["next_cursor"]
    return rows

def get_prop(page: dict, name: str):
    props = page.get("properties", {})
    prop = props.get(name, {})
    t = prop.get("type", "")
    if t == "title":
        items = prop.get("title", [])
        return items[0]["plain_text"] if items else ""
    if t == "rich_text":
        items = prop.get("rich_text", [])
        return items[0]["plain_text"] if items else ""
    if t == "select":
        sel = prop.get("select")
        return sel["name"] if sel else ""
    if t == "checkbox":
        return prop.get("checkbox", False)
    if t == "url":
        return prop.get("url", "")
    if t == "number":
        return prop.get("number")
    if t == "date":
        d = prop.get("date")
        return d["start"] if d else ""
    return ""

def notion_update_page(page_id: str, properties: dict):
    url = f"{NOTION_BASE}/pages/{page_id}"
    resp = requests.patch(url, headers=notion_headers(), json={"properties": properties})
    resp.raise_for_status()
    return resp.json()

def notion_create_page(database_id: str, properties: dict):
    url = f"{NOTION_BASE}/pages"
    payload = {
        "parent": {"database_id": database_id},
        "properties": properties,
    }
    resp = requests.post(url, headers=notion_headers(), json=payload)
    resp.raise_for_status()
    return resp.json()

# ─── LEER FUENTES DESDE NOTION ────────────────────────────────────────────────

def leer_competidores() -> list[dict]:
    rows = notion_query(COMPETIDORES_DB, {
        "property": "Activo",
        "checkbox": {"equals": True}
    })
    resultado = []
    for row in rows:
        handle = get_prop(row, "Handle").lstrip("@")
        url    = get_prop(row, "URL Instagram")
        if handle:
            resultado.append({"handle": handle, "url": url, "tipo": "competidor"})
    print(f"  → {len(resultado)} competidores activos")
    return resultado

def leer_referentes() -> list[dict]:
    rows = notion_query(REFERENTES_DB, {
        "property": "Activo",
        "checkbox": {"equals": True}
    })
    resultado = []
    for row in rows:
        nombre    = get_prop(row, "Nombre")
        url_canal = get_prop(row, "URL Canal")
        plataforma = get_prop(row, "Plataforma")
        if url_canal:
            resultado.append({
                "nombre": nombre,
                "url": url_canal,
                "plataforma": plataforma or "Instagram",
                "tipo": "referente"
            })
    print(f"  → {len(resultado)} referentes activos")
    return resultado

def leer_viral_explorar() -> list[dict]:
    rows = notion_query(MIS_IDEAS_DB, {
        "and": [
            {"property": "Origen",  "select": {"equals": "Viral/Explorar"}},
            {"property": "Estado",  "select": {"equals": "Idea cruda"}},
        ]
    })
    resultado = []
    for row in rows:
        url  = get_prop(row, "De que va")
        idea = get_prop(row, "Idea")
        if url and url.startswith("http"):
            resultado.append({"url": url, "idea": idea, "page_id": row["id"], "tipo": "viral"})
    print(f"  → {len(resultado)} URLs en Viral/Explorar")
    return resultado

def marcar_viral_procesado(page_id: str):
    notion_update_page(page_id, {
        "Estado": {"select": {"name": "Procesado"}}
    })

# ─── APIFY HELPERS ────────────────────────────────────────────────────────────

def apify_run_actor(actor_id: str, input_data: dict, timeout: int = 300) -> list:
    url = f"{APIFY_BASE}/acts/{actor_id}/runs?token={APIFY_API_TOKEN}"
    resp = requests.post(url, json=input_data)
    resp.raise_for_status()
    run_id = resp.json()["data"]["id"]

    status_url = f"{APIFY_BASE}/actor-runs/{run_id}?token={APIFY_API_TOKEN}"
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(8)
        r = requests.get(status_url)
        r.raise_for_status()
        status = r.json()["data"]["status"]
        if status == "SUCCEEDED":
            break
        if status in ("FAILED", "ABORTED", "TIMED-OUT"):
            print(f"  ⚠️  Actor {actor_id} terminó con estado: {status}")
            return []
    else:
        print(f"  ⚠️  Timeout esperando actor {actor_id}")
        return []

    dataset_id = r.json()["data"]["defaultDatasetId"]
    items_url  = f"{APIFY_BASE}/datasets/{dataset_id}/items?token={APIFY_API_TOKEN}&format=json"
    items_resp = requests.get(items_url)
    items_resp.raise_for_status()
    return items_resp.json()

def scrapear_canal_instagram(handle: str, reel_count: int = REELS_POR_CANAL) -> list:
    print(f"    Scrapeando canal @{handle}...")
    return apify_run_actor(ACTOR_CANAL, {
        "channelUsername": handle,
        "reelCount": reel_count
    })

def scrapear_urls_individuales(urls: list[str]) -> list:
    print(f"    Scrapeando {len(urls)} URLs individuales...")
    return apify_run_actor(ACTOR_URLS, {
        "directUrls": urls,
        "resultsType": "posts",
        "resultsLimit": len(urls)
    })

# ─── ANÁLISIS ─────────────────────────────────────────────────────────────────

def calcular_like_rate(video: dict) -> float:
    likes = video.get("likesCount") or video.get("likes") or 0
    views = video.get("videoViewCount") or video.get("views") or 0
    if views == 0:
        return 0.0
    return round((likes / views) * 100, 2)

def filtrar_outliers(videos: list) -> list:
    for v in videos:
        v["like_rate"] = calcular_like_rate(v)
    if not videos:
        return []
    promedio = sum(v["like_rate"] for v in videos) / len(videos)
    umbral   = max(promedio, OUTLIER_UMBRAL)
    outliers = [v for v in videos if v["like_rate"] > umbral]
    print(f"    Like rate promedio: {promedio:.1f}% | Umbral: {umbral:.1f}% | Outliers: {len(outliers)}/{len(videos)}")
    return outliers

# ─── CLASIFICACIÓN GVB ────────────────────────────────────────────────────────

PATRONES_GVB = {
    1: (r"\b(no|deja de|sin usar|nunca más|para de)\b", "Negación Sorpresiva"),
    2: (r"\b\d+\b.*(minutos?|horas?|días?|semanas?|segundos?|pasos?|formas?|maneras?)", "Cifra Concreta"),
    3: (r"\b(nadie te dice|por esto|el secreto|lo que no saben|así es como)\b", "Secreto Revelado"),
    4: (r"\b(antes|después|de .* a .*|pasé de|cambié|ahora)\b", "Contraste"),
    5: (r"\?", "Curiosidad Directa"),
    6: (r"\b(acaba de|esta semana|ya cambió|nuevo|acaban de|lanzaron|actualización)\b", "Urgencia/Novedad"),
}

PALABRAS_NEGOCIO = ["clientes", "ventas", "tiempo", "dinero", "ingreso", "crecimiento",
                    "leads", "facturar", "negocios", "empresa", "cobrar", "monetizar"]
PALABRAS_TECNICO = ["modelo", "prompt", "parámetro", "token", "api", "llm",
                    "fine-tuning", "embedding", "vector", "agente técnico"]

def clasificar_patron_gvb(texto: str) -> tuple[int, str]:
    texto_lower = texto.lower()
    for num, (patron, nombre) in PATRONES_GVB.items():
        if re.search(patron, texto_lower):
            return num, nombre
    return 0, "Sin Patrón"

def detectar_tono(texto: str) -> str:
    texto_lower = texto.lower()
    es_negocio = any(p in texto_lower for p in PALABRAS_NEGOCIO)
    es_tecnico  = any(p in texto_lower for p in PALABRAS_TECNICO)
    if es_negocio and es_tecnico:
        return "Mixto"
    if es_negocio:
        return "Operador de Negocio"
    if es_tecnico:
        return "Tecnico IA"
    return "Operador de Negocio"

def detectar_formato(texto: str) -> str:
    texto_lower = texto.lower()
    if any(p in texto_lower for p in ["tier", "ranking", "mejor", "peor", "vs", "comparativa"]):
        return "Tier List"
    if any(p in texto_lower for p in ["cómo", "paso", "tutorial", "aprende", "guía"]):
        return "Tutorial"
    if any(p in texto_lower for p in ["nuevo", "acaba", "lanzó", "actualización", "cambia"]):
        return "Noticia"
    if any(p in texto_lower for p in ["antes", "después", "de 0 a", "pasé de"]):
        return "Contraste"
    return "Caso de Uso"

def primeras_palabras(texto: str, n: int) -> str:
    palabras = texto.strip().split()
    return " ".join(palabras[:n])

# ─── ESCRIBIR EN HOOKS DB ────────────────────────────────────────────────────

def hook_ya_existe(hook_texto: str) -> bool:
    rows = notion_query(HOOKS_DB, {
        "property": "Hook Texto",
        "rich_text": {"equals": hook_texto}
    })
    return len(rows) > 0

def guardar_hook(outlier: dict, fuente: str, dry_run: bool = False):
    caption      = outlier.get("caption") or outlier.get("text") or ""
    transcript   = outlier.get("transcript") or ""
    hook_texto   = primeras_palabras(caption, 12)
    trans_hook   = primeras_palabras(transcript, 15) if transcript else ""
    like_rate    = outlier.get("like_rate", 0.0)
    views        = outlier.get("videoViewCount") or outlier.get("views") or 0
    duracion     = outlier.get("videoDuration") or outlier.get("duration") or 0
    fecha_post   = outlier.get("timestamp") or outlier.get("takenAt") or datetime.now().isoformat()
    semana       = datetime.now().isocalendar()[1]

    if not hook_texto:
        return

    patron_num, _ = clasificar_patron_gvb(caption + " " + transcript)
    tono          = detectar_tono(caption + " " + transcript)
    formato       = detectar_formato(caption)

    if dry_run:
        print(f"    [DRY-RUN] Hook: '{hook_texto}' | {like_rate}% | P{patron_num} | {tono}")
        return

    if hook_ya_existe(hook_texto):
        print(f"    ↩ Duplicado, omitido: '{hook_texto[:40]}...'")
        return

    notion_create_page(HOOKS_DB, {
        "Hook Texto":       {"title": [{"text": {"content": hook_texto}}]},
        "Transcript Hook":  {"rich_text": [{"text": {"content": trans_hook}}]},
        "Patron GVB":       {"select": {"name": str(patron_num)}},
        "Formato":          {"select": {"name": formato}},
        "Like Rate":        {"number": like_rate},
        "Views":            {"number": views},
        "Fuente":           {"rich_text": [{"text": {"content": fuente}}]},
        "Duracion seg":     {"number": duracion},
        "Fecha Post":       {"date": {"start": fecha_post[:10]}},
        "Semana":           {"number": semana},
        "Tono":             {"select": {"name": tono}},
    })
    print(f"    ✅ Guardado: '{hook_texto[:50]}' | {like_rate}% | P{patron_num} | {tono}")

# ─── FLUJO PRINCIPAL ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Sabueso — Agente 1 GVB")
    parser.add_argument("--dry-run",  action="store_true", help="Ver sin escribir en Notion")
    parser.add_argument("--source",   choices=["competidores", "referentes", "viral"], help="Procesar solo una fuente")
    parser.add_argument("--limit",    type=int, default=REELS_POR_CANAL, help="Max reels por canal")
    args = parser.parse_args()

    if not NOTION_API_KEY or not APIFY_API_TOKEN:
        print("❌ Faltan variables de entorno: NOTION_API_KEY y/o APIFY_API_TOKEN")
        sys.exit(1)

    print("\n🐕 SABUESO — Iniciando\n" + "="*40)
    total_videos   = 0
    total_outliers = 0
    top_hooks      = []

    if not args.source or args.source == "competidores":
        print("\n📌 Procesando Competidores...")
        for canal in leer_competidores():
            videos = scrapear_canal_instagram(canal["handle"], args.limit)
            total_videos += len(videos)
            outliers = filtrar_outliers(videos)
            total_outliers += len(outliers)
            for o in outliers:
                guardar_hook(o, f"@{canal['handle']}", dry_run=args.dry_run)
                caption    = o.get("caption") or ""
                hook_texto = primeras_palabras(caption, 12)
                patron_num, _ = clasificar_patron_gvb(caption)
                top_hooks.append((hook_texto, o["like_rate"], patron_num, canal["handle"]))

    if not args.source or args.source == "referentes":
        print("\n📚 Procesando Referentes...")
        for ref in leer_referentes():
            plataforma = ref.get("plataforma", "Instagram")
            if "instagram" in plataforma.lower():
                handle = ref["url"].rstrip("/").split("/")[-1].lstrip("@")
                videos = scrapear_canal_instagram(handle, args.limit)
            else:
                print(f"  ⚠️  {ref['nombre']} es YouTube — actor pendiente de configurar")
                continue
            total_videos += len(videos)
            outliers = filtrar_outliers(videos)
            total_outliers += len(outliers)
            for o in outliers:
                guardar_hook(o, f"@{ref['nombre']}", dry_run=args.dry_run)
                caption    = o.get("caption") or ""
                hook_texto = primeras_palabras(caption, 12)
                patron_num, _ = clasificar_patron_gvb(caption)
                top_hooks.append((hook_texto, o["like_rate"], patron_num, ref["nombre"]))

    if not args.source or args.source == "viral":
        print("\n🔍 Procesando Viral/Explorar desde Mis Ideas...")
        items = leer_viral_explorar()
        if items:
            urls     = [i["url"] for i in items]
            page_ids = [i["page_id"] for i in items]
            videos   = scrapear_urls_individuales(urls)
            total_videos += len(videos)
            outliers = filtrar_outliers(videos)
            total_outliers += len(outliers)
            for o in outliers:
                fuente = o.get("ownerUsername") or "viral/explorar"
                guardar_hook(o, f"@{fuente}", dry_run=args.dry_run)
                caption    = o.get("caption") or ""
                hook_texto = primeras_palabras(caption, 12)
                patron_num, _ = clasificar_patron_gvb(caption)
                top_hooks.append((hook_texto, o["like_rate"], patron_num, fuente))
            if not args.dry_run:
                for pid in page_ids:
                    marcar_viral_procesado(pid)
                    print(f"  ✅ Marcado como Procesado: {pid}")

    top_hooks.sort(key=lambda x: x[1], reverse=True)

    patrones = [h[2] for h in top_hooks if h[2] > 0]
    patron_frecuente = max(set(patrones), key=patrones.count) if patrones else "—"
    _, patron_nombre = PATRONES_GVB.get(patron_frecuente, (None, "Sin datos"))

    print(f"""
SABUESO COMPLETADO
==================
Videos analizados:  {total_videos}
Outliers guardados: {total_outliers}

Top 3 hooks esta semana:""")

    for i, (hook, lr, pnum, fuente) in enumerate(top_hooks[:3], 1):
        _, pnombre = PATRONES_GVB.get(pnum, (None, "?"))
        print(f"  {i}. \"{hook}\" — {lr}% — P{pnum} {pnombre} — @{fuente}")

    print(f"""
Patrón GVB más frecuente: P{patron_frecuente} — {patron_nombre}
{"[DRY-RUN — nada fue guardado en Notion]" if args.dry_run else ""}
→ Listo para /viral:destrip
""")

if __name__ == "__main__":
    main()
