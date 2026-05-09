# /viral:script — El Guionista (HookGenie + Guion)

Agente 3 del sistema go-viral: Convierte un hook en un guion de video optimizado según el formato, con duración DURA y estimación precisa.

**Flow:** Hook → HookGenie (10 variaciones) → Selección → Guion estructurado → Caption Master (Agente 4)

---

## EJECUCIÓN

```bash
# Opción 1: Hook explícito
python3 scripts/guionista.py "No hagas esto en tu negocio digital si quieres crecer"

# Opción 2: Leer Brief más reciente automáticamente
python3 scripts/guionista.py --auto

# Flags:
# --formato     Force formato (default: detectar del Brief)
# --duracion    Override duración máxima (segundos)
# --dry-run     Ver sin escribir en Mis Posts
```

**Importante:** Al terminar, llama automáticamente al Agente 4 (Caption Master). No hay output sin captions.

---

## PASOS DEL FLUJO

### PASO 1: HookGenie — 10 Variaciones

Tomar el hook del Brief y generar 10 versiones (2 por patrón GVB):

```python
PATRONES = {
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
```

**Seleccionar el ganador:**
- ≤12 palabras
- Ataca un dolor real
- Tono "Operador de Negocio"

### PASO 2: Detectar Formato y Duración DURA

```python
DURACIONES = {
    "Tier List": 45,
    "Tutorial": 60,
    "Noticia": 30,
    "Contraste": 45,
    "Caso de Uso": 45,
    "Comparativa": 45
}
```

Si el guion supera duración máxima, rechazar y recortar (nunca sacrificar hook ni CTA).

### PASO 3: Escribir Guion Según Estructura

#### CONTRASTE / CASO DE USO (≤45 seg ≈ 112 palabras)

```
[0-3 seg]   HOOK — sin preámbulo
[3-8 seg]   DOLOR — una frase
[8-20 seg]  SOLUCIÓN — accionable
[20-35 seg] RESULTADO — concreto
[35-45 seg] RETENCIÓN + CTA
```

#### TUTORIAL (≤60 seg ≈ 150 palabras)

```
[0-3 seg]   HOOK
[3-10 seg]  PROMESA
[10-45 seg] PASOS — máx 3
[45-55 seg] RESULTADO demostrado
[55-60 seg] RETENCIÓN + CTA
```

#### TIER LIST (≤45 seg)

```
[0-3 seg]   HOOK
[3-38 seg]  TIERS — máx 4 elementos
[38-45 seg] GANADOR + CTA
```

#### NOTICIA (≤30 seg ≈ 75 palabras)

```
[0-3 seg]   HOOK — novedad
[3-15 seg]  QUÉ CAMBIÓ
[15-25 seg] ACCIÓN CONCRETA
[25-30 seg] CTA
```

### PASO 4: Estimar Duración y Validar

```python
palabras = len(guion.split())
segundos = palabras / 2.5  # promedio al hablar

if segundos > duracion_max:
    raise GuionDemasiadoLargoError()
```

### PASO 5: Llamar Agente 4 Automáticamente

Al terminar, pasar al Caption Master que genera 3 versiones validadas.

---

## REGLAS CRÍTICAS

⚠️ **Duración DURA:** No negociable.
⚠️ **Sin jerga:** API → "integración", parámetro → "configuración"
⚠️ **Hook primero:** 0-3 seg cautivador, sin explicación
⚠️ **CTA siempre:** comenta, guarda, sígueme, link en bio
⚠️ **Timecodes:** [0:00-0:03] en cada sección
⚠️ **Caption automático:** Guion NUNCA sin captions validados
