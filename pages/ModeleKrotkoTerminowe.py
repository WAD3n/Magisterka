import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Edytor CSV", layout="wide")

# Path to your R script
r_script_path = "pages/ModeleKrotkoTerminowe.r"

# Run the R script
os.system(f"Rscript {r_script_path}")

st.write("Pozyskano Dane")