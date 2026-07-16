import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import express from "express";
import cors from "cors";
import jwt from "jsonwebtoken";
import { bindAsUser, findRole } from "./ldapAuth.js";
import { registerGuest, verifyGuest } from "./guestAuth.js";
import { registerStaff, verifyStaff } from "./staffAuth.js";
import * as db from "./db.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const roles = JSON.parse(fs.readFileSync(path.join(__dirname, "../roles.json"), "utf-8"));

const app = express();
app.use(cors());
app.use(express.json());

const JWT_SECRET = process.env.JWT_SECRET;

// Autentica usuarios LDAP, verifica su grupo y emite un JWT de sesión.
app.post("/auth/login", async (req, res) => {
  const { username, password } = req.body || {};
  if (!username || !password) {
    return res.status(400).json({ error: "username y password requeridos" });
  }
  try {
    await bindAsUser(username, password);
    const role = await findRole(username);
    if (!role) {
      return res.status(403).json({ error: "usuario sin departamento asignado" });
    }
    const token = jwt.sign({ sub: username, role }, JWT_SECRET, { expiresIn: "8h" });
    res.json({ token, role });
  } catch (err) {
    res.status(401).json({ error: "credenciales inválidas" });
  }
});

// Crea una cuenta de invitado en el almacenamiento local de proxy2.
app.post("/api/guest/register", async (req, res) => {
  const { username, password } = req.body || {};
  if (!username || !password) {
    return res.status(400).json({ error: "usuario y contraseña requeridos" });
  }
  try {
    await registerGuest(username, password);
    res.status(201).json({ ok: true });
  } catch (err) {
    res.status(409).json({ error: err.message });
  }
});

// Valida credenciales de invitado y devuelve un JWT para la plataforma pública.
app.post("/api/guest/login", async (req, res) => {
  const { username, password } = req.body || {};
  const user = await verifyGuest(username, password);
  if (!user) return res.status(401).json({ error: "credenciales inválidas" });
  const token = jwt.sign({ sub: user.user_na, role: user.roles[0] }, JWT_SECRET, {
    expiresIn: "4h",
  });
  res.json({ token });
});

// Registra una cuenta interna vinculada a una cédula ya cargada en la tabla employees.
app.post("/api/staff/register", async (req, res) => {
  const { cedula, username, password } = req.body || {};
  if (!cedula || !username || !password) {
    return res.status(400).json({ error: "cédula, usuario y contraseña requeridos" });
  }
  try {
    const employee = await registerStaff(cedula, username, password);
    res.status(201).json({ ok: true, nombre: employee.nombre, cargo: employee.cargo });
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// Inicia sesión de personal auto-registrado y devuelve un JWT con su cargo como rol.
app.post("/api/staff/login", async (req, res) => {
  const { username, password } = req.body || {};
  if (!username || !password) {
    return res.status(400).json({ error: "usuario y contraseña requeridos" });
  }
  const account = await verifyStaff(username, password);
  if (!account) return res.status(401).json({ error: "credenciales inválidas" });
  const token = jwt.sign({ sub: account.username, role: account.cargo }, JWT_SECRET, {
    expiresIn: "8h",
  });
  res.json({ token, role: account.cargo, nombre: account.nombre });
});

// Middleware que extrae y valida el JWT enviado en la cabecera Authorization.
function auth(req, res, next) {
  const header = req.headers.authorization || "";
  const token = header.startsWith("Bearer ") ? header.slice(7) : null;
  if (!token) return res.status(401).json({ error: "token requerido" });
  try {
    req.user = jwt.verify(token, JWT_SECRET);
    next();
  } catch (err) {
    res.status(401).json({ error: "token inválido" });
  }
}

// Comprueba si un rol tiene un permiso concreto según roles.json.
function hasPermission(role, permission) {
  const roleDef = roles[role];
  return Boolean(roleDef && roleDef.permissions.includes(permission));
}

// Devuelve el catálogo público de productos con búsqueda opcional.
app.get("/api/public/catalog", async (req, res) => {
  const rows = await db.publicCatalog(req.query.q);
  res.json(rows);
});

// Procesa el checkout público, valida permisos y crea un pedido real.
app.post("/api/public/orders", auth, async (req, res) => {
  if (!hasPermission(req.user.role, "checkout")) {
    return res.status(403).json({ error: "permiso denegado" });
  }
  try {
    const order = await db.createOrder(req.user.sub, req.body.items);
    res.status(201).json(order);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// Devuelve los pedidos propios del usuario autenticado.
app.get("/api/public/orders/mine", auth, async (req, res) => {
  if (!hasPermission(req.user.role, "checkout")) {
    return res.status(403).json({ error: "permiso denegado" });
  }
  const rows = await db.listMyOrders(req.user.sub);
  res.json(rows);
});

// Lista los registros de un departamento si el rol tiene permiso de lectura.
app.get("/api/:department", auth, async (req, res) => {
  const { department } = req.params;
  if (!hasPermission(req.user.role, `read:${department}`)) {
    return res.status(403).json({ error: "permiso denegado" });
  }
  try {
    const rows = await db.listDepartment(department, req.query.q);
    res.json(rows);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// Crea un pedido a nombre de un comprador sin cuenta (Atención/Administrador), con la
// misma validación transaccional de stock que el checkout de invitado.
app.post("/api/pedidos", auth, async (req, res) => {
  if (!hasPermission(req.user.role, "write:pedidos")) {
    return res.status(403).json({ error: "permiso denegado" });
  }
  const { cliente_nombre, cliente_cedula, items } = req.body || {};
  try {
    const order = await db.createStaffOrder({ cliente_nombre, cliente_cedula }, items);
    res.status(201).json(order);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// Crea un registro de un departamento (pedidos se maneja en la ruta específica de arriba).
app.post("/api/:department", auth, async (req, res) => {
  const { department } = req.params;
  if (!hasPermission(req.user.role, `write:${department}`)) {
    return res.status(403).json({ error: "permiso denegado" });
  }
  try {
    const record = await db.createRecord(department, req.body || {});
    res.status(201).json(record);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// Actualiza un registro de un departamento con control de permisos por rol.
app.put("/api/:department/:id", auth, async (req, res) => {
  const { department, id } = req.params;
  if (!hasPermission(req.user.role, `write:${department}`)) {
    return res.status(403).json({ error: "permiso denegado" });
  }
  try {
    const record = await db.updateRecord(department, id, req.body || {});
    res.json(record);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// Elimina un registro de un departamento, excepto pedidos y rrhh por regla de negocio.
app.delete("/api/:department/:id", auth, async (req, res) => {
  const { department, id } = req.params;
  if (department === "pedidos") {
    return res.status(400).json({ error: "los pedidos no se pueden eliminar" });
  }
  if (department === "rrhh") {
    return res.status(400).json({ error: "los empleados no se eliminan desde la app" });
  }
  if (!hasPermission(req.user.role, `write:${department}`)) {
    return res.status(403).json({ error: "permiso denegado" });
  }
  try {
    await db.deleteRecord(department, id);
    res.status(204).end();
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// Endpoint simple para comprobar que proxy2 está vivo.
app.get("/health", (req, res) => res.json({ ok: true }));

const port = process.env.PORT || 4000;
app.listen(port, () => console.log(`proxy2 escuchando en :${port}`));
