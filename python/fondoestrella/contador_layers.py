from collections import Counter
import calendar

def traduccion_mes(mes):
    return  {
        'january': 'enero', 'february': 'febrero', 'march': 'marzo',
        'april': 'abril', 'may': 'mayo', 'june': 'junio',
        'july': 'julio', 'august': 'agosto', 'september': 'septiembre',
        'october': 'octubre', 'november': 'noviembre', 'december': 'diciembre',
    }.get(mes, 'N/A')

def meses_anho(anho):
    meses = {}
    for mes in range(1, 13):
        nombre_mes = calendar.month_name[mes].lower()
        dias_mes = calendar.monthrange(anho, mes)[1]
        meses[nombre_mes] = dias_mes
    return meses


anho = 2025
meses = meses_anho(anho)
impresion = '/home/jose/Documentos/clientes/15FONDOESTRELLA/clean_valuation/python/fondoestrella/contador_layers.txt'
# Se abre el archivo para su ecritura (creacion de archivo con w)
with open(impresion, 'w', encoding='utf-8') as p:

    # Iteracion de meses para la escritura de datos de los archivos 
    casos = set()
    for mes_num, (mes_str, dias) in enumerate(meses.items(), start=1):
        proyecto = '/home/jose/Documentos/clientes/15FONDOESTRELLA/'
        modulo = 'clean_valuation/python/valoracion/'
        archivo = f'actualizacion_layers.yaml'
        direccion = proyecto + modulo + archivo
        operador = 'w'

        # Se filtran los tipos de casos mediante el patron en el archivo original
        patron = "total_layers:"
        with open(direccion, 'r', encoding='utf-8') as f:
            for linea in f:
                linea = linea.strip()
                if linea.startswith(patron):
                    valor = linea.replace(patron, "").strip().strip('"')
                    casos.add(int(valor))
        print(f'Archivo: {direccion}')

    p.write(f'Estructura: {sorted(list(casos), reverse=True)}\n')
    p.write(f'Tamano: {len(list(casos))}')
