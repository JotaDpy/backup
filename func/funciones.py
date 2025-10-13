# pylint: disable=undefined-variable
# pyright: reportUndefinedVariable=false
import re

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

def buscar_layers_positivos(
        env,
        producto: int,
        orden="desc",
        cantidad=None,
        fecha_inicio=None,
        fecha_fin=None):
    # Definimos el dominio de la búsqueda
    domain = [('product_id', '=', producto), ('quantity', '>', 0)]
    
    # Agregar filtros de fecha si se proporcionan
    if fecha_inicio:
        # Convertir string a datetime si es necesario
        if isinstance(fecha_inicio, str):
            from datetime import datetime
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
        # Convertir string a datetime si es necesario
        if isinstance(fecha_fin, str):
            from datetime import datetime
            try:
                fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').strftime('%Y-%m-%d 23:59:59')
            except ValueError:
                try:
                    fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
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

def cabecera_principal(iterador, enviroment, lista):
        # Escribir cabecera global del archivo YAML
    iterador.write("# ========================================\n")
    iterador.write("# ANÁLISIS MASIVO DE STOCK VALUATION LAYERS\n")
    iterador.write("# ========================================\n")
    iterador.write("# Generado automáticamente por actualizacion_layers.py\n")
    iterador.write(f"# Período analizado: Febrero 2025\n")
    iterador.write(f"# Total productos: {len(lista)}\n")
    iterador.write(f"# Fecha de análisis: {enviroment['res.users'].browse(enviroment.uid).name} - {enviroment.cr.now()}\n\n")

def cabecera_producto(
        iterador,
        count,
        lista,
        id,
        objeto,
        valoracion
    ):
        # Escribir cabecera del producto
        iterador.write(f"# ----------------------------------------\n")
        iterador.write(f"# PRODUCTO {count}/{len(lista)}\n")
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

def info_alg1_msg(iterador, objeto1, objeto2):
    """ Algoritmo 1 de actualización, se aplica a todos los layers que tienen el
    quantity > 0.
    objeto1: Stock Valuation Layer
    objeto2: Account Move Line
    """
    # Extraer valores del layer
    layer_data = {
        'quantity': objeto1.quantity,
        'unit_cost': objeto1.unit_cost,
        'value': objeto1.value
    }
    
    # Extraer valores de la factura (si existe)
    invoice_data = {
        'quantity': objeto2.quantity if objeto2 else 0.0,
        'balance': abs(objeto2.balance) if objeto2 else 0.0
    }
    
    # LÓGICA: Si tiene factura, SIEMPRE debe actualizarse
    tiene_factura = objeto2 is not None
    diferencia = abs(layer_data['value'] - invoice_data['balance']) if tiene_factura else 0.0
    
    # Calcular nuevo unit_cost basado en factura
    unit_cost_nuevo = None
    value_nuevo = None
    if tiene_factura and invoice_data['quantity'] > 0:
        unit_cost_nuevo = round(invoice_data['balance'] / invoice_data['quantity'], 3)
        value_nuevo = invoice_data['balance']  # El value debe ser igual al balance de la factura

    # Clasificación mejorada
    if tiene_factura:
        msg = {
            True: "Error con la diferencia",
            diferencia > 1000: "USD-PYG ajuste grande",
            0 < diferencia < 1000: "USD-PYG ajuste pequeño",
            diferencia == 0: "Estaba correcto, pero igual se actualiza"
        }
    else:
        msg = {True: "Sin factura"}
    
    iterador.write(f'      actualizacion_analisis:\n')
    iterador.write(f'        tiene_factura: {tiene_factura}\n')
    iterador.write(f'        debe_actualizar: {tiene_factura}\n')
    iterador.write(f'        layer_quantity: {layer_data["quantity"]}\n')
    iterador.write(f'        invoice_quantity: {invoice_data["quantity"]}\n')
    iterador.write(f'        layer_value_actual: {layer_data["value"]}\n')
    iterador.write(f'        layer_value_nuevo: {value_nuevo or "N/A"}\n')
    iterador.write(f'        invoice_balance: {invoice_data["balance"]}\n')
    iterador.write(f'        diferencia: {diferencia}\n')
    iterador.write(f'        layer_unit_cost_actual: {layer_data["unit_cost"]}\n')
    iterador.write(f'        layer_unit_cost_nuevo: {unit_cost_nuevo or "N/A"}\n')
    iterador.write(f'        correction_type: "{msg[True]}"\n')