import streamlit as st
import os
import tempfile
import fitz
from lingua import Language, LanguageDetectorBuilder
from langdetect import detect as langdetect_detect
from langdetect import DetectorFactory
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import re

# Set the page title, which will also change the sidebar name
st.set_page_config(page_title="VERITRACE metadata")

# Set seed for langdetect to ensure consistent results
DetectorFactory.seed = 0

# Define the set of languages we're interested in (VERITRACE languages + Greek)
LANGUAGES = [
    Language.LATIN,
    Language.ENGLISH,
    Language.GERMAN,
    Language.FRENCH,
    Language.DUTCH,
    Language.ITALIAN,
    Language.GREEK
]

@st.cache_resource
def get_lingua_detector():
    return LanguageDetectorBuilder.from_languages(*LANGUAGES).build()

# Function to check if a PDF has a text layer
def has_text_layer(pdf_path):
    doc = fitz.open(pdf_path)
    for page in doc:
        if page.get_text().strip():
            return True
    return False

# Function to perform OCR on a PDF (placeholder - you'll need to implement this with an OCR library)
def ocr_pdf(pdf_path):
    # Placeholder for OCR functionality
    return "OCR text output would go here"

# Combined language detection function
def detect_language(text, lingua_detector):
    lingua_result = lingua_detector.detect_language_of(text)
    try:
        langdetect_result = langdetect_detect(text)
    except:
        langdetect_result = None
    
    if lingua_result and langdetect_result:
        if lingua_result.name.lower() == langdetect_result.lower():
            return lingua_result, 1.0  # Both agree, high confidence
        else:
            # They disagree, return Lingua's result with medium confidence
            return lingua_result, 0.7
    elif lingua_result:
        return lingua_result, 0.7  # Only Lingua detected, medium confidence
    elif langdetect_result:
        return Language[langdetect_result.upper()], 0.6  # Only langdetect detected, slightly lower confidence
    else:
        return None, 0.0  # Neither detected a language

def detect_languages(text, method='ngram', n=3):
    lingua_detector = get_lingua_detector()
    if method == 'ngram':
        return segment_languages_ngram(text, lingua_detector, n)
    elif method == 'lines':
        return segment_languages_lines(text, lingua_detector, n)
    else:
        st.error(f"Unknown segmentation method: {method}")
        return []

def segment_languages_ngram(text, lingua_detector, n=3):
    words = re.findall(r'\b\w+\b', text)
    segmented = []
    
    progress_bar = st.progress(0)
    total_segments = max(1, len(words) // n)  # Ensure total_segments is at least 1
    
    for i in range(0, len(words), n):
        chunk = ' '.join(words[i:i+n])
        lang, confidence = detect_language(chunk, lingua_detector)
        segmented.append((chunk, lang, confidence))
        
        # Ensure progress never exceeds 1.0
        progress = min(1.0, (i//n + 1) / total_segments)
        progress_bar.progress(progress)
    
    progress_bar.empty()  # Remove the progress bar when done
    return segmented

def segment_languages_lines(text, lingua_detector, n=3):
    lines = text.split('\n')
    segmented = []
    
    progress_bar = st.progress(0)
    total_segments = max(1, len(lines) // n)  # Ensure total_segments is at least 1
    
    for i in range(0, len(lines), n):
        chunk = '\n'.join(lines[i:i+n]).strip()
        if chunk:
            lang, confidence = detect_language(chunk, lingua_detector)
            segmented.append((chunk, lang, confidence))
        
        # Ensure progress never exceeds 1.0
        progress = min(1.0, (i//n + 1) / total_segments)
        progress_bar.progress(progress)
    
    progress_bar.empty()  # Remove the progress bar when done
    return segmented

def generate_language_report(segmented):
    total_segments = len(segmented)
    language_counts = Counter(lang.name if lang else "Unknown" for _, lang, _ in segmented)
    
    report = "Language Analysis Report\n"
    report += "========================\n\n"
    
    report += "Language Distribution:\n"
    for lang, count in language_counts.items():
        percentage = count / total_segments * 100
        report += f"  {lang}: {count} segments ({percentage:.2f}%)\n"
    report += "\n"
    
    report += "Segment Details:\n"
    for i, (chunk, lang, confidence) in enumerate(segmented[:10], 1):  # Show first 10 segments
        report += f"Segment {i}:\n"
        report += f"  Text: {chunk[:50]}{'...' if len(chunk) > 50 else ''}\n"
        report += f"  Detected Language: {lang.name if lang else 'Unknown'}\n"
        report += f"  Confidence: {confidence:.2%}\n"
        report += "\n"
    
    if len(segmented) > 10:
        report += f"... and {len(segmented) - 10} more segments\n"
    
    return report

def main():
    st.title("VERITRACE Labs - PDF Multilingual Language Analyzer")

    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        # File information
        st.subheader("File Information")
        file_size = os.path.getsize(tmp_file_path) / (1024 * 1024)  # Size in MB
        has_text = has_text_layer(tmp_file_path)
        st.write(f"File name: {uploaded_file.name}")
        st.write(f"File size: {file_size:.2f} MB")
        st.write(f"Has text layer: {'Yes' if has_text else 'No'}")

        # Extract text
        if has_text:
            doc = fitz.open(tmp_file_path)
            text = ""
            for page in doc:
                text += page.get_text()
        else:
            text = ocr_pdf(tmp_file_path)
        
        # Language analysis options
        st.subheader("Language Analysis Options")
        st.write("The default option is recommended.")
        analysis_method = st.selectbox("Choose analysis method", ["lines", "ngram"], index=0)  # Set "lines" as default
        if analysis_method == "lines":
            n = st.slider("Select number of lines", min_value=1, max_value=10, value=2)  # Default to 2 lines
        else:
            n = st.slider("Select n-gram size", min_value=1, max_value=10, value=3)  # Keep 3 as default for n-grams

        if st.button("Analyze"):
            with st.spinner('Analyzing languages...'):
                # Detect languages
                language_spans = detect_languages(text, method=analysis_method, n=n)

                if not language_spans:
                    st.warning("No text detected in the document.")
                else:
                    # Generate report
                    report = generate_language_report(language_spans)

                    # Display language statistics
                    st.subheader("Language Statistics")
                    lang_stats = Counter(lang.name if lang else "Unknown" for _, lang, _ in language_spans)

                    # Create a bar plot with a color palette and gradient styling
                    fig, ax = plt.subplots(figsize=(10, 6))  # Adjust the figure size
                    colors = sns.color_palette("viridis", len(lang_stats))
                    sns.barplot(x=list(lang_stats.keys()), y=list(lang_stats.values()), ax=ax, palette=colors, width=0.5)  # Adjust the bar width

                    # Add gradient styling
                    for i, bar in enumerate(ax.patches):
                        bar.set_facecolor(colors[i])

                    plt.title("Language Distribution")
                    plt.xticks(rotation=45)
                    st.pyplot(fig)

                    # Provide download link for the report
                    st.download_button(
                        label="Download Language Analysis Report",
                        data=report,
                        file_name="language_analysis_report.txt",
                        mime="text/plain"
                    )

                    # Display report summary
                    st.subheader("Language Analysis Summary")
                    st.text(report)

        # Clean up
        os.unlink(tmp_file_path)

if __name__ == "__main__":
    main()