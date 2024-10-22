import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Login</h1>
        <div className="login-container">
          <input
            type="text"
            className="login-input"
            placeholder="Username"
          />
          <input
            type="password"
            className="login-input"
            placeholder="Password"
          />
          <button className="login-button">Submit</button>
        </div>
      </header>
    </div>
  );
}

export default App;
