# Análisis de los costos erróneos en KEEPER
El inconveniente radica en que el cliente hacía sus compras de productos en dólares, y el sistema no
contaba con una cotización ni una validación de control. Entonces cuando compraban 1 producto con
coste de 10 USD, el sistema lo adoptaba como 10 GS.

Se crearon cientos y cientos de facturas con este problema y tenemos que crear un algortimo que
solucione todos estos registros. Me gustaría hacerlo por bloques para ir probando y también hacer un
backup antes de eliminar los registros.

El flujo es el siguiente
- Pedido de Compra ('purchase.order')
- Facturas proveedores ('account.move')

Primero vamos a crear una tabla .csv de los registros de 'purchase.order' y mediante condicionales
ver a que facturas apuntan y entender como se comporta 'acccount.move'

<span style="color: aqua; font-size: 20px">Pedido de compra -> PO01810

```python
# Registros de pedido de compra
# unit_cost is not null and value is not null and (unit_cost = 0 or value = 0)
direccion = '/home/jose/Documentos/clientes/17KEEPER/backup/storage/purchase_order_usd.csv'
compras = env['purchase.order'].search([
    ('currency_id.name', '=', 'USD-COMPRA'),
    ("invoice_status", "=", "invoiced"),
])
with open(direccion, 'w') as f:
    f.write(f'id,name,moneda,estado,producto,cantidad,precio_unitario\n')
    for reco in compras:
        # Escribir la línea padre
        f.write(
            f'"{reco.id}",'
            f'"{reco.name}",'
            f'"{reco.currency_id.name}",'
            f'"{reco.state}",'
            f'"PADRE",'
            f'"",'
            f'""\n'
        )
        # Escribir cada producto como línea hija con indentación
        for line in reco.order_line:
            producto_name = line.product_id.name.replace(',', ' ').replace('"', '`') if line.product_id.name else 'Sin nombre'
            f.write(
                f'"",'  # ID vacío para líneas hijas
                f'"",'  # Name vacío para líneas hijas
                f'"",'  # Moneda vacía para líneas hijas
                f'"",'  # Estado vacío para líneas hijas
                f'"  └─ {producto_name}",'  # Producto con símbolo de indentación
                f'"{line.product_qty}",'
                f'"{line.price_unit}"\n'
            )

```
### Prueba de ejecución del método def action_view_picking()
Vamos a probar un experimento para el método en el formulario con name 'PO01818'

```python
compras = env['purchase.order'].search([('name', '=', 'PO01810')])
dicc = compras.action_view_picking()
for x, y in dicc.items():
    print(f'"{x}": {y}')

```
Esto nos retorna un diccionario que viene desde 'ir.actions.actions' de esta forma:

```json
{
    "id": 274,
    "name": "Transferencias",
    "type": "ir.actions.act_window",
    "xml_id": "stock.action_picking_tree_all",
    "help": "<p class=\"o_view_nocontent_smiling_face\">Defina una nueva transferencia</p>",
    "binding_model_id": null,
    "binding_type": "action",
    "binding_view_types": ["list", "form"],
    "display_name": "Transferencias",
    "view_id": null,
    "domain": [["id", "in", [63497, 63420]]],
    "context": {
    "default_partner_id": 46499,
    "default_origin": "PO01810",
    "default_picking_type_id": 5
    },
    "res_id": 0,
    "res_model": "stock.picking",
    "target": "current",
    "view_mode": ["tree", "kanban", "form", "calendar", "pivot"],
    "mobile_view_mode": "kanban",
    "views": [[null, "tree"], [null, "kanban"], [null, "form"], [null, "calendar"], [null, "pivot"]],
    "limit": 80,
    "groups_id": [],
    "search_view_id": [729, "stock.picking.internal.search"],
    "filter": false
}
```
Y es con la llave dicc["context"] que accedemos a otro diccionario que contiene el "origin",
esa llave nueva es la que nos dice a que pedido de compra está relacionado cierto 'stock.picking'

<span style="color: greenyellow; font-size: 20px">Prueba con -> SO35640

```python
venta = env['sale.order'].search([('name', '=', 'SO35640')])
dicc = venta.action_view_delivery()
for x, y in dicc.items():
    print(f'{x}: {y}')

```

Esto nos retorna también un diccionario de la siguiente manera, pero en este caso no tiene el origin
como 'PO...' si no como 'SO...'; solo nos sirve los que son del tipo 'PO' para nuestra tarea

```json
{
    "id": 274,
    "name": "Transferencias",
    "type": "ir.actions.act_window",
    "xml_id": "stock.action_picking_tree_all",
    "help": "<p class=\"o_view_nocontent_smiling_face\"> Defina una nueva transferencia </p>",
    "binding_model_id": null,
    "binding_type": "action",
    "binding_view_types": ["list", "form"],
    "display_name": "Transferencias",
    "view_id": null,
    "domain": [["id", "in", [52146, 52141]]],
    "context": {
    "lang": "es_PY",
    "tz": "America/Asuncion",
    "uid": 1,
    "default_partner_id": 16650,
    "default_picking_type_id": 3,
    "default_origin": "SO35640",
    "default_group_id": 23922
    },
    "res_id": 0,
    "res_model": "stock.picking",
    "target": "current",
    "view_mode": ["tree", "kanban", "form", "calendar", "pivot"],
    "mobile_view_mode": "kanban",
    "views": [[null, "tree"], [null, "kanban"], [null, "form"], [null, "calendar"], [null, "pivot"]],
    "limit": 80,    "id": 274,
    "name": "Transferencias",
    "type": "ir.actions.act_window",
    "xml_id": "stock.action_picking_tree_all",
    "help": "<p class=\"o_view_nocontent_smiling_face\">Defina una nueva transferencia</p>",
    "binding_model_id": null,
    "binding_type": "action",
    "binding_view_types": ["list", "form"],
    "display_name": "Transferencias",
    "view_id": null,
    "domain": [["id", "in", [63497, 63420]]],
    "context": {
    "default_partner_id": 46499,
    "default_origin": "PO01810",
    "default_picking_type_id": 5
    },
    "res_id": 0,
    "res_model": "stock.picking",
    "target": "current",
    "view_mode": ["tree", "kanban", "form", "calendar", "pivot"],
    "mobile_view_mode": "kanban",
    "views": [[null, "tree"], [null, "kanban"], [null, "form"], [null, "calendar"], [null, "pivot"]],
    "limit": 80,
    "groups_id": [],
    "search_view_id": [729, "stock.picking.internal.search"],
    "filter": false
    "groups_id": [],
    "search_view_id": [729, "stock.picking.internal.search"],
    "filter": false
}

```

encontrar un producto que tenga svl que sean de compra, de venta, y de modificaciones manuales
para no buscar lo mas rapido sera a un producto que tenga venta, modificarle el costo manualmente,
así creamos el svl de modificacion manual, ya que si hay una venta tuvo que haber una compra, por ende

## Registros erróneos para el modelo de 'stock.valuation.layer'
Tenemos que buscar los registros en donde las columnas de unit_cost y value tengan valores 0, ya que
no corresponde a un escenario correcto. La cantidad total segun Dbeaver es de 4173

### <span style="color: greenyellow"> Casos de unit_cost y value con valores igual a 0

```python
# unit_cost is not null and value is not  null and (unit_cost = 0 or value = 0)
layer = env['stock.valuation.layer'].search([
    ('unit_cost', '!=', False),
    ('value', '!=', False),
    '|',
    ('unit_cost', '=', '0'),
    ('value', '=', '0')
])

```
Este algoritmo me permite saber la cantidad de registros malos que vienen desde
el modelo 'stock.valuation.layer', ahora con otro algoritmo tengo que retroceder hasta llegar al
modelo de 'purchase.order'.

Todo esto para entender en cual de todos los caminos se ensucia y posteriormente aplciar una
solución.

## <span style="color: orange; font-size: 20px">Conexión de 'stock.picking' con 'stock.valuation.layer'
Tenemos que entender como funciona el método de conexión entre los modelos

```python
# Cen/WH/IN//03193
picking = env['stock.picking'].search([('name', '=', 'Cen/WH/IN//03193')])
dicc = picking.action_view_stock_valuation_layers()
for x, y in dicc.items():
    print(f'{x}: {y}')
dominio_id = dicc["domain"]
res_id = dicc["res_id"]
if dominio_ids:
    print(f'dominio_id: {dicc["domain"]} -> {type(dicc["domain"])}')
elif dominio_id:
    print(f'res_id: {dicc["res_id"]} -> {type(dicc["res_id"])}')


```
El campo que nos interesa es el que se encuentra en "domain" or "res_id"
```yaml
id: 1405
name: Valoración de stock
type: ir.actions.act_window
xml_id: stock_account.stock_valuation_layer_action
help: <p class="o_view_nocontent_smiling_face"></p>
            <p>
                No hay capas de valoración. Las capas de valoración se crean cuando hay movimientos de productos que impacten la valoración del stock.
            </p>
        
binding_model_id: False
binding_type: action
binding_view_types: list,form
display_name: Valoración de stock
view_id: (3749, 'stock.valuation.layer.tree')
domain: [('id', 'in', [163247, 163248, 163249])]
context: {'search_default_group_by_product_id': True, 'lang': 'es_PY', 'tz': 'America/Asuncion', 'uid': 1, 'no_at_date': True}
res_id: 0
res_model: stock.valuation.layer
target: current
view_mode: tree,form,pivot
mobile_view_mode: kanban
views: [(3749, 'tree'), (False, 'form'), (False, 'pivot')]
limit: 80
groups_id: []
search_view_id: False
filter: False
```

## <span style="color: orange; font-size: 20px">Conexión de 'purchase.order' con 'stock.picking'
Tenemos que entender como funciona el método de conexión entre los modelos

```python
# PO01818, PO01810
purchase = env['purchase.order'].search([('name', '=', 'PO01810')])
dicc = purchase.action_view_picking()
for x, y in dicc.items():
    print(elif dominio_id:
    print(f'dicc["res_id"]: {dicc["res_id"]} -> {type(dicc["res_id"])}')
f'{x}: {y}')
```
El campo que nos interesa es el que se encuentra en "domain" or "res_id"
```yaml
id: 274
name: Transferencias
type: ir.actions.act_window
xml_id: stock.action_picking_tree_all
help: <p class="o_view_nocontent_smiling_face">
                Defina una nueva transferencia
              </p>
            
binding_model_id: False
binding_type: action
binding_view_types: list,form
display_name: Transferencias
view_id: False
domain: [('id', 'in', [63497, 63420])]
context: {'default_partner_id': 46499, 'default_origin': 'PO01810', 'default_picking_type_id': 5}
res_id: 0
res_model: stock.picking
target: current
view_mode: tree,kanban,form,calendar,pivot
mobile_view_mode: kanban
views: [(False, 'tree'), (False, 'kanban'), (False, 'form'), (False, 'calendar'), (False, 'pivot')]
limit: 80
groups_id: []
search_view_id: (729, 'stock.picking.internal.search')
filter: False
```

product_id = 8644 or id = 150252

### QUERYS
Filtro por fecha ascendente
SELECT a1,a2,a3,a4,a5,a6,a7,a8,a9,a11,a12,a13,a14,a15,a16,a17,a18,a19,a20,a21,a22,a23 WHERE a9 > '2025-02-01' ORDER BY a9
SELECT a1,a2,a3,a4,a5,a6,a7,a8,a9,a11,a12,a13,a14,a15,a16,a17,a18,a19,a20,a21,a22,a23 WHERE a16 == 'posted'  ORDER BY a9

Filtro por cantidad positivo
SELECT a1,a2,a3,a4,a5,a6,a7,a8,a9,a11,a12,a13,a14,a15,a16,a17,a18,a19,a20,a21,a22,a23 WHERE a12 > 0.0 ORDER BY a9

Igual que Odoo
SELECT a2,a14,a9,a12,a10,a11,a20,a18,a19,a16,a17,a23 WHERE a9 > '2025-02-01' ORDER BY a9

Igual que el Layer
SELECT a1,a2,a3,a4,a5,a6,a7,a8,a9,a10,a11,a12,a13,a14,a15,a16,a17,a18,a19,a20,a21,a22 WHERE a16 != '' ORDER BY a9

## Prueba corta

```python
direccion = '/home/jose/Documentos/clientes/17KEEPER/backup/storage/analisis_nahuel.csv'
purchase = env['purchase.order'].search([('name', '=', 'PO01524')])
facturas = env['account.move'].search([('invoice_origin', '=', purchase.name)])
account_move_line = env['account.move.line'].search([('move_id', 'in', facturas.ids)])
lineas = facturas.invoice_line_ids | facturas.line_ids
# ABRIR ARCHIVO UNA SOLA VEZ
contador = 0
contador_fact = 0
with open(direccion, 'w') as f:
    # HEADER UNA SOLA VEZ
    f.write('po_id,po_name,move_id,move_name,product_id,product_name,balance\n')
    # ESCRIBIR LÍNEAS SIN REABRIR EL ARCHIVO
    for fact in facturas:
        lines = lineas = fact.invoice_line_ids | fact.line_ids
        contador_fact += 1
        print(f'fact: {fact.name}')
        print(f'len invoice_line_ids: {len(lines)}')
        for line in lines:
            print(f'ID LINE: {line.id}')
            contador += 1
            descripcion = str(line.name).replace('"', '`') if line.name else ''
            f.write(
                f'"{purchase.id}",'
                f'"{purchase.name}",'
                f'"{line.move_id.id}",'
                f'"{line.move_id.name}",'
                f'"{line.product_id.id if line.product_id else ""}",'
                f'"{descripcion}",'
                f'"{line.balance}"\n'
            )
            print()
print(f'Contador: {contador}')
print(f'Contador fact: {contador_fact}')


```

stock_move_id in (110124, 93542, 93711, 103123, 122829, 122831, 122837, 122830, 124285, 124396, 124679, 125026, 108863, 109164, 109806, 122838)

Estos son los ids en donde:
purchase_line_ids = null and (location_id = 5 or location_dest_id = 5)


## Casos donde puede haber SVL sin purchase line debido a que son ajustes de inventario
En total vamos a tener 3 algoritmos en el modelo de SLV
- Limpieza para quantity > 0 (igualar SVL a su account_move_line de compra correspondiente)

- Limpieza para quantity = 0 and stock_valuation_layer_id != False (Casos de ajuste de precio, setear en 0 ya que en la compra ya estara correcto el costeo)

- Limpieza para todos los casos (sucios y limpios por igual) * Calculo de promediacion de costos simulando todo el circuito, Compras, Ajustes Manuales, Ventas, Ajustes de Inventario

### cuando corresponde a un ajuste de inventario, lo que hace es:
- cargar la cantidad del producto, ya sea positivo o negativo, y carga el costo actual del producto en ese momento
Ej. tenemos 10 unid de producto A en stock, y en odoo figura 8, entonces en el ajuste se crea un SVL con la sgte estructura:
quantity: 2 | unit_cost: 1000 | value: 2000

pero como no podemos confiar en que en ese momento el costo que tomo odoo haya sido correcto, por lo que cuando
encontremos estos casos deberemos cargarle el costo que tenemos en nuestra variable temporal;
(algoritmo no creado aun) donde estamos almacenando el costo del producto a cargar

en el algoritmo 1 ignoramos ya que solo procesaremos compras (q > 0)

Y a la inversá será con quantity < 0 y tambiémn con su propio algoritmo

### CON A ID = 5 (Inventory adjustment)
INVENTARIO -----> +++++q
Tenemos 107 registros de 'stock.valuation.layer' en donde el stock_move.location_id.id = 5 (Inventory adjustment)

INVENTARIO -----> -----q
Tenemos 80 registros de 'stock.valuation.layer' en donde el stock_move.location_dest_id.id = 5

### CON EL ID != 5
INVENTARIO -----> +++++q
Tenemos 329 registros de 'stock.valuation.layer' en donde el stock_move.location_id.id != 5

(si viene de una ubicacion del cliente, oseea es una devolucion, entonces se comportara igual que el caso de inventory adjustment)


INVENTARIO -----> +++++q
Tenemos 436 registros de 'stock.valuation.layer' en donde el stock_move.location_dest_id.id != 5

