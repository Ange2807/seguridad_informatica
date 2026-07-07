# Proyecto #2 — Red por departamentos (Docker)

Diseño de una red segmentada por departamentos, con una plataforma online pública, apps
internas de terminal, y una zona de servidores (OpenLDAP + PostgreSQL) totalmente aislada.

El diagrama completo está en [`docs/diagrama-red.excalidraw`](docs/diagrama-red.excalidraw)
(ábrelo en [excalidraw.com](https://excalidraw.com) o con la extensión de VS Code).

## Arquitectura

```
Internet → proxy1 (DMZ, único puerto :443)
             └── online-platform (público, cuentas invitado vía JSON)
                      └── net-gateway
atención / rrhh / inventario (Python + Textual, cada uno en su propia red) ──┘
                      └── proxy2 (único bridge autorizado)
                               ├── OpenLDAP (personal, roles)
                               └── PostgreSQL (datos por departamento)
```

- **Único puerto expuesto al host:** `443` en `proxy1`. Ningún otro servicio publica puertos.
- **Departamentos aislados entre sí:** cada uno vive en su propia red Docker
  (`net-atencion`, `net-rrhh`, `net-inventario`) y solo puede llegar a `proxy2` vía `net-gateway`.
- **Zona de servidores aislada:** `net-servers` es `internal: true`; solo `proxy2` la puentea.
  Ni OpenLDAP ni PostgreSQL tienen salida a Internet.
- **Acceso del personal:** las apps de departamento no exponen puertos. Se usan con
  `docker attach <contenedor>` (o SSH al host).

## Autenticación y autorización

- **Personal interno** → `proxy2` hace *bind* contra OpenLDAP (usuario + contraseña) y resuelve
  el rol a partir del grupo LDAP al que pertenece (`ou=groups`).
- **Invitados externos (opcional)** → `online-platform` valida contra un `users.json` local
  (`{ id, user_na, user_pw, roles }`), sin tocar LDAP.
- **Permisos por rol** → `roles.json` (`{ RoleName: { permissions: [...] } }`), consultado por
  `proxy2` para autorizar cada petición, sin importar si el token vino de LDAP o del registro
  de invitado.

Usuarios semilla en OpenLDAP (contraseña `Password123`):

| usuario | grupo / rol  |
|---------|--------------|
| ana     | atencion     |
| carlos  | rrhh         |
| maria   | inventario   |

## Funcionalidades de tienda por departamentos

Cada app de departamento (Textual) y la plataforma pública tienen operaciones completas, no
solo lectura:

- **Inventario / RRHH** (apps de terminal): buscar (`r` limpia el filtro, Enter en el campo de
  búsqueda filtra), **crear** (`n`), **editar** (`e` sobre la fila seleccionada) y **eliminar**
  (`d`), todo contra `proxy2` con permisos `read:<depto>` / `write:<depto>`.
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
docker compose up --build -d
```

- Plataforma pública: https://localhost (certificado autofirmado, el navegador dará aviso).
- Apps de departamento (sin puertos publicados):

```powershell
docker attach seguridad_informatica-atencion-1
docker attach seguridad_informatica-rrhh-1
docker attach seguridad_informatica-inventario-1
```

Dentro de cada app: `n` nuevo registro, `e` editar el seleccionado, `d` eliminar, `r` refrescar/limpiar
búsqueda. En Atención, `Tab`/clic cambia entre las pestañas Tickets y Pedidos. Para salir sin matar
el contenedor: `Ctrl+P` seguido de `Ctrl+Q`.

> Nota: las cuentas de invitado (`online-platform/src/users.json`) viven dentro del contenedor y
> **se pierden si reconstruyes `online-platform`** (no hay volumen para ese archivo). Si acabas de
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
proxy1/            nginx, único punto público
proxy2/             gateway interno: auth LDAP + acceso a BD
online-platform/    front web público + cuentas invitado (JSON)
apps/atencion/      Python + Textual — terminal, red aislada
apps/rrhh/          Python + Textual — terminal, red aislada
apps/inventario/    Python + Textual — terminal, red aislada
openldap/bootstrap/ usuarios y grupos semilla (LDIF)
db/init.sql         esquema y datos semilla de PostgreSQL
```
