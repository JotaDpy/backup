# exec(open('/home/jose/Documentos/clientes/17KEEPER/backup/python/grupos_bloquedos.py').read())
# Configuración para reconocimiento de Odoo en VS Code
# pylint: disable=undefined-variable
# pyright: reportUndefinedVariable=false

grupo = env['res.groups'].browse(294)
usuarios = grupo.users
print(f'Usuario | Inicio de sesión | Idioma | Última autenticación | Compañia | Estado')
for user in usuarios:
    print(
    f'{user.name} | '
    f'{user.login} | '
    f'{user.lang} | '
    f'{user.login_date} | '
    f'{user.company_id} | '
    f'{user.state}'
    )
