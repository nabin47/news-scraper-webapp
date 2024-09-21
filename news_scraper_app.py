import streamlit as st
from GoogleNews import GoogleNews
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

# Function to search for news articles using GoogleNews
def search_articles(query, start_date, end_date, article_limit):
    gn = GoogleNews()
    gn.set_lang('en')
    gn.set_time_range(start_date.strftime('%m/%d/%Y'), end_date.strftime('%m/%d/%Y'))
    search_results = gn.search(query)  # Perform the search
    news_data = []

    for entry in gn.results()[:article_limit]:
        title = entry.get("title", "N/A")
        link = entry.get("link", "N/A")
        published = entry.get("date", "N/A")

        # Fetch the full article text from the link
        full_article_text = get_full_article_text(link)

        # Generate a summarized version of the full article
        summary_generated = generate_summary(full_article_text)

        # Append data to news_data list
        news_data.append([title, link, published, summary_generated, full_article_text])

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
            csv_headers = ['Title', 'Link', 'Published', 'Summary', 'Full Article']
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
