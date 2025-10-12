# exec(open('/home/user/Escritorio/odoo/odoo/odoo-server-17/backup2/python/actualizacion_layers.py').read())
# Configuración para reconocimiento de Odoo en VS Code
# pylint: disable=undefined-variable
# pyright: reportUndefinedVariable=false

from datetime import datetime, date
import re

direccion = '/home/user/Escritorio/odoo/odoo/odoo-server-17/backup2/storage/analisis_nahuel.csv'
direccion2 = '/home/user/Escritorio/odoo/odoo/odoo-server-17/backup2/keep/actualizazcion_layers.yaml'

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


def buscar_layers_negativos(
        env,
        producto: int,
        orden="desc",
        cantidad=None,
        fecha_inicio=None,
        fecha_fin=None):
    # Definimos el dominio de la búsqueda
    domain = [('product_id', '=', producto), ('quantity', '<', 0)]

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
        layers_negative = env['stock.valuation.layer'].search(
            domain,
            order=f"create_date {orden}",
            limit=cantidad
        )
    else:
        layers_negative = env['stock.valuation.layer'].search(
            domain,
            order=f"create_date {orden}"
        )

    return layers_negative

def verificar_tipo(svl):
    tipo = 'no_especificado'


    #agregaremos logica de tipo aca
    return tipo

def promediar_costos(stock_valuation_layers, costo_unitario=0, stock_qty=0):
    '''
    Le pasamos la lista de SVL a procesar
    el costo inicial
    el stock inicial
    '''

    costo_unitario = costo_unitario
    stock_qty = stock_qty

    for svl in stock_valuation_layers:
        if verificar_tipo(svl) == 'no_especificado':
            print('error al verificar tipo para el stock valuation layer %s del producto %s', svl, svl.product_id.name)
        if verificar_tipo(svl) == 'compra':
            # en compras lo que hacemos es promediar el costo unitario y actualizar el stock actual segun lo nuevo
            if costo_unitario and stock_qty > 0:
                costo_total_ant = costo_unitario * stock_qty # valor de stock total antes de comprar
                stock_actual = stock_qty + svl.quantity
                nuevo_costo = ((costo_total_ant) + svl.value) / (stock_actual)
                stock_qty = stock_actual
                costo_unitario = nuevo_costo
            else:
                costo_unitario += svl.unit_cost
                stock_qty += svl.quantity
        if verificar_tipo(svl) == 'venta':
            #en ventas solamente lo que hacemos es cargar el precio unitario
            #segun el actual que vamos calculando  ese momento
            if costo_unitario and stock_qty > 0:
                svl.unit_cost = costo_unitario
                svl.value = svl.quantity * costo_unitario
            else:
                svl.unit_cost = costo_unitario
                svl.value = costo_unitario
                #verificar o loggear si esto ocurre
        if verificar_tipo(svl) == 'ajuste':
            # si es un ajuste automatico ponemos en cero porque ese ajuste ya pisamos al cargar desde la compra el valor
            if svl.stock_valuation_layer_id: #and svl.value > 0: #quiza aca con value > 0 aplicamos solo  compra y manejamos distitno lo de ventas
                # en ventas se va tomar luego el costo actual a ese momento
                #todo: ver si lo facturado al cliente al ser a un costo distinto en que puede impactar
                svl.unit_cost = 0
                svl.value = 0

            #en ajuste promediamos el valor del ajuste entre lo que tenemos en stock a ese momento
            if costo_unitario and stock_qty > 0:
                costo_total_ant = costo_unitario * stock_qty # valor de stock total antes de comprar
                stock_actual = stock_qty # este svl no tiene quantity
                nuevo_costo = ((costo_total_ant) + svl.value) / (stock_actual)
                costo_unitario = nuevo_costo # el ajuste nuevo se distribuye entre todos los productos que tenemos a ese momento
            else:
                costo_unitario += svl.unit_cost
                stock_qty += svl.quantity
                #verificar o loggear si ocurre
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
        iterador.write(f"        date: \"{objeto_move_line.invoice_date or objeto_move_line.move_id.date}\"\n")
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
    iterador.write(f"    total_layers: {len(layers)}\n")
    iterador.write(f"    completitud: \"{round((contador1/len(objeto_layer))*100, 1)}%\"\n\n")

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
    info_cabecera_principal(iterador=f, enviroment=env, lista=lista_productos)
 
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
            fecha_inicio='2025-02-01')
        
        if not layers:
            continue  # Saltar productos sin layers en el período
            
        # Escribir cabecera del producto
        producto_obj = env['product.product'].browse(product_id)
        total_layers_analizados += len(layers)
        info_cabecera_productos(
            iterador=f,
            count=contador_productos,
            producto=lista_productos,
            id=product_id,
            objeto=producto_obj,
            valoracion=layers)
        
        layers_con_purchase = 0
        layers_sin_purchase = 0
        
        for index, layer in enumerate(layers, 1):
            # Algoritmo para cruzar 'stock.valuation.layer' con 'purchase.order.line'
            stock_move = layer.stock_move_id
            purchase_order_line = stock_move.purchase_line_id if stock_move else None
            
            # Verificar que existe purchase_order_line
            if not purchase_order_line:
                layers_sin_purchase += 1
                info_not_purchase_order_line(iterador=f, indice=index, objeto1=layer, objeto2=stock_move)
                continue
            
            layers_con_purchase += 1
            
            # Buscar account_move_line
            account_move_line = env['account.move.line'].search([
                ('purchase_line_id', '=', purchase_order_line.id),
                ('move_id.move_type', '=', 'in_invoice')
            ], order='create_date asc', limit=1)
            
            # Escribir información completa del layer
            info_layer_encontrado(iterador=f, indice=index, objeto1=layer, objeto2=account_move_line)

            # Stock Valuation Layer info
            info_layer_completo(iterador=f, objeto_layer=layer)
            
            # Stock Move info
            info_stock_move(iterador=f, object_stock_move=stock_move)
            
            # Purchase Order Line info
            info_purchase_order_line(iterador=f, object_purchase_order_line=purchase_order_line)
            
            info_account_move_line(
                iterador=f,
                objeto_move_line=account_move_line,
                objeto_purchase_order_line=purchase_order_line)            

            # Algoritmo de actualización
            layer_quantity = layer.quantity
            layer_unit_cost = layer.unit_cost
            layer_value = layer.value
            if account_move_line:
                line_quantity = account_move_line.quantity
                line_balance = account_move_line.balance
            else:
                line_quantity = None
                line_balance = None

            f.write(f'      actualizacion_buscada:\n')
            f.write(f'        layer_unit_cost: {layer_unit_cost}\n')
            f.write(f'        layer_quantity: {layer_quantity}\n')
            f.write(f'        line_quantity: {line_quantity}\n')
            f.write(f'        layer_value: {layer_value}\n')
            f.write(f'        line_balance: {line_balance}\n')
        
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
            objeto_layer=layer)
        
        # Log de progreso cada 10 productos
        if contador_productos % 10 == 0:
            print(f"📈 Procesados {contador_productos}/{len(lista_productos)} productos...")

    # Escribir resumen final
    info_resumen_final(
        iterador=f,
        count1=contador_productos,
        count2=productos_con_datos,
        count3=productos_sin_datos,
        count4=total_layers_analizados,
        enviroment=env)

print(f"✅ Análisis completado!")
print(f"📊 Resumen:")
print(f"   - Productos analizados: {contador_productos}")
print(f"   - Total layers procesados: {total_layers_analizados}")
print(f"   - Productos con datos completos: {productos_con_datos}")
print(f"   - Productos sin datos: {productos_sin_datos}")
print(f"📁 Archivo generado: {direccion2}")
