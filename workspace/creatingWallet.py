import pandas as pd
import numpy as np
from scipy.stats import pearsonr
import matplotlib.pyplot as plt

# Wczytanie danych z plików CSV
model_results = pd.read_csv("model_results.csv")
company_values = pd.read_csv("workspace/companyValues.csv")
# Filtruj spółki tylko dla tych, które występują w model_results
symbols = model_results['symbol'].unique()
filtered_data = company_values[company_values['symbol'].isin(symbols)]

# Obliczanie dziennych zwrotów dla każdej spółki
filtered_data['daily_return'] = (
    filtered_data.groupby('symbol')['close'].pct_change()
)
filtered_data = filtered_data.dropna()

# Obliczanie korelacji pomiędzy wszystkimi spółkami
korelacje = {}
for i, symbol1 in enumerate(symbols):
    for j, symbol2 in enumerate(symbols):
        if i < j:  # Aby uniknąć powtarzania i porównywania spółki z samą sobą
            df1 = filtered_data[filtered_data['symbol'] == symbol1]
            df2 = filtered_data[filtered_data['symbol'] == symbol2]
            # Sprawdzenie, czy obie serie mają wystarczającą liczbę punktów
            if len(df1['daily_return']) > 1 and len(df2['daily_return']) > 1:
                corr, _ = pearsonr(df1['daily_return'], df2['daily_return'])
                # Zapis w jednym kierunku
                korelacje[f"{symbol1}-{symbol2}"] = corr
                # Jeśli chcesz mieć ułatwione odczytywanie w obu kierunkach,
                # można dopisać również:
                # korelacje[f"{symbol2}-{symbol1}"] = corr
            else:
                korelacje[f"{symbol1}-{symbol2}"] = None  # Brak wystarczających danych

print("Obliczona Korelacja:")
for pair, value in korelacje.items():
    if value is not None:
        print(f"{pair}: {value:.2f}")
    else:
        print(f"{pair}: N/A (brak danych)")

# Obliczanie wskaźnika Sharpe'a oraz ryzyka
# Zakładamy stopę wolną od ryzyka r_f (np. 2%)
r_f = 0.02
sharpe_ratios = {}
ryzyko = {}
odchylenie = {}
for symbol in symbols:
    df = filtered_data[filtered_data['symbol'] == symbol]
    mean_return = df['daily_return'].mean()
    std_dev = df['daily_return'].std(ddof=1)
    odchylenie[symbol] = std_dev

    # Zabezpieczenie przed dzieleniem przez zero:
    if std_dev == 0 or np.isnan(std_dev):
        sharpe_ratios[symbol] = np.nan
    else:
        # Uproszczone obliczanie Sharpe'a:
        sharpe_ratios[symbol] = (mean_return - r_f / 252) / std_dev

    # Ryzyko (wariancja zwrotów)
    risk = df['daily_return'].var(ddof=1)
    ryzyko[symbol] = risk if not np.isnan(risk) else 0.0

print("\nWskaźniki Sharpe'a:")
for symbol, s_val in sharpe_ratios.items():
    print(f"{symbol}: {s_val:.2f}")

print("\nRyzyko:")
for symbol, risk_val in ryzyko.items():
    print(f"{symbol}: {risk_val:.2e}")

print("\nOdchylenie Standardowe:")
for symbol, odch in odchylenie.items():
    if odch is not None:
        print(f"{symbol}: {odch:.4f}")
    else:
        print(f"{symbol}: brak danych")

# --- Budowa portfela ---
symbols_list = list(symbols)
portfolio = []

# Usuwamy spółki, które mają Sharpe = NaN lub inf
symbols_list = [s for s in symbols_list if not np.isnan(sharpe_ratios[s])]

if not symbols_list:
    print("Brak spółek z poprawnym Sharpe’em!")
else:
    # Wybierz spółkę o najwyższym Sharpe
    first_choice = max(symbols_list, key=lambda s: sharpe_ratios[s])
    portfolio.append(first_choice)
    symbols_list.remove(first_choice)

    # Definiujemy funkcję, która dla danej spółki liczy "neutralność"
    # względem już wybranego portfela (średnia bezwzględna korelacja)
    def avg_abs_correlation_with_portfolio(sym):
        corrs = []
        for p_sym in portfolio:
            pair_corr = None
            # Sprawdź kierunek klucza
            if f"{sym}-{p_sym}" in korelacje:
                pair_corr = korelacje[f"{sym}-{p_sym}"]
            elif f"{p_sym}-{sym}" in korelacje:
                pair_corr = korelacje[f"{p_sym}-{sym}"]
            if pair_corr is not None:
                corrs.append(abs(pair_corr))
        if len(corrs) == 0:
            return 1.0
        return np.mean(corrs)

    min_sharpe = min(sharpe_ratios[s] for s in symbols_list + [first_choice] if not np.isnan(sharpe_ratios[s]))
    max_sharpe = max(sharpe_ratios[s] for s in symbols_list + [first_choice] if not np.isnan(sharpe_ratios[s]))

    def combined_score(sym):
        # Normalizacja Sharpe do [0,1]:
        if max_sharpe == min_sharpe:
            norm_sharpe = 1.0
        else:
            norm_sharpe = (sharpe_ratios[sym] - min_sharpe) / (max_sharpe - min_sharpe)

        avg_corr = avg_abs_correlation_with_portfolio(sym)
        neutral = 1 - avg_corr  # w [0,1], im bliżej 1, tym spółka mniej skorelowana

        # Połowa wagi Sharpe, połowa wagi neutralności
        return 0.5 * norm_sharpe + 0.5 * neutral

    # Krok 2 i kolejne:
    while symbols_list:
        next_symbol = max(symbols_list, key=combined_score)
        portfolio.append(next_symbol)
        symbols_list.remove(next_symbol)

    # Funkcja, która liczy średnią |korelację| spółki 'sym'
    # z pozostałymi spółkami w *pełnym* (docelowym) portfelu
    def avg_abs_correlation_with_others(sym, portfolio_symbols):
        corrs = []
        for p_sym in portfolio_symbols:
            if p_sym == sym:
                continue
            # Klucz korelacji może być w obu kierunkach
            if f"{sym}-{p_sym}" in korelacje:
                pair_corr = korelacje[f"{sym}-{p_sym}"]
            elif f"{p_sym}-{sym}" in korelacje:
                pair_corr = korelacje[f"{p_sym}-{sym}"]
            else:
                pair_corr = None

            if pair_corr is not None:
                corrs.append(abs(pair_corr))
        if not corrs:
            return None
        return np.mean(corrs)

    # Wyświetl gotowy portfel
    print("\nKOLEJNOŚĆ BUDOWY PORTFELA:")
    for i, sym in enumerate(portfolio, start=1):
        # Obliczamy średnią wartość bezwzględnej korelacji spółki 'sym'
        # z pozostałymi spółkami w portfelu
        avg_corr_value = avg_abs_correlation_with_others(sym, portfolio)
        if avg_corr_value is None:
            avg_corr_str = "brak danych"
        else:
            avg_corr_str = f"{avg_corr_value:.3f}"

        print(
            f"{i}. {sym} | Sharpe: {sharpe_ratios[sym]:.3f}"
            f" | Korelacja z pozostalymi Aktywami: {avg_corr_str}"
        )
