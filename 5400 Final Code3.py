#!/usr/bin/env python
# coding: utf-8

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import base64
import altair as alt

# ─────────────────────────────────────────────────────────────
# DATABASE & FILE LOADING
# ─────────────────────────────────────────────────────────────
DB_USER     = 'postgres'
DB_PASSWORD = '123'
DB_HOST     = 'localhost'
DB_PORT     = '5432'
DB_NAME     = 'ManagingDataProject'

engine = create_engine(
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

@st.cache_data(show_spinner=False)
def load_data():
    cutoff = pd.to_datetime("2020-01-01")

    # News from Postgres
    df_news = pd.read_sql("SELECT * FROM classified_news", engine)
    df_news = (
        df_news
        .drop(columns=["image"], errors="ignore")
        .dropna(subset=["summary"])
        .assign(Date=lambda d: pd.to_datetime(d["Date"], errors="coerce"))
    )
    df_news = df_news.loc[df_news["Date"] >= cutoff]

    # Tweets with sentiment from CSV
    df_tweets = pd.read_csv("tweets_with_sentiment.csv")
    df_tweets = (
        df_tweets
        .rename(columns={"date.1": "Date"})
        .assign(Date=lambda d: pd.to_datetime(d["Date"], errors="coerce"))
    )
    df_tweets = df_tweets.loc[df_tweets["Date"] >= cutoff]

    # Stock from Postgres
    df_stock = pd.read_sql("SELECT * FROM stock_data", engine)
    df_stock["Date"] = (
        df_stock["Date"].astype(str)
                .str.slice(0, 10)
                .pipe(lambda s: pd.to_datetime(s, errors="coerce"))
    )
    df_stock = df_stock.dropna(subset=["Date", "Close"])
    df_stock = df_stock.loc[df_stock["Date"] >= cutoff]

    # Sentiment + Next‑Day Returns
    df_sent = pd.read_csv("streamlit_df.csv")
    df_sent = df_sent.rename(columns={"count_controversial.1": "count_news_controversial"})

    return df_news, df_tweets, df_stock, df_sent

df_news, df_tweets, df_stock, df_sent = load_data()

# ─────────────────────────────────────────────────────────────
# COMPANY KEYWORD MAPPING (ticker → keywords list)
# ─────────────────────────────────────────────────────────────
COMPANY_KEYWORDS = {
    "AAPL": ["AAPL", "Apple"],
    "MSFT": ["MSFT", "Microsoft"],
    "NVDA": ["NVDA", "Nvidia"],
    "META": ["META", "Meta", "Facebook", "facebook"],
    "GOOGL": ["GOOGL", "Alphabet", "Google"],
    "AMZN": ["AMZN", "Amazon"],
    "TSLA": ["TSLA", "Tesla"],
}

# ─────────────────────────────────────────────────────────────
# STREAMLIT UI SETUP
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sentiment & Returns Visualization",
    page_icon="📈",
    layout="wide"
)
st.title("📈 Magnificent 7: Media Sentiment & Returns (Since 2020)")
st.markdown(
    "Select a ticker and date range to see price chart, sentiment polarity, "
    "sentiment‑vs‑return scatter, and a bold UP/DOWN recommendation!"
)

# Background image
def get_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

bg = get_base64("/Users/tristana./Desktop/5400_stock_background.jpg")
st.markdown(f"""
<style>
.stApp {{
  background-image: url('data:image/jpeg;base64,{bg}');
  background-size: cover;
  background-attachment: fixed;
}}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# SIDEBAR CONTROLS
# ─────────────────────────────────────────────────────────────
MAG7 = list(COMPANY_KEYWORDS.keys())
ticker = st.sidebar.selectbox("Select a Magnificent 7 ticker", [""] + MAG7)

# Date range (>=2020-01-01)
min_date = min(df_news["Date"].min().date(),
               df_tweets["Date"].min().date(),
               df_stock["Date"].min().date())
max_date = max(df_news["Date"].max().date(),
               df_tweets["Date"].max().date(),
               df_stock["Date"].max().date())
start_date, end_date = st.sidebar.date_input(
    "Select date range",
    value=(min_date, max_date),
    min_value=min_date, max_value=max_date
)

if not ticker:
    st.warning("Please select a ticker.")
    st.stop()

keywords = COMPANY_KEYWORDS[ticker]

# ─────────────────────────────────────────────────────────────
# FILTER DATA
# ─────────────────────────────────────────────────────────────
# Sentiment/returns filtered by company only
df_s = df_sent.query("Company == @ticker")

# News filtered by date
df_n = df_news.loc[
    (df_news["Date"].dt.date >= start_date) &
    (df_news["Date"].dt.date <= end_date)
]

# Tweets filtered by date
df_t = df_tweets.loc[
    (df_tweets["Date"].dt.date >= start_date) &
    (df_tweets["Date"].dt.date <= end_date)
]

# Stock filtered by date & company
df_st = df_stock.loc[
    (df_stock["Date"].dt.date >= start_date) &
    (df_stock["Date"].dt.date <= end_date) &
    (df_stock["Company"].str.upper() == ticker)
]

# Helper to push rows mentioning any keyword to the top
def tag_priority(df, text_cols):
    text = df[text_cols].fillna("").agg(" ".join, axis=1).str.lower()
    prio = text.apply(lambda t: any(kw.lower() in t for kw in keywords))
    return df.assign(_prio=prio.astype(int))

# Top 10 news & tweets by priority + recency
df_n = (
    tag_priority(df_n, ["headline", "summary"])
    .sort_values(["_prio", "Date"], ascending=[False, False])
    .head(10)
)
tweet_col = "fullText" if "fullText" in df_t.columns else "Tweet"
df_t = (
    tag_priority(df_t, [tweet_col])
    .sort_values(["_prio", "Date"], ascending=[False, False])
    .head(10)
)

# ─────────────────────────────────────────────────────────────
# STOCK PRICE PANEL
# ─────────────────────────────────────────────────────────────
st.subheader(f"{ticker}: Stock Price Since 2020")
if not df_st.empty:
    st.line_chart(df_st.set_index("Date")[["Close"]])
else:
    st.info("No stock data for this ticker & date range.")

# ─────────────────────────────────────────────────────────────
# SENTIMENT & RETURNS PANEL
# ─────────────────────────────────────────────────────────────
st.subheader(f"{ticker}: Sentiment & Next‑Day Returns")
if df_s.empty:
    st.info("No sentiment/return data for this ticker.")
else:
    st.dataframe(df_s, use_container_width=True)

    # Polarity counts
    pos_news = (df_s["avg_news_sentiment"] > 0).sum()
    neg_news = (df_s["avg_news_sentiment"] < 0).sum()
    pos_tweet = (df_s["avg_tweet_sentiment"] > 0).sum()
    neg_tweet = (df_s["avg_tweet_sentiment"] < 0).sum()

    df_chart = pd.DataFrame({
        "Source": ["News", "News", "Tweets", "Tweets"],
        "Polarity": ["Positive", "Negative"] * 2,
        "Count": [pos_news, neg_news, pos_tweet, neg_tweet]
    })

    # Horizontal bar chart
    chart = (
        alt.Chart(df_chart)
        .mark_bar(size=40)
        .encode(
            y=alt.Y('Source:N', title='Source'),
            x=alt.X('Count:Q', title='Count'),
            color=alt.Color('Polarity:N', title='Polarity'),
            tooltip=['Source','Polarity','Count']
        )
        .properties(title='Sentiment Polarity Counts', width=600, height=200)
    )
    st.altair_chart(chart, use_container_width=True)

    # Sentiment vs Return scatter
    scatter_news = (
        alt.Chart(df_s)
        .mark_circle(size=60)
        .encode(
            x='avg_news_sentiment',
            y='return_next',
            tooltip=['avg_news_sentiment','return_next'],
            color=alt.value('#1f77b4')
        )
        .properties(title='News Sentiment vs Next‑Day Return', width=350, height=250)
    )
    scatter_tweet = (
        alt.Chart(df_s)
        .mark_square(size=60)
        .encode(
            x='avg_tweet_sentiment',
            y='return_next',
            tooltip=['avg_tweet_sentiment','return_next'],
            color=alt.value('#ff7f0e')
        )
        .properties(title='Tweet Sentiment vs Next‑Day Return', width=350, height=250)
    )
    c1, c2 = st.columns(2)
    c1.altair_chart(scatter_news, use_container_width=True)
    c2.altair_chart(scatter_tweet, use_container_width=True)

    # Context + Flashy Recommendation
    st.markdown("**Overall Sentiment Score (average of news & tweet):**")
    avg_sent = pd.concat([
        df_s["avg_news_sentiment"], 
        df_s["avg_tweet_sentiment"]
    ]).mean()
    arrow = "🚀 UP!" if avg_sent > 0 else "🔻 DOWN"
    # number in black, arrow in green
    st.markdown(
        f"<h2 style='text-align:center; color:black; font-weight:bold;'>"
        f"{avg_sent:.3f} &nbsp; "
        f"<span style='color:green;'>{arrow}</span>"
        f"</h2>",
        unsafe_allow_html=True
    )

# ─────────────────────────────────────────────────────────────
# SIDE-BY-SIDE: Top News & Tweets
# ─────────────────────────────────────────────────────────────
st.subheader("Top News & Tweets")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Top News**")
    for _, row in df_n.iterrows():
        st.markdown(f"- [{row.headline}]({row.url})")

with col2:
    st.markdown("**Top Tweets**")
    for _, row in df_t.iterrows():
        st.markdown(f"- {row[tweet_col]}")
