# exec(open('/home/jose/Documentos/clientes/17KEEPER/backup/python/actualizacion_layers_promedio.py').read())
# Configuración para reconocimiento de Odoo en VS Code
# pylint: disable=undefined-variable
# pyright: reportUndefinedVariable=false

from datetime import datetime, date
import re
import logging
_logger = logging.getLogger(__name__)
direccion = '/home/user/Escritorio/odoo/odoo/odoo-server-17/backup2/backup/storage/analisis_nahuel.csv'
direccion2 = '/home/jose/Documentos/clientes/17KEEPER/backup/keep/promediacion.yaml'

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

def verificar_tipo(svl):
    """
    Detecta el tipo de SVL:
    - 'ajuste_inventario': ajuste de inventario (entrada o salida)
    - 'compra': entrada por compra
    - 'venta': salida por venta
    - 'ajuste': ajuste manual (sin stock_move_id)
    - 'no_especificado': no se pudo determinar
    """
    move = svl.stock_move_id

    # 1. Ajuste de inventario (entrada o salida)
    if move and (move.location_id.usage == 'inventory' or move.location_dest_id.usage == 'inventory'):
        return 'ajuste_inventario'

    # 2. Ajuste manual (sin movimiento asociado)
    if not move and svl.quantity == 0:
        return 'ajuste'

    # 3. Compra (entrada por compra)
    if svl.quantity > 0 and move and move.purchase_line_id:
        return 'compra'

    # 4. Venta (salida por venta)
    if svl.quantity < 0 and move and move.location_dest_id.usage == 'customer':
        return 'venta'

    # 5. Devolución de compra (salida hacia proveedor)
    if svl.quantity < 0 and move and move.location_dest_id.usage == 'supplier':
        return 'venta'

    # 6. Devolución de venta (entrada desde cliente)
    if svl.quantity > 0 and move and move.location_id.usage == 'customer':
        return 'venta'

    # 7. Otros posibles ajustes (con movimiento pero cantidad cero)
    if move and svl.quantity == 0:
        return 'ajuste'

    # 8. Si nada coincide
    return 'no_especificado'

def setear_a_cero(stock_valuation_layers, dry_run=True):
    contador_zerados = 0
    
    for svl in stock_valuation_layers:
        # si es un ajuste automatico ponemos en cero porque ese ajuste ya pisamos al cargar desde la compra el valor
        if svl.quantity == 0 and svl.stock_valuation_layer_id:  # and svl.value > 0: #quiza aca con value > 0 aplicamos solo  compra y manejamos distitno lo de ventas
            # en ventas se va tomar luego el costo actual a ese momento
            if dry_run:
                # print(f"[DRY RUN] SVL ajuste {svl.id} -> unit_cost a escribir={0}, value a escribir={0}")
                contador_zerados += 1
            else:
                try:
                    # print(f"🔄 SETEANDO A CERO svl id {svl.id}")
                    # print(f"   - valor antes: {svl.value}")
                    # print(f"   - unit_cost antes: {svl.unit_cost}")
                    
                    # Intentar la escritura
                    result = svl.write({
                        'unit_cost': 0,
                        'value': 0,
                    })
                    
                    # print(f"   - write() resultado: {result}")
                    
                    # FORZAR COMMIT DE LA TRANSACCIÓN
                    svl.env.cr.commit()
                    
                    # REFRESCAR EL OBJETO DESDE LA BD
                    svl.invalidate_cache()
                    svl_actualizado = svl.env['stock.valuation.layer'].browse(svl.id)
                    
                    # print(f"   - valor después: {svl_actualizado.value}")
                    # print(f"   - unit_cost después: {svl_actualizado.unit_cost}")
                    
                    # if svl_actualizado.value == 0 and svl_actualizado.unit_cost == 0:
                    #     print(f"   ✅ ÉXITO: SVL {svl.id} zerado correctamente")
                    #     contador_zerados += 1
                    # else:
                    #     print(f"   ❌ FALLO: SVL {svl.id} NO se zeró - valor: {svl_actualizado.value}, unit_cost: {svl_actualizado.unit_cost}")
                        
                    #     # Intentar diagnóstico adicional
                    #     print(f"   🔍 Diagnóstico:")
                    #     print(f"      - Campo editable: {svl._fields['value'].readonly}")
                    #     print(f"      - Usuario actual: {svl.env.user.name}")
                    #     print(f"      - Permisos write: {svl.check_access_rights('write', raise_exception=False)}")
                
                except Exception as e:
                    print(f"   💥 ERROR al escribir SVL {svl.id}: {str(e)}")
                    import traceback
                    traceback.print_exc()
    
    # print(f"📊 Resumen setear_a_cero: {contador_zerados} layers procesados")
    return contador_zerados

def promediar_costos(iterador, enviroment, stock_valuation_layers, costo_unitario=0, stock_qty=0, dry_run=True):
    """
    Recalcula los costos de los stock_valuation_layers usando Costo promedio

    Params:
        stock_valuation_layers : list
            Lista de SVL ordenados cronológicamente(solo de un producto).
        costo_unitario : float
            Costo promedio inicial (por si ya hay stock previo)
        stock_qty : float
            Cantidad inicial de stock (por si ya hay stock previo)

    Notes:
        - SVL de 'compra' ajustan el costo promedio y el stock.
        - SVL de 'venta' solo asignan el costo promedio actual.
        - SVL de 'ajuste' reparten su valor entre el stock actual o lo ponen en cero si ya fue procesado.
    """
    contador_escrituras = 0
    contador_warnings = 0
    
    iterador.write(f"🚀 Iniciando promediación - Estado inicial: costo={costo_unitario}, stock={stock_qty}\n")
    for svl in stock_valuation_layers:
        tipo = verificar_tipo(svl)
        costo_antes = costo_unitario
        stock_antes = stock_qty

        if tipo == 'no_especificado':
            warning_msg = f"[WARNING] No se pudo determinar tipo para SVL {svl.id} del producto {svl.product_id.name}\n"
            iterador.write(warning_msg)
            contador_warnings += 1

        elif tipo == 'compra':
            iterador.write(f"📦 COMPRA SVL {svl.id} - quantity: {svl.quantity}, value: {svl.value}\n")
            # en compras lo que hacemos es promediar el costo unitario y actualizar el stock actual segun lo nuevo
            if costo_unitario and stock_qty > 0:
                costo_total_ant = costo_unitario * stock_qty # valor de stock total antes de comprar
                stock_actual = stock_qty + svl.quantity
                nuevo_costo = (costo_total_ant + svl.value) / stock_actual
                iterador.write(f"   - Promediación: ({costo_unitario}*{stock_qty} + {svl.value}) / {stock_actual} = {nuevo_costo}\n")
                costo_unitario = nuevo_costo
                stock_qty = stock_actual
            else:
                # Si no hay stock previo, usamos el costo del SVL directamente
                iterador.write(f"   - Stock inicial: usando costo directo {svl.unit_cost}\n")
                costo_unitario = svl.unit_cost
                stock_qty = svl.quantity

        elif tipo == 'venta':
            valor_esperado = svl.quantity * costo_unitario
            iterador.write(f"🛒 VENTA SVL {svl.id} - quantity: {svl.quantity}, costo_promedio: {costo_unitario}\n")
            iterador.write(f"   - Value esperado: {svl.quantity} * {costo_unitario} = {valor_esperado}\n")
            
            # Salida de stock, aplicamos costo promedio actual
            if dry_run:
                iterador.write(f"   [DRY RUN] SVL venta {svl.id} -> unit_cost a escribir={costo_unitario}, value a escribir={valor_esperado}\n")
            else:
                try:
                    iterador.write(f"   🔄 ESCRIBIENDO VENTA - valor antes: {svl.value}, unit_cost antes: {svl.unit_cost}\n")
                    
                    result = svl.write({
                        'unit_cost': costo_unitario,
                        'value': valor_esperado,
                    })
                    
                    iterador.write(f"   - write() resultado: {result}\n")
                    
                    # FORZAR COMMIT DE LA TRANSACCIÓN
                    svl.env.cr.commit()
                    
                    # REFRESCAR EL OBJETO DESDE LA BD
                    # svl.invalidate_cache()
                    svl_actualizado = svl.env['stock.valuation.layer'].browse(svl.id)
                    
                    iterador.write(f"   - valor después: {svl_actualizado.value}\n")
                    iterador.write(f"   - unit_cost después: {svl_actualizado.unit_cost}\n")
                    
                    if abs(svl_actualizado.value - valor_esperado) < 1 and abs(svl_actualizado.unit_cost - costo_unitario) < 1:
                        iterador.write(f"   ✅ ÉXITO: VENTA {svl.id} actualizada correctamente\n")
                        contador_escrituras += 1
                    else:
                        iterador.write(f"      FALLO: VENTA {svl.id} NO se actualizó correctamente\n")
                        iterador.write(f"      Esperado: value={valor_esperado}, unit_cost={costo_unitario}\n")
                        iterador.write(f"      Real: value={svl_actualizado.value}, unit_cost={svl_actualizado.unit_cost}\n")
                        
                except Exception as e:
                    print(f"   💥 ERROR al escribir VENTA {svl.id}: {str(e)}\n")
                    import traceback
                    print(f"   Traceback: {traceback.format_exc()}\n")

            stock_qty += svl.quantity  # svl.quantity es negativo en ventas, por eso sumamos
            iterador.write(f"   - Stock después de venta: {stock_qty}\n")

            if costo_unitario and stock_qty <= 0:
                warning_msg = f"[WARNING] Stock llegó a {stock_qty} después de venta para SVL {svl.id}"
                iterador.write(warning_msg)
                contador_warnings += 1

        elif tipo == 'ajuste':
            iterador.write(f"🔧 AJUSTE SVL {svl.id} - quantity: {svl.quantity}, value: {svl.value}\n")
            # si es un ajuste automatico ponemos en cero porque ese ajuste ya pisamos al cargar desde la compra el valor
            if svl.stock_valuation_layer_id:
                iterador.write(f"   - Ajuste automático - SKIP (ya procesado)\n")
                continue
            # en ajuste promediamos el valor del ajuste entre lo que tenemos en stock a ese momento
            if costo_unitario and stock_qty > 0:
                costo_total_ant = costo_unitario * stock_qty
                stock_actual = stock_qty  # este svl no tiene quantity
                nuevo_costo = (costo_total_ant + svl.value) / stock_actual
                iterador.write(f"   - Promediación ajuste: ({costo_unitario}*{stock_qty} + {svl.value}) / {stock_actual} = {nuevo_costo}\n")
                costo_unitario = nuevo_costo
            else:
                warning_msg = f"[WARNING] Costo unitario en 0 y stock en 0 para ajuste SVL {svl.id}"
                iterador.write(warning_msg)
                contador_warnings += 1

        elif tipo == 'ajuste_inventario':
            valor_esperado = svl.quantity * costo_unitario
            iterador.write(f"📋 AJUSTE INVENTARIO SVL {svl.id} - quantity: {svl.quantity}, costo_actual: {costo_unitario}\n")
            iterador.write(f"   - Value esperado: {svl.quantity} * {costo_unitario} = {valor_esperado}\n")
            
            # si es un ajuste de inventario promediamos la cantidad agregada y le cargamos el costo en ese momento y distribuimos
            if costo_unitario and stock_qty > 0:
                if dry_run:
                    iterador.write(f"   [DRY RUN] SVL ajuste inventario {svl.id} -> unit_cost a escribir={costo_unitario}, value a escribir={valor_esperado}\n")
                else:
                    try:
                        iterador.write(f"   🔄 ESCRIBIENDO AJUSTE INVENTARIO - valor antes: {svl.value}, unit_cost antes: {svl.unit_cost}\n")
                        
                        result = svl.write({
                            'unit_cost': costo_unitario,
                            'value': valor_esperado,
                        })
                        
                        iterador.write(f"   - write() resultado: {result}\n")
                        
                        # FORZAR COMMIT DE LA TRANSACCIÓN
                        svl.env.cr.commit()
                        
                        # REFRESCAR EL OBJETO DESDE LA BD
                        svl.invalidate_cache()
                        svl_actualizado = svl.env['stock.valuation.layer'].browse(svl.id)
                        
                        iterador.write(f"   - valor después: {svl_actualizado.value}\n")
                        iterador.write(f"   - unit_cost después: {svl_actualizado.unit_cost}\n")
                        
                        if abs(svl_actualizado.value - valor_esperado) < 0.01 and abs(svl_actualizado.unit_cost - costo_unitario) < 0.01:
                            iterador.write(f"   ✅ ÉXITO: AJUSTE INVENTARIO {svl.id} actualizado correctamente\n")
                            contador_escrituras += 1
                        else:
                            iterador.write(f"   ❌ FALLO: AJUSTE INVENTARIO {svl.id} NO se actualizó correctamente\n")
                            iterador.write(f"      Esperado: value={valor_esperado}, unit_cost={costo_unitario}\n")
                            iterador.write(f"      Real: value={svl_actualizado.value}, unit_cost={svl_actualizado.unit_cost}\n")
                            
                    except Exception as e:
                        iterador.write(f"   💥 ERROR al escribir AJUSTE INVENTARIO {svl.id}: {str(e)}\n")
                        import traceback
                        iterador.write(f"   Traceback: {traceback.format_exc()}\n")
            else:
                warning_msg = f"[WARNING] Costo unitario en 0 y stock en 0 para ajuste inventario SVL {svl.id}\n"
                iterador.write(warning_msg)
                contador_warnings += 1
                
            stock_qty += svl.quantity  # luego actualizamos stock
            iterador.write(f"   - Stock después de ajuste inventario: {stock_qty}\n")
        
        # Log del cambio en el costo promedio si hubo cambio significativo
        if abs(costo_antes - costo_unitario) > 0.01:
            iterador.write(f"   💰 Costo promedio cambió: {costo_antes} → {costo_unitario}\n")
    
    iterador.write(f"📊 Resumen promediación:\n")
    iterador.write(f"   - Escrituras exitosas: {contador_escrituras}\n")
    iterador.write(f"   - Warnings generados: {contador_warnings}\n")
    iterador.write(f"   - Costo final: {costo_unitario}\n")
    iterador.write(f"   - Stock final: {stock_qty}\n")
    
    return contador_escrituras, contador_warnings

def buscar_layers(
        env,
        producto: int,
        orden="desc",
        cantidad=None,
        fecha_inicio=None,
        fecha_fin=None):
    # Definimos el dominio de la búsqueda
    domain = [('product_id', '=', producto)]
    
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
        layers = env['stock.valuation.layer'].search(
            domain,
            order=f"create_date {orden}",
            limit=cantidad
        )
    else:
        layers = env['stock.valuation.layer'].search(
            domain,
            order=f"create_date {orden}"
        )

    return layers

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
    iterador.write("# PROMEDIACION MASIVA DE STOCK VALUATION LAYERS\n")
    iterador.write("# ========================================\n")
    iterador.write("# Generado automáticamente por actualizacion_layers_promedio.py\n")
    iterador.write(f"# Período ajustado: Febrero 2025\n")
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

def info_layer_completo(iterador, objeto_layer):
    iterador.write(f"      stock_valuation_layer:\n")
    iterador.write(f"        create_date: \"{objeto_layer.create_date}\"\n")
    iterador.write(f"        description: \"{format_yaml_string(objeto_layer.description)}\"\n")
    iterador.write(f"        quantity: {objeto_layer.quantity}\n")
    iterador.write(f"        unit_cost: {objeto_layer.unit_cost}\n")
    iterador.write(f"        value: {objeto_layer.value}\n")
    iterador.write(f"        remaining_qty: {objeto_layer.remaining_qty}\n")

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

def obtener_inicial(producto):
    costo = 0
    stock = 0
    svl_antes = env['stock.valuation.layer'].search([
        ('create_date', '<', '2025-02-01'),
        ('product_id', '=', producto)
    ])
    stock = sum(svl_antes.mapped('quantity') or [])
    total_value = sum(svl_antes.mapped('value') or [])
    costo = (total_value / stock) if stock else 0
    return costo, stock

# ---- EJECUCION DEL SCRIPT ----
layer_febrero = env['stock.valuation.layer'].search([
    ('create_date', '>=', '2025-02-01')
])
lista_productos = list(set(layer_febrero.product_id.ids))  # Eliminar duplicados

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
        layers = buscar_layers(
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

        # buscar costos a la fecha
        costo_inicial, stock_inicial = obtener_inicial(product_id)

        # ponemos en cero los que son ajuste de precio (cantidad = 0 y svl = true)
        layers_zerados = setear_a_cero(layers, dry_run=True)

        # ultimo paso para svl, promediar simulando la cronologia de compras y ventas
        escrituras_promedio, warnings_promedio = promediar_costos(
            iterador=f,
            enviroment=env,
            stock_valuation_layers=layers,
            costo_unitario=costo_inicial,
            stock_qty=stock_inicial,
            dry_run=False)
        
        # print(f"📈 Producto {contador_productos} completado - Zerados: {layers_zerados}, Escrituras: {escrituras_promedio}, Warnings: {warnings_promedio}")
        productos_con_datos += 1
        
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
