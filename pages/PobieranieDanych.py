import pandas as pd
import streamlit as st
import matplotlib as plt
from tvDatafeed import TvDatafeed as tv, Interval
import os
# Correct file path with raw string
file = r'Dane\companies_symbol.csv'

# Load CSV file
try:
    df = pd.read_csv(file)
    companySymbols = df[['symbol', 'trademark']]
except FileNotFoundError:
    print(f"Error: File {file} not found.")
    exit()

# Initialize TradingView instance
username = "hubert_gluchowski"
password = "zaqwsxCDE3!@#$"
try:
    tradingViewInstance = tv(username, password)
    print("Connection Successful")
except Exception as error:
    print(f"Error: Could not connect to TradingView. {error}")
    exit()

companyValues = []

# Fetch data for each company symbol
for index, row in companySymbols.iterrows():
    element = row['symbol']
    trademark = row['trademark']
    try:
        output = tradingViewInstance.get_hist(
            symbol=element, 
            exchange=f"{trademark}", 
            interval=Interval.in_daily, 
            n_bars=31
        )
        companyValues.append(output)
        print(f"Data retrieved for {element}: {output.shape if output is not None else 'No data'}")
    except Exception as error:
        print(f"Failed to retrieve data for {element}: {error}")

# Save data if available
if companyValues:
    try:
        # Concatenate all data and reset the index to include the timestamp as a column
        companyValues = pd.concat(companyValues).reset_index()  # reset_index includes 'datetime' as a column
        companyValues.to_csv('Dane\companyValues.csv', index=False)
        print("Successfully created Data Frame with timestamp")
    except Exception as error:
        print(f"Error while saving data: {error}")
else:
    print("Creating Data Frame: unsuccessful")


# Funkcja do wczytania danych z pliku CSV
def load_csv(file_path):
    try:
        return pd.read_csv(file_path, parse_dates=["datetime"])
    except FileNotFoundError:
        st.error(f"Plik {file_path} nie istnieje.")
        return pd.DataFrame()

# Ścieżka do pliku CSV
file_path = "Dane/companyValues.csv"

# Wczytaj dane
df = load_csv(file_path)

if not df.empty:
    # Filtruj dane po symbolu akcji
    symbols = df['symbol'].unique()
    selected_symbol = st.selectbox("Wybierz symbol akcji", symbols)

    # Filtrowanie po symbolu
    filtered_data = df[df['symbol'] == selected_symbol]

    # Wybierz kolumnę do rysowania wykresu
    column_to_plot = st.selectbox(
        "Wybierz kolumnę do wykresu",
        ["open", "high", "low", "close", "volume"]
    )

    # Rysuj wykres
    st.line_chart(filtered_data.set_index('datetime')[column_to_plot])
else:
    st.warning("Brak danych do wyświetlenia. Upewnij się, że plik CSV istnieje i zawiera dane.")