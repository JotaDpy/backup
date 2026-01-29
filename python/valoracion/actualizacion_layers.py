# exec(open('/home/jose/Documentos/clientes/15FONDOESTRELLA/clean_valuation/python/valoracion/actualizacion_layers.py').read())
# Configuración para reconocimiento de Odoo en VS Code
# pylint: disable=undefined-variable
# pyright: reportUndefinedVariable=false

from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import sys
import os
import calendar
import re

# Importar el simulador FIFO
sys.path.insert(0, '/home/jose/Documentos/clientes/15FONDOESTRELLA/clean_valuation/python/valoracion')
try:
    from fifo_simulator import simular_fifo_producto, validar_fifo_layer_entrada, generar_reporte_fifo_producto
    print("✅ Simulador FIFO importado correctamente")
except ImportError as e:
    print(f"⚠️ Error al importar fifo_simulator: {e}")
    print(f"El script continuará usando el método tradicional (menos preciso)")
    simular_fifo_producto = None
    validar_fifo_layer_entrada = None
    generar_reporte_fifo_producto = None

import calendar
import re
import sys
import os

def get_fecha_min_layer(product_id):
    query = """
        SELECT MIN(create_date)
        FROM stock_valuation_layer
        WHERE product_id = %s
    """
    self.env.cr.execute(query, (product_id,))
    result = self.env.cr.fetchone()

    if not result or not result[0]:
        return None

    return result[0].strftime('%Y-%m-%d %H:%M:%S')

def get_product_category(categoria, enviroment, limit=None):
    def product_template_interseccion(objeto_template):
        product_product = env['product.product'].search([
            ('product_tmpl_id', 'in', objeto_template.ids)
        ])
        return product_product or []

    # A. Obtenemos el Recordset de productos (los objetos completos)
    productos_recordset = enviroment['product.template'].search([
        ('categ_id', '=', categoria.id)
    ], limit=limit)
    
    # B. Obtenemos la cantidad exacta (Usando search_count como pediste)
    cantidad = enviroment['product.template'].search_count([
        ('categ_id', '=', categoria.id)
    ])

    # 3. Llenamos el diccionario
    # Usamos categoria.name (o categoria.id) como clave para separar por categoría
    return {
        'cat_id': categoria.id,
        'complete_name': categoria.complete_name,
        'cost_method': categoria.property_cost_method,
        'valuation': categoria.property_valuation,
        'total_productos': cantidad,       # Aquí va el número entero
        'records_product_template': productos_recordset, # Aquí va el objeto Recordset
        'records_product_product': product_template_interseccion(productos_recordset) # Aquí va el objeto Recordset
    }

def meses_anho(anho):
    meses = {}
    for mes in range(1, 13):
        nombre_mes = calendar.month_name[mes].lower()
        dias_mes = calendar.monthrange(anho, mes)[1]
        meses[nombre_mes] = dias_mes
    return meses

def format_num(numero):
    NUMERO = float(abs(numero))
    parte_entera, parte_decimal = f"{NUMERO:.2f}".split(".")
    parte_entera_con_puntos = ".".join(
        [parte_entera[::-1][i:i + 3] for i in range(0, len(parte_entera), 3)]
    )[::-1]

    if numero < 0:
        msg = f"(-) {parte_entera_con_puntos},{parte_decimal}"
    else:
        msg = f"{parte_entera_con_puntos},{parte_decimal}"

    return msg

def format_yaml_string(value):
    """
    Formatea un string para que sea seguro en YAML.
    Escapa caracteres especiales y maneja valores None.
    """
    if value is None or value == False:
        return "N/A"
    
    # Convertir a string si no lo es
    if not isinstance(value, str):
        value = str(value)
    
    # Reemplazar caracteres problemáticos
    value = value.replace('"', "'")  # Comillas dobles por simples
    value = value.replace('\n', ' ')  # Saltos de línea por espacios
    value = value.replace('\r', ' ')  # Retornos de carro por espacios
    value = value.replace('\t', ' ')  # Tabs por espacios
    value = value.replace('\\', '/')  # Backslashes por forward slashes
    
    # Escapar caracteres especiales de YAML
    value = value.replace(':', ' - ')  # Dos puntos pueden romper YAML
    value = value.replace('[', '(').replace(']', ')')  # Corchetes
    value = value.replace('{', '(').replace('}', ')')  # Llaves
    
    # Limpiar espacios múltiples
    value = re.sub(r'\s+', ' ', value).strip()
    
    # Si está vacío después de limpiar, retornar N/A
    if not value:
        return "N/A"
    
    return value

def buscar_layers(
        env,
        producto: int,
        orden="desc",
        signo=None,
        cantidad=None,
        fecha_inicio=None,
        fecha_fin=None):
    # Definimos el dominio de la búsqueda
    domain = [('product_id', '=', producto.id)]

    if signo:
        if signo == '>':
            domain.append(('quantity', '>', 0))
        elif signo == '<':
            domain.append(('quantity', '<', 0))

    # Agregar filtros de fecha si se proporcionan
    if fecha_inicio:
        # Convertir string a datetime si es necesario
        if isinstance(fecha_inicio, str):
            try:
                fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').strftime('%Y-%m-%d 00:00:00')
            except ValueError:
                try:
                    fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    print(f"Formato de fecha_inicio incorrecto: {fecha_inicio}")
                    fecha_inicio = None
        
        if fecha_inicio:
            domain.append(('create_date', '>=', fecha_inicio))
    
    if fecha_fin:
        # CASO 1: fecha_fin es un entero y fecha_inicio es string (sumar fecha_fin)
        if isinstance(fecha_fin, int) and isinstance(fecha_inicio, str):
            try:
                # Convertir fecha_inicio a datetime para sumar fecha_fin
                fecha_base = datetime.strptime(
                    fecha_inicio, '%Y-%m-%d %H:%M:%S')

                # Sumar los fecha_fin indicados
                fecha_calculada = fecha_base + relativedelta(months=fecha_fin)

                # Convertir a string en formato final del día
                fecha_calculada = fecha_calculada.strftime('%Y-%m-%d 23:59:59')
                print(
                    f"Fecha fin calculada: {fecha_inicio} + {fecha_fin} fecha_fin = {fecha_calculada}")
                if fecha_calculada:
                    domain.append(('create_date', '<=', fecha_calculada))

            except Exception as e:
                print(f"Error al calcular fecha_fin desde fecha_fin: {e}")
                fecha_fin = None

        # CASO 2: fecha_fin es un string (fecha)
        elif isinstance(fecha_fin, str):
            try:
                fecha_fin = datetime.strptime(
                    fecha_fin, '%Y-%m-%d').strftime('%Y-%m-%d 23:59:59')
            except ValueError:
                try:
                    fecha_fin = datetime.strptime(
                        fecha_fin, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    print(f"Formato de fecha_fin incorrecto: {fecha_fin}")
                    fecha_fin = None

            if fecha_fin:
                domain.append(('create_date', '<=', fecha_fin))

    # Buscamos los layers con o sin límite
    if isinstance(cantidad, int):
        layers_positive = env['stock.valuation.layer'].search(
            domain,
            order=f"create_date {orden}",
            limit=cantidad
        )
    else:
        layers_positive = env['stock.valuation.layer'].search(
            domain,
            order=f"create_date {orden}"
        )

    return layers_positive

def impresion_csv(direccion, layers):
    # Impresion en .csv
    with open(direccion, 'w') as f:
        f.write(
            f'id,' f'create_uid,' f'create_date,' f'write_uid,' f'write_date,'
            f'company_id,' f'product_id,' f'quantity,' f'unit_cost,' f'value,'
            f'remaining_qty,' f'description,' f'stock_valuation_layer_id,' f'stock_move_id,'
            f'account_move_id,' f'remaining_value,' f'account_move_line_id,' f'price_diff_value,'
            f'categ_id\n')

        for layer in layers:
            f.write(
                f'"{layer.id}",'
                f'"{layer.create_uid}",'
                f'"{layer.create_date}",'
                f'"{layer.write_uid}",'
                f'"{layer.write_date}",'
                f'"{layer.company_id}",'
                f'"{layer.product_id}",'
                f'"{layer.quantity}",'
                f'"{layer.unit_cost}",'
                f'"{layer.value}",'
                f'"{layer.remaining_qty}",'
                f'"{layer.description}",'
                f'"{layer.stock_valuation_layer_id}",'
                f'"{layer.stock_move_id}",'
                f'"{layer.account_move_id}",'
                f'"{layer.remaining_value}",'
                f'"{layer.account_move_line_id}",'
                f'"{layer.price_diff_value}",'
                f'"{layer.categ_id}"\n')

def info_cabecera_principal(iterador, enviroment, lista):
        # Escribir cabecera global del archivo YAML
    iterador.write("# ========================================\n")
    iterador.write("# ANÁLISIS MASIVO DE STOCK VALUATION LAYERS\n")
    iterador.write("# ========================================\n")
    iterador.write("# Generado automáticamente por actualizacion_layers.py\n")
    iterador.write(f"# Período analizado: Febrero 2025\n")
    iterador.write(f"# Total productos: {len(lista)}\n")
    iterador.write(f"# Fecha de análisis: {enviroment['res.users'].browse(enviroment.uid).name} - {enviroment.cr.now()}\n\n")

def info_cabecera_productos(iterador, count, producto, id, objeto, valoracion):
    iterador.write(f"# ----------------------------------------\n")
    iterador.write(f"# PRODUCTO {count}/{len(producto)}\n")
    iterador.write(f"# ----------------------------------------\n")
    iterador.write(f"# ID: {id}\n")
    iterador.write(f"# Nombre: {format_yaml_string(objeto.name)}\n")
    iterador.write(f"# Cantidad de layers: {len(valoracion)}\n")
    iterador.write(f"# ----------------------------------------\n\n")
    
    iterador.write(f"producto_{count}:\n")
    iterador.write(f"  product_info:\n")
    iterador.write(f"    id: {id}\n")
    iterador.write(f"    name: \"{format_yaml_string(objeto.name)}\"\n")
    iterador.write(f"    default_code: \"{format_yaml_string(objeto.default_code)}\"\n")
    iterador.write(f"    categ_id: \"{format_yaml_string(objeto.categ_id.name)}\"\n")
    iterador.write(f"    total_layers: {len(valoracion)}\n")
    iterador.write(f"  layers:\n")

def info_not_purchase_order_line(iterador, indice, objeto1, objeto2):
    iterador.write(f"    layer_{indice}:\n")
    iterador.write(f"      layer_id: {objeto1.id}\n")
    iterador.write(f"      status: \"sin_purchase_order_line\"\n")
    iterador.write(f"      layer_info:\n")
    iterador.write(f"        create_date: \"{objeto1.create_date}\"\n")
    iterador.write(f"        description: \"{format_yaml_string(objeto1.description)}\"\n")
    iterador.write(f"        quantity: {objeto1.quantity}\n")
    iterador.write(f"        unit_cost: {objeto1.unit_cost}\n")
    iterador.write(f"        value: {objeto1.value}\n")
    iterador.write(f"        stock_move_id: {objeto2.id if objeto2 else 'N/A'}\n")
    iterador.write(f"      observacion: \"Layer sin purchase_order_line asociada\"\n\n")

def info_layer_encontrado(iterador, indice, objeto1, objeto2):
    # objeto1: layer
    # objeto2: account_move_line
    iterador.write(f"    layer_{indice}:\n")
    iterador.write(f"      layer_id: {objeto1.id}\n")
    iterador.write(f"      status: \"{'completo' if objeto2 else 'incompleto'}\"\n")

def info_layer_completo(iterador, objeto_layer):
    iterador.write(f"      stock_valuation_layer:\n")
    iterador.write(f"        create_date: \"{objeto_layer.create_date}\"\n")
    iterador.write(f"        description: \"{format_yaml_string(objeto_layer.description)}\"\n")
    iterador.write(f"        quantity: {objeto_layer.quantity}\n")
    iterador.write(f"        unit_cost: {objeto_layer.unit_cost}\n")
    iterador.write(f"        value: {objeto_layer.value}\n")
    iterador.write(f"        remaining_qty: {objeto_layer.remaining_qty}\n")
    iterador.write(f"        remaining_value: {objeto_layer.remaining_value}\n")

def info_stock_move(iterador, object_stock_move):
    iterador.write(f"      stock_move:\n")
    iterador.write(f"        id: {object_stock_move.id}\n")
    iterador.write(f"        name: \"{format_yaml_string(object_stock_move.name)}\"\n")
    iterador.write(f"        date: \"{object_stock_move.date}\"\n")
    iterador.write(f"        state: \"{object_stock_move.state}\"\n")

def info_purchase_order_line(iterador, object_purchase_order_line):
    iterador.write(f"      purchase_order_line:\n")
    iterador.write(f"        id: {object_purchase_order_line.id}\n")
    iterador.write(f"        name: \"{format_yaml_string(object_purchase_order_line.name)}\"\n")
    iterador.write(f"        qty_ordered: {object_purchase_order_line.product_qty}\n")
    iterador.write(f"        price_unit: {object_purchase_order_line.price_unit}\n")
    iterador.write(f"        currency: \"{object_purchase_order_line.currency_id.name}\"\n")
    iterador.write(f'        qty_received: {object_purchase_order_line.qty_received}\n')
    iterador.write(f'        qty_invoiced: {object_purchase_order_line.qty_invoiced}\n')

def info_fifo_analysis(iterador, objeto_layer, env, resultado_fifo=None):
    """
    Genera un bloque de análisis específico para FIFO.
    Analiza remaining_qty, remaining_value y el estado del layer.
    
    Args:
        iterador: Archivo de salida YAML
        objeto_layer: Layer a analizar
        env: Environment de Odoo
        resultado_fifo: Resultado de simular_fifo_producto() (opcional, se calcula si no se provee)
    """
    iterador.write(f"      fifo_analysis:\n")
    
    # Determinar si es entrada o salida
    es_entrada = objeto_layer.quantity > 0
    es_salida = objeto_layer.quantity < 0
    
    if es_entrada:
        # Análisis para layers de ENTRADA
        
        # PASO 1: Obtener información del simulador (si no se pasó, calcular)
        if resultado_fifo is None and simular_fifo_producto is not None:
            resultado_fifo = simular_fifo_producto(env, objeto_layer.product_id.id)
        
        # PASO 2: Obtener información de este layer desde el simulador
        entrada_info = resultado_fifo['entradas'].get(objeto_layer.id) if resultado_fifo else None
        
        if entrada_info:
            # PASO 3: Usar valores SIMULADOS (más precisos)
            qty_consumida_por_salidas = sum(c['qty_consumida'] for c in entrada_info['consumido_por'])
            remaining_qty_esperado = entrada_info['remaining_qty_simulado']
            remaining_value_esperado = entrada_info['remaining_value_simulado']
            
            # Información sobre consumo
            layers_salida_ids = [c['salida_id'] for c in entrada_info['consumido_por']]
            total_salidas = len(entrada_info['consumido_por'])
        else:
            # Fallback: usar búsqueda directa (método antiguo)
            layers_salida = env['stock.valuation.layer'].search([
                ('stock_valuation_layer_id', '=', objeto_layer.id),
                ('quantity', '<', 0)
            ])
            qty_consumida_por_salidas = sum(abs(s.quantity) for s in layers_salida)
            remaining_qty_esperado = objeto_layer.quantity - qty_consumida_por_salidas
            remaining_value_esperado = (remaining_qty_esperado / objeto_layer.quantity * objeto_layer.value) if objeto_layer.quantity != 0 else 0
            layers_salida_ids = [s.id for s in layers_salida]
            total_salidas = len(layers_salida)
        
        # PASO 4: Calcular diferencias entre valores actuales y esperados
        # 4A. Diferencia en remaining_qty
        diferencia_remaining_qty = abs(objeto_layer.remaining_qty - remaining_qty_esperado)
        
        # 4B. Diferencia en remaining_value
        diferencia_remaining_value = abs(objeto_layer.remaining_value - remaining_value_esperado)
        
        # PASO 5: Valores del layer (lo que Odoo tiene almacenado)
        qty_consumida = objeto_layer.quantity - objeto_layer.remaining_qty
        proporcion_restante = (objeto_layer.remaining_qty / objeto_layer.quantity * 100) if objeto_layer.quantity != 0 else 0
        proporcion_consumida = 100 - proporcion_restante
        
        # Umbrales considerando conversión USD-PYG (1 USD ≈ 7000-9000 PYG)
        # - < 100 PYG: Error de redondeo (OK)
        # - 100-1000 PYG: Error menor, posible centavo USD (WARNING)
        # - > 1000 PYG: Error significativo (ERROR)
        # También usar porcentaje: < 0.1% es aceptable
        porcentaje_diferencia = (diferencia_remaining_value / abs(objeto_layer.value) * 100) if objeto_layer.value != 0 else 0
        
        # Clasificar el tipo de error
        if diferencia_remaining_value < 100:
            remaining_value_correcto = True
            tipo_diferencia = "redondeo_normal"
        elif diferencia_remaining_value < 1000 or porcentaje_diferencia < 0.1:
            remaining_value_correcto = True  # Tolerable
            tipo_diferencia = "diferencia_menor"
        else:
            remaining_value_correcto = False
            tipo_diferencia = "diferencia_significativa"
        
        # Determinar estado del layer
        if objeto_layer.remaining_qty <= 0:
            estado = "consumido_totalmente"
        elif objeto_layer.remaining_qty == objeto_layer.quantity:
            estado = "sin_consumir"
        else:
            estado = "parcialmente_consumido"
        
        iterador.write(f"        tipo: \"entrada\"\n")
        iterador.write(f"        estado: \"{estado}\"\n")
        iterador.write(f"        qty_original: {objeto_layer.quantity}\n")
        iterador.write(f"        value_original: {format_num(objeto_layer.value)}\n")
        iterador.write(f"\n")
        
        # BLOQUE 1: INFORMACIÓN SUPUESTA (lo que tiene Odoo en BD)
        iterador.write(f"        informacion_supuesta:\n")
        iterador.write(f"          # Valores actuales en la base de datos de Odoo\n")
        iterador.write(f"          qty_restante: {objeto_layer.remaining_qty}\n")
        iterador.write(f"          value_restante: {format_num(objeto_layer.remaining_value)}\n")
        iterador.write(f"          qty_consumida: {qty_consumida}\n")
        iterador.write(f"          value_consumido: {format_num(objeto_layer.value - objeto_layer.remaining_value)}\n")
        iterador.write(f"          proporcion_restante: \"{round(proporcion_restante, 2)}%\"\n")
        iterador.write(f"          proporcion_consumida: \"{round(proporcion_consumida, 2)}%\"\n")
        iterador.write(f"\n")
        
        # BLOQUE 2: INFORMACIÓN ESPERADA (lo que dice el simulador)
        iterador.write(f"        informacion_esperada:\n")
        iterador.write(f"          # Valores calculados por el simulador FIFO (desde el origen)\n")
        iterador.write(f"          qty_restante: {remaining_qty_esperado}\n")
        iterador.write(f"          value_restante: {format_num(remaining_value_esperado)}\n")
        iterador.write(f"          qty_consumida_por_salidas: {qty_consumida_por_salidas}\n")
        iterador.write(f"          total_salidas_que_consumieron: {total_salidas}\n")
        proporcion_restante_esperado = (remaining_qty_esperado / objeto_layer.quantity * 100) if objeto_layer.quantity != 0 else 0
        proporcion_consumida_esperado = 100 - proporcion_restante_esperado
        iterador.write(f"          proporcion_restante: \"{round(proporcion_restante_esperado, 2)}%\"\n")
        iterador.write(f"          proporcion_consumida: \"{round(proporcion_consumida_esperado, 2)}%\"\n")
        iterador.write(f"\n")
        
        # BLOQUE 3: VALIDACIÓN Y DIFERENCIAS
        iterador.write(f"        validacion:\n")
        iterador.write(f"          diferencia_qty_restante: {diferencia_remaining_qty}\n")
        iterador.write(f"          diferencia_value_restante: {format_num(diferencia_remaining_value)}\n")
        iterador.write(f"          diferencia_value_porcentaje: \"{round(porcentaje_diferencia, 4)}%\"\n")
        iterador.write(f"          remaining_qty_correcto: {diferencia_remaining_qty == 0}\n")
        iterador.write(f"          remaining_value_correcto: {remaining_value_correcto}\n")
        iterador.write(f"          tipo_diferencia: \"{tipo_diferencia}\"\n")
        
        # BLOQUE 4: ALERTAS Y ACCIONES RECOMENDADAS
        if diferencia_remaining_qty > 0 or not remaining_value_correcto:
            iterador.write(f"\n")
            iterador.write(f"        alertas:\n")
            
            if diferencia_remaining_qty > 0:
                iterador.write(f"          - tipo: \"ERROR_QTY\"\n")
                iterador.write(f"            mensaje: \"remaining_qty incorrecto\"\n")
                iterador.write(f"            diferencia: {diferencia_remaining_qty}\n")
                iterador.write(f"            accion: \"Actualizar remaining_qty de {objeto_layer.remaining_qty} a {remaining_qty_esperado}\"\n")
            
            if not remaining_value_correcto:
                iterador.write(f"          - tipo: \"ERROR_VALUE\"\n")
                iterador.write(f"            mensaje: \"Diferencia significativa en remaining_value (> 1000 PYG o > 0.1%)\"\n")
                iterador.write(f"            diferencia: {format_num(diferencia_remaining_value)}\n")
                iterador.write(f"            porcentaje: \"{round(porcentaje_diferencia, 4)}%\"\n")
                iterador.write(f"            accion: \"Actualizar remaining_value de {format_num(objeto_layer.remaining_value)} a {format_num(remaining_value_esperado)}\"\n")
        elif tipo_diferencia == "diferencia_menor":
            iterador.write(f"\n")
            iterador.write(f"        nota: \"Diferencia menor (< 1000 PYG), posible redondeo en conversión USD-PYG\"\n")
        
        # Información sobre consumo (si hay salidas)
        if total_salidas > 0:
            iterador.write(f"\n")
            iterador.write(f"        consumo_detallado:\n")
            iterador.write(f"          total_salidas: {total_salidas}\n")
            iterador.write(f"          layer_salidas_ids: [{', '.join(str(id) for id in layers_salida_ids)}]\n")
        else:
            if estado == "parcialmente_consumido" or estado == "consumido_totalmente":
                iterador.write(f"\n")
                iterador.write(f"        alerta_critica: \"Layer marcado como consumido pero el simulador no encontró salidas asociadas\"\n")
        
        # Información sobre consumo
        if total_salidas > 0:
            iterador.write(f"        # Información sobre consumo\n")
            iterador.write(f"        consumido_por_layers: {total_salidas}\n")
            iterador.write(f"        layer_salidas_ids: [{', '.join(str(id) for id in layers_salida_ids)}]\n")
        else:
            if estado == "parcialmente_consumido" or estado == "consumido_totalmente":
                iterador.write(f"        alerta_not_layers_salida: \"Layer consumido pero no se encontraron layers de salida asociados\"\n")
    
    elif es_salida:
        # Análisis para layers de SALIDA
        iterador.write(f"        # Análisis para layers de SALIDA\n")
        iterador.write(f"        tipo: \"salida\"\n")
        iterador.write(f"        qty_salida: {abs(objeto_layer.quantity)}\n")
        iterador.write(f"        value_salida: {format_num(abs(objeto_layer.value))}\n")
        iterador.write(f"        unit_cost_usado: {objeto_layer.unit_cost}\n")
        
        # Buscar layer de entrada del que se consumió
        if objeto_layer.stock_valuation_layer_id:
            layer_padre = objeto_layer.stock_valuation_layer_id
            iterador.write(f"        # Buscar layer de entrada del que se consumió\n")
            iterador.write(f"          layer_id: {layer_padre.id}\n")
            iterador.write(f"          layer_create_date: \"{layer_padre.create_date}\"\n")
            iterador.write(f"          layer_unit_cost: {layer_padre.unit_cost}\n")
            iterador.write(f"          layer_description: \"{format_yaml_string(layer_padre.description)}\"\n")
            
            # Validar que el unit_cost coincida
            unit_cost_coincide = abs(objeto_layer.unit_cost - layer_padre.unit_cost) < 0.01
            iterador.write(f"          unit_cost_coincide: {unit_cost_coincide}\n")
            
            if not unit_cost_coincide:
                iterador.write(f"          diferencia_unit_cost: {abs(objeto_layer.unit_cost - layer_padre.unit_cost)}\n")
                iterador.write(f"          alerta_not_unit_cost_coincide: \"El unit_cost de la salida no coincide con el layer padre\"\n")
        else:
            iterador.write(f"        alerta_not_objeto_layer_stock_valuation_layer_id: \"Layer de salida sin referencia a layer de entrada (stock_valuation_layer_id)\"\n")
    
    else:
        # Cantidad = 0 (caso raro)
        iterador.write(f"        # Cantidad = 0 (caso raro)\n")
        iterador.write(f"        tipo: \"neutral\"\n")
        iterador.write(f"        alerta_raro: \"Layer con cantidad = 0\"\n")

def info_account_move_line(iterador, objeto_move_line, objeto_purchase_order_line):
    purchase_order = objeto_purchase_order_line.order_id

    if objeto_move_line:
        quantity = objeto_move_line.quantity
        balance = objeto_move_line.balance
        price_unit_calculated = round(balance / quantity, 2) if quantity != 0 else 0
        
        iterador.write(f"      purchase_order:\n")
        iterador.write(f"        id: {purchase_order.id}\n")
        iterador.write(f"        name: \"{format_yaml_string(purchase_order.name)}\"\n")
        iterador.write(f"        date_order: \"{purchase_order.date_order}\"\n")
        iterador.write(f"        currency: \"{purchase_order.currency_id.name}\"\n")
        iterador.write(f"        state: \"{purchase_order.state}\"\n")
        
        iterador.write(f"      account_move_line:\n")
        iterador.write(f"        id: {objeto_move_line.id}\n")
        iterador.write(f"        name: \"{format_yaml_string(objeto_move_line.name)}\"\n")
        iterador.write(f"        quantity: {quantity}\n")
        iterador.write(f"        balance: {balance}\n")
        iterador.write(f"        price_unit_original: {objeto_move_line.price_unit}\n")
        iterador.write(f"        price_unit_calculated: {price_unit_calculated}\n")
        iterador.write(f"        currency: \"{objeto_move_line.currency_id.name if objeto_move_line.currency_id else 'N/A'}\"\n")
        
        iterador.write(f"      invoice_info:\n")
        iterador.write(f"        id: {objeto_move_line.move_id.id}\n")
        iterador.write(f"        name: \"{format_yaml_string(objeto_move_line.move_id.name)}\"\n")
        iterador.write(f"        date: \"{objeto_move_line.fecha_vencimiento_fe or objeto_move_line.move_id.date}\"\n")
        iterador.write(f"        state: \"{objeto_move_line.move_id.state}\"\n")
        iterador.write(f"        amount_total: {objeto_move_line.move_id.amount_total}\"\n")
    else:
        iterador.write(f"      purchase_order:\n")
        iterador.write(f"        id: {purchase_order.id}\n")
        iterador.write(f"        name: \"{format_yaml_string(purchase_order.name)}\"\n")
        iterador.write(f"        date_order: \"{purchase_order.date_order}\"\n")
        iterador.write(f"        currency: \"{purchase_order.currency_id.name}\"\n")
        iterador.write(f"        state: \"{purchase_order.state}\"\n")
        iterador.write(f"      account_move_line: null\n")
        iterador.write(f"      observacion: \"No se encontró account_move_line para esta purchase_line\"\n")

    return 

def info_resumen_productos(iterador, contador1, contador2, objeto_layer):
    iterador.write(f"  resumen_producto:\n")
    iterador.write(f"    layers_con_purchase: {contador1}\n")
    iterador.write(f"    layers_sin_purchase: {contador2}\n")
    iterador.write(f"    total_layers: {len(objeto_layer)}\n")
    iterador.write(f"    completitud: \"{round((contador1/len(objeto_layer))*100, 1)}%\"\n\n")

def info_resumen_fifo_producto(iterador, layers, env, resultado_fifo=None, correcciones=None):
    """
    Genera un resumen FIFO para todos los layers de un producto.
    
    Args:
        iterador: Archivo de salida YAML
        layers: Lista de layers del producto
        env: Environment de Odoo
        resultado_fifo: Resultado de simular_fifo_producto() (opcional)
        correcciones: Lista de correcciones realizadas por algoritmo1 (opcional)
    """
    iterador.write(f"  resumen_fifo:\n")
    
    # Obtener simulación si no se pasó
    if resultado_fifo is None and len(layers) > 0 and simular_fifo_producto is not None:
        resultado_fifo = simular_fifo_producto(env, layers[0].product_id.id)
    
    # Filtrar layers de entrada y salida
    layers_entrada = [l for l in layers if l.quantity > 0]
    layers_salida = [l for l in layers if l.quantity < 0]
    
    # Análisis de layers de entrada
    layers_con_stock = [l for l in layers_entrada if l.remaining_qty > 0]
    layers_consumidos = [l for l in layers_entrada if l.remaining_qty <= 0]
    
    # Cálculos totales
    total_qty_entrada = sum(l.quantity for l in layers_entrada)
    total_value_entrada = sum(l.value for l in layers_entrada)
    total_remaining_qty = sum(l.remaining_qty for l in layers_entrada)
    total_remaining_value = sum(l.remaining_value for l in layers_entrada)
    
    total_qty_salida = sum(abs(l.quantity) for l in layers_salida)
    total_value_salida = sum(abs(l.value) for l in layers_salida)
    
    # ============================================================
    # USAR INFORMACIÓN DE CORRECCIONES SI ESTÁ DISPONIBLE
    # ============================================================
    layers_corregidos_qty = []
    layers_corregidos_value = []
    
    if correcciones:
        for corr in correcciones:
            if corr.get('tuvo_error_qty', False):
                layers_corregidos_qty.append(corr['layer_id'])
            if corr.get('tuvo_error_value', False):
                layers_corregidos_value.append(corr['layer_id'])
    
    # Validaciones mejoradas con valores esperados
    layers_con_diferencia_significativa_value = []
    layers_con_diferencia_menor_value = []
    layers_con_redondeo_normal = []
    layers_con_diferencia_qty = []
    
    # Totales esperados (usando simulador si está disponible)
    total_remaining_qty_esperado = 0
    total_remaining_value_esperado = 0
    
    for layer in layers_entrada:
        # Usar datos del simulador si está disponible
        if resultado_fifo and layer.id in resultado_fifo['entradas']:
            entrada_info = resultado_fifo['entradas'][layer.id]
            remaining_qty_esperado = entrada_info['remaining_qty_simulado']
            remaining_value_esperado = entrada_info['remaining_value_simulado']
        else:
            # Fallback: método antiguo con búsqueda directa
            if layer.quantity > 0:
                # Buscar salidas asociadas
                salidas = env['stock.valuation.layer'].search([
                    ('stock_valuation_layer_id', '=', layer.id),
                    ('quantity', '<', 0)
                ])
                qty_consumida_por_salidas = sum(abs(s.quantity) for s in salidas)
                
                # Calcular valores esperados
                remaining_qty_esperado = layer.quantity - qty_consumida_por_salidas
                remaining_value_esperado = (remaining_qty_esperado / layer.quantity * layer.value) if layer.quantity != 0 else 0
            else:
                remaining_qty_esperado = 0
                remaining_value_esperado = 0
        
        # Acumular totales esperados
        total_remaining_qty_esperado += remaining_qty_esperado
        total_remaining_value_esperado += remaining_value_esperado
        
        # Validar remaining_qty
        if abs(layer.remaining_qty - remaining_qty_esperado) > 0:
            layers_con_diferencia_qty.append(layer.id)
        
        # Validar remaining_value
        diferencia = abs(layer.remaining_value - remaining_value_esperado)
        porcentaje_dif = (diferencia / abs(layer.value) * 100) if layer.value != 0 else 0
        
        # Clasificar según umbrales
        if diferencia < 100:
            layers_con_redondeo_normal.append(layer.id)
        elif diferencia < 1000 or porcentaje_dif < 0.1:
            layers_con_diferencia_menor_value.append(layer.id)
        else:
            layers_con_diferencia_significativa_value.append(layer.id)

    iterador.write(f"    layers_entrada_total: {len(layers_entrada)}\n")
    iterador.write(f"    layers_salida_total: {len(layers_salida)}\n")
    iterador.write(f"    layers_con_stock_disponible: {len(layers_con_stock)}\n")
    iterador.write(f"    layers_completamente_consumidos: {len(layers_consumidos)}\n")
    
    # TOTALES ACTUALES (valores en Odoo)
    iterador.write(f"    total_qty_entrada: {total_qty_entrada}\n")
    iterador.write(f"    total_qty_salida: {total_qty_salida}\n")
    iterador.write(f"    total_qty_disponible_actual: {total_remaining_qty}\n")
    iterador.write(f"    total_value_entrada: {format_num(total_value_entrada)}\n")
    iterador.write(f"    total_value_salida: {format_num(total_value_salida)}\n")
    iterador.write(f"    total_value_stock_actual: {format_num(total_remaining_value)}\n")
    
    # TOTALES ESPERADOS (basados en salidas reales)
    iterador.write(f"    total_qty_disponible_esperado: {total_remaining_qty_esperado}\n")
    iterador.write(f"    total_value_stock_esperado: {format_num(total_remaining_value_esperado)}\n")
    
    # DIFERENCIAS TOTALES
    diferencia_qty_total = abs(total_remaining_qty - total_remaining_qty_esperado)
    diferencia_value_total = abs(total_remaining_value - total_remaining_value_esperado)
    iterador.write(f"    diferencia_qty_total: {diferencia_qty_total}\n")
    iterador.write(f"    diferencia_value_total: {format_num(diferencia_value_total)}\n")
    
    # ============================================================
    # REPORTAR LAYERS CORREGIDOS (antes de la corrección)
    # ============================================================
    if layers_corregidos_qty:
        iterador.write(f"\n")
        iterador.write(f"    # LAYERS CORREGIDOS POR ALGORITMO1\n")
        iterador.write(f"    layers_corregidos_qty: {len(layers_corregidos_qty)}\n")
        iterador.write(f"    layer_ids_corregidos_qty: [{', '.join(map(str, layers_corregidos_qty))}]\n")
        iterador.write(f"    nota_correccion_qty: \"Estos layers tenían remaining_qty incorrecto y fueron corregidos\"\n")
    
    if layers_corregidos_value:
        iterador.write(f"\n")
        iterador.write(f"    layers_corregidos_value: {len(layers_corregidos_value)}\n")
        iterador.write(f"    layer_ids_corregidos_value: [{', '.join(map(str, layers_corregidos_value))}]\n")
        iterador.write(f"    nota_correccion_value: \"Estos layers tenían remaining_value incorrecto y fueron corregidos\"\n")
    
    # VALIDACIONES DE REMAINING_QTY (estado actual después de correcciones)
    if layers_con_diferencia_qty:
        iterador.write(f"\n")
        iterador.write(f"    layers_con_error_qty: {len(layers_con_diferencia_qty)}\n")
        iterador.write(f"    layer_ids_error_qty: [{', '.join(map(str, layers_con_diferencia_qty))}]\n")
        iterador.write(f"    alerta_qty: \"Layers con remaining_qty incorrecto (después de algoritmo1)\"\n")
    
    # VALIDACIONES DE REMAINING_VALUE (estado actual después de correcciones)
    if layers_con_diferencia_significativa_value:
        iterador.write(f"\n")
        iterador.write(f"    layers_diferencia_significativa_value: {len(layers_con_diferencia_significativa_value)}\n")
        iterador.write(f"    layer_ids_error_significativo: [{', '.join(map(str, layers_con_diferencia_significativa_value))}]\n")
        iterador.write(f"    alerta_value: \"Layers con diferencia > 1000 PYG o > 0.1% - REVISAR (después de algoritmo1)\"\n")
    
    if layers_con_diferencia_menor_value:
        iterador.write(f"\n")
        iterador.write(f"    layers_diferencia_menor_value: {len(layers_con_diferencia_menor_value)}\n")
        iterador.write(f"    layer_ids_diferencia_menor: [{', '.join(map(str, layers_con_diferencia_menor_value))}]\n")
        iterador.write(f"    nota: \"Diferencias menores (100-1000 PYG), posible conversión USD-PYG\"\n")
    
    if layers_con_redondeo_normal:
        iterador.write(f"\n")
        iterador.write(f"    layers_redondeo_normal: {len(layers_con_redondeo_normal)}\n")
        iterador.write(f"    nota_redondeo: \"Diferencias < 100 PYG (redondeo normal)\"\n")
    
    # Cálculo de costo promedio ponderado
    if total_remaining_qty > 0:
        costo_promedio_actual = total_remaining_value / total_remaining_qty
        iterador.write(f"\n")
        iterador.write(f"    costo_promedio_ponderado_actual: {format_num(costo_promedio_actual)}\n")
    
    if total_remaining_qty_esperado > 0:
        costo_promedio_esperado = total_remaining_value_esperado / total_remaining_qty_esperado
        iterador.write(f"    costo_promedio_ponderado_esperado: {format_num(costo_promedio_esperado)}\n")
    
    iterador.write(f"\n")

def info_resumen_final(iterador, count1, count2, count3, count4, enviroment):
    # contador_producto = count1
    # productos_con_dato = count2
    # productos_sin_dato = count3
    # total_layers_analizados = count4
    iterador.write(f"# ========================================\n")
    iterador.write(f"# RESUMEN FINAL DEL ANÁLISIS\n")
    iterador.write(f"# ========================================\n")
    iterador.write(f"resumen_general:\n")
    iterador.write(f"  productos_analizados: {count1}\n")
    iterador.write(f"  productos_con_datos: {count2}\n")
    iterador.write(f"  productos_sin_datos: {count3}\n")
    iterador.write(f"  total_layers_analizados: {count4}\n")
    iterador.write(f"  fecha_analisis: \"{enviroment.cr.now()}\"\n")

def corregir_layer_con_factura(layer, account_move_line):
    """
    Corrige un layer específico con datos de factura (sin escribir a YAML).
    
    Parámetros:
    - layer: Stock Valuation Layer a corregir
    - account_move_line: Línea contable con datos de factura
    
    Returns:
    - bool: True si se actualizó, False si no
    """
    if not account_move_line or account_move_line.quantity <= 0:
        return False
    
    # Calcular valores correctos desde factura
    balance = abs(account_move_line.balance)
    quantity = account_move_line.quantity
    unit_cost_nuevo = round(balance / quantity, 3)
    
    # Actualizar layer
    layer.write({
        'unit_cost': unit_cost_nuevo,
        'value': balance,
    })
    
    return True

def actualizar_layers_con_facturas(env, layers):
    """
    PASADA 1: Actualiza todos los layers con datos de facturas ANTES de simular.
    
    Esta función debe ejecutarse ANTES del simulador FIFO para que el simulador
    trabaje con valores correctos (de facturas) en lugar de valores corruptos de Odoo.
    
    Parámetros:
    - env: Environment de Odoo
    - layers: Lista de layers a procesar
    
    Returns:
    - dict: Estadísticas de actualización
    """
    actualizados = 0
    sin_factura = 0
    sin_purchase = 0
    
    for layer in layers:
        # Solo procesar layers de entrada
        if layer.quantity <= 0:
            continue
        
        # Buscar purchase_order_line
        stock_move = layer.stock_move_id
        purchase_order_line = stock_move.purchase_line_id if stock_move else None
        
        if not purchase_order_line:
            sin_purchase += 1
            continue
        
        # Buscar account_move_line (factura)
        account_move_line = env['account.move.line'].search([
            ('purchase_line_id', '=', purchase_order_line.id),
            ('parent_state', '=', 'posted'),
            ('display_type', '=', False),
        ], limit=1)
        
        if not account_move_line:
            sin_factura += 1
            continue
        
        # Actualizar layer con datos de factura
        if corregir_layer_con_factura(layer, account_move_line):
            actualizados += 1
    
    return {
        'actualizados': actualizados,
        'sin_factura': sin_factura,
        'sin_purchase': sin_purchase,
        'total': len(layers),
    }

def _algoritmo_ppd(iterador, layer, account_move_line):
    """
    **Algoritmo para Precio Promedio Ponderado (PPD)**
    
    Solo actualiza value y unit_cost desde factura.
    No toca remaining_qty ni remaining_value (Odoo los maneja automáticamente en PPD).
    
    Parámetros:
    - iterador: Archivo YAML
    - layer: Stock Valuation Layer
    - account_move_line: Línea contable con factura
    
    Returns:
    - dict: Información sobre la corrección realizada
    """
    # Extraer valores del layer (valores actuales antes de cualquier cambio)
    layer_data = {
        'quantity': layer.quantity,
        'unit_cost': layer.unit_cost,
        'value': layer.value
    }
    
    # Extraer valores de la factura (si existe)
    invoice_data = {
        'quantity': account_move_line.quantity if account_move_line else 0.0,
        'balance': abs(account_move_line.balance) if account_move_line else 0.0
    }   
    
    # Variables para el análisis
    tiene_factura = account_move_line is not None
    diferencia_original = abs(layer_data['value'] - invoice_data['balance']) if tiene_factura else 0.0
    
    # PASO 1: REALIZAR LA ACTUALIZACIÓN (SI CORRESPONDE)
    unit_cost_nuevo = None
    value_nuevo = None
    se_actualizo = False
    
    if tiene_factura and invoice_data['quantity'] > 0:
        unit_cost_nuevo = round(invoice_data['balance'] / invoice_data['quantity'], 3)
        value_nuevo = invoice_data['balance']

        # Ejecutar la actualización
        layer.write({
            'unit_cost': unit_cost_nuevo,
            'value': value_nuevo,
        })
        se_actualizo = True

    # PASO 2: CLASIFICACIÓN
    if tiene_factura:
        if diferencia_original > 1000:
            correction_type = "PPD - USD-PYG ajuste grande (corregido)"
        elif 0 < diferencia_original < 1000:
            correction_type = "PPD - USD-PYG ajuste pequeño (corregido)"
        elif diferencia_original == 0:
            correction_type = "PPD - Estaba correcto"
        else:
            correction_type = "PPD - Revisión necesaria"
    else:
        correction_type = "PPD - Sin factura"
    
    # PASO 3: ESCRIBIR AL YAML
    iterador.write(f'      actualizacion_analisis:\n')
    iterador.write(f'        metodo_costeo: "PPD"\n')
    iterador.write(f'        tiene_factura: {tiene_factura}\n')
    iterador.write(f'        se_actualizo: {se_actualizo}\n')
    iterador.write(f'        layer_quantity: {layer_data["quantity"]}\n')
    iterador.write(f'        invoice_quantity: {invoice_data["quantity"]}\n')
    iterador.write(f'        layer_value_original: {format_num(layer_data["value"])}\n')
    iterador.write(f'        layer_value_nuevo: {format_num(value_nuevo or layer_data["value"])}\n')
    iterador.write(f'        invoice_balance: {format_num(invoice_data["balance"])}\n')
    iterador.write(f'        diferencia_value: {format_num(diferencia_original)}\n')
    iterador.write(f'        layer_unit_cost_original: {format_num(layer_data["unit_cost"])}\n')
    iterador.write(f'        layer_unit_cost_nuevo: {format_num(unit_cost_nuevo or layer_data["unit_cost"])}\n')
    iterador.write(f'        correction_type: "{correction_type}"\n')
    
    # RETORNAR INFORMACIÓN SOBRE LA CORRECCIÓN
    return {
        'layer_id': layer.id,
        'se_actualizo': se_actualizo,
        'diferencia_value': diferencia_original,
    }

def _algoritmo_fifo(iterador, layer, account_move_line, resultado_fifo):
    """
    **Algoritmo para FIFO**
    
    Actualiza:
    1. value y unit_cost desde factura
    2. remaining_qty y remaining_value desde simulador
    
    Parámetros:
    - iterador: Archivo YAML
    - layer: Stock Valuation Layer
    - account_move_line: Línea contable con factura
    - resultado_fifo: Resultado del simulador FIFO
    """
    # VALORES ORIGINALES (antes de cualquier cambio)
    layer_data_original = {
        'quantity': layer.quantity,
        'unit_cost': layer.unit_cost,
        'value': layer.value,
        'remaining_qty': layer.remaining_qty,
        'remaining_value': layer.remaining_value,
    }
    
    # Extraer valores de la factura
    invoice_data = {
        'quantity': account_move_line.quantity if account_move_line else 0.0,
        'balance': abs(account_move_line.balance) if account_move_line else 0.0
    }
    
    tiene_factura = account_move_line is not None
    
    # ============================================================
    # PARTE 1: ACTUALIZAR VALUE Y UNIT_COST DESDE FACTURA
    # ============================================================
    unit_cost_nuevo = None
    value_nuevo = None
    actualizado_factura = False
    diferencia_value = 0.0
    
    if tiene_factura and invoice_data['quantity'] > 0:
        unit_cost_nuevo = round(invoice_data['balance'] / invoice_data['quantity'], 3)
        value_nuevo = invoice_data['balance']
        diferencia_value = abs(layer_data_original['value'] - value_nuevo)
        
        # Actualizar value y unit_cost
        layer.write({
            'unit_cost': unit_cost_nuevo,
            'value': value_nuevo,
        })
        actualizado_factura = True
    
    # ============================================================
    # PARTE 2: ACTUALIZAR REMAINING_QTY Y REMAINING_VALUE DESDE SIMULADOR
    # ============================================================
    remaining_qty_nuevo = None
    remaining_value_nuevo = None
    actualizado_simulador = False
    diferencia_remaining_qty = 0.0
    diferencia_remaining_value = 0.0
    
    if resultado_fifo and layer.id in resultado_fifo['entradas']:
        entrada_info = resultado_fifo['entradas'][layer.id]
        remaining_qty_nuevo = entrada_info['remaining_qty_simulado']
        remaining_value_nuevo = entrada_info['remaining_value_simulado']
        
        diferencia_remaining_qty = abs(layer_data_original['remaining_qty'] - remaining_qty_nuevo)
        diferencia_remaining_value = abs(layer_data_original['remaining_value'] - remaining_value_nuevo)
        
        # Actualizar remaining_qty y remaining_value
        layer.write({
            'remaining_qty': remaining_qty_nuevo,
            'remaining_value': remaining_value_nuevo,
        })
        actualizado_simulador = True
    
    # ============================================================
    # CLASIFICACIÓN
    # ============================================================
    if tiene_factura and actualizado_simulador:
        correction_type = "FIFO - Corregido desde factura + simulador"
    elif tiene_factura:
        correction_type = "FIFO - Corregido solo desde factura (sin simulador)"
    elif actualizado_simulador:
        correction_type = "FIFO - Corregido solo desde simulador (sin factura)"
    else:
        correction_type = "FIFO - Sin corrección"
    
    # ============================================================
    # ESCRIBIR AL YAML
    # ============================================================
    iterador.write(f'      actualizacion_analisis:\n')
    iterador.write(f'        metodo_costeo: "FIFO"\n')
    iterador.write(f'        tiene_factura: {tiene_factura}\n')
    iterador.write(f'        tiene_simulador: {resultado_fifo is not None}\n')
    iterador.write(f'        actualizado_factura: {actualizado_factura}\n')
    iterador.write(f'        actualizado_simulador: {actualizado_simulador}\n')
    iterador.write(f'\n')
    
    # Bloque 1: Valores de factura
    iterador.write(f'        factura:\n')
    iterador.write(f'          quantity: {invoice_data["quantity"]}\n')
    iterador.write(f'          balance: {format_num(invoice_data["balance"])}\n')
    iterador.write(f'          value_original: {format_num(layer_data_original["value"])}\n')
    iterador.write(f'          value_nuevo: {format_num(value_nuevo or layer_data_original["value"])}\n')
    iterador.write(f'          diferencia_value: {format_num(diferencia_value)}\n')
    iterador.write(f'          unit_cost_original: {format_num(layer_data_original["unit_cost"])}\n')
    iterador.write(f'          unit_cost_nuevo: {format_num(unit_cost_nuevo or layer_data_original["unit_cost"])}\n')
    iterador.write(f'\n')
    
    # Bloque 2: Valores del simulador
    iterador.write(f'        simulador:\n')
    iterador.write(f'          remaining_qty_original: {layer_data_original["remaining_qty"]}\n')
    iterador.write(f'          remaining_qty_nuevo: {remaining_qty_nuevo if remaining_qty_nuevo is not None else layer_data_original["remaining_qty"]}\n')
    iterador.write(f'          diferencia_remaining_qty: {diferencia_remaining_qty}\n')
    iterador.write(f'          remaining_value_original: {format_num(layer_data_original["remaining_value"])}\n')
    iterador.write(f'          remaining_value_nuevo: {format_num(remaining_value_nuevo if remaining_value_nuevo is not None else layer_data_original["remaining_value"])}\n')
    iterador.write(f'          diferencia_remaining_value: {format_num(diferencia_remaining_value)}\n')
    iterador.write(f'\n')
    
    iterador.write(f'        correction_type: "{correction_type}"\n')
    
    # RETORNAR INFORMACIÓN SOBRE LA CORRECCIÓN
    return {
        'layer_id': layer.id,
        'actualizado_factura': actualizado_factura,
        'actualizado_simulador': actualizado_simulador,
        'diferencia_value': diferencia_value,
        'diferencia_remaining_qty': diferencia_remaining_qty,
        'diferencia_remaining_value': diferencia_remaining_value,
        'tuvo_error_qty': diferencia_remaining_qty > 0,
        'tuvo_error_value': diferencia_remaining_value > 1000,  # Umbral significativo
    }

def algoritmo1(iterador, layer, account_move_line, producto_obj, resultado_fifo=None):
    """
    **Algoritmo 1 - Maestro de actualización**
    
    Delega a sub-algoritmos según el método de costeo:
    - FIFO: Actualiza value, unit_cost, remaining_qty, remaining_value
    - PPD: Actualiza solo value y unit_cost
    
    Parámetros:
    - iterador: Archivo YAML
    - layer: Stock Valuation Layer
    - account_move_line: Línea contable con factura
    - producto_obj: Objeto producto (para obtener método de costeo)
    - resultado_fifo: Resultado del simulador FIFO (opcional)
    
    Returns:
    - dict: Información sobre la corrección realizada
    """
    metodo_costeo = producto_obj.categ_id.property_cost_method
    
    if metodo_costeo == 'fifo':
        return _algoritmo_fifo(iterador, layer, account_move_line, resultado_fifo)
    elif metodo_costeo == 'average':
        return _algoritmo_ppd(iterador, layer, account_move_line)
    else:
        # Método de costeo no soportado
        iterador.write(f'      actualizacion_analisis:\n')
        iterador.write(f'        error: "Método de costeo no soportado: {metodo_costeo}"\n')
        iterador.write(f'        metodo_costeo: "{metodo_costeo}"\n')
        return {
            'layer_id': layer.id,
            'error': True,
            'metodo_costeo': metodo_costeo,
        }


anho = 2025
meses = meses_anho(anho)
# Prueba de búsquedas de productos
direccion = '/home/jose/Documentos/clientes/15FONDOESTRELLA/clean_valuation/python/valoracion/actualizacion_layers.yaml'
categoria_auto = env['product.category'].search([
    ('property_cost_method', '=', 'fifo'),
    ('property_valuation', '=', 'real_time'),
])

for cat in categoria_auto:
    diccionario = get_product_category(categoria=cat, enviroment=env)
    product_product = diccionario.get('records_product_product', [])

    if not product_product:
        continue

    # 3281 con mejor cantidad de errores
    # opciones = [1632, 1772, 3281, 3535, 4899]
    # opciones = [3281, 1933, 1943, 2671]
    opciones = [2671]
    product_product = product_product.filtered(lambda x: x.id in [2671])

    # impresion_csv(direccion, prueba_nahuel)
    with open(direccion, 'w') as f:
        print(f"Iniciando análisis de {len(product_product)} productos únicos...")

        # Escribir cabecera global del archivo YAML
        info_cabecera_principal(iterador=f, enviroment=env, lista=product_product)
        contador_productos = 0
        total_layers_analizados = 0
        productos_con_datos = 0
        productos_sin_datos = 0

        for producto_obj in product_product:
            contador_productos += 1

            # Buscar layers para este producto
            layers = buscar_layers(
                env=env,
                producto=producto_obj,
                orden="asc",
                signo=None,
                cantidad=None,
                # fecha_inicio=get_fecha_min_layer(producto_obj.id),
                fecha_inicio='2025-01-30',
                fecha_fin=None,
            )

            if not layers:
                continue

            # ============================================================
            # PASADA 1: ACTUALIZAR LAYERS CON FACTURAS PRIMERO
            # ============================================================
            # Obtener TODOS los layers del producto (no solo los filtrados por fecha)
            # para que el simulador tenga valores correctos desde el origen
            todos_los_layers = env['stock.valuation.layer'].search([
                ('product_id', '=', producto_obj.id)
            ], order='create_date asc, id asc')
            
            print(f"\n{'='*80}")
            print(f"Producto {producto_obj.id} - {producto_obj.name}")
            print(f"{'='*80}")
            print(f"PASADA 1: Actualizando layers con datos de facturas...")
            stats = actualizar_layers_con_facturas(env, todos_los_layers)
            print(f"  ✅ Actualizados: {stats['actualizados']}")
            print(f"  ⚠️  Sin factura: {stats['sin_factura']}")
            print(f"  ⚠️  Sin purchase: {stats['sin_purchase']}")
            print(f"  📊 Total layers: {stats['total']}")
            
            # ============================================================
            # PASADA 2: EJECUTAR SIMULACIÓN FIFO (con valores ya corregidos)
            # ============================================================
            resultado_fifo = None
            if simular_fifo_producto is not None:
                fecha_min = get_fecha_min_layer(producto_obj.id)
                print(f"\nPASADA 2: Ejecutando simulación FIFO desde el ORIGEN...")
                print(f"  Fecha mínima (origen): {fecha_min}")
                print(f"  Layers a analizar (desde {layers[0].create_date if layers else 'N/A'}): {len(layers)}")
                
                # Simulador desde el ORIGEN (ahora con valores corregidos)
                resultado_fifo = simular_fifo_producto(env, producto_obj.id, fecha_inicio=None, fecha_fin=None)
                print(f"  ✅ Simulación completada: {resultado_fifo['total_entradas']} entradas, {resultado_fifo['total_salidas']} salidas")
            else:
                print(f"⚠️ Simulador FIFO no disponible - usando método tradicional")

            # Escribir cabecera del producto
            total_layers_analizados += len(layers)
            info_cabecera_productos(
                iterador=f,
                count=contador_productos,
                producto=product_product,
                id=producto_obj.id,
                objeto=producto_obj,
                valoracion=layers)

            # Lista para almacenar información de correcciones
            correcciones_realizadas = []
            
            layers_con_purchase = 0
            layers_sin_purchase = 0
            for index, layer in enumerate(layers, 1):
                # Algoritmo para cruzar 'stock.valuation.layer' con 'purchase.order.line'
                stock_move = layer.stock_move_id
                purchase_order_line = stock_move.purchase_line_id if stock_move else None

                # Verificar que existe purchase_order_line
                if not purchase_order_line:
                    layers_sin_purchase += 1
                    info_not_purchase_order_line(
                        iterador=f,
                        indice=index,
                        objeto1=layer,
                        objeto2=stock_move)
                    # FIFO Analysis para layers sin purchase
                    info_fifo_analysis(iterador=f, objeto_layer=layer, env=env, resultado_fifo=resultado_fifo)
                    continue

                layers_con_purchase += 1

                # Buscar account_move_line
                account_move_line = env['account.move.line'].search([
                    ('purchase_line_id', '=', purchase_order_line.id),
                    ('move_id.move_type', '=', 'in_invoice')
                ], order='create_date asc', limit=1)

                # Impresiones de los diferentes modelos
                info_layer_encontrado(iterador=f, indice=index, objeto1=layer, objeto2=account_move_line)
                info_layer_completo(iterador=f, objeto_layer=layer)
                info_stock_move(iterador=f, object_stock_move=stock_move)
                info_purchase_order_line(iterador=f, object_purchase_order_line=purchase_order_line)
                info_account_move_line(
                    iterador=f,
                    objeto_move_line=account_move_line,
                    objeto_purchase_order_line=purchase_order_line)            
                info_fifo_analysis(iterador=f, objeto_layer=layer, env=env, resultado_fifo=resultado_fifo)

                # Algoritmo 1 de actualización (polimórfico: FIFO o PPD)
                correccion_info = algoritmo1(iterador=f, layer=layer, account_move_line=account_move_line, 
                          producto_obj=producto_obj, resultado_fifo=resultado_fifo)
                
                # Guardar información de corrección si hubo cambios significativos
                if correccion_info:
                    correcciones_realizadas.append(correccion_info)

                f.write(f"\n")
            # Resumen del producto
            if layers_con_purchase > 0:
                productos_con_datos += 1
            else:
                productos_sin_datos += 1

            info_resumen_productos(
                iterador=f,
                contador1=layers_con_purchase,
                contador2=layers_sin_purchase,
                objeto_layer=layers)
            
            # Resumen FIFO específico (ahora con información de correcciones)
            info_resumen_fifo_producto(iterador=f, layers=layers, env=env, 
                                      resultado_fifo=resultado_fifo, 
                                      correcciones=correcciones_realizadas)
            
            # GENERAR REPORTE DETALLADO DEL SIMULADOR (opcional)
            # Descomentar las siguientes líneas para generar un reporte TXT adicional con el detalle completo
            if generar_reporte_fifo_producto is not None:
                archivo_reporte = f'/home/jose/Documentos/clientes/15FONDOESTRELLA/clean_valuation/python/valoracion/reporte_fifo_producto_{producto_obj.id}.txt'
            reporte_simulador = generar_reporte_fifo_producto(env, producto_obj.id, archivo_reporte)
            print(f"Reporte detallado guardado en: {archivo_reporte}")

            # Log de progreso cada 10 productos
            if contador_productos % 10 == 0:
                print(f"Procesados {contador_productos}/{len(product_product)} productos...")

        # Escribir resumen final
        info_resumen_final(
            iterador=f,
            count1=contador_productos,
            count2=productos_con_datos,
            count3=productos_sin_datos,
            count4=total_layers_analizados,
            enviroment=env)
        print(f"\nAnálisis completado!")
        print(f"Resumen:")
        print(f"   - Productos analizados: {contador_productos}")
        print(f"   - Productos con datos completos: {productos_con_datos}")
        print(f"   - Productos sin datos: {productos_sin_datos}")
        print(f"   - Total layers procesados: {total_layers_analizados}")
        print(f"Archivo generado: {direccion}")
