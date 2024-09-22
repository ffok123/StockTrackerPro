import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime, timedelta
import base64
import io
import numpy as np
from newsapi import NewsApiClient
from textblob import TextBlob

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

# Calculate technical indicators
def calculate_technical_indicators(df):
    # Simple Moving Average (SMA)
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    
    # Relative Strength Index (RSI)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    return df

# Fetch news and perform sentiment analysis
@st.cache_data(ttl=3600)
def get_news_sentiment(symbols):
    try:
        api_key = st.secrets["NEWS_API_KEY"]
        newsapi = NewsApiClient(api_key=api_key)
        news_sentiment = {}

        for symbol in symbols:
            articles = newsapi.get_everything(q=symbol, language='en', sort_by='publishedAt', page_size=10)
            
            if articles['status'] == 'ok':
                sentiments = []
                for article in articles['articles']:
                    blob = TextBlob(article['title'] + " " + article['description'])
                    sentiment = blob.sentiment.polarity
                    sentiments.append({
                        'title': article['title'],
                        'description': article['description'],
                        'url': article['url'],
                        'sentiment': sentiment
                    })
                
                avg_sentiment = sum(article['sentiment'] for article in sentiments) / len(sentiments)
                news_sentiment[symbol] = {
                    'articles': sentiments,
                    'average_sentiment': avg_sentiment
                }
        
        return news_sentiment
    except Exception as e:
        st.error(f"Error fetching news sentiment: {str(e)}")
        return {}

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

    # Stock price history chart with technical indicators
    st.subheader("Stock Price History with Technical Indicators")
    for symbol in symbols:
        if symbol in data:
            df = calculate_technical_indicators(data[symbol])
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name=f"{symbol} Close Price"))
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], name=f"{symbol} SMA20"))
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], name=f"{symbol} SMA50"))
            fig.update_layout(
                title=f"{symbol} Stock Price with Moving Averages",
                xaxis_title="Date",
                yaxis_title="Price (USD)",
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)

            # RSI chart
            rsi_fig = go.Figure()
            rsi_fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name=f"{symbol} RSI"))
            rsi_fig.add_shape(type="line", x0=df.index[0], y0=30, x1=df.index[-1], y1=30,
                              line=dict(color="red", width=2, dash="dash"))
            rsi_fig.add_shape(type="line", x0=df.index[0], y0=70, x1=df.index[-1], y1=70,
                              line=dict(color="red", width=2, dash="dash"))
            rsi_fig.update_layout(
                title=f"{symbol} Relative Strength Index (RSI)",
                xaxis_title="Date",
                yaxis_title="RSI",
                yaxis=dict(range=[0, 100]),
                hovermode="x unified"
            )
            st.plotly_chart(rsi_fig, use_container_width=True)

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

    # News Sentiment Analysis
    st.subheader("News Sentiment Analysis")
    news_sentiment = get_news_sentiment(symbols)
    
    if news_sentiment:
        for symbol in symbols:
            if symbol in news_sentiment:
                st.write(f"### {symbol} News Sentiment")
                avg_sentiment = news_sentiment[symbol]['average_sentiment']
                st.write(f"Average Sentiment: {avg_sentiment:.2f}")
                
                sentiment_color = "green" if avg_sentiment > 0 else "red" if avg_sentiment < 0 else "gray"
                st.markdown(f"<h4 style='color: {sentiment_color};'>{'Positive' if avg_sentiment > 0 else 'Negative' if avg_sentiment < 0 else 'Neutral'}</h4>", unsafe_allow_html=True)
                
                for article in news_sentiment[symbol]['articles']:
                    st.write(f"**{article['title']}**")
                    st.write(f"Sentiment: {article['sentiment']:.2f}")
                    st.write(f"[Read more]({article['url']})")
                    st.write("---")
    else:
        st.warning("Unable to fetch news sentiment data. Please check your API key and try again.")

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
