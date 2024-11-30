import streamlit as st
import pandas as pd
import os

import warnings 
warnings.filterwarnings("ignore")

st.set_page_config(layout="wide")

# Pfad zur Excel-Datei
excel_file = 'portfolio/overview_own_assets.xlsx'

# Überprüfen, ob die Datei existiert
if os.path.exists(excel_file):
    # Lesen der Excel-Datei und Abrufen der Blattnamen
    xls = pd.ExcelFile(excel_file, engine='openpyxl')
    sheet_names = xls.sheet_names

    # Seitenleiste für die Navigation
    st.sidebar.title('Navigation')
    sheet = st.sidebar.selectbox('Wählen Sie ein Arbeitsblatt aus', sheet_names)

    # Cache für das Laden der Daten
    @st.cache_data
    def load_data(sheet):
        return pd.read_excel(excel_file, sheet_name=sheet, engine='openpyxl')

    df = load_data(sheet)

    # Hauptbereich
    st.write(f'Daten aus {sheet}')
    st.dataframe(df)
else:
    st.error(f'Die Datei {excel_file} wurde nicht gefunden.')