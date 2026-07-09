CREATE TABLE tickets (
    id SERIAL PRIMARY KEY,
    cliente TEXT NOT NULL,
    asunto TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'abierto',
    creado_en TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    cedula TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    cargo TEXT NOT NULL CHECK (cargo IN ('atencion', 'rrhh', 'inventario', 'administrador')),
    creado_en TIMESTAMP NOT NULL DEFAULT now()
);

-- Cuentas creadas por auto-registro (validadas contra employees.cedula).
-- El personal LDAP (ana/carlos/maria) sigue entrando por OpenLDAP y no necesita fila aquí.
CREATE TABLE staff_accounts (
    id SERIAL PRIMARY KEY,
    cedula TEXT NOT NULL UNIQUE REFERENCES employees(cedula) ON DELETE CASCADE,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    creado_en TIMESTAMP NOT NULL DEFAULT now()
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
    ('Tienda Norte', 'Consulta de garantia', 'cerrado'),
    ('Ferreteria Union', 'Producto llego danado', 'abierto'),
    ('Panaderia Central', 'Solicita factura fiscal', 'en progreso'),
    ('Autoservicio Lopez', 'Cambio de direccion de envio', 'abierto'),
    ('Libreria Moderna', 'Reembolso por cancelacion', 'cerrado'),
    ('Farmacia San Jose', 'Duda sobre metodo de pago', 'cerrado');

-- ana/carlos/maria: mismo personal que ya existe en OpenLDAP (referencia, no necesitan auto-registro).
-- sofia/diego: ya se auto-registraron (fila abajo en staff_accounts), password Password123.
-- Admin Principal, Jorge Diaz, Lucia Fernandez, Pedro Ramirez: en el roster pero SIN cuenta
-- todavia, para probar el auto-registro por cedula.
INSERT INTO employees (cedula, nombre, cargo) VALUES
    ('V-00000001', 'Ana Gomez', 'atencion'),
    ('V-00000002', 'Carlos Perez', 'rrhh'),
    ('V-00000003', 'Maria Lopez', 'inventario'),
    ('V-00000004', 'Admin Principal', 'administrador'),
    ('V-00000005', 'Jorge Diaz', 'inventario'),
    ('V-00000006', 'Lucia Fernandez', 'atencion'),
    ('V-00000007', 'Pedro Ramirez', 'rrhh'),
    ('V-00000008', 'Sofia Castillo', 'atencion'),
    ('V-00000009', 'Diego Torres', 'inventario');

-- Cuentas ya auto-registradas de antemano (contraseña Password123 para ambas), para poder
-- iniciar sesion sin tener que pasar primero por "Registrarme".
INSERT INTO staff_accounts (cedula, username, password_hash) VALUES
    ('V-00000008', 'sofia', '$2a$10$tG3xy525DAv418V2DyuMZuVdnmU43KvjklHB4vtoykK1n6g.fu7su'),
    ('V-00000009', 'diego', '$2a$10$tG3xy525DAv418V2DyuMZuVdnmU43KvjklHB4vtoykK1n6g.fu7su');

INSERT INTO inventory (producto, cantidad, ubicacion, precio) VALUES
    ('Laptop 14"', 42, 'Bodega A', 549.99),
    ('Monitor 24"', 75, 'Bodega A', 189.50),
    ('Teclado mecanico', 120, 'Bodega B', 39.90),
    ('Mouse inalambrico', 200, 'Bodega B', 15.99),
    ('Impresora laser', 8, 'Bodega C', 259.00),
    ('Silla ergonomica', 5, 'Bodega C', 189.90),
    ('Audifonos bluetooth', 60, 'Bodega B', 45.50),
    ('Webcam HD', 34, 'Bodega B', 29.99),
    ('Router wifi', 3, 'Bodega C', 79.90),
    ('Disco SSD 1TB', 27, 'Bodega A', 89.00);

-- Cuenta de invitado ya registrada en online-platform/../proxy2/src/users.json
-- (usuario: cliente_demo, contraseña: DemoCliente123) — con 2 pedidos ya hechos,
-- para probar "Mis pedidos" y la pestaña "Pedidos" de Atención sin tener que comprar primero.
INSERT INTO orders (guest_username, estado, total, creado_en) VALUES
    ('cliente_demo', 'enviado', 605.98, now() - interval '3 days'),
    ('cliente_demo', 'pendiente', 45.50, now() - interval '1 day');

INSERT INTO order_items (order_id, producto, cantidad, precio_unitario) VALUES
    (1, 'Laptop 14"', 1, 549.99),
    (1, 'Mouse inalambrico', 1, 15.99),
    (1, 'Webcam HD', 1, 29.99),
    (2, 'Audifonos bluetooth', 1, 45.50);

UPDATE inventory SET cantidad = cantidad - 1 WHERE producto = 'Laptop 14"';
UPDATE inventory SET cantidad = cantidad - 1 WHERE producto = 'Mouse inalambrico';
UPDATE inventory SET cantidad = cantidad - 1 WHERE producto = 'Webcam HD';
UPDATE inventory SET cantidad = cantidad - 1 WHERE producto = 'Audifonos bluetooth';
