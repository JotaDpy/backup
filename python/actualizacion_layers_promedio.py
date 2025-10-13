# exec(open('/home/user/Escritorio/odoo/odoo/odoo-server-17/backup2/backup/python/actualizacion_layers_promedio.py').read())
# Configuración para reconocimiento de Odoo en VS Code
# pylint: disable=undefined-variable
# pyright: reportUndefinedVariable=false

from datetime import datetime, date
import re
import logging
_logger = logging.getLogger(__name__)
direccion = '/home/jose/Documentos/clientes/17KEEPER/backup/storage/analisis_nahuel.csv'
direccion2 = '/home/user/Escritorio/odoo/odoo/odoo-server-17/backup2/backup/keep/promediacion.yaml'

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
    Obtenemos el tipo de stock_valuation_layer.

    Returns:
        'compra'  -> Entrada de stock por compra
        'venta'   -> Salida de stock por venta
        'ajuste'  -> Ajuste manual o automático
        'no_especificado' -> No se pudo determinar
    """
    if svl.stock_move_id:
        if svl.quantity > 0 and svl.stock_move_id.purchase_line_id:
            return 'compra'
        elif svl.quantity < 0:
            return 'venta'
    elif svl.quantity == 0:
        return 'ajuste'
    return 'no_especificado'

def setear_a_cero(stock_valuation_layers, dry_run=False):
    for svl in stock_valuation_layers:
        # si es un ajuste automatico ponemos en cero porque ese ajuste ya pisamos al cargar desde la compra el valor
        if svl.quantity == 0 and svl.stock_valuation_layer_id:  # and svl.value > 0: #quiza aca con value > 0 aplicamos solo  compra y manejamos distitno lo de ventas
            # en ventas se va tomar luego el costo actual a ese momento
            if dry_run:
                _logger.info(f"[DRY RUN] SVL ajuste {svl.id} -> unit_cost a escribir={0}, value a escribir={0}")
            else:
                svl.write({
                    'unit_cost': 0,
                    'value': 0,
                })


def promediar_costos(stock_valuation_layers, costo_unitario=0, stock_qty=0, dry_run=True):
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
    for svl in stock_valuation_layers:
        tipo = verificar_tipo(svl)

        if tipo == 'no_especificado':
            print(f"[WARNING] No se pudo determinar tipo para SVL {svl.id} del producto {svl.product_id.name}")

        elif tipo == 'compra':
            # en compras lo que hacemos es promediar el costo unitario y actualizar el stock actual segun lo nuevo
            if costo_unitario and stock_qty > 0:
                costo_total_ant = costo_unitario * stock_qty # valor de stock total antes de comprar
                stock_actual = stock_qty + svl.quantity
                nuevo_costo = (costo_total_ant + svl.value) / stock_actual
                costo_unitario = nuevo_costo
                stock_qty = stock_actual
            else:
                # Si no hay stock previo, usamos el costo del SVL directamente
                costo_unitario = svl.unit_cost
                stock_qty = svl.quantity

        elif tipo == 'venta':
            # Salida de stock, aplicamos costo promedio actual
            # en ventas solamente lo que hacemos es cargar el precio unitario
            # segun el actual que vamos calculando  ese momento
            if costo_unitario and stock_qty > 0:
                if dry_run:
                    _logger.info(f"[DRY RUN] SVL venta {svl.id} -> unit_cost a escribir={costo_unitario}, value a escribir={svl.quantity * costo_unitario}")
                else:
                    svl.write({
                        'unit_cost': costo_unitario,
                        'value': svl.quantity * costo_unitario,
                    })

                stock_qty -= svl.quantity #Tambien debemos disminuir el stock para que no afecte el promedio
            else:
                print(f"[WARNING] Costo unitario en 0 y stock en 0 actual para  {svl.id} del producto {svl.product_id.name} de la venta")

        elif tipo == 'ajuste':
            # si es un ajuste automatico ponemos en cero porque ese ajuste ya pisamos al cargar desde la compra el valor
            if svl.stock_valuation_layer_id:  # and svl.value > 0: #quiza aca con value > 0 aplicamos solo  compra y manejamos distitno lo de ventas
                continue
            # en ajuste promediamos el valor del ajuste entre lo que tenemos en stock a ese momento
            if costo_unitario and stock_qty > 0:
                costo_total_ant = costo_unitario * stock_qty  # valor de stock total antes de comprar
                stock_actual = stock_qty  # este svl no tiene quantity
                nuevo_costo = (costo_total_ant + svl.value) / (stock_actual)
                costo_unitario = nuevo_costo  # el ajuste nuevo se distribuye entre todos los productos que tenemos a ese momento
            else:
                print(f"[WARNING] Costo unitario en 0 y stock en 0 actual para  {svl.id} del producto {svl.product_id.name} del ajuste")


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

# Análisis masivo de productos de febrero
layer_febrero = env['stock.valuation.layer'].search([
    ('create_date', '>=', '2025-02-01')
])
lista_productos = list(set(layer_febrero.product_id.ids))  # Eliminar duplicados



def obtener_inicial(producto):
    costo = 0
    stock = 0

    return costo, stock



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

        #buscar costos a la fecha
        costo_inicial, stock_inicial = obtener_inicial(product_id)


        #ponemos en cero los que son ajuste de precio (cantidad = 0 y svl = true)
        setear_a_cero(iterador=f,layer=layers, dry_run=True)

        #ultimo paso para svl, promediar simulando la cronologia de compras y ventas
        promediar_costos(layers, costo_inicial, stock_inicial, dry_run=True) #dry_run false para activar escritura

        
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
