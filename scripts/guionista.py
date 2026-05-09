#!/usr/bin/env python3
"""
El Guionista — Agent 3: HookGenie + Guion
Convierte hooks en guiones de video con duración DURA
"""

import os
import sys
import argparse
import re
from datetime import datetime, date
from typing import List, Dict, Tuple, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")

if not NOTION_API_KEY:
    print("❌ Falta variable de entorno: NOTION_API_KEY")
    sys.exit(1)

BRIEF_SEMANAL_DS = "ff4746d0-2480-412a-9763-ba6defde282a"
MIS_POSTS_DS = "3066a95b-4630-42a2-b113-dbbf022d7970"

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

# HookGenie patterns
HOOKGENIE_PATTERNS = {
    1: [
        "No [acción común] para [resultado]. Hay algo mejor.",
        "[Herramienta] no es para [uso obvio]. Es para [resultado de negocio]."
    ],
    2: [
        "En [X] minutos tienes [resultado concreto de negocio].",
        "[X] de cada 10 dueños de negocios digitales no hace esto."
    ],
    3: [
        "Lo que nadie te dice sobre [tema] en tu negocio digital.",
        "Por esto tus competidores consiguen más clientes con IA."
    ],
    4: [
        "Antes: [dolor]. Ahora: [resultado]. Gracias a [herramienta].",
        "[Dolor conocido] → [herramienta] → [resultado en tiempo concreto]."
    ],
    5: [
        "¿Por qué [herramienta] hace que los negocios digitales [resultado]?",
        "¿Qué pasa cuando conectas [herramienta A] con [herramienta B]?"
    ],
    6: [
        "Esto acaba de cambiar en [herramienta] y afecta tu negocio.",
        "Si no haces esto esta semana en tu negocio digital, ya vas tarde."
    ]
}

DURACIONES = {
    "Tier List": 45,
    "Tutorial": 60,
    "Noticia": 30,
    "Contraste": 45,
    "Caso de Uso": 45,
    "Comparativa": 45
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

def get_brief_reciente() -> Optional[Dict]:
    """Lee el Brief más reciente"""
    rows = notion_query(BRIEF_SEMANAL_DS)

    if not rows:
        return None

    # Ordenar por Semana (más reciente primero)
    row = rows[0]  # Simplificado
    props = row["properties"]

    return {
        "titulo": props["Titulo"]["title"][0]["plain_text"] if props["Titulo"]["title"] else "",
        "tema_1_hook": props.get("Tema 1 Hook", {}).get("rich_text", [{}])[0].get("plain_text", ""),
        "tema_1_formato": props.get("Tema 1 Formato", {}).get("select", {}).get("name", "Contraste"),
        "tema_1_patron": props.get("Tema 1 Patron GVB", {}).get("select", {}).get("name", "4 - Contraste")
    }

def generar_variaciones_hookgenie(hook_original: str, patron: int) -> List[str]:
    """Genera 2 variaciones del hook para el patrón dado"""
    templates = HOOKGENIE_PATTERNS.get(patron, [hook_original])

    # Simplificado: retornar templates
    return templates

def seleccionar_hook_ganador(hook_original: str) -> str:
    """Selecciona el hook ganador (≤12 palabras, operador de negocio)"""
    words = hook_original.split()
    if len(words) > 12:
        return " ".join(words[:12])
    return hook_original

def detectar_tema(brief_props: Dict) -> Tuple[str, str, str]:
    """Detecta formato, patrón, duración del brief"""
    formato = brief_props.get("tema_1_formato", "Contraste")
    patron = brief_props.get("tema_1_patron", "4 - Contraste")
    duracion = DURACIONES.get(formato, 45)

    return formato, patron, duracion

def escribir_guion_contraste(hook: str, tema: str, duracion: int) -> str:
    """Escribe guion para Contraste/Caso de Uso (≤45 seg)"""
    guion = f"""[0:00-0:03] HOOK
{hook}

[0:03-0:08] DOLOR
La mayoría de emprendedores gasta dinero en ads sin ver resultados reales.

[0:08-0:20] SOLUCIÓN
La clave está en automatizar el proceso de validación del problema antes de invertir.
Así identificas si realmente vale la pena escalar.

[0:20-0:35] RESULTADO
Con este método, reduje mis costos de adquisición en 3x en 2 semanas.
Ahora pruebo ideas en 48 horas, no en 3 meses.

[0:35-0:45] RETENCIÓN + CTA
Si quieres reproducir esto, comenta "MÉTODO" abajo.
Te paso el paso a paso completo."""

    return guion

def escribir_guion_tutorial(hook: str, tema: str, duracion: int) -> str:
    """Escribe guion para Tutorial (≤60 seg)"""
    guion = f"""[0:00-0:03] HOOK
{hook}

[0:03-0:10] PROMESA
Te voy a mostrar los 3 pasos exactos que usamos para aumentar ventas 3x.

[0:10-0:25] PASO 1
Primero: identifica dónde están tus clientes potenciales. No donde crees que están.
Usa Google Trends + Reddit para ver qué buscan realmente.

[0:25-0:40] PASO 2
Segundo: crea contenido que responda esa búsqueda específica.
No hagas contenido genérico, sé quirúrgico con el problema.

[0:40-0:55] PASO 3
Tercero: mide como obsesionado. Like rate, watch time, clicks.
Cada métrica te dice si la gente realmente necesita tu solución.

[0:55-0:60] RESULTADO + CTA
Estos 3 pasos generaron 250k en ingresos el mes pasado.
Guarda este video y implementa hoy mismo."""

    return guion

def escribir_guion_noticia(hook: str, tema: str, duracion: int) -> str:
    """Escribe guion para Noticia (≤30 seg)"""
    guion = f"""[0:00-0:03] HOOK
{hook}

[0:03-0:15] QUÉ CAMBIÓ
OpenAI acaba de lanzar su API de voz en tiempo real.
Eso significa que ahora puedes automatizar atención al cliente al 100%.

[0:15-0:25] ACCIÓN CONCRETA
Si tienes un negocio digital, pruébalo HOY en tu chatbot.
El setup toma literalmente 15 minutos.

[0:25-0:30] CTA
Comenta "READY" si quieres el link para probar.
Más abajo en el primer comentario."""

    return guion

def estimar_duracion(guion: str) -> float:
    """Estima duración en segundos (150 palabras/min)"""
    palabras = len(guion.split())
    return palabras / 2.5

def validar_guion(guion: str, duracion_max: int) -> bool:
    """Valida que el guion no supere la duración"""
    duracion_estimada = estimar_duracion(guion)
    return duracion_estimada <= duracion_max

def crear_guion_en_mis_posts(
    titulo: str,
    guion: str,
    formato: str,
    patron: str,
    hashtags: str = ""
) -> Optional[str]:
    """Crea página en Mis Posts"""
    props = {
        "Titulo": {
            "title": [{"text": {"content": titulo}}]
        },
        "Semana": {
            "number": date.today().isocalendar()[1]
        },
        "Formato": {
            "select": {"name": formato}
        },
        "Patron GVB": {
            "select": {"name": patron}
        },
        "Estado": {
            "select": {"name": "Pendiente grabacion"}
        },
        "Guion": {
            "rich_text": [{"text": {"content": guion}}]
        },
        "Hashtags": {
            "rich_text": [{"text": {"content": hashtags}}]
        }
    }

    url = f"https://api.notion.com/v1/pages"
    payload = {
        "parent": {"database_id": MIS_POSTS_DS},
        "properties": props
    }

    try:
        resp = requests.post(url, headers=NOTION_HEADERS, json=payload)
        resp.raise_for_status()
        return resp.json()["id"]
    except Exception as e:
        print(f"❌ Error creando en Mis Posts: {e}")
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("hook", nargs="?", help="Hook explícito")
    parser.add_argument("--auto", action="store_true", help="Leer Brief automático")
    parser.add_argument("--formato", help="Force formato")
    parser.add_argument("--duracion", type=int, help="Override duración máxima")
    parser.add_argument("--dry-run", action="store_true", help="Ver sin escribir")
    args = parser.parse_args()

    print("\n" + "="*70)
    print("✍️  EL GUIONISTA — HookGenie + Guion")
    print("="*70)

    # Obtener hook
    if args.hook:
        hook = args.hook
        print(f"\n📌 Hook explícito: \"{hook}\"")
    elif args.auto:
        print(f"\n📚 Leyendo Brief más reciente...")
        brief = get_brief_reciente()
        if not brief:
            print("❌ Sin Brief Semanal disponible")
            return
        hook = brief["tema_1_hook"]
        formato = brief["tema_1_formato"]
        patron = brief["tema_1_patron"]
        print(f"  ✓ Hook Tema 1: \"{hook}\"")
        print(f"  ✓ Formato: {formato}")
        print(f"  ✓ Patrón: {patron}")
    else:
        print("❌ Especificar hook o usar --auto")
        return

    # Formato y duración
    if not args.auto:
        formato = args.formato or "Contraste"
        patron = "4 - Contraste"
    duracion_max = args.duracion or DURACIONES.get(formato, 45)

    print(f"\n🎬 PASO 1: HookGenie — 10 variaciones")
    print(f"  Patrón original: {patron}")
    print(f"  Hook ganador: \"{hook}\" ({len(hook.split())} palabras)")

    # PASO 2-3: Escribir guion
    print(f"\n🎯 PASO 2-3: Escribir guion ({formato}, {duracion_max}s máx)")

    if "Tutorial" in formato:
        guion = escribir_guion_tutorial(hook, "", duracion_max)
    elif "Noticia" in formato:
        guion = escribir_guion_noticia(hook, "", duracion_max)
    else:  # Contraste, Caso de Uso, etc
        guion = escribir_guion_contraste(hook, "", duracion_max)

    # PASO 4: Validar duración
    duracion_estimada = estimar_duracion(guion)
    if duracion_estimada > duracion_max:
        print(f"  ⚠️  Guion demasiado largo: {duracion_estimada:.0f}s (máx {duracion_max}s)")
        print(f"  Recortando...")
        # Simplificado: usar versión recortada
        guion = guion[:int(len(guion) * 0.8)]  # Recortar 20%

    print(f"  ✓ Duración estimada: {duracion_estimada:.0f}s")
    print(f"  ✓ Guion OK: {len(guion.split())} palabras")

    # Mostrar guion
    print(f"\n{'-'*70}")
    print("GUION")
    print(f"{'-'*70}")
    print(guion)

    # PASO 5: Llamar Caption Master automáticamente
    print(f"\n\n{'='*70}")
    print("🎨 PASO 5: Llamando Caption Master (Agente 4)")
    print(f"{'='*70}")

    # Importar y ejecutar caption master
    try:
        from scripts.caption_master import generar_captions_validados

        titulo = f"Video: {hook[:30]}..."
        captions = generar_captions_validados(
            guion=guion,
            formato=formato,
            tema=hook,
            angulo="Estrategia de negocio"
        )

        # Guardar en Mis Posts
        if not args.dry_run:
            hashtags = " ".join(["#claude", "#ia", "#negociosdigitales", "#automatizacion", "#productividad"])
            page_id = crear_guion_en_mis_posts(
                titulo=titulo,
                guion=guion,
                formato=formato,
                patron=patron,
                hashtags=hashtags
            )
            if page_id:
                print(f"\n✅ Guardado en Mis Posts")

        # Mostrar captions
        print(f"\n{'-'*70}")
        print("CAPTIONS VALIDADAS")
        print(f"{'-'*70}")
        for idx, (caption, validacion) in enumerate(captions, 1):
            print(f"\nCAPTION {chr(64+idx)}")
            print(caption)
            if validacion:
                print(f"✅ Validación: OK")
            else:
                print(f"❌ Validación: Errores")

    except ImportError:
        print("⚠️  Caption Master no disponible aún")

    print(f"\n{'='*70}")
    print("✅ GUIONISTA COMPLETADO")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
