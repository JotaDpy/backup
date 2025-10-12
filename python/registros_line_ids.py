# exec(open('/home/jose/Documentos/clientes/17KEEPER/backup/python/registros_line_ids.py').read())

# Configuración para reconocimiento de Odoo en VS Code
# pylint: disable=undefined-variable
# pyright: reportUndefinedVariable=false

"""
Script para análisis de registros line_ids
EJECUTAR DESDE SHELL DE ODOO - env está disponible globalmente
"""

direccion = '/home/jose/Documentos/clientes/17KEEPER/backup/storage/analisis_nahuel.csv'

# Pedido de compras
purchase = env['purchase.order'].search([('name', '=', 'PO01524')])

# Cruce con 'account.move' y 'account.move.line'
facturas = env['account.move'].search([('invoice_origin', '=', purchase.name)])
account_move_line = env['account.move.line'].search([('move_id', 'in', facturas.ids)])
lineas = facturas.invoice_line_ids | facturas.line_ids

# Buscamos con que tipo de One2many está definido
venta = facturas.invoice_line_ids.ids
contable = facturas.line_ids.ids

# Scripts de lectura
contador = 0
contador_fact = 0
with open(direccion, 'w') as f:
    f.write('po_id,po_name,move_id,move_name,product_id,product_name,balance\n')

    for fact in facturas:
        # Contador factura
        contador_fact += 1

        # Unión de recordsets
        lines = fact.invoice_line_ids | fact.line_ids

        print(f'\n{"-"*40}')
        print(f'Factura: {fact.name}')
        print(f'Tamaño account_move_line: {len(lines)}')
        for line in lines:
            contador += 1
            descripcion = str(line.name).replace('"', '`') if line.name else ''

            # Para conocer su origen
            origen = None
            if line.id in venta:
                origen_line = 'invoice_line_ids'
            elif line.id in contable:
                origen_line = 'line_ids'

            # Escribimos en el .csv
            f.write(
                f'"{purchase.id}",'
                f'"{purchase.name}",'
                f'"{line.move_id.id}",'
                f'"{line.move_id.name}",'
                f'"{line.product_id.id if line.product_id else ""}",'
                f'"{descripcion}",'
                f'"{line.balance}"\n'
            )
            print(f'account_move_line.id: ({line.id} , {origen_line})')

# Impresiones
print(f'\nLineas totales: {contador}')
print(f'Factura totales: {contador_fact}')
