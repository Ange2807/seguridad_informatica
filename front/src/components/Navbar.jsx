import React from 'react';
import { Shield, User, LogOut, ShoppingCart } from 'lucide-react';

const Navbar = ({ user, onOpenAuth, onLogout, onToggleCart, cartCount }) => {
  return (
    <nav style={{ padding: '20px 0', marginBottom: '40px', borderBottom: '1px solid var(--glass-border)' }}>
      <div className="container flex-between">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Shield color="var(--primary)" size={32} />
          <h2 style={{ margin: 0, letterSpacing: '1px' }}>SECURE<span style={{ color: 'var(--primary)' }}>CORP</span></h2>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <button className="btn-secondary" onClick={onToggleCart} style={{ display: 'flex', alignItems: 'center', gap: '8px', position: 'relative' }}>
            <ShoppingCart size={20} />
            {cartCount > 0 && (
              <span style={{
                position: 'absolute', top: '-8px', right: '-8px',
                background: 'var(--primary)', color: '#000',
                borderRadius: '50%', width: '20px', height: '20px',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '12px', fontWeight: 'bold'
              }}>
                {cartCount}
              </span>
            )}
          </button>
          {user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)' }}>
                <User size={20} />
                <span>{user.username}</span>
              </div>
              <button className="btn-secondary" onClick={onLogout} title="Logout" style={{ padding: '10px' }}>
                <LogOut size={20} />
              </button>
            </div>
          ) : (
            <button className="btn-primary" onClick={onOpenAuth}>
              Iniciar Sesión
            </button>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
