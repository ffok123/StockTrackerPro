import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime, timedelta
import base64
import io
import numpy as np
from newsapi import NewsApiClient
from newsapi.newsapi_exception import NewsAPIException
from textblob import TextBlob
import plotly.express as px
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Set page title and favicon
st.set_page_config(page_title="Stock Data Visualizer", page_icon=":chart_with_upwards_trend:")

# Main title
st.title("Stock Data Visualization App")

# Add a message about the API key
st.warning("""
⚠️ Important: This app requires a News API key to function properly.
Please replace 'YOUR_NEWS_API_KEY_HERE' in the `main.py` file with your actual News API key.
You can obtain a free API key from https://newsapi.org/
""")

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
    
    # Replace 'YOUR_NEWS_API_KEY_HERE' with your actual News API key
    api_key = "YOUR_NEWS_API_KEY_HERE"
    
    logger.debug(f"Using API key: {api_key[:5]}...")

    # Ensure start_date and end_date are datetime objects
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()

    st.info("Due to API limitations, news sentiment analysis is only available for the last 30 days.")

    try:
        newsapi = NewsApiClient(api_key=api_key)
        logger.debug("NewsApiClient initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing NewsApiClient: {str(e)}")
        return {}

    for symbol in symbols:
        logger.info(f"Fetching news for {symbol}")
        company_name = info[symbol]['longName'] if 'longName' in info[symbol] else symbol
        
        try:
            logger.debug(f"Sending API request for {company_name}")
            articles = newsapi.get_everything(
                qintitle=company_name,
                language='en',
                sort_by='publishedAt',
                from_param=start_date.strftime('%Y-%m-%d'),
                to=end_date.strftime('%Y-%m-%d'),
                page_size=10
            )
            logger.debug(f"API response for {company_name}: {articles}")
            
            if articles['status'] == 'ok':
                if not articles['articles']:
                    logger.warning(f"No articles found for {company_name}")
                else:
                    logger.info(f"Found {len(articles['articles'])} articles for {company_name}")
                    sentiments = []
                    for article in articles['articles']:
                        try:
                            title = article.get('title', '')
                            description = article.get('description', '')
                            if title is None:
                                title = ''
                            if description is None:
                                description = ''
                            
                            logger.debug(f"Article title: {title}")
                            logger.debug(f"Article description: {description}")
                            
                            blob = TextBlob(title + " " + description)
                            sentiment = blob.sentiment.polarity
                            logger.debug(f"Article sentiment: {sentiment}")
                            
                            sentiments.append({
                                'title': title,
                                'description': description,
                                'url': article.get('url', ''),
                                'publishedAt': article.get('publishedAt', ''),
                                'sentiment': sentiment
                            })
                        except Exception as e:
                            logger.error(f"Error processing article: {str(e)}")
                            continue
                    
                    avg_sentiment = sum(article['sentiment'] for article in sentiments) / len(sentiments) if sentiments else 0
                    news_sentiment[symbol] = {
                        'articles': sentiments,
                        'average_sentiment': avg_sentiment
                    }
                    logger.info(f"Calculated average sentiment for {company_name}: {avg_sentiment}")
            else:
                logger.warning(f"Received non-OK status for {company_name}: {articles['status']}")
        except NewsAPIException as e:
            st.error(f"News API Error: {str(e)}")
            logger.error(f"NewsAPIException: {str(e)}")
        except Exception as e:
            error_message = f"An error occurred while fetching news data: {str(e)}"
            st.error(error_message)
            logger.error(error_message)
            logger.error(f"Start date: {start_date}, End date: {end_date}")
            return {}

    if not news_sentiment:
        logger.warning("No news sentiment data was collected.")
        return {}

    logger.info(f"Final news sentiment data: {news_sentiment}")
    return news_sentiment

# Visualize stock data
def visualize_stock_data(data, info, news_sentiment):
    for symbol in data:
        st.subheader(f"{info[symbol]['longName']} ({symbol})")
        
        # Calculate technical indicators
        df = calculate_technical_indicators(data[symbol])
        
        # Stock price chart
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df.index,
                                     open=df['Open'],
                                     high=df['High'],
                                     low=df['Low'],
                                     close=df['Close'],
                                     name='Price'))
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], name='SMA 20'))
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], name='SMA 50'))
        fig.update_layout(title='Stock Price', xaxis_title='Date', yaxis_title='Price', height=600)
        st.plotly_chart(fig, use_container_width=True)
        
        # Volume chart
        fig_volume = go.Figure()
        fig_volume.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume'))
        fig_volume.update_layout(title='Trading Volume', xaxis_title='Date', yaxis_title='Volume', height=400)
        st.plotly_chart(fig_volume, use_container_width=True)
        
        # RSI chart
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI'))
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
        fig_rsi.update_layout(title='Relative Strength Index (RSI)', xaxis_title='Date', yaxis_title='RSI', height=400)
        st.plotly_chart(fig_rsi, use_container_width=True)
        
        # Display news sentiment
        if symbol in news_sentiment:
            st.subheader("News Sentiment Analysis")
            avg_sentiment = news_sentiment[symbol]['average_sentiment']
            st.write(f"Average sentiment score: {avg_sentiment:.2f}")
            
            sentiment_color = 'green' if avg_sentiment > 0 else 'red' if avg_sentiment < 0 else 'gray'
            st.markdown(f"<h3 style='color: {sentiment_color};'>{'Positive' if avg_sentiment > 0 else 'Negative' if avg_sentiment < 0 else 'Neutral'}</h3>", unsafe_allow_html=True)
            
            # Display recent news articles
            st.subheader("Recent News Articles")
            for article in news_sentiment[symbol]['articles']:
                st.write(f"**{article['title']}**")
                st.write(f"Sentiment: {article['sentiment']:.2f}")
                st.write(f"Published at: {article['publishedAt']}")
                st.write(f"[Read more]({article['url']})")
                st.write("---")
        else:
            st.warning("No news sentiment data available for this stock.")

# Main function
def main():
    # Fetch news sentiment data
    news_sentiment = get_news_sentiment(symbols, start_date, end_date, info)
    
    # Visualize stock data
    visualize_stock_data(data, info, news_sentiment)
    
    # Download data as CSV
    csv = io.StringIO()
    for symbol in data:
        data[symbol].to_csv(csv, index=True)
    
    csv_contents = csv.getvalue()
    b64 = base64.b64encode(csv_contents.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="stock_data.csv">Download CSV File</a>'
    st.markdown(href, unsafe_allow_html=True)

if __name__ == "__main__":
    main()