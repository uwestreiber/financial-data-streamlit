import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Funktion zur Berechnung der CAGR
def calculate_cagr(start_value, end_value, periods):
    return (end_value / start_value) ** (1 / periods) - 1

# Funktion zur Suche nach dem nächsten verfügbaren Datum mit einem Close-Wert
def find_next_available_date(hist, date):
    while date not in hist.index or pd.isna(hist.loc[date]["Close"]):
        date += timedelta(days=1)
        if date > hist.index.max():
            raise ValueError("Kein gültiges Datum innerhalb des historischen Bereichs gefunden")
    return date

# Funktion zur Suche nach dem letzten verfügbaren Datum mit einem Close-Wert
def find_previous_available_date(hist, date):
    while date not in hist.index or pd.isna(hist.loc[date]["Close"]):
        date -= timedelta(days=1)
        if date < hist.index.min():
            raise ValueError("Kein gültiges Datum innerhalb des historischen Bereichs gefunden")
    return date

# Funktion zum Einfärben von Tabellen
def highlight_top3(val, top3_values):
    """
    Funktion, um die Hintergrundfarbe für die 3 höchsten Werte in einer Spalte festzulegen.
    """
    color = 'lightgreen' if val in top3_values else 'white'
    return f'background-color: {color}'

# Funktion zum Einfärben von Tabellen
def highlight_min(val, min_value):
    """
    Funktion, um den Hintergrund für den kleinsten Wert in einer Spalte festzulegen.
    """
    color = 'yellow' if val == min_value else 'white'
    return f'background-color: {color}'

# Investments und deren Ticker
investments = {
    "S&P 100": "^SP100",
    "S&P 500": "^GSPC",
    "DAX": "^GDAXI",
    "TecDAX": "EXS2.DE",
    "MSCI World": "URTH",
    "MSCI India": "INDA",
    "MSCI Argentinia": "ARGT",
    "NIFTY 50": "^NSEI",
    "Smcndctrs ETF": "VVSM.DE",
    "Rbtcs & AI ETF": "XB0T.DE",
    "MSCI World IT": "XDWT.MI"
}

# DataFrame zur Speicherung der Ergebnisse
comparison_data = pd.DataFrame(columns=["Investment", "CAGR %", "Jahre", "Startdatum", "Enddatum"])

# Berechnung der CAGR für jedes Investment
for investment, ticker in investments.items():
    try:
        ticker_obj = yf.Ticker(ticker)
        hist = ticker_obj.history(period="max")
        
        if len(hist) > 0:
            hist.index = hist.index.tz_localize(None)  # Sicherstellen, dass die Indexwerte offset-naive sind
            start_date = find_next_available_date(hist, hist.index[0])
            end_date = find_previous_available_date(hist, hist.index[-1])
            
            # Nur vollständige Jahre berücksichtigen
            start_year = start_date.year
            end_year = end_date.year
            num_years = end_year - start_year

            if num_years > 0:
                start_value = hist.loc[start_date]["Close"]
                end_value = hist.loc[end_date]["Close"]

                cagr = calculate_cagr(start_value, end_value, num_years) * 100
                new_data = pd.DataFrame({
                    "Investment": [investment],
                    "CAGR %": [round(cagr, 2)],
                    "Jahre": [num_years],
                    "Startdatum": [start_date.strftime('%Y-%m-%d')],
                    "Enddatum": [end_date.strftime('%Y-%m-%d')]
                })
                comparison_data = pd.concat([comparison_data, new_data], ignore_index=True)
    except Exception as e:
        print(f"Fehler bei {investment}: {e}")

# Start- und Enddatum des Investments mit der geringsten Anzahl an Jahren bestimmen
min_years_row = comparison_data.loc[comparison_data["Jahre"].idxmin()]
min_start_date = min_years_row["Startdatum"]
min_end_date = min_years_row["Enddatum"]

# Berechnung des normierten CAGR für jedes Investment
comparison_data["CAGR % (min yrs)"] = np.nan

for investment, row in comparison_data.iterrows():
    try:
        ticker = investments[row["Investment"]]
        ticker_obj = yf.Ticker(ticker)
        hist = ticker_obj.history(start=min_start_date, end=min_end_date)
        
        if len(hist) > 0:
            hist.index = hist.index.tz_localize(None)  # Sicherstellen, dass die Indexwerte offset-naive sind
            start_date = find_next_available_date(hist, datetime.strptime(min_start_date, '%Y-%m-%d'))
            end_date = find_previous_available_date(hist, datetime.strptime(min_end_date, '%Y-%m-%d'))

            if start_date < end_date:
                start_value = hist.loc[start_date]["Close"]
                end_value = hist.loc[end_date]["Close"]
                min_years = (datetime.strptime(min_end_date, '%Y-%m-%d') - datetime.strptime(min_start_date, '%Y-%m-%d')).days / 365.25

                cagr = calculate_cagr(start_value, end_value, min_years) * 100
                comparison_data.at[investment, "CAGR % (min yrs)"] = round(cagr, 2)
    except Exception as e:
        print(f"Fehler bei {row['Investment']}: {e}")

# Berechnung der 3-jährigen und 5-jährigen CAGR
comparison_data["CAGR 3 yrs"] = np.nan
comparison_data["CAGR 5 yrs"] = np.nan
comparison_data["CAGR 7 yrs"] = np.nan
comparison_data["CAGR 10 yrs"] = np.nan
comparison_data["CAGR 15 yrs"] = np.nan
comparison_data["CAGR 20 yrs"] = np.nan
comparison_data["CAGR 25 yrs"] = np.nan
comparison_data["CAGR 30 yrs"] = np.nan

for investment, row in comparison_data.iterrows():
    try:
        ticker = investments[row["Investment"]]
        ticker_obj = yf.Ticker(ticker)
        hist = ticker_obj.history(period="max")  # 'max' verwenden, um so viel wie möglich Daten zu holen

        if len(hist) > 0:
            hist.index = hist.index.tz_localize(None)  # Sicherstellen, dass die Indexwerte offset-naive sind

            # Berechnung der 3-jährigen CAGR
            end_date = find_previous_available_date(hist, hist.index[-1])
            start_date = find_previous_available_date(hist, end_date - timedelta(days=3*365))
            if start_date < end_date:
                start_value = hist.loc[start_date]["Close"]
                end_value = hist.loc[end_date]["Close"]
                cagr_3yrs = calculate_cagr(start_value, end_value, 3) * 100
                comparison_data.at[investment, "CAGR 3 yrs"] = round(cagr_3yrs, 2)
            else:
                comparison_data.at[investment, "CAGR 3 yrs"] = np.nan

            # Berechnung der 5-jährigen CAGR
            start_date = find_previous_available_date(hist, end_date - timedelta(days=5*365))
            if start_date < end_date:
                start_value = hist.loc[start_date]["Close"]
                end_value = hist.loc[end_date]["Close"]
                cagr_5yrs = calculate_cagr(start_value, end_value, 5) * 100
                comparison_data.at[investment, "CAGR 5 yrs"] = round(cagr_5yrs, 2)
            else:
                comparison_data.at[investment, "CAGR 5 yrs"] = np.nan

            # Berechnung der 7-jährigen CAGR
            start_date = find_previous_available_date(hist, end_date - timedelta(days=7*365))
            if start_date < end_date:
                start_value = hist.loc[start_date]["Close"]
                end_value = hist.loc[end_date]["Close"]
                cagr_7yrs = calculate_cagr(start_value, end_value, 7) * 100
                comparison_data.at[investment, "CAGR 7 yrs"] = round(cagr_7yrs, 2)
            else:
                comparison_data.at[investment, "CAGR 7 yrs"] = np.nan

            # Berechnung der 10-jährigen CAGR
            start_date = find_previous_available_date(hist, end_date - timedelta(days=10*365))
            if start_date < end_date:
                start_value = hist.loc[start_date]["Close"]
                end_value = hist.loc[end_date]["Close"]
                cagr_10yrs = calculate_cagr(start_value, end_value, 10) * 100
                comparison_data.at[investment, "CAGR 10 yrs"] = round(cagr_10yrs, 2)
            else:
                comparison_data.at[investment, "CAGR 10 yrs"] = np.nan

            # Berechnung der 15-jährigen CAGR
            start_date = find_previous_available_date(hist, end_date - timedelta(days=15*365))
            if start_date < end_date:
                start_value = hist.loc[start_date]["Close"]
                end_value = hist.loc[end_date]["Close"]
                cagr_15yrs = calculate_cagr(start_value, end_value, 15) * 100
                comparison_data.at[investment, "CAGR 15 yrs"] = round(cagr_15yrs, 2)
            else:
                comparison_data.at[investment, "CAGR 15 yrs"] = np.nan

            # Berechnung der 20-jährigen CAGR
            start_date = find_previous_available_date(hist, end_date - timedelta(days=20*365))
            if start_date < end_date:
                start_value = hist.loc[start_date]["Close"]
                end_value = hist.loc[end_date]["Close"]
                cagr_20yrs = calculate_cagr(start_value, end_value, 20) * 100
                comparison_data.at[investment, "CAGR 20 yrs"] = round(cagr_20yrs, 2)
            else:
                comparison_data.at[investment, "CAGR 20 yrs"] = np.nan

            # Berechnung der 25-jährigen CAGR
            start_date = find_previous_available_date(hist, end_date - timedelta(days=25*365))
            if start_date < end_date:
                start_value = hist.loc[start_date]["Close"]
                end_value = hist.loc[end_date]["Close"]
                cagr_25yrs = calculate_cagr(start_value, end_value, 25) * 100
                comparison_data.at[investment, "CAGR 25 yrs"] = round(cagr_25yrs, 2)
            else:
                comparison_data.at[investment, "CAGR 25 yrs"] = np.nan

            # Berechnung der 30-jährigen CAGR
            start_date = find_previous_available_date(hist, end_date - timedelta(days=30*365))
            if start_date < end_date:
                start_value = hist.loc[start_date]["Close"]
                end_value = hist.loc[end_date]["Close"]
                cagr_30yrs = calculate_cagr(start_value, end_value, 30) * 100
                comparison_data.at[investment, "CAGR 30 yrs"] = round(cagr_30yrs, 2)
            else:
                comparison_data.at[investment, "CAGR 30 yrs"] = np.nan
    except Exception as e:
        print(f"Fehler bei {row['Investment']}: {e}")

# Streamlit-Benutzerschnittstelle
st.title("Zinseszins-Rechner für Kinder")

# Eingaben für Startkapital und durchschnittlicher Zins in zwei Spalten
col1, col2 = st.columns(2)
with col1:
    initial_capital = st.number_input("Startkapital", min_value=0.0, value=1000.0)
with col2:
    annual_interest_rate = st.number_input("Durchschnittlicher Zins in % p.a.", min_value=0.0, value=5.0)


# Vergleichstabelle mit historischen CAGR-Daten
st.subheader("Historische CAGR-Daten für verschiedene Investments")
st.write(comparison_data)

# Voreinstellungen für jede 5-Jahres-Periode in einer 3x2 Matrix
st.subheader("Monatliche Sparraten einstellen")
cols = st.columns(3)
preset_values = [100, 100, 100, 100, 100, 100]  # Voreinstellungen für jede 5-Jahres-Periode

adjustments = []
for i in range(6):
    col = cols[i % 3]
    with col:
        preset_value = preset_values[i] if i < len(preset_values) else 100
        adjustments.append(st.slider(f"Monatliche Sparrate für Jahre {i*5+1}-{i*5+5}", min_value=0, max_value=1000, value=preset_value, step=50))

# Funktion zur Berechnung des Zinseszinses mit flexiblen Anpassungen
def calculate_compound_interest_with_adjustments(initial_capital, annual_interest_rate, adjustments, years=30):
    data = []
    cumulative_savings_no_interest = 0
    cumulative_interest = 0
    total_cumulative_savings = initial_capital
    period_savings = 0
    period_start_savings = initial_capital

    for year in range(1, years + 1):
        period = (year - 1) // 5
        monthly_savings = adjustments[period]

        cumulative_savings_no_interest += monthly_savings * 12
        period_savings += monthly_savings * 12
        total_cumulative_savings *= (1 + annual_interest_rate / 100)
        total_cumulative_savings += monthly_savings * 12
        cumulative_interest = total_cumulative_savings - initial_capital - cumulative_savings_no_interest

        # Am Ende jeder Periode
        if year % 5 == 0:
            period_end_savings = total_cumulative_savings - period_start_savings
            data.append([
                f"Jahre {year-4}-{year}",
                f"{cumulative_savings_no_interest:,.2f}",
                f"{cumulative_interest:,.2f}",
                f"{total_cumulative_savings:,.2f}",
                f"{period_end_savings:,.2f}"
            ])
            period_savings = 0
            period_start_savings = total_cumulative_savings

    df = pd.DataFrame(data, columns=[
        "Periode",
        "Kumulierte Einzahlungen",
        "Kumulierte Zinsen",
        "Kumulierte Sparmenge",
        "Sparmenge je Periode"
    ])
    
    # Spaltenüberschriften mittig ausrichten
    styles = [
        dict(selector="th", props=[("text-align", "center")])
    ]
    df_styled = df.style.set_table_styles(styles)
    
    return df_styled

# Berechnung
df = calculate_compound_interest_with_adjustments(initial_capital, annual_interest_rate, adjustments)

# Funktion zur Berechnung des Kindergeldes mit festem Sparbetrag
def calculate_kindergeld_savings(initial_capital, annual_interest_rate, monthly_savings, years=30):
    data = []
    cumulative_savings_no_interest = 0
    total_cumulative_savings = initial_capital

    for year in range(1, years + 1):
        cumulative_savings_no_interest += monthly_savings * 12
        total_cumulative_savings *= (1 + annual_interest_rate / 100)
        total_cumulative_savings += monthly_savings * 12

        # Am Ende jedes Jahres
        if year % 5 == 0:
            data.append(round(total_cumulative_savings, 2))

    return data

# Berechnung des Kindergeldes
kindergeld_savings = calculate_kindergeld_savings(initial_capital, annual_interest_rate, 250)

# Ausgabe der Tabelle
st.subheader("Ergebnisse")

# Tabelle mit angepassten Spaltenüberschriften anzeigen
st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)

# Interaktives Diagramm mit plotly.graph_objects
st.subheader("Visualisierung der Sparentwicklung")
fig = go.Figure()

fig.add_trace(go.Scatter(x=[i * 5 for i in range(1, len(df.data) + 1)], y=df.data["Kumulierte Einzahlungen"],
                         mode='lines', name='Kumulierte Einzahlungen'))

fig.add_trace(go.Scatter(x=[i * 5 for i in range(1, len(df.data) + 1)], y=df.data["Kumulierte Zinsen"],
                         mode='lines', name='Kumulierte Zinsen'))

fig.add_trace(go.Scatter(x=[i * 5 for i in range(1, len(df.data) + 1)], y=df.data["Kumulierte Sparmenge"],
                         mode='lines', name='Kumulierte Sparmenge'))

fig.add_trace(go.Scatter(x=[i * 5 for i in range(1, len(kindergeld_savings) + 1)], y=kindergeld_savings,
                         mode='lines', name='Kumulierte Sparmenge Kindergeld', line=dict(color='black', dash='dot')))

fig.update_layout(
    title="Entwicklung der Sparmenge über 30 Jahre",
    xaxis_title="Jahre",
    yaxis_title="Betrag (in Euro)",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="center",
        x=0.5
    ),
    yaxis=dict(
        tickformat=",",
        tickprefix="€",
        ticksuffix="",
    ),
    xaxis=dict(
        tickformat="d"
    )
)

st.plotly_chart(fig)