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


referencias = [
'1293', '1199', '968', '864', '775', '724', '723', '697',
'680', '645', '642', '635', '633', '613', '560', '471',
'443', '431', '367', '339', '323', '312', '296', '282',
'263', '260', '259', '251', '238', '235', '229', '221',
'202', '199', '197', '194', '193', '192', '190', '188',
'181', '176', '173', '172', '171', '167', '163', '162',
'158', '156', '150', '148', '146', '144', '139', '138',
'136', '130', '127', '126', '125', '124', '123', '122',
'119', '117', '116', '108', '107', '106', '103', '102',
'99', '93', '92', '91', '90', '89', '88', '87', '85',
'82', '81', '80', '79', '78', '77', '76', '74', '73',
'72', '71', '70', '69', '67', '66', '65', '63', '62',
'60', '59', '58', '57', '56', '55', '54', '53', '52',
'51', '50', '49', '48', '47', '46', '45', '44', '43',
'42', '41', '40', '39', '38', '37', '36', '35', '34',
'33', '32', '31', '30', '29', '28', '27', '26', '25',
'24', '23', '22', '21', '20', '19', '18', '17', '16',
'15', '14', '13', '12', '11', '10', '9', '8', '7', '6',
'5', '4', '3', '2', '1'
]

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
