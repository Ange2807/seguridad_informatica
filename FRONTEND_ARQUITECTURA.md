# Arquitectura del Sistema: Frontend TUI y Backend API

Este documento detalla la lógica, estructura y flujo de datos del proyecto, haciendo especial énfasis en el **Frontend (Terminal User Interface)**, diseñado para ser altamente modular, asíncrono y reactivo, y finalizando con un resumen de la infraestructura del Backend.

---

## 🎨 Arquitectura del Frontend (Python + Textual)

El frontend está desarrollado completamente en Python utilizando **Textual**, un framework moderno para crear aplicaciones de terminal asíncronas (TUI) impulsado por `asyncio`. Esto permite que la interfaz sea fluida y no se quede "congelada" mientras espera respuestas del servidor.

### 1. Núcleo de la Aplicación (`app.py`)
Es el punto de entrada principal. Define la clase `OnlineStoreApp` que hereda de `App`.
- **Enrutamiento:** Maneja el sistema de navegación basado en **Pantallas (Screens)**. Inicia empujando la pantalla de Login (`push_screen(LoginScreen)`).
- **Inyección de Dependencias:** Instancia el cliente de la API (`ApiClient`) de forma global para que todas las pantallas compartan la misma sesión y el mismo token de autenticación (estado global).
- **Estilos:** Carga el archivo central de CSS (`theme.tcss`).

### 2. Cliente de API (`api.py`)
Es el "cerebro" de las comunicaciones. Utiliza la librería **`httpx`** para realizar peticiones HTTP de forma asíncrona.
- **Gestión de Estado:** Almacena el `token` JWT, el `role` y el `username` del usuario logueado.
- **Autenticación:** Posee métodos separados para el registro y login de invitados (`guest_login`) y del personal de la empresa (`staff_login`).
- **CRUD Genérico:** En lugar de crear métodos repetitivos para cada departamento, abstrae la lógica en métodos genéricos: `get_records(dept)`, `create_record(dept, data)`, `update_record(dept, id, data)`, `delete_record(dept, id)`. A estos métodos simplemente se les inyecta por parámetro a qué departamento (`"inventario"`, `"rrhh"`, etc.) se le quiere hacer la petición.
- **Inyección de Tokens:** Intercepta automáticamente las peticiones privadas a través del método `_auth_headers()` para adjuntar el token JWT como `Bearer Token`.

### 3. Pantallas de la Interfaz (`screens/`)

La interfaz está dividida lógicamente en pantallas que representan el flujo de la aplicación.

#### A. Pantalla de Login (`login.py`)
- Utiliza un sistema de pestañas (`TabbedContent`) para separar el inicio de sesión de invitados (clientes) y del personal (Staff).
- Implementa validaciones básicas en el cliente antes de enviar la petición.
- **Enrutamiento dinámico:** Si la petición de login es exitosa, decide el flujo: si el usuario es un cliente, navega a `CatalogScreen`. Si es empleado, navega a `StaffScreen`.

#### B. Panel de Control del Staff (`staff.py`)
Es la pantalla más compleja, estructurada modularmente para soportar control de acceso basado en roles (RBAC):
- **Generación Dinámica de Pestañas:** Lee el `role` del `ApiClient`. Si el rol es `inventario`, solo instancia y añade la pestaña de inventario. Si el rol es `administrador`, inyecta todas las pestañas.
- **Clase Base `BaseDeptTab`:** Todos los departamentos (Atención, Inventario, RRHH) heredan de una clase base que estandariza cómo se carga la tabla de datos (`DataTable`) llamando al CRUD genérico de la API.
- **Auto-rellenado (Auto-fill):** Captura el evento `DataTable.RowSelected`. Cuando el usuario hace clic o presiona Enter en una fila, intercepta los datos de la tabla e inyecta automáticamente esa información en los `Input` (cuadros de texto) correspondientes.
- **Manejo de Formularios:** Los botones interceptan el evento de presión (`on_button_pressed`), construyen un diccionario `data` leyendo los inputs de Textual, validan localmente, e invocan asíncronamente a `api.py`.

#### C. Catálogo de Clientes (`catalog.py`)
- Muestra los productos públicos mediante un `DataTable`.
- Implementa un **Carrito de Compras** en memoria. Al seleccionar productos de la tabla, los añade al panel lateral.
- El botón de *Checkout* compila la lista y se la envía a la API (`checkout`), la cual realiza la transacción real de descuento de stock.

#### D. Historial de Pedidos (`orders.py`)
- Una vista exclusiva para los clientes invitados que consulta el endpoint `/api/public/orders/mine`. Extrae la identidad del cliente directamente del Token JWT enviado.

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
   - **Transacciones Seguras:** Para la compra (Checkout), utiliza transacciones de base de datos (`BEGIN...COMMIT`) garantizando que no se cobre el total si no hay suficiente stock en `inventory`, haciendo todo en una sola operación atómica.
