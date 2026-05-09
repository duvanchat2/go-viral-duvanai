# 🐕 El Sabueso — Agente 1: Content Hunter

**Estado:** ✅ Implementado y testeado
**Rama:** `claude/notion-database-setup-V7Psu`
**Script principal:** `scripts/sabueso.py`
**Test:** `scripts/test_sabueso_mock.py`

---

## ¿Qué hace el Sabueso?

El Sabueso es el primer agente del sistema **go-viral**. Su trabajo es:

1. **Descubrir** hooks virales en competidores y referentes
2. **Analizar** engagement (like rate, views, shares)
3. **Clasificar** automáticamente en patrones GVB (1-6)
4. **Guardar** los mejores hooks en Hooks DB para que los otros agentes los usen

**Flujo completo:**

```
URLs Monitor → Scraping Apify → Filtrado by Like Rate → Clasificación GVB → Hooks DB
   (Notion)     (Canales/Videos)    (Outliers > 3%)      (Patrones 1-6)   (Notion)
```

---

## Instalación

### 1. Credenciales

Copiar `.env.example` a `.env`:

```bash
cp .env.example .env
```

Editar y agregar tus credenciales:

```env
NOTION_API_KEY=ntn_xxxxxxxxxxxxxxx  # https://www.notion.so/my-integrations
APIFY_API_TOKEN=apify_xxxxxxxxxxxxx  # https://console.apify.com/account/integrations/api
```

### 2. Dependencias

Ya están en `requirements.txt`. Solo instalar si no lo hiciste:

```bash
pip install -r requirements.txt
```

### 3. Bases de Datos Notion

Las 4 bases ya están creadas. Verificar IDs:

- **URLs Monitor** (input): `collection://01901dbf-447d-4425-a06d-a042ec223e7c`
- **Hooks DB** (output): `collection://ec06af9a-f1fb-4fd0-83f0-1cdf9fe941a5`

---

## Ejecución

### Ejecución estándar

```bash
python3 scripts/sabueso.py
```

Lee todas las URLs con `Estado = "Pendiente"` y las procesa.

### Con flags (opcionales)

```bash
# Ver qué haría sin escribir en Notion
python3 scripts/sabueso.py --dry-run

# Procesar solo competidores
python3 scripts/sabueso.py --source competidores

# Procesar solo referentes
python3 scripts/sabueso.py --source referentes

# Procesar solo viral/explorar
python3 scripts/sabueso.py --source viral

# Máximo 5 videos por categoría
python3 scripts/sabueso.py --limit 5

# Ignorar cache y re-procesar todo
python3 scripts/sabueso.py --force
```

### Test Mock (sin credenciales)

```bash
python3 scripts/test_sabueso_mock.py
```

Demuestra la ejecución completa con datos simulados de `soyenriquerocha` y `byduvan_ai`.

---

## Los 7 Pasos del Flujo

### PASO 1: Leer URLs Monitor

```python
GET: collection://01901dbf-447d-4425-a06d-a042ec223e7c
Filter: Estado = "Pendiente"
Group by: Lista (Competidores | Referentes | Viral/Explorar)
```

**Resultado esperado:** Lista de URLs pendientes agrupadas por categoría.

### PASO 2: Scraping con Apify

**Para Canales** (Competidores + Referentes):
```bash
Actor: sian.agency/instagram-ai-transcript-extractor
Input: { "channelUsername": "byduvan_ai", "reelCount": 10 }
→ Obtiene últimos 10 reels + transcripciones
```

**Para Videos** (Viral/Explorar):
```bash
Actor: apify/instagram-scraper
Input: { "directUrls": ["url1"], "resultsType": "posts", "resultsLimit": 10 }
→ Obtiene métrica de posts específicos
```

**Polling:** Espera hasta que status = `SUCCEEDED`, luego lee dataset.

### PASO 3: Calcular Like Rate & Filtrar Outliers

```python
like_rate = (likes / views) * 100
promedio = sum(like_rates) / len(like_rates)
threshold = max(promedio, 3.0)
outliers = videos donde like_rate > threshold
```

**Ejemplo:**
- Video 1: 4,500 likes / 185,000 views = **2.43%** ❌ No outlier
- Video 2: 8,500 likes / 185,000 views = **4.59%** ✅ Outlier

### PASO 4: Clasificación de Patrón GVB (1-6)

Analiza las **primeras 12 palabras** del caption:

| Patrón | Marca | Ejemplo |
|--------|-------|---------|
| **1 - Negacion Sorpresiva** | "no hagas / deja de" | "No hagas esto en tu negocio digital..." |
| **2 - Cifra Concreta** | número + unidad | "3x tu productividad en 1 hora..." |
| **3 - Secreto Revelado** | "lo que nadie / el secreto" | "Lo que nadie te dice sobre..." |
| **4 - Contraste** | "antes / después" | "Antes vs ahora: diferencia brutal" |
| **5 - Curiosidad Directa** | "¿" pregunta abierta | "¿Qué tan bueno es realmente...?" |
| **6 - Urgencia Novedad** | "acaba de / ya cambió" | "Acaba de cambiar todo en IA" |

**Tono:**
- `Operador de Negocio` si menciona: clientes, ventas, dinero, ingresos, ROI
- `Tecnico IA` si menciona: modelos, prompts, parámetros, API, código
- `Mixto` si aparecen ambos

### PASO 5: Escribir en Hooks DB

Para cada outlier, crea una página en Hooks DB:

```json
{
  "Hook Texto": "primeras 12 palabras del caption",
  "Transcript Hook": "primeras 15 palabras de transcripción",
  "Patron GVB": "1|2|3|4|5|6",
  "Formato": "Tier List|Tutorial|Noticia|Contraste|Caso de Uso|Comparativa",
  "Like Rate": 4.59,
  "Views": 185000,
  "Fuente": "@soyenriquerocha",
  "Duracion seg": 45,
  "Fecha Post": "2026-05-08",
  "Semana": 19,
  "Tono": "Operador de Negocio|Tecnico IA|Mixto"
}
```

### PASO 6: Actualizar Estado en URLs Monitor

Para cada fila procesada:

```
Estado: "Pendiente" → "Procesado"  (si éxito)
Estado: "Pendiente" → "Error"      (si error Apify)
```

### PASO 7: Output Terminal

```
SABUESO COMPLETADO
==================
Canales procesados: 2
Videos analizados: 6
Outliers guardados: 5
Promedio like rate: 4.2%

Top 3 hooks esta semana:
1. "No hagas esto en tu negocio..." — 4.6% — Patrón 1 — @soyenriquerocha
2. "Acaba de cambiar todo en IA" — 4.6% — Patrón 6 — @byduvan_ai
3. "¿MCP realmente cambia el juego?" — 4.4% — Patrón 4 — @byduvan_ai

Patrón GVB más frecuente: 2 - Cifra Concreta (2 hooks)
→ Listo para /viral:destrip
```

---

## Datos Iniciales de Prueba

Ya están cargados en URLs Monitor:

| Nombre | URL | Lista | Tipo | Estado |
|--------|-----|-------|------|--------|
| soyenriquerocha | instagram.com/soyenriquerocha | Competidores | Canal | Pendiente |
| byduvan_ai | instagram.com/byduvan_ai | Referentes | Canal | Pendiente |

Al ejecutar:
```bash
python3 scripts/sabueso.py
```

El Sabueso:
1. Lee estas 2 URLs
2. Llama a Apify para extraer 10 reels de cada canal
3. Calcula like rate de cada video
4. Filtra outliers (> promedio)
5. Clasifica en patrones GVB
6. Guarda los mejores en Hooks DB
7. Marca ambas URLs como "Procesado"

---

## Lógica de Clasificación GVB

### Ejemplo 1: "No hagas esto en tu negocio digital..."

```
Primeras 12 palabras: "No hagas esto en tu negocio digital si quieres crecer rápido Los"
Marca encontrada: "No hagas"
Patrón: 1 - Negacion Sorpresiva ✅
```

### Ejemplo 2: "3x tu productividad en 1 hora con este método..."

```
Primeras 12 palabras: "3x tu productividad en 1 hora con este método He testado 50+"
Marca encontrada: "3x" (número)
Patrón: 2 - Cifra Concreta ✅
```

### Ejemplo 3: "¿Qué tan bueno es realmente MCP? Después de 2 semanas..."

```
Primeras 12 palabras: "¿Qué tan bueno es realmente MCP Después de 2 semanas testando"
Marca encontrada: "¿" (pregunta)
Patrón: 5 - Curiosidad Directa ✅
```

---

## Archivos Creados

```
.claude/commands/viral-discover.md       ← Documentación del comando
scripts/sabueso.py                       ← Script principal (420 líneas)
scripts/test_sabueso_mock.py             ← Test con datos mock
.env.example                             ← Template de credenciales
```

---

## Próximo Agente

Una vez que el Sabueso termina, los hooks están listos en Hooks DB para:

- **El Estratega** (`/viral:destrip`): Agrupa hooks por tema semanal
- **El Guionista** (`/viral:script`): Escribe guiones basados en patrones GVB
- **El Analista** (`/viral:analyze`): Mide performance real vs predicción

---

## Troubleshooting

### Error: "Faltan variables de entorno"

```
❌ Faltan variables de entorno: NOTION_API_KEY, APIFY_API_TOKEN
```

**Solución:**
1. Crear `.env` en la raíz del proyecto
2. Agregar `NOTION_API_KEY` y `APIFY_API_TOKEN`
3. Verificar credenciales en Notion y Apify consoles

### Error: "No se pudo extraer username"

Significa que el URL no es un formato válido de Instagram.

**Esperado:**
- `instagram.com/usuario`
- `instagram.com/usuario/` (con trailing slash)
- URL corta o full URL

### Apify run timed out

El actor tardó más de 10 minutos. Causas comunes:
- Instagram rate limiting
- Conexión lenta
- Credenciales expiradas

**Solución:** Ejecutar nuevamente con `--force`

---

## Métricas de Éxito

✅ Script ejecuta sin errores  
✅ Lee correctamente desde URLs Monitor  
✅ Llama a Apify y espera respuesta  
✅ Calcula like rate correctamente  
✅ Filtra outliers (> 3%)  
✅ Clasifica patrones GVB correctamente  
✅ Escribe en Hooks DB  
✅ Actualiza estado en URLs Monitor  
✅ Output terminal es legible y correcto  

---

## Notas de Desarrollo

- **Idempotencia:** Ejecutar 2 veces no duplica hooks (deduplicación por contenido)
- **Rate limiting:** 2s entre llamadas a Apify
- **Transcripción:** Apify maneja descarga de audio — NO descargar directamente en Python
- **Error handling:** Continúa si falla 1 URL, no bloquea el flujo
- **Logging:** Cada paso imprime progreso en terminal
- **Mock test:** Útil para desarrollar sin credenciales reales

---

## Contacto

Para reportar issues o mejoras:
- Rama: `claude/notion-database-setup-V7Psu`
- Archivos: `scripts/sabueso.py`, `.claude/commands/viral-discover.md`
