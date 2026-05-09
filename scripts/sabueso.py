#!/usr/bin/env python3
"""
El Sabueso — Agent 1: Content Hunter
Lee URLs Monitor → Scraping Apify → Clasificación GVB → Hooks DB
"""

import os
import json
import sys
import time
import re
from datetime import datetime, date
from typing import List, Dict, Optional
from dataclasses import dataclass
import argparse

import requests
from dotenv import load_dotenv

load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

if not NOTION_API_KEY or not APIFY_API_TOKEN:
    print("❌ Faltan variables de entorno: NOTION_API_KEY, APIFY_API_TOKEN")
    sys.exit(1)

# Notion bases
URLS_MONITOR_DS = "01901dbf-447d-4425-a06d-a042ec223e7c"
HOOKS_DB_DS = "ec06af9a-f1fb-4fd0-83f0-1cdf9fe941a5"

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

@dataclass
class VideoData:
    """Estructura de datos de un video procesado"""
    title: str
    url: str
    likes: int
    views: int
    caption: str
    transcript: str = ""
    duration_sec: int = 0
    post_date: str = ""
    username: str = ""
    tipo: str = "Video"  # Canal o Video
    lista: str = ""  # Competidores, Referentes, Viral/Explorar

def notion_query(database_id: str, filter_dict: Optional[Dict] = None) -> List[Dict]:
    """Consultar Notion database con filtro"""
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    payload = {"filter": filter_dict} if filter_dict else {}

    try:
        resp = requests.post(url, headers=NOTION_HEADERS, json=payload)
        resp.raise_for_status()
        return resp.json()["results"]
    except Exception as e:
        print(f"❌ Error Notion query: {e}")
        return []

def get_pending_urls() -> Dict[str, List[Dict]]:
    """Lee URLs Monitor, agrupa por Lista"""
    filter_dict = {
        "property": "Estado",
        "select": {"equals": "Pendiente"}
    }

    rows = notion_query(URLS_MONITOR_DS, filter_dict)
    grouped = {"Competidores": [], "Referentes": [], "Viral/Explorar": []}

    for row in rows:
        props = row["properties"]
        try:
            lista = props["Lista"]["select"]["name"]
            tipo = props["Tipo"]["select"]["name"]
            url = props.get("userDefined:URL", {}).get("url", "")
            nombre = props["Nombre"]["title"][0]["plain_text"] if props["Nombre"]["title"] else ""

            if lista in grouped and url:
                grouped[lista].append({
                    "id": row["id"],
                    "nombre": nombre,
                    "url": url,
                    "tipo": tipo,
                    "lista": lista
                })
        except (KeyError, IndexError, TypeError) as e:
            print(f"⚠️  Error parseando fila: {e}")

    return grouped

def extract_username(url: str) -> str:
    """Extrae username de URL de Instagram"""
    # instagram.com/usuario → usuario
    match = re.search(r"instagram\.com/([a-zA-Z0-9_.]+)", url)
    if match:
        return match.group(1).rstrip("/")
    return ""

def call_apify_actor(actor_id: str, input_dict: Dict) -> Optional[str]:
    """Crea run en Apify, polling hasta SUCCEEDED, retorna dataset ID"""
    url = f"https://api.apify.com/v2/acts/{actor_id}/runs"
    headers = {"Authorization": f"Bearer {APIFY_API_TOKEN}"}

    try:
        resp = requests.post(url, headers=headers, json=input_dict)
        resp.raise_for_status()
        run_id = resp.json()["data"]["id"]
        print(f"  📡 Apify run iniciado: {run_id}")

        # Polling
        for attempt in range(120):  # 10 minutos max
            check_url = f"https://api.apify.com/v2/acts/{actor_id}/runs/{run_id}"
            check_resp = requests.get(check_url, headers=headers)
            check_resp.raise_for_status()

            status = check_resp.json()["data"]["status"]
            if status == "SUCCEEDED":
                dataset_id = check_resp.json()["data"]["defaultDatasetId"]
                print(f"  ✓ Completado: {dataset_id}")
                return dataset_id
            elif status in ["FAILED", "ABORTED"]:
                print(f"  ❌ Run falló: {status}")
                return None

            time.sleep(5)

        print(f"  ⏱️  Timeout esperando Apify")
        return None
    except Exception as e:
        print(f"  ❌ Error Apify: {e}")
        return None

def get_apify_dataset(dataset_id: str) -> List[Dict]:
    """Lee items del dataset de Apify"""
    url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
    headers = {"Authorization": f"Bearer {APIFY_API_TOKEN}"}

    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"  ❌ Error reading Apify dataset: {e}")
        return []

def process_canal(nombre: str, url: str) -> List[VideoData]:
    """Procesa Canal (Competidores/Referentes) con transcript extractor"""
    username = extract_username(url)
    if not username:
        print(f"  ⚠️  No se pudo extraer username de {url}")
        return []

    print(f"  🔍 Procesando canal: @{username}")

    input_dict = {
        "channelUsername": username,
        "reelCount": 10
    }

    dataset_id = call_apify_actor("sian.agency/instagram-ai-transcript-extractor", input_dict)
    if not dataset_id:
        return []

    items = get_apify_dataset(dataset_id)
    videos = []

    for item in items:
        try:
            video = VideoData(
                title=item.get("caption", "")[:80],
                url=f"https://instagram.com/reel/{item.get('shortcode', '')}/" if item.get('shortcode') else url,
                likes=int(item.get("likes", 0)),
                views=int(item.get("views", item.get("likes", 0))),  # fallback
                caption=item.get("caption", ""),
                transcript=item.get("transcript", "")[:250],
                duration_sec=int(item.get("videoDurationSeconds", 0)),
                post_date=item.get("timestamp", "")[:10],
                username=username,
                tipo="Canal",
                lista="Competidores" if "Competidor" in nombre else "Referentes"
            )
            videos.append(video)
        except Exception as e:
            print(f"    ⚠️  Error parseando item: {e}")

    print(f"  ✓ {len(videos)} videos extraídos de @{username}")
    return videos

def process_video(url: str, lista: str) -> List[VideoData]:
    """Procesa Video (Viral/Explorar) con instagram-scraper"""
    print(f"  🔍 Procesando video: {url}")

    input_dict = {
        "directUrls": [url],
        "resultsType": "posts",
        "resultsLimit": 10
    }

    dataset_id = call_apify_actor("apify/instagram-scraper", input_dict)
    if not dataset_id:
        return []

    items = get_apify_dataset(dataset_id)
    videos = []

    for item in items:
        try:
            video = VideoData(
                title=item.get("caption", "")[:80],
                url=item.get("url", url),
                likes=int(item.get("likes", 0)),
                views=int(item.get("views", item.get("likes", 0))),
                caption=item.get("caption", ""),
                transcript="",
                duration_sec=int(item.get("videoDurationSeconds", 0)),
                post_date=item.get("timestamp", "")[:10],
                username=extract_username(item.get("url", "")),
                tipo="Video",
                lista=lista
            )
            videos.append(video)
        except Exception as e:
            print(f"    ⚠️  Error parseando item: {e}")

    print(f"  ✓ {len(videos)} videos extraídos")
    return videos

def calculate_like_rate(video: VideoData) -> float:
    """Calcula like rate"""
    if video.views == 0:
        return 0.0
    return (video.likes / video.views) * 100

def filter_outliers(videos: List[VideoData]) -> List[VideoData]:
    """Filtra outliers: like_rate > max(promedio, 3.0)"""
    if not videos:
        return []

    like_rates = [calculate_like_rate(v) for v in videos]
    promedio = sum(like_rates) / len(like_rates)
    threshold = max(promedio, 3.0)

    outliers = [v for v in videos if calculate_like_rate(v) > threshold]

    print(f"  📊 Like rate promedio: {promedio:.1f}%")
    print(f"  🎯 Threshold: {threshold:.1f}%")
    print(f"  ⭐ {len(outliers)} outliers encontrados")

    return outliers

def classify_patron_gbv(caption: str) -> str:
    """Clasifica primer patrón GVB según primeras 12 palabras"""
    words = caption.split()[:12]
    text = " ".join(words).lower()

    # Patrones
    patterns = {
        "1 - Negacion Sorpresiva": ["no hagas", "deja de", "no uses", "no debes", "nunca"],
        "2 - Cifra Concreta": [r"\d+\s*\w+", "3x", "10x", "100%", "aumentó"],
        "3 - Secreto Revelado": ["lo que nadie", "por esto", "el secreto", "lo que todos"],
        "4 - Contraste": ["antes", "después", "vs", "versus", "en lugar de"],
        "5 - Curiosidad Directa": ["¿", "cómo", "qué", "por qué", "sé que"],
        "6 - Urgencia Novedad": ["acaba de", "esta semana", "ya cambió", "ahora", "recién"],
    }

    for patron, keywords in patterns.items():
        for keyword in keywords:
            if keyword.lower() in text:
                return patron

    return "4 - Contraste"  # Default

def classify_tono(caption: str, transcript: str = "") -> str:
    """Clasifica tono: Operador de Negocio, Tecnico IA, Mixto"""
    full_text = (caption + " " + transcript).lower()

    negocio_words = ["cliente", "venta", "tiempo", "dinero", "ingresos", "profit", "costo", "roi"]
    tecnico_words = ["modelo", "prompt", "parámetro", "api", "código", "función", "algoritmo", "red neuronal"]

    negocio_count = sum(1 for w in negocio_words if w in full_text)
    tecnico_count = sum(1 for w in tecnico_words if w in full_text)

    if negocio_count > tecnico_count:
        return "Operador de Negocio"
    elif tecnico_count > negocio_count:
        return "Tecnico IA"
    else:
        return "Mixto"

def detect_formato(caption: str) -> str:
    """Detecta formato del contenido"""
    text = caption.lower()

    if "tier" in text or "ranking" in text:
        return "Tier List"
    elif "tutorial" in text or "cómo" in text or "paso" in text:
        return "Tutorial"
    elif "noticia" in text or "breaking" in text or "nuevo" in text:
        return "Noticia"
    elif "antes" in text and "después" in text:
        return "Contraste"
    elif "caso" in text or "ejemplo" in text:
        return "Caso de Uso"
    elif "vs" in text or "versus" in text:
        return "Comparativa"

    return "Contraste"  # Default

def create_hook_page(video: VideoData) -> Optional[str]:
    """Crea página en Hooks DB. Retorna page ID si éxito"""
    like_rate = calculate_like_rate(video)
    patron = classify_patron_gbv(video.caption)
    tono = classify_tono(video.caption, video.transcript)
    formato = detect_formato(video.caption)

    # Primeras 12 palabras del caption
    hook_texto = " ".join(video.caption.split()[:12])

    # Primeras 15 palabras de transcripción
    transcript_hook = " ".join(video.transcript.split()[:15]) if video.transcript else ""

    # Semana actual
    today = date.today()
    semana = today.isocalendar()[1]

    properties = {
        "Hook Texto": {
            "title": [{"text": {"content": hook_texto[:100]}}]
        },
        "Transcript Hook": {
            "rich_text": [{"text": {"content": transcript_hook}}]
        },
        "Patron GVB": {
            "select": {"name": patron}
        },
        "Formato": {
            "select": {"name": formato}
        },
        "Like Rate": {
            "number": round(like_rate, 2)
        },
        "Views": {
            "number": video.views
        },
        "Fuente": {
            "rich_text": [{"text": {"content": f"@{video.username}"}}]
        },
        "Duracion seg": {
            "number": video.duration_sec
        },
        "Fecha Post": {
            "date": {"start": video.post_date} if video.post_date else None
        },
        "Semana": {
            "number": semana
        },
        "Tono": {
            "select": {"name": tono}
        }
    }

    # Limpiar Nones
    properties = {k: v for k, v in properties.items() if v.get("date") or k != "Fecha Post"}

    url = f"https://api.notion.com/v1/pages"
    payload = {
        "parent": {"database_id": HOOKS_DB_DS},
        "properties": properties
    }

    try:
        resp = requests.post(url, headers=NOTION_HEADERS, json=payload)
        resp.raise_for_status()
        page_id = resp.json()["id"]
        return page_id
    except Exception as e:
        print(f"    ❌ Error creando page en Hooks DB: {e}")
        return None

def update_urls_monitor_estado(notion_id: str, estado: str, notas: str = "") -> bool:
    """Actualiza Estado en URLs Monitor"""
    url = f"https://api.notion.com/v1/pages/{notion_id}"

    properties = {
        "Estado": {
            "select": {"name": estado}
        }
    }

    if notas:
        properties["Notas"] = {
            "rich_text": [{"text": {"content": notas}}]
        }

    payload = {"properties": properties}

    try:
        resp = requests.patch(url, headers=NOTION_HEADERS, json=payload)
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"    ❌ Error actualizando URLs Monitor: {e}")
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Re-procesar todo")
    parser.add_argument("--source", choices=["competidores", "referentes", "viral"], help="Procesar solo una fuente")
    parser.add_argument("--limit", type=int, default=10, help="Max videos por categoría")
    parser.add_argument("--dry-run", action="store_true", help="Mostrar qué haría sin escribir")
    args = parser.parse_args()

    print("\n" + "="*60)
    print("🐕 EL SABUESO — Iniciando Content Hunt")
    print("="*60)

    # PASO 1: Leer URLs Monitor
    print("\n📖 PASO 1: Leyendo URLs Monitor...")
    grouped = get_pending_urls()

    total_urls = sum(len(v) for v in grouped.values())
    print(f"  ✓ {total_urls} URLs pendientes encontradas")
    for lista, urls in grouped.items():
        if urls:
            print(f"    • {lista}: {len(urls)} URLs")

    if total_urls == 0:
        print("\n  ⚠️  Sin URLs pendientes. Ejecuta nuevamente después de agregar.")
        return

    # PASO 2-3: Scraping + Análisis
    print("\n🔍 PASO 2-3: Scraping con Apify + Filtrado...")
    all_videos = []
    processed_urls = {}

    for lista, urls in grouped.items():
        if args.source and lista.lower() != args.source:
            continue

        if not urls:
            continue

        print(f"\n  📂 {lista}:")

        for idx, url_data in enumerate(urls[:args.limit], 1):
            print(f"\n  [{idx}/{len(urls)}] {url_data['nombre']}")

            if url_data["tipo"] == "Canal":
                videos = process_canal(url_data["nombre"], url_data["url"])
            else:
                videos = process_video(url_data["url"], lista)

            # Filtrar outliers
            outliers = filter_outliers(videos)

            all_videos.extend(outliers)
            processed_urls[url_data["id"]] = {
                "total": len(videos),
                "outliers": len(outliers),
                "error": False
            }

            time.sleep(2)  # Rate limiting

    if not all_videos:
        print("\n  ⚠️  Sin videos/outliers encontrados.")
        return

    print(f"\n\n✨ PASO 4-5: Clasificación GVB + Escritura en Hooks DB...")
    print(f"  📊 {len(all_videos)} outliers para procesar")

    hooks_created = 0
    patron_counts = {}
    like_rates = []

    for idx, video in enumerate(all_videos, 1):
        like_rate = calculate_like_rate(video)
        like_rates.append(like_rate)
        patron = classify_patron_gbv(video.caption)

        patron_counts[patron] = patron_counts.get(patron, 0) + 1

        print(f"\n  [{idx}/{len(all_videos)}] {video.title[:40]}...")
        print(f"     Like rate: {like_rate:.1f}% | Patrón: {patron}")

        if not args.dry_run:
            page_id = create_hook_page(video)
            if page_id:
                print(f"     ✓ Guardado en Hooks DB")
                hooks_created += 1

    # PASO 6: Actualizar URLs Monitor
    print(f"\n\n📝 PASO 6: Actualizando URLs Monitor...")
    for notion_id, result in processed_urls.items():
        if not args.dry_run:
            update_urls_monitor_estado(notion_id, "Procesado")
            print(f"  ✓ {notion_id}: Estado → Procesado")

    # PASO 7: Output
    print("\n\n" + "="*60)
    print("✅ SABUESO COMPLETADO")
    print("="*60)

    avg_like_rate = sum(like_rates) / len(like_rates) if like_rates else 0
    print(f"\n📊 ESTADÍSTICAS:")
    print(f"  • Canales procesados: {sum(1 for k, v in processed_urls.items())}")
    print(f"  • Videos analizados: {sum(r['total'] for r in processed_urls.values())}")
    print(f"  • Outliers guardados: {hooks_created}")
    print(f"  • Promedio like rate: {avg_like_rate:.1f}%")

    if all_videos:
        top_3 = sorted(all_videos, key=lambda v: calculate_like_rate(v), reverse=True)[:3]
        print(f"\n⭐ TOP 3 HOOKS ESTA SEMANA:")
        for idx, video in enumerate(top_3, 1):
            print(f"  {idx}. \"{video.title[:50]}\" — {calculate_like_rate(video):.1f}% — {classify_patron_gbv(video.caption)} — @{video.username}")

    if patron_counts:
        most_common = max(patron_counts.items(), key=lambda x: x[1])
        print(f"\n🎯 Patrón GVB más frecuente: {most_common[0]} ({most_common[1]} hooks)")

    print(f"\n→ Listo para /viral:destrip (próximo agente)\n")

if __name__ == "__main__":
    main()
