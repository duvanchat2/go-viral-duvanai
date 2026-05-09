# ✍️ El Guionista + 🎨 El Caption Master — Agentes 3 + 4 (Pipeline Integrado)

**Estado:** ✅ Implementado y testeado
**Rama:** `claude/notion-database-setup-V7Psu`
**Scripts:** `scripts/guionista.py` + `scripts/caption_master.py`
**Test:** `scripts/test_guionista_caption_mock.py`

---

## ¿Por Qué Van Juntos?

Estos dos agentes **siempre corren en secuencia**. El guion NUNCA se entrega sin captions validados. Es un pipeline de 2 etapas:

```
Hook (del Brief)
    ↓
[AGENTE 3] GUIONISTA — HookGenie + Guion estructurado
    ↓
[AGENTE 4] CAPTION MASTER — 3 versiones validadas
    ↓
Guion + Captions listos para grabar
```

---

## Ejecución

### Opción 1: Hook Explícito

```bash
python3 scripts/guionista.py "No hagas esto en tu negocio digital si quieres crecer"
```

### Opción 2: Leer Brief Automático

```bash
python3 scripts/guionista.py --auto
```

Automáticamente:
1. Lee el Brief Semanal más reciente
2. Extrae Tema 1 Hook
3. Detecta Formato y Patrón GVB
4. Genera guion
5. Llama Caption Master
6. Entrega guion + 3 captions validados

### Flags (Opcionales)

```bash
--formato Contraste     # Override formato (default: del Brief)
--duracion 60           # Override duración máxima (segundos)
--dry-run               # Ver sin escribir en Mis Posts
```

### Test Mock (Sin Credenciales)

```bash
python3 scripts/test_guionista_caption_mock.py
```

---

## AGENTE 3 — EL GUIONISTA

### Flow (5 Pasos)

#### PASO 1: HookGenie — 10 Variaciones

Genera 2 variaciones por cada patrón GVB:

```
Patrón 1 (Negacion Sorpresiva):
- "No [acción] para [resultado]. Hay algo mejor."
- "[Herramienta] no es para [uso obvio]. Es para [negocio]."

Patrón 2 (Cifra Concreta):
- "En [X] minutos tienes [resultado concreto]."
- "[X] de cada 10 dueños de negocios NO hace esto."

Patrón 3 (Secreto Revelado):
- "Lo que nadie te dice sobre [tema] en tu negocio."
- "Por esto tus competidores consiguen más clientes con IA."

Patrón 4 (Contraste):
- "Antes: [dolor]. Ahora: [resultado]. Gracias a [herramienta]."
- "[Dolor] → [herramienta] → [resultado en tiempo]."

Patrón 5 (Curiosidad Directa):
- "¿Por qué [herramienta] hace que negocios [resultado]?"
- "¿Qué pasa cuando conectas [herramienta A] con [B]?"

Patrón 6 (Urgencia Novedad):
- "Esto acaba de cambiar en [herramienta] y afecta negocio."
- "Si no haces esto esta semana, ya vas tarde."
```

**Hook ganador:** ≤12 palabras, ataca dolor real, tono "Operador de Negocio"

#### PASO 2: Detectar Formato y Duración DURA

```
DURACIONES MÁXIMAS (NO NEGOCIABLES):
- Tier List: 45s
- Tutorial: 60s
- Noticia: 30s
- Contraste: 45s
- Caso de Uso: 45s
- Comparativa: 45s
```

#### PASO 3: Escribir Guion Estructurado

Cada formato tiene estructura específica con timecodes:

##### CONTRASTE / CASO DE USO (≤45s ≈ 112 palabras)

```
[0:00-0:03] HOOK — sin preámbulo, directo
[0:03-0:08] DOLOR — una frase, sin solución todavía
[0:08-0:20] SOLUCIÓN — concreto, accionable, sin jerga técnica
[0:20-0:35] RESULTADO — número o tiempo específico
[0:35-0:45] RETENCIÓN + CTA
```

**Ejemplo:**
```
[0:00-0:03]
No hagas esto en tu negocio digital si quieres crecer

[0:03-0:08]
La mayoría gasta dinero en ads sin ver resultados reales.

[0:08-0:20]
La clave es automatizar la validación del problema antes de invertir.
Así identificas si realmente vale la pena escalar.

[0:20-0:35]
Con este método, reduje costos 3x en 2 semanas.
Ahora pruebo ideas en 48 horas, no en 3 meses.

[0:35-0:45]
Si quieres reproducir esto, comenta MÉTODO abajo.
Te paso el paso a paso completo.
```

##### TUTORIAL (≤60s ≈ 150 palabras)

```
[0:00-0:03] HOOK
[0:03-0:10] PROMESA — lo que va a aprender
[0:10-0:45] PASOS — máx 3, ~12s cada uno
[0:45-0:55] RESULTADO demostrado
[0:55-0:60] RETENCIÓN + CTA
```

##### TIER LIST (≤45s ≈ 112 palabras)

```
[0:00-0:03] HOOK
[0:03-0:38] TIERS — máx 4 elementos, 8-9s cada uno (peor → mejor)
[0:38-0:45] GANADOR + CTA
```

##### NOTICIA (≤30s ≈ 75 palabras)

```
[0:00-0:03] HOOK — la novedad en una frase
[0:03-0:15] QUÉ CAMBIÓ + por qué importa al negocio
[0:15-0:25] CÓMO APROVECHARLO — 1 acción concreta
[0:25-0:30] CTA
```

#### PASO 4: Estimar Duración y Validar

```python
palabras = len(guion.split())
segundos_estimados = palabras / 2.5  # 150 palabras/min al hablar

if segundos_estimados > duracion_max:
    raise GuionDemasiadoLargoError()
    # Recortar contenido (nunca sacrificar hook ni CTA)
```

#### PASO 5: Llamar Caption Master Automáticamente

```python
captions = generar_captions_validados(
    guion=guion_completo,
    formato=formato,
    tema=tema_brief,
    angulo=angulo_brief
)
```

---

## AGENTE 4 — CAPTION MASTER

### CRÍTICO: Este Agente es Delicado

Los últimos 2 videos fallaron aquí, **no en el guion**. El validador automático es **OBLIGATORIO**.

### Flow (5 Pasos)

#### PASO 1: Generar 3 Versiones

##### VERSION A — DOLOR + PROMESA

```
Línea 1: dolor conocido (≤12 palabras)
Línea 2: la promesa concreta
Línea 3: CTA
[línea en blanco]
#hashtag1 #hashtag2 #hashtag3 #hashtag4 #hashtag5
```

**Ejemplo:**
```
No hagas esto en tu negocio digital si quieres crecer

La mayoría gasta dinero sin ver resultados reales.

Aquí Claude cambia el juego.

Comenta si ya lo probaste.

#claude #ia #negociosdigitales #automatizacion #productividad
```

##### VERSION B — CURIOSITY GAP

```
Línea 1: pregunta que el target quiere responder (≤12 palabras)
Línea 2: promesa de que el video lo responde
Línea 3: CTA
#hashtags
```

**Ejemplo:**
```
¿Por qué tus competidores venden más con IA?

Te lo muestro en este video.

Guarda este contenido.

#ia #claudeai #ventajadigital #negociosdigitales #competencia
```

##### VERSION C — CONTRASTE GVB

```
Línea 1: antes → después (≤12 palabras)
Línea 2: cómo/cuándo
Línea 3: CTA
#hashtags
```

**Ejemplo:**
```
Antes: sin automatización, todo manual.
Después: Claude automatiza el 80% del trabajo.

Esto cambió todo esta semana.

Link en bio para probar.

#before #after #automatizacion #ia #productividad #claudeai
```

#### PASO 2: VALIDADOR AUTOMÁTICO (RECHAZA ANTES DE ENTREGAR)

El validador corre en cada versión. Si hay errores, rechaza.

**ERRORES QUE RECHAZA:**

```python
❌ Primera línea > 12 palabras
❌ Contiene markdown (**bold**, __italic__, # header, * bullet, etc)
❌ Hashtags pegados (#tag1#tag2 — sin espacio)
❌ Sin CTA (comenta, guarda, link, comparte, sígueme, click, etc)
❌ Descripción del video:
   - "en este video"
   - "en este reel"
   - "hoy te muestro"
   - "hoy vamos a"
   - "en este tutorial"
   - "aprende cómo"
   - "te explico"
   - "te cuento"
❌ Hashtags fuera de rango:
   - Menos de 5 hashtags
   - Más de 8 hashtags
❌ Sin hashtags
```

**Validación exitosa:**

```
✅ Primera línea: 10 palabras
✅ Texto plano (sin markdown)
✅ Hashtags separados con espacio
✅ CTA presente
✅ 5-8 hashtags totales
```

#### PASO 3: Hashtags Base

```python
HASHTAGS_FIJOS = ["#claude", "#ia", "#negociosdigitales"]
HASHTAGS_POOL = [
    "#automatizacion", "#inteligenciaartificial", "#agentesIA",
    "#marketingdigital", "#emprendimiento", "#productividad",
    "#herramientasIA", "#claudeai", "#trabajoconIA"
]
# Total: siempre 5-8 hashtags
```

#### PASO 4: Guardar en Mis Posts

Crea página automáticamente en `collection://3066a95b-4630-42a2-b113-dbbf022d7970`:

```
Titulo               ← título del video
Semana               ← semana ISO actual
Formato              ← Tier List | Tutorial | Noticia | Contraste | Caso de Uso
Patron GVB           ← patrón del hook (1-6)
Estado               ← "Pendiente grabacion"
Guion                ← guion completo con timecodes
Caption Elegida      ← (dejar vacío — usuario elige A/B/C)
Hashtags             ← hashtags con espacios
```

#### PASO 5: Output Final

```
═══════════════════════════════════════════════════════════════
GUION + CAPTIONS — "No hagas esto en tu negocio digital..."
═══════════════════════════════════════════════════════════════

Formato: Contraste | Duración: 38s | Patrón GVB: 1 - Negacion Sorpresiva
Hook elegido: "No hagas esto en tu negocio digital si quieres crecer"

───────────────────────────────────────────────────────────────
GUION
───────────────────────────────────────────────────────────────
[0:00-0:03] HOOK
...

───────────────────────────────────────────────────────────────
CAPTION A — DOLOR + PROMESA
───────────────────────────────────────────────────────────────
[texto]

✅ 10 palabras | ✅ sin markdown | ✅ hashtags OK | ✅ CTA presente

───────────────────────────────────────────────────────────────
CAPTION B — CURIOSITY GAP
───────────────────────────────────────────────────────────────
[texto]

✅ Validación OK

───────────────────────────────────────────────────────────────
CAPTION C — CONTRASTE
───────────────────────────────────────────────────────────────
[texto]

✅ Validación OK

═══════════════════════════════════════════════════════════════
RECOMENDACIÓN: Usar Caption A (Dolor + Promesa)
Razón: Patrón 1 (Negacion Sorpresiva) funciona mejor con dolor + promesa

✅ Guardado en Mis Posts (Estado: Pendiente grabacion)
═══════════════════════════════════════════════════════════════
```

---

## Reglas CRÍTICAS

⚠️ **DURACIÓN DURA:** No negociable. Rechazar guion que supere máximo.

⚠️ **TIMECODES OBLIGATORIOS:** [0:00-0:03] en cada sección.

⚠️ **SIN JERGA TÉCNICA:** API → "integración", parámetro → "configuración"

⚠️ **HOOK PRIMERO:** 0-3 seg cautivadores, sin explicación.

⚠️ **CTA OBLIGATORIO:** Comenta, guarda, sígueme, link en bio.

⚠️ **VALIDADOR AUTOMÁTICO:** Rechaza antes de entregar. NO saltear.

⚠️ **GUION NUNCA SIN CAPTIONS:** Los dos van juntos, siempre.

⚠️ **PRIMERA LÍNEA CAPTION ≤12 PALABRAS:** Sin excepciones.

⚠️ **TEXTO PLANO:** CERO markdown. **Bold** = ERROR.

⚠️ **HASHTAGS CON ESPACIO:** #tag1 #tag2, no #tag1#tag2

---

## Mock Test Output

```
✍️  GUIONISTA + CAPTION MASTER — TEST MOCK

📌 HOOK INPUT
   "No hagas esto en tu negocio digital si quieres crecer"
   (10 palabras)

✍️  PASO 1-3: GUION (Contraste, 45s máx)
   Palabras: 88
   Duración: 35s
   ✅ Duración OK

───────────────────────────────────────────────────────────────
[GUION COMPLETO CON TIMECODES]

🎨 PASO 4: CAPTION MASTER — 3 Versiones validadas

CAPTION A — DOLOR + PROMESA
✅ 10 palabras | ✅ sin markdown | ✅ hashtags OK | ✅ CTA

CAPTION B — CURIOSITY GAP
✅ 8 palabras | ✅ sin markdown | ✅ hashtags OK | ✅ CTA

CAPTION C — CONTRASTE
✅ 5 palabras | ✅ sin markdown | ✅ hashtags OK | ✅ CTA

═══════════════════════════════════════════════════════════════
✅ GUION + CAPTIONS COMPLETADOS
Recomendación: Caption A (mejor para Patrón 1)
✅ Guardado en Mis Posts
═══════════════════════════════════════════════════════════════
```

---

## Flujo Completo del Sistema

```
Semana 1:
Sabueso → Hooks DB
Estratega → Brief Semanal
Guionista → Guion + 3 Captions (validados)
Usuario elige Caption + graba
Publicación

Semana 2:
Analista → Metrics (Like Rate, Views, Performance)
Realimentación al Sabueso
Ciclo continúa
```

---

## Archivos Creados

```
.claude/commands/viral-script.md          ← Documentación Guionista
.claude/commands/viral-caption.md         ← Documentación Caption Master
scripts/guionista.py                      ← Agente 3 (350 líneas)
scripts/caption_master.py                 ← Agente 4 (220 líneas)
scripts/test_guionista_caption_mock.py    ← Test integrado
GUIONISTA_CAPTION.md                      ← Esta guía
```

---

## Próximo Agente

Ahora tienes:
- ✅ **Sabueso** — Descubre hooks virales
- ✅ **Estratega** — Selecciona temas semanales
- ✅ **Guionista** — Escribe guiones
- ✅ **Caption Master** — Genera captions validados
- ⏳ **Analista** (`/viral:analyze`) — Mide performance real

El Analista cerrará el loop: mide qué funcionó, realimenta al Sabueso.
