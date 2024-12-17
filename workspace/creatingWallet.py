import pandas as pd
import numpy as np
from scipy.stats import pearsonr
import matplotlib.pyplot as plt

# Wczytanie danych z plików CSV
model_results = pd.read_csv("model_results.csv")
company_values = pd.read_csv("workspace/companyValues.csv")

# Filtruj spółki tylko dla tych, które występują w model_results
symbols = model_results['symbol'].unique()

# Dodaj przzedrostek NASDAQ
symbols = ["NASDAQ:" + _ for _ in symbols]
print(symbols)
filtered_data = company_values[company_values['symbol'].isin(symbols)]

# Obliczanie dziennych zwrotów dla każdej spółki
filtered_data['daily_return'] = filtered_data.groupby('symbol')['close'].pct_change()
filtered_data = filtered_data.dropna()

print(filtered_data)

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

print("Obliczona Korelacja:")
print(korelacje.keys())
print(korelacje.values())

for pair, value in korelacje.items():
    if value is not None:
        print(f"{pair}: {value:.2f}")
    else:
        print(f"{pair}: N/A (brak danych)")

#Dodać Zapis Korealcji Do Pliku

# Obliczanie wskaźnika Sharpe'a oraz ryzyka dla każdej spółki z companyValues.csv
# Zakładamy stopę wolną od ryzyka r_f (np. 2%)
r_f = 0.02
sharpe_ratios = {}
ryzyko = {}
odchylenie = {}

for symbol in symbols:
    df = filtered_data[filtered_data['symbol'] == symbol]
    # Średnia dzienna stopa zwrotu i odchylenie standardowe
    mean_return = np.mean(df['daily_return'])
    std_dev = np.std(df['daily_return'])
    odchylenie[symbol] = std_dev

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

print("\nOdchylenie Standardowe:")
for symbol, odchylenie in odchylenie.items():
    print(f"{symbol}: {odchylenie:.4f}")

# Obliczanie wskaźnika Sharpe'a i ryzyka dla futureValue z model_results.csv
model_results['return'] = (model_results['futureValue'] - model_results['actualValue']) / model_results['actualValue']

print(model_results)


# Wizualizacja: Efektywność (risk vs mean return) - Efektywna granica Markowitza
mean_returns = [np.mean(filtered_data[filtered_data['symbol'] == symbol]['daily_return']) for symbol in symbols]
risks = [ryzyko[symbol] for symbol in symbols]


print(model_results['return'])


plt.figure(figsize=(10, 6))
plt.scatter(risks,model_results['return'],c='red',label="Predykcja")
plt.scatter(risks, mean_returns, c='blue', label='Aktualna')
for i, symbol in enumerate(symbols):
    symbol = symbol.split('NASDAQ:')
    plt.text(risks[i], mean_returns[i], symbol[1])

plt.title('Efektywna granica Markowitza')
plt.xlabel('Ryzyko (wariancja zwrotów)')
plt.ylabel('Średni dzienny zwrot')
plt.grid(True)
plt.legend()
plt.show()
