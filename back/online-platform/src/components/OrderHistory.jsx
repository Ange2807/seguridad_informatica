import { useState, useEffect } from 'react';

export default function OrderHistory({ token, refreshTrigger }) {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!token) {
      setOrders([]);
      return;
    }
    const fetchOrders = async () => {
      setLoading(true);
      try {
        const res = await fetch('/api/public/orders/mine', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();
        if (res.ok && Array.isArray(data)) {
          setOrders(data);
        } else {
          setOrders([]);
        }
      } catch (err) {
        console.error("Error al cargar pedidos:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchOrders();
  }, [token, refreshTrigger]);

  return (
    <section className="section-card orders-section">
      <h2>Historial de Pedidos</h2>
      {!token ? (
        <p className="status-text">Inicia sesión para ver tu historial de pedidos.</p>
      ) : loading ? (
        <div className="empty-state">Cargando pedidos...</div>
      ) : orders.length === 0 ? (
        <div className="empty-state">Todavía no tienes pedidos.</div>
      ) : (
        <div className="table-responsive">
          <table>
            <thead>
              <tr>
                <th>Pedido ID</th>
                <th>Fecha</th>
                <th>Artículos</th>
                <th>Total</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {orders.map(order => (
                <tr key={order.id}>
                  <td>#{order.id}</td>
                  <td>{new Date(order.creado_en).toLocaleString()}</td>
                  <td>
                    {order.items.map((it, idx) => (
                      <div key={idx}>{it.cantidad}x {it.producto}</div>
                    ))}
                  </td>
                  <td style={{ color: 'var(--success)', fontWeight: 600 }}>
                    ${Number(order.total).toFixed(2)}
                  </td>
                  <td>{order.estado}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
