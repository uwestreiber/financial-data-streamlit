### TEST ###

import bt
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# Lade Daten für ein bestimmtes Symbol
data = bt.get('TSLA', start='2016-01-01')

# Berechne den 50-Tage gleitenden Durchschnitt
sma_50 = data.rolling(50).mean()

# Signalmatrix: Preis > SMA
signal = data > sma_50

# Strategie erstellen
sma_strategy = bt.Strategy('SMA 50',
    [bt.algos.SelectWhere(signal),
     bt.algos.WeighEqually(),
     bt.algos.Rebalance()])

# Backtest erstellen und ausführen
test = bt.Backtest(sma_strategy, data)
result = bt.run(test)

# Equity-Kurve aus den Ergebnissen extrahieren
equity_curve = result.prices
st.write(equity_curve.head(500))

# Visualisiere die Equity-Kurve mit Plotly
fig = go.Figure()

# Plot der Equity-Kurve
#fig.add_trace(go.Scatter(x=equity_curve.index, y=equity_curve, mode='lines', name='Equity Curve'))
fig.add_trace(go.Scatter(x=equity_curve.index, y=equity_curve['SMA 50'], mode='lines', name='Equity Curve'))

# Layout-Einstellungen
fig.update_layout(
    title='Performance der SMA 50-Strategie',
    xaxis_title='Datum',
    yaxis_title='Wert des Portfolios',
    legend_title='Strategie',
    width=1000,
    height=600
)

# Plot in Streamlit anzeigen
st.plotly_chart(fig)

# Statistiken anzeigen
st.write(result.display())
