"""
EJEMPLO RÁPIDO: Cómo usar el simulador FIFO

Este archivo muestra ejemplos prácticos de cómo interactuar con el simulador.
"""

# ============================================================================
# OPCIÓN 1: USO AUTOMÁTICO (Recomendado - ya integrado en actualizacion_layers.py)
# ============================================================================

# Simplemente ejecuta el script principal como siempre:
# exec(open('/home/jose/Documentos/clientes/15FONDOESTRELLA/clean_valuation/python/valoracion/actualizacion_layers.py').read())

# Eso es todo. El simulador se ejecuta automáticamente y el YAML tendrá datos más precisos.


# ============================================================================
# OPCIÓN 2: USO MANUAL desde la shell de Odoo
# ============================================================================

from fifo_simulator import simular_fifo_producto, validar_fifo_layer_entrada, generar_reporte_fifo_producto

# Ejemplo 1: Simular FIFO completo para un producto
# --------------------------------------------------
producto_id = 2671
resultado = simular_fifo_producto(env, producto_id)

print(f"Producto {producto_id}:")
print(f"  Total entradas: {resultado['total_entradas']}")
print(f"  Total salidas: {resultado['total_salidas']}")

# Ver una entrada específica
layer_entrada_id = 250880
if layer_entrada_id in resultado['entradas']:
    entrada = resultado['entradas'][layer_entrada_id]
    print(f"\nEntrada {layer_entrada_id}:")
    print(f"  Cantidad original: {entrada['quantity']}")
    print(f"  Remaining qty (DB): {entrada['remaining_qty_db']}")
    print(f"  Remaining qty (Simulado): {entrada['remaining_qty_simulado']}")
    print(f"  Consumido por {len(entrada['consumido_por'])} salidas")
    
    # Ver detalle de consumo
    for consumo in entrada['consumido_por']:
        print(f"    - Salida {consumo['salida_id']} ({consumo['salida_date']}): {consumo['qty_consumida']} unidades")

# Ver una salida específica
layer_salida_id = 250900
if layer_salida_id in resultado['salidas']:
    salida = resultado['salidas'][layer_salida_id]
    print(f"\nSalida {layer_salida_id}:")
    print(f"  Cantidad: {salida['quantity']}")
    print(f"  Consumió de {len(salida['consumio_de'])} entradas")
    
    # Ver detalle de consumo
    for consumo in salida['consumio_de']:
        print(f"    - Entrada {consumo['entrada_id']} ({consumo['entrada_date']}): {consumo['qty_tomada']} unidades")


# Ejemplo 2: Validar un layer específico
# ---------------------------------------
layer_id = 116548
validacion = validar_fifo_layer_entrada(env, layer_id)

print(f"\n{'='*60}")
print(f"VALIDACIÓN LAYER {layer_id}")
print(f"{'='*60}")
print(f"Producto: {validacion['producto']}")
print(f"Fecha creación: {validacion['create_date']}")
print(f"\nCantidad original: {validacion['quantity']}")
print(f"\nREMAINING QTY:")
print(f"  DB: {validacion['remaining_qty_db']}")
print(f"  Esperado: {validacion['remaining_qty_esperado']}")
print(f"  Diferencia: {validacion['diferencia_qty']}")
print(f"  ¿Correcto?: {'✅ SÍ' if validacion['qty_correcto'] else '❌ NO'}")

print(f"\nREMAINING VALUE:")
print(f"  DB: {validacion['remaining_value_db']:,.2f}")
print(f"  Esperado: {validacion['remaining_value_esperado']:,.2f}")
print(f"  Diferencia: {validacion['diferencia_value']:,.2f}")
print(f"  ¿Correcto?: {'✅ SÍ' if validacion['value_correcto'] else '❌ NO'}")

print(f"\nCONSUMO:")
print(f"  Consumido por {validacion['total_salidas_que_consumieron']} salidas")
for consumo in validacion['consumido_por']:
    print(f"    - Salida {consumo['salida_id']}: {consumo['qty_consumida']} unidades, {consumo['value_consumido']:,.2f} PYG")


# Ejemplo 3: Generar reporte completo en TXT
# -------------------------------------------
archivo_salida = '/home/jose/Documentos/clientes/15FONDOESTRELLA/clean_valuation/python/valoracion/ejemplo_reporte_2671.txt'
reporte = generar_reporte_fifo_producto(env, producto_id=2671, archivo_salida=archivo_salida)

print(f"\n{'='*60}")
print(f"Reporte guardado en: {archivo_salida}")
print(f"{'='*60}")

# También puedes imprimir el reporte en consola
print(reporte)


# ============================================================================
# OPCIÓN 3: Activar reporte TXT automático en actualizacion_layers.py
# ============================================================================

# Edita actualizacion_layers.py y descomenta estas líneas (aprox. línea 892):
"""
# GENERAR REPORTE DETALLADO DEL SIMULADOR (opcional)
archivo_reporte = f'/home/jose/Documentos/clientes/15FONDOESTRELLA/clean_valuation/python/valoracion/reporte_fifo_producto_{producto_obj.id}.txt'
reporte_simulador = generar_reporte_fifo_producto(env, producto_obj.id, archivo_reporte)
print(f"Reporte detallado guardado en: {archivo_reporte}")
"""

# Luego ejecuta normalmente:
# exec(open('/home/jose/Documentos/clientes/15FONDOESTRELLA/clean_valuation/python/valoracion/actualizacion_layers.py').read())


# ============================================================================
# EJEMPLO 4: Analizar diferencias específicas
# ============================================================================

# Buscar layers con diferencias significativas
producto_id = 2671
resultado = simular_fifo_producto(env, producto_id)

print(f"\n{'='*60}")
print(f"LAYERS CON DIFERENCIAS SIGNIFICATIVAS")
print(f"{'='*60}")

for layer_id, entrada in resultado['entradas'].items():
    diff_qty = abs(entrada['remaining_qty_db'] - entrada['remaining_qty_simulado'])
    diff_value = abs(entrada['remaining_value_db'] - entrada['remaining_value_simulado'])
    
    # Solo mostrar si hay diferencia significativa
    if diff_qty > 0.01 or diff_value > 1000:
        print(f"\nLayer {layer_id}:")
        print(f"  Diferencia qty: {diff_qty}")
        print(f"  Diferencia value: {diff_value:,.2f} PYG")
        print(f"  Remaining qty DB: {entrada['remaining_qty_db']}")
        print(f"  Remaining qty Simulado: {entrada['remaining_qty_simulado']}")
        print(f"  Consumido por {len(entrada['consumido_por'])} salidas")


# ============================================================================
# EJEMPLO 5: Detectar consumo multi-capa
# ============================================================================

# Buscar salidas que consumieron de múltiples entradas
resultado = simular_fifo_producto(env, producto_id=2671)

print(f"\n{'='*60}")
print(f"SALIDAS CON CONSUMO MULTI-CAPA")
print(f"{'='*60}")

for salida_id, salida in resultado['salidas'].items():
    if len(salida['consumio_de']) > 1:
        print(f"\nSalida {salida_id}:")
        print(f"  Cantidad total: {abs(salida['quantity'])}")
        print(f"  Consumió de {len(salida['consumio_de'])} entradas diferentes:")
        for consumo in salida['consumio_de']:
            print(f"    - Entrada {consumo['entrada_id']}: {consumo['qty_tomada']} unidades")
        
        # Este es el caso que el método antiguo no detectaba correctamente
        print(f"  ⚠️ Odoo solo guardó stock_valuation_layer_id = {salida.get('stock_valuation_layer_id_db')}")
        print(f"     (apunta solo a la última entrada, perdiendo el resto)")


# ============================================================================
# RESUMEN
# ============================================================================

"""
🎯 PARA USO DIARIO:
   → Simplemente ejecuta actualizacion_layers.py
   → El simulador se ejecuta automáticamente
   → Obtienes el YAML con datos más precisos

🔍 PARA DEBUGGING/ANÁLISIS:
   → Usa los ejemplos 1-5 de arriba desde la shell de Odoo
   → Inspecciona layers específicos
   → Genera reportes TXT detallados

📊 PARA REPORTES COMPLETOS:
   → Descomenta las líneas de reporte TXT en actualizacion_layers.py
   → Obtendrás un archivo TXT por producto con todo el detalle
"""
