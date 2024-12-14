const express = require('express');
const sql = require('mssql');
const cors = require('cors');

const app = express();
app.use(cors());  

// Konfiguracja połączenia z SQL Server
const config = {
    user: '123',  
    password: 'asdffdsa25531',            
    server: 'localhost',               
    database: 'magisterka',
    options: {
        encrypt: false,               
        enableArithAbort: true,
        port: 1433                     
    }
};

// Endpoint do pobierania danych z tabeli prediction
app.get('/predictions', async (req, res) => {
  try {
    let pool = await sql.connect(config);
    let result = await pool.request().query('SELECT * FROM dbo.predictions');
    res.json(result.recordset);
  } catch (err) {
    res.status(500).send(err.message);
  }
});
app.get('/User', async (req, res) => {
  try {
    let pool = await sql.connect(config);
    let result = await pool.request().query('SELECT * FROM dbo.User');
    res.json(result.recordset);
  } catch (err) {
    res.status(500).send(err.message);
  }
});
// Uruchomienie serwera
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Serwer działa na porcie ${PORT}`);
});
