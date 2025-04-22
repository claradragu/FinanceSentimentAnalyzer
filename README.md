# **Real-Time Sentiment & Stock Impact Dashboard**

MarketPulse is an interactive data analytics platform that tracks and analyzes how social media sentiment, news headlines, and public controversy influence stock price movements. By integrating data from Twitter, Reddit, financial news sources, and live stock prices, this project provides actionable insights into the relationship between market sentiment and financial performance.

---

## Features
- **Real-Time Data Collection**  
  Pulls live data from:
  - **Stock Prices** (`yfinance`)
  - **News Articles** (Finnhub API)
  - **Twitter Data** (X API)
  - **Reddit Discussions** (Reddit API)

- **Sentiment & Controversy Analysis**  
  - Uses **NLTK** for sentiment scoring (positive, negative, neutral).
  - Leverages **Ollama API** for controversy classification.

- **Data Centralization**  
  - All data stored and managed in a **PostgreSQL** database for seamless integration across sources.

- **Financial Modeling**  
  - Implements **OLS Regression** and **Logistic Regression** to model the impact of sentiment on stock returns.

- **Interactive Visualization**  
  - Streamlit dashboard for exploring sentiment trends, controversial events, and stock price reactions.

---

##  Project Workflow

```plaintext
1.  Data Extraction:
     - YFinance, Finnhub, X API, Reddit API

2.  Data Processing:
     - Sentiment Analysis (NLTK)
     - Controversy Detection (Ollama API)

3.  Data Storage:
     - PostgreSQL Database Integration

4.  Modeling:
     - OLS & Logistic Regression

5.  Visualization:
     - Streamlit Interactive Dashboard
