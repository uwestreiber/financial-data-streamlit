import streamlit as st
import yfinance as yf
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import wbdata #docu: https://wbdata.readthedocs.io/en/stable/
import requests
import urllib
import datetime
import os

########################################### separate Klasse als fix für .info --> per session_state???
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







############################################################################################Funkionen für Market Cap Berechnung
# Funktion zum Laden der Stammdaten aus einer .txt-Datei
import pandas as pd

# Funktion zum Laden der CSV-Datei und Formatierung der Spalten
def load_and_sort_csv():
    file_path = os.path.join("pages", "market_cap_overview.csv")
    
    # CSV-Datei laden
    df = pd.read_csv(file_path, delimiter=";")
    
    # Spalte 'Ticker' als String formatieren
    df['Ticker'] = df['Ticker'].astype(str).str.strip()
    
    # Spalte 'Qty Shares' als Ganzzahl formatieren
    df['Qty Shares'] = df['Qty Shares'].astype(int)
    
    # Spalte 'Date Beginning' als datetime formatieren
    df['Date Beginning'] = pd.to_datetime(df['Date Beginning'], format="%Y-%m-%d")
    
    # Sortieren der Daten nach 'Ticker' und 'Date Beginning'
    df = df.sort_values(by=['Ticker', 'Date Beginning'])
    
    return df

def fetch_adj_close_data(df):
    # Neues DataFrame, um die historischen Adjusted Close-Daten zu speichern
    history_adj_close = pd.DataFrame()

    # Durchlaufen der Ticker-Symbole im df DataFrame
    for ticker in df['Ticker']:
        print(f"Lade Daten für: {ticker}")
        # Historische Adjusted Close-Daten für den Ticker abrufen
        stock_data = yf.download(ticker, start=start_date_index, end=end_date_index)["Adj Close"]

        # Die Adjusted Close-Daten in das DataFrame einfügen
        history_adj_close[ticker] = stock_data
    
    # Die gesammelten Adjusted Close-Daten zurückgeben
    return history_adj_close

def calculate_market_cap(df, history_adj_close, start_date_index):
    # DataFrame, um die Marktkapitalisierung zu speichern
    market_cap_data = pd.DataFrame()

    # Durchlaufen der Ticker-Symbole im df DataFrame
    for index, row in df.iterrows():
        ticker = row['Ticker']
        print(f"Berechne Marktkapitalisierung für: {ticker}")

        # Berechnung der Marktkapitalisierung dynamisch je nach Datum
        market_cap = pd.Series(index=history_adj_close.index)

        # Berechnung basierend auf den unterschiedlichen 'Qty Shares'
        ticker_data = df[df['Ticker'] == ticker].sort_values(by='Date Beginning')

        for i, ticker_row in ticker_data.iterrows():
            start_date = ticker_row['Date Beginning']
            qty_shares = ticker_row['Qty Shares']

            # Überprüfen, ob das 'start_date_index' vor dem ersten 'Date Beginning' liegt
            if start_date > pd.to_datetime(start_date_index):
                relevant_dates = history_adj_close.index[history_adj_close.index >= start_date]
            else:
                # Falls 'start_date_index' später ist, verwenden wir es als Filter
                relevant_dates = history_adj_close.index[history_adj_close.index >= pd.to_datetime(start_date_index)]
            
            # Multipliziere die Adjusted Close-Daten für diesen Zeitraum mit der Anzahl der Aktien
            market_cap.loc[relevant_dates] = history_adj_close.loc[relevant_dates, ticker] * qty_shares

        # Die berechnete Marktkapitalisierung in das DataFrame einfügen
        market_cap_data[ticker] = market_cap
    
    # Die berechnete Marktkapitalisierung zurückgeben
    return market_cap_data

def calculate_market_cap_by_industry(df, market_cap_data):
    # Neues DataFrame, um die Marktkapitalisierung pro Industry zu speichern
    market_cap_industry = pd.DataFrame()

    # Durchlaufen der einzigartigen Industries im df DataFrame
    industries = df['Industry'].unique()
    
    for industry in industries:
        # Alle Ticker, die zu dieser Industry gehören
        tickers_in_industry = df[df['Industry'] == industry]['Ticker']

        print(f"Summiere Marktkapitalisierung für Industry: {industry}")

        # Marktkapitalisierung für alle Ticker in dieser Industry summieren
        market_cap_industry[industry] = market_cap_data[tickers_in_industry].sum(axis=1)
    
    # Die berechnete Marktkapitalisierung pro Industry zurückgeben
    return market_cap_industry

#Re-Sampling Size für Market Cap (Segmente Uwe)
def resample_data(market_cap_industry, resample_size):
    # Resampling des DataFrames basierend auf der Auswahl (z.B. Täglich, Wöchentlich, etc.)
    resampled_data = market_cap_industry.resample(resample_options[resample_size]).sum()
    return resampled_data
############################################################################################Funkionen für Market Cap Berechnung - ENDE











# Laden der historischen Indexwerte über yfinance
tickers = {
    "S&P 500": "^GSPC",  # S&P 500
    "DAX": "^GDAXI",     # DAX
    "NIFTY 50": "^NSEI", # NIFTY 50
    "SSE Composite": "000001.SS", # NIFTY 50
    "VIX Daten": "^VIX"
}

# Start- und Enddatum für historische Daten
start_date_index = "2020-01-01"
end_date_index = "2024-12-31"



# Auswahl der Resampling-Größe mit Dropdown-Menü
resample_options = {
    'Täglich': 'D',
    'Wöchentlich': 'W',
    'Monatlich': 'M',
    'Jährlich': 'A'
}

# Dropdown zur Auswahl der Resampling-Größe
resample_size = st.selectbox('Resampling-Größe wählen für Länderindizes:', options=list(resample_options.keys()), index=0)


# DataFrame zur Speicherung der Indexdaten
df_index = {}
for index_name, ticker in tickers.items():
    data = yf.download(ticker, start=start_date_index, end=end_date_index)["Adj Close"]
    df_index[index_name] = data.resample(resample_options[resample_size]).last()
#df_index = df_index.ffill().dropna()
#print(df_index)





#Weltbank API mittels wbdata abfragen
sources = wbdata.get_sources()
#indicators = wbdata.get_indicators(source=2) #2 = World Development Indicators
gdp_list = wbdata.get_data("NY.GDP.MKTP.CD", country=["USA", "IND", "DEU", "CHN"], date=("2000", "2023"))
inflation_consumer_price_list = wbdata.get_data("FP.CPI.TOTL.ZG", country=["USA", "IND", "DEU", "CHN"], date=("2000", "2023"))
unemployment_per_total_work_force_list = wbdata.get_data("SL.UEM.TOTL.ZS", country=["USA", "IND", "DEU", "CHN"], date=("2000", "2023"))
#query1 = wbdata.get_countries(query='China')
#query2 = wbdata.get_indicators(query="gdp per capita", source=2)
#query3 = wbdata.get_indicators(query="Unemployment")

#print(f"Ergebnisse der Suchanfrage: {query3}")


##########################Dataframe GDP erstellen, bearbeiten, richtige Ausgabe
df_gdp = pd.json_normalize(gdp_list) # Konvertiere die Daten in ein DataFrame
# Relevante Spalten extrahieren
df_gdp = df_gdp[['country.value', 'date', 'value']]
df_gdp.columns = ['Country', 'Year', 'GDP']
# Datentypen anpassen
df_gdp['Year'] = pd.to_numeric(df_gdp['Year'])  # Stelle sicher, dass die Jahreszahlen als Zahlen behandelt werden
df_gdp['GDP'] = pd.to_numeric(df_gdp['GDP'])
df_gdp_sorted = df_gdp.sort_values(by=['Year']) # Sortiere die Daten nach Jahr für eine korrekte Darstellung

##########################Dataframe Inflation Consumer Price erstellen, bearbeiten, richtige Ausgabe
df_inflation = pd.json_normalize(inflation_consumer_price_list) # Konvertiere die Daten in ein DataFrame
# Relevante Spalten extrahieren
df_inflation = df_inflation[['country.value', 'date', 'value']]
df_inflation.columns = ['Country', 'Year', 'Inflation']
# Datentypen anpassen
df_inflation['Year'] = pd.to_numeric(df_inflation['Year'])  # Stelle sicher, dass die Jahreszahlen als Zahlen behandelt werden
df_inflation['Inflation'] = pd.to_numeric(df_inflation['Inflation'])
df_inflation_sorted = df_inflation.sort_values(by=['Year']) # Sortiere die Daten nach Jahr für eine korrekte Darstellung

##########################Dataframe Unemployment (% from total work force) erstellen, bearbeiten, richtige Ausgabe
df_unemployment = pd.json_normalize(unemployment_per_total_work_force_list) # Konvertiere die Daten in ein DataFrame
# Relevante Spalten extrahieren
df_unemployment = df_unemployment[['country.value', 'date', 'value']]
df_unemployment.columns = ['Country', 'Year', 'Rate']
# Datentypen anpassen
df_unemployment['Year'] = pd.to_numeric(df_unemployment['Year'])  # Stelle sicher, dass die Jahreszahlen als Zahlen behandelt werden
df_unemployment['Rate'] = pd.to_numeric(df_unemployment['Rate'])
df_unemployment_sorted = df_unemployment.sort_values(by=['Year']) # Sortiere die Daten nach Jahr für eine korrekte Darstellung

#print(f"Arbeitslosenzahlen in Prozent: {df_unemployment_sorted}")






# 1. GDP Diagramm formatieren
#fig_gdp = px.line(df_gdp, x='Year', y=['Germany_GDP', 'USA_GDP', 'India_GDP'], title='GDP Entwicklung')
#fig_gdp = px.line(df_gdp, x='Year', y='GDP', color='Country', title='GDP Entwicklung in Deutschland, USA und Indien')

# Daten für Deutschland und Indien (primäre Achse)
fig_gdp = go.Figure()
fig_gdp.add_trace(go.Scatter(x=df_gdp[df_gdp["Country"] == "Germany"]["Year"], y=df_gdp[df_gdp["Country"] == "Germany"]["GDP"], mode='lines+markers', name="Germany", line=dict(color='blue')))
fig_gdp.add_trace(go.Scatter(x=df_gdp[df_gdp["Country"] == "India"]["Year"], y=df_gdp[df_gdp["Country"] == "India"]["GDP"], mode='lines+markers', name="India", line=dict(color='green')))

# Daten für USA (sekundäre Achse)
fig_gdp.add_trace(go.Scatter(x=df_gdp[df_gdp["Country"] == "United States"]["Year"], y=df_gdp[df_gdp["Country"] == "United States"]["GDP"], mode='lines+markers', name="United States", line=dict(color='red'), yaxis="y2"))
fig_gdp.add_trace(go.Scatter(x=df_gdp[df_gdp["Country"] == "China"]["Year"], y=df_gdp[df_gdp["Country"] == "China"]["GDP"], mode='lines+markers', name="China", line=dict(color='grey'), yaxis="y2"))

# Layout anpassen, um die sekundäre Achse hinzuzufügen
fig_gdp.update_layout(
    title="BiP Entwicklung (in Bln USD) in Deutschland, USA, Indien, China",
    xaxis=dict(title="Jahr"),
    yaxis=dict(title="BiP (Deutschland, Indien)", showgrid=False,),
    yaxis2=dict(title="BiP (USA, China)", overlaying="y", side="right", showgrid=False,),
    legend=dict(x=0.1, y=1.1, orientation="h"),
)




# 2. Inflation Diagramm
fig_inflation = go.Figure()
fig_inflation.add_trace(go.Scatter(x=df_inflation_sorted[df_inflation_sorted["Country"] == "Germany"]["Year"], y=df_inflation_sorted[df_inflation_sorted["Country"] == "Germany"]["Inflation"], mode='lines+markers', name="Germany", line=dict(color='blue')))
fig_inflation.add_trace(go.Scatter(x=df_inflation_sorted[df_inflation_sorted["Country"] == "India"]["Year"], y=df_inflation_sorted[df_inflation_sorted["Country"] == "India"]["Inflation"], mode='lines+markers', name="India", line=dict(color='green')))
fig_inflation.add_trace(go.Scatter(x=df_inflation_sorted[df_inflation_sorted["Country"] == "United States"]["Year"], y=df_inflation_sorted[df_inflation_sorted["Country"] == "United States"]["Inflation"], mode='lines+markers', name="United States", line=dict(color='red')))
fig_inflation.add_trace(go.Scatter(x=df_inflation_sorted[df_inflation_sorted["Country"] == "China"]["Year"], y=df_inflation_sorted[df_inflation_sorted["Country"] == "China"]["Inflation"], mode='lines+markers', name="China", line=dict(color='grey')))

# Layout anpassen
fig_inflation.update_layout(
    title="Inflation (consumer Goods) Entwicklung (in Prozent) in Deutschland, USA und Indien",
    xaxis=dict(title="Jahr"),
    yaxis=dict(title="Inflation in %", showgrid=True,),
    legend=dict(x=0.1, y=1.1, orientation="h"),
)



# 3. Leitzins Diagramm
#fig_interest_rate = px.line(df, x='Year', y=['Germany_Interest_Rate', 'USA_Interest_Rate', 'India_Interest_Rate'], title='Leitzins')

# 4. Arbeitsmarktdaten Diagramm
fig_unemployment = go.Figure()
fig_unemployment.add_trace(go.Scatter(x=df_unemployment_sorted[df_unemployment_sorted["Country"] == "Germany"]["Year"], y=df_unemployment_sorted[df_unemployment_sorted["Country"] == "Germany"]["Rate"], mode='lines+markers', name="Germany", line=dict(color='blue')))
fig_unemployment.add_trace(go.Scatter(x=df_unemployment_sorted[df_unemployment_sorted["Country"] == "India"]["Year"], y=df_unemployment_sorted[df_unemployment_sorted["Country"] == "India"]["Rate"], mode='lines+markers', name="India", line=dict(color='green')))
fig_unemployment.add_trace(go.Scatter(x=df_unemployment_sorted[df_unemployment_sorted["Country"] == "United States"]["Year"], y=df_unemployment_sorted[df_unemployment_sorted["Country"] == "United States"]["Rate"], mode='lines+markers', name="United States", line=dict(color='red')))
fig_unemployment.add_trace(go.Scatter(x=df_unemployment_sorted[df_unemployment_sorted["Country"] == "China"]["Year"], y=df_unemployment_sorted[df_unemployment_sorted["Country"] == "China"]["Rate"], mode='lines+markers', name="China", line=dict(color='grey')))

# Layout anpassen
fig_unemployment.update_layout(
    title="Arbeitslosenzahlen in Prozent zu potentiell und real Arbeitstätigen (work force).",
    xaxis=dict(title="Jahr"),
    yaxis=dict(title="Arbeitslosen in %", showgrid=True,),
    legend=dict(x=0.1, y=1.1, orientation="h"),
)

# 4.2 VIX und Andere Subjektive Charts (^VIX)
fig_vix_and_others = go.Figure()

# Daten für DAX und NIFTY 50 auf der primären Achse
fig_vix_and_others.add_trace(go.Scatter(x=df_index["VIX Daten"].index, y=df_index["VIX Daten"], mode='lines', name="Volatility Index", line=dict(color='blue')))

# Layout mit Range-Slider anpassen
fig_vix_and_others.update_layout(
    title=f"Volatility Index (^VIX) - {resample_size}",
    xaxis=dict(
        title="Jahr",
        rangeslider=dict(visible=True),  # Range-Slider aktivieren
        type="date"  # Datumstyp für die Achse
    ),
    yaxis=dict(title="Indexwert", showgrid=True),
    legend=dict(x=0.1, y=1.1, orientation="h")
)





# 5. Indizes je Markt auf 2 Diagramme
#Diagramm 1
fig_indices_ger_india = go.Figure()

# Daten für DAX und NIFTY 50 auf der primären Achse
fig_indices_ger_india.add_trace(go.Scatter(x=df_index["DAX"].index, y=df_index["DAX"], mode='lines', name="DAX", line=dict(color='blue')))
fig_indices_ger_india.add_trace(go.Scatter(x=df_index["NIFTY 50"].index, y=df_index["NIFTY 50"], mode='lines', name="NIFTY 50", line=dict(color='green')))

# Layout mit Range-Slider anpassen
fig_indices_ger_india.update_layout(
    title=f"Entwicklung der Länderindizes (DAX, NIFTY 50) - {resample_size}",
    xaxis=dict(
        title="Jahr",
        rangeslider=dict(visible=True),  # Range-Slider aktivieren
        type="date"  # Datumstyp für die Achse
    ),
    yaxis=dict(title="Indexwert", showgrid=True),
    legend=dict(x=0.1, y=1.1, orientation="h")
)

#Diagramm 2
fig_indices_usa_china = go.Figure()

# Daten für S&P 500 und SSE Composite auf der sekundären Achse
fig_indices_usa_china.add_trace(go.Scatter(x=df_index["S&P 500"].index, y=df_index["S&P 500"], mode='lines', name="S&P 500", line=dict(color='red')))
fig_indices_usa_china.add_trace(go.Scatter(x=df_index["SSE Composite"].index, y=df_index["SSE Composite"], mode='lines', name="SSE Composite", line=dict(color='grey')))

# Layout mit Range-Slider anpassen
fig_indices_usa_china.update_layout(
    title=f"Entwicklung der Länderindizes (S&P 500, SSE Composite) - {resample_size}",
    xaxis=dict(
        title="Jahr",
        rangeslider=dict(visible=True),  # Range-Slider aktivieren
        type="date"  # Datumstyp für die Achse
    ),
    yaxis=dict(title="Indexwert", showgrid=True),
    legend=dict(x=0.1, y=1.1, orientation="h")
)

# Streamlit App/ Darstellung auf Screen
st.title('Wirtschaftliche Kennzahlen Dashboard')

#st.plotly_chart(fig_interest_rate, use_container_width=True)

st.plotly_chart(fig_gdp, use_container_width=True)
st.plotly_chart(fig_unemployment, use_container_width=True)
st.plotly_chart(fig_inflation, use_container_width=True)
st.plotly_chart(fig_vix_and_others, use_container_width=True)
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(fig_indices_ger_india, use_container_width=True)

with col2:
    st.plotly_chart(fig_indices_usa_china, use_container_width=True)

###############################################################
# Test - Sektor/Industrievergleich aus S&P500 Ticker Symbolen
# CSV-Datei laden und formatieren
df = load_and_sort_csv()

# Abrufen der Adjusted Close-Daten und Speichern im DataFrame
history_adj_close = fetch_adj_close_data(df)

# Berechnung der Marktkapitalisierung basierend auf den bereits vorhandenen Adjusted Close-Daten
market_cap_data = calculate_market_cap(df, history_adj_close, start_date_index)

# Berechnung der Marktkapitalisierung pro Industry
market_cap_industry = calculate_market_cap_by_industry(df, market_cap_data)

# Ausgabe des DataFrames
print("Sortiert Stammdatendatei:")
print(df)
print("Historische Adjusted Close-Daten:")
print(history_adj_close.head())
print("Marktkapitalisierung je Aktie:")
print(market_cap_data.head())
print("Marktkapitalisierung je Industrie:")
print(market_cap_industry.head())




# Resampling des DataFrames
resampled_market_cap_industry = resample_data(market_cap_industry, resample_size)

# Erstelle eine leere Plotly-Figur
fig_market_cap_segments = go.Figure()

# Füge für jede Industry eine Linie hinzu (für das resampelte DataFrame)
for industry in resampled_market_cap_industry.columns:
    fig_market_cap_segments.add_trace(go.Scatter(x=resampled_market_cap_industry.index, 
                                                 y=resampled_market_cap_industry[industry],
                                                 mode='lines',
                                                 name=industry))

# Layout-Anpassungen für bessere Lesbarkeit und interaktive Funktionen
fig_market_cap_segments.update_layout(
    title=f"Marktkapitalisierung nach Segmente (Uwe) ({resample_size})",
    xaxis_title="Datum",
    yaxis_title="Marktkapitalisierung (USD)",
    hovermode="x unified",  # Einheitliches Hovering über alle Linien
    legend_title_text='Industries'
)
# Plotly-Diagramm in Streamlit anzeigen
st.plotly_chart(fig_market_cap_segments)