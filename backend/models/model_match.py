"""
Keyword Matching module untuk Research Intelligence
Handles keyword matching analysis with topics and documents
"""

import pandas as pd
import re
from collections import defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

# Import preprocessing functions
from .preprocessing import preprocess_dataframe, combine_title_abstract


def ensure_nltk_data():
    """
    Memastikan NLTK data tersedia untuk keyword matching
    """
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
    except LookupError:
        print("Downloading required NLTK data...")
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)


def preprocess_keywords(keywords):
    """
    Preprocessing keywords list
    
    Args:
        keywords: List of keywords atau string separated by comma
        
    Returns:
        list: Cleaned keywords list
    """
    if isinstance(keywords, str):
        # Split by comma if single string
        keywords = [k.strip() for k in keywords.split(',')]
    
    # Clean and filter keywords
    cleaned_keywords = []
    for keyword in keywords:
        if isinstance(keyword, str) and keyword.strip():
            # Basic cleaning
            cleaned = re.sub(r'[^\w\s]', ' ', keyword.strip().lower())
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            if len(cleaned) > 1:  # Skip single characters
                cleaned_keywords.append(cleaned)
    
    return list(set(cleaned_keywords))  # Remove duplicates


def keyword_matching(topics_info, keywords_list, threshold=0.1):
    """
    Mencocokkan keywords dengan topics yang dihasilkan BERTopic (basic string matching)
    
    Args:
        topics_info: Output dari BERTopic (DataFrame, dict, atau list)
        keywords_list: List keywords yang ingin dicari
        threshold: Threshold untuk matching (tidak digunakan di basic matching)
    
    Returns:
        dict: Hasil matching keywords dengan topics
    """
    matches = defaultdict(list)
    
    # Preprocess keywords
    keywords_list = preprocess_keywords(keywords_list)