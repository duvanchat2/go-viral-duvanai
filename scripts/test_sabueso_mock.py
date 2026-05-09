#!/usr/bin/env python3
"""
Test Mock del Sabueso — Simula la ejecución con datos de prueba
Demuestra los 7 pasos del flujo sin depender de credenciales reales
"""

from datetime import date, datetime
from typing import List

class MockVideo:
    def __init__(self, title, likes, views, caption, username, tipo="Video"):
        self.title = title
        self.likes = likes
        self.views = views
        self.caption = caption
        self.username = username
        self.tipo = tipo
        self.transcript = f"Transcripción de {title}..."
        self.duration_sec = 45
        self.post_date = "2026-05-08"

# Datos mock de ejemplo — simulan lo que Apify retornaría
MOCK_VIDEOS = {
    "soyenriquerocha": [
        MockVideo(
            "No hagas esto en tu negocio digital",
            8500, 185000,
            "No hagas esto en tu negocio digital si quieres crecer rápido. Los 3 errores que cometí",
            "soyenriquerocha"
        ),
        MockVideo(
            "3x tu productividad en 1 hora",
            6200, 142000,
            "3x tu productividad en 1 hora con este método. He testado 50+ técnicas",
            "soyenriquerocha"
        ),
        MockVideo(
            "El secreto de los mejores Content Creators",
            4100, 95000,
            "Lo que nadie te dice sobre hacer viral contenido. He analizado 1000 videos",
            "soyenriquerocha"
        ),
    ],
    "byduvan_ai": [
        MockVideo(
            "Claude vs ChatGPT: El análisis definitivo",
            5800, 201000,
            "Antes usaba solo ChatGPT. Después de 2 meses con Claude, cambié de opinión",
            "byduvan_ai"
        ),
        MockVideo(
            "Acaba de cambiar todo en IA",
            7100, 156000,
            "Acaba de salir o23-preview. Esta es la primera prueba real del cambio",
            "byduvan_ai"
        ),
        MockVideo(
            "¿Qué tan bueno es realmente MCP?",
            3900, 88000,
            "¿MCP realmente cambia el juego? Después de 2 semanas testando",
            "byduvan_ai"
        ),
    ]
}

def classify_patron(caption: str) -> str:
    """Clasifica el patrón GVB"""
    text = caption.lower()

    patterns = {
        "1 - Negacion Sorpresiva": ["no hagas", "no uses", "deja de"],
        "2 - Cifra Concreta": ["3x", "50+", "1000"],
        "3 - Secreto Revelado": ["lo que nadie", "el secreto", "lo que todos"],
        "4 - Contraste": ["antes", "después", "vs"],
        "5 - Curiosidad Directa": ["¿qué", "¿cómo", "¿por qué"],
        "6 - Urgencia Novedad": ["acaba de", "esta semana", "ya cambió"],
    }

    for patron, keywords in patterns.items():
        for kw in keywords:
            if kw in text:
                return patron

    return "4 - Contraste"

def classify_tono(caption: str) -> str:
    """Clasifica el tono"""
    text = caption.lower()

    negocio = ["negocio", "crecer", "dinero", "ventas", "clientes"]
    tecnico = ["claude", "chatgpt", "mcp", "ia", "modelo", "prompt"]

    negocio_count = sum(1 for w in negocio if w in text)
    tecnico_count = sum(1 for w in tecnico if w in text)

    if negocio_count > tecnico_count:
        return "Operador de Negocio"
    elif tecnico_count > negocio_count:
        return "Tecnico IA"
    else:
        return "Mixto"

def main():
    print("\n" + "="*70)
    print("🐕 EL SABUESO — TEST MOCK CON DATOS INICIALES")
    print("="*70)

    # PASO 1
    print("\n📖 PASO 1: Leyendo URLs Monitor...")
    print("  ✓ 2 URLs pendientes encontradas")
    print("    • Competidores: soyenriquerocha")
    print("    • Referentes: byduvan_ai")

    # PASO 2-3
    print("\n🔍 PASO 2-3: Scraping con Apify + Filtrado...")

    all_videos = []
    all_like_rates = []

    for username, videos in MOCK_VIDEOS.items():
        print(f"\n  📂 Procesando: @{username}")

        for idx, video in enumerate(videos, 1):
            like_rate = (video.likes / video.views) * 100 if video.views > 0 else 0
            all_like_rates.append(like_rate)
            all_videos.append((video, like_rate))
            print(f"    [{idx}] {video.title[:40]}...")
            print(f"        Likes: {video.likes:,} | Views: {video.views:,} | Like Rate: {like_rate:.2f}%")

    # Calcular promedio y filtrar outliers
    promedio = sum(all_like_rates) / len(all_like_rates)
    threshold = max(promedio, 3.0)

    print(f"\n  📊 Estadísticas:")
    print(f"     Like rate promedio: {promedio:.2f}%")
    print(f"     Threshold outliers: {threshold:.2f}%")

    outliers = [(v, lr) for v, lr in all_videos if lr > threshold]
    print(f"  ⭐ {len(outliers)} outliers encontrados")

    # PASO 4-5
    print(f"\n✨ PASO 4-5: Clasificación GVB + Escritura en Hooks DB...")
    print(f"  📊 {len(outliers)} hooks para procesar\n")

    patron_counts = {}

    for idx, (video, like_rate) in enumerate(outliers, 1):
        patron = classify_patron(video.caption)
        tono = classify_tono(video.caption)
        hook_texto = " ".join(video.caption.split()[:12])

        patron_counts[patron] = patron_counts.get(patron, 0) + 1

        print(f"  [{idx}/{len(outliers)}] {video.title[:45]}...")
        print(f"     Like rate: {like_rate:.2f}%")
        print(f"     Patrón: {patron}")
        print(f"     Tono: {tono}")
        print(f"     Hook: \"{hook_texto}\"")
        print(f"     ✓ Guardado en Hooks DB")
        print()

    # PASO 6
    print("📝 PASO 6: Actualizando URLs Monitor...")
    print("  ✓ soyenriquerocha: Estado → Procesado")
    print("  ✓ byduvan_ai: Estado → Procesado")

    # PASO 7
    print("\n\n" + "="*70)
    print("✅ SABUESO COMPLETADO")
    print("="*70)

    print(f"\n📊 ESTADÍSTICAS:")
    print(f"  • Canales procesados: 2")
    print(f"  • Videos analizados: {len(all_videos)}")
    print(f"  • Outliers guardados: {len(outliers)}")
    print(f"  • Promedio like rate: {promedio:.1f}%")

    # Top 3
    top_3 = sorted(outliers, key=lambda x: x[1], reverse=True)[:3]
    print(f"\n⭐ TOP 3 HOOKS ESTA SEMANA:")
    for idx, (video, like_rate) in enumerate(top_3, 1):
        patron = classify_patron(video.caption)
        hook_short = " ".join(video.caption.split()[:8])
        print(f"  {idx}. \"{hook_short}...\" — {like_rate:.1f}% — {patron} — @{video.username}")

    # Patrón más frecuente
    if patron_counts:
        most_common = max(patron_counts.items(), key=lambda x: x[1])
        print(f"\n🎯 Patrón GVB más frecuente: {most_common[0]} ({most_common[1]} hooks)")

    print(f"\n→ Listo para /viral:destrip (próximo agente)\n")

    # Datos que irían a Notion
    print("\n" + "-"*70)
    print("📋 DATOS GUARDADOS EN HOOKS DB (Notion):")
    print("-"*70)

    for idx, (video, like_rate) in enumerate(outliers, 1):
        patron = classify_patron(video.caption)
        tono = classify_tono(video.caption)
        hook_texto = " ".join(video.caption.split()[:12])
        semana = date.today().isocalendar()[1]

        print(f"\n[{idx}] Hook Entry #{idx}")
        print(f"  Hook Texto: \"{hook_texto}\"")
        print(f"  Patron GVB: {patron}")
        print(f"  Tono: {tono}")
        print(f"  Like Rate: {like_rate:.2f}%")
        print(f"  Views: {video.views:,}")
        print(f"  Fuente: @{video.username}")
        print(f"  Duracion: {video.duration_sec}s")
        print(f"  Semana: {semana}")

if __name__ == "__main__":
    main()
