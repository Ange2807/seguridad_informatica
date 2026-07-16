# Guía Sencilla de Seguridad del Backend

A diferencia del frontend, el backend es donde ocurre la **verdadera defensa** del sistema. Aquí es donde se protegen los datos y se decide quién entra y qué puede hacer. Todo el sistema está diseñado como una "fortaleza con anillos de seguridad".

Aquí te explico las 5 defensas principales de forma muy sencilla:

---

## 1. Un solo guardia en la puerta (API Gateway)
Nadie puede llegar a la base de datos directamente. Todas las peticiones del mundo exterior tienen que pasar obligatoriamente por dos puntos de control:
* **Proxy1 (Nginx):** Obliga a que toda la comunicación sea cifrada (candadito verde / HTTPS) para que nadie pueda espiar los datos en el cable.
* **Proxy2 (El Cerebro):** Es el único que recibe peticiones, las analiza y decide si las deja pasar o las bloquea.

## 2. Contraseñas Irreconocibles (Bcrypt y LDAP)
El sistema nunca guarda las contraseñas en "texto plano". 
* Para los empleados más nuevos (que se registran con su cédula), sus contraseñas se pasan por un algoritmo matemático llamado **Bcrypt**. Esto las convierte en texto incomprensible (ej. `$2a$10$tG3x...`). Si un hacker roba la base de datos, no podrá saber cuáles son las contraseñas reales.
* Los empleados antiguos usan **LDAP**, un directorio corporativo externo que maneja la seguridad por su cuenta.

## 3. Pases de Invitado In-falsificables (JWT)
Cuando un empleado inicia sesión correctamente, el servidor no se queda recordando quién es; en su lugar, le da un **Pase Digital (Token JWT)**. 
* Este pase tiene un sello de seguridad criptográfico (una firma). 
* Si un hacker intenta modificar su pase para decir "Soy el Administrador", el sello se rompe y el servidor (Proxy2) lo rechaza inmediatamente.

## 4. Control de Permisos Estricto (RBAC)
No basta con estar adentro, el backend verifica qué puedes hacer paso por paso:
* Si un empleado de Recursos Humanos (RRHH) intenta enviar una orden para borrar un producto del inventario, el backend revisa su rol. 
* Al ver que no coincide con los permisos requeridos para esa acción, el backend **corta la operación de inmediato (Error 403 Prohibido)**, antes siquiera de preguntar a la base de datos.

## 5. La Bóveda Aislada (Redes de Docker)
Los tesoros del sistema (La Base de Datos PostgreSQL y el servidor LDAP) viven en un **cuarto sin ventanas hacia el exterior** (una red interna de Docker llamada `net-servers`).
* No tienen puerto público de internet. 
* Literalmente, la única computadora en todo el ecosistema que puede hablar con la base de datos es el Proxy2. Cualquier ataque externo chocaría primero contra los Proxies sin poder "ver" que existe una base de datos detrás.
