const bcrypt = require("bcryptjs");
const { pool } = require("./db");

async function findEmployeeByCedula(cedula) {
  const { rows } = await pool.query(
    "SELECT cedula, nombre, cargo FROM employees WHERE cedula = $1",
    [cedula]
  );
  return rows[0] || null;
}

async function registerStaff(cedula, username, password) {
  const employee = await findEmployeeByCedula(cedula);
  if (!employee) {
    throw new Error("la cédula no corresponde a ningún empleado cargado por RRHH");
  }
  const existingCedula = await pool.query(
    "SELECT id FROM staff_accounts WHERE cedula = $1",
    [cedula]
  );
  if (existingCedula.rows.length > 0) {
    throw new Error("esta cédula ya tiene una cuenta registrada");
  }
  const existingUsername = await pool.query(
    "SELECT id FROM staff_accounts WHERE username = $1",
    [username]
  );
  if (existingUsername.rows.length > 0) {
    throw new Error("el usuario ya existe");
  }
  const hash = await bcrypt.hash(password, 10);
  await pool.query(
    "INSERT INTO staff_accounts (cedula, username, password_hash) VALUES ($1, $2, $3)",
    [cedula, username, hash]
  );
  return employee;
}

async function verifyStaff(username, password) {
  const { rows } = await pool.query(
    `SELECT sa.username, sa.password_hash, e.cargo, e.nombre
     FROM staff_accounts sa
     JOIN employees e ON e.cedula = sa.cedula
     WHERE sa.username = $1`,
    [username]
  );
  const account = rows[0];
  if (!account) return null;
  const valid = await bcrypt.compare(password, account.password_hash);
  if (!valid) return null;
  return account;
}

module.exports = { registerStaff, verifyStaff, findEmployeeByCedula };
