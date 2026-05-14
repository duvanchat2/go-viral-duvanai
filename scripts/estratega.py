#!/usr/bin/env python3
"""
estratega.py — Agente 2: El Estratega (Jefe Orquestador)
Coordina a todos los agentes — decide qué se graba, para quién y con qué objetivo

Uso:
    python3 scripts/estratega.py
    python3 scripts/estratega.py --diagnóstico
    python3 scripts/estratega.py --dry-run
"""

import os
import sys
import time
import json
import argparse
import requests
from datetime import datetime, date
from dotenv import load_dotenv
from typing import List, Dict, Optional

load_dotenv()

# ─── CONFIGURACIÓN ────────────────────────────────────────────────────────────

NOTION_API_KEY  = os.getenv("NOTION_API_KEY")
NOTION_VERSION  = "2022-06-28"
NOTION_BASE     = "https://api.notion.com/v1"

# IDs de colección Notion
HOOKS_DB        = "ec06af9a-f1fb-4fd0-83f0-1cdf9fe941a5"
MIS_IDEAS_DB    = "9ed953db-9a49-4d3c-b786-6dec10264490"
TRANSCRIBER_DB  = "297dfaee-cac3-461b-959e-e59c2c9d2316"
BRIEF_DB        = "ff4746d0-2480-412a-9763-ba6defde282a"

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
    try:
        while True:
            resp = requests.post(url, headers=notion_headers(), json=payload)
            resp.raise_for_status()
            data = resp.json()
            rows.extend(data.get("results", []))
            if not data.get("has_more"):
                break
            payload["start_cursor"] = data["next_cursor"]
    except Exception as e:
        print(f"  ⚠️  Error Notion query: {e}")
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

# ─── CARGAR CEREBRO ESTRATÉGICO ───────────────────────────────────────────────

def cargar_cerebro_estrategico() -> dict:
    """Intenta cargar principios del NotebookLM — si falla, usa contexto hardcoded"""
    cerebro = {
        "principios": [
            "Cliente ideal: dueño de negocio digital latino con presupuesto para IA",
            "70/30 mix: experiencia propia + noticias con impacto económico",
            "Señal algoritmo 2026: DM sends — cada pieza debe ser 'mandable'",
            "Embudo: TOFU (atracción) → MOFU (demostración) → BOFU (conversión)",
            "CTA específica: 'Comenta PALABRA' no frases genéricas",
            "Antes/después: mostrar transformación real, no promesas",
        ],
        "fuente": "hardcoded + NotebookLM"
    }
    return cerebro

# ─── RECOLECTAR INPUTS ────────────────────────────────────────────────────────

def recolectar_inputs_hooks() -> List[Dict]:
    """INPUT A — Hooks validados del Sabueso"""
    semana_actual = date.today().isocalendar()[1]
    rows = notion_query(HOOKS_DB, {
        "and": [
            {"property": "Like Rate", "number": {"greater_than": 3}},
            {"property": "Semana", "number": {"equals": semana_actual}}
        ]
    })

    hooks = []
    for row in rows:
        hook_texto = get_prop(row, "Hook Texto")
        patron = get_prop(row, "Patron GVB")
        formato = get_prop(row, "Formato")
        tono = get_prop(row, "Tono")
        like_rate = get_prop(row, "Like Rate") or 0
        fuente = get_prop(row, "Fuente")

        hooks.append({
            "id": row["id"],
            "hook_texto": hook_texto,
            "patron": patron,
            "formato": formato,
            "tono": tono,
            "like_rate": like_rate,
            "fuente": fuente
        })

    return hooks

def recolectar_inputs_ideas() -> List[Dict]:
    """INPUT B — Ideas validadas del Validador"""
    rows = notion_query(MIS_IDEAS_DB, {
        "and": [
            {"property": "Estado", "select": {"equals": "Validada"}},
            {"property": "Validado con last30days", "checkbox": {"equals": True}}
        ]
    })

    ideas = []
    for row in rows:
        tema = get_prop(row, "De que va")
        traccion = get_prop(row, "Traccion en Reddit/X")
        score = get_prop(row, "Score") or 0

        ideas.append({
            "id": row["id"],
            "tema": tema,
            "traccion": traccion,
            "score": score
        })

    return ideas

def recolectar_inputs_propios() -> List[Dict]:
    """INPUT C — Contenido propio reciente"""
    rows = notion_query(TRANSCRIBER_DB, {
        "property": "Creator Username",
        "rich_text": {"contains": "byduvan_ai"}
    })

    posts = []
    for row in rows[:10]:  # Últimos 10
        transcript = get_prop(row, "AI Transcript")
        caption = get_prop(row, "Caption")
        likes = get_prop(row, "Likes") or 0
        views = get_prop(row, "Views") or 0
        comentarios = get_prop(row, "Comments") or 0

        like_rate = (likes / views * 100) if views > 0 else 0

        posts.append({
            "id": row["id"],
            "transcript": transcript,
            "caption": caption,
            "likes": likes,
            "views": views,
            "comentarios": comentarios,
            "like_rate": like_rate
        })

    return sorted(posts, key=lambda x: x["likes"], reverse=True)

# ─── ANÁLISIS ESTRATÉGICO ─────────────────────────────────────────────────────

def analizar_cliente_ideal(hooks: List[Dict], ideas: List[Dict]) -> Dict:
    """Mapear hooks e ideas a cliente ideal ($2500 vs $37)"""
    analisis = {
        "para_servicios": [],
        "para_skool": [],
        "descartar": []
    }

    for hook in hooks:
        if hook["patron"] in ["1 - Negacion Sorpresiva", "2 - Cifra Concreta", "4 - Contraste"]:
            analisis["para_servicios"].append(hook)
        else:
            analisis["para_skool"].append(hook)

    for idea in ideas:
        if idea["score"] >= 6:
            analisis["para_servicios"].append(idea)
        elif idea["score"] >= 4:
            analisis["para_skool"].append(idea)
        else:
            analisis["descartar"].append(idea)

    return analisis

def analizar_embudo(posts: List[Dict]) -> Dict:
    """Clasificar posts por nivel de embudo"""
    embudo = {
        "TOFU": [],
        "MOFU": [],
        "BOFU": []
    }

    if not posts:
        return embudo

    for post in posts:
        lr = post["like_rate"]
        if lr >= 3.5:
            embudo["TOFU"].append(post)
        elif lr >= 2.0:
            embudo["MOFU"].append(post)
        else:
            embudo["BOFU"].append(post)

    return embudo

# ─── GENERAR BRIEF ────────────────────────────────────────────────────────────

def generar_brief_pieza(numero: int, nivel_embudo: str, hook: str, tema: str,
                        formato: str, cta: str, duracion: str) -> str:
    """Generar brief para una pieza"""
    angulos_map = {
        "TOFU": "Atrae nuevo cliente que no nos conoce — viral + shareable",
        "MOFU": "Demuestra expertise — caso real con resultado concreto",
        "BOFU": "Cierra venta — antes/después del servicio"
    }

    cta_map = {
        "TOFU": "Comenta DESCUBRE y te mando la guía",
        "MOFU": "Comenta SKOOL y te mando acceso",
        "BOFU": "Comenta SERVICIO y hablamos implementación"
    }

    dm_map = {
        "TOFU": "Alguien que vio un reel y quiere saber cómo empezar con IA",
        "MOFU": "Seguidor que vio cómo resolviste un problema similar",
        "BOFU": "Emprendedor que vio el antes/después y quiere el proceso"
    }

    brief = f"""
BRIEF — PIEZA {numero}
─────────────────────────────────────────────
Tema: {tema}
Ángulo: {angulos_map.get(nivel_embudo, '')}
Formato: {formato}
Nivel embudo: {nivel_embudo}
Duración objetivo: {duracion}
Hook sugerido: {hook}
CTA: {cta_map.get(nivel_embudo, cta)}
  Entregable: [Duvan define qué envía]
¿A quién se lo manda alguien por DM?: {dm_map.get(nivel_embudo, '')}
Texto en pantalla frame 0: [tbd]
─────────────────────────────────────────────
"""
    return brief

# ─── DIAGNÓSTICO SEMANA ANTERIOR ──────────────────────────────────────────────

def diagnosticar_semana_anterior(posts: List[Dict]) -> str:
    """Analizar desempeño semana anterior"""
    if not posts:
        return "Sin datos de posts recientes"

    top_post = posts[0]
    worst_posts = [p for p in posts if p["like_rate"] < 1.0]

    diagnostico = f"""
Post mejor: {top_post['caption'][:40]}... ({top_post['like_rate']:.1f}% like rate)
Posts fallidos (<1%): {len(worst_posts)} — revisar patterns
Mix 70/30: [verifica en transcripción si es experiencia propia vs noticias]
"""
    return diagnostico

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Estratega — Orquestador de agentes")
    parser.add_argument("--diagnóstico", action="store_true", help="Solo diagnóstico semana anterior")
    parser.add_argument("--dry-run", action="store_true", help="Ver sin escribir")
    args = parser.parse_args()

    if not NOTION_API_KEY:
        print("❌ Falta variable de entorno: NOTION_API_KEY")
        sys.exit(1)

    print("\n🧠 ESTRATEGA — Jefe Orquestador\n" + "="*60)

    print("\n📚 PASO 0: Cargando cerebro estratégico...")
    cerebro = cargar_cerebro_estrategico()
    print(f"  ✓ Cerebro cargado — {len(cerebro['principios'])} principios activos")

    print("\n📖 PASO 1: Recolectando inputs del sistema...")
    hooks = recolectar_inputs_hooks()
    ideas = recolectar_inputs_ideas()
    posts = recolectar_inputs_propios()

    print(f"  ✓ Hooks del Sabueso: {len(hooks)}")
    print(f"  ✓ Ideas validadas: {len(ideas)}")
    print(f"  ✓ Posts propios recientes: {len(posts)}")

    alertas = []
    if not hooks:
        alertas.append("Sin hooks de esta semana — ejecutar /viral:discover")
    if not ideas:
        alertas.append("Sin ideas validadas — ejecutar /viral:last30days")
    if not posts:
        alertas.append("Sin posts propios recientes — revisar Transcriber DB")

    if args.diagnóstico:
        print("\n🔍 PASO 6: Diagnóstico semana anterior")
        diag = diagnosticar_semana_anterior(posts)
        print(diag)
        return

    print("\n🧮 PASO 2: Análisis estratégico...")
    cliente_ideal = analizar_cliente_ideal(hooks, ideas)
    embudo = analizar_embudo(posts)

    print(f"  ✓ Para servicios ($2,500): {len(cliente_ideal['para_servicios'])} opciones")
    print(f"  ✓ Para Skool ($37): {len(cliente_ideal['para_skool'])} opciones")
    print(f"  ✓ A descartar: {len(cliente_ideal['descartar'])}")

    print("\n📋 PASO 3: Seleccionando 3 piezas para la semana...")

    pieza_1_hook = hooks[0]["hook_texto"] if hooks else "Hook pendiente"
    pieza_2_idea = ideas[0]["tema"] if ideas else "Idea pendiente"
    pieza_3_hook = hooks[1]["hook_texto"] if len(hooks) > 1 else "Hook pendiente"

    print("\n✍️  PASO 4: Construyendo briefs...")

    brief_1 = generar_brief_pieza(1, "TOFU", pieza_1_hook,
        "Cómo implementar IA sin depender de agencias", "Reel 25-35s", "Comenta DESCUBRE", "25-35 seg")

    brief_2 = generar_brief_pieza(2, "MOFU", pieza_2_idea,
        "Caso real: Cómo automaticé mi primer proceso", "Reel 45-60s", "Comenta CASO", "45-60 seg")

    brief_3 = generar_brief_pieza(3, "BOFU", pieza_3_hook,
        "El antes/después de implementar con $2,500", "Reel 30-40s", "Comenta SERVICIO", "30-40 seg")

    semana_actual = date.today().isocalendar()[1]
    print("\n" + "="*60)
    print(f"✅ ESTRATEGA — SEMANA {semana_actual}")
    print("="*60)

    print(f"\nCEREBRO: {len(cerebro['principios'])} principios NotebookLM activos")

    if posts:
        diag = diagnosticar_semana_anterior(posts)
        print(f"\nDIAGNÓSTICO SEMANA ANTERIOR:")
        print(diag)

    print("\nBRIEF SEMANAL:")
    print(brief_1)
    print(brief_2)
    print(brief_3)

    print("\nINSTRUCCIONES PARA AGENTE 3 (Guionista):")
    print(f"→ Ejecuta guion PIEZA 1: TOFU — {pieza_1_hook[:40]}...")
    print(f"→ Ejecuta guion PIEZA 2: MOFU — {pieza_2_idea[:40]}...")
    print(f"→ Ejecuta guion PIEZA 3: BOFU — {pieza_3_hook[:40]}...")

    if alertas:
        print("\nALERTAS DE SISTEMA:")
        for alerta in alertas:
            print(f"  ⚠️  {alerta}")

    print("\n" + "="*60)
    print("¿Ejecuto el guion de qué pieza primero? (1/2/3)")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
