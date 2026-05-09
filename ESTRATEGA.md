# 📊 El Estratega — Agente 2: Brief Semanal

**Estado:** ✅ Implementado y testeado
**Rama:** `claude/notion-database-setup-V7Psu`
**Script principal:** `scripts/estratega.py`
**Test:** `scripts/test_estratega_mock.py`

---

## ¿Qué hace el Estratega?

El Estratega es el segundo agente del sistema **go-viral**. Su trabajo es:

1. **Recibir** el output del Sabueso (Hooks DB con hooks de la semana)
2. **Analizar** patrones ganadores propios (Mis Posts)
3. **Agrupar** hooks por tema semántico
4. **Calificar** temas basados en 7 criterios
5. **Seleccionar** los 3 temas más relevantes
6. **Generar** un Brief Semanal accionable

**Flujo completo:**

```
Hooks DB → Tema Agrupation → Scoring → Top 3 Selection → Brief Semanal
(Input)    (Semántica)       (Criterios)  (Ranking)       (Output)
            + Mis Posts
```

---

## Instalación

### Requisitos

Mismo que el Sabueso:
- `.env` con `NOTION_API_KEY`
- `requirements.txt` ya instalado

---

## Ejecución

### Ejecución estándar

```bash
python3 scripts/estratega.py
```

Lee todos los hooks de la **semana ISO actual** y genera Brief Semanal.

### Con flags (opcionales)

```bash
# Ver qué haría sin escribir en Notion
python3 scripts/estratega.py --dry-run

# Procesar semana específica
python3 scripts/estratega.py --week 18

# Mostrar scoring detallado
python3 scripts/estratega.py --verbose

# Combinados
python3 scripts/estratega.py --week 18 --dry-run --verbose
```

### Test Mock (sin credenciales)

```bash
python3 scripts/test_estratega_mock.py
```

Demuestra el flujo completo con datos simulados del Sabueso y Mis Posts.

---

## Los 6 Pasos del Flujo

### PASO 1: Leer Hooks DB

```python
GET: collection://ec06af9a-f1fb-4fd0-83f0-1cdf9fe941a5
Filter: Semana = semana_iso_actual
```

**Error si está vacía:**
```
❌ Hooks DB vacía — ejecuta /viral:discover primero
```

**Resultado esperado:** Lista de hooks agrupados (Competidores + Referentes).

---

### PASO 2: Leer Historial Propio (Mis Posts)

```python
GET: collection://3066a95b-4630-42a2-b113-dbbf022d7970
Extract:
  - Outliers positivos: Like Rate > 5%
  - Outliers negativos: Like Rate < 2% OR Views < 50
  - Temas recientes: Semana >= semana_actual - 2
```

**Propósito:** Identificar patrones ganadores y errores a evitar.

**Ejemplo:**

```
✅ POSITIVOS (Like Rate > 5%):
- "ROI sin gastar en ads" — 6.2% — Patrón 2 - Cifra Concreta

❌ NEGATIVOS (Like Rate < 2%):
- "Deep dive algoritmos" — 1.5% — Tono Tecnico IA
```

---

### PASO 3: Agrupar y Scoring

#### Agrupación Temática

Hooks se agrupan por similitud semántica:

```python
# Keywords
business_words = {"negocio", "dinero", "ventas", "crecimiento"}
ai_words = {"ia", "claude", "chatgpt", "modelo", "prompt"}

# Grupos resultantes
grupos = {
  "business": [hooks que hablan de negocio],
  "ia": [hooks que hablan de IA],
  "growth": [hooks sobre crecimiento]
}
```

#### Scoring Formula

Para cada grupo calcular:

```python
score = 0
score += 3 if patron_gvb aparece en 3+ hooks
score += 2 if patron coincide con outlier positivo propio
score += 2 if tono == "Operador de Negocio"
score += 1 if like_rate_promedio > 5%
score += 1 if fuente incluye referente (no solo competidor)
score -= 2 if tema similar publicado en últimas 2 semanas
score -= 3 if tono == "Tecnico IA" en mayoría
```

**Ejemplo de cálculo:**

```
Tema: "Negocio Digital"
Hooks:
1. "No hagas X en negocio" — Patrón 1, Tono Operador
2. "3x productividad" — Patrón 2, Tono Mixto
3. "Lo que nadie sabe" — Patrón 3, Tono Mixto

Score:
+ 0 (patrón no aparece 3+ veces)
+ 2 (tono Operador en mayoría)
+ 1 (like_rate promedio 4.4%, no > 5%)
+ 1 (hay referente @soyenriquerocha)
- 0 (tema no repetido)
= 4 puntos
```

---

### PASO 4: Seleccionar Top 3

Ordenar temas por score descendente. Para cada tema producir:

| Campo | Contenido |
|-------|-----------|
| **tema** | Descripción en 1 línea |
| **angulo** | El dolor/novedad específico |
| **formato** | Tier List\|Tutorial\|Noticia\|Contraste\|Caso de Uso\|Comparativa |
| **duracion** | Segundos objetivo (45-120) |
| **patron_gvb** | Número 1-6 + nombre |
| **hook_sugerido** | ≤12 palabras, plano, tono Operador |
| **por_que_ahora** | Razón de relevancia esta semana |

**Ejemplo:**

```
TEMA 1: Estrategia de Negocio
Ángulo: Errores que matan startups
Formato: Contraste — 60 seg
Patrón GVB: 1 - Negacion Sorpresiva
Hook: "No hagas esto en tu negocio digital si quieres crecer"
Por qué: Patrón validado en competidores (like_rate 4.6%)
```

---

### PASO 5: Escribir Brief Semanal

Crear página en `collection://ff4746d0-2480-412a-9763-ba6defde282a`:

```json
{
  "Titulo": "Brief Semana 19 — 2026-05-09",
  "Semana": 19,
  "Fecha": "2026-05-09",
  "Tema 1 Hook": "No hagas esto en tu negocio digital...",
  "Tema 1 Formato": "Contraste",
  "Tema 1 Patron GVB": "1 - Negacion Sorpresiva",
  "Tema 2 Hook": "Lo que nadie te dice sobre...",
  "Tema 2 Formato": "Noticia",
  "Tema 3 Hook": "Acaba de cambiar todo en IA...",
  "Funciono esta semana": "ROI sin gastar en ads (6.2%)",
  "No funciono esta semana": "Deep dive técnico (1.5%) — demasiado especializado",
  "Estado": "Pendiente"
}
```

---

### PASO 6: Output Terminal

```
ESTRATEGA COMPLETADO — BRIEF SEMANA 19
======================================

TEMA 1 ⭐ (score: 3.0)
Tema: Cómo crecer y escalar tu negocio digital
Ángulo: Errores que matan startups
Formato: Contraste — 60 seg
Patrón GVB: 1 - Negacion Sorpresiva
Hook: "No hagas esto en tu negocio digital si quieres crecer"
Por qué: Like rate validado en competidores

TEMA 2 (score: 1.5)
Tema: Growth Hacking
Ángulo: Tácticas para crecer 10x
Formato: Tutorial — 90 seg
Patrón GVB: 2 - Cifra Concreta
Hook: "3x tu productividad en 1 hora con este método"
Por qué: Patrón coincide con outlier positivo propio (6.2%)

TEMA 3 — reserva (score: 1.0)
Tema: Herramientas IA
...

📈 APRENDIZAJE SEMANA:
✅ Funcionó: ROI sin gastar en ads (6.2%) — Patrón 2 - Cifra Concreta
❌ No funcionó: Deep dive en algoritmos (1.5%) — demasiado técnico

→ Próximo: /viral:script "No hagas esto en tu negocio digital si quieres crecer"
```

---

## Lógica de Agrupación Temática

### Palabras Clave por Tema

| Tema | Keywords |
|------|----------|
| **business** | negocio, dinero, ventas, crecimiento, productividad, roi, ingresos |
| **ia** | ia, claude, chatgpt, modelo, prompt, api, código, algoritmo |
| **growth** | 3x, 10x, antes, después, contraste, vs, doblar, aumentar |

### Proceso

```python
# 1. Extraer keywords del hook
hook = "No hagas esto en tu negocio digital..."
keywords = extract_keywords(hook)  # {"business"}

# 2. Asignar al grupo
if "business" in keywords:
    grupos["business"].append(hook)

# 3. Calcular score del grupo
score = calculate_theme_score(grupos["business"], ...)
```

---

## Criterios de Scoring Detallado

### Bonificaciones (+)

| Criterio | Puntos | Triggereable |
|----------|--------|-------------|
| Patrón muy frecuente | +3 | Mismo patrón en 3+ hooks del grupo |
| Match patrón ganador | +2 | Patrón = un outlier positivo propio |
| Tono comercial | +2 | Mayoría del grupo = "Operador de Negocio" |
| Alto engagement | +1 | Like rate promedio > 5% |
| Fuente mixta | +1 | Incluye referente (no solo competidor) |

### Penalizaciones (-)

| Criterio | Puntos | Trigger |
|----------|--------|---------|
| Tema repetido | -2 | Similar a publicado en últimas 2 semanas |
| Tono muy técnico | -3 | Mayoría = "Tecnico IA" |

---

## Flujo de Errores

### Hooks DB Vacía

```
PASO 1 → Sem conexión o sin datos
↓
❌ ERROR: "Hooks DB vacía — ejecuta /viral:discover primero"
↓
EXIT (no continuar)
```

**Solución:** Ejecutar `/viral:discover` primero para llenar Hooks DB.

### Mis Posts Vacío

```
PASO 2 → Sem historial propio
↓
⚠️ WARNING: "Sin historial propio — usando scoring genérico"
↓
CONTINUE (usar scoring sin data propia)
```

**Impacto:** Score menos preciso, pero no bloquea.

### Notion Write Error

```
PASO 5 → Error creando Brief
↓
❌ ERROR: "Error escribiendo Brief Semanal"
↓
Imprimir resultado + advertencia
```

**Solución:** Verificar `NOTION_API_KEY` y permisos.

---

## Datos de Entrada/Salida

### Entrada

| Fuente | Tabla | Campos |
|--------|-------|--------|
| Sabueso output | Hooks DB | Hook Texto, Patron GVB, Tono, Like Rate, Views, Fuente, Semana |
| Historial propio | Mis Posts | Like Rate, Views, Patron GVB, Semana |

### Salida

| Destino | Tabla | Campos |
|---------|-------|--------|
| Guionista input | Brief Semanal | Tema 1/2/3 Hook, Formato, Patron GVB, Aprendizajes |

---

## Archivos Creados

```
.claude/commands/viral-destrip.md      ← Documentación del comando
scripts/estratega.py                   ← Script principal (400 líneas)
scripts/test_estratega_mock.py         ← Test con datos mock (280 líneas)
ESTRATEGA.md                           ← Esta guía
```

---

## Mock Test Output

```
📖 PASO 1: Leyendo Hooks DB...
  ✓ 5 hooks encontrados

📚 PASO 2: Analizando historial propio...
  ✓ Outliers positivos: 1
  ✓ Outliers negativos: 1

📊 PASO 3: Calculando scores...
  • business: score 3.0 (2 hooks)
  • ia: score 1.0 (2 hooks)
  • growth: score 1.0 (1 hooks)

✅ ESTRATEGA COMPLETADO — BRIEF SEMANA 19
- Tema 1 (score 3.0): Estrategia de Negocio
- Tema 2 (score 1.5): Growth Hacking
- Tema 3 (score 1.0): Herramientas IA
```

---

## Próximo Agente

Una vez que el Estratega completa, el Brief Semanal está listo para:

- **El Guionista** (`/viral:script`): Convierte hooks en guiones
- **El Analista** (`/viral:analyze`): Mide performance real vs predicción

---

## Troubleshooting

### Error: "Hooks DB vacía"

```
❌ Hooks DB vacía — ejecuta /viral:discover primero
```

**Causa:** PASO 1 no encontró hooks de la semana actual.

**Solución:**
1. Ejecutar `/viral:discover` primero
2. Verificar que hay URLs en "Estado = Pendiente"

### Error: "Sin historial propio"

```
⚠️ Mis Posts vacío — no hay data propia para scoring
```

**Causa:** Primera ejecución, sin posts previos.

**Solución:** Es normal. El scoring será más genérico. Después de publicar, tendrá más data.

### Tema con score negativo

```
Tema: Tecnico IA
Score: -2.5  ← DESCARTADO
```

**Causa:** Tono muy técnico (-3) sin compensar con otros criterios.

**Solución:** Sistema funciona correctamente — evita temas demasiado especializados.

---

## Métricas de Éxito

✅ Script ejecuta sin errores  
✅ Lee correctamente de Hooks DB  
✅ Analiza Mis Posts (historial)  
✅ Agrupa hooks por tema  
✅ Calcula scores con 7 criterios  
✅ Selecciona top 3 temas  
✅ Escribe Brief Semanal en Notion  
✅ Output terminal es claro y accionable  

---

## Diferencia: Sabueso vs Estratega

| Aspecto | Sabueso | Estratega |
|---------|---------|-----------|
| **Input** | URLs de competidores | Hooks DB (Sabueso output) |
| **Output** | Hooks DB | Brief Semanal |
| **Lógica** | Scraping + clasificación | Agrupación + scoring |
| **Contexto** | Datos externos | Datos propios + externos |
| **Decisión** | Todos los hooks ganadores | Top 3 temas para producir |

---

## Notas Técnicas

- **Agrupación:** Simple basada en keywords (business/ia/growth)
- **Scoring:** 7 criterios, min -3, máx +10
- **Deduplicación:** Automática por tema similar
- **Semana ISO:** `date.today().isocalendar()[1]`
- **Notion write:** Una página por semana
