import streamlit as st
import plotly.graph_objects as go
import plotly.subplots as sp
import pandas as pd

# Beispiel-Daten
df = pd.DataFrame({
    'Datum': pd.date_range(start='2023-01-01', periods=10, freq='D'),
    'RSI': [30, 32, 35, 40, 45, 42, 38, 36, 33, 31],
    'Signal': [0.1, 0.15, 0.18, 0.12, 0.1, 0.13, 0.14, 0.16, 0.15, 0.12],
    'MACD': [0.05, 0.08, 0.1, 0.06, 0.07, 0.09, 0.11, 0.12, 0.1, 0.08],
    'Kaufsignal (MACD)': [0, 0, 1, 0, 0, 1, 0, 0, 1, 0]
})

# Erstellen der Figur mit einem Subplot
fig2 = sp.make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.8, 0.2])

# Preisplot (hier einfach den MACD zum Beispiel)
fig2.add_trace(go.Scatter(x=df['Datum'], y=df['MACD'], mode='lines', name='MACD'), row=1, col=1)

# Hinzufügen der Kaufsignale als grüne Dreiecke auf der zweiten (unteren) Achse
kauf_signale = df[df['Kaufsignal (MACD)'] == 1]
fig2.add_trace(go.Scatter(
    x=kauf_signale['Datum'],
    y=[0.5] * len(kauf_signale),  # Einheitliche Höhe für die Signale
    mode='markers',
    marker=dict(symbol='triangle-up', color='green', size=10),
    name='Kaufsignal'
), row=2, col=1)

fig2.update_layout(title='Kaufsignale auf separater Achse')
fig2.update_yaxes(visible=False, row=2, col=1)  # Versteckt die y-Achse des unteren Charts
fig2.update_xaxes(title_text='Datum', row=2, col=1)

st.plotly_chart(fig2)
