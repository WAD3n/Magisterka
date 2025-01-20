import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Edytor CSV", layout="wide")

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

# Funkcja do zapisania CSV
def save_csv(dataframe, file_path):
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        dataframe.to_csv(file_path, index=False)
        st.success("Zmiany zostały zapisane do pliku CSV.")
    except Exception as e:
        st.error(f"Błąd podczas zapisywania pliku: {e}")

# Ścieżka do pliku CSV
file_path = "Dane/companies_symbol.csv"

# Nagłówek aplikacji
st.title("Ekspolator Aktywów")

# Wczytaj dane z pliku CSV
df = load_csv(file_path)

# Edytor danych
st.write("Wybierz Interesujące cię aktywa:")
edited_df = st.data_editor(df, num_rows="dynamic")

# Przyciski akcji
col1, col2 = st.columns(2)
with col1:
    if st.button("Zapisz zmiany"):
        save_csv(edited_df, file_path)