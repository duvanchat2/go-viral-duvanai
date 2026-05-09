#!/usr/bin/env python3
"""
transcriptor.py — Agente de Transcripción y Scoring
Lee Hooks DB, transcribe videos con Apify/AssemblyAI, calcula score compuesto

Uso:
    python3 scripts/transcriptor.py
    python3 scripts/transcriptor.py --dry-run
"""

import os
import re
import sys
import time
import json
import argparse
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ─── CONFIGURACIÓN ────────────────────────────────────────────────────────────

NOTION_API_KEY      = os.getenv("NOTION_API_KEY")
APIFY_API_TOKEN     = os.getenv("APIFY_API_TOKEN")
ASSEMBLYAI_API_KEY  = os.getenv("ASSEMBLYAI_API_KEY")

NOTION_VERSION      = "2022-06-28"
NOTION_BASE         = "https://api.notion.com/v1"
APIFY_BASE          = "https://api.apify.com/v2"
ASSEMBLYAI_BASE     = "https://api.assemblyai.com/v2"

HOOKS_DB            = "ec06af9a-f1fb-4fd0-83f0-1cdf9fe941a5"
ACTOR_TRANSCRIBE    = "sian.agency~instagram-ai-transcript-extractor"

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

# ─── LEER HOOKS PENDIENTES ────────────────────────────────────────────────────

def leer_hooks_pendientes() -> list[dict]:
    rows = notion_query(HOOKS_DB, {
        "and": [
            {"property": "Estado Transcripcion", "select": {"equals": "Pendiente"}},
            {"property": "URL Video", "url": {"is_not_empty": True}}
        ]
    })
    resultado = []
    for row in rows:
        hook_texto = get_prop(row, "Hook Texto")
        url_video = get_prop(row, "URL Video")
        like_rate = get_prop(row, "Like Rate") or 0
        views = get_prop(row, "Views") or 0
        comentarios = get_prop(row, "Comentarios") or 0

        if url_video:
            resultado.append({
                "id": row["id"],
                "hook_texto": hook_texto,
                "url_video": url_video,
                "like_rate": like_rate,
                "views": views,
                "comentarios": comentarios
            })
    print(f"  → {len(resultado)} hooks pendientes de transcribir")
    return resultado

# ─── TRANSCRIPCIÓN CON APIFY ──────────────────────────────────────────────────

def transcribir_con_apify(url_video: str) -> str:
    url = f"{APIFY_BASE}/acts/{ACTOR_TRANSCRIBE}/runs?token={APIFY_API_TOKEN}"
    payload = {"directUrl": url_video}

    try:
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
        run_id = resp.json()["data"]["id"]

        status_url = f"{APIFY_BASE}/actor-runs/{run_id}?token={APIFY_API_TOKEN}"
        while True:
            time.sleep(5)
            r = requests.get(status_url)
            r.raise_for_status()
            if r.json()["data"]["status"] == "SUCCEEDED":
                break

        dataset_id = r.json()["data"]["defaultDatasetId"]
        items_url = f"{APIFY_BASE}/datasets/{dataset_id}/items?token={APIFY_API_TOKEN}&format=json"
        items = requests.get(items_url).json()

        if items and len(items) > 0:
            return items[0].get("transcript", "")
        return ""
    except Exception as e:
        print(f"    ⚠️  Apify falló: {e}")
        return None

# ─── TRANSCRIPCIÓN CON ASSEMBLYAI ─────────────────────────────────────────────

def transcribir_con_assemblyai(url_video: str) -> str:
    headers = {
        "Authorization": ASSEMBLYAI_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "audio_url": url_video,
        "speech_model": "universal-2",
        "language_code": "es"
    }

    try:
        # Enviar transcripción
        resp = requests.post(f"{ASSEMBLYAI_BASE}/transcript", json=payload, headers=headers)
        resp.raise_for_status()
        transcript_id = resp.json()["id"]

        # Polling
        while True:
            time.sleep(3)
            r = requests.get(f"{ASSEMBLYAI_BASE}/transcript/{transcript_id}", headers=headers)
            r.raise_for_status()
            data = r.json()
            if data["status"] == "completed":
                return data.get("text", "")
            elif data["status"] == "error":
                print(f"    ⚠️  AssemblyAI error: {data.get('error')}")
                return None
    except Exception as e:
        print(f"    ⚠️  AssemblyAI falló: {e}")
        return None

# ─── CALCULAR SCORE COMPUESTO ─────────────────────────────────────────────────

def calcular_score(like_rate: float, comentarios: int, views: int) -> float:
    if views == 0:
        return 0

    comentarios_rate = (comentarios / views) * 100

    bonus = 10 if comentarios > 20 else 0

    score = (like_rate * 0.4) + (comentarios_rate * 0.35) + bonus
    return round(score, 2)

# ─── EXTRAER PRIMERAS N PALABRAS ──────────────────────────────────────────────

def primeras_palabras(texto: str, n: int) -> str:
    return " ".join(texto.strip().split()[:n])

# ─── PROCESAR HOOKS ───────────────────────────────────────────────────────────

def procesar_hook(hook: dict, dry_run: bool = False):
    print(f"\n  🎬 Transcribiendo: {hook['hook_texto'][:40]}...")

    # Intentar Apify primero
    transcript = transcribir_con_apify(hook["url_video"])

    # Si Apify falla, usar AssemblyAI
    if transcript is None:
        print(f"    → Intentando AssemblyAI...")
        transcript = transcribir_con_assemblyai(hook["url_video"])

    if not transcript:
        print(f"    ❌ Error: No se pudo transcribir")
        if not dry_run:
            notion_update_page(hook["id"], {
                "Estado Transcripcion": {"select": {"name": "Error"}}
            })
        return False

    # Extraer primeras 15 palabras
    transcript_hook = primeras_palabras(transcript, 15)

    # Calcular score
    comentarios_rate = (hook["comentarios"] / hook["views"] * 100) if hook["views"] > 0 else 0
    score = calcular_score(hook["like_rate"], hook["comentarios"], hook["views"])

    print(f"    ✅ Transcript: {transcript_hook[:50]}...")
    print(f"    📊 Score: {score} (like_rate: {hook['like_rate']:.1f}% + comentarios_rate: {comentarios_rate:.1f}%)")

    if not dry_run:
        notion_update_page(hook["id"], {
            "Transcripcion": {
                "rich_text": [{"text": {"content": transcript}}]
            },
            "Transcript Hook": {
                "rich_text": [{"text": {"content": transcript_hook}}]
            },
            "Score": {"number": score},
            "Comentarios Rate": {"number": comentarios_rate},
            "Estado Transcripcion": {"select": {"name": "Transcrito"}}
        })

    return True

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Transcriptor — Transcribe hooks y calcula score")
    parser.add_argument("--dry-run", action="store_true", help="Ver sin escribir")
    args = parser.parse_args()

    if not NOTION_API_KEY or not APIFY_API_TOKEN or not ASSEMBLYAI_API_KEY:
        print("❌ Faltan variables de entorno: NOTION_API_KEY, APIFY_API_TOKEN, ASSEMBLYAI_API_KEY")
        sys.exit(1)

    print("\n🎙️  TRANSCRIPTOR — Iniciando\n" + "="*50)

    print("\n📖 Leyendo Hooks DB...")
    hooks = leer_hooks_pendientes()

    if not hooks:
        print("  ℹ️  Sin hooks pendientes")
        return

    # Procesar cada hook
    procesados = 0
    errores = 0

    for hook in hooks:
        try:
            if procesar_hook(hook, args.dry_run):
                procesados += 1
            else:
                errores += 1
        except Exception as e:
            print(f"    ❌ Error inesperado: {e}")
            errores += 1

    # Output final
    print("\n" + "="*50)
    print(f"✅ TRANSCRIPTOR COMPLETADO")
    print("="*50)
    print(f"\nHooks procesados: {procesados}")
    print(f"Errores: {errores}")

    if args.dry_run:
        print("\n(dry-run — sin cambios en Notion)")

    print()

if __name__ == "__main__":
    main()
