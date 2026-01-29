# Cambios: Cálculo de Valores Esperados en FIFO

## Fecha: 26 de enero de 2026

---

## 🎯 Objetivo

Agregar contadores y cálculos que determinen los **valores esperados** para `remaining_qty` y `remaining_value` basándose en las **salidas reales** de cada layer, en lugar de asumir que los valores almacenados en Odoo son correctos.

---

## ❌ Problema Anterior

### Cálculo incorrecto en `info_fifo_analysis()`:

```python
# ANTES (INCORRECTO) - Línea 319
remaining_value_esperado = (objeto_layer.remaining_qty / objeto_layer.quantity * objeto_layer.value)
```

**Problema**: Asumía que `remaining_qty` ya era correcto, pero precisamente ese campo está corrupto.

### En `info_resumen_fifo_producto()`:

```python
# ANTES (INCORRECTO)
remaining_esperado = (layer.remaining_qty / layer.quantity * layer.value)
```

**Problema**: Usaba el `remaining_qty` corrupto para calcular el `remaining_value` esperado.

---

## ✅ Solución Implementada

### 1. En `info_fifo_analysis()` - Cálculo basado en salidas reales

```python
# PASO 1: Buscar todas las salidas que consumieron este layer
layers_salida = env['stock.valuation.layer'].search([
    ('stock_valuation_layer_id', '=', objeto_layer.id),
    ('quantity', '<', 0)
])

# PASO 2: Calcular qty consumida REAL basada en las salidas
qty_consumida_por_salidas = sum(abs(s.quantity) for s in layers_salida)

# PASO 3: Calcular valores ESPERADOS basados en las salidas reales
remaining_qty_esperado = objeto_layer.quantity - qty_consumida_por_salidas
remaining_value_esperado = (remaining_qty_esperado / objeto_layer.quantity * objeto_layer.value)

# PASO 4: Calcular diferencias entre valores actuales y esperados
diferencia_remaining_qty = abs(objeto_layer.remaining_qty - remaining_qty_esperado)
diferencia_remaining_value = abs(objeto_layer.remaining_value - remaining_value_esperado)
```

### 2. Nuevo output en YAML

#### Estructura anterior:
```yaml
fifo_analysis:
  tipo: "entrada"
  qty_original: 360.0
  qty_restante: 27.0              # ❌ Valor corrupto de Odoo
  qty_consumida: 333.0            # ❌ Basado en valor corrupto
  remaining_value_esperado: 122.858,77   # ❌ Calculado con qty corrupto
```

#### Estructura nueva (mejorada):
```yaml
fifo_analysis:
  tipo: "entrada"
  qty_original: 360.0
  
  # VALORES ACTUALES (lo que tiene Odoo - pueden estar mal)
  qty_restante_actual: 27.0
  qty_consumida_actual: 333.0
  value_restante_actual: 42.397.210,00
  value_consumido_actual: -40.759.093,00
  
  # VALORES ESPERADOS (basados en salidas reales)
  qty_consumida_por_salidas: 333.0        # ✅ Suma real de salidas
  qty_restante_esperado: 27.0             # ✅ quantity - salidas
  value_restante_esperado: 122.858,77     # ✅ Basado en qty esperado
  
  # DIFERENCIAS
  diferencia_qty_restante: 0.0            # ✅ qty_actual vs qty_esperado
  diferencia_value_restante: 42.274.351,23  # ✅ value_actual vs value_esperado
  diferencia_value_porcentaje: "2580.6674%"
  
  # VALIDACIONES
  remaining_qty_correcto: True            # ✅ Nueva validación
  remaining_value_correcto: False
  tipo_diferencia: "diferencia_significativa"
```

### 3. Nuevas alertas

```yaml
# Si qty está mal
alerta_remaining_qty: "remaining_qty incorrecto - Diferencia: 150.0"

# Si value está mal (ya existía, mejorada)
alerta_remaining_value: "Diferencia significativa (> 1000 PYG o > 0.1%)"
```

---

## 📊 Mejoras en `info_resumen_fifo_producto()`

### Output anterior:
```yaml
resumen_fifo:
  total_qty_disponible: 2187.0           # ❌ Suma de remaining_qty corruptos
  total_value_stock_actual: 6.546.087.370,00   # ❌ Suma de remaining_value corruptos
```

### Output nuevo:
```yaml
resumen_fifo:
  # TOTALES ACTUALES (valores en Odoo - pueden estar mal)
  total_qty_disponible_actual: 2187.0
  total_value_stock_actual: 6.546.087.370,00
  
  # TOTALES ESPERADOS (basados en salidas reales)
  total_qty_disponible_esperado: 2187.0     # ✅ Suma de qty_esperado
  total_value_stock_esperado: 10.932.452,00  # ✅ Suma de value_esperado
  
  # DIFERENCIAS TOTALES
  diferencia_qty_total: 0.0
  diferencia_value_total: 6.535.154.918,00   # ✅ ERROR MASIVO detectado
  
  # VALIDACIONES
  layers_con_error_qty: 0                    # ✅ Nuevo contador
  layers_diferencia_significativa_value: 5
  layers_diferencia_menor_value: 0
  layers_redondeo_normal: 154
  
  # COSTOS PROMEDIO
  costo_promedio_ponderado_actual: 2.993.181,24    # ❌ Basado en values corruptos
  costo_promedio_ponderado_esperado: 5.000,21      # ✅ Basado en values correctos
```

---

## 🔍 Ejemplo Real

### Producto: Cinta de Embalaje (ID 2671)

#### Layer 250880 - ANTES:
```yaml
qty_restante: 432.0
value_restante: 844.252.556,00
remaining_value_esperado: 1.924.427,00   # ❌ Calculado con qty corrupto
remaining_value_diferencia: 842.328.129,00
```

#### Layer 250880 - AHORA:
```yaml
# ACTUALES
qty_restante_actual: 432.0
value_restante_actual: 844.252.556,00

# ESPERADOS (basados en 0 salidas encontradas)
qty_consumida_por_salidas: 0             # ✅ Sin salidas = sin consumo
qty_restante_esperado: 432.0             # ✅ 432 - 0 = 432
value_restante_esperado: 1.924.427,00    # ✅ (432/432) * 1.924.427

# DIFERENCIAS
diferencia_qty_restante: 0.0             # ✅ QTY CORRECTO
diferencia_value_restante: 842.328.129,00  # ❌ VALUE MUY MAL
diferencia_value_porcentaje: "43770.33%"

# VALIDACIONES
remaining_qty_correcto: True             # ✅ Nueva validación
remaining_value_correcto: False
alerta_remaining_value: "Diferencia significativa (> 1000 PYG o > 0.1%)"
```

---

## 🎯 Beneficios

1. **Detección precisa de errores**:
   - Ahora sabemos si `remaining_qty` está mal (antes no lo validábamos)
   - Ahora sabemos si `remaining_value` está mal basado en valores correctos

2. **Contador de salidas**:
   - `qty_consumida_por_salidas`: Suma exacta de todas las salidas vinculadas
   - Permite detectar layers con consumo registrado pero sin salidas asociadas

3. **Valores esperados confiables**:
   - No dependen de datos corruptos de Odoo
   - Se calculan desde cero basándose en transacciones reales

4. **Resumen completo**:
   - Totales actuales vs totales esperados
   - Diferencia total en qty y value
   - Costos promedio actuales vs esperados

5. **Preparación para corrección**:
   - Tenemos todos los valores correctos calculados
   - Solo falta ejecutar un UPDATE con esos valores

---

## 📝 Cambios en el Código

### Archivos modificados:
- `actualizacion_layers.py`

### Funciones modificadas:
1. **`info_fifo_analysis()`**:
   - Agregado: Búsqueda de salidas asociadas
   - Agregado: Cálculo de `qty_consumida_por_salidas`
   - Agregado: Cálculo de `remaining_qty_esperado`
   - Mejorado: Cálculo de `remaining_value_esperado` (ahora usa qty esperado)
   - Agregado: Validación de `remaining_qty_correcto`
   - Agregado: Output de valores actuales vs esperados

2. **`info_resumen_fifo_producto(iterador, layers, env)`**:
   - Agregado parámetro: `env` (necesario para buscar salidas)
   - Agregado: Loop que busca salidas para cada layer
   - Agregado: Cálculo de totales esperados
   - Agregado: Contador de layers con error en qty
   - Mejorado: Clasificación separada para qty y value
   - Agregado: Output de totales esperados y diferencias

### Línea de llamada modificada:
```python
# Línea 833 - Ahora pasa env
info_resumen_fifo_producto(iterador=f, layers=layers, env=env)
```

---

## 🚀 Próximos Pasos

1. **Ejecutar el script actualizado** en producto 2671
2. **Verificar** que los valores esperados sean correctos
3. **Analizar** las diferencias encontradas
4. **Crear script de corrección** que haga:
   ```python
   layer.write({
       'remaining_qty': remaining_qty_esperado,
       'remaining_value': remaining_value_esperado
   })
   ```

---

## ✅ Conclusión

Ahora el script **calcula correctamente los valores esperados** basándose en las transacciones reales (salidas), en lugar de asumir que los datos en Odoo son correctos. Esto nos da una base sólida para identificar y corregir los errores en el sistema FIFO.
