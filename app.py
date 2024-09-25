import streamlit as st
import pandas as pd
from PIL import Image

# Set page config to wide mode and set the page title
st.set_page_config(layout="wide", page_title="VERITRACE metadata")

# Custom CSS to inject contained in a string
custom_css = """
<style>
    .sidebar .sidebar-content {
        background-image: linear-gradient(#2e7bcf,#2e7bcf);
        color: white;
    }
    .sidebar .sidebar-content .block-container {
        padding-top: 1rem;
    }
    .sidebar .sidebar-content .block-container h1 {
        color: white;
        font-size: 1.5rem;
        margin-bottom: 1rem;
    }
</style>
"""

# Inject custom CSS with Markdown
st.markdown(custom_css, unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("# VERITRACE metadata")
    st.markdown("---")

@st.cache_data
def get_total_records():
    with open('visualizations/total_records.txt', 'r') as f:
        return int(f.read().strip())

def main():
    st.title("VERITRACE Metadata Visualizations")
    
    st.subheader("*NOTE*: The VERITRACE metadata on this website is raw and has not yet been systematically cleaned. Please do not use it for analysis.")

    # Load total records
    total_records = get_total_records()
    
    # Center the text using HTML and CSS
    # Format the total_records with a period as the thousands separator
    formatted_total_records = f"{total_records:,}".replace(",", ".")
    
    st.markdown(f"<h2 style='text-align: center;'>Total number of records: {formatted_total_records}</h2>", unsafe_allow_html=True)

    # Display a divider with half the width using HTML and CSS
    st.markdown("<hr style='width: 50%; margin: auto;'>", unsafe_allow_html=True)
    
    # Display pre-computed visualizations
    st.subheader("Number of Records by Source Name")
    st.image('visualizations/source_name_chart.png')

    st.subheader("Number of Records by File Type")
    st.image('visualizations/file_type_chart.png')

    st.subheader("Distribution of Records by Date (1540-1728)")
    st.image('visualizations/date_histogram.png')

    st.subheader("Number of Records by Primary Language")
    st.image('visualizations/language_chart.png')

    st.subheader("Number of Records by Language for Each Data Source")
    st.image('visualizations/language_by_source_chart.png')

if __name__ == "__main__":
    main()