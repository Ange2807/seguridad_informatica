import pg from "pg";
const { Pool } = pg;

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
    fields: ["producto", "cantidad", "ubicacion", "precio", "disponible"],
  },
  pedidos: {
    table: "orders",
    searchColumns: ["guest_username", "estado"],
    fields: ["estado"],
  },
};

const ORDER_ITEMS_JOIN = `
  SELECT o.id, o.guest_username, o.cliente_nombre, o.cliente_cedula,
    COALESCE(o.guest_username, o.cliente_nombre) AS comprador,
    o.estado, o.total, o.creado_en,
    COALESCE(
      json_agg(json_build_object('producto', oi.producto, 'cantidad', oi.cantidad, 'precio_unitario', oi.precio_unitario))
        FILTER (WHERE oi.id IS NOT NULL),
      '[]'
    ) AS items
  FROM orders o
  LEFT JOIN order_items oi ON oi.order_id = o.id
`;

/**
 * Lista las órdenes del sistema. Si se proporciona `query`, busca por
 * comprador (usuario invitado, nombre o cédula) o `estado` usando coincidencia parcial (ILIKE).
 * @param {string} [query] - Texto de búsqueda opcional.
 * @returns {Promise<Array>} - Arreglo de órdenes con sus items agregados.
 */
async function listOrders(query) {
  if (query) {
    const { rows } = await pool.query(
      `${ORDER_ITEMS_JOIN} WHERE o.guest_username ILIKE $1 OR o.cliente_nombre ILIKE $1
         OR o.cliente_cedula ILIKE $1 OR o.estado ILIKE $1
       GROUP BY o.id ORDER BY o.id DESC`,
      [`%${query}%`]
    );
    return rows;
  }
  const { rows } = await pool.query(`${ORDER_ITEMS_JOIN} GROUP BY o.id ORDER BY o.id DESC`);
  return rows;
}

/**
 * Devuelve las órdenes pertenecientes a un usuario específico.
 * @param {string} username - Nombre de usuario del invitado.
 * @returns {Promise<Array>} - Arreglo de órdenes del usuario.
 */
async function listMyOrders(username) {
  const { rows } = await pool.query(
    `${ORDER_ITEMS_JOIN} WHERE o.guest_username = $1 GROUP BY o.id ORDER BY o.id DESC`,
    [username]
  );
  return rows;
}

/**
 * Obtiene la configuración del departamento (tabla, columnas de búsqueda, campos).
 * Lanza un error si el departamento no existe.
 * @param {string} department - Identificador del departamento.
 * @returns {Object} - Configuración del departamento.
 * @throws {Error} - "departamento desconocido" si no existe.
 */
function getDept(department) {
  const dept = DEPARTMENTS[department];
  if (!dept) throw new Error("departamento desconocido");
  return dept;
}

/**
 * Lista registros de un departamento genérico. Para `pedidos` delega en `listOrders`.
 * Si se proporciona `query`, realiza búsqueda parcial sobre las columnas definidas.
 * @param {string} department - Identificador del departamento.
 * @param {string} [query] - Texto de búsqueda opcional.
 * @returns {Promise<Array>} - Arreglo de registros.
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
 * Crea un registro en la tabla asociada al departamento usando solo los campos válidos.
 * @param {string} department - Identificador del departamento.
 * @param {Object} data - Objeto con los campos a insertar.
 * @returns {Promise<Object>} - Registro recién insertado.
 * @throws {Error} - Si no se reciben campos válidos.
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
 * Actualiza un registro por `id` en la tabla del departamento usando los campos provistos.
 * @param {string} department - Identificador del departamento.
 * @param {number} id - ID del registro a actualizar.
 * @param {Object} data - Campos a actualizar.
 * @returns {Promise<Object>} - Registro actualizado.
 * @throws {Error} - Si no se reciben campos válidos o el registro no existe.
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
 * Elimina un registro por `id` en la tabla del departamento.
 * @param {string} department - Identificador del departamento.
 * @param {number} id - ID del registro a eliminar.
 * @throws {Error} - Si el registro no existe.
 */
async function deleteRecord(department, id) {
  const dept = getDept(department);
  const { rowCount } = await pool.query(`DELETE FROM ${dept.table} WHERE id = $1`, [id]);
  if (rowCount === 0) throw new Error("registro no encontrado");
}

/**
 * Devuelve el catálogo público (productos disponibles) con campos reducidos.
 * Si `query` está presente, busca por `producto` usando coincidencia parcial.
 * @param {string} [query] - Texto de búsqueda opcional.
 * @returns {Promise<Array>} - Arreglo de productos.
 */
async function publicCatalog(query) {
  if (query) {
    const { rows } = await pool.query(
      "SELECT id, producto, cantidad, precio FROM inventory WHERE disponible = true AND producto ILIKE $1 ORDER BY id",
      [`%${query}%`]
    );
    return rows;
  }
  const { rows } = await pool.query(
    "SELECT id, producto, cantidad, precio FROM inventory WHERE disponible = true ORDER BY id"
  );
  return rows;
}

/**
 * Bloquea filas de inventario (`FOR UPDATE`), valida disponibilidad/stock y decrementa
 * la cantidad para cada item. Debe ejecutarse dentro de una transacción ya abierta.
 * @param {import('pg').PoolClient} client - Cliente con una transacción en curso.
 * @param {Array<Object>} items - Arreglo de items {id, cantidad}.
 * @returns {Promise<{total: number, orderItems: Array<Object>}>}
 * @throws {Error} - Producto inexistente, no disponible, cantidad inválida o sin stock.
 */
async function _reserveStock(client, items) {
  let total = 0;
  const orderItems = [];
  for (const item of items) {
    const { rows } = await client.query(
      "SELECT id, producto, cantidad, precio, disponible FROM inventory WHERE id = $1 FOR UPDATE",
      [item.id]
    );
    const product = rows[0];
    if (!product) throw new Error(`el producto ${item.id} no existe`);
    if (!product.disponible) throw new Error(`${product.producto} no está disponible`);
    const cantidadPedida = Number(item.cantidad) || 0;
    if (cantidadPedida <= 0) throw new Error(`cantidad inválida para ${product.producto}`);
    if (product.cantidad < cantidadPedida) {
      throw new Error(`sin stock suficiente de ${product.producto}`);
    }
    total += Number(product.precio) * cantidadPedida;
    orderItems.push({ producto: product.producto, cantidad: cantidadPedida, precio_unitario: product.precio });
    await client.query("UPDATE inventory SET cantidad = cantidad - $1 WHERE id = $2", [
      cantidadPedida,
      item.id,
    ]);
  }
  return { total, orderItems };
}

// Inserta la orden y sus items ya calculados; debe ejecutarse dentro de la misma transacción.
async function _insertOrder(client, orderFields, total, orderItems) {
  const columns = Object.keys(orderFields);
  const values = Object.values(orderFields);
  const placeholders = columns.map((_, i) => `$${i + 1}`).join(", ");
  const orderRes = await client.query(
    `INSERT INTO orders (${columns.join(", ")}, estado, total) VALUES (${placeholders}, 'pendiente', $${columns.length + 1}) RETURNING *`,
    [...values, total]
  );
  const order = orderRes.rows[0];
  for (const item of orderItems) {
    await client.query(
      "INSERT INTO order_items (order_id, producto, cantidad, precio_unitario) VALUES ($1, $2, $3, $4)",
      [order.id, item.producto, item.cantidad, item.precio_unitario]
    );
  }
  return { ...order, items: orderItems };
}

/**
 * Crea una orden para un `username` (invitado autenticado) con los `items` indicados.
 * Operación transaccional: bloquea filas de inventario, valida stock, decrementa
 * inventario, inserta la orden y sus items. Hace `COMMIT` o `ROLLBACK`.
 * @param {string} username - Nombre de usuario del invitado que realiza la orden.
 * @param {Array<Object>} items - Arreglo de items {id, cantidad}.
 * @returns {Promise<Object>} - Orden creada con su lista de items y total.
 * @throws {Error} - Cuando el carrito está vacío, producto inexistente, cantidad inválida o sin stock.
 */
async function createOrder(username, items) {
  if (!Array.isArray(items) || items.length === 0) {
    throw new Error("el carrito está vacío");
  }
  const client = await pool.connect();
  try {
    await client.query("BEGIN");
    const { total, orderItems } = await _reserveStock(client, items);
    const order = await _insertOrder(client, { guest_username: username }, total, orderItems);
    await client.query("COMMIT");
    return order;
  } catch (err) {
    await client.query("ROLLBACK");
    throw err;
  } finally {
    client.release();
  }
}

/**
 * Crea una orden en nombre de un comprador sin cuenta (usada por Atención), identificado
 * por nombre y cédula. Misma validación transaccional de stock que `createOrder`.
 * @param {{cliente_nombre: string, cliente_cedula: string}} comprador
 * @param {Array<Object>} items - Arreglo de items {id, cantidad}.
 * @returns {Promise<Object>} - Orden creada con su lista de items y total.
 * @throws {Error} - Faltan datos del comprador, carrito vacío, producto inexistente, sin stock, etc.
 */
async function createStaffOrder({ cliente_nombre, cliente_cedula }, items) {
  if (!cliente_nombre || !cliente_cedula) {
    throw new Error("nombre y cédula del comprador son requeridos");
  }
  if (!Array.isArray(items) || items.length === 0) {
    throw new Error("selecciona al menos un producto");
  }
  const client = await pool.connect();
  try {
    await client.query("BEGIN");
    const { total, orderItems } = await _reserveStock(client, items);
    const order = await _insertOrder(client, { cliente_nombre, cliente_cedula }, total, orderItems);
    await client.query("COMMIT");
    return order;
  } catch (err) {
    await client.query("ROLLBACK");
    throw err;
  } finally {
    client.release();
  }
}

export {
  pool,
  listDepartment,
  createRecord,
  updateRecord,
  deleteRecord,
  publicCatalog,
  createOrder,
  createStaffOrder,
  listMyOrders,
};
