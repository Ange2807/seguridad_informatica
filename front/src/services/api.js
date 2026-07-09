const API_BASE = '/api';

function getAuthHeader() {
  const token = localStorage.getItem('jwt_token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

export const api = {
  async login(username, password) {
    const res = await fetch(`${API_BASE}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Login failed');
    return data;
  },

  async register(username, password) {
    const res = await fetch(`${API_BASE}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Registration failed');
    return data;
  },

  async getCatalog(query = '') {
    const res = await fetch(`${API_BASE}/catalog${query ? '?q=' + encodeURIComponent(query) : ''}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to fetch catalog');
    return data;
  },

  async checkout(items) {
    const res = await fetch(`${API_BASE}/checkout`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        ...getAuthHeader()
      },
      body: JSON.stringify({ items })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Checkout failed');
    return data;
  },

  async getMyOrders() {
    const res = await fetch(`${API_BASE}/my-orders`, {
      headers: {
        ...getAuthHeader()
      }
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to fetch orders');
    return data;
  }
};
