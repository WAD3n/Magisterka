import React from 'react';
import { useNavigate } from 'react-router-dom';

function Inwestuj() {
  const navigate = useNavigate();

  return (
    <div className='header'>
     <h1>Inwestuj</h1>
      <button onClick={() => navigate('/home')} className='nav-button'>Home</button>
      </div>
  );
}

export default Inwestuj;
