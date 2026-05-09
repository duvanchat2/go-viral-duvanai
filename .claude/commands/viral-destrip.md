# /viral:destrip — El Estratega (Brief Semanal)

Agente 2 del sistema go-viral: Lee hooks virales del Sabueso, analiza patrones ganadores propios, y genera un brief semanal accionable con los 3 temas principales.

**Flow:** Hooks DB → Mis Posts (historial) → Scoring temático → Brief Semanal

---

## EJECUCIÓN

```bash
# Generar brief semanal basado en hooks esta semana
python3 scripts/estratega.py

# Flags (opcionales):
# --week N          Procesar semana N (default: actual)
# --dry-run         Ver sin escribir en Notion
# --verbose         Mostrar scoring detallado
```

---

## PASOS DEL FLUJO

### PASO 1: Leer Hooks DB
- Conectar a Notion `collection://ec06af9a-f1fb-4fd0-83f0-1cdf9fe941a5`
- Extraer filas donde `Semana` = semana ISO actual
- Si está vacía: error `"Hooks DB vacía — ejecuta /viral:discover primero"`

### PASO 2: Leer Historial Mis Posts
- Conectar a Notion `collection://3066a95b-4630-42a2-b113-dbbf022d7970`
- Extraer **outliers positivos**: `Like Rate > 5%` → patrones ganadores
- Extraer **outliers negativos**: `Like Rate < 2%` o `Views < 50` → errores a evitar
- Extraer **temas recientes**: `Semana >= semana_actual - 2` → evitar repetición

### PASO 3: Scoring de Temas Candidatos
Agrupar hooks por similitud semántica. Para cada grupo:

```python
score = 0
score += 3 if patron_gvb aparece en 3+ hooks del grupo
score += 2 if patron coincide con outlier positivo propio
score += 2 if tono == "Operador de Negocio"
score += 1 if like_rate_promedio_grupo > 5%
score += 1 if fuente incluye referente (no solo competidor)
score -= 2 if tema similar publicado en últimas 2 semanas
score -= 3 if tono == "Tecnico IA" en mayoría del grupo
```

### PASO 4: Seleccionar Top 3 Temas
Ordenar por score descendente. Producir para cada tema:

```
tema:              Descripción en una línea
angulo:            El dolor específico o novedad que ataca
formato:           Tier List | Tutorial | Noticia | Contraste | Caso de Uso
duracion:          Segundos objetivo (45-120)
patron_gvb:        Número 1-6 + nombre
hook_sugerido:     ≤12 palabras, texto plano, tono operador de negocio
por_que_ahora:     Razón de relevancia esta semana
```

### PASO 5: Escribir en Brief Semanal
Crear página en `collection://ff4746d0-2480-412a-9763-ba6defde282a`:

```
Titulo                  ← "Brief Semana N — YYYY-MM-DD"
Semana                  ← número ISO
Fecha                   ← hoy ISO
Tema 1 Hook            ← hook_sugerido del tema 1
Tema 1 Formato         ← select exacto (Tier List|Tutorial|Noticia|Contraste|Caso de Uso|Comparativa)
Tema 1 Patron GVB      ← select exacto (1-6)
Tema 2 Hook            ← hook del tema 2
Tema 2 Formato         ← formato del tema 2
Tema 3 Hook            ← hook del tema 3
Funciono esta semana   ← resumen outliers positivos propios
No funciono esta semana ← resumen outliers negativos + causa
Estado                 ← "Pendiente"
```

### PASO 6: Output Terminal

```
ESTRATEGA COMPLETADO — BRIEF SEMANA N
======================================

TEMA 1 ⭐ (score: X)
Tema: [descripción]
Ángulo: [dolor/novedad]
Formato: [tipo] — [duración] seg
Patrón GVB: N - [nombre]
Hook: "[≤12 palabras]"
Por qué: [razón]

TEMA 2 (score: X)
[ídem]

TEMA 3 — reserva (score: X)
[ídem]

APRENDIZAJE SEMANA:
✅ Funcionó: [outlier positivo + patrón]
❌ No funcionó: [outlier negativo + causa]

→ Próximo: /viral:script "[tema 1 hook]"
```

---

## REQUISITOS

`.env`:
```
NOTION_API_KEY=ntn_...
APIFY_API_TOKEN=apify_...  (para futuros agentes)
```

**Datos previos:**
- Hooks DB con filas de esta semana (del Sabueso)
- Mis Posts con al menos 1 entry (historial propio)

---

## LÓGICA DE SCORING

### Bonificaciones (+)

| Criteria | Puntos | Trigger |
|----------|--------|---------|
| Patrón GVB frecuente | +3 | Mismo patrón en 3+ hooks |
| Match patrón ganador | +2 | Patrón coincide con outlier positivo propio |
| Tono negocio | +2 | `Tono == "Operador de Negocio"` |
| Alto engagement | +1 | `like_rate_promedio > 5%` |
| Referente validado | +1 | Fuente incluye referente (no solo competidor) |

### Penalizaciones (-)

| Criteria | Puntos | Trigger |
|----------|--------|---------|
| Tema repetido | -2 | Similar a publicado en últimas 2 semanas |
| Tono técnico | -3 | `Tono == "Tecnico IA"` en mayoría |

### Scoring Ejemplo

```
Hooks del grupo "ROI":
- Hook 1: Patrón 2, Tono Operador, Like Rate 6.2%
- Hook 2: Patrón 2, Tono Mixto, Like Rate 4.8%
- Hook 3: Patrón 2, Tono Operador, Like Rate 5.1%

Cálculo:
+ 3 (patrón 2 aparece 3 veces)
+ 2 (tono Operador en mayoría)
+ 1 (like_rate promedio 5.4% > 5%)
+ 1 (fuentes: @competitor + @referente)
- 0 (tema no repetido)
= 7 puntos
```

---

## AGRUPACIÓN TEMÁTICA

Los hooks se agrupan por **similitud semántica**:

- "No hagas X en negocio" + "Evita Y en ventas" → **Tema: Errores comunes**
- "3x productividad" + "Método para doblar tiempo" → **Tema: Eficiencia**
- "Lo que nadie dice" + "Secreto revelado" → **Tema: Insider knowledge**

Usar análisis simple de palabras clave (business, growth, AI, etc.).

---

## REGLAS CRÍTICAS

⚠️ **Si Hooks DB vacía:** Error inmediato, no continuar

⚠️ **Tema repetido:** Penalización automática si publicado en últimas 2 semanas

⚠️ **Hook sugerido:** Máximo 12 palabras, sin emojis, tono "Operador de Negocio"

⚠️ **Formato:** Debe ser uno de los 6 exactos del select de Notion

⚠️ **Deduplicación:** Si 2 temas tienen score similar, priorizar por fuente (referente > competidor)
