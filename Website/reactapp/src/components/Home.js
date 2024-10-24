import React from 'react';
import { useNavigate } from 'react-router-dom';

function Home() {
  const navigate = useNavigate();

  const handleLogout = () => {
    navigate('/');
  };

  return (
    <div>
      <nav className="navigation-bar">
        <button onClick={() => navigate('/inwestuj')} className="nav-button">Inwestuj</button>
        <button onClick={() => navigate('/moj-portfel')} className="nav-button">Mój portfel</button>
        <button onClick={handleLogout} className="nav-button">Wyloguj</button>
      </nav>
    </div>
  );
}

export default Home;
