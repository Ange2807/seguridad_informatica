import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import bcrypt from "bcryptjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const USERS_FILE = path.join(__dirname, "users.json");

// Lee el archivo local donde se guardan las cuentas de invitados.
function readUsers() {
  const raw = fs.readFileSync(USERS_FILE, "utf-8");
  return JSON.parse(raw);
}

// Sobrescribe el archivo local con la lista actualizada de invitados.
function writeUsers(data) {
  fs.writeFileSync(USERS_FILE, JSON.stringify(data, null, 2));
}

// Registra un invitado nuevo con contraseña hasheada y rol guest.
async function registerGuest(username, password) {
  const data = readUsers();
  if (data.users.find((u) => u.user_na === username)) {
    throw new Error("el usuario ya existe");
  }
  const hash = await bcrypt.hash(password, 10);
  const id = data.users.length ? Math.max(...data.users.map((u) => u.id)) + 1 : 1;
  data.users.push({ id, user_na: username, user_pw: hash, roles: ["guest"] });
  writeUsers(data);
}

// Comprueba si un invitado existe y si su contraseña coincide.
async function verifyGuest(username, password) {
  const data = readUsers();
  const user = data.users.find((u) => u.user_na === username);
  if (!user) return null;
  const valid = await bcrypt.compare(password, user.user_pw);
  if (!valid) return null;
  return user;
}

export { registerGuest, verifyGuest };
