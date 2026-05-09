#!/usr/bin/env python3
"""
El Caption Master — Agent 4: 3 Captions Validados
Genera y valida captions — rechaza si no cumple requisitos
CRÍTICO: Los últimos 2 videos fallaron aquí
"""

import re
from typing import List, Tuple

# Hashtags base
HASHTAGS_FIJOS = ["#claude", "#ia", "#negociosdigitales"]
HASHTAGS_POOL = [
    "#automatizacion", "#inteligenciaartificial", "#agentesIA",
    "#marketingdigital", "#emprendimiento", "#productividad",
    "#herramientasIA", "#claudeai", "#trabajoconIA"
]

def validar_caption(caption: str) -> Tuple[bool, List[str]]:
    """
    Validador automático — rechaza si no cumple requisitos
    Retorna (es_válido, lista_de_errores)
    """
    errores = []

    lineas = caption.split('\n')
    if not lineas:
        return False, ["Caption vacío"]

    linea_1 = lineas[0]
    palabras_linea_1 = len(linea_1.split())

    # ERROR 1: Primera línea > 12 palabras
    if palabras_linea_1 > 12:
        errores.append(
            f"❌ Primera línea tiene {palabras_linea_1} palabras (máx 12)"
        )

    # ERROR 2: Contiene markdown
    markdown_chars = ['**', '__', '* ', '- ', '# ', '```']
    if any(c in caption for c in markdown_chars):
        errores.append("❌ Caption contiene markdown — texto plano obligatorio")

    # ERROR 3: Hashtags pegados
    if re.search(r'#\w+#\w+', caption):
        errores.append("❌ Hashtags pegados sin espacio — separar con espacio")

    # ERROR 4: Descripción del video (palabras prohibidas)
    PALABRAS_PROHIBIDAS = [
        'en este video', 'en este reel', 'hoy te muestro',
        'hoy vamos a', 'en este tutorial', 'aprende cómo',
        'te explico', 'te cuento', 'en el siguiente video',
        'en el video', 'en el reel'
    ]
    for palabra in PALABRAS_PROHIBIDAS:
        if palabra.lower() in caption.lower():
            errores.append(
                f"❌ Caption descriptiva detectada: '{palabra}' — remove"
            )

    # ERROR 5: Sin CTA
    PALABRAS_CTA = [
        'comenta', 'link en bio', 'skool', 'guarda',
        'comparte', 'sígueme', 'click', 'activa notificaciones'
    ]
    if not any(p in caption.lower() for p in PALABRAS_CTA):
        errores.append("❌ Sin CTA — agregar: comenta, guarda, link en bio, etc.")

    # ERROR 6: Validar hashtags
    hashtags = re.findall(r'#\w+', caption)

    if len(hashtags) == 0:
        errores.append("❌ Sin hashtags — usar 5-8")
    elif len(hashtags) < 5:
        errores.append(f"❌ Solo {len(hashtags)} hashtags — usar 5-8")
    elif len(hashtags) > 8:
        errores.append(f"❌ {len(hashtags)} hashtags — máximo 8")

    es_valido = len(errores) == 0

    if es_valido:
        return True, [
            f"✅ {palabras_linea_1} palabras línea 1",
            f"✅ Texto plano (sin markdown)",
            f"✅ Hashtags OK ({len(hashtags)} total)",
            f"✅ CTA presente"
        ]
    else:
        return False, errores

def generar_caption_a(hook: str, tema: str) -> str:
    """VERSION A — DOLOR + PROMESA"""
    caption = f"""{hook}

La verdad es que la mayoría gasta dinero sin ver resultados reales.

Aquí es donde Claude cambia el juego.

Comenta si ya lo probaste.

#claude #ia #negociosdigitales #automatizacion #productividad"""

    return caption

def generar_caption_b(hook: str, tema: str) -> str:
    """VERSION B — CURIOSITY GAP"""
    caption = f"""¿Por qué tus competidores venden más con IA?

{hook}

Te lo muestro en este video.

Guarda este contenido.

#ia #competencia #claudeai #ventajadigital #negociosdigitales"""

    return caption

def generar_caption_c(hook: str, tema: str) -> str:
    """VERSION C — CONTRASTE GVB"""
    caption = f"""Antes: sin automatización, todo manual.
Después: {hook}

Esto cambió todo esta semana.

Link en bio para probar.

#before #after #automatizacion #ia #productividad #claudeai"""

    return caption

def generar_captions_validados(
    guion: str,
    formato: str,
    tema: str,
    angulo: str
) -> List[Tuple[str, bool]]:
    """
    Genera 3 versiones y valida cada una
    Retorna lista de (caption_texto, es_valido)
    """
    # Extraer hook del guion (primera línea después de [0:00-0:03])
    lineas = guion.split('\n')
    hook = ""
    for linea in lineas:
        if linea and not linea.startswith('['):
            hook = linea.strip()
            break

    if not hook or hook.startswith('['):
        hook = "Cambia tu negocio digital hoy"

    # Generar 3 versiones
    captions = []

    # VERSION A
    caption_a = generar_caption_a(hook, tema)
    es_valido_a, _ = validar_caption(caption_a)
    captions.append((caption_a, es_valido_a))

    # VERSION B
    caption_b = generar_caption_b(hook, tema)
    es_valido_b, _ = validar_caption(caption_b)
    captions.append((caption_b, es_valido_b))

    # VERSION C
    caption_c = generar_caption_c(hook, tema)
    es_valido_c, _ = validar_caption(caption_c)
    captions.append((caption_c, es_valido_c))

    return captions

def validar_y_reportar(captions: List[Tuple[str, bool]]) -> List[Tuple[str, List[str]]]:
    """
    Valida cada caption y retorna (texto, lista_validaciones)
    """
    resultados = []

    for idx, (caption, _) in enumerate(captions):
        es_valido, detalles = validar_caption(caption)
        resultados.append((caption, detalles))

    return resultados

def main():
    """Test del Caption Master"""
    print("\n" + "="*70)
    print("🎨 CAPTION MASTER — Test Mock")
    print("="*70)

    guion_mock = """[0:00-0:03] HOOK
No hagas esto en tu negocio digital si quieres crecer

[0:03-0:08] DOLOR
La mayoría gasta dinero sin ver resultados reales.

[0:08-0:20] SOLUCIÓN
Automatiza el proceso antes de invertir.

[0:20-0:35] RESULTADO
Reduje costos 3x en 2 semanas.

[0:35-0:45] CTA
Comenta MÉTODO y te paso el paso a paso."""

    print("\n📄 GUION INPUT:")
    print(guion_mock)

    # Generar captions
    captions = generar_captions_validados(
        guion=guion_mock,
        formato="Contraste",
        tema="Negocio Digital",
        angulo="Automatización"
    )

    # Validar
    print("\n" + "="*70)
    print("CAPTIONS VALIDADAS")
    print("="*70)

    letras = ['A', 'B', 'C']
    for idx, (caption, es_valido) in enumerate(captions):
        es_valido_check, detalles = validar_caption(caption)

        print(f"\n{'─'*70}")
        print(f"CAPTION {letras[idx]}")
        print(f"{'─'*70}")
        print(caption)
        print()

        for detalle in detalles:
            print(f"  {detalle}")

    # Resumen
    validos = sum(1 for _, es_valido in captions if es_valido)
    print(f"\n{'='*70}")
    print(f"📊 RESUMEN: {validos}/3 captions válidos")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
