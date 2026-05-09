# /viral:discover — El Sabueso (Content Hunter)

Agente 1 del sistema go-viral: Descubre hooks virales en competidores, referentes y tendencias, clasifica por patrón GVB y almacena en Hooks DB.

**Flow:** Lee URLs Monitor (Notion) → Scraping con Apify → Análisis de like rate → Clasificación GVB → Escribe Hooks DB → Actualiza URLs Monitor

---

## EJECUCIÓN AUTOMÁTICA

Este comando ejecuta automáticamente el flujo completo. Usa las credenciales en `.env`:

```bash
# Ejecución estándar — procesa URLs Pendientes
/viral:discover

# Ejecución con flags:
/viral:discover --dry-run           # Ver qué haría sin escribir
/viral:discover --source referentes # Solo procesar referentes
/viral:discover --limit 5           # Max 5 videos por categoría
```

**Internamente:** ejecuta `python3 scripts/sabueso.py` con argumentos

---

## REQUISITOS PREVIOS

✅ **Notion:** 4 bases de datos ya creadas (IDs en código)
✅ **Apify:** Token en `.env` con créditos disponibles
✅ **URLs Monitor:** al menos 1 URL con Estado = "Pendiente"
✅ **Python:** 3.8+ con `requests` y `python-dotenv`

---

## PASOS DEL FLUJO

### PASO 1: Leer URLs Monitor
- Conectar a Notion `collection://01901dbf-447d-4425-a06d-a042ec223e7c`
- Extraer filas donde `Estado = "Pendiente"`
- Agrupar por `Lista`: Competidores | Referentes | Viral/Explorar

### PASO 2: Scraping con Apify
**Para Canal (Competidores + Referentes):**
```json
Actor: sian.agency/instagram-ai-transcript-extractor
Input: { "channelUsername": "byduvan_ai", "reelCount": 10 }
```

**Para Video (Viral/Explorar):**
```json
Actor: apify/instagram-scraper
Input: { "directUrls": ["url1"], "resultsType": "posts", "resultsLimit": 10 }
```

Polling hasta status `SUCCEEDED`, leer dataset output.

### PASO 3: Calcular Like Rate & Filtrar Outliers
```
like_rate = (likes / views) * 100
promedio = sum(like_rates) / len(like_rates)
outliers = videos donde like_rate > max(promedio, 3.0)
```

### PASO 4: Clasificar en Patrón GVB (1-6)
Analizar primeras 12 palabras del caption:

1. **Negacion Sorpresiva**: "no hagas / deja de / no uses"
2. **Cifra Concreta**: número + tiempo + resultado
3. **Secreto Revelado**: "lo que nadie / por esto / el secreto"
4. **Contraste**: antes/después
5. **Curiosidad Directa**: pregunta abierta
6. **Urgencia Novedad**: "acaba de / esta semana / ya cambió"

**Tono:** 
- `Operador de Negocio` si menciona: clientes, ventas, tiempo, dinero
- `Tecnico IA` si menciona: modelos, prompts, parámetros
- `Mixto` si ambos

### PASO 5: Escribir Outliers en Hooks DB
Para cada outlier, crear página en `collection://ec06af9a-f1fb-4fd0-83f0-1cdf9fe941a5`:

```
Hook Texto ← primeras 12 palabras del caption
Transcript Hook ← primeras 15 palabras de transcripción
Patron GVB ← 1-6 (exacto del select)
Formato ← Tier List|Tutorial|Noticia|Contraste|Caso de Uso|Comparativa
Like Rate ← float
Views ← number
Fuente ← @username
Duracion seg ← number
Fecha Post ← ISO date
Semana ← week number
Tono ← Operador de Negocio|Tecnico IA|Mixto
```

### PASO 6: Actualizar Estado en URLs Monitor
Para cada fila procesada:
- Sin error → `Estado = "Procesado"`
- Con error Apify → `Estado = "Error"`, agregar nota

### PASO 7: Output Terminal
```
SABUESO COMPLETADO
==================
Canales procesados: N
Videos analizados: N
Outliers guardados: N
Promedio like rate: X%

Top 3 hooks esta semana:
1. "[hook]" — X% — Patrón N — @fuente
2. ...
3. ...

Patrón GVB más frecuente: N - nombre
→ Listo para /viral:destrip (próximo agente)
```

---

## REQUISITOS

`.env`:
```
NOTION_API_KEY=ntn_...
APIFY_API_TOKEN=apify_...
```

Datos iniciales en URLs Monitor:
- soyenriquerocha (Lista: Competidores, Estado: Pendiente)
- byduvan_ai (Lista: Referentes, Estado: Pendiente)

---

## REGLAS CRÍTICAS

⚠️ **Nunca descargar audio de Instagram desde Python directo**
→ Usar Apify actor: `sian.agency/instagram-ai-transcript-extractor`

⚠️ **AssemblyAI (si se usa):**
→ Siempre `"speech_model": "universal-2"`

⚠️ **Outlier threshold:**
→ like_rate > max(promedio, 3.0%) — evita ruido si promedio muy bajo

⚠️ **Patrón GVB:**
→ Ser estricto en clasificación — si no encaja, marcar como "Mixto"

⚠️ **Deduplicación:**
→ Si mismo hook de múltiples fuentes, guardar una vez con todas las fuentes en notas
