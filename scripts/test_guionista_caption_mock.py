#!/usr/bin/env python3
"""
Test Mock: Guionista + Caption Master
Demuestra el flujo completo: Hook → Guion → 3 Captions validados
"""

import sys
import re

# Mock Caption Master functions
def validar_caption(caption):
    """Validador automático"""
    errores = []
    
    linea_1 = caption.split('\n')[0]
    palabras = len(linea_1.split())
    
    if palabras > 12:
        errores.append(f"❌ Primera línea: {palabras} palabras (máx 12)")
    else:
        errores.append(f"✅ Primera línea: {palabras} palabras")
    
    if '**' in caption or '__' in caption or '# ' in caption:
        errores.append("❌ Contiene markdown")
    else:
        errores.append("✅ Texto plano")
    
    if re.search(r'#\w+#\w+', caption):
        errores.append("❌ Hashtags pegados")
    else:
        errores.append("✅ Hashtags separados")
    
    cta_words = ['comenta', 'guarda', 'link', 'comparte', 'sígueme']
    if any(w in caption.lower() for w in cta_words):
        errores.append("✅ CTA presente")
    else:
        errores.append("❌ Sin CTA")
    
    hashtags = re.findall(r'#\w+', caption)
    if 5 <= len(hashtags) <= 8:
        errores.append(f"✅ Hashtags OK ({len(hashtags)})")
    else:
        errores.append(f"❌ Hashtags: {len(hashtags)} (necesita 5-8)")
    
    return errores

def main():
    print("\n" + "="*70)
    print("✍️  GUIONISTA + CAPTION MASTER — TEST MOCK")
    print("="*70)

    # PASO 1: Hook
    hook = "No hagas esto en tu negocio digital si quieres crecer"
    print(f"\n📌 HOOK INPUT")
    print(f"   \"{hook}\"")
    print(f"   ({len(hook.split())} palabras)")

    # PASO 2: Generar guion
    print(f"\n✍️  PASO 1-3: GUION (Contraste, 45s máx)")
    
    guion = """[0:00-0:03] HOOK
No hagas esto en tu negocio digital si quieres crecer

[0:03-0:08] DOLOR
La mayoría de emprendedores gasta dinero en ads sin ver resultados reales.

[0:08-0:20] SOLUCIÓN
La clave es automatizar la validación del problema antes de invertir.
Así identificas si realmente vale la pena escalar.

[0:20-0:35] RESULTADO
Con este método, reduje costos de adquisición 3x en 2 semanas.
Ahora pruebo ideas en 48 horas, no en 3 meses.

[0:35-0:45] RETENCIÓN + CTA
Si quieres reproducir esto, comenta MÉTODO abajo.
Te paso el paso a paso completo."""

    palabras = len(guion.split())
    segundos = palabras / 2.5
    print(f"   Palabras: {palabras}")
    print(f"   Duración estimada: {segundos:.0f}s (máx 45s)")
    
    if segundos <= 45:
        print(f"   ✅ Duración OK")
    else:
        print(f"   ⚠️  Demasiado largo, recortando...")
        guion = guion[:int(len(guion)*0.85)]
        segundos = len(guion.split()) / 2.5
        print(f"   ✅ Duración ajustada: {segundos:.0f}s")

    print(f"\n{'-'*70}")
    print("GUION")
    print(f"{'-'*70}")
    print(guion)

    # PASO 4: Caption Master
    print(f"\n\n🎨 PASO 4: CAPTION MASTER — 3 Versiones validadas")
    print(f"{'='*70}")

    # VERSION A - DOLOR + PROMESA
    caption_a = """No hagas esto en tu negocio digital si quieres crecer

La verdad que la mayoría gasta dinero sin resultados.

Aquí Claude hace la diferencia real.

Comenta si ya lo probaste.

#claude #ia #negociosdigitales #automatizacion #productividad"""

    # VERSION B - CURIOSITY GAP
    caption_b = """¿Por qué tus competidores venden más con IA?

No hagas esto en tu negocio digital si quieres crecer

Te lo muestro en este video.

Guarda este contenido ahora.

#ia #claudeai #ventajadigital #negociosdigitales #competencia"""

    # VERSION C - CONTRASTE
    caption_c = """Antes: sin automatización, todo manual.
Después: No hagas esto en tu negocio digital si quieres crecer

Esto cambió todo esta semana.

Link en bio para probar.

#before #after #automatizacion #ia #productividad #claudeai"""

    captions = [
        ("A — DOLOR + PROMESA", caption_a),
        ("B — CURIOSITY GAP", caption_b),
        ("C — CONTRASTE GVB", caption_c)
    ]

    for nombre, caption in captions:
        print(f"\n{'─'*70}")
        print(f"CAPTION {nombre}")
        print(f"{'─'*70}")
        print(caption)
        print()

        detalles = validar_caption(caption)
        for detalle in detalles:
            print(f"  {detalle}")

    # PASO 5: Output final
    print(f"\n{'='*70}")
    print("✅ GUION + CAPTIONS COMPLETADOS")
    print(f"{'='*70}")

    print(f"""
Formato: Contraste | Duración: 38s | Patrón GVB: 1 - Negacion Sorpresiva
Hook elegido: "No hagas esto en tu negocio digital si quieres crecer"

─────────────────────────────────────────────────────────────────────
RECOMENDACIÓN: Usar Caption A (Dolor + Promesa)
Razón: Patrón 1 (Negacion Sorpresiva) funciona mejor con dolor + promesa

✅ Guardado en Mis Posts (Estado: Pendiente grabacion)
═════════════════════════════════════════════════════════════════════
""")

if __name__ == "__main__":
    main()
