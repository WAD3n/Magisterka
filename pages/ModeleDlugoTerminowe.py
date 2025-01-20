import pandas as pd
import numpy as np
import xgboost as xgb
import streamlit as st
import matplotlib as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split
import os


output_file = "Wyniki/Predykcje/DlugoTerminowe.csv"
    # Append to the file
file_exists = os.path.isfile(output_file)
if file_exists:
    os.remove(output_file)

if not os.path.isfile(output_file):
    header_data = {
        "Symbol": [],
        "True Value": [],
        "Mean Prediction": [],
        "RMSE": [],
        "MSE": [],
        "SMAPE": [],
        "MAPE": [],
        "Huber Loss": []
    }
    df_header = pd.DataFrame(header_data)
    df_header.to_csv(output_file, index=False)
# Wagi dla metryk
weights = {
    "rmse": 0.2,
    "mse": 0.2,
    "smape": 0.2,
    "mape": 0.2,
    "huber_loss": 0.2
}

# Funkcje metryk
def rmse(actual, predicted):
    return np.sqrt(np.mean((np.array(actual) - np.array(predicted))**2))

def mse(actual, predicted):
    return np.mean((np.array(actual) - np.array(predicted))**2)

def smape(actual, predicted):
    actual, predicted = np.array(actual), np.array(predicted)
    return 100 * np.mean(2 * np.abs(actual - predicted) / (np.abs(actual) + np.abs(predicted)))

def mape(actual, predicted):
    actual, predicted = np.array(actual), np.array(predicted)
    return 100 * np.mean(np.abs((actual - predicted) / actual))



def huber_loss(actual, predicted, delta=1):
    actual, predicted = np.array(actual), np.array(predicted)
    residual = actual - predicted
    condition = np.abs(residual) <= delta
    huber = np.where(condition, 0.5 * residual**2, delta * np.abs(residual) - 0.5 * delta**2)
    return np.mean(huber)

# Wczytanie danych
df = pd.read_csv("Dane/companyValues.csv")
df = df.set_index('datetime')
df.index = pd.to_datetime(df.index)

# Usunięcie zbędnych kolumn
columns = ['high', 'low', 'close', 'volume']
df = df.drop(columns=columns)

# Liczba lagów na podstawie liczby wierszy dla jednego symbolu
num_lags = df[df['symbol'] == df['symbol'].iloc[0]].shape[0] // 2

# Dodanie lagów
for lag in range(1, num_lags + 1):
    df[f'lag_{lag}'] = df.groupby('symbol')['open'].shift(lag)

# Usunięcie braków
df = df.dropna()

# Lista cech i celu
FEATURES = ['open'] + [f'lag_{i}' for i in range(1, num_lags + 1)]
TARGET = ['open']

# Przetwarzanie dla każdego symbolu
symbols = df['symbol'].unique()
for symbol in symbols:
    print(f"Training for symbol: {symbol}")
    
    # Filtrowanie danych dla symbolu
    Filtered = df[df['symbol'] == symbol].drop(columns='symbol')
    
    # Podział na zbiory
    train, test = train_test_split(Filtered, test_size=0.3, shuffle=False)
    X_train = train[FEATURES]
    Y_train = train[TARGET]
    X_test = test[FEATURES]
    Y_test = test[TARGET]

    # Przechowywanie wyników
    predictionsXGB = []
    predictions_rf = []
    predictions_mlp = []
    true_values = []

    # Iteracyjne trenowanie modeli z przesuwanym oknem
    for i in range(len(X_test)):
        first_index = X_test.index.min()

        # Inicjalizacja modeli
        regXGB = xgb.XGBRegressor(
            n_estimators=1000,
            eval_metric="rmse",
            verbosity=0,
            learning_rate=0.1,
            reg_alpha=1,
            reg_lambda=1
        )
        regRF = RandomForestRegressor(
            n_estimators=100,
            random_state=42,
            n_jobs=-1
        )
        regMLP = MLPRegressor(
            hidden_layer_sizes=(10, 5),
            max_iter=500,
            random_state=42
        )

        # Trenowanie modeli na oknie
        regXGB.fit(X_train, Y_train)
        regRF.fit(X_train, Y_train.values.ravel())
        regMLP.fit(X_train, Y_train.values.ravel())

        # Prognozowanie za pomocą modeli
        pred_xgb = regXGB.predict(X_test.loc[[first_index]])[0]
        pred_rf = regRF.predict(X_test.loc[[first_index]])[0]
        pred_mlp = regMLP.predict(X_test.loc[[first_index]])[0]

        # Obliczenie średniej predykcji
        mean_pred = (pred_xgb + pred_rf + pred_mlp) / 3

        # Przechowywanie wyników
        predictionsXGB.append(pred_xgb)
        predictions_rf.append(pred_rf)
        predictions_mlp.append(pred_mlp)
        true_values.append(Y_test.loc[first_index].values[0])

        # Dodanie predykcji do okna
        new_row_X = X_test.loc[[first_index]].copy()

        # Przesunięcie lagów
        for lag in range(num_lags, 1, -1):
            new_row_X[f'lag_{lag}'] = new_row_X[f'lag_{lag-1}']

        # Aktualizacja `lag_1` nową predykcją
        new_row_X['lag_1'] = new_row_X['open']
        new_row_X['open'] = mean_pred  # Aktualizacja wartości 'open'

        # Dodanie nowego wiersza do zbioru treningowego
        X_train = pd.concat([X_train, new_row_X])
        Y_train = pd.concat([Y_train, pd.DataFrame([mean_pred], columns=TARGET, index=new_row_X.index)])

        # Usunięcie przetworzonego wiersza ze zbioru testowego
        X_test = X_test.drop(index=first_index)
        Y_test = Y_test.drop(index=first_index)

        if len(X_test) == 0:
            true_value = true_values[-1]
            pred_xgb = predictionsXGB[-1]
            pred_rf = predictions_rf[-1]
            pred_mlp = predictions_mlp[-1]
            mean_prediction = (pred_xgb + pred_rf + pred_mlp) / 3
            print(f"True Value: {true_value}, Mean Prediction: {mean_prediction}")
            # Konwersja na listy dla metryk
            true_values_list = [true_value]
            predictions_list = [mean_prediction]
            # Obliczanie metryk
            rmse_val = rmse(true_values_list, predictions_list)
            mse_val = mse(true_values_list, predictions_list)
            smape_val = smape(true_values_list, predictions_list)
            mape_val = mape(true_values_list, predictions_list)
            huber_loss_val = huber_loss(true_values_list, predictions_list)
            # Wyświetlenie wyników
            print(f"RMSE: {rmse_val}")
            print(f"MSE: {mse_val}")
            print(f"SMAPE: {smape_val}%")
            print(f"MAPE: {mape_val}%")
            print(f"Huber Loss: {huber_loss_val}")


    # Prognozowanie dla dwukrotności długości okna
    for i in range(len(X_train) // 2):
        new_pred_xgb = regXGB.predict(X_train.iloc[[-1]])[0]
        new_pred_rf = regRF.predict(X_train.iloc[[-1]])[0]
        new_pred_mlp = regMLP.predict(X_train.iloc[[-1]])[0]

        mean_pred = (new_pred_xgb + new_pred_rf + new_pred_mlp) / 3

        # Dodawanie nowej predykcji
        new_row = X_train.iloc[[-1]].copy()

        # Przesunięcie lagów
        for lag in range(num_lags, 1, -1):
            new_row[f'lag_{lag}'] = new_row[f'lag_{lag-1}']

        new_row['lag_1'] = new_row['open']
        new_row['open'] = mean_pred

        X_train = pd.concat([X_train, new_row])
        predictionsXGB.append(new_pred_xgb)
        predictions_rf.append(new_pred_rf)
        predictions_mlp.append(new_pred_mlp)
        true_values.append(None)


    mean_prediction = (predictions_mlp[-1] + predictions_rf[-1] + predictionsXGB[-1])/3
    data_to_save = {
        "Symbol": [symbol],
        "True Value": [true_value],
        "Mean Prediction": [mean_prediction],
        "RMSE": [rmse_val],
        "MSE": [mse_val],
        "SMAPE": [smape_val],
        "MAPE": [mape_val],
        "Huber Loss": [huber_loss_val]
    }
    df_to_save = pd.DataFrame(data_to_save)
    df_to_save.to_csv(output_file, mode='a', index=False, header=not file_exists)


    # Wyświetlanie wyników
    results = pd.DataFrame({
        "True Values": true_values,
        "Predictions XGBoost": predictionsXGB,
        "Predictions Random Forest": predictions_rf,
        "Predictions MLP": predictions_mlp
    })
    print(results)
    results = results.reset_index()

    # Tworzenie DataFrame do wizualizacji w Streamlit
    chart_data = pd.DataFrame({
        "True Values": results["True Values"],
        "XGBoost Predictions": results["Predictions XGBoost"],
        "Random Forest Predictions": results["Predictions Random Forest"],
        "MLP Predictions": results["Predictions MLP"]
    })
    # Wyświetlenie symbolu jako nagłówka
    st.header(f"Symbol: {symbol}")
    # Rysowanie wykresu liniowego
    st.line_chart(chart_data)