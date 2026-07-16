# Defensa Arquitectónica de Seguridad: Frontend

Esta guía presenta la estrategia de defensa secuencial implementada en las interfaces del sistema: **La Plataforma Pública (React)** y **La Terminal Interna (TUI en Python)**. El enfoque está estructurado para justificar cada decisión técnica desde una perspectiva de ciberseguridad.

---

## 1. El Principio Base: "Zero Trust" en el Cliente

El principio fundamental aplicado al diseño de ambos frontends es que **el cliente nunca es confiable**. Un atacante tiene control total sobre su navegador o su entorno local, por lo que el frontend actúa *exclusivamente* como una capa de presentación. Toda validación visual es para mejorar la Experiencia de Usuario (UX), mientras que la verdadera barrera (Control de Acceso, Validación de Negocio, etc.) recae en la API.

---

## 2. Defensa de la Web Pública (React - Invitados)

La plataforma pública está expuesta a internet, por lo que su diseño se basa en **minimizar la superficie de ataque**.

### A. Ausencia de Estado Sensible (Stateless Frontend)
Se ha retirado cualquier funcionalidad de inicio de sesión o carrito interactivo de la vista pública. El frontend simplemente hace una petición `GET` al catálogo público. Al no manejar autenticación, **no hay tokens JWT ni cookies de sesión en el navegador** que puedan ser robados (XSS) o suplantados (CSRF).

### B. Mitigación de Cross-Site Scripting (XSS)
React neutraliza inherentemente los ataques XSS mediante el *data binding*. Cualquier dato que provenga del backend (por ejemplo, nombres de productos alterados) es escapado antes de inyectarse en el DOM.

```jsx
// En el componente de React, las llaves {} sanitizan automáticamente el texto
<h3>{producto.nombre}</h3> // Si el nombre trae un <script>, se renderiza como texto plano.
```

---

## 3. Defensa de la Terminal de Empleados (Python Textual TUI)

La TUI es utilizada por el personal interno para operaciones críticas. Sus defensas se basan en la **volatilidad de las credenciales** y el **aislamiento de red**.

### A. Almacenamiento en Memoria Volátil (RAM)
Nunca se almacena el Token JWT en el disco duro (archivos, base de datos local, logs). Las credenciales viven exclusivamente en la memoria RAM de la instancia en tiempo de ejecución. Al cerrar la app, el sistema operativo libera la memoria, destruyendo el token.

```python
# Archivo: front/api.py
class ApiClient:
    def __init__(self):
        # El estado de autenticación nace vacío y solo vive en memoria
        self.token: str | None = None
        self.role: str | None = None

    def logout(self):
        # Destrucción explícita de credenciales en RAM
        self.token = None
        self.role = None
```

### B. Aislamiento de Red Interna (Docker Networks)
La TUI no se conecta al proxy público expuesto a internet. Se comunica directamente con la API a través de la red privada de Docker, evitando vectores de ataque *Man-In-The-Middle* (MITM) desde redes públicas.

```python
# Archivo: front/api.py
# El tráfico viaja internamente a proxy2 sin salir a internet
BASE_URL = os.environ.get("PROXY2_URL", "http://localhost:4000")
```

### C. Inyección Automatizada y Transparente de Headers
Para prevenir descuidos (ej. enviar el token en la URL, lo cual queda en los logs del servidor), el cliente API intercepta todas las peticiones protegidas y adjunta el token en la cabecera HTTP `Authorization: Bearer <token>` de forma centralizada.

```python
# Archivo: front/api.py
def _auth_headers(self) -> dict:
    if self.token:
        # El token siempre viaja en la cabecera estándar de autorización
        return {"Authorization": f"Bearer {self.token}"}
    return {}

async def get_records(self, department: str, query: str = ""):
    # Uso automático de las cabeceras protegidas
    r = await c.get(f"/api/{department}", headers=self._auth_headers())
```

### D. Seguridad por Oscuridad (UI) vs Seguridad Real (API)
El frontend lee el `self.role` del usuario y adapta la interfaz para ocultar pestañas a las que no tiene acceso (por ejemplo, ocultando "Recursos Humanos" a alguien de "Inventario"). 
Si un empleado alterase el código Python localmente para forzar la visualización del panel de RRHH, **el backend detendría cualquier acción**, porque el `hasPermission` del Proxy2 examinará la firma criptográfica del JWT y devolverá `403 Forbidden`. La UI solo oculta lo que la API ya protege.
