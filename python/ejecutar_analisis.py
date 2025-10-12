#!/usr/bin/env python3
# exec(open('/home/jose/Documentos/clientes/17KEEPER/backup/python/ejecutar_analisis.py').read())
# SELECT a1,a2,a3,a4,a5,a6,a7,a8,a9,a10,a11,a12,a13,a14,a15,a16,a17,a18,a19,a20 WHERE a9 == 0.0 | a10 == 0.0 ORDER BY a2

# Configuración para reconocimiento de Odoo en VS Code
# pylint: disable=undefined-variable
# pyright: reportUndefinedVariable=false

"""
Script simplificado para ejecutar el análisis desde el shell de Odoo
Ejecutar con: exec(open('ejecutar_analisis.py').read())
"""

# DIAGNÓSTICO: ¿Por qué account_move_line_id es NULL?
print("🔍 PASO 1: DIAGNÓSTICO - Investigando account_move_line_id...")

query_diagnostico = """
SELECT 
    COUNT(*) as total_layers,
    COUNT(account_move_line_id) as layers_con_aml_id,
    COUNT(*) - COUNT(account_move_line_id) as layers_sin_aml_id
FROM stock_valuation_layer svl
WHERE svl.id IN (
    SELECT DISTINCT svl2.id 
    FROM purchase_order po
    LEFT JOIN res_currency rc ON rc.id = po.currency_id
    LEFT JOIN stock_picking sp ON sp.origin = po.name
    LEFT JOIN stock_move sm ON sm.picking_id = sp.id
    LEFT JOIN stock_valuation_layer svl2 ON svl2.stock_move_id = sm.id
    WHERE po.currency_id IS NOT NULL
    AND sp.id IS NOT NULL
    AND svl2.id IS NOT NULL
    AND rc.name LIKE '%USD%'
)
"""

env.cr.execute(query_diagnostico)
diagnostico = env.cr.fetchone()

print(f"📊 Total layers USD: {diagnostico[0]}")
print(f"📊 Layers con account_move_line_id: {diagnostico[1]}")
print(f"📊 Layers sin account_move_line_id: {diagnostico[2]}")

# PASO 2: Investigar conexión contable alternativa
print("\n🔍 PASO 2: Investigando conexión contable alternativa...")

query_po_account_move = """
SELECT 
    COUNT(DISTINCT po.id) as total_po_usd,
    COUNT(DISTINCT am.id) as facturas_relacionadas,
    COUNT(DISTINCT aml.id) as lineas_contables
FROM purchase_order po
LEFT JOIN res_currency rc ON rc.id = po.currency_id
LEFT JOIN account_move am ON am.invoice_origin = po.name
LEFT JOIN account_move_line aml ON aml.move_id = am.id
WHERE rc.name LIKE '%USD%'
AND po.invoice_status = 'invoiced'
"""

env.cr.execute(query_po_account_move)
conexion_contable = env.cr.fetchone()

print(f"📊 Purchase Orders USD: {conexion_contable[0]}")
print(f"📊 Facturas relacionadas: {conexion_contable[1]}")
print(f"📊 Líneas contables disponibles: {conexion_contable[2]}")

# PASO 3: Ejecutar análisis completo
print("\n🔧 PASO 3: Ejecutando análisis completo...")

import os
from datetime import datetime

# INSTRUCCIÓN: Cambiar esta ruta por donde esté la carpeta 'backup' en tu máquina
output_dir = '/home/jose/Documentos/clientes/17KEEPER/backup/keep'
os.makedirs(output_dir, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
archivo_principal = f'{output_dir}/analisis_costos.csv'
archivo_manual = f'{output_dir}/analisis_costos_manual.csv'
archivo_txt = f'{output_dir}/resumen_costos.txt'

# Decidir si incluir contabilidad basado en si hay facturas
incluir_contabilidad = conexion_contable[1] > 0

if incluir_contabilidad:
    print("✅ Ejecutando con datos contables...")
    # Query con datos contables
    query_completa = """
    SELECT DISTINCT
        po.id as po_id,
        po.name as po_name,
        po.currency_id,
        rc.name as currency_name,
        sp.id as picking_id,
        sp.name as picking_name,
        sp.origin,
        svl.id as layer_id,
        svl.create_date as layer_create_date,
        svl.unit_cost,
        svl.value,
        svl.quantity,
        svl.description,
        svl.account_move_line_id as account_move_line_layer_id,
        am.id as invoice_id,
        am.name as invoice_name,
        am.state as invoice_state,
        aml.id as move_line_id,
        aml.name as move_line_name,
        aml.balance as move_line_balance,
        aml.debit,
        aml.credit,
        CASE 
            WHEN svl.unit_cost = 0 OR svl.value = 0 THEN 'PROBLEMATICO'
            WHEN rc.name LIKE '%USD%' THEN 'USD_REVISAR'
            ELSE 'OK'
        END as status
    FROM purchase_order po
    LEFT JOIN res_currency rc ON rc.id = po.currency_id
    LEFT JOIN stock_picking sp ON sp.origin = po.name
    LEFT JOIN stock_move sm ON sm.picking_id = sp.id
    LEFT JOIN stock_valuation_layer svl ON svl.stock_move_id = sm.id
    LEFT JOIN account_move am ON am.invoice_origin = po.name AND am.move_type = 'in_invoice'
    LEFT JOIN account_move_line aml ON aml.move_id = am.id AND aml.product_id = svl.product_id
    WHERE po.currency_id IS NOT NULL
    AND sp.id IS NOT NULL
    AND svl.id IS NOT NULL
    AND (
        svl.unit_cost = 0 
        OR svl.value = 0 
        OR rc.name LIKE '%USD%'
    )
    ORDER BY po.id, sp.id, svl.id
    """
    
    headers = [
        'po_id', 'po_name', 'currency_id', 'currency_name', 
        'picking_id', 'picking_name', 'origin', 'layer_id',
        'layer_create_date', 'unit_cost', 'value', 'quantity', 'description',
        'account_move_line_layer_id', 'invoice_id', 'invoice_name', 
        'invoice_state', 'move_line_id', 'move_line_name', 'move_line_balance', 
        'debit', 'credit', 'status'
    ]
else:
    print("⚠️ Ejecutando sin datos contables...")
    # Query sin datos contables
    query_completa = """
    SELECT DISTINCT
        po.id as po_id,
        po.name as po_name,
        po.currency_id,
        rc.name as currency_name,
        sp.id as picking_id,
        sp.name as picking_name,
        sp.origin,
        svl.id as layer_id,
        svl.create_date as layer_create_date,
        svl.unit_cost,
        svl.value,
        svl.quantity,
        svl.description,
        svl.account_move_line_id as account_move_line_layer_id,
        CASE 
            WHEN svl.unit_cost = 0 OR svl.value = 0 THEN 'PROBLEMATICO'
            WHEN rc.name LIKE '%USD%' THEN 'USD_REVISAR'
            ELSE 'OK'
        END as status
    FROM purchase_order po
    LEFT JOIN res_currency rc ON rc.id = po.currency_id
    LEFT JOIN stock_picking sp ON sp.origin = po.name
    LEFT JOIN stock_move sm ON sm.picking_id = sp.id
    LEFT JOIN stock_valuation_layer svl ON svl.stock_move_id = sm.id
    WHERE po.currency_id IS NOT NULL
    AND sp.id IS NOT NULL
    AND svl.id IS NOT NULL
    AND (
        svl.unit_cost = 0 
        OR svl.value = 0 
        OR rc.name LIKE '%USD%'
    )
    ORDER BY po.id, sp.id, svl.id
    """
    
    headers = [
        'po_id', 'po_name', 'currency_id', 'currency_name',
        'picking_id', 'picking_name', 'origin', 'layer_id',
        'layer_create_date', 'unit_cost', 'value', 'quantity', 'description', 
        'account_move_line_layer_id', 'status'
    ]

print(f"🚀 Ejecutando query...")
env.cr.execute(query_completa)
results = env.cr.fetchall()

print(f"📝 Escribiendo archivos...")

# Archivo con .write() directo (tu formato preferido)
with open(archivo_manual, 'w') as f:
    # Escribir header
    f.write(','.join([f'"{h}"' for h in headers]) + '\n')
    
    problematicos = 0
    usd_revisar = 0
    con_datos_contables = 0
    
    for row in results:
        # Limpiar y formatear cada campo
        formatted_fields = []
        for field in row:
            if field is None:
                formatted_fields.append('""')
            elif isinstance(field, str):
                # Limpiar texto para CSV - REMOVER SALTOS DE LÍNEA
                clean_text = field.replace(',', ';').replace('"', "'").replace('\n', ' ').replace('\r', ' ').strip()
                formatted_fields.append(f'"{clean_text}"')
            else:
                formatted_fields.append(f'"{field}"')

        f.write(','.join(formatted_fields) + '\n')
        
        # Contar estadísticas
        status = row[-1]  # El status es el último campo
        if status == 'PROBLEMATICO':
            problematicos += 1
        elif status == 'USD_REVISAR':
            usd_revisar += 1
        
        # Si incluye contabilidad, contar registros con datos contables
        if incluir_contabilidad and len(row) > 17 and row[17]:  # move_line_id (ahora en posición 17)
            con_datos_contables += 1

# Archivo .txt con resumen
with open(archivo_txt, 'w') as f:
    f.write("ANÁLISIS DE COSTOS USD EN KEEPER\n")
    f.write("=" * 50 + "\n\n")
    f.write(f"Fecha de análisis: {timestamp}\n")
    f.write(f"Total registros: {len(results)}\n")
    f.write(f"Problemáticos: {problematicos}\n")
    f.write(f"USD a revisar: {usd_revisar}\n")
    if incluir_contabilidad:
        f.write(f"Con datos contables: {con_datos_contables}\n")
    f.write("\n" + "=" * 50 + "\n\n")
    
    # Escribir algunos ejemplos de registros problemáticos
    f.write("EJEMPLOS DE REGISTROS PROBLEMÁTICOS:\n")
    f.write("-" * 30 + "\n")
    count = 0
    for row in results:
        status = row[-1] if len(row) > 0 else ''
        if status == 'PROBLEMATICO' and count < 10:
            f.write(f"PO: {row[1]}, Layer: {row[7]}, unit_cost: {row[8]}, value: {row[9]}\n")
            count += 1

print("=" * 60)
print("✅ ANÁLISIS COMPLETADO!")
print("=" * 60)
print(f"📄 Total registros procesados: {len(results)}")
print(f"🚨 Registros problemáticos: {problematicos}")
print(f"💰 Registros USD para revisar: {usd_revisar}")
if incluir_contabilidad:
    print(f"🧾 Registros con datos contables: {con_datos_contables}")

print(f"\n📁 ARCHIVOS GENERADOS:")
print(f"   📊 CSV manual: {archivo_manual}")
print(f"   📄 TXT resumen: {archivo_txt}")
print(f"\n🎉 ¡Análisis completado exitosamente!")