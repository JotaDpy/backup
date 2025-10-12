# exec(open('/home/jose/Documentos/clientes/17KEEPER/backup/python/actualizacion_layers.py').read())
# Configuración para reconocimiento de Odoo en VS Code
# pylint: disable=undefined-variable
# pyright: reportUndefinedVariable=false

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

direccion = '/home/jose/Documentos/clientes/17KEEPER/backup/storage/analisis_nahuel.csv'
direccion2 = '/home/jose/Documentos/clientes/17KEEPER/backup/keep/actualizazcion_layers.yaml'

# ------ PRIMERA FORMA ------
# Búsquedas de 'purchase.order'
product_id = 8644
purchase = env['purchase.order'].search([('name', '=', 'PO01524')])
purchase_line = purchase.order_line.filtered(lambda x: x.product_id.id == product_id)

# Busquedas de layers
layers = buscar_layers_positivos(
    env=env,
    producto=product_id,
    orden="asc",
    cantidad=None,
    fecha_inicio='2025-02-01',
)
layer_quantity_unique = buscar_layers_positivos(
    env=env,
    producto=product_id,
    orden="asc",
    cantidad=1,
    fecha_inicio='2025-02-01',
)

# Algortimo para cruzar 'stock.valuation.layer' con 'purchase.order.line'
stock_move = layer_quantity_unique.stock_move_id
purchase_order_line = stock_move.purchase_line_id

print(f'purchase_order_line: {purchase_order_line}\n\n')

account_move_line = env['account.move.line'].search([('purchase_line_id', '=', purchase_order_line.id)])
filtro_lineas = account_move_line.filtered(
    lambda x: x.purchase_line_id.id in purchase_line.ids
    and x.move_id.move_type == 'in_invoice'
).sorted('create_date', reverse=False)[:1]

for record in filtro_lineas or []:
    print(f' - Factura:            {record.move_id.name}')
    print(f'       * Línea:        {record.name}')
    print(f'       * Fecha:        {record.invoice_date}')
    print(f'       * Línea compra: {record.purchase_line_id}\n')

# Búsquedas de 'account.move.line'
facturas = env['account.move'].search([('invoice_origin', '=', purchase.name)])
account_move_line = env['account.move.line'].search([('move_id', 'in', facturas.ids)], order="invoice_date asc")
lineas = (facturas.invoice_line_ids).filtered(
    lambda x: x.purchase_line_id.id in purchase_line.ids and x.move_type == 'in_invoice'
)[0]

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


# Impresiones
print(f'\nCantidad layers:  {len(layers)}')
print(f'Layers positivos: {len(layer_quantity_unique)}')

print(f'Pedido de compra: {purchase.name}')
print(f'Líneas: {purchase_line.ids}')
print(f'purchase_line: {purchase_line}')
print(f'product_product: {product_id}')
print(f'\naccount_move: {facturas.mapped('name')}')
print(f'account_move_line ids: {lineas}')
print(f'account_move_line names:')
for record in lineas or []:
    print(f'    - {record.name} -> {record.move_id.name} - {record.purchase_line_id}')

