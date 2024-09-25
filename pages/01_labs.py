import streamlit as st
import os
import tempfile
import fitz
import re
from collections import Counter
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from transformers import XLMRobertaTokenizer, XLMRobertaForSequenceClassification
import torch
from lingua import Language, LanguageDetectorBuilder
import fasttext
import langid

# Initialize models
@st.cache_resource
def load_models():
    # FastText
    fasttext_model = fasttext.load_model('lid.176.bin')
    
    # Lingua
    lingua_detector = LanguageDetectorBuilder.from_languages(
        Language.ENGLISH, Language.FRENCH, Language.LATIN, Language.GREEK
    ).build()
    
    # XLM-RoBERTa
    tokenizer = XLMRobertaTokenizer.from_pretrained("xlm-roberta-base")
    model = XLMRobertaForSequenceClassification.from_pretrained("xlm-roberta-base")
    
    return fasttext_model, lingua_detector, tokenizer, model

# Function to detect language using ensemble method
def detect_language(word, fasttext_model, lingua_detector, xlmr_tokenizer, xlmr_model):
    # FastText prediction
    fasttext_lang = fasttext_model.predict(word)[0][0].split('__')[-1]
    
    # Lingua prediction
    lingua_lang = lingua_detector.detect_language_of(word)
    
    # langid prediction
    langid_lang, _ = langid.classify(word)
    
    # XLM-RoBERTa prediction
    inputs = xlmr_tokenizer(word, return_tensors="pt")
    with torch.no_grad():
        outputs = xlmr_model(**inputs)
    xlmr_lang = xlmr_tokenizer.decode(outputs.logits.argmax().item())
    
    # Voting system
    votes = Counter([fasttext_lang, str(lingua_lang), langid_lang, xlmr_lang])
    most_common = votes.most_common(1)[0]
    
    # If there's a clear winner, return it. Otherwise, prefer Lingua for Latin/Greek
    if most_common[1] > 1:
        return most_common[0]
    elif lingua_lang in [Language.LATIN, Language.GREEK]:
        return str(lingua_lang)
    else:
        return most_common[0]

def process_document(text, fasttext_model, lingua_detector, xlmr_tokenizer, xlmr_model):
    words = re.findall(r'\b\w+\b', text)
    results = []
    
    progress_bar = st.progress(0)
    for i, word in enumerate(words):
        lang = detect_language(word, fasttext_model, lingua_detector, xlmr_tokenizer, xlmr_model)
        results.append((word, lang))
        progress_bar.progress((i + 1) / len(words))
    
    progress_bar.empty()
    return results

def generate_report(results):
    total_words = len(results)
    language_counts = Counter(lang for _, lang in results)
    
    report = "Language Analysis Report\n"
    report += "========================\n\n"
    
    report += "Language Distribution:\n"
    for lang, count in language_counts.items():
        percentage = count / total_words * 100
        report += f"  {lang}: {count} words ({percentage:.2f}%)\n"
    report += "\n"
    
    report += "Word Details (first 100 words):\n"
    for word, lang in results[:100]:
        report += f"  {word}: {lang}\n"
    
    if len(results) > 100:
        report += f"... and {len(results) - 100} more words\n"
    
    return report

def main():
    st.title("High-Accuracy Multilingual Document Analyzer")

    fasttext_model, lingua_detector, xlmr_tokenizer, xlmr_model = load_models()

    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        # Extract text
        doc = fitz.open(tmp_file_path)
        text = ""
        for page in doc:
            text += page.get_text()

        if st.button("Analyze"):
            with st.spinner('Analyzing languages...'):
                results = process_document(text, fasttext_model, lingua_detector, xlmr_tokenizer, xlmr_model)

                if not results:
                    st.warning("No text detected in the document.")
                else:
                    # Generate report
                    report = generate_report(results)

                    # Display language statistics
                    st.subheader("Language Statistics")
                    lang_stats = Counter(lang for _, lang in results)
                    fig, ax = plt.subplots()
                    sns.barplot(x=list(lang_stats.keys()), y=list(lang_stats.values()), ax=ax)
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