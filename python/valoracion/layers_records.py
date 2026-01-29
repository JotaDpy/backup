# exec(open('/home/jose/Documentos/clientes/15FONDOESTRELLA/clean_valuation/python/valoracion/layers_records.py').read())
# Configuración para reconocimiento de Odoo en VS Code
# pylint: disable=undefined-variable
# pyright: reportUndefinedVariable=false

import csv


def buscar_valuation(product_list):
    # Nota el 'return', si no la función no devuelve nada
    producto = env['product.product'].browse(product_list)
    return producto

# Buscamos direcció
proyecto = '/home/jose/Documentos/clientes/15FONDOESTRELLA/'
modules = 'clean_valuation/python/valoracion/'
archivo = 'analisis_jota.csv'
direccion = proyecto + modules + archivo

# Buscamos productos + attrs

opciones = [1632, 1772, 3281, 3535, 4899]
productos = buscar_valuation(opciones)
campos_usados = [
    'id', 'display_name',
    'remaining_qty', 'remaining_value',
    'description', 'stock_move_id',
    'account_move_id', 'create_date',
]

# Abrimos el archivo que esta en la variable direccion
with open(direccion, 'w', encoding='utf-8') as f:
    w = csv.writer(f)

    # Se escribe la cabecera
    f.write(f'id,display_name,remaining_qty,'
            f'remaining_value,description,stock_move_id,'
            f'account_move_id,create_date\n')

    for prod in productos:
        valoraciones = prod.stock_valuation_layer_ids
        # Se escriben las filas
        for val in valoraciones:
            stock_move_id = str(val.stock_move_id).replace(',', '')
            account_move_id = str(val.account_move_id).replace(',', '')
            f.write(f'{val.id},')
            f.write(f'{val.display_name[:16]},')
            f.write(f'{val.remaining_qty},')
            f.write(f'{val.remaining_value:.2f},')
            f.write(f'{val.description[0:30]},')
            f.write(f'{stock_move_id},')
            f.write(f'{account_move_id},')
            f.write(f'{val.create_date}\n')
        for _ in range(2):
            f.write(f'{"-"*10},')
            f.write(f'{"-"*10},')
            f.write(f'{"-"*10},')
            f.write(f'{"-"*10},')
            f.write(f'{"-"*10},')
            f.write(f'{"-"*10},')
            f.write(f'{"-"*10},')
            f.write(f'{"-"*10}\n')
