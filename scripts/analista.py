#!/usr/bin/env python3
"""
El Analista — Agent 5: Análisis de Performance Real
Lee posts publicados, mide rendimiento, detecta causas, actualiza Brief y Hooks DB
"""

import os
import sys
import argparse
import requests
from datetime import datetime, date
from collections import defaultdict
from typing import List, Dict, Tuple, Optional

from dotenv import load_dotenv

load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")

if not NOTION_API_KEY:
    print("❌ Falta variable de entorno: NOTION_API_KEY")
    sys.exit(1)

MIS_POSTS_DS = "3066a95b-4630-42a2-b113-dbbf022d7970"
BRIEF_SEMANAL_DS = "ff4746d0-2480-412a-9763-ba6defde282a"
HOOKS_DB_DS = "ec06af9a-f1fb-4fd0-83f0-1cdf9fe941a5"

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

def notion_query(database_id: str, filter_dict: Optional[Dict] = None) -> List[Dict]:
    """Consultar Notion database"""
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    payload = {"filter": filter_dict} if filter_dict else {}

    try:
        resp = requests.post(url, headers=NOTION_HEADERS, json=payload)
        resp.raise_for_status()
        return resp.json()["results"]
    except Exception as e:
        print(f"❌ Error Notion query: {e}")
        return []

def get_posts_publicados(semana: int) -> List[Dict]:
    """Lee posts publicados de la semana especificada"""
    filter_dict = {
        "and": [
            {"property": "Estado", "select": {"equals": "Publicado"}},
            {"property": "Semana", "number": {"equals": semana}}
        ]
    }

    rows = notion_query(MIS_POSTS_DS, filter_dict)

    posts = []
    for row in rows:
        props = row["properties"]
        posts.append({
            "id": row["id"],
            "titulo": props.get("Titulo", {}).get("title", [{}])[0].get("plain_text", ""),
            "likes": props.get("Likes", {}).get("number", 0),
            "views": props.get("Views", {}).get("number", 0),
            "patron": props.get("Patron GVB", {}).get("select", {}).get("name", ""),
            "formato": props.get("Formato", {}).get("select", {}).get("name", ""),
            "caption": props.get("Caption Elegida", {}).get("rich_text", [{}])[0].get("plain_text", ""),
            "duracion": props.get("Duracion seg", {}).get("number", 0),
            "semana": props.get("Semana", {}).get("number", 0),
        })

    return posts

def calcular_like_rate(likes: int, views: int) -> float:
    """Calcula like rate"""
    return (likes / views) * 100 if views > 0 else 0

def clasificar_rendimiento(like_rate: float, views: int) -> str:
    """Clasifica rendimiento en 3 categorías"""
    if like_rate >= 5:
        return "OUTLIER_POSITIVO"
    elif like_rate >= 3:
        return "NORMAL"
    elif like_rate < 2 or views < 50:
        return "FALLIDO"
    else:
        return "NORMAL"

def detectar_causa(post: Dict) -> List[str]:
    """Detecta causas de posts fallidos"""
    causas = []
    caption = post.get("caption", "").lower()

    # Causa 1: caption descriptiva
    palabras_descriptivas = [
        'en este video', 'en este reel', 'hoy te', 'te muestro',
        'aprende', 'te explico', 'en el siguiente video'
    ]
    if any(p in caption for p in palabras_descriptivas):
        causas.append("CAPTION_DESCRIPTIVA")

    # Causa 2: duración excedida
    duracion = post.get("duracion", 0)
    formato = post.get("formato", "")
    limites = {"Tier List": 45, "Tutorial": 60, "Noticia": 30, "Contraste": 45}
    if formato in limites and duracion > limites[formato]:
        causas.append(f"DURACION_EXCEDIDA ({duracion}s > {limites[formato]}s)")

    # Causa 3: vistas muy bajas
    if post.get("views", 0) < 50:
        causas.append("ALGORITMO_NO_DISTRIBUYO")

    return causas if causas else ["CAUSA_DESCONOCIDA"]

def get_brief_semana(semana: int) -> Optional[Dict]:
    """Lee el Brief de la semana especificada"""
    filter_dict = {"property": "Semana", "number": {"equals": semana}}
    rows = notion_query(BRIEF_SEMANAL_DS, filter_dict)

    if not rows:
        return None

    row = rows[0]
    props = row["properties"]

    return {
        "id": row["id"],
        "titulo": props.get("Titulo", {}).get("title", [{}])[0].get("plain_text", ""),
        "semana": props.get("Semana", {}).get("number", 0)
    }

def actualizar_brief(brief_id: str, funciono: str, no_funciono: str) -> bool:
    """Actualiza Brief Semanal con aprendizajes"""
    url = f"https://api.notion.com/v1/pages/{brief_id}"
    payload = {
        "properties": {
            "Funciono esta semana": {
                "rich_text": [{"text": {"content": funciono}}]
            },
            "No funciono esta semana": {
                "rich_text": [{"text": {"content": no_funciono}}]
            },
            "Estado": {
                "select": {"name": "Completado"}
            }
        }
    }

    try:
        resp = requests.patch(url, headers=NOTION_HEADERS, json=payload)
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"❌ Error actualizando Brief: {e}")
        return False

def actualizar_hook_like_rate(patron: str, fuente: str, like_rate: float) -> bool:
    """Actualiza Like Rate en Hooks DB si es post propio"""
    if not fuente == "@byduvan_ai":
        return False

    # Buscar hook con patrón similar
    rows = notion_query(HOOKS_DB_DS, None)

    for row in rows:
        props = row["properties"]
        if props.get("Patron GVB", {}).get("select", {}).get("name", "") == patron:
            url = f"https://api.notion.com/v1/pages/{row['id']}"
            payload = {
                "properties": {
                    "Like Rate": {"number": like_rate}
                }
            }

            try:
                resp = requests.patch(url, headers=NOTION_HEADERS, json=payload)
                resp.raise_for_status()
                return True
            except Exception as e:
                print(f"⚠️  No se pudo actualizar hook: {e}")
                return False

    return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--week", type=int, help="Analizar semana específica (default: semana anterior)")
    parser.add_argument("--dry-run", action="store_true", help="Ver sin escribir")
    args = parser.parse_args()

    # Calcular semana a analizar (por default, la anterior)
    semana_actual = date.today().isocalendar()[1]
    semana_analizar = args.week or (semana_actual - 1)

    print("\n" + "="*70)
    print(f"📊 EL ANALISTA — Análisis Semana {semana_analizar}")
    print("="*70)

    # PASO 1: Leer posts publicados
    print(f"\n📖 PASO 1: Leyendo Mis Posts publicados (semana {semana_analizar})...")
    posts = get_posts_publicados(semana_analizar)

    if not posts:
        print(f"  ⚠️  Sin posts publicados — publica un video y actualiza Estado a 'Publicado'")
        return

    print(f"  ✓ {len(posts)} posts encontrados")

    # PASO 2-3: Calcular métricas y clasificar
    print(f"\n📊 PASO 2: Calculando métricas reales...")

    outliers_positivos = []
    posts_normales = []
    posts_fallidos = []

    for post in posts:
        like_rate_real = calcular_like_rate(post["likes"], post["views"])
        rendimiento = clasificar_rendimiento(like_rate_real, post["views"])

        post["like_rate_real"] = like_rate_real
        post["rendimiento"] = rendimiento

        if rendimiento == "OUTLIER_POSITIVO":
            outliers_positivos.append(post)
        elif rendimiento == "NORMAL":
            posts_normales.append(post)
        elif rendimiento == "FALLIDO":
            posts_fallidos.append(post)

    print(f"  ✓ OUTLIERS POSITIVOS: {len(outliers_positivos)}")
    print(f"  ✓ NORMALES: {len(posts_normales)}")
    print(f"  ✓ FALLIDOS: {len(posts_fallidos)}")

    # PASO 3: Detectar causas
    print(f"\n🔍 PASO 3: Detectando causas en posts fallidos...")
    for post in posts_fallidos:
        causas = detectar_causa(post)
        post["causas"] = causas

    # PASO 4-5: Actualizar Brief y Hooks
    brief = get_brief_semana(semana_analizar)

    funciono_text = ""
    no_funciono_text = ""

    if outliers_positivos and brief and not args.dry_run:
        post_top = outliers_positivos[0]
        funciono_text = f"{post_top['titulo']} ({post_top['like_rate_real']:.1f}%) — {post_top['patron']}"
        actualizar_hook_like_rate(post_top["patron"], "@byduvan_ai", post_top["like_rate_real"])

    if posts_fallidos and brief and not args.dry_run:
        post_fail = posts_fallidos[0]
        no_funciono_text = f"{post_fail['titulo']} ({post_fail['like_rate_real']:.1f}%) — {', '.join(post_fail['causas'])}"

    if brief and not args.dry_run:
        actualizar_brief(brief["id"], funciono_text, no_funciono_text)

    # PASO 6: Output
    print("\n" + "="*70)
    print(f"✅ ANALISTA — SEMANA {semana_analizar}")
    print("="*70)

    print(f"\nPOSTS ANALIZADOS: {len(posts)}\n")

    if outliers_positivos:
        print("OUTLIERS POSITIVOS ✅")
        for post in outliers_positivos:
            print(f"  ✅ \"{post['titulo'][:50]}\" — {post['like_rate_real']:.1f}% — Patrón {post['patron']}")
            print(f"     Aprendizaje: Este patrón + formato {post['formato']} funciona")

    if posts_normales:
        print("\nPOSTS NORMALES ➡️")
        for post in posts_normales:
            print(f"  ➡️  \"{post['titulo'][:50]}\" — {post['like_rate_real']:.1f}%")

    if posts_fallidos:
        print("\nPOSTS FALLIDOS ❌")
        for post in posts_fallidos:
            print(f"  ❌ \"{post['titulo'][:50]}\" — {post['like_rate_real']:.1f}%")
            print(f"     Causas: {', '.join(post['causas'])}")
            print(f"     Acción: Revisar caption (sin descriptivas) y hook fuerte")

    # Impacto en scoring
    print("\n" + "="*70)
    print("IMPACTO EN SCORING PRÓXIMA SEMANA")
    print("="*70)

    patrones_impacto = defaultdict(lambda: {"positivo": 0, "fallido": 0})

    for post in outliers_positivos:
        patron = post["patron"]
        patrones_impacto[patron]["positivo"] += 1

    for post in posts_fallidos:
        patron = post["patron"]
        patrones_impacto[patron]["fallido"] += 1

    if patrones_impacto:
        for patron, impacto in patrones_impacto.items():
            if impacto["positivo"] > 0:
                print(f"\n  {patron} ↑ (funcionó — bonus +2 en próximo Estratega)")
            if impacto["fallido"] > 0:
                print(f"  {patron} ↓ (falló — penalización -1 en próximo Estratega)")

    # Estado final
    if brief and not args.dry_run:
        print(f"\n✅ ACTUALIZADO EN NOTION:")
        print(f"  ✅ Brief Semana {semana_analizar} → Estado: Completado")
        if outliers_positivos:
            print(f"  ✅ Hooks DB → Like rate actualizado de outlier")

    print(f"\n→ Loop cerrado. Ejecutar /viral:discover el próximo domingo.")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
