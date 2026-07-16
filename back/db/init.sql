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
    disponible BOOLEAN NOT NULL DEFAULT true,
    actualizado_en TIMESTAMP NOT NULL DEFAULT now()
);

-- guest_username: pedidos del checkout de invitado (histórico/backend, sin frontend activo hoy).
-- cliente_nombre/cliente_cedula: pedidos creados por Atención a nombre de un comprador sin cuenta.
-- Un pedido siempre trae uno de los dos pares de datos, nunca ambos.
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    guest_username TEXT,
    cliente_nombre TEXT,
    cliente_cedula TEXT,
    estado TEXT NOT NULL DEFAULT 'pendiente',
    total NUMERIC(10,2) NOT NULL DEFAULT 0,
    creado_en TIMESTAMP NOT NULL DEFAULT now(),
    CHECK (guest_username IS NOT NULL OR (cliente_nombre IS NOT NULL AND cliente_cedula IS NOT NULL))
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
    ('00000001', 'Ana Gomez', 'atencion'),
    ('00000002', 'Carlos Perez', 'rrhh'),
    ('00000003', 'Maria Lopez', 'inventario'),
    ('00000004', 'Admin Principal', 'administrador'),
    ('00000005', 'Jorge Diaz', 'inventario'),
    ('00000006', 'Lucia Fernandez', 'atencion'),
    ('00000007', 'Pedro Ramirez', 'rrhh'),
    ('00000008', 'Sofia Castillo', 'atencion'),
    ('00000009', 'Diego Torres', 'inventario'),
    ('30973666', 'Angelina Rincon', 'administrador'),
    ('31778858', 'Sarai Rincon', 'rrhh');

-- Cuentas ya auto-registradas de antemano, para poder iniciar sesion sin tener que pasar
-- primero por "Registrarme". sofia/diego: password Password123. ange: password 123456789.
-- sarai: password 987654321.
INSERT INTO staff_accounts (cedula, username, password_hash) VALUES
    ('00000008', 'sofia', '$2a$10$tG3xy525DAv418V2DyuMZuVdnmU43KvjklHB4vtoykK1n6g.fu7su'),
    ('00000009', 'diego', '$2a$10$tG3xy525DAv418V2DyuMZuVdnmU43KvjklHB4vtoykK1n6g.fu7su'),
    ('30973666', 'ange', '$2a$10$ZiCPyYN/Sn5uvQockp7xeOtotWeYnT5Dh0qbf5.SQRey/KtksiIBK'),
    ('31778858', 'sarai', '$2a$10$GfPS3iPxQBZGflde8sF6t.49/xm7cRHopzIs1ygeOKUkcDbQqS2eu');

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

-- Pedido de ejemplo creado por Atención a nombre de un comprador sin cuenta.
INSERT INTO orders (cliente_nombre, cliente_cedula, estado, total, creado_en) VALUES
    ('Roberto Salas', 'V-00000010', 'pendiente', 189.50, now() - interval '2 hours');

INSERT INTO order_items (order_id, producto, cantidad, precio_unitario) VALUES
    (1, 'Laptop 14"', 1, 549.99),
    (1, 'Mouse inalambrico', 1, 15.99),
    (1, 'Webcam HD', 1, 29.99),
    (2, 'Audifonos bluetooth', 1, 45.50),
    (3, 'Monitor 24"', 1, 189.50);

UPDATE inventory SET cantidad = cantidad - 1 WHERE producto = 'Laptop 14"';
UPDATE inventory SET cantidad = cantidad - 1 WHERE producto = 'Mouse inalambrico';
UPDATE inventory SET cantidad = cantidad - 1 WHERE producto = 'Webcam HD';
UPDATE inventory SET cantidad = cantidad - 1 WHERE producto = 'Audifonos bluetooth';
