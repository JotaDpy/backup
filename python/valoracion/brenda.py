# exec(open('/home/jose/Documentos/clientes/15FONDOESTRELLA/clean_valuation/python/valoracion/brenda.py').read())
# Configuración para reconocimiento de Odoo en VS Code
# pylint: disable=undefined-variable
# pyright: reportUndefinedVariable=false

categorias = env['product.category'].search([
    ('property_valuation', '=', 'real_time')
])

for e in categorias:
    print(f'id: {e.id}')
    print(f'name: {e.name}')
    print(f'categoria: {e.property_valuation}\n')