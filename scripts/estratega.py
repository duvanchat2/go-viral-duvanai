#!/usr/bin/env python3
"""
El Estratega — Agent 2: Brief Semanal
Lee Hooks DB → Analiza historial propio → Genera Brief Semanal
"""

import os
import json
import sys
import argparse
from datetime import datetime, date, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict

import requests
from dotenv import load_dotenv

load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")

if not NOTION_API_KEY:
    print("❌ Falta variable de entorno: NOTION_API_KEY")
    sys.exit(1)

# Notion bases
HOOKS_DB_DS = "ec06af9a-f1fb-4fd0-83f0-1cdf9fe941a5"
MIS_POSTS_DS = "3066a95b-4630-42a2-b113-dbbf022d7970"
BRIEF_SEMANAL_DS = "ff4746d0-2480-412a-9763-ba6defde282a"

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

@dataclass
class Hook:
    """Un hook de Hooks DB"""
    id: str
    texto: str
    patron: str
    tono: str
    like_rate: float
    views: int
    fuente: str
    semana: int
    formato: str

@dataclass
class PostPropio:
    """Un post de Mis Posts"""
    id: str
    titulo: str
    like_rate: float
    views: int
    semana: int
    patron: str
    formato: str

@dataclass
class Tema:
    """Tema candidato con score"""
    nombre: str
    description: str
    angulo: str
    formato: str
    duracion: int
    patron_gvb: str
    hook_sugerido: str
    por_que_ahora: str
    score: float
    hooks_fuente: List[Hook]

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

def get_current_week() -> int:
    """Retorna número de semana ISO actual"""
    return date.today().isocalendar()[1]

def get_hooks_this_week(semana: int) -> List[Hook]:
    """Lee Hooks DB filtrado por semana"""
    filter_dict = {
        "property": "Semana",
        "number": {"equals": semana}
    }

    rows = notion_query(HOOKS_DB_DS, filter_dict)
    hooks = []

    for row in rows:
        props = row["properties"]
        try:
            hook = Hook(
                id=row["id"],
                texto=props["Hook Texto"]["title"][0]["plain_text"] if props["Hook Texto"]["title"] else "",
                patron=props["Patron GVB"]["select"]["name"] if props["Patron GVB"]["select"] else "",
                tono=props["Tono"]["select"]["name"] if props["Tono"]["select"] else "Mixto",
                like_rate=float(props["Like Rate"]["number"]) if props["Like Rate"]["number"] else 0.0,
                views=int(props["Views"]["number"]) if props["Views"]["number"] else 0,
                fuente=props["Fuente"]["rich_text"][0]["plain_text"] if props["Fuente"]["rich_text"] else "",
                semana=int(props["Semana"]["number"]) if props["Semana"]["number"] else 0,
                formato=props["Formato"]["select"]["name"] if props["Formato"]["select"] else "Contraste"
            )
            hooks.append(hook)
        except (KeyError, IndexError, TypeError) as e:
            print(f"⚠️  Error parseando hook: {e}")

    return hooks

def get_mis_posts_history(semana_actual: int) -> Tuple[List[PostPropio], List[PostPropio]]:
    """Lee Mis Posts, retorna (outliers_positivos, outliers_negativos)"""
    rows = notion_query(MIS_POSTS_DS)
    positivos = []
    negativos = []

    for row in rows:
        props = row["properties"]
        try:
            like_rate = float(props["Like Rate"]["number"]) if props["Like Rate"]["number"] else 0.0
            views = int(props["Views"]["number"]) if props["Views"]["number"] else 0
            semana = int(props["Semana"]["number"]) if props["Semana"]["number"] else 0

            post = PostPropio(
                id=row["id"],
                titulo=props["Titulo"]["title"][0]["plain_text"] if props["Titulo"]["title"] else "",
                like_rate=like_rate,
                views=views,
                semana=semana,
                patron=props.get("Patron GVB", {}).get("select", {}).get("name", ""),
                formato=props.get("Formato", {}).get("select", {}).get("name", "")
            )

            # Outliers positivos: like_rate > 5%
            if like_rate > 5:
                positivos.append(post)

            # Outliers negativos: like_rate < 2% o views < 50
            if like_rate < 2 or views < 50:
                negativos.append(post)

        except (KeyError, IndexError, TypeError) as e:
            print(f"⚠️  Error parseando post: {e}")

    return positivos, negativos

def extract_keywords(text: str) -> set:
    """Extrae palabras clave para agrupación temática"""
    business_words = {"negocio", "dinero", "ventas", "crecimiento", "productividad", "roi", "ingresos", "cliente"}
    ai_words = {"ia", "claude", "chatgpt", "modelo", "prompt", "api", "código", "algoritmo", "mcp"}
    growth_words = {"3x", "10x", "antes", "después", "contraste", "vs", "doblar", "aumentar"}

    text_lower = text.lower()
    keywords = set()

    if any(w in text_lower for w in business_words):
        keywords.add("business")
    if any(w in text_lower for w in ai_words):
        keywords.add("ia")
    if any(w in text_lower for w in growth_words):
        keywords.add("growth")

    return keywords

def group_hooks_by_theme(hooks: List[Hook]) -> Dict[str, List[Hook]]:
    """Agrupa hooks por similitud semántica"""
    groups = defaultdict(list)

    for hook in hooks:
        keywords = extract_keywords(hook.texto)

        # Asignar grupo basado en keywords
        if "business" in keywords:
            groups["business"].append(hook)
        elif "ia" in keywords:
            groups["ia"].append(hook)
        elif "growth" in keywords:
            groups["growth"].append(hook)
        else:
            groups["general"].append(hook)

    # Filtrar grupos pequeños
    return {k: v for k, v in groups.items() if len(v) > 0}

def calculate_theme_score(
    group: List[Hook],
    positivos: List[PostPropio],
    negativos: List[PostPropio],
    tema_reciente: set
) -> float:
    """Calcula score para un grupo de hooks"""
    score = 0.0

    # +3 si patrón aparece 3+ veces
    patron_counts = defaultdict(int)
    for hook in group:
        patron_counts[hook.patron] += 1

    for count in patron_counts.values():
        if count >= 3:
            score += 3
            break

    # +2 si patrón coincide con outlier positivo propio
    for post in positivos:
        for hook in group:
            if post.patron == hook.patron:
                score += 2
                break

    # +2 si tono = "Operador de Negocio" en mayoría
    tono_counts = defaultdict(int)
    for hook in group:
        tono_counts[hook.tono] += 1

    if tono_counts.get("Operador de Negocio", 0) > len(group) / 2:
        score += 2

    # +1 si like_rate promedio > 5%
    avg_like_rate = sum(h.like_rate for h in group) / len(group)
    if avg_like_rate > 5:
        score += 1

    # +1 si fuente incluye referente
    has_referente = any("@" in h.fuente for h in group)
    if has_referente:
        score += 1

    # -2 si tema similar publicado en últimas 2 semanas
    if any(h.texto in tema_reciente for h in group):
        score -= 2

    # -3 si tono = "Tecnico IA" en mayoría
    if tono_counts.get("Tecnico IA", 0) > len(group) / 2:
        score -= 3

    return score

def generate_tema_from_group(
    group: List[Hook],
    group_name: str,
    score: float
) -> Tema:
    """Genera un tema candidato a partir de un grupo de hooks"""

    # Tema: descripción
    if group_name == "business":
        tema_name = "Estrategia de Negocio"
        description = "Cómo crecer y escalar tu negocio digital"
        angulo = "Métodos probados para incrementar ingresos"
    elif group_name == "ia":
        tema_name = "Herramientas IA"
        description = "Cómo usar IA para automatizar procesos"
        angulo = "Herramientas que duplican tu productividad"
    elif group_name == "growth":
        tema_name = "Growth Hacking"
        description = "Tácticas para crecer 10x tu audiencia"
        angulo = "Estrategias contraintuitivas de crecimiento"
    else:
        tema_name = "Insight del Competidor"
        description = "Lo que están haciendo bien los líderes"
        angulo = "Patrones de contenido ganador"

    # Hook sugerido: primeras 12 palabras del mejor hook
    best_hook = max(group, key=lambda h: h.like_rate)
    hook_words = best_hook.texto.split()[:12]
    hook_sugerido = " ".join(hook_words)

    # Patrón: el más frecuente
    patron_counts = defaultdict(int)
    for hook in group:
        patron_counts[hook.patron] += 1

    patron_gvb = max(patron_counts.items(), key=lambda x: x[1])[0]

    # Formato: el más común en el grupo
    formato_counts = defaultdict(int)
    for hook in group:
        formato_counts[hook.formato] += 1

    formato = max(formato_counts.items(), key=lambda x: x[1])[0] if formato_counts else "Contraste"

    # Duración objetivo
    duracion = 60  # default

    # Por qué ahora
    avg_like_rate = sum(h.like_rate for h in group) / len(group)
    por_que = f"Like rate promedio {avg_like_rate:.1f}% — patrón {patron_gvb} validado"

    return Tema(
        nombre=tema_name,
        description=description,
        angulo=angulo,
        formato=formato,
        duracion=duracion,
        patron_gvb=patron_gvb,
        hook_sugerido=hook_sugerido,
        por_que_ahora=por_que,
        score=score,
        hooks_fuente=group
    )

def create_brief_page(temas_top3: List[Tema], semana: int) -> Optional[str]:
    """Crea página en Brief Semanal"""
    hoje = date.today().isoformat()
    titulo = f"Brief Semana {semana} — {hoje}"

    properties = {
        "Titulo": {
            "title": [{"text": {"content": titulo}}]
        },
        "Semana": {
            "number": semana
        },
        "Fecha": {
            "date": {"start": hoje}
        },
        "Tema 1 Hook": {
            "rich_text": [{"text": {"content": temas_top3[0].hook_sugerido}}]
        },
        "Tema 1 Formato": {
            "select": {"name": temas_top3[0].formato}
        },
        "Tema 1 Patron GVB": {
            "select": {"name": temas_top3[0].patron_gvb}
        },
        "Estado": {
            "select": {"name": "Pendiente"}
        }
    }

    # Agregar Tema 2 si existe
    if len(temas_top3) > 1:
        properties["Tema 2 Hook"] = {
            "rich_text": [{"text": {"content": temas_top3[1].hook_sugerido}}]
        }
        properties["Tema 2 Formato"] = {
            "select": {"name": temas_top3[1].formato}
        }

    # Agregar Tema 3 si existe
    if len(temas_top3) > 2:
        properties["Tema 3 Hook"] = {
            "rich_text": [{"text": {"content": temas_top3[2].hook_sugerido}}]
        }

    # Aprendizajes (si hay datos)
    # Por ahora vacío, puede llenarse después

    url = f"https://api.notion.com/v1/pages"
    payload = {
        "parent": {"database_id": BRIEF_SEMANAL_DS},
        "properties": properties
    }

    try:
        resp = requests.post(url, headers=NOTION_HEADERS, json=payload)
        resp.raise_for_status()
        page_id = resp.json()["id"]
        return page_id
    except Exception as e:
        print(f"❌ Error creando Brief Semanal: {e}")
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--week", type=int, help="Semana a procesar (default: actual)")
    parser.add_argument("--dry-run", action="store_true", help="Ver sin escribir")
    parser.add_argument("--verbose", action="store_true", help="Mostrar scoring detallado")
    args = parser.parse_args()

    semana = args.week or get_current_week()

    print("\n" + "="*70)
    print(f"📊 EL ESTRATEGA — Brief Semanal {semana}")
    print("="*70)

    # PASO 1: Leer Hooks DB
    print(f"\n📖 PASO 1: Leyendo Hooks DB (semana {semana})...")
    hooks = get_hooks_this_week(semana)

    if not hooks:
        print(f"❌ Hooks DB vacía — ejecuta /viral:discover primero")
        return

    print(f"  ✓ {len(hooks)} hooks encontrados")

    # PASO 2: Leer historial propio
    print("\n📚 PASO 2: Analizando historial propio (Mis Posts)...")
    positivos, negativos = get_mis_posts_history(semana)
    print(f"  ✓ Outliers positivos (like_rate > 5%): {len(positivos)}")
    print(f"  ✓ Outliers negativos (like_rate < 2% o views < 50): {len(negativos)}")

    # PASO 3: Agrupar y scoring
    print("\n📊 PASO 3: Calculando scores temáticos...")
    grupos = group_hooks_by_theme(hooks)

    temas_candidatos = []
    tema_reciente = {p.patron for p in positivos}  # Simple filter para ahora

    for grupo_name, group_hooks in grupos.items():
        score = calculate_theme_score(group_hooks, positivos, negativos, tema_reciente)
        tema = generate_tema_from_group(group_hooks, grupo_name, score)
        temas_candidatos.append(tema)

        if args.verbose:
            print(f"  • {grupo_name}: score {score:.1f} ({len(group_hooks)} hooks)")

    # PASO 4: Top 3
    print("\n🎯 PASO 4: Seleccionando top 3 temas...")
    temas_top3 = sorted(temas_candidatos, key=lambda t: t.score, reverse=True)[:3]

    for idx, tema in enumerate(temas_top3, 1):
        print(f"  {idx}. {tema.nombre} (score: {tema.score:.1f})")

    # PASO 5: Escribir Brief
    print("\n✍️  PASO 5: Escribiendo Brief Semanal...")
    if not args.dry_run:
        page_id = create_brief_page(temas_top3, semana)
        if page_id:
            print(f"  ✓ Brief creado: {page_id}")

    # PASO 6: Output
    print("\n\n" + "="*70)
    print(f"✅ ESTRATEGA COMPLETADO — BRIEF SEMANA {semana}")
    print("="*70)

    for idx, tema in enumerate(temas_top3, 1):
        suffix = " ⭐" if idx == 1 else ""
        print(f"\nTEMA {idx}{suffix} (score: {tema.score:.1f})")
        print(f"Tema: {tema.description}")
        print(f"Ángulo: {tema.angulo}")
        print(f"Formato: {tema.formato} — {tema.duracion} seg")
        print(f"Patrón GVB: {tema.patron_gvb}")
        print(f"Hook: \"{tema.hook_sugerido}\"")
        print(f"Por qué: {tema.por_que_ahora}")

    if positivos or negativos:
        print(f"\n📈 APRENDIZAJE SEMANA:")
        if positivos:
            print(f"✅ Funcionó: {positivos[0].titulo} ({positivos[0].like_rate:.1f}%)")
        if negativos:
            print(f"❌ No funcionó: {negativos[0].titulo} ({negativos[0].like_rate:.1f}%)")

    print(f"\n→ Próximo: /viral:script \"{temas_top3[0].hook_sugerido}\"\n")

if __name__ == "__main__":
    main()
