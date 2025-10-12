-- Para saber quien apunta a cierta tabla
    SELECT
        conname AS nombre_restriccion,
        conrelid::regclass AS tabla_origen,
        a.attname AS columna_origen,
        confrelid::regclass AS tabla_destino,
        af.attname AS columna_destino
    FROM
        pg_constraint c
    JOIN
        pg_attribute a ON a.attnum = ANY(c.conkey) AND a.attrelid = c.conrelid
    JOIN
        pg_attribute af ON af.attnum = ANY(c.confkey) AND af.attrelid = c.confrelid
    WHERE
        c.contype = 'f'
        AND confrelid::regclass::text = 'account_account';

-- Para saber en que tabla se encuentra dicho campo
SELECT
    table_schema,
    table_name,
    column_name
FROM
    information_schema.columns
WHERE
    column_name = 'property_account_income_id';

-- Sensible a mayúsculas y minúsculas (case-sensitive).
SELECT * FROM tu_tabla
WHERE columna_existente LIKE '%cadena%';

-- No Sensible a mayúsculas y minúsculas (case-sensitive).
SELECT * FROM tu_tabla
WHERE columna_existente ILIKE '%cadena%';

-- Para conocer la relación entre 2 tablas, mediante claves foráneas o directa
SELECT
    con.conname AS nombre_restriccion,
    conrelid::regclass AS tabla_origen,
    a.attname AS columna_origen,
    confrelid::regclass AS tabla_destino,
    af.attname AS columna_destino
FROM
    pg_constraint con
    JOIN pg_class rel ON rel.oid = con.conrelid
    JOIN pg_attribute a ON a.attrelid = con.conrelid AND a.attnum = ANY(con.conkey)
    JOIN pg_attribute af ON af.attrelid = con.confrelid AND af.attnum = ANY(con.confkey)
WHERE
    con.contype = 'f'
    AND conrelid::regclass::text IN ('account_orgen_pago', 'account_payment')
    AND confrelid::regclass::text IN ('account_orgen_pago', 'account_payment');

account_journal
account_payment