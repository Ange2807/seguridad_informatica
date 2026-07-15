let authToken = null;
let cart = [];

function showMsg(text, ok) {
  const el = document.getElementById('msg');
  el.textContent = text;
  el.className = 'msg active ' + (ok ? 'ok' : 'error');
  setTimeout(() => {
    el.className = 'msg';
  }, 5000);
}

async function loadCatalog(query) {
  const qs = query ? `?q=${encodeURIComponent(query)}` : '';
  try {
    const res = await fetch(`/api/public/catalog${qs}`);
    const rows = await res.json();
    const container = document.getElementById('catalog-grid');
    
    if (!rows || rows.length === 0) {
      container.innerHTML = '<div class="empty-state">No se encontraron productos.</div>';
      return;
    }

    container.innerHTML = rows.map(r => `
      <div class="product-card">
        <h3>${r.producto}</h3>
        <div class="product-price">$${Number(r.precio).toFixed(2)}</div>
        <div class="product-stock">Disponibles: ${r.cantidad}</div>
        <button data-id="${r.id}" data-nombre="${r.producto}" data-precio="${r.precio}" class="add-btn">
          Agregar al Carrito
        </button>
      </div>`).join('');
      
    document.querySelectorAll('.add-btn').forEach(btn => {
      btn.addEventListener('click', () => addToCart(btn.dataset));
    });
  } catch (err) {
    console.error("Error al cargar catálogo:", err);
  }
}

function addToCart({ id, nombre, precio }) {
  const existing = cart.find(item => item.id === id);
  if (existing) {
    existing.cantidad += 1;
  } else {
    cart.push({ id, nombre, precio: Number(precio), cantidad: 1 });
  }
  renderCart();
}

function renderCart() {
  const list = document.getElementById('cart-items');
  if (cart.length === 0) {
    list.innerHTML = '<div class="empty-state">Tu carrito está vacío</div>';
  } else {
    list.innerHTML = cart.map(item =>
      `<li class="cart-item">
         <div>
           <span class="cart-item-name">${item.nombre}</span>
           <span class="cart-item-qty">x${item.cantidad}</span>
         </div>
         <span class="cart-item-price">$${(item.precio * item.cantidad).toFixed(2)}</span>
       </li>`
    ).join('');
  }
  const total = cart.reduce((sum, item) => sum + item.precio * item.cantidad, 0);
  document.getElementById('cart-total').textContent = `$${total.toFixed(2)}`;
}

document.getElementById('search-btn').addEventListener('click', () => {
  loadCatalog(document.getElementById('search-input').value);
});

document.getElementById('clear-search-btn').addEventListener('click', () => {
  document.getElementById('search-input').value = '';
  loadCatalog();
});

document.getElementById('checkout-btn').addEventListener('click', async () => {
  if (!authToken) {
    showMsg('Inicia sesión de invitado para poder pagar.', false);
    return;
  }
  if (cart.length === 0) {
    showMsg('El carrito está vacío.', false);
    return;
  }
  const items = cart.map(item => ({ id: item.id, cantidad: item.cantidad }));
  
  try {
    const res = await fetch('/api/public/orders', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${authToken}` },
      body: JSON.stringify({ items })
    });
    const data = await res.json();
    if (res.ok) {
      showMsg(`Pedido #${data.id} confirmado. Total: $${Number(data.total).toFixed(2)}`, true);
      cart = [];
      renderCart();
      loadCatalog();
      loadMyOrders();
    } else {
      showMsg(data.error || 'No se pudo procesar el pedido', false);
    }
  } catch (err) {
    showMsg('Error de red al procesar el pago', false);
  }
});

async function loadMyOrders() {
  if (!authToken) return;
  try {
    const res = await fetch('/api/public/orders/mine', {
      headers: { Authorization: `Bearer ${authToken}` }
    });
    const orders = await res.json();
    const body = document.getElementById('orders-body');
    
    if (!res.ok || !Array.isArray(orders) || orders.length === 0) {
      body.innerHTML = '<tr><td colspan="5" class="empty-state">Todavía no tienes pedidos.</td></tr>';
      document.getElementById('orders-status').style.display = 'none';
      return;
    }
    
    document.getElementById('orders-status').style.display = 'none';
    body.innerHTML = orders.map(order => {
      const items = order.items.map(it => `${it.cantidad}x ${it.producto}`).join('<br>');
      const fecha = new Date(order.creado_en).toLocaleString();
      return `<tr>
        <td>#${order.id}</td>
        <td>${fecha}</td>
        <td>${items}</td>
        <td style="color:var(--success); font-weight:600;">$${Number(order.total).toFixed(2)}</td>
        <td>${order.estado}</td>
      </tr>`;
    }).join('');
  } catch (err) {
    console.error("Error al cargar pedidos:", err);
  }
}

document.getElementById('register-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const username = document.getElementById('reg-user').value;
  const password = document.getElementById('reg-pass').value;
  try {
    const res = await fetch('/api/guest/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    showMsg(res.ok ? 'Cuenta creada, ya puedes iniciar sesión.' : data.error, res.ok);
    if(res.ok) {
        document.getElementById('register-form').reset();
    }
  } catch (err) {
    showMsg("Error de red", false);
  }
});

document.getElementById('login-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const username = document.getElementById('login-user').value;
  const password = document.getElementById('login-pass').value;
  try {
    const res = await fetch('/api/guest/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    if (res.ok) {
      authToken = data.token;
      document.getElementById('session-status').textContent = `Conectado como ${username}`;
      showMsg('Sesión iniciada.', true);
      document.getElementById('login-form').reset();
      loadMyOrders();
    } else {
      showMsg(data.error, false);
    }
  } catch(err) {
    showMsg("Error de red", false);
  }
});

// Init
loadCatalog();
renderCart();
