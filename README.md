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
             ├── /            → online-platform (estático: HTML/CSS/JS del front)
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
| V-00000001 | Ana Gomez | atencion | sí, vía LDAP |
| V-00000002 | Carlos Perez | rrhh | sí, vía LDAP |
| V-00000003 | Maria Lopez | inventario | sí, vía LDAP |
| V-00000004 | Admin Principal | administrador | no — regístrate tú |
| V-00000005 | Jorge Diaz | inventario | no — regístrate tú |
| V-00000006 | Lucia Fernandez | atencion | no — regístrate tú |

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

Cada app de departamento (Textual) y la plataforma pública tienen operaciones completas, no
solo lectura:

- **Inventario** (app de terminal): buscar (`r` limpia el filtro, Enter en el campo de búsqueda
  filtra), **crear** (`n`), **editar** (`e`) y **eliminar** (`d`), todo contra `proxy2` con
  permisos `read:inventario` / `write:inventario`.
- **RRHH** (app de terminal): buscar, **crear** (`n`) y **editar** (`e`) empleados (cédula,
  nombre, cargo) — sin `eliminar` (ver la nota de por qué en la sección de autenticación).
- **Atención al Cliente** (app de terminal, dos pestañas):
  - **Tickets**: mismo CRUD completo que los demás departamentos.
  - **Pedidos**: ve todos los pedidos de la tienda (con sus items) y puede **cambiar el estado**
    (`pendiente → procesando → enviado → entregado → cancelado`) con `e`. Los pedidos no se crean
    ni se eliminan manualmente — la API lo bloquea explícitamente (`POST`/`DELETE` a
    `/api/pedidos` devuelven 400).
- **Plataforma pública**: catálogo con buscador, carrito de compra (en el navegador),
  **checkout real** (descuenta stock dentro de una transacción SQL, valida existencias) y una
  sección **"Mis pedidos"** con el historial del cliente (items, total, estado — se actualiza
  cuando Atención cambia el estado).
- `inventory` tiene columna `precio`; `orders`/`order_items` registran cada compra.

Con esto el ciclo completo de una tienda queda cerrado: el cliente compra en la web → el pedido
aparece en la cola de Atención → Atención actualiza el estado → el cliente lo ve reflejado en su
historial.

## Levantar el proyecto

```powershell
cd back
docker compose up --build -d
```

- Plataforma pública: https://localhost (certificado autofirmado, el navegador dará aviso).
- Apps de departamento (sin puertos publicados). Usa el comando que corresponda a tu departamento:

```powershell
# Aplicación Unificada (Menú)
docker attach back-online-tui-1

# O directo a los departamentos:
docker attach back-atencion-1
docker attach back-rrhh-1
docker attach back-inventario-1
```

En la pantalla de login de cualquiera de las tres, el botón **"Registrarme"** pide cédula +
usuario + contraseña — solo funciona si esa cédula ya está en el roster de `employees` (ver
tabla arriba). Dentro de cada app: `n` nuevo registro, `e` editar el seleccionado, `d` eliminar
(no disponible en RRHH), `r` refrescar/limpiar búsqueda. En Atención, `Tab`/clic cambia entre las
pestañas Tickets y Pedidos. Para salir sin matar el contenedor: `Ctrl+P` seguido de `Ctrl+Q`.

> Nota: las cuentas de invitado (`proxy2/src/users.json`) viven dentro del contenedor y
> **se pierden si reconstruyes `proxy2`** (no hay volumen para ese archivo). Si acabas de
> reconstruir, vuelve a registrarte antes de probar el checkout o "Mis pedidos".

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
online-platform/     front web estático (sin lógica de API)
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
| GET | `/api/public/catalog?q=` | público, sin login |
| POST | `/api/public/orders` | invitado con `checkout` (checkout real) |
| GET | `/api/public/orders/mine` | invitado — su propio historial |
| GET/POST/PUT | `/api/:departamento` (+ `?q=` búsqueda) | personal, según `read:`/`write:` |
| DELETE | `/api/:departamento/:id` | igual, excepto `pedidos` y `rrhh` (bloqueados) |
| GET/PUT | `/api/pedidos` | rol `atencion` o `administrador` — ver y cambiar estado |

`POST /auth/login` (bind LDAP) no pasa por `proxy1`; solo lo usan las apps de departamento,
que hablan con `proxy2` directo por `net-gateway`.
