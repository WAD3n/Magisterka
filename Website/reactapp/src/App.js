import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Login from './components/Login';
import Home from './components/Home';
import Inwestuj from './components/Inwestuj';
import MojPortfel from './components/MojPortfel';
import './App.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/home" element={<Home />} />
        <Route path="/inwestuj" element={<Inwestuj />} />
        <Route path="/moj-portfel" element={<MojPortfel />} />
      </Routes>
    </Router>
  );
}

export default App;
