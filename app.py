import streamlit as st
import pymongo
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import datetime

# Set page config to wide mode
st.set_page_config(layout="wide")

# MongoDB connection
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["veritrace"]
collection = db["veritrace_all"]

ROWS_PER_PAGE = 20  # Show 20 records per page

# Custom CSS to style the app
st.markdown("""
<style>
    .stApp {
        max-width: 1400px;
        padding-top: 2rem;
    }
    .stDataFrame {
        width: 100%;
    }
    .dataframe {
        font-family: Arial, sans-serif;
        border-collapse: collapse;
        width: 100%;
    }
    .dataframe th {
        background-color: #4CAF50 !important;
        color: white !important;
        text-align: left;
        padding: 12px;
    }
    .dataframe td {
        padding: 12px;
        border-bottom: 1px solid #ddd;
    }
    .dataframe tr:nth-child(even) {
        background-color: #f2f2f2;
    }
    .dataframe tr:hover {
        background-color: #ddd;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def fetch_all_data():
    data = list(collection.find({}, {'_id': 0}))
    return pd.DataFrame(data)

def fetch_paginated_data(skip, limit):
    data = list(collection.find().skip(skip).limit(limit))
    return pd.DataFrame(data)

def get_total_records():
    return collection.count_documents({})

def display_dataframe(df, width=None, height=450):
    styled_df = df.style.set_table_styles([
        {'selector': 'th', 'props': [('background-color', '#4CAF50'), ('color', 'white')]},
        {'selector': 'tr:nth-child(even)', 'props': [('background-color', '#f2f2f2')]},
        {'selector': 'tr:hover', 'props': [('background-color', '#ddd')]},
    ])
    st.dataframe(styled_df, width=width, height=height, use_container_width=True)

def plot_bar_chart(df, column, title, top_n=20):
    plt.figure(figsize=(12, 6))
    value_counts = df[column].value_counts().nlargest(top_n)
    ax = sns.barplot(x=value_counts.index, y=value_counts.values)
    plt.title(title)
    plt.xlabel(column)
    plt.ylabel('Count')
    plt.xticks(rotation=45, ha='right')
    
    # Add count labels on top of each bar
    for i, v in enumerate(value_counts.values):
        ax.text(i, v, str(v), ha='center', va='bottom')
    
    plt.tight_layout()
    st.pyplot(plt)

def plot_date_histogram(df, date_column):
    df[date_column] = pd.to_numeric(df[date_column], errors='coerce')
    df = df[(df[date_column] >= 1540) & (df[date_column] <= 1728)]
    
    plt.figure(figsize=(12, 6))
    ax = sns.histplot(data=df, x=date_column, bins=188, kde=True)
    plt.title('Distribution of Records by Date (1540-1728)', fontsize=14)
    plt.xlabel('Year', fontsize=12)
    plt.ylabel('Count', fontsize=12)
    plt.xticks(fontsize=11)
    plt.yticks(fontsize=11)
    
    # Remove the top and right spines
    sns.despine()
    
    plt.tight_layout()
    st.pyplot(plt)

def main():
    st.title("VERITRACE Metadata Visualizations")
    
    # Fetch all data for analytics and search
    with st.spinner('Loading all data...'):
        full_df = fetch_all_data()
    
    # Initialize session state for pagination
    if 'page' not in st.session_state:
        st.session_state.page = 1
    
    total_records = len(full_df)
    total_pages = -(-total_records // ROWS_PER_PAGE)  # Ceiling division
    
    # Display searchable dataframe
    st.subheader(f"Raw Data (Page {st.session_state.page} of {total_pages})")
    
    # Allow user to adjust width
    width = st.slider("Adjust dataframe width", min_value=800, max_value=1400, value=1200, step=50)
    
    # Pagination
    skip = (st.session_state.page - 1) * ROWS_PER_PAGE
    display_df = full_df.iloc[skip:skip+ROWS_PER_PAGE]
    
    display_dataframe(display_df, width=width)
    
    # Pagination controls
    col1, col2, col3 = st.columns([1,2,1])
    
    with col1:
        if st.button("⬅️ Previous") and st.session_state.page > 1:
            st.session_state.page -= 1
            st.rerun()
    
    with col2:
        st.write(f"Showing records {skip+1} to {min(skip+ROWS_PER_PAGE, total_records)} out of {total_records}")
    
    with col3:
        if st.button("Next ➡️") and st.session_state.page < total_pages:
            st.session_state.page += 1
            st.rerun()
    
    # Analytics
    st.markdown("## Analytics")
    
    # 1. Number of records by 'source_name' column
    if 'source_name' in full_df.columns:
        st.subheader("Number of Records by Source Name")
        plot_bar_chart(full_df, 'source_name', 'Records by Source Name')
    
    # 2. Number of records by 'file_type'
    if 'file_type' in full_df.columns:
        st.subheader("Number of Records by File Type")
        plot_bar_chart(full_df, 'file_type', 'Records by File Type')
    
    # 3. Date visualization for 'simple_clean_date'
    if 'simple_clean_date' in full_df.columns:
        st.subheader("Distribution of Records by Date (1540-1728)")
        plot_date_histogram(full_df, 'simple_clean_date')
    
    # 4. Counts of records for 'primary_language_orig'
    if 'primary_language_orig' in full_df.columns:
        st.subheader("Number of Records by Primary Language")
        plot_bar_chart(full_df, 'primary_language_orig', 'Records by Primary Language')

if __name__ == "__main__":
    main()