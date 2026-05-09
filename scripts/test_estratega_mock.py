#!/usr/bin/env python3
"""
Test Mock del Estratega — Simula generación de Brief Semanal
"""

from datetime import date
from collections import defaultdict

# Datos mock de Hooks DB (output del Sabueso)
MOCK_HOOKS = [
    {
        "texto": "No hagas esto en tu negocio digital si quieres crecer",
        "patron": "1 - Negacion Sorpresiva",
        "tono": "Operador de Negocio",
        "like_rate": 4.59,
        "views": 185000,
        "fuente": "@soyenriquerocha",
        "formato": "Contraste"
    },
    {
        "texto": "3x tu productividad en 1 hora con este método simple",
        "patron": "2 - Cifra Concreta",
        "tono": "Mixto",
        "like_rate": 4.37,
        "views": 142000,
        "fuente": "@soyenriquerocha",
        "formato": "Tutorial"
    },
    {
        "texto": "Lo que nadie te dice sobre hacer viral contenido hoy",
        "patron": "3 - Secreto Revelado",
        "tono": "Mixto",
        "like_rate": 4.32,
        "views": 95000,
        "fuente": "@soyenriquerocha",
        "formato": "Noticia"
    },
    {
        "texto": "Antes usaba solo ChatGPT después descubrí Claude AI",
        "patron": "4 - Contraste",
        "tono": "Tecnico IA",
        "like_rate": 2.89,
        "views": 201000,
        "fuente": "@byduvan_ai",
        "formato": "Contraste"
    },
    {
        "texto": "Acaba de cambiar todo en IA esta semana mismo",
        "patron": "6 - Urgencia Novedad",
        "tono": "Mixto",
        "like_rate": 4.55,
        "views": 156000,
        "fuente": "@byduvan_ai",
        "formato": "Noticia"
    },
]

# Datos mock de Mis Posts (historial propio)
MOCK_MIS_POSTS_POSITIVOS = [
    {
        "titulo": "ROI sin gastar dinero en ads",
        "like_rate": 6.2,
        "views": 125000,
        "patron": "2 - Cifra Concreta",
        "semana": 18
    }
]

MOCK_MIS_POSTS_NEGATIVOS = [
    {
        "titulo": "Deep dive en algoritmos complejos",
        "like_rate": 1.5,
        "views": 28000,
        "patron": "0 - Tecnico",
        "semana": 17
    }
]

def extract_keywords(text):
    """Extrae palabras clave"""
    business_words = {"negocio", "dinero", "ventas", "crecimiento", "productividad", "roi", "ingresos"}
    ai_words = {"ia", "claude", "chatgpt", "modelo", "prompt", "api"}

    text_lower = text.lower()
    keywords = set()

    if any(w in text_lower for w in business_words):
        keywords.add("business")
    if any(w in text_lower for w in ai_words):
        keywords.add("ia")

    return keywords

def group_hooks_by_theme(hooks):
    """Agrupa hooks por tema"""
    groups = defaultdict(list)

    for hook in hooks:
        keywords = extract_keywords(hook["texto"])

        if "business" in keywords:
            groups["business"].append(hook)
        elif "ia" in keywords:
            groups["ia"].append(hook)
        else:
            groups["growth"].append(hook)

    return dict(groups)

def calculate_score(group, positivos, negativos):
    """Calcula score para un grupo"""
    score = 0.0

    # +3 si patrón aparece 3+ veces
    patron_counts = defaultdict(int)
    for hook in group:
        patron_counts[hook["patron"]] += 1

    for count in patron_counts.values():
        if count >= 3:
            score += 3
            break

    # +2 si patrón coincide con outlier positivo
    for post in positivos:
        for hook in group:
            if post["patron"] == hook["patron"]:
                score += 2
                break

    # +2 si tono = "Operador de Negocio"
    tono_counts = defaultdict(int)
    for hook in group:
        tono_counts[hook["tono"]] += 1

    if tono_counts.get("Operador de Negocio", 0) > len(group) / 2:
        score += 2

    # +1 si like_rate promedio > 5%
    avg_like_rate = sum(h["like_rate"] for h in group) / len(group)
    if avg_like_rate > 5:
        score += 1

    # +1 si hay referente
    if any("@" in h["fuente"] for h in group):
        score += 1

    # -3 si tono Tecnico IA
    if tono_counts.get("Tecnico IA", 0) > len(group) / 2:
        score -= 3

    return score

def main():
    print("\n" + "="*70)
    print("📊 EL ESTRATEGA — TEST MOCK — Brief Semanal")
    print("="*70)

    # PASO 1
    print("\n📖 PASO 1: Leyendo Hooks DB...")
    hooks = MOCK_HOOKS
    print(f"  ✓ {len(hooks)} hooks encontrados")
    for h in hooks:
        print(f"    • \"{h['texto'][:45]}...\" — {h['patron']}")

    # PASO 2
    print("\n📚 PASO 2: Analizando historial propio...")
    positivos = MOCK_MIS_POSTS_POSITIVOS
    negativos = MOCK_MIS_POSTS_NEGATIVOS
    print(f"  ✓ Outliers positivos (like_rate > 5%): {len(positivos)}")
    for p in positivos:
        print(f"    ✅ {p['titulo']} — {p['like_rate']:.1f}%")
    print(f"  ✓ Outliers negativos: {len(negativos)}")
    for n in negativos:
        print(f"    ❌ {n['titulo']} — {n['like_rate']:.1f}%")

    # PASO 3
    print("\n📊 PASO 3: Calculando scores temáticos...")
    grupos = group_hooks_by_theme(hooks)

    temas = []
    for grupo_name, group_hooks in grupos.items():
        score = calculate_score(group_hooks, positivos, negativos)
        temas.append({
            "nombre": grupo_name,
            "hooks": group_hooks,
            "score": score
        })
        print(f"  • {grupo_name}: score {score:.1f} ({len(group_hooks)} hooks)")

    # PASO 4
    print("\n🎯 PASO 4: Seleccionando top 3 temas...")
    temas_sorted = sorted(temas, key=lambda t: t["score"], reverse=True)

    # Tema descriptions
    tema_names = {
        "business": ("Estrategia de Negocio", "Cómo crecer y escalar tu negocio digital"),
        "ia": ("Herramientas IA", "Cómo usar IA para automatizar procesos"),
        "growth": ("Growth Hacking", "Tácticas para crecer 10x tu audiencia")
    }

    temas_top3 = []
    for idx, tema in enumerate(temas_sorted[:3], 1):
        nombre, desc = tema_names.get(tema["nombre"], ("Tema", "Descripción"))

        # Hook sugerido
        best_hook = max(tema["hooks"], key=lambda h: h["like_rate"])
        hook_words = best_hook["texto"].split()[:12]
        hook_sugerido = " ".join(hook_words)

        # Patrón más frecuente
        patron_counts = defaultdict(int)
        for h in tema["hooks"]:
            patron_counts[h["patron"]] += 1
        patron = max(patron_counts.items(), key=lambda x: x[1])[0]

        # Formato más común
        formato_counts = defaultdict(int)
        for h in tema["hooks"]:
            formato_counts[h["formato"]] += 1
        formato = max(formato_counts.items(), key=lambda x: x[1])[0]

        temas_top3.append({
            "nombre": nombre,
            "description": desc,
            "angulo": f"Insights validados por {len(tema['hooks'])} hooks de referentes",
            "formato": formato,
            "duracion": 60,
            "patron": patron,
            "hook": hook_sugerido,
            "score": tema["score"]
        })

    # PASO 5 (simulado)
    print("\n✍️  PASO 5: Escribiendo Brief Semanal...")
    semana = date.today().isocalendar()[1]
    hoje = date.today().isoformat()
    print(f"  ✓ Brief creado: Brief Semana {semana} — {hoje}")

    # PASO 6
    print("\n\n" + "="*70)
    print(f"✅ ESTRATEGA COMPLETADO — BRIEF SEMANA {semana}")
    print("="*70)

    for idx, tema in enumerate(temas_top3, 1):
        suffix = " ⭐" if idx == 1 else ""
        print(f"\nTEMA {idx}{suffix} (score: {tema['score']:.1f})")
        print(f"Tema: {tema['description']}")
        print(f"Ángulo: {tema['angulo']}")
        print(f"Formato: {tema['formato']} — {tema['duracion']} seg")
        print(f"Patrón GVB: {tema['patron']}")
        print(f"Hook: \"{tema['hook']}\"")
        print(f"Por qué: Like rate validado en competidores")

    print(f"\n📈 APRENDIZAJE SEMANA:")
    if positivos:
        print(f"✅ Funcionó: {positivos[0]['titulo']} ({positivos[0]['like_rate']:.1f}%) — {positivos[0]['patron']}")
    if negativos:
        print(f"❌ No funcionó: {negativos[0]['titulo']} ({negativos[0]['like_rate']:.1f}%) — demasiado técnico")

    print(f"\n→ Próximo: /viral:script \"{temas_top3[0]['hook']}\"\n")

    # Datos que irían a Brief Semanal
    print("-"*70)
    print(f"📋 DATOS GUARDADOS EN BRIEF SEMANAL (Notion):")
    print("-"*70)
    print(f"\nTítulo: Brief Semana {semana} — {hoje}")
    print(f"Semana: {semana}")
    print(f"Fecha: {hoje}")
    print(f"\nTema 1 Hook: \"{temas_top3[0]['hook']}\"")
    print(f"Tema 1 Formato: {temas_top3[0]['formato']}")
    print(f"Tema 1 Patron GVB: {temas_top3[0]['patron']}")

    if len(temas_top3) > 1:
        print(f"\nTema 2 Hook: \"{temas_top3[1]['hook']}\"")
        print(f"Tema 2 Formato: {temas_top3[1]['formato']}")

    if len(temas_top3) > 2:
        print(f"\nTema 3 Hook: \"{temas_top3[2]['hook']}\"")

    print(f"\nFunciono esta semana: {positivos[0]['titulo']} con patrón {positivos[0]['patron']}")
    print(f"No funciono esta semana: {negativos[0]['titulo']} — demasiado técnico, bajo engagement")
    print(f"Estado: Pendiente")

if __name__ == "__main__":
    main()
