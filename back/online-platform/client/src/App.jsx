import { useEffect, useState } from "react";
import SearchBox from "./components/SearchBox.jsx";
import ProductRow from "./components/ProductCard.jsx";
import { StoreIcon } from "./components/icons.jsx";

// [SEGURIDAD] El frontend pide los datos a proxy1 (Nginx), quien los rutea a proxy2 internamente.
// Al ser un frontend 'stateless' y de solo lectura, no hay exposición directa de la BD ni manejo de tokens vulnerables.
async function fetchCatalog(query) {
  const qs = query ? `?q=${encodeURIComponent(query)}` : "";
  const res = await fetch(`/api/public/catalog${qs}`);
  if (!res.ok) throw new Error("No se pudo cargar el catálogo");
  return res.json();
}

export default function App() {
  const [products, setProducts] = useState([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadCatalog = (q) => {
    setLoading(true);
    setError(null);
    fetchCatalog(q)
      .then(setProducts)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadCatalog();
  }, []);

  const handleClear = () => {
    setQuery("");
    loadCatalog();
  };

  return (
    <>
      <nav className="navbar">
        <div className="nav-container">
          <div className="logo">
            <StoreIcon className="logo-icon" />
            Catálogo de Tienda por Departamentos
          </div>
        </div>
      </nav>

      <header className="hero">
        <div className="hero-content">
          <h1>Equipamiento de Alta Calidad</h1>
          <p>Consulta nuestro catálogo de productos y precios disponibles.</p>
        </div>
      </header>

      <div className="main-layout">
        <main className="content-area">
          <section className="section-card catalog-section">
            <div className="section-header">
              <h2>Catálogo de Productos</h2>
              <SearchBox
                query={query}
                onQueryChange={setQuery}
                onSearch={() => loadCatalog(query)}
                onClear={handleClear}
              />
            </div>

            {loading && <div className="empty-state">Cargando catálogo...</div>}
            {!loading && error && <div className="empty-state">{error}</div>}
            {!loading && !error && products.length === 0 && (
              <div className="empty-state">No se encontraron productos.</div>
            )}
            {!loading && !error && products.length > 0 && (
              <div className="catalog-list">
                {products.map((p) => (
                  <ProductRow key={p.id} {...p} />
                ))}
              </div>
            )}
          </section>
        </main>
      </div>
    </>
  );
}
