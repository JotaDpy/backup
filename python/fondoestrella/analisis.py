from collections import Counter

direccion = '/home/jose/Documentos/clientes/15FONDOESTRELLA/clean_valuation/python/valoracion/actualizacion_layers.yaml'

patron = "correction_type:"
casos = Counter()

with open(direccion, 'r', encoding='utf-8') as f:
    for linea in f:
        linea = linea.strip()
        if linea.startswith(patron):
            valor = linea.replace(patron, "").strip().strip('"')
            casos[valor] += 1

print(f'Cantidad de casos distintos: {len(casos)}\n')

for key, value in casos.items():
    print(f'"{key}": {value}')

print(f'Suma de todos los casos: {sum(casos.values())}')