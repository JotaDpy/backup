#!/usr/bin/env python3
"""
Versión debug para entender el problema paso a paso
"""

# Para autocompletado en VS Code
try:
    from odoo_env_types import env
except ImportError:
    pass

print("🔍 DIAGNÓSTICO: ¿Por qué solo se imprime una línea?")
print("=" * 50)

# Búsqueda de purchase order
direccion = '/home/jose/Documentos/clientes/17KEEPER/backup/storage/analisis_nahuel_debug.csv'
purchase = env['purchase.order'].search([('name', '=', 'PO01524')])

if not purchase:
    print("❌ No se encontró la Purchase Order PO01524")
    exit()

print(f"✅ Purchase Order encontrada: {purchase.name}")
print(f"📦 Productos en líneas: {len(purchase.order_line)}")

# Buscar facturas relacionadas
facturas = env['account.move'].search([('invoice_origin', '=', purchase.name)])
print(f"📄 Facturas relacionadas: {len(facturas)}")

if not facturas:
    print("❌ No hay facturas relacionadas con este PO")
    exit()

# Contar líneas totales antes de escribir
total_lineas = 0
for fact in facturas:
    print(f"  📋 Factura {fact.name}: {len(fact.invoice_line_ids)} líneas")
    total_lineas += len(fact.invoice_line_ids)

print(f"📊 Total de líneas a escribir: {total_lineas}")

if total_lineas == 0:
    print("❌ No hay líneas de factura para procesar")
    exit()

print("\n🔧 Escribiendo archivo...")

# ESCRITURA CORRECTA
with open(direccion, 'w') as f:
    # Header una sola vez
    f.write('po_id,po_name,move_id,move_name,product_id,product_name,balance\n')
    
    lineas_escritas = 0
    for i, fact in enumerate(facturas):
        print(f"  📋 Procesando factura {i+1}/{len(facturas)}: {fact.name}")
        
        for j, line in enumerate(fact.invoice_line_ids):
            lineas_escritas += 1
            descripcion = str(line.name).replace('"', '`') if line.name else 'Sin descripción'
            
            # Escribir línea
            linea_csv = (
                f'"{purchase.id}",'
                f'"{purchase.name}",'
                f'"{line.move_id.id}",'
                f'"{line.move_id.name}",'
                f'"{line.product_id.id if line.product_id else ""}",'
                f'"{descripcion}",'
                f'"{line.balance}"\n'
            )
            
            f.write(linea_csv)
            print(f"    ✍️  Línea {lineas_escritas} escrita")

print(f"\n✅ Proceso completado!")
print(f"📊 Líneas esperadas: {total_lineas}")
print(f"📊 Líneas escritas: {lineas_escritas}")
print(f"💾 Archivo guardado: {direccion}")

# Verificar archivo final
import os
if os.path.exists(direccion):
    with open(direccion, 'r') as f:
        lineas_archivo = f.readlines()
    print(f"📄 Líneas en archivo: {len(lineas_archivo)} (incluyendo header)")
    
    print("\n🔍 Primeras 3 líneas del archivo:")
    for i, linea in enumerate(lineas_archivo[:3]):
        print(f"  {i+1}: {linea.strip()}")
else:
    print("❌ El archivo no se creó correctamente")