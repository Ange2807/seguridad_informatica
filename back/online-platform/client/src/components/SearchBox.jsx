import { SearchIcon } from "./icons.jsx";

export default function SearchBox({ query, onQueryChange, onSearch, onClear }) {
  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch();
  };

  return (
    <form className="search-box" onSubmit={handleSubmit}>
      <input
        type="text"
        value={query}
        onChange={(e) => onQueryChange(e.target.value)}
        placeholder="Buscar producto..."
      />
      <button type="submit" className="btn-icon" aria-label="Buscar">
        <SearchIcon />
      </button>
      <button type="button" className="btn-text" onClick={onClear}>Limpiar</button>
    </form>
  );
}
