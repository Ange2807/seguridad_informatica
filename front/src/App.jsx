import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import AuthModal from './components/AuthModal';
import Catalog from './components/Catalog';
import Cart from './components/Cart';

function App() {
  const [user, setUser] = useState(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [showCart, setShowCart] = useState(false);
  const [cart, setCart] = useState([]);

  useEffect(() => {
    // Check if token exists on load
    const token = localStorage.getItem('jwt_token');
    if (token) {
      // Decode token properly in a real app, for now just set a dummy user state
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        setUser({ username: payload.sub });
      } catch (e) {
        localStorage.removeItem('jwt_token');
      }
    }
  }, []);

  const handleLoginSuccess = (userData) => {
    setUser(userData);
    setShowAuthModal(false);
  };

  const handleLogout = () => {
    localStorage.removeItem('jwt_token');
    setUser(null);
  };

  const addToCart = (item) => {
    setCart([...cart, item]);
  };

  return (
    <div>
      <Navbar 
        user={user} 
        onOpenAuth={() => setShowAuthModal(true)} 
        onLogout={handleLogout} 
        onToggleCart={() => setShowCart(!showCart)}
        cartCount={cart.length}
      />
      
      <main>
        <Catalog onAddToCart={addToCart} />
      </main>

      {showAuthModal && (
        <AuthModal 
          onClose={() => setShowAuthModal(false)} 
          onLoginSuccess={handleLoginSuccess}
        />
      )}

      {showCart && (
        <Cart 
          cart={cart}
          onUpdateCart={setCart}
          onClose={() => setShowCart(false)}
          user={user}
        />
      )}
    </div>
  );
}

export default App;
