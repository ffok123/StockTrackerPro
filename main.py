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
import plotly.express as px
import logging
import os

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Set page title and favicon
st.set_page_config(page_title="Stock Data Visualizer", page_icon=":chart_with_upwards_trend:")

# Main title
st.title("Stock Data Visualization App")

# User input for stock symbols
stock_symbols = st.text_input("Enter stock symbols separated by commas (e.g., AAPL, GOOGL):", "AAPL, MSFT").upper()
symbols = [symbol.strip() for symbol in stock_symbols.split(',')]

# Date range selection
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start date", datetime.now() - timedelta(days=365))
with col2:
    end_date = st.date_input("End date", datetime.now())

if start_date > end_date:
    st.error("Error: End date must be after start date.")
    st.stop()

# Fetch stock data
@st.cache_data
def get_stock_data(symbols, start_date, end_date):
    data = {}
    info = {}
    for symbol in symbols:
        try:
            stock = yf.Ticker(symbol)
            data[symbol] = stock.history(start=start_date, end=end_date)
            info[symbol] = stock.info
        except Exception as e:
            st.error(f"Error fetching data for {symbol}: {str(e)}")
    return data, info

data, info = get_stock_data(symbols, start_date, end_date)

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
def get_news_sentiment(symbols, start_date, end_date, info):
    news_sentiment = {}
    api_key = "dd81e3f696c6436ab2b9f2a6adf3260c"
    
    logger.debug(f"Using API key: {api_key[:5]}...")

    try:
        newsapi = NewsApiClient(api_key=api_key)
        logger.debug("NewsApiClient initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing NewsApiClient: {str(e)}")
        return None

    for symbol in symbols:
        logger.info(f"Fetching news for {symbol}")
        company_name = info[symbol]['longName'] if 'longName' in info[symbol] else symbol
        query = f"{company_name} OR {symbol}"
        
        try:
            logger.debug(f"Sending API request for {query}")
            articles = newsapi.get_everything(
                q=query,
                language='en',
                sort_by='publishedAt',
                from_param=start_date.isoformat(),
                to=end_date.isoformat(),
                page_size=10
            )
            logger.debug(f"API response received for {query}")
            
            logger.info(f"Received {len(articles['articles'])} articles for {symbol}")
            
            if articles['status'] == 'ok':
                sentiments = []
                for article in articles['articles']:
                    blob = TextBlob(article['title'] + " " + article['description'])
                    sentiment = blob.sentiment.polarity
                    sentiments.append({
                        'title': article['title'],
                        'description': article['description'],
                        'url': article['url'],
                        'publishedAt': article['publishedAt'],
                        'sentiment': sentiment
                    })
                
                avg_sentiment = sum(article['sentiment'] for article in sentiments) / len(sentiments) if sentiments else 0
                news_sentiment[symbol] = {
                    'articles': sentiments,
                    'average_sentiment': avg_sentiment
                }
                logger.info(f"Calculated average sentiment for {symbol}: {avg_sentiment}")
            else:
                logger.warning(f"Received non-OK status for {symbol}: {articles['status']}")
        except Exception as e:
            logger.error(f"Error processing news for {symbol}: {str(e)}")
    
    logger.debug("Finished processing all symbols")
    return news_sentiment

def get_sentiment_category(sentiment):
    if sentiment > 0.1:
        return "Positive"
    elif sentiment < -0.1:
        return "Negative"
    else:
        return "Neutral"

def get_sentiment_color(sentiment):
    if sentiment > 0.1:
        return "green"
    elif sentiment < -0.1:
        return "red"
    else:
        return "gray"

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
    st.subheader(f"Stock Price History with Technical Indicators ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})")
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
    st.subheader(f"Trading Volume ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})")
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
    news_sentiment = get_news_sentiment(symbols, start_date, end_date, info)
    
    if news_sentiment is None:
        st.error("Unable to fetch news sentiment data. Please check if the NEWS_API_KEY is properly set in the environment variables.")
    elif news_sentiment:
        sentiment_data = []
        for symbol in symbols:
            if symbol in news_sentiment:
                avg_sentiment = news_sentiment[symbol]['average_sentiment']
                sentiment_category = get_sentiment_category(avg_sentiment)
                sentiment_data.append({
                    'Symbol': symbol,
                    'Sentiment Score': avg_sentiment,
                    'Sentiment Category': sentiment_category
                })
        
        sentiment_df = pd.DataFrame(sentiment_data)
        fig = px.bar(sentiment_df, x='Symbol', y='Sentiment Score', color='Sentiment Category',
                     title='Average Sentiment Score by Stock',
                     labels={'Sentiment Score': 'Average Sentiment Score'},
                     color_discrete_map={'Positive': 'green', 'Neutral': 'gray', 'Negative': 'red'})
        st.plotly_chart(fig)

        for symbol in symbols:
            if symbol in news_sentiment:
                st.write(f"### {symbol} News Sentiment")
                avg_sentiment = news_sentiment[symbol]['average_sentiment']
                sentiment_category = get_sentiment_category(avg_sentiment)
                sentiment_color = get_sentiment_color(avg_sentiment)
                
                st.markdown(f"<h4 style='color: {sentiment_color};'>Average Sentiment: {avg_sentiment:.2f} ({sentiment_category})</h4>", unsafe_allow_html=True)
                
                for article in news_sentiment[symbol]['articles']:
                    st.write(f"**{article['title']}**")
                    st.write(f"Published at: {article['publishedAt']}")
                    article_sentiment = get_sentiment_category(article['sentiment'])
                    article_color = get_sentiment_color(article['sentiment'])
                    st.markdown(f"<p style='color: {article_color};'>Sentiment: {article['sentiment']:.2f} ({article_sentiment})</p>", unsafe_allow_html=True)
                    st.write(f"[Read more]({article['url']})")
                    st.write("---")
    else:
        st.warning("No news sentiment data available for the selected stocks and date range.")

    # Data table
    st.subheader(f"Stock Data Tables ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})")
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
            href = f'<a href="data:file/csv;base64,{b64}" download="{symbol}_stock_data_{start_date.strftime("%Y-%m-%d")}_{end_date.strftime("%Y-%m-%d")}.csv">Download {symbol} CSV File</a>'
            st.markdown(href, unsafe_allow_html=True)

else:
    st.warning("Please enter valid stock symbols.")

# Add footer
st.markdown("---")
st.markdown("Created with Streamlit, yfinance, and Plotly")