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

# User input for stock symbol
stock_symbol = st.text_input("Enter a stock symbol (e.g., AAPL, GOOGL):", "AAPL").upper()

# Fetch stock data
@st.cache_data
def get_stock_data(symbol, period="1y"):
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period=period)
        return data, stock.info
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {str(e)}")
        return None, None

data, info = get_stock_data(stock_symbol)

if data is not None and info is not None:
    # Display company name and description
    st.header(f"{info['longName']} ({stock_symbol})")
    st.write(info['longBusinessSummary'])

    # Key financial information table
    st.subheader("Key Financial Information")
    key_stats = pd.DataFrame({
        "Metric": ["Market Cap", "P/E Ratio", "Forward P/E", "Dividend Yield", "52 Week High", "52 Week Low"],
        "Value": [
            f"${info['marketCap']:,}",
            f"{info['trailingPE']:.2f}" if 'trailingPE' in info else 'N/A',
            f"{info['forwardPE']:.2f}" if 'forwardPE' in info else 'N/A',
            f"{info['dividendYield']*100:.2f}%" if 'dividendYield' in info else 'N/A',
            f"${info['fiftyTwoWeekHigh']:.2f}",
            f"${info['fiftyTwoWeekLow']:.2f}"
        ]
    })
    st.table(key_stats)

    # Stock price history chart
    st.subheader("Stock Price History")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name="Close Price"))
    fig.update_layout(
        title=f"{stock_symbol} Stock Price",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Volume chart
    st.subheader("Trading Volume")
    volume_fig = go.Figure()
    volume_fig.add_trace(go.Bar(x=data.index, y=data['Volume'], name="Volume"))
    volume_fig.update_layout(
        title=f"{stock_symbol} Trading Volume",
        xaxis_title="Date",
        yaxis_title="Volume",
        hovermode="x unified"
    )
    st.plotly_chart(volume_fig, use_container_width=True)

    # Data table
    st.subheader("Stock Data Table")
    st.dataframe(data)

    # CSV download button
    def get_csv_download_link(df):
        csv = df.to_csv(index=True)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="{stock_symbol}_stock_data.csv">Download CSV File</a>'
        return href

    st.markdown(get_csv_download_link(data), unsafe_allow_html=True)

else:
    st.warning("Please enter a valid stock symbol.")

# Add footer
st.markdown("---")
st.markdown("Created with Streamlit, yfinance, and Plotly")
