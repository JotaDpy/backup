from datetime import datetime, timedelta
import calendar

anho = 2025
meses = {}

for mes in range(1, 13):
    nombre_mes = calendar.month_name[mes].lower()
    
    dias_mes = calendar.monthrange(anho, mes)[1]
    meses[nombre_mes] = dias_mes

for mes_num, (mes_str, dias) in enumerate(meses.items(), start=1):
    date_from = datetime(anho, mes_num, 1)
    date_to = datetime(anho, mes_num, dias, 23, 59, 59)

    print(f'Mes en cadena: {mes_str} | {type(mes_str)}')
    print(f'Mes en numero: {mes_num} | {type(mes_num)}')
    print(f'Desde: {date_from} | {type(date_from)}')
    print(f'Hasta: {date_to} | {type(date_to)}')
    print()
