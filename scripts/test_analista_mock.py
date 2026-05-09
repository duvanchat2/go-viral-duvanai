#!/usr/bin/env python3
"""
Test Mock del Analista — Simula análisis de posts publicados
"""

from collections import defaultdict

# Datos mock de Mis Posts publicados (semana anterior)
MOCK_MIS_POSTS_PUBLICADOS = [
    {
        "titulo": "No hagas esto en tu negocio digital",
        "likes": 9100,
        "views": 185000,
        "patron": "1 - Negacion Sorpresiva",
        "formato": "Contraste",
        "caption": "No hagas esto en tu negocio digital si quieres crecer\n\nLa verdad es que la mayoría gasta dinero sin ver resultados reales.\n\nAquí es donde Claude cambia el juego.\n\nComenta si ya lo probaste.",
        "semana": 18,
        "fuente": "@byduvan_ai"
    },
    {
        "titulo": "3x tu productividad en 1 hora",
        "likes": 4970,
        "views": 142000,
        "patron": "2 - Cifra Concreta",
        "formato": "Tutorial",
        "caption": "3x tu productividad en 1 hora con este método\n\nEn este video te muestro paso a paso cómo automatizar tareas repetitivas.\n\nGuarda este video.\n\n#ia #productividad",
        "semana": 18,
        "fuente": "@byduvan_ai"
    },
    {
        "titulo": "Lo que nadie te dice sobre contenido viral",
        "likes": 300,
        "views": 25000,
        "patron": "3 - Secreto Revelado",
        "formato": "Noticia",
        "caption": "En este reel te cuento lo que nadie sabe.\n\nAprende cómo los creadores top hacen viral su contenido.\n\nTe explico en el siguiente video.",
        "semana": 18,
        "fuente": "@byduvan_ai"
    }
]

def calcular_like_rate(likes, views):
    """Calcula like rate"""
    return (likes / views) * 100 if views > 0 else 0

def clasificar_rendimiento(like_rate, views):
    """Clasifica rendimiento en 3 categorías"""
    if like_rate >= 5:
        return "OUTLIER_POSITIVO"
    elif like_rate >= 3:
        return "NORMAL"
    elif like_rate < 2 or views < 50:
        return "FALLIDO"
    else:
        return "NORMAL"

def detectar_causa(post):
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

def main():
    print("\n" + "="*70)
    print("📊 EL ANALISTA — TEST MOCK — Análisis Semana 18")
    print("="*70)

    # PASO 1: Leer posts publicados
    print("\n📖 PASO 1: Leyendo Mis Posts publicados (semana 18)...")
    posts = MOCK_MIS_POSTS_PUBLICADOS
    print(f"  ✓ {len(posts)} posts encontrados")

    # PASO 2: Calcular métricas
    print("\n📊 PASO 2: Calculando métricas reales...")

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
    print("\n🔍 PASO 3: Detectando causas en posts fallidos...")
    for post in posts_fallidos:
        causas = detectar_causa(post)
        post["causas"] = causas
        print(f"  ❌ {post['titulo']}")
        for causa in causas:
            print(f"     • {causa}")

    # PASO 4-5: Resumen para Brief y Hooks
    print("\n" + "="*70)
    print("✅ ANALISTA — SEMANA 18")
    print("="*70)

    print(f"\nPOSTS ANALIZADOS: {len(posts)}\n")

    if outliers_positivos:
        print("OUTLIERS POSITIVOS ✅")
        for post in outliers_positivos:
            print(f"  ✅ \"{post['titulo'][:40]}...\" — {post['like_rate_real']:.1f}% — Patrón {post['patron']}")
            print(f"     Aprendizaje: Patrón funciona + tono directo sin descriptiva")

    if posts_normales:
        print("\nPOSTS NORMALES ➡️")
        for post in posts_normales:
            print(f"  ➡️  \"{post['titulo'][:40]}...\" — {post['like_rate_real']:.1f}%")

    if posts_fallidos:
        print("\nPOSTS FALLIDOS ❌")
        for post in posts_fallidos:
            print(f"  ❌ \"{post['titulo'][:40]}...\" — {post['like_rate_real']:.1f}%")
            print(f"     Causas: {', '.join(post['causas'])}")
            print(f"     Acción: Evitar captions descriptivas y asegurar hook fuerte en primeras líneas")

    # PASO 6: Impacto en scoring
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

    for patron, impacto in patrones_impacto.items():
        if impacto["positivo"] > 0:
            print(f"\n  {patron} ↑ (funcionó {impacto['positivo']}x — bonus +2 en próximo Estratega)")
        if impacto["fallido"] > 0:
            print(f"  {patron} ↓ (falló {impacto['fallido']}x — penalización -1 en próximo Estratega)")

    # Datos para actualizar Brief
    print("\n" + "="*70)
    print("DATOS PARA ACTUALIZAR BRIEF SEMANA 18")
    print("="*70)

    if outliers_positivos:
        funciono = outliers_positivos[0]
        print(f"\nFunciono esta semana:")
        print(f"  \"{funciono['titulo']}\" — {funciono['like_rate_real']:.1f}% — {funciono['patron']}")

    if posts_fallidos:
        no_funciono = posts_fallidos[0]
        print(f"\nNo funciono esta semana:")
        print(f"  \"{no_funciono['titulo']}\" — {no_funciono['like_rate_real']:.1f}% — {', '.join(no_funciono['causas'])}")

    print(f"\nEstado: Completado\n")

if __name__ == "__main__":
    main()
