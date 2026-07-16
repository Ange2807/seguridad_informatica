# Arquitectura del Sistema: Frontend TUI y Backend API

Este documento detalla la lógica, estructura y flujo de datos del proyecto, haciendo especial énfasis en el **Frontend (Terminal User Interface)**, diseñado para ser altamente modular, asíncrono y reactivo, y finalizando con un resumen de la infraestructura del Backend.

---

## 🎨 Arquitectura del Frontend (Python + Textual)

El frontend está desarrollado completamente en Python utilizando **Textual**, un framework moderno para crear aplicaciones de terminal asíncronas (TUI) impulsado por `asyncio`. Esto permite que la interfaz sea fluida y no se quede "congelada" mientras espera respuestas del servidor.

`front/` (servicio `online-tui`) es una app **exclusiva de personal**: login único (LDAP o
cuenta auto-registrada) y un panel con pestañas que cambian según el `role` que viene en el JWT.
No hay pantalla de catálogo/carrito para clientes finales aquí — comprar para un cliente sin
cuenta es una de las pestañas del panel de staff (ver más abajo).

### 1. Núcleo de la Aplicación (`app.py`)
Es el punto de entrada principal. Define la clase `SecureCorpApp` que hereda de `App`.
- **Enrutamiento:** Maneja el sistema de navegación basado en **Pantallas (Screens)**. Inicia empujando la pantalla de Login (`push_screen(LoginScreen)`).
- **Inyección de Dependencias:** Instancia el cliente de la API (`ApiClient`) de forma global para que todas las pantallas compartan la misma sesión y el mismo token de autenticación (estado global).
- **Estilos:** Carga el archivo central de CSS (`theme.tcss`).
- **Funciones Principales:**
  - `on_mount()`: Inicia la app mostrando la pantalla de login.
  - `show_staff()`, `show_login()`: Controlan la navegación entre pantallas.
  - `do_logout()`: Limpia los datos de sesión y redirige al login.

### 2. Cliente de API (`api.py`)
Es el "cerebro" de las comunicaciones. Utiliza la librería **`httpx`** para realizar peticiones HTTP de forma asíncrona.
- **Gestión de Estado:** Almacena el `token` JWT, el `role`, el `username` y el `nombre` del usuario logueado.
- **Autenticación de staff con fallback:** `staff_login()` intenta primero `/auth/login` (LDAP —
  cubre a ana/carlos/maria) y, si falla, cae a `/api/staff/login` (cuentas auto-registradas por
  cédula). Sin este fallback el personal LDAP no puede entrar y el menú por rol nunca llega a
  mostrarse — es el motivo por el que antes el menú "no cambiaba".
- **CRUD Genérico:** En lugar de crear métodos repetitivos para cada departamento, abstrae la lógica en métodos genéricos: `get_records(dept)`, `create_record(dept, data)`, `update_record(dept, id, data)`, `delete_record(dept, id)`. A estos métodos simplemente se les inyecta por parámetro a qué departamento (`"inventario"`, `"rrhh"`, `"pedidos"`, etc.) se le quiere hacer la petición.
- **Inyección de Tokens:** Intercepta automáticamente las peticiones privadas a través del método `_auth_headers()` para adjuntar el token JWT como `Bearer Token`.
- **Funciones Principales:**
  - `_auth_headers()`: Genera las cabeceras de autorización con JWT.
  - `staff_register()`, `staff_login()`: Manejan la autenticación de personal.
  - `get_catalog()`: Consulta el catálogo público (usado por la pestaña Nuevo Pedido de Atención).
  - `get_records()`, `create_record()`, `update_record()`, `delete_record()`: Métodos CRUD genéricos.
  - `logout()`: Borra el estado de la sesión localmente.

### 3. Pantallas de la Interfaz (`screens/`)

#### A. Pantalla de Login (`login.py`)
- Un único formulario de staff (usuario/contraseña) más el botón "Registrarse" (cédula + usuario + contraseña) para el auto-registro.
- Implementa validaciones básicas en el cliente antes de enviar la petición.
- Si el login es exitoso, siempre navega a `StaffScreen` — el rol dentro del token decide qué pestañas ve.
- **Funciones Principales:**
  - `compose()`: Dibuja la estructura visual (inputs, botones).
  - `on_button_pressed(event)`: Intercepta los clicks de "Ingresar" y "Registrarse", llama a `api.py` y ejecuta las redirecciones.

#### B. Panel de Control del Staff (`staff.py`)
Es la pantalla más compleja, estructurada modularmente para soportar control de acceso basado en roles (RBAC):
- **Generación Dinámica de Pestañas** (`StaffScreen.on_mount`): Lee el `role` del `ApiClient` y agrega solo las pestañas correspondientes:
  - `atencion` / `administrador` → **Nuevo Pedido** (`NuevoPedidoTab`) + **Pedidos** (`PedidosTab`)
  - `inventario` / `administrador` → **Inventario** (`InventarioTab`)
  - `rrhh` / `administrador` → **RRHH** (`RrhhTab`)
  - `administrador` acumula las cuatro pestañas.
- **Clase Base `BaseDeptTab`:** RRHH, Inventario y Pedidos (departamentos con tabla + formulario CRUD estándar) heredan de una clase base que estandariza cómo se carga el `DataTable` llamando al CRUD genérico de la API.
- **`NuevoPedidoTab` (no hereda de `BaseDeptTab`):** es el reemplazo de la antigua pestaña de Tickets. Muestra el mismo catálogo público (`get_catalog()`), deja armar un pedido en memoria (`cart`) agregando productos con cantidad, y al confirmar pide **nombre y cédula del comprador** (sin cuenta, sin cobro) y llama a `create_record("pedidos", {...})`, que en el backend valida stock y descuenta inventario igual que un checkout real.
- **`InventarioTab`:** además de producto/cantidad/precio/ubicación, incluye un `Select` de **disponible** (sí/no). Un producto no disponible desaparece del catálogo público y de `NuevoPedidoTab`, aunque sigue editable desde aquí.
- **Auto-rellenado (Auto-fill):** Captura el evento `DataTable.RowSelected` en las pestañas CRUD. Cuando el usuario hace clic o presiona Enter en una fila, intercepta los datos de la tabla e inyecta automáticamente esa información en los `Input`/`Select` correspondientes.
- **Funciones Principales:**
  - `compose()`: (en StaffScreen y cada Tab) Construye la UI con pestañas, tablas y formularios.
  - `on_mount() / _load_data()`: Determina permisos de usuario e inicializa el fetch de datos.
  - `populate_table()`: Llena el DataTable con los registros traídos.
  - `on_data_table_row_selected(event)`: Autocompleta los inputs del formulario al seleccionar una fila.
  - `on_button_pressed(event)`: Enruta cada botón (por prefijo de id: `btn-rrhh-`, `btn-inv-`, `btn-np-`, `btn-ped-`) a la acción correspondiente contra `api.py`.

### 4. Estilos y Layout (`styles/theme.tcss`)
El diseño visual está aislado en un archivo CSS compatible con Textual.
- Define una paleta de colores oscuros ("Dark Cyber Theme").
- Utiliza **Flexbox** (vía propiedades como `width: 1fr`) en contenedores como `.form-row` para asegurar que los inputs de edición se distribuyan equitativamente en la pantalla, evitando desbordamientos, de modo que toda la información quede visible.

---

## ⚙️ Resumen del Backend (Express + Postgres + LDAP)

El backend es el encargado de la persistencia y la seguridad criptográfica, diseñado como un único punto de entrada (Gateway):

1. **Proxy 2 (API Gateway en Node.js/Express):** 
   - Centraliza todas las peticiones.
   - **Autenticación LDAP / Local:** Puede validar usuarios internamente (invitados/registro por cédula) o conectarse mediante el protocolo LDAP a un servidor OpenLDAP para validar al personal heredado.
   - **Generación JWT:** Firma tokens con un *secret* y empaqueta el rol (`role`) del usuario en el token.
2. **Motor de Autorización (RBAC):**
   - Utiliza un middleware genérico `hasPermission(role, resource)`. Este middleware lee un archivo maestro de configuración (`roles.json`), verifica si el rol tiene el permiso solicitado (ej. `write:inventario`) y, de no ser así, corta la conexión devolviendo un `403 Forbidden`.
3. **Persistencia (PostgreSQL):**
   - El proxy se conecta a Postgres. Cada operación es validada contra un esquema predefinido en `db.js`.
   - **Transacciones Seguras:** tanto el checkout de invitado (`createOrder`) como el pedido creado por Atención (`createStaffOrder`, `POST /api/pedidos`) comparten la misma reserva de stock transaccional (`_reserveStock`): bloquean las filas de `inventory` (`FOR UPDATE`), verifican `disponible` y cantidad, y hacen `COMMIT`/`ROLLBACK` atómico. La única diferencia es a quién queda atado el pedido: `guest_username` para invitado, `cliente_nombre` + `cliente_cedula` para el que arma Atención.
