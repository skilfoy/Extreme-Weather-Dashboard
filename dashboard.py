
import streamlit as st
import pandas as pd
from googlesearch import search
from datetime import datetime
import time
import requests
from bs4 import BeautifulSoup
from requests.exceptions import HTTPError
import random

# Function to perform Google search and return results in a DataFrame
def google_search(query, num_results=5, max_retries=5):
    search_results = []
    retry_count = 0
    sleep_interval = 5  # Start with a 5 second sleep interval

    while len(search_results) < num_results and retry_count < max_retries:
        try:
            results = list(
                search(
                    term=query,
                    num_results=num_results,
                    sleep_interval=sleep_interval,
                    lang="en",
                    advanced=True
                )
            )
            search_results.extend(results)
            break  # Exit the loop if successful
        except HTTPError as e:
            if e.response.status_code == 429:
                retry_count += 1
                sleep_interval *= 2  # Exponential backoff
                time.sleep(sleep_interval)
            else:
                raise e

    data = []
    retrieval_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for result in search_results[:num_results]:
        url = result.url
        title = result.title
        description = result.description  # Use full description from the search result
        result_dict = {
            'URL': url,
            'Title': title,
            'Description': description,
            'Retrieval Time': retrieval_time
        }
        data.append(result_dict)

    return pd.DataFrame(data)

# Streamlit application
st.set_page_config(layout="wide", initial_sidebar_state="collapsed")
st.title("Real-Time Extreme Weather Search Dashboard")

# Sidebar control panel
st.sidebar.title("Control Panel")
refresh_interval = st.sidebar.slider("Update Interval (seconds)", min_value=1, max_value=300, value=10)
num_results = st.sidebar.slider("Number of Top Results", min_value=1, max_value=10, value=5)

# Initialize session state for queries and saved articles
if 'queries' not in st.session_state:
    st.session_state.queries = ["Hurricane", "Winter snowstorm"]
if 'saved_articles' not in st.session_state:
    st.session_state.saved_articles = []

# Function to add a new search query
def add_search():
    st.session_state.queries.append("New Query")
    st.rerun()  # Immediately refresh the app to reflect changes

# Function to remove a search query
def remove_search(index):
    if len(st.session_state.queries) > 1:
        st.session_state.queries.pop(index)
        st.rerun()  # Immediately refresh the app to reflect changes

# Function to save an article
def save_article(url, title, description):
    st.session_state.saved_articles.append({
        'Title': title,
        'URL': url,
        'Description': description
    })
    st.rerun()

# Display input fields for each query with remove button
for i, query in enumerate(st.session_state.queries):
    cols = st.sidebar.columns([5, 1])
    query_input = cols[0].text_input(f"Search Query {i+1}", value=query, key=f"query_{i}")
    cols[1].button("–", key=f"remove_{i}", on_click=remove_search, args=(i,))
    st.session_state.queries[i] = query_input

# Add button for new search
st.sidebar.markdown(
    """
    <style>
    .full-width-button > div > button {
        width: 100%;
        font-size: 24px;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True
)

if st.sidebar.button("＋", key="add", help="Add New Search Query"):
    add_search()

# Main content: Query results
st.header("Query Results")
placeholders = [st.empty() for _ in st.session_state.queries]

def update_dashboard():
    for i, query in enumerate(st.session_state.queries):
        results = google_search(query, num_results=num_results)
        with placeholders[i].container():
            st.subheader(f"Top {num_results} Results for '{query}'")
            for idx, row in results.iterrows():
                result_key = f"{query}_{idx}_{int(time.time())}"
                title_col, save_col = st.columns([5, 1])
                title_col.markdown(
                    f"""
                    <a href="{row['URL']}" target="_blank">
                        <button style="width: 100%; font-size: 20px; font-weight: bold;">
                            {row['Title']}
                        </button>
                    </a>
                    """,
                    unsafe_allow_html=True
                )
                save_col.button("＋", key=f"save_{result_key}", on_click=save_article, args=(row['URL'], row['Title'], row['Description']))
                st.markdown(f"<div style='text-align: justify;'>{row['Description']}</div>", unsafe_allow_html=True)

update_dashboard()

# Right sidebar: Saved articles
st.sidebar.subheader("Saved Articles")
for article in st.session_state.saved_articles:
    st.sidebar.markdown(f"**[{article['Title']}]({article['URL']})**")
    st.sidebar.markdown(f"{article['Description']}")

# Main loop to refresh the dashboard at the specified interval
while True:
    update_dashboard()
    time.sleep(refresh_interval)
