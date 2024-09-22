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
import os

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# set up secret API key
news_api_key = os.environ.get('NEWS_API_KEY')
if news_api_key:
    logger.debug("NEWS_API_KEY found in environment variables.")
    st.text(f'NEWS_API_KEY found. First 5 characters: {news_api_key[:5]}...')
    st.text(f'Length of NEWS_API_KEY: {len(news_api_key)}')
else:
    logger.warning("NEWS_API_KEY not found in environment variables.")
    st.text('NEWS_API_KEY not found in environment variables.')

# Main title
st.title("Stock Data Visualization App")

# Rest of the code remains unchanged
...
