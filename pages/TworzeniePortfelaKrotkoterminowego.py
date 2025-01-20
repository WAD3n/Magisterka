import pandas as pd
import numpy as np
from scipy.stats import pearsonr
import os
import streamlit as st

# Wczytanie danych z plików CSV
model_results = pd.read_csv("Wyniki/Predykcje/KrotkoTerminowa.csv")
company_values = pd.read_csv("Dane/companyValues.csv")

# Obliczenie proporcji futureValue / actualValue i dodanie do model_results
model_results['value_ratio'] = model_results['futureValue'] / model_results['actualValue']

# Filtruj dane spółek zgodnie z wartościami w kolumnie 'index'
symbols = model_results['index'].unique()
filtered_data = company_values[company_values['symbol'].isin(symbols)]

# Obliczanie dziennych zwrotów
filtered_data['daily_return'] = filtered_data.groupby('symbol')['close'].pct_change()
filtered_data = filtered_data.dropna()

# Obliczanie korelacji między spółkami
korelacje = {}
for i, symbol1 in enumerate(symbols):
    for j, symbol2 in enumerate(symbols):
        if i < j:
            df1 = filtered_data[filtered_data['symbol'] == symbol1]
            df2 = filtered_data[filtered_data['symbol'] == symbol2]
            if len(df1['daily_return']) > 1 and len(df2['daily_return']) > 1:
                corr, _ = pearsonr(df1['daily_return'], df2['daily_return'])
                korelacje[f"{symbol1}-{symbol2}"] = corr
            else:
                korelacje[f"{symbol1}-{symbol2}"] = None

# Obliczanie wskaźników Sharpe'a, ryzyka i odchylenia standardowego
r_f = 0.02  # stopa wolna od ryzyka
sharpe_ratios = {}
ryzyko = {}
odchylenie = {}

for symbol in symbols:
    df = filtered_data[filtered_data['symbol'] == symbol]
    mean_return = df['daily_return'].mean()
    std_dev = df['daily_return'].std(ddof=1)
    odchylenie[symbol] = std_dev

    if std_dev == 0 or np.isnan(std_dev):
        sharpe_ratios[symbol] = np.nan
    else:
        sharpe_ratios[symbol] = (mean_return - r_f / 252) / std_dev

    ryzyko[symbol] = df['daily_return'].var(ddof=1) if not np.isnan(std_dev) else 0.0

# Normalizacja value_ratio
value_ratios = model_results.set_index('index')['value_ratio']
min_ratio = value_ratios.min()
max_ratio = value_ratios.max()

def normalized_value_ratio(sym):
    ratio = value_ratios.get(sym, np.nan)
    if np.isnan(ratio):
        return 0.0
    return 1.0 if max_ratio == min_ratio else (ratio - min_ratio) / (max_ratio - min_ratio)

# --- Budowa portfela ---
symbols_list = [s for s in symbols if not np.isnan(sharpe_ratios[s])]
portfolio = []

if symbols_list:
    # Wybór pierwszej spółki o najwyższym Sharpe
    first_choice = max(symbols_list, key=lambda s: sharpe_ratios[s])
    portfolio.append(first_choice)
    symbols_list.remove(first_choice)

    def avg_abs_correlation_with_portfolio(sym):
        corrs = []
        for p_sym in portfolio:
            if f"{sym}-{p_sym}" in korelacje:
                corrs.append(abs(korelacje[f"{sym}-{p_sym}"]))
            elif f"{p_sym}-{sym}" in korelacje:
                corrs.append(abs(korelacje[f"{p_sym}-{sym}"]))
        return np.mean(corrs) if corrs else 1.0

    min_sharpe = min(sharpe_ratios[s] for s in symbols_list + [first_choice] if not np.isnan(sharpe_ratios[s]))
    max_sharpe = max(sharpe_ratios[s] for s in symbols_list + [first_choice] if not np.isnan(sharpe_ratios[s]))

    # Zaktualizowana funkcja combined_score
    def combined_score(sym):
        norm_sharpe = 1.0 if max_sharpe == min_sharpe else (sharpe_ratios[sym] - min_sharpe) / (max_sharpe - min_sharpe)
        norm_ratio = normalized_value_ratio(sym)
        neutral = 1 - avg_abs_correlation_with_portfolio(sym)
        # Kombinacja wskaźników z wagami
        return 0.4 * norm_sharpe + 0.4 * norm_ratio + 0.2 * neutral

    while symbols_list:
        next_symbol = max(symbols_list, key=combined_score)
        portfolio.append(next_symbol)
        symbols_list.remove(next_symbol)

    def avg_abs_correlation_with_others(sym, portfolio_symbols):
        corrs = []
        for p_sym in portfolio_symbols:
            if p_sym == sym:
                continue
            if f"{sym}-{p_sym}" in korelacje:
                corrs.append(abs(korelacje[f"{sym}-{p_sym}"]))
            elif f"{p_sym}-{sym}" in korelacje:
                corrs.append(abs(korelacje[f"{p_sym}-{sym}"]))
        return np.mean(corrs) if corrs else None

    # Tworzenie DataFrame z wynikami
    portfolio_results = []
    for i, sym in enumerate(portfolio, start=1):
        avg_corr_value = avg_abs_correlation_with_others(sym, portfolio)
        avg_corr_str = f"{avg_corr_value:.3f}" if avg_corr_value is not None else "brak danych"

        value_ratio = model_results.loc[model_results['index'] == sym, 'value_ratio'].values[0]
        value_ratio_str = f"{value_ratio:.3f}" if not np.isnan(value_ratio) else "brak danych"

        portfolio_results.append({
            "Rank": i,
            "Symbol": sym,
            "Sharpe": round(sharpe_ratios[sym], 3),
            "Avg Correlation": avg_corr_value,
            "Value Ratio": value_ratio,
            "Risk": ryzyko[sym],
            "Standard Deviation": round(odchylenie[sym], 4)
        })

    # Zapis do pliku CSV
    portfolio_df = pd.DataFrame(portfolio_results)
    portfolio_df.to_csv("Wyniki/Portfele/KrotkoTerminowy.csv", index=False)

    print("\nKOLEJNOŚĆ BUDOWY PORTFELA zapisana do pliku")

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
file_path = "Wyniki/Portfele/KrotkoTerminowy.csv"

# Nagłówek aplikacji
st.title("Portfel Krótko Terminowy")

# Wczytaj dane z pliku CSV
df = load_csv(file_path)

edited_df = st.dataframe(df)