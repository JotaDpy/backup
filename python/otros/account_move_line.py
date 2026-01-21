# exec(open('/home/jose/Documentos/clientes/17KEEPER/backup/python/keeper/account_move_line.py').read())
# Configuración para reconocimiento de Odoo en VS Code
# pylint: disable=undefined-variable
# pyright: reportUndefinedVariable=false

factura = env['account.move'].browse(365115)
lineas = factura.invoice_line_ids

for reco in lineas:
    print(f'Nombre:    {reco.product_id.name}')
    print(f'Cuenta:    {reco.account_id.name}')
    print(f'Analítico: {reco.analytic_distribution}')
    print(f'Cantidad:  {reco.price_unit}\n')
