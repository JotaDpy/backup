"""
Simulador FIFO - Reconstruye el historial completo de consumo FIFO

Este módulo simula exactamente cómo Odoo ejecuta el algoritmo FIFO,
permitiendo reconstruir qué cantidad de cada entrada consumió cada salida.

Autor: Análisis FIFO
Fecha: 29 de enero de 2026
"""

from datetime import datetime

def simular_fifo_producto(env, producto_id, fecha_inicio=None, fecha_fin=None):
    """
    Simula el algoritmo FIFO de Odoo para un producto completo.
    
    Retorna un diccionario con el historial detallado de consumo:
    {
        'entradas': {
            layer_id: {
                'quantity': 100,
                'value': 1000000,
                'remaining_qty_simulado': 50,
                'remaining_value_simulado': 500000,
                'consumido_por': [
                    {
                        'salida_id': 123,
                        'salida_date': '2025-01-15',
                        'qty_consumida': 30,
                        'value_consumido': 300000,
                    },
                    ...
                ]
            },
            ...
        },
        'salidas': {
            layer_id: {
                'quantity': -50,
                'consumio_de': [
                    {
                        'entrada_id': 100,
                        'entrada_date': '2025-01-01',
                        'qty_tomada': 30,
                        'value_tomado': 300000,
                    },
                    {
                        'entrada_id': 101,
                        'entrada_date': '2025-01-10',
                        'qty_tomada': 20,
                        'value_tomado': 200000,
                    }
                ],
                'value_total_simulado': -500000,
                'unit_cost_simulado': 10000,
            },
            ...
        }
    }
    
    Args:
        env: Environment de Odoo
        producto_id: ID del producto
        fecha_inicio: Fecha inicial del análisis (opcional)
        fecha_fin: Fecha final del análisis (opcional)
        
    Returns:
        dict: Diccionario con historial completo de FIFO
    """
    
    # 1. Buscar TODOS los layers del producto en orden cronológico
    domain = [('product_id', '=', producto_id)]
    
    if fecha_inicio:
        domain.append(('create_date', '>=', fecha_inicio))
    if fecha_fin:
        domain.append(('create_date', '<=', fecha_fin))
    
    layers = env['stock.valuation.layer'].search(
        domain,
        order='create_date asc, id asc'  # Orden cronológico estricto
    )
    
    # 2. Separar entradas y salidas
    entradas = []
    salidas = []
    
    for layer in layers:
        if layer.quantity > 0:
            entradas.append({
                'id': layer.id,
                'date': layer.create_date,
                'quantity': layer.quantity,
                'value': layer.value,
                'unit_cost': layer.unit_cost,
                'remaining_qty_db': layer.remaining_qty,
                'remaining_value_db': layer.remaining_value,
                'remaining_qty_simulado': layer.quantity,  # Inicialmente = quantity
                'remaining_value_simulado': layer.value,    # Inicialmente = value
                'consumido_por': []  # Lista de salidas que consumieron de esta entrada
            })
        elif layer.quantity < 0:
            salidas.append({
                'id': layer.id,
                'date': layer.create_date,
                'quantity': layer.quantity,
                'value_db': layer.value,
                'unit_cost_db': layer.unit_cost,
                'stock_valuation_layer_id_db': layer.stock_valuation_layer_id.id if layer.stock_valuation_layer_id else None,
                'consumio_de': [],  # Lista de entradas de las que consumió
                'value_total_simulado': 0,
                'unit_cost_simulado': 0,
            })
    
    # 3. Simular cada salida usando el algoritmo FIFO de Odoo
    for salida in salidas:
        qty_to_take = abs(salida['quantity'])  # Cantidad a consumir
        tmp_value = 0  # Acumulador de valor
        
        # Buscar entradas disponibles (con remaining_qty_simulado > 0)
        for entrada in entradas:
            if entrada['remaining_qty_simulado'] <= 0:
                continue  # Esta entrada ya está consumida
            
            # Verificar que la entrada sea anterior a la salida
            if entrada['date'] > salida['date']:
                # Esta entrada es posterior a la salida - no debería consumirse
                # (caso de stock negativo - vacuum)
                continue
            
            # Tomar la menor cantidad disponible
            qty_taken = min(qty_to_take, entrada['remaining_qty_simulado'])
            
            if qty_taken <= 0:
                continue
            
            # Calcular unit_cost de la entrada
            if entrada['remaining_qty_simulado'] > 0:
                entrada_unit_cost = entrada['remaining_value_simulado'] / entrada['remaining_qty_simulado']
            else:
                entrada_unit_cost = entrada['unit_cost']
            
            # Calcular valor tomado
            value_taken = qty_taken * entrada_unit_cost
            
            # Actualizar entrada (simular lo que hace Odoo)
            entrada['remaining_qty_simulado'] -= qty_taken
            entrada['remaining_value_simulado'] -= value_taken
            
            # Registrar en el historial de la entrada
            entrada['consumido_por'].append({
                'salida_id': salida['id'],
                'salida_date': str(salida['date']),
                'qty_consumida': qty_taken,
                'value_consumido': value_taken,
                'unit_cost_usado': entrada_unit_cost,
            })
            
            # Registrar en el historial de la salida
            salida['consumio_de'].append({
                'entrada_id': entrada['id'],
                'entrada_date': str(entrada['date']),
                'qty_tomada': qty_taken,
                'value_tomado': value_taken,
                'unit_cost_usado': entrada_unit_cost,
            })
            
            # Acumular valor
            qty_to_take -= qty_taken
            tmp_value += value_taken
            
            # Si ya tomamos todo, salir
            if qty_to_take <= 0:
                break
        
        # Calcular valores finales de la salida
        salida['value_total_simulado'] = -tmp_value
        if abs(salida['quantity']) > 0:
            salida['unit_cost_simulado'] = tmp_value / abs(salida['quantity'])
        
        # Detectar stock negativo
        if qty_to_take > 0:
            salida['stock_negativo'] = True
            salida['qty_faltante'] = qty_to_take
            salida['alerta'] = f"Stock negativo: faltaron {qty_to_take} unidades"
    
    # 4. Preparar resultado
    resultado = {
        'producto_id': producto_id,
        'total_entradas': len(entradas),
        'total_salidas': len(salidas),
        'entradas': {e['id']: e for e in entradas},
        'salidas': {s['id']: s for s in salidas},
    }
    
    return resultado

def validar_fifo_layer_entrada(env, layer_id):
    """
    Valida un layer de entrada específico simulando FIFO.
    
    Args:
        env: Environment de Odoo
        layer_id: ID del layer a validar
        
    Returns:
        dict: Resultados de validación con valores esperados vs actuales
    """
    layer = env['stock.valuation.layer'].browse(layer_id)
    
    if layer.quantity <= 0:
        return {
            'error': 'Este layer no es una entrada (quantity <= 0)'
        }
    
    # Simular FIFO para todo el producto
    resultado_fifo = simular_fifo_producto(
        env,
        layer.product_id.id,
        fecha_inicio=None,  # Desde el principio
        fecha_fin=None      # Hasta el final
    )
    
    # Obtener información de este layer
    entrada_info = resultado_fifo['entradas'].get(layer_id)
    
    if not entrada_info:
        return {
            'error': 'Layer no encontrado en simulación'
        }
    
    # Comparar valores
    validacion = {
        'layer_id': layer_id,
        'producto': layer.product_id.name,
        'create_date': str(layer.create_date),
        
        # Valores originales
        'quantity': layer.quantity,
        'value': layer.value,
        'unit_cost': layer.unit_cost,
        
        # Valores actuales en DB
        'remaining_qty_db': layer.remaining_qty,
        'remaining_value_db': layer.remaining_value,
        
        # Valores esperados (simulados)
        'remaining_qty_esperado': entrada_info['remaining_qty_simulado'],
        'remaining_value_esperado': entrada_info['remaining_value_simulado'],
        
        # Diferencias
        'diferencia_qty': abs(layer.remaining_qty - entrada_info['remaining_qty_simulado']),
        'diferencia_value': abs(layer.remaining_value - entrada_info['remaining_value_simulado']),
        
        # Historial de consumo
        'consumido_por': entrada_info['consumido_por'],
        'total_salidas_que_consumieron': len(entrada_info['consumido_por']),
        
        # Validación
        'qty_correcto': abs(layer.remaining_qty - entrada_info['remaining_qty_simulado']) < 0.01,
        'value_correcto': abs(layer.remaining_value - entrada_info['remaining_value_simulado']) < 100,
    }
    
    return validacion

def generar_reporte_fifo_producto(env, producto_id, archivo_salida=None):
    """
    Genera un reporte completo de FIFO para un producto.
    
    Args:
        env: Environment de Odoo
        producto_id: ID del producto
        archivo_salida: Ruta del archivo de salida (opcional)
        
    Returns:
        str: Reporte en formato de texto
    """
    resultado = simular_fifo_producto(env, producto_id)
    
    lineas = []
    lineas.append("=" * 80)
    lineas.append("REPORTE SIMULACIÓN FIFO")
    lineas.append("=" * 80)
    lineas.append(f"Producto ID: {producto_id}")
    lineas.append(f"Total entradas: {resultado['total_entradas']}")
    lineas.append(f"Total salidas: {resultado['total_salidas']}")
    lineas.append("")
    
    # Entradas
    lineas.append("-" * 80)
    lineas.append("ANÁLISIS DE ENTRADAS")
    lineas.append("-" * 80)
    
    for entrada_id, entrada in resultado['entradas'].items():
        lineas.append(f"\nEntrada #{entrada_id} - {entrada['date']}")
        lineas.append(f"  Quantity: {entrada['quantity']}")
        lineas.append(f"  Value: {entrada['value']:,.2f}")
        lineas.append(f"  Remaining (DB):       qty={entrada['remaining_qty_db']}, value={entrada['remaining_value_db']:,.2f}")
        lineas.append(f"  Remaining (Simulado): qty={entrada['remaining_qty_simulado']}, value={entrada['remaining_value_simulado']:,.2f}")
        
        dif_qty = abs(entrada['remaining_qty_db'] - entrada['remaining_qty_simulado'])
        dif_val = abs(entrada['remaining_value_db'] - entrada['remaining_value_simulado'])
        
        if dif_qty > 0.01 or dif_val > 100:
            lineas.append(f"  ⚠️ DIFERENCIA: qty={dif_qty}, value={dif_val:,.2f}")
        else:
            lineas.append(f"  ✅ CORRECTO")
        
        if entrada['consumido_por']:
            lineas.append(f"  Consumido por {len(entrada['consumido_por'])} salidas:")
            for consumo in entrada['consumido_por']:
                lineas.append(f"    - Salida #{consumo['salida_id']}: {consumo['qty_consumida']} unidades, {consumo['value_consumido']:,.2f}")
    
    # Salidas
    lineas.append("\n" + "-" * 80)
    lineas.append("ANÁLISIS DE SALIDAS")
    lineas.append("-" * 80)
    
    for salida_id, salida in resultado['salidas'].items():
        lineas.append(f"\nSalida #{salida_id} - {salida['date']}")
        lineas.append(f"  Quantity: {salida['quantity']}")
        lineas.append(f"  Value (DB):       {salida['value_db']:,.2f}")
        lineas.append(f"  Value (Simulado): {salida['value_total_simulado']:,.2f}")
        lineas.append(f"  Unit Cost (DB):       {salida['unit_cost_db']:,.2f}")
        lineas.append(f"  Unit Cost (Simulado): {salida['unit_cost_simulado']:,.2f}")
        
        if 'stock_negativo' in salida:
            lineas.append(f"  ⚠️ STOCK NEGATIVO: {salida['alerta']}")
        
        if salida['consumio_de']:
            lineas.append(f"  Consumió de {len(salida['consumio_de'])} entradas:")
            for consumo in salida['consumio_de']:
                lineas.append(f"    - Entrada #{consumo['entrada_id']}: {consumo['qty_tomada']} unidades, {consumo['value_tomado']:,.2f}")
    
    reporte = "\n".join(lineas)
    
    if archivo_salida:
        with open(archivo_salida, 'w') as f:
            f.write(reporte)
    
    return reporte

# Ejemplo de uso (comentado - descomentar solo para pruebas desde la shell de Odoo)
# resultado = simular_fifo_producto(env, producto_id=2671)

