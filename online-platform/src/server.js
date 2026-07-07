const express = require("express");
const path = require("path");
const fs = require("fs");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const cors = require("cors");

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, "../public")));

const USERS_FILE = path.join(__dirname, "users.json");
const PROXY2_URL = process.env.PROXY2_URL || "http://proxy2:4000";
const JWT_SECRET = process.env.JWT_SECRET;

function readUsers() {
  const raw = fs.readFileSync(USERS_FILE, "utf-8");
  return JSON.parse(raw);
}

function writeUsers(data) {
  fs.writeFileSync(USERS_FILE, JSON.stringify(data, null, 2));
}

app.post("/api/register", async (req, res) => {
  const { username, password } = req.body || {};
  if (!username || !password) {
    return res.status(400).json({ error: "usuario y contraseña requeridos" });
  }
  const data = readUsers();
  if (data.users.find((u) => u.user_na === username)) {
    return res.status(409).json({ error: "el usuario ya existe" });
  }
  const hash = await bcrypt.hash(password, 10);
  const id = data.users.length ? Math.max(...data.users.map((u) => u.id)) + 1 : 1;
  data.users.push({ id, user_na: username, user_pw: hash, roles: ["guest"] });
  writeUsers(data);
  res.status(201).json({ ok: true });
});

app.post("/api/login", async (req, res) => {
  const { username, password } = req.body || {};
  const data = readUsers();
  const user = data.users.find((u) => u.user_na === username);
  if (!user) return res.status(401).json({ error: "credenciales inválidas" });
  const valid = await bcrypt.compare(password, user.user_pw);
  if (!valid) return res.status(401).json({ error: "credenciales inválidas" });
  const token = jwt.sign({ sub: user.user_na, role: user.roles[0] }, JWT_SECRET, {
    expiresIn: "4h",
  });
  res.json({ token });
});

app.get("/api/catalog", async (req, res) => {
  try {
    const query = req.query.q ? `?q=${encodeURIComponent(req.query.q)}` : "";
    const upstream = await fetch(`${PROXY2_URL}/api/public/catalog${query}`);
    const rows = await upstream.json();
    res.json(rows);
  } catch (err) {
    res.status(502).json({ error: "catálogo no disponible" });
  }
});

app.post("/api/checkout", async (req, res) => {
  const authorization = req.headers.authorization;
  if (!authorization) {
    return res.status(401).json({ error: "inicia sesión para comprar" });
  }
  try {
    const upstream = await fetch(`${PROXY2_URL}/api/public/orders`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: authorization },
      body: JSON.stringify({ items: req.body.items || [] }),
    });
    const data = await upstream.json();
    res.status(upstream.status).json(data);
  } catch (err) {
    res.status(502).json({ error: "no se pudo procesar el pedido" });
  }
});

app.get("/api/my-orders", async (req, res) => {
  const authorization = req.headers.authorization;
  if (!authorization) {
    return res.status(401).json({ error: "inicia sesión para ver tus pedidos" });
  }
  try {
    const upstream = await fetch(`${PROXY2_URL}/api/public/orders/mine`, {
      headers: { Authorization: authorization },
    });
    const data = await upstream.json();
    res.status(upstream.status).json(data);
  } catch (err) {
    res.status(502).json({ error: "no se pudieron obtener los pedidos" });
  }
});

const port = process.env.PORT || 3000;
app.listen(port, () => console.log(`online-platform escuchando en :${port}`));
