import os
import requests
import pandas as pd
from io import BytesIO
import streamlit as st

# Load the API key from environment variables
API_KEY = os.getenv("API_KEY")

# Check if API_KEY is available
if not API_KEY:
    st.error("API key not found! Please set it as an environment variable in Streamlit Cloud.")
    st.stop()

# NewsAPI configuration
BASE_URL = "https://newsapi.org/v2/everything"

# Function to fetch news
def fetch_news(keyword, from_date, to_date):
    params = {
        "q": keyword,
        "from": from_date,
        "to": to_date,
        "sortBy": "relevancy",
        "pageSize": 100,
        "apiKey": API_KEY,
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        if data.get("status") == "ok":
            return data.get("articles", [])
        else:
            st.error(f"Error: {data.get('message')}")
            return []
    else:
        st.error("Failed to fetch data from NewsAPI.")
        return []

# Function to convert articles to a DataFrame
def articles_to_dataframe(articles):
    return pd.DataFrame(
        [
            {
                "Title": article["title"],
                "Description": article["description"],
                "Published At": article["publishedAt"],
                "Source": article["source"]["name"],
                "URL": article["url"],
            }
            for article in articles
        ]
    )

# Function to convert DataFrame to Excel file
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Articles")
    processed_data = output.getvalue()
    return processed_data

# Streamlit UI
st.title("News Fetcher App")
st.write("Fetch news articles by keyword and date range, and download them as an Excel file.")

# Input fields
keyword = st.text_input("Enter keyword(s):", placeholder="e.g., AI, climate change")
from_date = st.date_input("From Date")
to_date = st.date_input("To Date")

# Fetch news button
if st.button("Fetch News"):
    if keyword and from_date and to_date:
        with st.spinner("Fetching news..."):
            articles = fetch_news(keyword, from_date, to_date)
            if articles:
                st.success(f"Found {len(articles)} articles.")
                df = articles_to_dataframe(articles)
                st.dataframe(df)

                # Download button
                excel_file = to_excel(df)
                st.download_button(
                    label="Download Excel File",
                    data=excel_file,
                    file_name="news_articles.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            else:
                st.warning("No articles found for the given criteria.")
    else:
        st.error("Please provide all inputs.")

# Footer
st.write("Powered by [NewsAPI](https://newsapi.org/)")
