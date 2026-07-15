import { useState } from 'react';

export default function CartSidebar({ cart, token, setToken, setUsername, onCheckout, addToast }) {
  const [loginUser, setLoginUser] = useState('');
  const [loginPass, setLoginPass] = useState('');
  
  const [regUser, setRegUser] = useState('');
  const [regPass, setRegPass] = useState('');

  const total = cart.reduce((sum, item) => sum + item.precio * item.cantidad, 0);

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch('/api/guest/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: loginUser, password: loginPass })
      });
      const data = await res.json();
      if (res.ok) {
        setToken(data.token);
        setUsername(loginUser);
        addToast('Sesión iniciada.', 'success');
        setLoginUser('');
        setLoginPass('');
      } else {
        addToast(data.error, 'error');
      }
    } catch (err) {
      addToast("Error de red", 'error');
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch('/api/guest/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: regUser, password: regPass })
      });
      const data = await res.json();
      if (res.ok) {
        addToast('Cuenta creada, ya puedes iniciar sesión.', 'success');
        setRegUser('');
        setRegPass('');
      } else {
        addToast(data.error, 'error');
      }
    } catch (err) {
      addToast("Error de red", 'error');
    }
  };

  return (
    <>
      <div className="widget cart-widget">
        <div className="widget-header">
          <h3>🛒 Tu Carrito</h3>
        </div>
        <div className="widget-body">
          <ul id="cart-items" style={{ listStyle: 'none', padding: 0 }}>
            {cart.length === 0 ? (
              <div className="empty-state" style={{ padding: '1rem' }}>Tu carrito está vacío</div>
            ) : (
              cart.map(item => (
                <li key={item.id} className="cart-item">
                  <div>
                    <span className="cart-item-name">{item.nombre}</span>
                    <span className="cart-item-qty">x{item.cantidad}</span>
                  </div>
                  <span className="cart-item-price">${(item.precio * item.cantidad).toFixed(2)}</span>
                </li>
              ))
            )}
          </ul>
          <div className="cart-summary">
            <span>Total a Pagar</span>
            <span className="total-amount">${total.toFixed(2)}</span>
          </div>
          <button onClick={onCheckout} className="btn-primary btn-block">Finalizar Compra</button>
        </div>
      </div>

      {!token && (
        <div className="widget auth-widget">
          <div className="widget-header">
            <h3>👤 Mi Cuenta</h3>
          </div>
          <div className="widget-body">
            <div className="auth-container">
              <form onSubmit={handleLogin} className="auth-form">
                <h4>Iniciar Sesión</h4>
                <div className="input-group">
                  <input 
                    type="text" 
                    placeholder="Usuario" 
                    value={loginUser} 
                    onChange={e => setLoginUser(e.target.value)} 
                    required 
                  />
                </div>
                <div className="input-group">
                  <input 
                    type="password" 
                    placeholder="Contraseña" 
                    value={loginPass} 
                    onChange={e => setLoginPass(e.target.value)} 
                    required 
                  />
                </div>
                <button type="submit" className="btn-primary btn-block">Ingresar</button>
              </form>

              <div className="divider"><span>o</span></div>

              <form onSubmit={handleRegister} className="auth-form">
                <h4>Crear Cuenta Nueva</h4>
                <div className="input-group">
                  <input 
                    type="text" 
                    placeholder="Nuevo Usuario" 
                    value={regUser} 
                    onChange={e => setRegUser(e.target.value)} 
                    required 
                  />
                </div>
                <div className="input-group">
                  <input 
                    type="password" 
                    placeholder="Contraseña" 
                    value={regPass} 
                    onChange={e => setRegPass(e.target.value)} 
                    required 
                  />
                </div>
                <button type="submit" className="btn-secondary btn-block">Registrarme</button>
              </form>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
