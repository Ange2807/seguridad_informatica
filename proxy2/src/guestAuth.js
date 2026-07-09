const fs = require("fs");
const path = require("path");
const bcrypt = require("bcryptjs");

const USERS_FILE = path.join(__dirname, "users.json");

function readUsers() {
  const raw = fs.readFileSync(USERS_FILE, "utf-8");
  return JSON.parse(raw);
}

function writeUsers(data) {
  fs.writeFileSync(USERS_FILE, JSON.stringify(data, null, 2));
}

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

async function verifyGuest(username, password) {
  const data = readUsers();
  const user = data.users.find((u) => u.user_na === username);
  if (!user) return null;
  const valid = await bcrypt.compare(password, user.user_pw);
  if (!valid) return null;
  return user;
}

module.exports = { registerGuest, verifyGuest };
