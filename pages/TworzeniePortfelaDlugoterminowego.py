import pandas as pd
import numpy as np
from scipy.stats import pearsonr
import os
import streamlit as st


# Load model results dynamically
future_values = pd.read_csv("Wyniki/Predykcje/DlugoTerminowe.csv")
historical_prices = pd.read_csv("Dane/companyValues.csv")

# Calculate future returns based on True Value and Mean Prediction
future_values['future_return'] = (
    (future_values['Mean Prediction'] - future_values['True Value']) / future_values['True Value']
)
future_values = future_values.dropna()

# Prepare historical data
historical_prices['datetime'] = pd.to_datetime(historical_prices['datetime'])
historical_prices = historical_prices.sort_values(by=['symbol', 'datetime'])

# Get the last 'open' value for each symbol
last_open_values = historical_prices.groupby('symbol').last()['open']

# Map the last 'open' value to future_values
future_values['last_open'] = future_values['Symbol'].map(last_open_values)

# Calculate the ratio between last 'open' and Mean Prediction
future_values['open_to_prediction_ratio'] = future_values['last_open'] / future_values['Mean Prediction']

# Diagnostyka danych wejściowych
print("\nDiagnostyka danych wejściowych:")
print(
    future_values[
        ['Symbol', 'True Value', 'Mean Prediction', 'future_return', 'last_open', 'open_to_prediction_ratio']
    ].head()
)

# Calculate daily returns
historical_prices['daily_return'] = historical_prices.groupby('symbol')['close'].pct_change()
historical_prices = historical_prices.dropna()

# Merge historical data with future values
merged_data = pd.merge(
    future_values,
    historical_prices,
    left_on='Symbol',
    right_on='symbol',
    how='inner'
)

# Check if daily_return contains variability
if merged_data['daily_return'].std() == 0:
    print("\nBłąd: Wszystkie wartości daily_return są zerowe. Sprawdź dane wejściowe.")
else:
    # Calculate pairwise correlations between symbols
    symbols = merged_data['Symbol'].unique()
    korelacje = {}
    for i, symbol1 in enumerate(symbols):
        for j, symbol2 in enumerate(symbols):
            if i < j:
                df1 = merged_data[merged_data['Symbol'] == symbol1]
                df2 = merged_data[merged_data['Symbol'] == symbol2]
                merged = pd.merge(
                    df1[['datetime', 'daily_return']],
                    df2[['datetime', 'daily_return']],
                    on='datetime',
                    suffixes=(f'_{symbol1}', f'_{symbol2}')
                )
                if len(merged) > 1:
                    try:
                        corr, _ = pearsonr(merged[f'daily_return_{symbol1}'], merged[f'daily_return_{symbol2}'])
                        korelacje[f"{symbol1}-{symbol2}"] = corr
                    except ValueError:
                        korelacje[f"{symbol1}-{symbol2}"] = 1.0  # Default to uncorrelated
                else:
                    korelacje[f"{symbol1}-{symbol2}"] = 1.0  # Default to uncorrelated

    # Print correlations
    print("Obliczona Korelacja:")
    for pair, value in korelacje.items():
        print(f"{pair}: {value:.2f}" if value is not None else f"{pair}: N/A")

    # Calculate Sharpe ratios, risks, and standard deviations
    r_f = 0.02  # Annualized risk-free rate
    sharpe_ratios = {}
    risks = {}
    std_devs = {}
    for symbol in symbols:
        df = merged_data[merged_data['Symbol'] == symbol]
        mean_return = df['daily_return'].mean()
        std_dev = df['daily_return'].std()
        if std_dev > 0:
            sharpe_ratios[symbol] = (mean_return - r_f / 252) / std_dev
            risks[symbol] = std_dev ** 2  # Variance
            std_devs[symbol] = std_dev
        else:
            sharpe_ratios[symbol] = np.nan
            risks[symbol] = 0
            std_devs[symbol] = 0

    # Print Sharpe ratios and risks
    print("\nWskaźniki Sharpe'a:")
    for symbol, value in sharpe_ratios.items():
        print(f"{symbol}: {value:.2f}")

    print("\nRyzyko:")
    for symbol, value in risks.items():
        print(f"{symbol}: {value:.2e}")

    print("\nOdchylenie Standardowe:")
    for symbol, value in std_devs.items():
        print(f"{symbol}: {value:.4f}")

    # Define function for average absolute correlation
    def avg_abs_correlation_with_others(candidate, portfolio):
        correlations = []
        for existing in portfolio:
            key1 = f"{candidate}-{existing}"
            key2 = f"{existing}-{candidate}"
            if key1 in korelacje and korelacje[key1] is not None:
                correlations.append(abs(korelacje[key1]))
            elif key2 in korelacje and korelacje[key2] is not None:
                correlations.append(abs(korelacje[key2]))
        return np.mean(correlations) if correlations else 0.0

    # Portfolio construction
    portfolio = []
    remaining_symbols = list(sharpe_ratios.keys())

    # Start with the symbol with the highest combined score (Sharpe ratio * ratio)
    if remaining_symbols:
        best_symbol = max(
            remaining_symbols,
            key=lambda x: sharpe_ratios[x] * future_values.loc[future_values['Symbol'] == x, 'open_to_prediction_ratio'].iloc[0]
            if not np.isnan(sharpe_ratios[x]) else -np.inf
        )
        portfolio.append(best_symbol)
        remaining_symbols.remove(best_symbol)

    # Add additional symbols to the portfolio, minimizing correlation while considering the ratio
    while remaining_symbols:
        next_symbol = min(
            remaining_symbols,
            key=lambda x: avg_abs_correlation_with_others(x, portfolio) / future_values.loc[future_values['Symbol'] == x, 'open_to_prediction_ratio'].iloc[0]
        )
        portfolio.append(next_symbol)
        remaining_symbols.remove(next_symbol)

    # Create DataFrame with portfolio results
    portfolio_results = []
    for i, sym in enumerate(portfolio, start=1):
        avg_corr_value = avg_abs_correlation_with_others(sym, portfolio)
        value_ratio = future_values.loc[future_values['Symbol'] == sym, 'open_to_prediction_ratio'].iloc[0]

        portfolio_results.append({
            "Rank": i,
            "Symbol": sym,
            "Sharpe": round(sharpe_ratios[sym], 3),
            "Avg Correlation": round(avg_corr_value, 3),
            "Value Ratio": round(value_ratio, 3),
            "Risk": risks[sym],
            "Standard Deviation": round(std_devs[sym], 4)
        })

    # Save to CSV
    portfolio_df = pd.DataFrame(portfolio_results)
    portfolio_df.to_csv("Wyniki/Portfele/DlugoTerminowe.csv", index=False)
    print("\n Wyniki Zapisane Do Pliku\n'")

st.set_page_config(page_title="Portfel Długo Terminowy", layout="wide")

# Funkcja do wczytania CSV
def load_csv(file_path):
    try:
        if os.path.exists(file_path):
            return pd.read_csv(file_path)
        else:
            st.warning(f"Plik {file_path} nie istnieje. Tworzę nowy plik.")
            return pd.DataFrame({"Kolumna1": [], "Kolumna2": []})
    except Exception as e:
        st.error(f"Błąd podczas wczytywania pliku: {e}")
        return pd.DataFrame()

# Ścieżka do pliku CSV
file_path = "Wyniki/Portfele/DlugoTerminowe.csv"

# Nagłówek aplikacji
st.title("Portfel Długo Terminowy")

# Wczytaj dane z pliku CSV
df = load_csv(file_path)

edited_df = st.dataframe(df)