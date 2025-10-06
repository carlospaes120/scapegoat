import re
import string
from unidecode import unidecode

def clean_texts(text):
    if not isinstance(text, str):
        return "", ""

    # Remove URLs
    text = re.sub(r"http\S+|www\S+|pic\.twitter\.com\S+", "", text)
    
    # Remove mentions and hashtags (optional for transformers)
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"#\w+", "", text)
    
    # Remove multiple spaces
    text = re.sub(r"\s+", " ", text).strip()

    # === Version 1: for Transformers ===
    cleaned_text = text

    # === Version 2: for Classic ML (BoW, TF-IDF) ===
    text_bow = cleaned_text.lower()
    text_bow = unidecode(text_bow)  # Remove accents
    text_bow = re.sub(rf"[{re.escape(string.punctuation)}]", "", text_bow)  # Remove punctuation
    text_bow = re.sub(r"\s+", " ", text_bow).strip()

    return cleaned_text, text_bow
