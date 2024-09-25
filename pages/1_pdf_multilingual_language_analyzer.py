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
from collections import Counter, deque
import re
import magic
import hashlib
import PyPDF2
import time

st.set_page_config(page_title="PDF Multilingual Language Analyzer")

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

# Rate limiting
RATE_LIMIT = 5  # number of uploads allowed
RATE_LIMIT_PERIOD = 300  # in seconds (5 minutes)
upload_times = deque()

@st.cache_resource
def get_lingua_detector():
    return LanguageDetectorBuilder.from_languages(*LANGUAGES).build()

def is_valid_pdf(file):
    mime = magic.Magic(mime=True)
    file_type = mime.from_buffer(file.getvalue())
    return file_type == 'application/pdf'

def get_file_hash(file):
    return hashlib.md5(file.getvalue()).hexdigest()

def scan_pdf_for_malicious_content(file_path):
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page in pdf_reader.pages:
                if '/JavaScript' in page or '/JS' in page:
                    return False, "PDF contains JavaScript, which could be malicious."
            
            if '/EmbeddedFiles' in pdf_reader.trailer['/Root']:
                return False, "PDF contains embedded files, which could be malicious."
            
            return True, "PDF appears safe."
    except PyPDF2.errors.PdfReadError:
        return False, "Invalid or corrupted PDF file."
    except Exception as e:
        return False, f"Error scanning PDF: {str(e)}"

def check_rate_limit():
    current_time = time.time()
    while upload_times and current_time - upload_times[0] > RATE_LIMIT_PERIOD:
        upload_times.popleft()
    
    if len(upload_times) >= RATE_LIMIT:
        return False
    
    upload_times.append(current_time)
    return True

def has_text_layer(pdf_path):
    doc = fitz.open(pdf_path)
    for page in doc:
        if page.get_text().strip():
            return True
    return False

def ocr_pdf(pdf_path):
    # Placeholder for OCR functionality
    return "OCR text output would go here"

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

def detect_languages(text, method='lines', n=2):
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

def segment_languages_lines(text, lingua_detector, n=2):
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
        if not check_rate_limit():
            st.error(f"Rate limit exceeded. Please wait before uploading again.")
            return

        if not is_valid_pdf(uploaded_file):
            st.error("Invalid file type. Please upload a PDF file.")
            return

        file_hash = get_file_hash(uploaded_file)
        st.write(f"File hash: {file_hash}")

        if uploaded_file.size > 10 * 1024 * 1024:  # 10 MB limit
            st.error("File is too large. Please upload a file smaller than 10 MB.")
            return

        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        try:
            is_safe, message = scan_pdf_for_malicious_content(tmp_file_path)
            if not is_safe:
                st.error(message)
                return

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
            analysis_method = st.selectbox("Choose analysis method", ["lines", "ngram"], index=0)
            if analysis_method == "lines":
                n = st.slider("Select number of lines", min_value=1, max_value=10, value=2)
            else:
                n = st.slider("Select n-gram size", min_value=1, max_value=10, value=3)

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
                        fig, ax = plt.subplots(figsize=(10, 6))
                        colors = sns.color_palette("viridis", len(lang_stats))
                        sns.barplot(x=list(lang_stats.keys()), y=list(lang_stats.values()), ax=ax, palette=colors, width=0.5)

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

        finally:
            # Clean up
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

if __name__ == "__main__":
    main()