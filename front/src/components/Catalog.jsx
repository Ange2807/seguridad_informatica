import React, { useEffect, useState } from 'react';
import GlassCard from './GlassCard';
import { api } from '../services/api';
import { Search, Plus } from 'lucide-react';

const Catalog = ({ onAddToCart }) => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');

  const fetchCatalog = async (q = '') => {
    setLoading(true);
    try {
      const data = await api.getCatalog(q);
      setItems(data);
    } catch (err) {
      setError('No se pudo cargar el catálogo.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCatalog();
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    fetchCatalog(search);
  };

  return (
    <div className="container animate-fade-in">
      <div className="flex-between" style={{ marginBottom: '24px' }}>
        <h2>Catálogo de Dispositivos</h2>
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '8px', width: '300px' }}>
          <input 
            type="text" 
            placeholder="Buscar..." 
            className="input-field" 
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
          <button type="submit" className="btn-secondary" style={{ padding: '10px' }}>
            <Search size={20} />
          </button>
        </form>
      </div>
      
      {error && <div style={{ color: '#ff4444' }}>{error}</div>}
      {loading ? (
        <div>Cargando catálogo...</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '24px' }}>
          {items.map(item => (
            <GlassCard key={item.id} style={{ padding: '24px', display: 'flex', flexDirection: 'column' }}>
              <div style={{ flex: 1 }}>
                <h3 style={{ marginBottom: '8px', color: 'var(--primary)' }}>{item.name}</h3>
                <p style={{ color: 'var(--text-muted)', fontSize: '14px', marginBottom: '16px' }}>{item.description || 'Sin descripción'}</p>
                <div style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '16px' }}>${item.price}</div>
              </div>
              <button className="btn-primary" style={{ display: 'flex', justifyContent: 'center', gap: '8px' }} onClick={() => onAddToCart(item)}>
                <Plus size={20} /> Añadir al Carrito
              </button>
            </GlassCard>
          ))}
          {items.length === 0 && <p>No hay artículos disponibles.</p>}
        </div>
      )}
    </div>
  );
};

export default Catalog;
