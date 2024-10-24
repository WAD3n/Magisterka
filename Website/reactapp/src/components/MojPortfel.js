import React from 'react';
import { useNavigate } from 'react-router-dom';

function MojPortfel() {
  const navigate = useNavigate();

  return (
    <div className='header'>
      <h2>Mój portfel</h2>
      <button onClick={() => navigate('/home')} className='nav-button'>Home</button>
    </div>
  );
}

export default MojPortfel;
