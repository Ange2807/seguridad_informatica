import { useState, useEffect, useCallback } from 'react';
import Navbar from './components/Navbar';
import Catalog from './components/Catalog';
import CartSidebar from './components/CartSidebar';
import OrderHistory from './components/OrderHistory';
import ToastContainer from './components/ToastContainer';

export default function App() {
  const [token, setToken] = useState(null);
  const [username, setUsername] = useState('');
  const [cart, setCart] = useState([]);
  const [toasts, setToasts] = useState([]);
  
  // Need to force refresh order history after checkout
  const [refreshOrders, setRefreshOrders] = useState(0);

  const addToast = (message, type = 'success') => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 5000);
  };

  const addToCart = (product) => {
    setCart(prev => {
      const existing = prev.find(item => item.id === product.id);
      if (existing) {
        return prev.map(item => 
          item.id === product.id ? { ...item, cantidad: item.cantidad + 1 } : item
        );
      }
      return [...prev, { ...product, cantidad: 1 }];
    });
  };

  const handleCheckout = async () => {
    if (!token) {
      addToast('Inicia sesión de invitado para poder pagar.', 'error');
      return;
    }
    if (cart.length === 0) {
      addToast('El carrito está vacío.', 'error');
      return;
    }

    const items = cart.map(item => ({ id: item.id, cantidad: item.cantidad }));
    
    try {
      const res = await fetch('/api/public/orders', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ items })
      });
      const data = await res.json();
      if (res.ok) {
        addToast(`Pedido #${data.id} confirmado. Total: $${Number(data.total).toFixed(2)}`);
        setCart([]);
        setRefreshOrders(prev => prev + 1);
      } else {
        addToast(data.error || 'No se pudo procesar el pedido', 'error');
      }
    } catch (err) {
      addToast('Error de red al procesar el pago', 'error');
    }
  };

  return (
    <div className="app-container">
      <Navbar username={username} />
      
      <header className="hero">
        <div className="hero-content">
          <h1>Equipamiento de Alta Calidad</h1>
          <p>Descubre nuestro catálogo de productos y realiza tus compras con la mayor seguridad y confianza.</p>
        </div>
      </header>

      <div className="main-layout">
        <main className="content-area">
          <Catalog onAddToCart={addToCart} refreshTrigger={refreshOrders} />
          <OrderHistory token={token} refreshTrigger={refreshOrders} />
        </main>
        
        <aside className="sidebar">
          <CartSidebar 
            cart={cart} 
            token={token}
            setToken={setToken}
            setUsername={setUsername}
            onCheckout={handleCheckout}
            addToast={addToast}
          />
        </aside>
      </div>

      <ToastContainer toasts={toasts} />
    </div>
  );
}
