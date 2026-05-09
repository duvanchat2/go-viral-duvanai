# 📊 El Analista — Agente 5: Análisis de Performance Real

**Estado:** ✅ Implementado y testeado  
**Rama:** `claude/notion-database-setup-V7Psu`  
**Script principal:** `scripts/analista.py`  
**Test:** `scripts/test_analista_mock.py`

---

## ¿Qué hace el Analista?

El Analista es el quinto y último agente del sistema **go-viral**. Su trabajo es **cerrar el loop**:

1. **Leer** posts ya publicados (semana anterior)
2. **Medir** rendimiento real vs predicción del Estratega
3. **Detectar causas** de fracasos
4. **Actualizar** Brief Semanal con aprendizajes
5. **Mejorar** scoring del Estratega para la próxima semana

**Flujo completo:**

```
Mis Posts (Publicados) → Calcular Like Rate → Clasificar → Detectar Causas → Actualizar Brief + Hooks DB
(Input)                  (Métricas)           (3 categorías) (Diagnóstico)   (Feedback Loop)
```

---

## Instalación

### Requisitos

Mismo que otros agentes:
- `.env` con `NOTION_API_KEY`
- `requirements.txt` ya instalado

---

## Ejecución

### Ejecución estándar

```bash
python3 scripts/analista.py
```

Analiza posts publicados de la **semana anterior** (semana ISO actual - 1).

### Con flags (opcionales)

```bash
# Analizar semana específica
python3 scripts/analista.py --week 18

# Ver qué haría sin escribir en Notion
python3 scripts/analista.py --dry-run

# Combinados
python3 scripts/analista.py --week 18 --dry-run
```

### Test Mock (sin credenciales)

```bash
python3 scripts/test_analista_mock.py
```

---

## Los 6 Pasos del Flujo

### PASO 1: Leer Mis Posts Publicados

Filtra posts con `Estado = "Publicado"` y `Semana = semana_anterior`.

### PASO 2: Calcular Métricas Reales

```
like_rate_real = (likes / views) * 100
```

### PASO 3: Clasificar Rendimiento

- **OUTLIER_POSITIVO:** like_rate ≥ 5%
- **NORMAL:** 3% ≤ like_rate < 5%
- **FALLIDO:** like_rate < 2% OR views < 50

### PASO 4: Detectar Causas (Fallidos)

- CAPTION_DESCRIPTIVA: detecta palabras prohibidas
- DURACION_EXCEDIDA: supera límite del formato
- ALGORITMO_NO_DISTRIBUYO: views < 50

### PASO 5: Actualizar Brief Semanal

Escribe aprendizajes en `Funciono` / `No funciono` y marca como `Completado`.

### PASO 6: Actualizar Hooks DB

Si post propio y OUTLIER_POSITIVO, actualiza Like Rate real en Hooks DB.

---

## Output en Terminal

```
ANALISTA — SEMANA 18
====================

POSTS ANALIZADOS: 3

OUTLIERS POSITIVOS ✅
  ✅ "No hagas esto..." — 4.92% — Patrón 1

POSTS NORMALES ➡️
  ➡️  "3x tu productividad..." — 3.50%

POSTS FALLIDOS ❌
  ❌ "Lo que nadie te dice..." — 1.20%
     Causas: CAPTION_DESCRIPTIVA

IMPACTO EN SCORING PRÓXIMA SEMANA
  Patrón 1 ↑ (funcionó — +2)
  Patrón 3 ↓ (falló — -1)

✅ ACTUALIZADO EN NOTION
→ Loop cerrado.
```

---

## Métricas de Éxito

✅ Lee posts publicados  
✅ Calcula like rate real  
✅ Clasifica en 3 categorías  
✅ Detecta causas automáticamente  
✅ Actualiza Brief + Hooks DB  
✅ Output accionable  

