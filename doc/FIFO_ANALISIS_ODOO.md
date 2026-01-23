# ANÁLISIS PROFUNDO: SISTEMA FIFO EN ODOO
**Fecha:** 23 de enero de 2026  
**Cliente:** Fondo Estrella  
**Objetivo:** Entender FIFO para reprocesar valoraciones y asientos contables

---

## 1. DIFERENCIAS FUNDAMENTALES: AVERAGE vs FIFO

### 1.1 AVERAGE (Coste Promedio - AVCO)
```
Funcionamiento:
- Cada compra actualiza el costo promedio del producto
- Todas las unidades en stock tienen el mismo costo unitario
- Formula: Nuevo Costo = (Valor Total Stock + Valor Nueva Compra) / (Cantidad Total + Cantidad Nueva)

Stock Valuation Layer:
- Se crea UN SOLO layer por movimiento de entrada
- quantity: cantidad recibida
- value: valor total de la entrada
- unit_cost: costo unitario calculado
- remaining_qty: NO SE USA (siempre 0 o igual a quantity)
- remaining_value: NO SE USA (siempre 0 o igual a value)
```

### 1.2 FIFO (Primeras Entradas, Primeras Salidas)
```
Funcionamiento:
- Cada compra se registra como una "capa" independiente con su costo específico
- Las salidas consumen layers en orden cronológico (primero lo más antiguo)
- Cada layer mantiene su identidad y costo original
- Las unidades tienen costos diferentes según la capa de la que provienen

Stock Valuation Layer - CAMPOS CRÍTICOS PARA FIFO:
┌─────────────────┬──────────────────────────────────────────────────────┐
│ CAMPO           │ DESCRIPCIÓN EN FIFO                                  │
├─────────────────┼──────────────────────────────────────────────────────┤
│ quantity        │ Cantidad TOTAL que ingresó en este layer            │
│ value           │ Valor TOTAL de lo que ingresó                        │
│ unit_cost       │ Costo unitario de esta capa específica              │
│ remaining_qty   │ ⭐ Cantidad que AÚN QUEDA de este layer             │
│ remaining_value │ ⭐ Valor que AÚN QUEDA de este layer                │
└─────────────────┴──────────────────────────────────────────────────────┘

⭐ CAMPOS CLAVE: remaining_qty y remaining_value son ESENCIALES en FIFO
   - Se van reduciendo conforme las salidas consumen este layer
   - Cuando remaining_qty = 0, el layer está completamente consumido
```

---

## 2. ESTRUCTURA DE LAYERS EN FIFO

### 2.1 Layers de ENTRADA (quantity > 0)
```python
# Ejemplo: Compra de 100 unidades a $10 c/u
layer_entrada = {
    'product_id': 123,
    'quantity': 100.0,           # Cantidad que entró
    'unit_cost': 10.0,           # Costo unitario de esta compra
    'value': 1000.0,             # Valor total (100 * 10)
    'remaining_qty': 100.0,      # Al inicio, todo está disponible
    'remaining_value': 1000.0,   # Al inicio, todo el valor está disponible
    'description': 'Recepción PO001',
    'stock_move_id': 456,
    'account_move_line_id': 789  # Línea de factura del proveedor
}
```

### 2.2 Layers de SALIDA (quantity < 0)
```python
# Ejemplo: Venta/consumo de 60 unidades (consume del layer más antiguo)
layer_salida = {
    'product_id': 123,
    'quantity': -60.0,                    # Cantidad que salió (negativa)
    'unit_cost': 10.0,                    # Costo del layer que se consumió
    'value': -600.0,                      # Valor que salió (negativo)
    'remaining_qty': 0.0,                 # Las salidas no tienen remaining
    'remaining_value': 0.0,
    'description': 'Entrega SO005',
    'stock_move_id': 457,
    'stock_valuation_layer_id': layer_entrada.id  # ⭐ Referencia al layer consumido
}

# EFECTO EN EL LAYER DE ENTRADA:
layer_entrada_actualizado = {
    'remaining_qty': 40.0,       # 100 - 60 = 40 unidades quedan
    'remaining_value': 400.0,    # 1000 - 600 = 400 valor restante
    # quantity, value, unit_cost NO CAMBIAN (son históricos)
}
```

### 2.3 VISUALIZACIÓN DEL FLUJO FIFO

```
CRONOLOGÍA DE LAYERS:
════════════════════════════════════════════════════════════════

Día 1: Compra A - 100 unidades @ $10
┌─────────────────────────────────────────┐
│ Layer 1 (Entrada)                       │
│ qty: 100 | remaining_qty: 100           │
│ value: $1,000 | remaining: $1,000       │
└─────────────────────────────────────────┘

Día 5: Compra B - 50 unidades @ $12
┌─────────────────────────────────────────┐
│ Layer 1 (Entrada)                       │
│ remaining_qty: 100 | remaining: $1,000  │
├─────────────────────────────────────────┤
│ Layer 2 (Entrada)                       │
│ qty: 50 | remaining_qty: 50             │
│ value: $600 | remaining: $600           │
└─────────────────────────────────────────┘

Día 10: Venta - 120 unidades
┌─────────────────────────────────────────┐
│ Layer 1 (Entrada)                       │
│ remaining_qty: 0 ← CONSUMIDO TOTALMENTE │
├─────────────────────────────────────────┤
│ Layer 2 (Entrada)                       │
│ remaining_qty: 30 (50-20)               │
│ remaining: $360 ($600 - $240)           │
├─────────────────────────────────────────┤
│ Layer 3 (Salida) qty: -100              │
│ referencia → Layer 1                    │
├─────────────────────────────────────────┤
│ Layer 4 (Salida) qty: -20               │
│ referencia → Layer 2                    │
└─────────────────────────────────────────┘

STOCK FINAL: 30 unidades @ $12 c/u = $360
```

---

## 3. CAMPOS RELEVANTES EN STOCK.VALUATION.LAYER PARA FIFO

```python
# Modelo: stock.valuation.layer
campos_fifo = {
    # BÁSICOS (Comunes con AVERAGE)
    'id': 'ID único del layer',
    'product_id': 'Producto al que pertenece',
    'company_id': 'Compañía',
    'create_date': 'Fecha de creación del layer',
    
    # CANTIDADES Y VALORES
    'quantity': 'Cantidad total del movimiento (+entrada / -salida)',
    'unit_cost': 'Costo unitario en este layer',
    'value': 'Valor total (quantity * unit_cost)',
    
    # ⭐ CAMPOS ESPECÍFICOS FIFO (LOS MÁS IMPORTANTES)
    'remaining_qty': 'Cantidad que aún queda disponible de este layer',
    'remaining_value': 'Valor que aún queda disponible',
    
    # REFERENCIAS
    'stock_move_id': 'Movimiento de stock que generó este layer',
    'account_move_id': 'Asiento contable asociado',
    'account_move_line_id': 'Línea específica del asiento',
    
    # REFERENCIAS FIFO (pueden existir según versión)
    'stock_valuation_layer_id': 'Layer padre (para salidas, referencia al layer consumido)',
    
    # DESCRIPTIVOS
    'description': 'Descripción del movimiento',
    'price_diff_value': 'Diferencia de precio (ej: en devoluciones)',
}
```

---

## 4. RELACIONES CLAVE EN FIFO

### 4.1 Cadena de Trazabilidad
```
purchase.order (Orden de Compra)
    ↓
purchase.order.line (Línea de OC)
    ↓
stock.move (Movimiento de recepción)
    ↓
stock.valuation.layer (Layer de entrada con remaining_qty)
    ↓ [cuando hay salida]
stock.valuation.layer (Layer de salida que consume el anterior)
    ↓
account.move.line (Asiento contable de la operación)
```

### 4.2 Búsqueda de Layers FIFO por Producto
```python
# Layers de ENTRADA con stock disponible (ordenados por antigüedad)
layers_disponibles = env['stock.valuation.layer'].search([
    ('product_id', '=', product_id),
    ('quantity', '>', 0),              # Solo entradas
    ('remaining_qty', '>', 0),         # ⭐ Que tengan stock disponible
], order='create_date asc')            # ⭐ Más antiguos primero (FIFO)

# Layers de SALIDA
layers_salidas = env['stock.valuation.layer'].search([
    ('product_id', '=', product_id),
    ('quantity', '<', 0),              # Solo salidas
], order='create_date desc')
```

---

## 5. PROBLEMAS COMUNES EN FIFO

### 5.1 Inconsistencias en Layers de Entrada
```yaml
PROBLEMA 1: Unit_cost incorrecto en layer vs factura real
─────────────────────────────────────────────────────────
Síntoma:
  layer.unit_cost = 100.00 USD
  invoice.price_unit = 5,500,000 PYG (≈ 100 USD pero mal calculado)
  
Causa:
  - Conversión de moneda incorrecta en el momento de la recepción
  - Factura recibida después de la recepción con precio diferente
  - Error manual en precio de OC
  
Impacto en FIFO:
  - Todas las salidas que consuman este layer tendrán costo incorrecto
  - remaining_value será incorrecto
  - Asientos contables descuadrados
  
Solución:
  1. Corregir unit_cost y value del layer de entrada
  2. Recalcular remaining_value = remaining_qty * unit_cost_correcto
  3. ⚠️ Si ya hubo salidas, hay que recalcular TODOS los layers de salida
```

### 5.2 Layers huérfanos o sin factura
```yaml
PROBLEMA 2: Layer de entrada sin account_move_line_id
─────────────────────────────────────────────────────
Síntoma:
  layer.stock_move_id → purchase_line_id: OK
  layer.account_move_line_id: False o NULL
  
Causa:
  - Recepción confirmada pero factura no registrada
  - Factura cancelada o borrada
  - Error en proceso de facturación
  
Impacto:
  - No hay trazabilidad contable
  - Costo puede estar basado en precio de OC (no precio real de factura)
  
Identificación:
  layers_sin_factura = search([
      ('quantity', '>', 0),
      ('account_move_line_id', '=', False)
  ])
```

### 5.3 Remaining_qty negativo o incorrecto
```yaml
PROBLEMA 3: remaining_qty < 0 o descuadrado
───────────────────────────────────────────
Síntoma:
  layer.quantity = 100
  sum(salidas que lo consumieron) = 110
  layer.remaining_qty = -10  ← IMPOSIBLE
  
Causa:
  - Bug en algoritmo de consumo FIFO
  - Ajustes manuales de inventario mal procesados
  - Devoluciones mal contabilizadas
  
Solución:
  Recalcular remaining_qty:
  remaining_qty = quantity - sum(cantidades_consumidas_en_salidas)
```

---

## 6. ALGORITMO DE CORRECCIÓN PARA FIFO

### 6.1 Estrategia Recomendada

```python
"""
PASO 1: AUDITORÍA DE LAYERS DE ENTRADA
───────────────────────────────────────
Para cada producto FIFO:
  1. Buscar todos los layers con quantity > 0
  2. Para cada layer:
     a. Verificar que tiene stock_move_id
     b. Verificar que stock_move tiene purchase_line_id
     c. Buscar account_move_line asociado a esa purchase_line
     d. Comparar:
        - layer.unit_cost vs invoice.price_unit (convertido a moneda base)
        - layer.value vs invoice.balance
     e. Registrar discrepancias en YAML
"""

def analizar_layer_entrada_fifo(layer, output_file):
    # Datos del layer actual
    layer_data = {
        'quantity': layer.quantity,
        'unit_cost': layer.unit_cost,
        'value': layer.value,
        'remaining_qty': layer.remaining_qty,
        'remaining_value': layer.remaining_value
    }
    
    # Buscar factura
    stock_move = layer.stock_move_id
    if not stock_move:
        return "SIN_STOCK_MOVE"
    
    purchase_line = stock_move.purchase_line_id
    if not purchase_line:
        return "SIN_PURCHASE_LINE"
    
    # Buscar invoice line
    invoice_line = env['account.move.line'].search([
        ('purchase_line_id', '=', purchase_line.id),
        ('move_id.move_type', '=', 'in_invoice'),
        ('move_id.state', '=', 'posted')  # Solo facturas confirmadas
    ], limit=1)
    
    if not invoice_line:
        return "SIN_FACTURA"
    
    # Datos de la factura (en moneda base)
    invoice_data = {
        'quantity': invoice_line.quantity,
        'balance': abs(invoice_line.balance),
        'price_unit': abs(invoice_line.balance / invoice_line.quantity) if invoice_line.quantity else 0
    }
    
    # Análisis de diferencias
    diferencia_value = abs(layer_data['value'] - invoice_data['balance'])
    diferencia_unit_cost = abs(layer_data['unit_cost'] - invoice_data['price_unit'])
    
    # ⭐ CLASIFICACIÓN
    if diferencia_value > 1000:  # Umbral a ajustar
        return {
            'status': 'REQUIERE_CORRECCION_GRANDE',
            'layer_data': layer_data,
            'invoice_data': invoice_data,
            'diferencia_value': diferencia_value,
            'diferencia_unit_cost': diferencia_unit_cost
        }
    elif diferencia_value > 0.01:
        return {
            'status': 'REQUIERE_CORRECCION_PEQUEÑA',
            'layer_data': layer_data,
            'invoice_data': invoice_data,
            'diferencia_value': diferencia_value
        }
    else:
        return {
            'status': 'CORRECTO',
            'layer_data': layer_data,
            'invoice_data': invoice_data
        }

"""
PASO 2: VALIDACIÓN DE REMAINING_QTY
────────────────────────────────────
⭐ IMPORTANTE: En FIFO, remaining_qty debe ser exacto
"""

def validar_remaining_qty_fifo(layer):
    # Buscar todas las salidas que consumieron este layer
    layers_salida = env['stock.valuation.layer'].search([
        ('stock_valuation_layer_id', '=', layer.id),
        ('quantity', '<', 0)
    ])
    
    cantidad_consumida = sum(abs(l.quantity) for l in layers_salida)
    remaining_esperado = layer.quantity - cantidad_consumida
    
    if abs(layer.remaining_qty - remaining_esperado) > 0.001:
        return {
            'status': 'REMAINING_QTY_INCORRECTO',
            'remaining_actual': layer.remaining_qty,
            'remaining_esperado': remaining_esperado,
            'diferencia': layer.remaining_qty - remaining_esperado
        }
    
    return {'status': 'OK'}

"""
PASO 3: CORRECCIÓN DE LAYERS
─────────────────────────────
⚠️ CUIDADO: En FIFO, corregir un layer de entrada puede afectar a las salidas
"""

def corregir_layer_fifo(layer, invoice_line, modo='dry_run'):
    """
    Corrige un layer FIFO con los datos de la factura
    
    Args:
        layer: stock.valuation.layer a corregir
        invoice_line: account.move.line con datos correctos
        modo: 'dry_run' (solo simular) o 'apply' (aplicar cambios)
    """
    # Calcular valores correctos
    unit_cost_correcto = abs(invoice_line.balance / invoice_line.quantity)
    value_correcto = abs(invoice_line.balance)
    
    # ⭐ CLAVE EN FIFO: Actualizar remaining_value proporcionalmente
    proporcion_restante = layer.remaining_qty / layer.quantity if layer.quantity else 0
    remaining_value_correcto = value_correcto * proporcion_restante
    
    valores_nuevos = {
        'unit_cost': unit_cost_correcto,
        'value': value_correcto,
        'remaining_value': remaining_value_correcto
        # remaining_qty NO se toca (es correcto por las salidas)
    }
    
    if modo == 'apply':
        layer.write(valores_nuevos)
        return {'status': 'CORREGIDO', 'valores': valores_nuevos}
    else:
        return {'status': 'SIMULADO', 'valores': valores_nuevos}
```

---

## 7. FORMATO YAML PARA DEBUG FIFO

### 7.1 Estructura Recomendada

```yaml
producto_1:
  product_info:
    id: 4240
    name: "Bolsa para residuos"
    cost_method: "fifo"
    valuation: "real_time"
    
  # ⭐ NUEVO: Stock actual y valoración
  stock_summary:
    qty_available: 150
    stock_value_calculated: 15000.00  # Sum(remaining_value de todos los layers)
    stock_value_sistema: 14850.00     # Lo que dice Odoo
    diferencia: 150.00
    
  layers_entrada:  # ⭐ Separar entradas de salidas
    layer_1:
      layer_id: 12345
      status: "correcto"
      layer_info:
        create_date: "2025-01-15"
        quantity: 100
        unit_cost: 100.00
        value: 10000.00
        remaining_qty: 60        # ⭐ FIFO
        remaining_value: 6000.00 # ⭐ FIFO
      
      purchase_order_line:
        id: 5001
        qty_ordered: 100
        price_unit: 100.00
      
      account_move_line:
        id: 7001
        quantity: 100
        balance: 10000.00
        price_unit_calculated: 100.00
      
      invoice_info:
        name: "FACT-2025-001"
        date: "2025-01-16"
        
      analisis_fifo:
        tiene_factura: true
        unit_cost_correcto: true
        value_correcto: true
        remaining_qty_validado: true
        consumido_por: 2  # Número de layers de salida
        
    layer_2:
      layer_id: 12350
      status: "requiere_correccion"
      layer_info:
        quantity: 50
        unit_cost: 95.00     # ⚠️ Incorrecto
        value: 4750.00       # ⚠️ Incorrecto
        remaining_qty: 50
        remaining_value: 4750.00
      
      invoice_info:
        balance: 5000.00     # ⭐ Valor correcto de factura
        price_unit: 100.00   # ⭐ Costo correcto
      
      analisis_fifo:
        diferencia_value: 250.00
        diferencia_unit_cost: 5.00
        correction_needed: true
        valores_correctos:
          unit_cost: 100.00
          value: 5000.00
          remaining_value: 5000.00  # No consumido aún
          
  layers_salida:  # ⭐ Layers de consumo
    layer_3:
      layer_id: 12360
      quantity: -40
      value: -4000.00
      unit_cost: 100.00
      stock_valuation_layer_id: 12345  # ⭐ Consumió del layer_1
      consumed_from:
        layer_id: 12345
        fecha: "2025-01-20"
        
  resumen_fifo:
    total_layers_entrada: 2
    total_layers_salida: 1
    layers_con_stock: 2
    layers_consumidos_total: 0
    layers_requieren_correccion: 1
    valor_total_correccion: 250.00
```

---

## 8. CONSIDERACIONES ESPECIALES FIFO

### 8.1 ⚠️ Correcciones en Cascada
```
Si corriges el unit_cost de un layer de entrada que YA fue parcialmente consumido:

Layer Entrada (antes):
  quantity: 100, unit_cost: 95, value: 9500
  remaining_qty: 60, remaining_value: 5700

Salida que lo consumió:
  quantity: -40, unit_cost: 95, value: -3800

CORRECCIÓN: unit_cost correcto = 100

Layer Entrada (después):
  quantity: 100, unit_cost: 100, value: 10000
  remaining_qty: 60, remaining_value: 6000

⚠️ PROBLEMA: La salida sigue con unit_cost: 95
⚠️ SOLUCIÓN: Puede que también necesites corregir las salidas
```

### 8.2 Prioridad de Corrección
```
1. ALTA: Layers de entrada con remaining_qty > 0
   → Afectan futuras salidas
   
2. MEDIA: Layers de entrada completamente consumidos
   → Solo afectan histórico
   
3. BAJA: Layers de salida
   → Ya están consumidos, solo histórico
```

---

## 9. QUERIES ÚTILES PARA FIFO

```python
# 1. Productos con layers FIFO desbalanceados
"""
SELECT 
    p.id,
    p.default_code,
    SUM(svl.remaining_value) as valor_calculado,
    p.stock_value as valor_sistema,
    SUM(svl.remaining_value) - p.stock_value as diferencia
FROM stock_valuation_layer svl
JOIN product_product p ON p.id = svl.product_id
WHERE svl.remaining_qty > 0
GROUP BY p.id
HAVING ABS(SUM(svl.remaining_value) - p.stock_value) > 1
"""

# 2. Layers con remaining_qty negativo (ERROR GRAVE)
"""
SELECT * FROM stock_valuation_layer
WHERE remaining_qty < 0
"""

# 3. Layers de entrada sin factura
"""
SELECT svl.*
FROM stock_valuation_layer svl
WHERE svl.quantity > 0
  AND svl.account_move_line_id IS NULL
ORDER BY svl.create_date DESC
"""
```

---

## 10. CONCLUSIONES Y RECOMENDACIONES

### 10.1 Diferencias Clave vs AVERAGE
```
┌─────────────────────┬──────────────────┬───────────────────┐
│ ASPECTO             │ AVERAGE          │ FIFO              │
├─────────────────────┼──────────────────┼───────────────────┤
│ Layers por entrada  │ 1 simple         │ 1 con remaining   │
│ Layers por salida   │ 1 simple         │ Múltiples posible │
│ remaining_qty       │ NO usado         │ ⭐ CRÍTICO        │
│ remaining_value     │ NO usado         │ ⭐ CRÍTICO        │
│ Complejidad         │ Baja             │ Alta              │
│ Corrección          │ Directa          │ En cascada        │
└─────────────────────┴──────────────────┴───────────────────┘
```

### 10.2 Plan de Acción Recomendado

```
FASE 1: ANÁLISIS (NO modificar datos)
├── 1.1 Ejecutar script de análisis YAML
├── 1.2 Identificar patterns de error
├── 1.3 Cuantificar impacto
└── 1.4 Validar remaining_qty de todos los layers

FASE 2: CORRECCIÓN SIMULADA
├── 2.1 Dry-run de correcciones
├── 2.2 Generar YAML con before/after
├── 2.3 Revisar casos edge
└── 2.4 Aprobación

FASE 3: APLICACIÓN
├── 3.1 Backup de base de datos
├── 3.2 Corregir layers en orden cronológico
├── 3.3 Validar remaining_qty después
└── 3.4 Verificar cuadres contables
```

---

**Próximos Pasos:**
1. Ejecutar análisis YAML con script adaptado para FIFO
2. Revisar output e identificar patrones
3. Definir estrategia de corrección específica
