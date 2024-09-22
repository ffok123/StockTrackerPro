# Stock Data Visualization App

## Description
This Stock Data Visualization App is a powerful tool built with Streamlit that allows users to analyze and visualize stock market data. It provides comprehensive information about selected stocks, including price history, technical indicators, trading volume, and news sentiment analysis.

## Features
- Multi-stock comparison
- Interactive stock price charts with technical indicators (SMA20, SMA50, RSI)
- Trading volume visualization
- Key financial information display
- News sentiment analysis with average sentiment scores and individual article sentiments
- Custom date range selection for historical data
- Data table display with CSV download option

## Requirements
- Python 3.7+
- Streamlit
- yfinance
- pandas
- plotly
- numpy
- newsapi-python
- textblob

## Installation
1. Clone this repository or download the source code.
2. Install the required packages:
- pip install streamlit yfinance pandas plotly numpy newsapi-python textblob

3. Set up your News API key:
- Sign up for a free account at [https://newsapi.org/](https://newsapi.org/)
- Set the API key as an environment variable named `API_KEY`

## Usage
1. Run the Streamlit app:
- streamlit run main.py

2. Open your web browser and go to the URL displayed in the terminal (usually `http://localhost:5000`).
3. Enter stock symbols separated by commas (e.g., AAPL, GOOGL) in the input field.
4. Select the desired date range for analysis.
5. Explore the various charts, tables, and analysis provided by the app.

## Contributing
Contributions to improve the app are welcome. Please feel free to submit a Pull Request.

## License
This project is open source and available under the [MIT License](LICENSE).

## Acknowledgements
- Data provided by Yahoo Finance
- News data provided by NewsAPI
- Built with Streamlit, yfinance, and Plotly

Created by NicolasAxe