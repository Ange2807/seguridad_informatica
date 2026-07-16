import { PackageIcon } from "./icons.jsx";

export default function ProductRow({ producto, precio, cantidad }) {
  const lowStock = cantidad > 0 && cantidad <= 10;
  const outOfStock = cantidad === 0;

  return (
    <div className="product-row">
      <div className="product-icon">
        <PackageIcon />
      </div>
      <div className="product-info">
        <h3>{producto}</h3>
        <div className={`product-stock ${lowStock ? "stock-low" : ""} ${outOfStock ? "stock-out" : ""}`}>
          {outOfStock ? "Agotado" : `Disponibles: ${cantidad}`}
        </div>
      </div>
      <div className="product-price">${Number(precio).toFixed(2)}</div>
    </div>
  );
}
