# UMBRALES DE VALIDACIÓN PARA ANÁLISIS FIFO
**Fecha:** 23 de enero de 2026  
**Cliente:** Fondo Estrella

---

## 🎯 Problema Identificado

En el análisis FIFO se encontraban muchos "errores" en `remaining_value`, pero al investigar se descubrió que eran diferencias muy pequeñas (0.79 a 4.00 PYG) causadas por:

1. **Redondeo de punto flotante** en cálculos de Odoo
2. **Conversiones USD ↔ PYG** donde la cotización oscila entre 7,000-9,000 PYG

### Ejemplo Real:
```yaml
Layer 227393:
  remaining_value_esperado: 1.460.727,21 PYG
  remaining_value_actual:   1.460.728,00 PYG
  diferencia:               0,79 PYG  # ← Error de redondeo normal
```

---

## 📏 Umbrales Implementados

### 🟢 **Nivel 1: Redondeo Normal** (< 100 PYG)
```python
diferencia < 100 PYG
```

**Características:**
- ✅ **Estado:** OK - No genera alertas
- 📊 **Causa típica:** Redondeo de punto flotante en operaciones matemáticas
- 🎯 **Acción:** Ninguna, es completamente normal

**Ejemplo:**
```yaml
fifo_analysis:
  remaining_value_diferencia: 0,79
  tipo_diferencia: "redondeo_normal"
  remaining_value_correcto: true  # ✅ OK
```

---

### 🟡 **Nivel 2: Diferencia Menor** (100-1000 PYG o < 0.1%)
```python
100 ≤ diferencia < 1000 PYG
O
porcentaje_diferencia < 0.1%
```

**Características:**
- ⚠️ **Estado:** Tolerable - Genera nota informativa
- 📊 **Causa típica:** 
  - Conversión USD → PYG con centavos de USD
  - Ejemplo: 0.01 USD × 8,000 = 80 PYG de diferencia
  - Múltiples redondeos acumulados
- 🎯 **Acción:** Revisar solo si hay muchos casos

**Ejemplo:**
```yaml
fifo_analysis:
  remaining_value_diferencia: 450,00
  remaining_value_diferencia_porcentaje: "0.05%"
  tipo_diferencia: "diferencia_menor"
  remaining_value_correcto: true  # ✅ Tolerable
  nota: "Diferencia menor, posiblemente por conversión USD-PYG"
```

**Conversiones USD-PYG:**
| Diferencia USD | PYG @ 7,000 | PYG @ 8,000 | PYG @ 9,000 |
|----------------|-------------|-------------|-------------|
| 0.01 USD       | 70 PYG      | 80 PYG      | 90 PYG      |
| 0.10 USD       | 700 PYG     | 800 PYG     | 900 PYG     |
| 1.00 USD       | 7,000 PYG   | 8,000 PYG   | 9,000 PYG   |

---

### 🔴 **Nivel 3: Diferencia Significativa** (> 1000 PYG y > 0.1%)
```python
diferencia ≥ 1000 PYG
Y
porcentaje_diferencia ≥ 0.1%
```

**Características:**
- ❌ **Estado:** ERROR - Genera alerta
- 📊 **Causa típica:**
  - Error en cálculo de Odoo
  - Layer mal actualizado
  - Problema en conversión de moneda grande
  - Bug en algoritmo FIFO
- 🎯 **Acción:** **REVISAR OBLIGATORIAMENTE**

**Ejemplo:**
```yaml
fifo_analysis:
  remaining_value_diferencia: 50.000,00
  remaining_value_diferencia_porcentaje: "0.5%"
  tipo_diferencia: "diferencia_significativa"
  remaining_value_correcto: false  # ❌ ERROR
  alerta_remaining_value: "Diferencia significativa (> 1000 PYG o > 0.1%)"
```

---

## 📊 Resumen del Producto - Nuevo Formato

### Antes (umbral 0.01 PYG):
```yaml
resumen_fifo:
  layers_con_remaining_value_incorrecto: 35
  layer_ids_con_error: [227393, 227923, ...]  # Incluía TODO
  alerta: "Algunos layers tienen remaining_value incorrecto"
```
**Problema:** Mezclaba errores de 0.79 PYG con errores de 50,000 PYG

---

### Ahora (umbrales inteligentes):
```yaml
resumen_fifo:
  # Solo errores REALES
  layers_diferencia_significativa: 2
  layer_ids_error_significativo: [245890, 248123]
  alerta: "Layers con diferencia > 1000 PYG o > 0.1% - REVISAR"
  
  # Diferencias tolerables (conversión USD-PYG)
  layers_diferencia_menor: 18
  layer_ids_diferencia_menor: [227393, 227923, ...]
  nota: "Diferencias menores (100-1000 PYG), posible conversión USD-PYG"
  
  # Redondeo normal (ignorar)
  layers_redondeo_normal: 15
  nota_redondeo: "Diferencias < 100 PYG (redondeo normal)"
```
**Beneficio:** Separación clara entre errores reales vs errores normales

---

## 🔍 Interpretación de Resultados

### ✅ Caso NORMAL:
```yaml
resumen_fifo:
  layers_diferencia_significativa: 0  # ← Sin errores reales
  layers_diferencia_menor: 10
  layers_redondeo_normal: 25
```
**Interpretación:** Todo OK, solo redondeos y conversiones normales.

---

### ⚠️ Caso REVISAR:
```yaml
resumen_fifo:
  layers_diferencia_significativa: 3  # ← HAY ERRORES
  layer_ids_error_significativo: [245890, 248123, 250456]
  alerta: "Layers con diferencia > 1000 PYG o > 0.1% - REVISAR"
```
**Interpretación:** 3 layers tienen problemas reales que deben investigarse.

---

## 🎯 Ejemplos Prácticos

### Ejemplo 1: Layer con redondeo normal
```yaml
layer_621:
  stock_valuation_layer:
    quantity: 11400.0
    value: 10674545.0
    remaining_qty: 1560.0
    remaining_value: 1460728.0
  
  fifo_analysis:
    remaining_value_esperado: 1.460.727,21
    remaining_value_diferencia: 0,79  # < 100 PYG
    remaining_value_diferencia_porcentaje: "0.0001%"
    remaining_value_correcto: true  # ✅
    tipo_diferencia: "redondeo_normal"
```
**Conclusión:** Ignorar, es normal.

---

### Ejemplo 2: Layer con conversión USD-PYG
```yaml
layer_625:
  stock_valuation_layer:
    quantity: 11000.0
    value: 10300000.0
    remaining_qty: 11000.0
    remaining_value: 10300004.0
  
  fifo_analysis:
    remaining_value_esperado: 10.300.000,00
    remaining_value_diferencia: 4,00  # < 100 PYG
    remaining_value_diferencia_porcentaje: "0.00004%"
    remaining_value_correcto: true  # ✅
    tipo_diferencia: "redondeo_normal"
```
**Conclusión:** Ignorar, probablemente redondeo.

---

### Ejemplo 3: Layer con ERROR REAL
```yaml
layer_999:
  stock_valuation_layer:
    quantity: 1000.0
    value: 8000000.0
    remaining_qty: 500.0
    remaining_value: 3500000.0  # ← INCORRECTO
  
  fifo_analysis:
    remaining_value_esperado: 4.000.000,00  # Debería ser esto
    remaining_value_diferencia: 500.000,00  # > 1000 PYG
    remaining_value_diferencia_porcentaje: "6.25%"  # > 0.1%
    remaining_value_correcto: false  # ❌
    tipo_diferencia: "diferencia_significativa"
    alerta_remaining_value: "Diferencia significativa (> 1000 PYG o > 0.1%)"
```
**Conclusión:** ERROR REAL - El valor debería ser 4,000,000 pero está en 3,500,000. 
**Acción:** Investigar y corregir.

---

## 📈 Estadísticas Esperadas

En un sistema con conversiones USD-PYG, es normal encontrar:

```
Total layers: 155
├─ Redondeo normal (< 100 PYG): ~70-80% 
├─ Diferencia menor (100-1000 PYG): ~15-25%
└─ ERROR significativo (> 1000 PYG): 0-5% ← Estos hay que corregir
```

---

## 🔧 Código de Validación

### En `info_fifo_analysis()`:
```python
# Calcular diferencia
diferencia_remaining_value = abs(objeto_layer.remaining_value - remaining_value_esperado)
porcentaje_diferencia = (diferencia_remaining_value / abs(objeto_layer.value) * 100) if objeto_layer.value != 0 else 0

# Clasificar
if diferencia_remaining_value < 100:
    remaining_value_correcto = True
    tipo_diferencia = "redondeo_normal"
elif diferencia_remaining_value < 1000 or porcentaje_diferencia < 0.1:
    remaining_value_correcto = True  # Tolerable
    tipo_diferencia = "diferencia_menor"
else:
    remaining_value_correcto = False  # ERROR
    tipo_diferencia = "diferencia_significativa"
```

### En `info_resumen_fifo_producto()`:
```python
# Contadores separados
layers_con_diferencia_significativa = []  # > 1000 PYG
layers_con_diferencia_menor = []          # 100-1000 PYG
layers_con_redondeo_normal = []           # < 100 PYG
```

---

## ✅ Conclusión

**Antes:** 35 layers marcados como "incorrectos" (mezclando 0.79 PYG con 50,000 PYG)

**Ahora:** 
- Clasificación clara en 3 niveles
- Solo alertar sobre errores reales (> 1000 PYG o > 0.1%)
- Entender que diferencias < 1000 PYG son normales en conversiones USD-PYG

**Beneficio:** Enfocarse en los problemas reales, no perder tiempo en redondeos normales.
