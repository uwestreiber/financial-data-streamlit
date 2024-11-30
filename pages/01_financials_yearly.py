# Importieren von Paketen
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import urllib.parse

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from datetime import date
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from matplotlib.dates import AutoDateLocator

import warnings 
warnings.filterwarnings("ignore")

st.set_page_config(layout="wide")

# Klasse für yfinance und als fix für .info
########################################### separate Klasse als fix für .info
# Quelle: https://github.com/ranaroussi/yfinance/issues/1729
class YFinance:
    user_agent_key = "User-Agent"
    user_agent_value = ("Mozilla/5.0 (Windows NT 6.1; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/58.0.3029.110 Safari/537.36")
    
    def __init__(self, ticker):
        self.yahoo_ticker = ticker

    def __str__(self):
        return self.yahoo_ticker

    def _get_yahoo_cookie(self):
        cookie = None

        headers = {self.user_agent_key: self.user_agent_value}
        response = requests.get("https://fc.yahoo.com",
                                headers=headers,
                                allow_redirects=True)

        if not response.cookies:
            raise Exception("Failed to obtain Yahoo auth cookie.")

        cookie = list(response.cookies)[0]

        return cookie

    def _get_yahoo_crumb(self, cookie):
        crumb = None

        headers = {self.user_agent_key: self.user_agent_value}

        crumb_response = requests.get(
            "https://query1.finance.yahoo.com/v1/test/getcrumb",
            headers=headers,
            cookies={cookie.name: cookie.value},
            allow_redirects=True,
        )
        crumb = crumb_response.text

        if crumb is None:
            raise Exception("Failed to retrieve Yahoo crumb.")

        return crumb

    @property
    def info(self):
        # Yahoo modules doc informations :
        # https://cryptocointracker.com/yahoo-finance/yahoo-finance-api
        cookie = self._get_yahoo_cookie()
        crumb = self._get_yahoo_crumb(cookie)
        info = {}
        ret = {}

        headers = {self.user_agent_key: self.user_agent_value}

        yahoo_modules = ("summaryDetail,"
                         "financialData,"
                         "indexTrend,"
                         "quoteType,"
                         "assetProfile,"
                         "defaultKeyStatistics")

        url = ("https://query1.finance.yahoo.com/v10/finance/"
               f"quoteSummary/{self.yahoo_ticker}"
               f"?modules={urllib.parse.quote_plus(yahoo_modules)}"
               f"&ssl=true&crumb={urllib.parse.quote_plus(crumb)}")

        info_response = requests.get(url,
                                     headers=headers,
                                     cookies={cookie.name: cookie.value},
                                     allow_redirects=True)

        info = info_response.json()
        info = info['quoteSummary']['result'][0]

        for mainKeys in info.keys():
            for key in info[mainKeys].keys():
                if isinstance(info[mainKeys][key], dict):
                    try:
                        ret[key] = info[mainKeys][key]['raw']
                    except (KeyError, TypeError):
                        pass
                else:
                    ret[key] = info[mainKeys][key]

        return ret
########################################### Ende separate Klasse

# Variablen aus app.py holen
stock_yfinance = st.session_state["stock_yfinance"]

## 1. Daten von yfinance abrufen
ticker_info = yf.Ticker(stock_yfinance).fast_info
ticker_obj = yf.Ticker(stock_yfinance)

## 2. Daten von YFinance (die Klasse als bugfix) abrufen
yfinance_obj = YFinance(stock_yfinance) # aus Klasse FYinance
info2 = yfinance_obj.info # aus Klasse FYinance

# lokale Variablen definieren
n = 3 # Anzahl der Nachkommastellen
#currency = ticker_info['currency'] # aktuelles currency aus info abrufen
#st.session_state["currency"] = currency # global verfügbar machen
currency = st.session_state.get("currency")





###########################Navigationsbereich

st.sidebar.title("Anzahl Jahre")
num_years_financials = st.sidebar.selectbox(
    "G/V-Rechnung:",
    options=[4, 5, 6],
    index=0  # Standardwert: 4 (entspricht dem Index 1 in der Liste)
)

num_years_cashflow = st.sidebar.selectbox(
    "Kapitalfluss:",
    options=[4, 5, 6],
    index=0  # Standardwert: 4 (entspricht dem Index 1 in der Liste)
)

num_years_balance = st.sidebar.selectbox(
    "Bilanz:",
    options=[4, 5, 6],
    index=0  # Standardwert: 4 (entspricht dem Index 1 in der Liste)
)


st.title(f"Ausgewählte Finanzdaten für {stock_yfinance} in {currency}")
## TEIL UWE'S FINANCE TABLE_JAHRESBERICHTE_________________________________
# Variablen für yfinance definieren
annual_financials = ticker_obj.financials
annual_balance = ticker_obj.balance_sheet
annual_cashflow = ticker_obj.cashflow
annual_income = ticker_obj.income_stmt

### Tabelle 1 - Gewinn- und Verlustrechnung
# Überprüfen, ob Jahresdaten verfügbar sind
if not annual_financials.empty:
    available_years = annual_financials.shape[1]
    num_years_financials = min(num_years_financials, available_years)

    # Kennzahlen für Jahresberichte abrufen
    data_frame_gewinn_verlust = pd.DataFrame(columns=['Umsatz', 'Bruttoertrag', 'EBITDA', 'EBIT', 'EBT', 'Nettoergebnis'])

    for i in range(num_years_financials):
        ## Kennzahlen für Jahresberichte abrufen
        # Fiscal Jahr
        fiscal_year = annual_financials.columns[i].strftime('%Y')

        # Umsatz
        total_revenue = annual_financials.loc['Total Revenue'][i] / 1e9 if 'Total Revenue' in annual_financials.index else np.nan

        # Bruttoertrag nach Umsatz
        gross_profit = annual_financials.loc['Gross Profit'][i] / 1e9 if 'Gross Profit' in annual_financials.index else np.nan

        # EBITDA
        ebitda = annual_financials.loc['EBITDA'][i] / 1e9 if 'EBITDA' in annual_financials.index else np.nan

        # EBIT
        ebit = annual_financials.loc['EBIT'][i] / 1e9 if 'EBIT' in annual_financials.index else np.nan

        # EBT bzw.
        ebt = annual_financials.loc['EBT'][i] / 1e9 if 'EBT' in annual_financials.index else np.nan

        # Nettoergebnis bzw. Net Income after Tax (NIAT)
        net_income = annual_financials.loc['Net Income'][i] / 1e9 if 'Net Income' in annual_financials.index else np.nan

        # Daten dem DataFrame hinzufügen
        data_frame_gewinn_verlust.loc[fiscal_year] = [total_revenue, gross_profit, ebitda, ebit, ebt, net_income]

    ## Daten transponieren
    data_frame_gewinn_verlust = data_frame_gewinn_verlust.transpose()
    data_frame_gewinn_verlust = data_frame_gewinn_verlust.iloc[:, ::-1]  # Spalten umkehren
    data_frame_gewinn_verlust = data_frame_gewinn_verlust.round(n)  # alle Zahlen auf n Nachkommastellen runden

    # YoY-Berechnung für Umsatz, EBIT und Nettoergebnis
    for metric in ['Umsatz', 'EBIT', 'Nettoergebnis']:
        yoy = data_frame_gewinn_verlust.loc[metric].pct_change() * 100  # YoY berechnen (kein axis nötig)
        data_frame_gewinn_verlust.loc[f"{metric} YoY (%)"] = yoy.round(2)  # Gerundete Werte hinzufügen

else:
    st.text("Keine Jahresdaten verfügbar.")

# Reihenfolge der Kennzahlen und YoY-Werte definieren
new_order = ['Umsatz', 'Umsatz YoY (%)', 'Bruttoertrag', 'EBITDA', 'EBIT', 'EBIT YoY (%)', 'EBT', 'Nettoergebnis', 'Nettoergebnis YoY (%)']
data_frame_gewinn_verlust = data_frame_gewinn_verlust.loc[new_order]
######################################################################################
st.subheader("Gewinn- und Verlust in Mrd.")
st.dataframe(data_frame_gewinn_verlust)






### Tabelle 2 - FCF and Others
# Überprüfen, ob Jahresdaten verfügbar sind
if not annual_cashflow.empty:
    available_years = annual_cashflow.shape[1]
    num_years_cashflow = min(num_years_cashflow, available_years)

    # Kennzahlen für Jahresberichte abrufen
    data_frame_fcf_others = pd.DataFrame(columns=['Operating Cashflow', 'Investing Cashflow', 'Financing Cashflow', 'Free Cashflow'])

    for i in range(num_years_cashflow):
        ## Kennzahlen für Jahresberichte abrufen
        # Fiscal Jahr
        fiscal_year = annual_cashflow.columns[i].strftime('%Y')

        # Operating Cash Flow
        ops_cashflow = annual_cashflow.loc['Operating Cash Flow'][i] / 1e9 if 'Operating Cash Flow' in annual_cashflow.index else np.nan

        # Investing Cash Flow
        inv_cashflow = annual_cashflow.loc['Investing Cash Flow'][i] / 1e9 if 'Investing Cash Flow' in annual_cashflow.index else np.nan

        # Financing Cash Flow
        fin_cashflow = annual_cashflow.loc['Financing Cash Flow'][i] / 1e9 if 'Financing Cash Flow' in annual_cashflow.index else np.nan

        # Free Cash Flow
        fcf = annual_cashflow.loc['Free Cash Flow'][i] / 1e9 if 'Free Cash Flow' in annual_cashflow.index else np.nan

        # Daten dem DataFrame hinzufügen
        data_frame_fcf_others.loc[fiscal_year] = [ops_cashflow, inv_cashflow, fin_cashflow, fcf]

    ## Daten transponieren
    data_frame_fcf_others = data_frame_fcf_others.transpose()
    data_frame_fcf_others = data_frame_fcf_others.iloc[:, ::-1]  # Spalten umkehren
    data_frame_fcf_others = data_frame_fcf_others.round(n)  # alle Zahlen auf n Nachkommastellen runden

    # YoY-Berechnung für Free Cashflow
    data_frame_fcf_others.loc['Free Cashflow YoY (%)'] = (data_frame_fcf_others.loc['Free Cashflow'].pct_change() * 100).round(2)

else:
    st.text("Keine Jahresdaten verfügbar.")
    
# Reihenfolge der Kennzahlen und YoY-Werte anpassen
new_order = ['Operating Cashflow', 'Investing Cashflow', 'Financing Cashflow', 'Free Cashflow', 'Free Cashflow YoY (%)']
data_frame_fcf_others = data_frame_fcf_others.loc[new_order]
######################################################################################
st.subheader("Kapitalfluss in Mrd.")
st.dataframe(data_frame_fcf_others)





### Tabelle 3 - Weitere Kennzahlen aus Jahresberichten
# Überprüfen, ob Jahresdaten verfügbar sind
if not annual_cashflow.empty:
    available_years = annual_balance.shape[1]
    num_years_balance = min(num_years_balance, available_years)

    # Kennzahlen für Jahresberichte abrufen
    for i in range(num_years_balance):

        kennzahlen_balance_sheet = pd.DataFrame(columns=['Verschuldung', 'Eigenkapital', 'D/E Ratio', 'Inventar', 'Fertige Produkte', 'Anlagevermögen', 'Umlaufvermögen', 'Imaterielle Vermögenswerte', 'Summe Vermögen'])

        for i in range(num_years_balance):
        
            ## Kennzahlen für Jahresberichte abrufen
            # Fiscal Jahr
            fiscal_year = annual_cashflow.columns[i].strftime('%Y')

            # Total Debt
            total_debt = annual_balance.loc['Total Debt'][i] / 1e9 if 'Total Debt' in annual_balance.index else np.nan

            # Total Equity
            total_equity = annual_balance.loc['Stockholders Equity'][i] / 1e9 if 'Stockholders Equity' in annual_balance.index else np.nan

            # Debt to Equity Ratio
            debt_to_equity_ratio = total_debt / total_equity if total_equity else np.nan
            debt_to_equity_ratio = round(debt_to_equity_ratio, 2)

            # Inventar
            inventory = annual_balance.loc['Inventory'][i] / 1e9 if 'Inventory' in annual_balance.index else np.nan

            # Anderes Inventar
            other_inventory = annual_balance.loc['Finished Goods'][i] / 1e9 if 'Finished Goods' in annual_balance.index else np.nan

            # Anlagevermögen
            current_assets = annual_balance.loc['Current Assets'][i] / 1e9 if 'Current Assets' in annual_balance.index else np.nan

            # Umlaufvermögen
            non_current_assets = annual_balance.loc['Total Non Current Assets'][i] / 1e9 if 'Total Non Current Assets' in annual_balance.index else np.nan

            # Imaterielle Vermögenswerte
            intangible_assets = "TBD"
            
            # Summe (Vermögen)
            total_assets = current_assets + non_current_assets# + intangible_assets

            # Eigenkapital


            # Fremdkapital

            # Summe (Kapital)



            # Daten dem DataFrame hinzufügen
            kennzahlen_balance_sheet.loc[fiscal_year] = [total_debt, total_equity, debt_to_equity_ratio, inventory, other_inventory, current_assets, non_current_assets, intangible_assets, total_assets]

        ## Daten transponieren
        kennzahlen_balance_sheet = kennzahlen_balance_sheet.transpose()
        kennzahlen_balance_sheet = kennzahlen_balance_sheet.iloc[:, ::-1] # Spalten umkehren
        kennzahlen_balance_sheet = kennzahlen_balance_sheet.round(n) # alle Zahlen auf n Nachkommastellen runden                        
else:
    st.text("Keine Jahresdaten verfügbar.")
######################################################################################
st.subheader("Kennzahlen aus der Bilanz in Mrd.")
st.dataframe(kennzahlen_balance_sheet)