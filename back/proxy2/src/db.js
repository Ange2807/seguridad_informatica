const { Pool } = require("pg");

const pool = new Pool({
  host: process.env.DB_HOST,
  port: process.env.DB_PORT,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
});

const DEPARTMENTS = {
  atencion: {
    table: "tickets",
    searchColumns: ["cliente", "asunto"],
    fields: ["cliente", "asunto", "estado"],
  },
  rrhh: {
    table: "employees",
    searchColumns: ["cedula", "nombre", "cargo"],
    fields: ["cedula", "nombre", "cargo"],
  },
  inventario: {
    table: "inventory",
    searchColumns: ["producto", "ubicacion"],
    fields: ["producto", "cantidad", "ubicacion", "precio"],
  },
  pedidos: {
    table: "orders",
    searchColumns: ["guest_username", "estado"],
    fields: ["estado"],
  },
};

const ORDER_ITEMS_JOIN = `
  SELECT o.id, o.guest_username, o.estado, o.total, o.creado_en,
    COALESCE(
      json_agg(json_build_object('producto', oi.producto, 'cantidad', oi.cantidad, 'precio_unitario', oi.precio_unitario))
        FILTER (WHERE oi.id IS NOT NULL),
      '[]'
    ) AS items
  FROM orders o
  LEFT JOIN order_items oi ON oi.order_id = o.id
`;

async function listOrders(query) {
  if (query) {
    const { rows } = await pool.query(
      `${ORDER_ITEMS_JOIN} WHERE o.guest_username ILIKE $1 OR o.estado ILIKE $1 GROUP BY o.id ORDER BY o.id DESC`,
      [`%${query}%`]
    );
    return rows;
  }
  const { rows } = await pool.query(`${ORDER_ITEMS_JOIN} GROUP BY o.id ORDER BY o.id DESC`);
  return rows;
}

/**
 * Lista las órdenes del sistema. Si se proporciona `query`, busca por
 * `guest_username` o `estado` usando coincidencia parcial (ILIKE).
 * @param {string} [query] - Texto de búsqueda opcional.
 * @returns {Promise<Array>} - Arreglo de órdenes con sus items agregados.
 */

async function listMyOrders(username) {
  const { rows } = await pool.query(
    `${ORDER_ITEMS_JOIN} WHERE o.guest_username = $1 GROUP BY o.id ORDER BY o.id DESC`,
    [username]
  );
  return rows;
}

/**
 * Devuelve las órdenes pertenecientes a un usuario específico.
 * @param {string} username - Nombre de usuario del invitado.
 * @returns {Promise<Array>} - Arreglo de órdenes del usuario.
 */

function getDept(department) {
  const dept = DEPARTMENTS[department];
  if (!dept) throw new Error("departamento desconocido");
  return dept;
}

/**
 * Obtiene la configuración del departamento (tabla, columnas de búsqueda, campos).
 * Lanza un error si el departamento no existe.
 * @param {string} department - Identificador del departamento.
 * @returns {Object} - Configuración del departamento.
 * @throws {Error} - "departamento desconocido" si no existe.
 */

async function listDepartment(department, query) {
  if (department === "pedidos") return listOrders(query);
  const dept = getDept(department);
  if (query) {
    const conditions = dept.searchColumns.map((col, i) => `${col} ILIKE $${i + 1}`).join(" OR ");
    const params = dept.searchColumns.map(() => `%${query}%`);
    const { rows } = await pool.query(
      `SELECT * FROM ${dept.table} WHERE ${conditions} ORDER BY id`,
      params
    );
    return rows;
  }
  const { rows } = await pool.query(`SELECT * FROM ${dept.table} ORDER BY id`);
  return rows;
}

/**
 * Lista registros de un departamento genérico. Para `pedidos` delega en `listOrders`.
 * Si se proporciona `query`, realiza búsqueda parcial sobre las columnas definidas.
 * @param {string} department - Identificador del departamento.
 * @param {string} [query] - Texto de búsqueda opcional.
 * @returns {Promise<Array>} - Arreglo de registros.
 */

async function createRecord(department, data) {
  const dept = getDept(department);
  const columns = dept.fields.filter((field) => data[field] !== undefined);
  if (columns.length === 0) throw new Error("no se recibieron campos válidos");
  const values = columns.map((field) => data[field]);
  const placeholders = columns.map((_, i) => `$${i + 1}`).join(", ");
  const { rows } = await pool.query(
    `INSERT INTO ${dept.table} (${columns.join(", ")}) VALUES (${placeholders}) RETURNING *`,
    values
  );
  return rows[0];
}

/**
 * Crea un registro en la tabla asociada al departamento usando solo los campos válidos.
 * @param {string} department - Identificador del departamento.
 * @param {Object} data - Objeto con los campos a insertar.
 * @returns {Promise<Object>} - Registro recién insertado.
 * @throws {Error} - Si no se reciben campos válidos.
 */

async function updateRecord(department, id, data) {
  const dept = getDept(department);
  const columns = dept.fields.filter((field) => data[field] !== undefined);
  if (columns.length === 0) throw new Error("no se recibieron campos válidos");
  const setClause = columns.map((field, i) => `${field} = $${i + 1}`).join(", ");
  const values = columns.map((field) => data[field]);
  const { rows } = await pool.query(
    `UPDATE ${dept.table} SET ${setClause} WHERE id = $${columns.length + 1} RETURNING *`,
    [...values, id]
  );
  if (!rows[0]) throw new Error("registro no encontrado");
  return rows[0];
}

/**
 * Actualiza un registro por `id` en la tabla del departamento usando los campos provistos.
 * @param {string} department - Identificador del departamento.
 * @param {number} id - ID del registro a actualizar.
 * @param {Object} data - Campos a actualizar.
 * @returns {Promise<Object>} - Registro actualizado.
 * @throws {Error} - Si no se reciben campos válidos o el registro no existe.
 */

async function deleteRecord(department, id) {
  const dept = getDept(department);
  const { rowCount } = await pool.query(`DELETE FROM ${dept.table} WHERE id = $1`, [id]);
  if (rowCount === 0) throw new Error("registro no encontrado");
}

/**
 * Elimina un registro por `id` en la tabla del departamento.
 * @param {string} department - Identificador del departamento.
 * @param {number} id - ID del registro a eliminar.
 * @throws {Error} - Si el registro no existe.
 */

async function publicCatalog(query) {
  if (query) {
    const { rows } = await pool.query(
      "SELECT id, producto, cantidad, precio FROM inventory WHERE producto ILIKE $1 ORDER BY id",
      [`%${query}%`]
    );
    return rows;
  }
  const { rows } = await pool.query(
    "SELECT id, producto, cantidad, precio FROM inventory ORDER BY id"
  );
  return rows;
}

/**
 * Devuelve el catálogo público (productos) con campos reducidos.
 * Si `query` está presente, busca por `producto` usando coincidencia parcial.
 * @param {string} [query] - Texto de búsqueda opcional.
 * @returns {Promise<Array>} - Arreglo de productos.
 */

async function createOrder(username, items) {
  if (!Array.isArray(items) || items.length === 0) {
    throw new Error("el carrito está vacío");
  }
  const client = await pool.connect();
  try {
    await client.query("BEGIN");
    let total = 0;
    const orderItems = [];
    for (const item of items) {
      const { rows } = await client.query(
        "SELECT id, producto, cantidad, precio FROM inventory WHERE id = $1 FOR UPDATE",
        [item.id]
      );
      const product = rows[0];
      if (!product) throw new Error(`el producto ${item.id} no existe`);
      const cantidadPedida = Number(item.cantidad) || 0;
      if (cantidadPedida <= 0) throw new Error(`cantidad inválida para ${product.producto}`);
      if (product.cantidad < cantidadPedida) {
        throw new Error(`sin stock suficiente de ${product.producto}`);
      }
      const subtotal = Number(product.precio) * cantidadPedida;
      total += subtotal;
      orderItems.push({ producto: product.producto, cantidad: cantidadPedida, precio_unitario: product.precio });
      await client.query("UPDATE inventory SET cantidad = cantidad - $1 WHERE id = $2", [
        cantidadPedida,
        item.id,
      ]);
    }
    const orderRes = await client.query(
      "INSERT INTO orders (guest_username, estado, total) VALUES ($1, 'pendiente', $2) RETURNING *",
      [username, total]
    );
    const order = orderRes.rows[0];
    for (const item of orderItems) {
      await client.query(
        "INSERT INTO order_items (order_id, producto, cantidad, precio_unitario) VALUES ($1, $2, $3, $4)",
        [order.id, item.producto, item.cantidad, item.precio_unitario]
      );
    }
    await client.query("COMMIT");
    return { ...order, items: orderItems };
  } catch (err) {
    await client.query("ROLLBACK");
    throw err;
  } finally {
    client.release();
  }
}

/**
 * Crea una orden para un `username` con los `items` indicados.
 * Operación transaccional: bloquea filas de inventario (`FOR UPDATE`), valida stock,
 * decrementa inventario, inserta la orden y sus items. Hace `COMMIT` o `ROLLBACK`.
 * @param {string} username - Nombre de usuario del invitado que realiza la orden.
 * @param {Array<Object>} items - Arreglo de items {id, cantidad}.
 * @returns {Promise<Object>} - Orden creada con su lista de items y total.
 * @throws {Error} - Cuando el carrito está vacío, producto inexistente, cantidad inválida o sin stock.
 */

module.exports = {
  pool,
  listDepartment,
  createRecord,
  updateRecord,
  deleteRecord,
  publicCatalog,
  createOrder,
  listMyOrders,
};
