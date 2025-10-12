# exec(open('/home/jose/Documentos/clientes/17KEEPER/backup/python/actualizacion_layers.py').read())
# Configuración para reconocimiento de Odoo en VS Code
# pylint: disable=undefined-variable
# pyright: reportUndefinedVariable=false

from datetime import datetime, date
import re

direccion = '/home/jose/Documentos/clientes/17KEEPER/backup/storage/analisis_nahuel.csv'
direccion2 = '/home/jose/Documentos/clientes/17KEEPER/backup/keep/actualizazcion_layers.yaml'

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

# Análisis masivo de productos de febrero
layer_febrero = env['stock.valuation.layer'].search([
    ('create_date', '>=', '2025-02-01')
])
lista_productos = list(set(layer_febrero.product_id.ids))  # Eliminar duplicados

# Prueba a pedido de nahuel
prueba_nahuel = env['stock.valuation.layer'].search([
    ('create_date', '>=', '2025-02-01'),
    ('quantity', '<', 0.0),
    ('stock_move_id.purchase_line_id', '=', False),
    ('stock_move_id.location_id.usage', 'in', ['supplier']),
    ('stock_move_id.location_dest_id.usage', 'in', ['customer'])
    # ('stock_move_id.location_id.usage', 'not in', ['customer', 'inventory']),
    # ('stock_move_id.location_dest_id.usage', 'not in', ['internal', 'inventory']),
])


# impresion_csv(direccion, prueba_nahuel)

print(f"📊 Iniciando análisis de {len(lista_productos)} productos únicos...")
print(f"   Layers febrero 2025 en adelante: {len(layer_febrero)}")

with open(direccion2, 'w') as f:
    # Escribir cabecera global del archivo YAML
    f.write("# ========================================\n")
    f.write("# ANÁLISIS MASIVO DE STOCK VALUATION LAYERS\n")
    f.write("# ========================================\n")
    f.write("# Generado automáticamente por actualizacion_layers.py\n")
    f.write(f"# Período analizado: Febrero 2025\n")
    f.write(f"# Total productos: {len(lista_productos)}\n")
    f.write(f"# Fecha de análisis: {env['res.users'].browse(env.uid).name} - {env.cr.now()}\n\n")
    
    contador_productos = 0
    total_layers_analizados = 0
    productos_con_datos = 0
    productos_sin_datos = 0
    
    for product_id in lista_productos:
        contador_productos += 1
        
        # Buscar layers para este producto
        layers = buscar_layers_positivos(
            env=env,
            producto=product_id,
            orden="asc",
            cantidad=None,
            fecha_inicio='2025-02-01',
        )
        
        if not layers:
            continue  # Saltar productos sin layers en el período
            
        producto_obj = env['product.product'].browse(product_id)
        total_layers_analizados += len(layers)
        
        # Escribir cabecera del producto
        f.write(f"# ----------------------------------------\n")
        f.write(f"# PRODUCTO {contador_productos}/{len(lista_productos)}\n")
        f.write(f"# ----------------------------------------\n")
        f.write(f"# ID: {product_id}\n")
        f.write(f"# Nombre: {format_yaml_string(producto_obj.name)}\n")
        f.write(f"# Cantidad de layers: {len(layers)}\n")
        f.write(f"# ----------------------------------------\n\n")
        
        f.write(f"producto_{contador_productos}:\n")
        f.write(f"  product_info:\n")
        f.write(f"    id: {product_id}\n")
        f.write(f"    name: \"{format_yaml_string(producto_obj.name)}\"\n")
        f.write(f"    default_code: \"{format_yaml_string(producto_obj.default_code)}\"\n")
        f.write(f"    categ_id: \"{format_yaml_string(producto_obj.categ_id.name)}\"\n")
        f.write(f"    total_layers: {len(layers)}\n")
        f.write(f"  layers:\n")
        
        layers_con_purchase = 0
        layers_sin_purchase = 0
        
        for index, layer in enumerate(layers, 1):
            # Algoritmo para cruzar 'stock.valuation.layer' con 'purchase.order.line'
            stock_move = layer.stock_move_id
            purchase_order_line = stock_move.purchase_line_id if stock_move else None
            
            # Verificar que existe purchase_order_line
            if not purchase_order_line:
                layers_sin_purchase += 1
                f.write(f"    layer_{index}:\n")
                f.write(f"      layer_id: {layer.id}\n")
                f.write(f"      status: \"sin_purchase_order_line\"\n")
                f.write(f"      layer_info:\n")
                f.write(f"        create_date: \"{layer.create_date}\"\n")
                f.write(f"        description: \"{format_yaml_string(layer.description)}\"\n")
                f.write(f"        quantity: {layer.quantity}\n")
                f.write(f"        unit_cost: {layer.unit_cost}\n")
                f.write(f"        value: {layer.value}\n")
                f.write(f"        stock_move_id: {stock_move.id if stock_move else 'N/A'}\n")
                f.write(f"      observacion: \"Layer sin purchase_order_line asociada\"\n\n")
                continue
            
            layers_con_purchase += 1
            
            # Buscar account_move_line
            account_move_line = env['account.move.line'].search([
                ('purchase_line_id', '=', purchase_order_line.id),
                ('move_id.move_type', '=', 'in_invoice')
            ], order='create_date asc', limit=1)
            
            # Escribir información completa del layer
            f.write(f"    layer_{index}:\n")
            f.write(f"      layer_id: {layer.id}\n")
            f.write(f"      status: \"{'completo' if account_move_line else 'incompleto'}\"\n")
            
            # Stock Valuation Layer info
            f.write(f"      stock_valuation_layer:\n")
            f.write(f"        create_date: \"{layer.create_date}\"\n")
            f.write(f"        description: \"{format_yaml_string(layer.description)}\"\n")
            f.write(f"        quantity: {layer.quantity}\n")
            f.write(f"        unit_cost: {layer.unit_cost}\n")
            f.write(f"        value: {layer.value}\n")
            f.write(f"        remaining_qty: {layer.remaining_qty}\n")
            
            # Stock Move info
            f.write(f"      stock_move:\n")
            f.write(f"        id: {stock_move.id}\n")
            f.write(f"        name: \"{format_yaml_string(stock_move.name)}\"\n")
            f.write(f"        date: \"{stock_move.date}\"\n")
            f.write(f"        state: \"{stock_move.state}\"\n")
            
            # Purchase Order Line info
            f.write(f"      purchase_order_line:\n")
            f.write(f"        id: {purchase_order_line.id}\n")
            f.write(f"        name: \"{format_yaml_string(purchase_order_line.name)}\"\n")
            f.write(f"        qty_ordered: {purchase_order_line.product_qty}\n")
            f.write(f"        price_unit: {purchase_order_line.price_unit}\n")
            f.write(f"        currency: \"{purchase_order_line.currency_id.name}\"\n")
            f.write(f'        qty_received: {purchase_order_line.qty_received}\n')
            f.write(f'        qty_invoiced: {purchase_order_line.qty_invoiced}\n')
            
            if account_move_line:
                purchase_order = purchase_order_line.order_id
                quantity = account_move_line.quantity
                balance = account_move_line.balance
                price_unit_calculated = round(balance / quantity, 2) if quantity != 0 else 0
                
                f.write(f"      purchase_order:\n")
                f.write(f"        id: {purchase_order.id}\n")
                f.write(f"        name: \"{format_yaml_string(purchase_order.name)}\"\n")
                f.write(f"        date_order: \"{purchase_order.date_order}\"\n")
                f.write(f"        currency: \"{purchase_order.currency_id.name}\"\n")
                f.write(f"        state: \"{purchase_order.state}\"\n")
                
                f.write(f"      account_move_line:\n")
                f.write(f"        id: {account_move_line.id}\n")
                f.write(f"        name: \"{format_yaml_string(account_move_line.name)}\"\n")
                f.write(f"        quantity: {quantity}\n")
                f.write(f"        balance: {balance}\n")
                f.write(f"        price_unit_original: {account_move_line.price_unit}\n")
                f.write(f"        price_unit_calculated: {price_unit_calculated}\n")
                f.write(f"        currency: \"{account_move_line.currency_id.name if account_move_line.currency_id else 'N/A'}\"\n")
                
                f.write(f"      invoice_info:\n")
                f.write(f"        id: {account_move_line.move_id.id}\n")
                f.write(f"        name: \"{format_yaml_string(account_move_line.move_id.name)}\"\n")
                f.write(f"        date: \"{account_move_line.invoice_date or account_move_line.move_id.date}\"\n")
                f.write(f"        state: \"{account_move_line.move_id.state}\"\n")
                f.write(f"        amount_total: {account_move_line.move_id.amount_total}\"\n")
            else:
                purchase = purchase_order_line.order_id
                f.write(f'      purchase_order:\n')
                f.write(f'          id: {purchase.id}\n')
                f.write(f'          name: {purchase.name}\n')
                f.write(f"      account_move_line: null\n")
                f.write(f"      observacion: \"No se encontró account_move_line para esta purchase_line\"\n")
            
            f.write(f"\n")
        
        # Resumen del producto
        if layers_con_purchase > 0:
            productos_con_datos += 1
        else:
            productos_sin_datos += 1
            
        f.write(f"  resumen_producto:\n")
        f.write(f"    layers_con_purchase: {layers_con_purchase}\n")
        f.write(f"    layers_sin_purchase: {layers_sin_purchase}\n")
        f.write(f"    total_layers: {len(layers)}\n")
        f.write(f"    completitud: \"{round((layers_con_purchase/len(layers))*100, 1)}%\"\n\n")
        
        # Log de progreso cada 10 productos
        if contador_productos % 10 == 0:
            print(f"📈 Procesados {contador_productos}/{len(lista_productos)} productos...")

    # Escribir resumen final
    f.write(f"# ========================================\n")
    f.write(f"# RESUMEN FINAL DEL ANÁLISIS\n")
    f.write(f"# ========================================\n")
    f.write(f"resumen_general:\n")
    f.write(f"  productos_analizados: {contador_productos}\n")
    f.write(f"  productos_con_datos: {productos_con_datos}\n")
    f.write(f"  productos_sin_datos: {productos_sin_datos}\n")
    f.write(f"  total_layers_analizados: {total_layers_analizados}\n")
    f.write(f"  fecha_analisis: \"{env.cr.now()}\"\n")

print(f"✅ Análisis completado!")
print(f"📊 Resumen:")
print(f"   - Productos analizados: {contador_productos}")
print(f"   - Total layers procesados: {total_layers_analizados}")
print(f"   - Productos con datos completos: {productos_con_datos}")
print(f"   - Productos sin datos: {productos_sin_datos}")
print(f"📁 Archivo generado: {direccion2}")
