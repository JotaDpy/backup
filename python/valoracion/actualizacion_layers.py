# exec(open('/home/jose/Documentos/clientes/15FONDOESTRELLA/clean_valuation/python/valoracion/actualizacion_layers.py').read())
# Configuración para reconocimiento de Odoo en VS Code
# pylint: disable=undefined-variable
# pyright: reportUndefinedVariable=false

from datetime import datetime, date
import calendar
import re

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
    numero = float(numero)
    parte_entera, parte_decimal = f"{numero:.2f}".split(".")
    parte_entera_con_puntos = ".".join(
        [parte_entera[::-1][i:i + 3] for i in range(0, len(parte_entera), 3)]
    )[::-1]
    return f"{parte_entera_con_puntos},{parte_decimal}"

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
    domain = [('product_id', '=', producto.id), ('quantity', '>', 0)]
    
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
        # Convertir string a datetime si es necesario
        if isinstance(fecha_fin, str):
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

def algoritmo1(iterador, objeto1, objeto2):
    """
    **Algoritmo 1 de actualización**

Este algoritmo se aplica a todos los registros de **Stock Valuation Layer** que tienen 
    `quantity > 0`.

    **Parámetros:**
    - `iterador`: Iterador que recorre los registros a procesar.
    - `layer` (`Stock Valuation Layer`): Representa la capa de valoración de inventario.
    - `account_move_line` (`Account Move Line`): Representa la línea contable asociada.
    """

    # Extraer valores del layer (valores actuales antes de cualquier cambio)
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
    
    # Variables para el análisis
    tiene_factura = objeto2 is not None
    diferencia_original = abs(layer_data['value'] - invoice_data['balance']) if tiene_factura else 0.0
    
    # PASO 1: REALIZAR LA ACTUALIZACIÓN (SI CORRESPONDE)
    unit_cost_nuevo = None
    value_nuevo = None
    se_actualizo = False
    
    if tiene_factura and invoice_data['quantity'] > 0:
        unit_cost_nuevo = round(invoice_data['balance'] / invoice_data['quantity'], 3)
        value_nuevo = invoice_data['balance']  # El value debe ser igual al balance de la factura

        # Ejecutar la actualización
        objeto1.write({
            'unit_cost': unit_cost_nuevo,
            'value': value_nuevo,
        })
        se_actualizo = True

    # PASO 2: ANÁLISIS Y CLASIFICACIÓN DEL MENSAJE (DESPUÉS DE LA ACTUALIZACIÓN)
    # Usar la diferencia ORIGINAL para clasificar qué tipo de corrección se hizo
    if tiene_factura:
        if diferencia_original > 1000:
            correction_type = "USD-PYG ajuste grande (corregido)"
        elif 0 < diferencia_original < 1000:
            correction_type = "USD-PYG ajuste pequeño (corregido)"
        elif diferencia_original == 0:
            correction_type = "Estaba correcto, pero igual se actualiza"
        else:
            correction_type = "Revisión necesaria"
    else:
        correction_type = "Sin factura"
    
    # PASO 3: ESCRIBIR EL ANÁLISIS AL YAML
    iterador.write(f'      actualizacion_analisis:\n')
    iterador.write(f'        tiene_factura: {tiene_factura}\n')
    iterador.write(f'        debe_actualizar: {tiene_factura and invoice_data["quantity"] > 0}\n')
    iterador.write(f'        se_actualizo: {se_actualizo}\n')
    iterador.write(f'        layer_quantity: {layer_data["quantity"]}\n')
    iterador.write(f'        invoice_quantity: {invoice_data["quantity"]}\n')
    iterador.write(f'        layer_value_original: {format_num(layer_data["value"])}\n')
    iterador.write(f'        layer_value_nuevo: {format_num(value_nuevo or 0.0)}\n')
    iterador.write(f'        invoice_balance: {format_num(invoice_data["balance"])}\n')
    iterador.write(f'        diferencia_original: {format_num(diferencia_original)}\n')
    iterador.write(f'        layer_unit_cost_original: {format_num(layer_data["unit_cost"])}\n')
    iterador.write(f'        layer_unit_cost_nuevo: {format_num(unit_cost_nuevo or 0.0)}\n')
    iterador.write(f'        correction_type: "{correction_type}"\n')

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

    product_product = product_product.filtered(lambda x: x.id in [1632, 1772, 3281, 3535, 4899])

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
            layers = buscar_layers_positivos(
                env=env,
                producto=producto_obj,
                orden="asc",
                cantidad=None,
                fecha_inicio=get_fecha_min_layer(producto_obj.id)
            )

            if not layers:
                continue  # Saltar productos sin layers en el período

            # Escribir cabecera del producto
            total_layers_analizados += len(layers)
            info_cabecera_productos(
                iterador=f,
                count=contador_productos,
                producto=product_product,
                id=producto_obj.id,
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
                    info_not_purchase_order_line(
                        iterador=f,
                        indice=index,
                        objeto1=layer,
                        objeto2=stock_move)
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

                # Account Move Line info
                info_account_move_line(
                    iterador=f,
                    objeto_move_line=account_move_line,
                    objeto_purchase_order_line=purchase_order_line)            

                # Algoritmo 1 de actualización
                algoritmo1(iterador=f, objeto1=layer, objeto2=account_move_line)

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
