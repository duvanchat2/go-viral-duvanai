# /viral:caption — El Caption Master (Validado)

Agente 4 del sistema go-viral: Genera y valida 3 versiones de caption optimizadas, rechaza antes de entregar si no cumple requisitos.

**CRÍTICO:** Este es el agente más delicado. Los últimos 2 videos fallaron aquí, no en el guion.

**Flow:** Guion → 3 Versiones → Validador automático → Hashtags → Mis Posts

---

## EJECUCIÓN

Este agente se llama **automáticamente** desde el Guionista. No ejecutar directamente.

```bash
# (Llamado automáticamente desde guionista.py)
# Para testing:
python3 scripts/caption_master.py --test
```

---

## PASOS DEL FLUJO

### PASO 1: Generar 3 Versiones de Caption

#### VERSION A — DOLOR + PROMESA

```
Línea 1: dolor conocido en ≤12 palabras
Línea 2: la promesa concreta
Línea 3: CTA

#hashtag1 #hashtag2 #hashtag3 #hashtag4 #hashtag5
```

**Ejemplo:**
```
¿Gastazo en ads sin convertir?

En Claude encontré el atajo para ROI real.

Comenta si ya lo probaste.

#claude #ia #negociosdigitales #automatizacion #marketingdigital
```

#### VERSION B — CURIOSITY GAP

```
Línea 1: pregunta que el target quiere responder, ≤12 palabras
Línea 2: promesa de que el video lo responde
Línea 3: CTA

#hashtags
```

**Ejemplo:**
```
¿Por qué tus competidores venden más con IA?

Te lo muestro en 30 segundos.

Guarda este video.

#ia #competencia #ventajadigital #claudeai #negocios
```

#### VERSION C — CONTRASTE GVB

```
Línea 1: estado actual con dolor → estado deseado, ≤12 palabras
Línea 2: cómo/cuándo
Línea 3: CTA

#hashtags
```

**Ejemplo:**
```
Antes: clientes perdidos en el proceso.
Ahora: conversión automática con Claude.

Esto cambió todo esta semana.

Link en bio para probar.

#before #after #automatizacion #ia #productividad
```

---

### PASO 2: Validador Automático (RECHAZA antes de entregar)

```python
def validar_caption(caption: str) -> list[str]:
    errores = []
    
    # ERROR 1: Primera línea > 12 palabras
    linea_1 = caption.split('\n')[0]
    palabras_linea_1 = len(linea_1.split())
    if palabras_linea_1 > 12:
        errores.append(
            f"Primera línea tiene {palabras_linea_1} palabras (máx 12)"
        )
    
    # ERROR 2: Contiene markdown
    if any(c in caption for c in ['**', '__', '* ', '- ', '# ']):
        errores.append("Caption contiene markdown — texto plano obligatorio")
    
    # ERROR 3: Hashtags pegados
    import re
    if re.search(r'#\w+#\w+', caption):
        errores.append("Hashtags pegados sin espacio — separar")
    
    # ERROR 4: Descripción del video
    PALABRAS_PROHIBIDAS = [
        'en este video', 'en este reel', 'hoy te muestro', 
        'hoy vamos a', 'en este tutorial', 'aprende cómo',
        'te explico', 'te cuento', 'en el siguiente video'
    ]
    for palabra in PALABRAS_PROHIBIDAS:
        if palabra.lower() in caption.lower():
            errores.append(
                f"Caption descriptiva detectada: '{palabra}' — remove"
            )
    
    # ERROR 5: Sin CTA
    PALABRAS_CTA = [
        'comenta', 'link en bio', 'skool', 'guarda', 
        'comparte', 'sígueme', 'click', 'activa notificaciones'
    ]
    if not any(p in caption.lower() for p in PALABRAS_CTA):
        errores.append("Sin CTA — agregar: comenta, guarda, link en bio, etc.")
    
    # ERROR 6: Hashtags inválidos
    hashtags = re.findall(r'#\w+', caption)
    if len(hashtags) < 5:
        errores.append(f"Solo {len(hashtags)} hashtags — usar 5-8")
    if len(hashtags) > 8:
        errores.append(f"{len(hashtags)} hashtags — máximo 8")
    if len(hashtags) == 0:
        errores.append("Sin hashtags")
    
    return errores

# Si hay errores, reescribir automáticamente
# El validador es OBLIGATORIO — no saltear
```

---

### PASO 3: Hashtags Base para @byduvan_ai

```python
HASHTAGS_FIJOS = ["#claude", "#ia", "#negociosdigitales"]

HASHTAGS_POOL = [
    "#automatizacion", "#inteligenciaartificial", "#agentesIA",
    "#marketingdigital", "#emprendimiento", "#productividad",
    "#herramientasIA", "#claudeai", "#trabajoconIA",
    "#negociosdigitales", "#ventajacompetitiva"
]

# Seleccionar 2-3 del pool según tema
# Total: siempre 5-8 hashtags
```

---

### PASO 4: Guardar en Mis Posts

Crear página en `collection://3066a95b-4630-42a2-b113-dbbf022d7970`:

```
Titulo         ← título del video
Semana         ← semana ISO actual
Formato        ← Tier List | Tutorial | Noticia | Contraste | Caso de Uso
Patron GVB     ← patrón del hook
Estado         ← "Pendiente grabacion"
Guion          ← guion completo con timecodes
Caption Elegida ← (dejar vacío — usuario elige A/B/C)
Hashtags       ← hashtags con espacios
```

---

### PASO 5: Output Final

```
═════════════════════════════════════════════════════
CAPTIONS — [TÍTULO]
═════════════════════════════════════════════════════

CAPTION A — DOLOR + PROMESA
─────────────────────────
[texto plano, 3 líneas + hashtags]

✅ 12 palabras | ✅ sin markdown | ✅ hashtags OK | ✅ CTA presente

CAPTION B — CURIOSITY GAP
─────────────────────────
[texto plano]

✅ Validación OK

CAPTION C — CONTRASTE
─────────────────────────
[texto plano]

✅ Validación OK

═════════════════════════════════════════════════════
RECOMENDACIÓN: Caption [A/B/C] porque [razón basada en patrón]

✅ Guardado en Mis Posts (Estado: Pendiente grabacion)
═════════════════════════════════════════════════════
```

---

## REGLAS CRÍTICAS

⚠️ **Primera línea ≤12 palabras:** OBLIGATORIO, sin excepciones

⚠️ **Texto plano:** CERO markdown, CERO bold, CERO asteriscos

⚠️ **Hashtags con espacio:** `#hashtag1 #hashtag2`, no `#hashtag1#hashtag2`

⚠️ **5-8 hashtags siempre:** no menos, no más

⚠️ **CTA obligatorio:** comenta, guarda, link en bio, etc.

⚠️ **Sin descriptivo:** "en este video" → ERROR. Directo al contenido.

⚠️ **Validador automático:** Rechaza antes de entregar. Si hay errores, reescribe.

⚠️ **No entregar sin captions:** Guion + Captions juntos, siempre.
