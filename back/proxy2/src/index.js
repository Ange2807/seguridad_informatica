const express = require("express");
const cors = require("cors");
const jwt = require("jsonwebtoken");
const roles = require("../roles.json");
const { bindAsUser, findRole } = require("./ldapAuth");
const db = require("./db");

const app = express();
app.use(cors());
app.use(express.json());

const JWT_SECRET = process.env.JWT_SECRET;

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

function hasPermission(role, permission) {
  const roleDef = roles[role];
  return Boolean(roleDef && roleDef.permissions.includes(permission));
}

app.get("/api/public/catalog", async (req, res) => {
  const rows = await db.publicCatalog(req.query.q);
  res.json(rows);
});

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

app.get("/api/public/orders/mine", auth, async (req, res) => {
  if (!hasPermission(req.user.role, "checkout")) {
    return res.status(403).json({ error: "permiso denegado" });
  }
  const rows = await db.listMyOrders(req.user.sub);
  res.json(rows);
});

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

app.post("/api/:department", auth, async (req, res) => {
  const { department } = req.params;
  if (department === "pedidos") {
    return res.status(400).json({ error: "los pedidos solo se crean desde el checkout" });
  }
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

app.delete("/api/:department/:id", auth, async (req, res) => {
  const { department, id } = req.params;
  if (department === "pedidos") {
    return res.status(400).json({ error: "los pedidos no se pueden eliminar" });
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

app.get("/health", (req, res) => res.json({ ok: true }));

const port = process.env.PORT || 4000;
app.listen(port, () => console.log(`proxy2 escuchando en :${port}`));
