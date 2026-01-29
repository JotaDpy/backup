# EJEMPLOS DE USO - Parámetros de Fecha en buscar_layers()

## 📅 Función: `buscar_layers()`

### Parámetros de fecha:
- `fecha_inicio`: Fecha de inicio del rango (string o None)
- `fecha_fin`: Fecha final del rango (string, int o None)

---

## 🎯 Casos de Uso

### **Caso 1: Solo fecha_inicio (string)**
```python
layers = buscar_layers(
    env=env,
    producto=producto_obj,
    fecha_inicio='2025-01-01',
    fecha_fin=None
)
```
**Resultado:** Busca layers desde el 2025-01-01 00:00:00 en adelante (sin límite superior)

---

### **Caso 2: fecha_inicio + fecha_fin en meses (int)**
```python
layers = buscar_layers(
    env=env,
    producto=producto_obj,
    fecha_inicio='2025-01-01',  # string
    fecha_fin=4                  # int = 4 meses
)
```
**Cálculo interno:**
- fecha_inicio: `2025-01-01 00:00:00`
- fecha_fin: `2025-01-01` + 4 meses = `2025-05-01 23:59:59`

**Resultado:** Busca layers entre 2025-01-01 y 2025-05-01

**Output en consola:**
```
Fecha fin calculada: 2025-01-01 00:00:00 + 4 meses = 2025-05-01 23:59:59
```

---

### **Caso 3: Ambas fechas como strings**
```python
layers = buscar_layers(
    env=env,
    producto=producto_obj,
    fecha_inicio='2025-01-01',
    fecha_fin='2025-12-31'
)
```
**Resultado:** Busca layers entre 2025-01-01 y 2025-12-31

---

### **Caso 4: Solo fecha_fin (string)**
```python
layers = buscar_layers(
    env=env,
    producto=producto_obj,
    fecha_inicio=None,
    fecha_fin='2025-12-31'
)
```
**Resultado:** Busca layers hasta el 2025-12-31 23:59:59 (sin límite inferior)

---

### **Caso 5: Fechas con hora específica**
```python
layers = buscar_layers(
    env=env,
    producto=producto_obj,
    fecha_inicio='2025-01-01 10:30:00',
    fecha_fin='2025-01-31 18:45:00'
)
```
**Resultado:** Busca layers entre las fechas/horas exactas especificadas

---

### **Caso 6: Sin filtros de fecha**
```python
layers = buscar_layers(
    env=env,
    producto=producto_obj,
    fecha_inicio=None,
    fecha_fin=None
)
```
**Resultado:** Busca TODOS los layers del producto (sin filtro de fecha)

---

## 🔧 Ejemplos Prácticos

### Ejemplo 1: Análisis trimestral
```python
# Primer trimestre 2025
layers_q1 = buscar_layers(
    env=env,
    producto=producto_obj,
    fecha_inicio='2025-01-01',
    fecha_fin=3  # 3 meses
)
# Resultado: 2025-01-01 al 2025-04-01
```

### Ejemplo 2: Análisis semestral
```python
# Primer semestre 2025
layers_h1 = buscar_layers(
    env=env,
    producto=producto_obj,
    fecha_inicio='2025-01-01',
    fecha_fin=6  # 6 meses
)
# Resultado: 2025-01-01 al 2025-07-01
```

### Ejemplo 3: Análisis anual
```python
# Todo el año 2025
layers_2025 = buscar_layers(
    env=env,
    producto=producto_obj,
    fecha_inicio='2025-01-01',
    fecha_fin=12  # 12 meses
)
# Resultado: 2025-01-01 al 2026-01-01
```

### Ejemplo 4: Análisis desde el primer layer
```python
# Desde el primer layer del producto
fecha_min = get_fecha_min_layer(producto_obj.id)
layers = buscar_layers(
    env=env,
    producto=producto_obj,
    fecha_inicio=fecha_min,
    fecha_fin=None  # Sin límite
)
# Resultado: Desde el primer layer hasta ahora
```

### Ejemplo 5: Análisis mensual progresivo
```python
# Analizar mes por mes durante 6 meses
for mes in range(6):
    layers = buscar_layers(
        env=env,
        producto=producto_obj,
        fecha_inicio='2025-01-01',
        fecha_fin=mes + 1  # 1, 2, 3, 4, 5, 6 meses
    )
    print(f"Mes {mes+1}: {len(layers)} layers")
```

---

## ⚙️ Detalles Técnicos

### Formato de fechas aceptado:
- `'YYYY-MM-DD'` → Se convierte a `YYYY-MM-DD 00:00:00` (inicio) o `YYYY-MM-DD 23:59:59` (fin)
- `'YYYY-MM-DD HH:MM:SS'` → Se usa tal cual

### Cálculo de meses:
Usa `relativedelta` de `dateutil` para manejar correctamente:
- Cambios de año (ej: 2025-11-01 + 3 meses = 2026-02-01)
- Días fin de mes (ej: 2025-01-31 + 1 mes = 2025-02-28)
- Años bisiestos

### Orden de evaluación:
1. Si `fecha_fin` es `int` y `fecha_inicio` es `str` → Calcular fecha_fin = fecha_inicio + N meses
2. Si `fecha_fin` es `str` → Procesar normalmente
3. Convertir a formato de búsqueda de Odoo

---

## ✅ Validaciones

### Error 1: fecha_inicio mal formateada
```python
fecha_inicio='2025-13-01'  # Mes inválido
```
**Output:** `Formato de fecha_inicio incorrecto: 2025-13-01`  
**Resultado:** Se ignora el filtro de fecha_inicio

### Error 2: fecha_fin como int sin fecha_inicio
```python
fecha_inicio=None,
fecha_fin=4
```
**Resultado:** `fecha_fin` se ignora (no puede calcular meses sin inicio)

### Error 3: fecha_fin mal formateada
```python
fecha_fin='2025-14-50'  # Fecha inválida
```
**Output:** `Formato de fecha_fin incorrecto: 2025-14-50`  
**Resultado:** Se ignora el filtro de fecha_fin

---

## 🎯 Uso Recomendado en el Script

### Opción actual (desde primer layer):
```python
layers = buscar_layers(
    env=env,
    producto=producto_obj,
    orden="asc",
    signo=None,
    cantidad=None,
    fecha_inicio=get_fecha_min_layer(producto_obj.id),
    fecha_fin=None
)
```

### Opción mejorada (análisis trimestral):
```python
layers = buscar_layers(
    env=env,
    producto=producto_obj,
    orden="asc",
    signo='>',  # Solo entradas
    cantidad=None,
    fecha_inicio='2025-01-01',
    fecha_fin=3  # Primer trimestre
)
```

### Opción para debugging (últimos 2 meses):
```python
from datetime import datetime
from dateutil.relativedelta import relativedelta

fecha_actual = datetime.now()
fecha_hace_2_meses = fecha_actual - relativedelta(months=2)

layers = buscar_layers(
    env=env,
    producto=producto_obj,
    fecha_inicio=fecha_hace_2_meses.strftime('%Y-%m-%d'),
    fecha_fin=None
)
```

---

## 📊 Combinación con otros parámetros

```python
# Ejemplo completo: Entradas del primer trimestre 2025, ordenadas por fecha
layers = buscar_layers(
    env=env,
    producto=producto_obj,
    orden="asc",        # Ordenar ascendente por create_date
    signo='>',          # Solo layers con quantity > 0 (entradas)
    cantidad=50,        # Máximo 50 layers
    fecha_inicio='2025-01-01',
    fecha_fin=3         # 3 meses (hasta 2025-04-01)
)
```

---

## 🔍 Debugging

Para verificar las fechas calculadas, revisa el output en consola:

```python
layers = buscar_layers(
    env=env,
    producto=producto_obj,
    fecha_inicio='2025-01-01',
    fecha_fin=4
)
# Output en consola:
# Fecha fin calculada: 2025-01-01 00:00:00 + 4 meses = 2025-05-01 23:59:59
```
