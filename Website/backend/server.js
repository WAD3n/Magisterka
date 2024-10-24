const express = require('express');
const sql = require('mssql');
const cors = require('cors');

const app = express();
app.use(cors());  // Pozwól na połączenia z różnych domen

// Konfiguracja połączenia z SQL Server
const config = {
    user: '123',  // Nazwa użytkownika SQL Server
    password: 'asdffdsa25531',            // Hasło użytkownika SQL Server
    server: 'localhost',               // Lub DESKTOP-911JPPP, jeśli to nazwa Twojego serwera
    database: 'magisterka',
    options: {
        encrypt: false,                // Ustaw na true, jeśli używasz szyfrowania
        enableArithAbort: true,
        port: 1433                     // Upewnij się, że SQL Server nasłuchuje na tym porcie
    }
};

// Endpoint do pobierania danych z tabeli prediction
app.get('/predictions', async (req, res) => {
  try {
    let pool = await sql.connect(config);
    let result = await pool.request().query('SELECT * FROM dbo.predictions');
    res.json(result.recordset);  // Zwróć dane w formacie JSON
  } catch (err) {
    res.status(500).send(err.message);
  }
});

// Uruchomienie serwera
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Serwer działa na porcie ${PORT}`);
});
