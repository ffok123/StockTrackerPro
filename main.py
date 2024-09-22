import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime, timedelta
import base64
import io

# Set page title and favicon
st.set_page_config(page_title="Stock Data Visualizer", page_icon=":chart_with_upwards_trend:")

# Main title
st.title("Stock Data Visualization App")

# User input for stock symbols
stock_symbols = st.text_input("Enter stock symbols separated by commas (e.g., AAPL, GOOGL):", "AAPL, MSFT").upper()
symbols = [symbol.strip() for symbol in stock_symbols.split(',')]

# Fetch stock data
@st.cache_data
def get_stock_data(symbols, period="1y"):
    data = {}
    info = {}
    for symbol in symbols:
        try:
            stock = yf.Ticker(symbol)
            data[symbol] = stock.history(period=period)
            info[symbol] = stock.info
        except Exception as e:
            st.error(f"Error fetching data for {symbol}: {str(e)}")
    return data, info

data, info = get_stock_data(symbols)

if data and info:
    # Display company names and descriptions
    for symbol in symbols:
        if symbol in info:
            st.header(f"{info[symbol]['longName']} ({symbol})")
            st.write(info[symbol]['longBusinessSummary'])

    # Key financial information table
    st.subheader("Key Financial Information")
    key_stats = pd.DataFrame({
        "Metric": ["Market Cap", "P/E Ratio", "Forward P/E", "Dividend Yield", "52 Week High", "52 Week Low"]
    })

    for symbol in symbols:
        if symbol in info:
            key_stats[symbol] = [
                f"${info[symbol]['marketCap']:,}",
                f"{info[symbol]['trailingPE']:.2f}" if 'trailingPE' in info[symbol] else 'N/A',
                f"{info[symbol]['forwardPE']:.2f}" if 'forwardPE' in info[symbol] else 'N/A',
                f"{info[symbol]['dividendYield']*100:.2f}%" if 'dividendYield' in info[symbol] else 'N/A',
                f"${info[symbol]['fiftyTwoWeekHigh']:.2f}",
                f"${info[symbol]['fiftyTwoWeekLow']:.2f}"
            ]

    st.table(key_stats)

    # Stock price history chart
    st.subheader("Stock Price History")
    fig = go.Figure()
    for symbol in symbols:
        if symbol in data:
            fig.add_trace(go.Scatter(x=data[symbol].index, y=data[symbol]['Close'], name=f"{symbol} Close Price"))
    fig.update_layout(
        title="Stock Price Comparison",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Volume chart
    st.subheader("Trading Volume")
    volume_fig = go.Figure()
    for symbol in symbols:
        if symbol in data:
            volume_fig.add_trace(go.Bar(x=data[symbol].index, y=data[symbol]['Volume'], name=f"{symbol} Volume"))
    volume_fig.update_layout(
        title="Trading Volume Comparison",
        xaxis_title="Date",
        yaxis_title="Volume",
        hovermode="x unified"
    )
    st.plotly_chart(volume_fig, use_container_width=True)

    # Data table
    st.subheader("Stock Data Tables")
    for symbol in symbols:
        if symbol in data:
            st.write(f"{symbol} Data:")
            st.dataframe(data[symbol])

    # CSV download buttons
    st.subheader("Download Data")
    for symbol in symbols:
        if symbol in data:
            csv = data[symbol].to_csv(index=True)
            b64 = base64.b64encode(csv.encode()).decode()
            href = f'<a href="data:file/csv;base64,{b64}" download="{symbol}_stock_data.csv">Download {symbol} CSV File</a>'
            st.markdown(href, unsafe_allow_html=True)

else:
    st.warning("Please enter valid stock symbols.")

# Add footer
st.markdown("---")
st.markdown("Created with Streamlit, yfinance, and Plotly")
