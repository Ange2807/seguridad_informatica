import React, { useState } from 'react';
import GlassCard from './GlassCard';
import { X } from 'lucide-react';
import { api } from '../services/api';

const AuthModal = ({ onClose, onLoginSuccess }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      if (isLogin) {
        const data = await api.login(username, password);
        localStorage.setItem('jwt_token', data.token);
        onLoginSuccess({ username });
      } else {
        await api.register(username, password);
        const data = await api.login(username, password);
        localStorage.setItem('jwt_token', data.token);
        onLoginSuccess({ username });
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100
    }} className="animate-fade-in">
      <GlassCard style={{ width: '400px', padding: '32px', position: 'relative' }}>
        <button onClick={onClose} style={{
          position: 'absolute', top: '16px', right: '16px',
          background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer'
        }}>
          <X size={24} />
        </button>
        
        <h2 style={{ marginBottom: '24px', textAlign: 'center' }}>
          {isLogin ? 'Acceso Seguro' : 'Registro'}
        </h2>
        
        {error && (
          <div style={{
            background: 'rgba(255, 0, 0, 0.1)', color: '#ff4444', 
            padding: '12px', borderRadius: '8px', marginBottom: '16px', fontSize: '14px'
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: 'var(--text-muted)' }}>Usuario</label>
            <input 
              type="text" 
              className="input-field" 
              value={username} 
              onChange={e => setUsername(e.target.value)} 
              required 
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: 'var(--text-muted)' }}>Contraseña</label>
            <input 
              type="password" 
              className="input-field" 
              value={password} 
              onChange={e => setPassword(e.target.value)} 
              required 
            />
          </div>
          <button type="submit" className="btn-primary" style={{ marginTop: '8px' }} disabled={loading}>
            {loading ? 'Procesando...' : (isLogin ? 'Ingresar' : 'Registrarse')}
          </button>
        </form>

        <div style={{ marginTop: '24px', textAlign: 'center', fontSize: '14px', color: 'var(--text-muted)' }}>
          {isLogin ? '¿No tienes cuenta?' : '¿Ya tienes cuenta?'}
          <button 
            onClick={() => setIsLogin(!isLogin)}
            style={{ 
              background: 'transparent', border: 'none', color: 'var(--primary)', 
              marginLeft: '8px', cursor: 'pointer', fontWeight: 'bold' 
            }}
          >
            {isLogin ? 'Regístrate' : 'Inicia Sesión'}
          </button>
        </div>
      </GlassCard>
    </div>
  );
};

export default AuthModal;
