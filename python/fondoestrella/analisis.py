from os import sep

direccion = '/home/jose/Documentos/clientes/15FONDOESTRELLA/backup/python/valoracion/actualizacion_layers.yaml'
casos = []

# with open(direccion, 'r', encoding='utf-8') as f:
#     for linea in f:
#         linea = linea.strip()
#         if linea and "correction_type: " in linea:
#         	try:
#         		casos.append(linea.split("correction_type: ")[-1])
#         	except ValueError as error:
#         		print(casos.append(f"ERROR: {error}"))

patron = "total_layers: "
with open(direccion, 'r', encoding='utf-8') as f:
    for linea in f:
        linea = linea.strip()
        if linea and patron in linea:
            try:
                casos.append(int(linea.split(patron)[-1]))
            except ValueError as error:
                print(casos.append(f"ERROR: {error}"))

casos_unicos = sorted(list(set(casos)))

print(f'Cantidad de casos: {len(casos_unicos)}')
print(casos_unicos)
