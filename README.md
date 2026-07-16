# Proyecto #2 — Red por departamentos (Docker)

Diseño de una red segmentada por departamentos, con una plataforma online pública, apps
internas de terminal, y una zona de servidores (OpenLDAP + PostgreSQL) totalmente aislada.

Tres diagramas:
- [`docs/diagrama-red.excalidraw`](docs/diagrama-red.excalidraw) — topología de red, zonas y particiones de IP.
- [`docs/diagrama-funcionamiento.excalidraw`](docs/diagrama-funcionamiento.excalidraw) — cómo fluye una petición, autenticación (LDAP / cédula / invitado), endpoints reales.
- [`docs/diagrama-guia-uso.excalidraw`](docs/diagrama-guia-uso.excalidraw) — guía práctica: cómo correrlo, tabla de roles y qué puede hacer cada uno, paso a paso para probarlo.

(Ábrelos en [excalidraw.com](https://excalidraw.com) o con la extensión de VS Code.)

## Arquitectura

```
Internet → proxy1 (DMZ, único puerto :443)
             ├── /            → online-platform (estático: build de React servido por Express)
             └── /api/        → proxy2 (directo — mismo proxy1 habla con proxy2)
                                       ├── OpenLDAP (personal, roles)
                                       └── PostgreSQL (datos por departamento)
atención / rrhh / inventario (Python + Textual, cada uno en su propia red) → net-gateway → proxy2
```

- **Único puerto expuesto al host:** `443` en `proxy1`. Ningún otro servicio publica puertos.
- **Los dos proxies se hablan directamente:** toda petición del navegador llega primero a
  `proxy1`. Si es `/api/*`, nginx la reenvía tal cual a `proxy2:4000` (mismo path) y la respuesta
  vuelve por el mismo camino — `proxy1` no reescribe ni reprocesa el cuerpo. Si es cualquier otra
  ruta, se sirve el sitio estático desde `online-platform`. `online-platform` ya **no** contiene
  lógica de negocio ni le habla a `proxy2` — es un servidor de archivos estáticos puro.
- **Departamentos aislados entre sí:** cada uno vive en su propia red Docker
  (`net-atencion`, `net-rrhh`, `net-inventario`) y solo puede llegar a `proxy2` vía `net-gateway`.
- **Zona de servidores aislada:** `net-servers` es `internal: true`; solo `proxy2` la puentea.
  Ni OpenLDAP ni PostgreSQL tienen salida a Internet — ni siquiera `proxy1` puede alcanzarlos
  directamente (está en `net-dmz` + `net-online` + `net-gateway`, nunca en `net-servers`).
- **Acceso del personal:** las apps de departamento no exponen puertos. Se usan con
  `docker attach <contenedor>` (o SSH al host).

## Autenticación y autorización

Tres mecanismos conviven, los tres emiten el mismo tipo de JWT (`{ sub, role }`) y por eso
`roles.json` los autoriza de forma idéntica sin que a `proxy2` le importe cuál usaste:

- **Personal ya existente (LDAP)** → `proxy2` hace *bind* contra OpenLDAP (usuario + contraseña)
  y resuelve el rol a partir del grupo LDAP al que pertenece (`ou=groups`). Ruta: `POST /auth/login`.
- **Personal nuevo, auto-registro por cédula** → cualquiera puede crear su propia cuenta desde el
  botón "Registrarme" en el login de cualquier app de departamento, pero **solo si su cédula ya
  fue cargada por RRHH o un Administrador** en la tabla `employees`. El rol se asigna
  automáticamente según el `cargo` de esa fila — nadie elige su propio rol. Rutas:
  `POST /api/staff/register` (cédula + usuario + contraseña) y `POST /api/staff/login`.
  Este es un camino **paralelo** a LDAP, no lo reemplaza: ana/carlos/maria siguen entrando por
  LDAP; el personal nuevo entra por aquí.
- **Invitados externos (opcional)** → `proxy2` valida contra un `users.json` local
  (`{ id, user_na, user_pw, roles }`) en `POST /api/guest/register` y `/api/guest/login`, sin
  tocar LDAP ni la tabla de empleados.
- **Permisos por rol** → `roles.json` (`{ RoleName: { permissions: [...] } }`), consultado por
  `proxy2` para autorizar cada petición.

Usuarios semilla en OpenLDAP (contraseña `Password123`, entran por `/auth/login`):

| usuario | grupo / rol  |
|---------|--------------|
| ana     | atencion     |
| carlos  | rrhh         |
| maria   | inventario   |

Roster semilla en `employees` (cédula → cargo). ana/carlos/maria ya están cargadas por
consistencia, pero siguen usando LDAP. Las últimas tres **no tienen cuenta todavía** — sirven
para probar el auto-registro:

| cédula | nombre | cargo | ¿ya tiene cuenta? |
|---|---|---|---|
| 00000001 | Ana Gomez | atencion | sí, vía LDAP |
| 00000002 | Carlos Perez | rrhh | sí, vía LDAP |
| 00000003 | Maria Lopez | inventario | sí, vía LDAP |
| 00000004 | Admin Principal | administrador | no — regístrate tú |
| 00000005 | Jorge Diaz | inventario | no — regístrate tú |
| 00000006 | Lucia Fernandez | atencion | no — regístrate tú |

**Rol `administrador`**: superusuario — lectura y escritura en atención, rrhh, inventario y
pedidos, además de poder cargar empleados igual que RRHH. No existe una app propia para
administrador: usa el mismo botón "Registrarme"/"Iniciar sesión" en cualquiera de las 3 apps de
departamento (el rol viaja en el token, no depende del contenedor al que te conectaste) — para
gestionar empleados entra a la app de `rrhh`.

**RRHH y Administrador** son los únicos con `write:rrhh`: pueden **crear** empleados (cédula,
nombre, cargo) y **editar** cargo/nombre si alguien cambia de puesto. **No pueden eliminar**
empleados desde la app — `DELETE /api/rrhh/:id` está bloqueado a propósito, porque borrar un
empleado rompería la cuenta ya vinculada a esa cédula (`staff_accounts.cedula` referencia
`employees.cedula`). Si de verdad hay que dar de baja a alguien, se cambia su `cargo` o se hace
directo en la base de datos — no desde la UI.

## Funcionalidades de tienda por departamentos

Hay dos superficies de terminal distintas y ambas hablan con el mismo `proxy2`:

- **Apps de departamento fijas** (`apps/atencion`, `apps/rrhh`, `apps/inventario` — un
  contenedor por departamento, sin selector de rol):
  - **Inventario**: buscar (`r` limpia el filtro, Enter en el campo de búsqueda filtra),
    **crear** (`n`), **editar** (`e`) y **eliminar** (`d`).
  - **RRHH**: buscar, **crear** (`n`) y **editar** (`e`) empleados (cédula, nombre, cargo) — sin
    `eliminar` (ver la nota de por qué en la sección de autenticación).
  - **Atención al Cliente** (dos pestañas): **Tickets** (CRUD completo) y **Pedidos** (ver todos
    los pedidos con sus items y **cambiar el estado** con `e`; no se crean ni eliminan
    manualmente desde aquí).
- **`online-tui`** (un solo contenedor, login único — LDAP o cuenta auto-registrada — y menú
  según el rol del token):
  - **Atención/Administrador** → pestaña **Nuevo Pedido**: mira el mismo catálogo público,
    agrega productos con cantidad y confirma el pedido dando **nombre y cédula del comprador**
    (sin cobro, el comprador no necesita cuenta); y pestaña **Pedidos** para cambiar el estado.
  - **Inventario/Administrador** → crear, editar (incluye **precio** y **disponible**) y
    eliminar productos. Un producto marcado `disponible = false` desaparece del catálogo público
    y de la pestaña Nuevo Pedido, aunque siga existiendo en el inventario.
  - **RRHH/Administrador** → registrar y listar empleados (cédula, nombre, cargo).
  - **Administrador** ve las cuatro pestañas a la vez.
- **Plataforma pública** (app React en `online-platform/client/`): catálogo de precios de solo
  lectura con buscador, sin carrito ni cuentas de invitado — comprar es siempre a través de
  Atención en `online-tui`.
- `inventory` tiene columnas `precio` y `disponible`; `orders`/`order_items` registran cada
  pedido, ya sea del checkout de invitado (histórico, sin frontend activo hoy) o creado por
  Atención (`cliente_nombre` + `cliente_cedula`).

Con esto el ciclo de una compra queda: el comprador se acerca/llama → Atención arma el pedido en
`online-tui` con su nombre y cédula → el pedido aparece en la pestaña Pedidos (de Atención o de la
app fija de Atención) → se actualiza el estado según avanza.

## Levantar el proyecto

```powershell
docker compose up --build -d
```

- Plataforma pública: https://localhost (certificado autofirmado, el navegador dará aviso).
- Apps de departamento (sin puertos publicados):

```powershell
docker attach back-online-tui-1
```

En la pantalla de login de cualquiera de las tres, el botón **"Registrarme"** pide cédula +
usuario + contraseña — solo funciona si esa cédula ya está en el roster de `employees` (ver
tabla arriba). Dentro de cada app: `n` nuevo registro, `e` editar el seleccionado, `d` eliminar
(no disponible en RRHH), `r` refrescar/limpiar búsqueda. En Atención, `Tab`/clic cambia entre las
pestañas Tickets y Pedidos. Para salir sin matar el contenedor: `Ctrl+P` seguido de `Ctrl+Q`.

> Nota: las cuentas de invitado (`proxy2/src/users.json`) viven dentro del contenedor y
> **se pierden si reconstruyes `proxy2`** (no hay volumen para ese archivo). Si acabas de
> reconstruir, vuelve a registrarte antes de probar el checkout o "Mis pedidos".

> Nota: `db/init.sql` solo corre la primera vez que se crea el volumen `db-data`. Si ya tenías
> el proyecto levantado antes de las columnas `disponible` (inventory) y `cliente_nombre`/
> `cliente_cedula` (orders), necesitas recrear el volumen para verlas:
> `docker compose down -v && docker compose up --build -d` (esto borra los datos actuales de
> Postgres y los vuelve a sembrar).

## Notas de despliegue

Este proyecto fue probado de punta a punta con `docker compose up --build -d` en Docker Desktop
para Windows. Dos ajustes que hicieron falta frente al diseño original:

- `net-servers` usa `172.20.0.0/24` (no `172.17.0.0/24` como en el boceto original) porque esa
  red choca con la red `bridge` por defecto de Docker.
- OpenLDAP corre en `bitnamilegacy/openldap:2.6.10-debian-12-r4` (puerto interno `1389`, no
  `389`) — la imagen `osixia/openldap` tiene un bug de arranque no relacionado con este proyecto.

## Variables de entorno

Configurables por `.env` (opcional): `JWT_SECRET`, `LDAP_ADMIN_PASSWORD`, `DB_PASSWORD`.
Si no se definen, se usan valores por defecto de desarrollo — **cámbialos antes de cualquier
uso real**.

## Estructura

```
docker-compose.yml
docs/diagrama-red.excalidraw
docs/diagrama-funcionamiento.excalidraw
docs/diagrama-guia-uso.excalidraw
proxy1/             nginx — único punto público, reenvía / a online-platform y /api/ a proxy2
proxy2/              gateway único: auth LDAP + auto-registro por cédula + invitados (JSON) + BD
online-platform/     catálogo web en React (client/), servido como estático por Express — sin lógica de API
apps/atencion/       Python + Textual — terminal, red aislada
apps/rrhh/           Python + Textual — terminal, red aislada
apps/inventario/     Python + Textual — terminal, red aislada
openldap/bootstrap/  usuarios y grupos semilla (LDIF)
db/init.sql          esquema y datos semilla de PostgreSQL
```

## Endpoints de proxy2 (accesibles vía `https://localhost/api/...` a través de proxy1)

| Método | Ruta | Quién |
|---|---|---|
| POST | `/api/staff/register` | cualquiera — requiere cédula ya cargada por RRHH/Administrador |
| POST | `/api/staff/login` | personal auto-registrado (no-LDAP) |
| POST | `/api/guest/register`, `/api/guest/login` | invitados (JSON) |
| GET | `/api/public/catalog?q=` | público, sin login — solo productos con `disponible = true` |
| POST | `/api/public/orders` | invitado con `checkout` (histórico, sin frontend activo hoy) |
| GET | `/api/public/orders/mine` | invitado — su propio historial |
| POST | `/api/pedidos` | rol `atencion`/`administrador` — crea el pedido con `{cliente_nombre, cliente_cedula, items}` |
| GET/PUT | `/api/pedidos` | rol `atencion` o `administrador` — ver y cambiar estado |
| GET/POST/PUT | `/api/:departamento` (+ `?q=` búsqueda) | personal, según `read:`/`write:` |
| DELETE | `/api/:departamento/:id` | igual, excepto `pedidos` y `rrhh` (bloqueados) |

`POST /auth/login` (bind LDAP) no pasa por `proxy1`; solo lo usan las apps de departamento,
que hablan con `proxy2` directo por `net-gateway`.

## Exposición del Frontend y Código Base

A continuación se detalla cómo se gestionan ambos frontends (Plataforma Web y Terminal TUI) y las porciones de código que sustentan su funcionamiento.

### 1. Plataforma Web (React - online-platform)
Es una aplicación **React** que actúa exclusivamente como un catálogo de **solo lectura**. Al no tener estado de usuario (sesión) y no tener formularios que modifiquen la base de datos, reduce drásticamente los riesgos de seguridad web.

**Código clave de consumo de API (`client/src/App.jsx`):**
```jsx
// useEffect se dispara cuando la aplicación carga o cuando el usuario busca ('query')
useEffect(() => {
  const fetchCatalog = async () => {
    // Si hay una búsqueda, se agrega el parámetro ?q= a la URL
    const qs = query ? `?q=${encodeURIComponent(query)}` : "";
    
    // El frontend pide los datos a proxy1 (Nginx), quien los rutea a proxy2 internamente.
    // Nunca toca la base de datos directamente.
    const res = await fetch(`/api/public/catalog${qs}`);
    if (res.ok) {
      const data = await res.json();
      setProducts(data); // Se guardan los productos en el estado de React
    }
  };
  fetchCatalog();
}, [query]);

// Al renderizar la información, React usa llaves {} que previenen ataques XSS (Cross-Site Scripting)
// escapando automáticamente cualquier inyección de código.
<p>{product.producto}</p>
```

### 2. Terminal de Empleados (Python TUI)
Aplicación de consola usando la librería **Textual**. Es asíncrona, conectándose al backend mediante la librería `httpx`. Mantiene su seguridad mediante dos estrategias: **almacenamiento de credenciales en memoria** y **delegación de autorización al backend**.

**Manejo seguro de credenciales (`front/api.py`):**
```python
class ApiClient:
    def __init__(self):
        # El token JWT NO se guarda en disco duro ni bases de datos locales.
        # Solo existe en la memoria RAM de esta instancia.
        self.token: str | None = None
        self.role: str | None = None

    def _auth_headers(self) -> dict:
        # Este método inyecta automáticamente el token en CADA petición.
        # Evita descuidos de programadores que podrían exponer tokens en URLs.
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}
        
    def logout(self):
        # Al hacer logout, se purgan las credenciales de la memoria.
        self.token = None
        self.role = None
```

**Adaptación Visual según Rol (`front/screens/staff.py`):**
```python
class StaffScreen(Screen):
    def on_mount(self) -> None:
        # Se lee el rol del usuario (guardado en la RAM por ApiClient)
        role = self.app.api.role
        
        # El frontend usa esta lógica visual para NO molestar al usuario con 
        # opciones prohibidas (Ocultando pestañas, botones, etc).
        if role in ("atencion", "administrador"):
            self.query_one(TabbedContent).add_pane(NuevoPedidoTab())
            self.query_one(TabbedContent).add_pane(PedidosTab())
            
        if role in ("inventario", "administrador"):
            self.query_one(TabbedContent).add_pane(InventarioTab())
            
        # IMPORTANTE: Si un atacante modificara este archivo Python para
        # saltarse estos 'if' y ver la pestaña de "Inventario", NO podría 
        # crear ni borrar productos, porque al enviar la petición al servidor,
        # Proxy2 leería su firma criptográfica JWT y lo detendría (Error 403).
```
