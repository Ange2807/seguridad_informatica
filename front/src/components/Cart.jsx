import React, { useState } from 'react';
import GlassCard from './GlassCard';
import { X, CheckCircle, Trash2 } from 'lucide-react';
import { api } from '../services/api';

const Cart = ({ cart, onUpdateCart, onClose, user }) => {
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const handleCheckout = async () => {
    if (!user) {
      setError('Debes iniciar sesión para finalizar la compra.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      await api.checkout(cart);
      setSuccess(true);
      onUpdateCart([]); // Clear cart
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const removeItem = (index) => {
    const newCart = [...cart];
    newCart.splice(index, 1);
    onUpdateCart(newCart);
  };

  const total = cart.reduce((acc, item) => acc + (item.price || 0), 0);

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 90
    }} className="animate-fade-in">
      <GlassCard style={{ width: '500px', maxHeight: '80vh', display: 'flex', flexDirection: 'column', padding: '32px', position: 'relative' }}>
        <button onClick={onClose} style={{
          position: 'absolute', top: '16px', right: '16px',
          background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer'
        }}>
          <X size={24} />
        </button>
        
        <h2 style={{ marginBottom: '24px' }}>Tu Carrito</h2>
        
        {success ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <CheckCircle size={64} color="var(--primary)" style={{ margin: '0 auto 16px' }} />
            <h3>¡Pedido Procesado Exitosamente!</h3>
            <p style={{ color: 'var(--text-muted)', marginTop: '8px' }}>Tus dispositivos han sido solicitados.</p>
          </div>
        ) : (
          <>
            {error && <div style={{ color: '#ff4444', marginBottom: '16px' }}>{error}</div>}
            
            <div style={{ flex: 1, overflowY: 'auto', marginBottom: '24px' }}>
              {cart.length === 0 ? (
                <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '20px' }}>Tu carrito está vacío.</p>
              ) : (
                cart.map((item, idx) => (
                  <div key={idx} style={{ 
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '12px 0', borderBottom: '1px solid var(--glass-border)'
                  }}>
                    <div>
                      <div style={{ fontWeight: 'bold' }}>{item.name}</div>
                      <div style={{ color: 'var(--text-muted)', fontSize: '14px' }}>${item.price}</div>
                    </div>
                    <button onClick={() => removeItem(idx)} style={{
                      background: 'transparent', border: 'none', color: '#ff4444', cursor: 'pointer'
                    }}>
                      <Trash2 size={20} />
                    </button>
                  </div>
                ))
              )}
            </div>
            
            {cart.length > 0 && (
              <div style={{ borderTop: '1px solid var(--glass-border)', paddingTop: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '24px', fontSize: '20px', fontWeight: 'bold' }}>
                  <span>Total:</span>
                  <span>${total.toFixed(2)}</span>
                </div>
                <button className="btn-primary" style={{ width: '100%' }} onClick={handleCheckout} disabled={loading}>
                  {loading ? 'Procesando...' : 'Finalizar Pedido'}
                </button>
              </div>
            )}
          </>
        )}
      </GlassCard>
    </div>
  );
};

export default Cart;
