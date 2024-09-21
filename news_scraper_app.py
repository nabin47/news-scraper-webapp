import streamlit as st
from bs4 import BeautifulSoup
from datetime import datetime
import requests
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
import nltk

# Download NLTK data
nltk.download('punkt')

# Function to fetch news articles from Google News RSS feed
def fetch_google_news(query):
    url = f"https://news.google.com/rss/search?q={query}"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "xml")
    items = soup.find_all("item")
    
    news_items = []
    for item in items:
        title = item.title.text
        link = item.link.text
        pub_date = item.pubDate.text
        description = BeautifulSoup(item.description.text, "html.parser").text
        news_items.append({
            'title': title,
            'link': link,
            'pub_date': pub_date,
            'description': description
        })
    
    return news_items

# Function to fetch the full article text from the given URL
def get_full_article_text(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            paragraphs = soup.find_all('p')
            full_text = ' '.join([para.get_text() for para in paragraphs])
            return full_text
        else:
            return "N/A"
    except Exception as e:
        st.error(f"Error fetching article text from {url}: {str(e)}")
        return "N/A"

# Function to summarize the full article text using sumy (LSA method)
def generate_summary(text, sentence_count=3):
    try:
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        summary = summarizer(parser.document, sentence_count)
        return ' '.join([str(sentence) for sentence in summary])
    except Exception as e:
        st.error(f"Error summarizing article: {str(e)}")
        return text[:250] + '...'  # Fallback to truncating the first 250 characters

# Streamlit app layout
st.title("News Scraper Web App")
st.write("Search and collect news articles with summaries.")

# Input fields
query = st.text_input("Search Query", "Sheikh Hasina")
start_date = st.date_input("Start Date", datetime(2023, 1, 1).date())
end_date = st.date_input("End Date", datetime(2023, 12, 31).date())
article_limit = st.slider("Number of Articles to Collect", 1, 100, 10)

# Function to check if the article falls within the date range
def filter_articles_by_date(news_data, start_date, end_date):
    filtered_articles = []
    for article in news_data:
        article_date = datetime.strptime(article['pub_date'], '%a, %d %b %Y %H:%M:%S %Z').date()
        # Compare dates directly
        if start_date <= article_date <= end_date:
            filtered_articles.append(article)
    return filtered_articles

# Button to trigger search
if st.button("Search News"):
    st.info(f"Searching for articles about '{query}' from {start_date} to {end_date}...")

    # Fetch news articles from Google News RSS feed
    news_data = fetch_google_news(query)

    # Filter articles by the selected date range
    news_data = filter_articles_by_date(news_data, start_date, end_date)

    # Limit the number of articles to display
    news_data = news_data[:article_limit]

    st.success(f"Collected {len(news_data)} articles.")

    # Display a preview of the collected data
    if news_data:
        st.write("Here are the first few articles:")
        for article in news_data:
            st.write(f"**Title:** {article['title']}")
            st.write(f"**Published:** {article['pub_date']}")
            st.write(f"**Link:** {article['link']}")
            st.write(f"**Summary:** {article['description']}")
            st.write("---")

        # Prepare CSV data
        csv_headers = ['Title', 'Link', 'Published', 'Summary']
        csv_data = [[article['title'], article['link'], article['pub_date'], article['description']] for article in news_data]

        # Function to convert the data into a CSV format
        def convert_to_csv(data):
            csv_file = ""
            for row in data:
                csv_file += ','.join([f'"{col}"' for col in row]) + '\n'
            return csv_file

        # Allow user to download CSV
        csv_file = convert_to_csv([csv_headers] + csv_data)
        st.download_button(
            label="Download CSV",
            data=csv_file,
            file_name="news_articles.csv",
            mime="text/csv"
        )
# Copyright information

st.markdown(
    """
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: lightgray;
        color: black;
        text-align: center;
        padding: 10px;
        font-size: 14px;
    }
    </style>
    <div class="footer">
        © 2024 Jubair Ahmed Nabin. All rights reserved.
    </div>
    """,
    unsafe_allow_html=True
)
