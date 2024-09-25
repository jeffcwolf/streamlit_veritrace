import streamlit as st
import pandas as pd
from PIL import Image

# Set page config to wide mode
st.set_page_config(layout="wide")

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

ROWS_PER_PAGE = 20  # Show 20 records per page

@st.cache_data
def load_data():
    return pd.read_json('veritrace.veritrace_all.json')

@st.cache_data
def get_total_records():
    with open('visualizations/total_records.txt', 'r') as f:
        return int(f.read().strip())

def display_dataframe(df, width=None, height=450):
    styled_df = df.style.set_table_styles([
        {'selector': 'th', 'props': [('background-color', '#4CAF50'), ('color', 'white')]},
        {'selector': 'tr:nth-child(even)', 'props': [('background-color', '#f2f2f2')]},
        {'selector': 'tr:hover', 'props': [('background-color', '#ddd')]},
    ])
    st.dataframe(styled_df, width=width, height=height, use_container_width=True)

def main():
    st.title("VERITRACE Metadata Visualizations")
    
    # Load data
    with st.spinner('Loading data...'):
        full_df = load_data()
    
    # Initialize session state for pagination
    if 'page' not in st.session_state:
        st.session_state.page = 1
    
    total_records = get_total_records()
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
    st.subheader("Number of Records by Source Name")
    st.image('visualizations/source_name_chart.png')
    
    # 2. Number of records by 'file_type'
    st.subheader("Number of Records by File Type")
    st.image('visualizations/file_type_chart.png')
    
    # 3. Date visualization for 'simple_clean_date'
    st.subheader("Distribution of Records by Date (1540-1728)")
    st.image('visualizations/date_histogram.png')
    
    # 4. Counts of records for 'primary_language_orig'
    st.subheader("Number of Records by Primary Language")
    st.image('visualizations/language_chart.png')

if __name__ == "__main__":
    main()