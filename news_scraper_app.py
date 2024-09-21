import streamlit as st
import csv
from pygooglenews import GoogleNews
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import requests
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
import nltk

# Download NLTK data
nltk.download('punkt')

# Function to fetch the full article text from the given URL
def get_full_article_text(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            paragraphs = soup.find_all('p')  # Assuming the article text is in <p> tags
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

# Function to filter articles by date
def is_within_date_range(published_date, start_date, end_date):
    try:
        # Convert the published date from the news entry to a datetime object
        article_date = datetime.strptime(published_date, '%a, %d %b %Y %H:%M:%S %Z')
        return start_date <= article_date <= end_date
    except Exception as e:
        st.warning(f"Error parsing date: {str(e)}")
        return False

# Function to search for news articles with a date filter
def search_articles(query, start_date, end_date, article_limit):
    gn = GoogleNews()
    news_data = []
    search_results = gn.search(query)  # Perform the search

    for entry in search_results["entries"]:
        title = entry.get("title", "N/A")
        link = entry.get("link", "N/A")
        published = entry.get("published", "N/A")
        
        # Skip articles outside the date range
        if not is_within_date_range(published, start_date, end_date):
            continue

        # Clean the summary using BeautifulSoup to remove HTML tags
        summary_html = entry.get("summary", "N/A")
        summary_soup = BeautifulSoup(summary_html, "html.parser")
        summary_clean = summary_soup.get_text(strip=True)

        source = entry.get("source", {}).get("title", "N/A")

        # Fetch the full article text from the link
        full_article_text = get_full_article_text(link)

        # Generate a summarized version of the full article
        summary_generated = generate_summary(full_article_text)

        # Handle sub-articles
        sub_articles = entry.get("sub_articles", [])
        sub_articles_info = '; '.join([f"{sub.get('title', 'N/A')} ({sub.get('publisher', 'N/A')} - {sub.get('link', 'N/A')})" for sub in sub_articles])

        # Append data to news_data list
        news_data.append([title, link, published, summary_generated, source, full_article_text, sub_articles_info])

        # Stop collecting if the limit is reached
        if len(news_data) >= article_limit:
            break

    return news_data

# Streamlit app layout
st.title("News Scraper Web App")
st.write("Search and collect news articles with summaries.")

# Input fields
query = st.text_input("Search Query", "Sheikh Hasina")
start_date = st.date_input("Start Date", datetime(2023, 1, 1))
end_date = st.date_input("End Date", datetime(2023, 12, 31))
article_limit = st.slider("Number of Articles to Collect", 1, 1000, 10)

# Button to trigger search
if st.button("Search News"):
    if start_date > end_date:
        st.error("Start date cannot be after end date.")
    else:
        st.info(f"Searching for articles about '{query}' from {start_date} to {end_date}...")
        news_data = search_articles(query, start_date, end_date, article_limit)
        st.success(f"Collected {len(news_data)} articles.")

        # Display a preview of the collected data
        if news_data:
            st.write("Here are the first few articles:")
            st.write(news_data[:3])  # Display first few articles for preview

            # Prepare CSV data
            csv_headers = ['Title', 'Link', 'Published', 'Summary', 'Source', 'Full Article', 'Sub-Articles']
            csv_data = [csv_headers] + news_data

            # Function to convert the data into a CSV format
            def convert_to_csv(data):
                csv_file = ""
                for row in data:
                    csv_file += ','.join([f'"{col}"' for col in row]) + '\n'
                return csv_file

            # Allow user to download CSV
            csv_file = convert_to_csv(csv_data)
            st.download_button(
                label="Download CSV",
                data=csv_file,
                file_name="news_articles.csv",
                mime="text/csv"
            )
