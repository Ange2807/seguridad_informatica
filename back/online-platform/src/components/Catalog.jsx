import { useState, useEffect } from 'react';

export default function Catalog({ onAddToCart, refreshTrigger }) {
  const [products, setProducts] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchCatalog = async (query = '') => {
    setLoading(true);
    try {
      const qs = query ? `?q=${encodeURIComponent(query)}` : '';
      const res = await fetch(`/api/public/catalog${qs}`);
      const data = await res.json();
      setProducts(data || []);
    } catch (err) {
      console.error("Error al cargar catálogo:", err);
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCatalog();
  }, [refreshTrigger]);

  const handleSearch = () => fetchCatalog(search);
  const handleClear = () => {
    setSearch('');
    fetchCatalog('');
  };

  return (
    <section className="section-card catalog-section">
      <div className="section-header">
        <h2>Catálogo de Productos</h2>
        <div className="search-box">
          <input 
            type="text" 
            placeholder="Buscar producto..." 
            value={search}
            onChange={e => setSearch(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSearch()}
          />
          <button onClick={handleSearch} className="btn-icon">🔍</button>
          <button onClick={handleClear} className="btn-secondary">Limpiar</button>
        </div>
      </div>

      {loading ? (
        <div className="empty-state">Cargando...</div>
      ) : products.length === 0 ? (
        <div className="empty-state">No se encontraron productos.</div>
      ) : (
        <div className="catalog-grid">
          {products.map(p => (
            <div key={p.id} className="product-card">
              <h3>{p.producto}</h3>
              <div className="product-price">${Number(p.precio).toFixed(2)}</div>
              <div className="product-stock">Disponibles: {p.cantidad}</div>
              <button onClick={() => onAddToCart(p)} className="add-btn">
                Agregar al Carrito
              </button>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
