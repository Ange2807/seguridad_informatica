CREATE TABLE tickets (
    id SERIAL PRIMARY KEY,
    cliente TEXT NOT NULL,
    asunto TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'abierto',
    creado_en TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    puesto TEXT NOT NULL,
    area TEXT NOT NULL,
    contratado_en DATE NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE inventory (
    id SERIAL PRIMARY KEY,
    producto TEXT NOT NULL,
    cantidad INTEGER NOT NULL DEFAULT 0,
    ubicacion TEXT NOT NULL,
    precio NUMERIC(10,2) NOT NULL DEFAULT 0,
    actualizado_en TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    guest_username TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'pendiente',
    total NUMERIC(10,2) NOT NULL DEFAULT 0,
    creado_en TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    producto TEXT NOT NULL,
    cantidad INTEGER NOT NULL,
    precio_unitario NUMERIC(10,2) NOT NULL
);

INSERT INTO tickets (cliente, asunto, estado) VALUES
    ('Comercial ACME', 'Factura duplicada', 'abierto'),
    ('Distribuidora Sol', 'Retraso en entrega', 'en progreso'),
    ('Tienda Norte', 'Consulta de garantia', 'cerrado');

INSERT INTO employees (nombre, puesto, area) VALUES
    ('Carlos Perez', 'Analista de RRHH', 'Recursos Humanos'),
    ('Sofia Reyes', 'Reclutadora', 'Recursos Humanos'),
    ('Luis Marin', 'Gerente de Planta', 'Operaciones');

INSERT INTO inventory (producto, cantidad, ubicacion, precio) VALUES
    ('Laptop 14"', 42, 'Bodega A', 549.99),
    ('Monitor 24"', 75, 'Bodega A', 189.50),
    ('Teclado mecanico', 120, 'Bodega B', 39.90);
