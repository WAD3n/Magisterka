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
filtered_data['daily_return'] = filtered_data.groupby('symbol')['close'].pct_change()
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
                korelacje[f"{symbol1}-{symbol2}"] = corr
            else:
                korelacje[f"{symbol1}-{symbol2}"] = None  # Brak wystarczających danych

print("Korelacje:")
for pair, value in korelacje.items():
    if value is not None:
        print(f"{pair}: {value:.2f}")
    else:
        print(f"{pair}: N/A (brak danych)")

# Obliczanie wskaźnika Sharpe'a oraz ryzyka dla każdej spółki z companyValues.csv
# Zakładamy stopę wolną od ryzyka r_f (np. 2%)
r_f = 0.02
sharpe_ratios = {}
ryzyko = {}

for symbol in symbols:
    df = filtered_data[filtered_data['symbol'] == symbol]
    # Średnia dzienna stopa zwrotu i odchylenie standardowe
    mean_return = np.mean(df['daily_return'])
    std_dev = np.std(df['daily_return'])

    # Oblicz wskaźnik Sharpe'a
    sharpe_ratio = (mean_return - r_f / 252) / std_dev
    sharpe_ratios[symbol] = sharpe_ratio

    # Ryzyko (wariancja zwrotów)
    risk = np.var(df['daily_return'])
    ryzyko[symbol] = risk

print("\nWskaźniki Sharpe'a:")
for symbol, sharpe in sharpe_ratios.items():
    print(f"{symbol}: {sharpe:.2f}")

print("\nRyzyko:")
for symbol, risk in ryzyko.items():
    print(f"{symbol}: {risk:.2e}")

# Obliczanie wskaźnika Sharpe'a i ryzyka dla futureValue z model_results.csv
model_results['return'] = (model_results['futureValue'] - model_results['actualValue']) / model_results['actualValue']

# Ryzyko i Sharpe na podstawie futureValue
future_sharpe_ratios = {}
future_ryzyko = {}

for symbol in symbols:
    df = model_results[model_results['symbol'] == symbol]
    # Średni zwrot prognozy i odchylenie standardowe
    mean_return = np.mean(df['return'])
    std_dev = np.std(df['return'])

    # Oblicz wskaźnik Sharpe'a
    sharpe_ratio = (mean_return - r_f / 252) / std_dev
    future_sharpe_ratios[symbol] = sharpe_ratio

    # Ryzyko (wariancja zwrotów prognoz)
    risk = np.var(df['return'])
    future_ryzyko[symbol] = risk

print("\nWskaźniki Sharpe'a (futureValue):")
for symbol, sharpe in future_sharpe_ratios.items():
    print(f"{symbol}: {sharpe:.2f}")

print("\nRyzyko (futureValue):")
for symbol, risk in future_ryzyko.items():
    print(f"{symbol}: {risk:.2e}")

# Wizualizacja: Efektywność (risk vs mean return) - Efektywna granica Markowitza
mean_returns = [np.mean(filtered_data[filtered_data['symbol'] == symbol]['daily_return']) for symbol in symbols]
risks = [ryzyko[symbol] for symbol in symbols]

plt.figure(figsize=(10, 6))
plt.scatter(risks, mean_returns, c='blue', label='Spółki')
for i, symbol in enumerate(symbols):
    plt.text(risks[i], mean_returns[i], symbol)

plt.title('Efektywna granica Markowitza')
plt.xlabel('Ryzyko (wariancja zwrotów)')
plt.ylabel('Średni dzienny zwrot')
plt.grid(True)
plt.legend()
plt.show()
