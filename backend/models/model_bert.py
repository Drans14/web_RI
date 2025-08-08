import os
import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tqdm import tqdm
from joblib import Parallel, delayed
from sklearn.feature_extraction.text import CountVectorizer
from bertopic import BERTopic
from hdbscan import HDBSCAN
from sentence_transformers import SentenceTransformer
from umap import UMAP
from gensim.models.coherencemodel import CoherenceModel
from gensim.corpora.dictionary import Dictionary
from bertopic.representation import KeyBERTInspired
import joblib
import requests
import json
from .preprocessing import preprocess_dataframe,simple_tokenizer
import torch
import plotly.io as pio
import plotly.express as px


def bertopic_analysis(df):
    try:
        df_processed = preprocess_dataframe(df)
        docs_series = df_processed['Title'].astype(str) + " " + df_processed['Abstract'].astype(str)
        docs = docs_series.tolist()
        n_docs = len(docs)
        print(f"Total dokumen valid: {n_docs}")

        if n_docs < 5:
            raise ValueError("Terlalu sedikit dokumen untuk analisis topic modeling")

        print("Membuat embeddings...")
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        embedding_model = SentenceTransformer("all-MiniLM-L6-v2", device=device)
        embeddings = embedding_model.encode(docs, show_progress_bar=True, batch_size=64, device=device)

        try:
            umap_model = joblib.load("save_models/umap_model.joblib")
            vectorizer_model = joblib.load("save_models/vectorizer_model.joblib")
            ctfidf_model = joblib.load("save_models/ctfidf_model.joblib")
            representation_model = KeyBERTInspired()
        except Exception as e:
            print(f"Error loading models: {e}")
            return {"error": f"Model files tidak ditemukan: {str(e)}", "plot_html": None}

        print("Tokenizing documents...")
        docs_tokenized = simple_tokenizer(docs)
        dictionary = Dictionary(docs_tokenized)

        # Step 6: Tentukan range min_cluster_size berdasarkan jumlah dokumen
        if n_docs < 500:
            min_cluster_range = range(4, 18)
        elif n_docs < 1000:
            min_cluster_range = range(8, 25)
        elif n_docs < 1500:
            min_cluster_range = range(12, 30)
        elif n_docs < 2500:
            min_cluster_range = range(15, 35)
        elif n_docs < 3500:
            min_cluster_range = range(18, 42)
        elif n_docs < 4500:
            min_cluster_range = range(20, 45)
        elif n_docs < 5500:
            min_cluster_range = range(21, 50)
        elif n_docs < 6500:
            min_cluster_range = range(23, 50)
        elif n_docs < 7500:
            min_cluster_range = range(25, 55)
        elif n_docs < 8500:
            min_cluster_range = range(30, 60)
        elif n_docs < 10000:
            min_cluster_range = range(35, 65)
        else:
            min_cluster_range = range(50, 85)

        print(f"Evaluasi min_cluster_size: {list(min_cluster_range)}")

        def evaluate_min_cluster(min_cluster):
            try:
                hdbscan_model = HDBSCAN(
                    min_cluster_size=min_cluster,
                    metric='euclidean',
                    cluster_selection_method='eom',
                    prediction_data=False,
                    core_dist_n_jobs=-2
                )
                topic_model = BERTopic(
                    embedding_model=embedding_model,
                    umap_model=umap_model,
                    hdbscan_model=hdbscan_model,
                    vectorizer_model=vectorizer_model,
                    ctfidf_model=ctfidf_model,
                    verbose=False
                )
                topic_model.fit(docs, embeddings)
                topic_words = []
                topic_freq = topic_model.get_topic_freq()
                topic_ids = topic_freq[(topic_freq['Count'] >= 5) & (topic_freq['Topic'] != -1)]['Topic'].tolist()
                topic_ids = [t for t in topic_ids if t != -1]
                for topic_id in topic_ids:
                    words = topic_model.get_topic(topic_id)
                    if isinstance(words, list):
                        topic_words.append([word for word, _ in words])
                if len(topic_words) > 1:
                    coherence_model = CoherenceModel(
                        topics=topic_words,
                        texts=docs_tokenized,
                        dictionary=dictionary,
                        coherence='c_v',
                        processes=1,
                        topn=15
                    )
                    coherence = coherence_model.get_coherence()
                    return (min_cluster, coherence, topic_model)
                else:
                    return (min_cluster, np.nan, None)
            except Exception as e:
                print(f"min_cluster_size = {min_cluster} → ERROR: {str(e)}")
                return (min_cluster, np.nan, None)

        results = []
        for m in tqdm(min_cluster_range, desc="Evaluating cluster sizes"):
            result = evaluate_min_cluster(m)
            results.append(result)

        best_score = -1
        best_size = None
        best_model = None

        # Simpan opsi cluster yang valid untuk dropdown
        valid_clusters = []
        
        for min_cluster, coherence, model in results:
            if not np.isnan(coherence):
                print(f"min_cluster_size = {min_cluster} → Coherence = {coherence:.4f}")
                valid_clusters.append(min_cluster)
                if coherence > best_score:
                    best_score = coherence
                    best_size = min_cluster
                    best_model = model
            else:
                print(f"min_cluster_size = {min_cluster} → Tidak cukup topik atau error")

        filtered = [(m, c) for m, c, _ in results if not np.isnan(c)]
        plot_html = None

        if filtered:
            min_clusters = [x[0] for x in filtered]
            scores = [x[1] for x in filtered]

            plot_df = pd.DataFrame({
                'min_cluster_size': min_clusters,
                'coherence_score': scores
            })

            fig = px.line(
                plot_df,
                x='min_cluster_size',
                y='coherence_score',
                markers=True,
                title="Coherence Score vs. min_cluster_size (HDBSCAN)",
                labels={
                    'min_cluster_size': 'Min Cluster Size',
                    'coherence_score': 'Coherence Score'
                }
            )

            fig.update_layout(width=800, height=500, showlegend=False)

            if best_score > -1 and best_size is not None:
                fig.add_vline(
                    x=best_size,
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"Best: {best_size} (Score: {best_score:.4f})",
                    annotation_position="top left"
                )

            plot_html = pio.to_html(fig, full_html=False, include_plotlyjs='cdn', div_id="coherence-plot")

        # Siapkan data untuk cache (untuk generate topics nanti)
        cache_data = {
            "docs": docs,
            "embeddings": embeddings,
            "embedding_model": embedding_model,
            "umap_model": umap_model,
            "vectorizer_model": vectorizer_model,
            "ctfidf_model": ctfidf_model,
            "representation_model": representation_model,
        }

        return {
            "plot_html": plot_html,
            "best_params": {
                "min_cluster_size": best_size,
                "coherence_score": best_score
            },
            "cluster_options": sorted(valid_clusters),  # Kirim opsi cluster yang valid
            "cache_data": cache_data  # Data untuk di-cache
        }

    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "plot_html": None
        }

    
def generate_topics_with_label(
    docs,
    embeddings,
    embedding_model,
    umap_model,
    vectorizer_model,
    ctfidf_model,
    representation_model,
    min_cluster_size
):
    try:
        print(f"Generating topics with min_cluster_size: {min_cluster_size}")
        
        # Buat model HDBSCAN baru dengan parameter yang dipilih user
        hdbscan_model = HDBSCAN(
            min_cluster_size=min_cluster_size,
            metric='euclidean',
            cluster_selection_method='eom',
            prediction_data=True
        )

        # Buat model BERTopic dengan semua komponen yang sudah ada
        topic_model = BERTopic(
            embedding_model=embedding_model,
            umap_model=umap_model,
            hdbscan_model=hdbscan_model,
            vectorizer_model=vectorizer_model,
            ctfidf_model=ctfidf_model,
            representation_model=representation_model,
            calculate_probabilities=True,
            verbose=True
        )

        print("Fitting topic model...")
        topics, probs = topic_model.fit_transform(docs, embeddings)
        
        print("Reducing outliers...")
        new_topics = topic_model.reduce_outliers(docs, topics, strategy="distributions")
        topic_model.update_topics(docs, topics=new_topics, vectorizer_model=vectorizer_model)

        print("Getting topic info...")
        topic_info = topic_model.get_topic_info()
        
        # Generate labels menggunakan Groq API
        print("Generating labels with Groq API...")
        auto_labels = generate_labels_with_groq(topic_info)

        # Update topic info dengan labels
        for topic_id, label in auto_labels.items():
            topic_info.loc[topic_info['Topic'] == topic_id, 'Name'] = label

        return topic_model, topic_info

    except Exception as e:
        import traceback
        print("Error in generate_topics_with_label:")
        print(traceback.format_exc())
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }


def generate_labels_with_groq(topic_info):
    """Generate labels untuk setiap topik menggunakan Groq API"""
    auto_labels = {}
    api_key = "masukan_api_key_di_sini"  # Ganti dengan API key Groq Anda
    base_url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    for _, row in topic_info.iterrows():
        topic_id = row["Topic"]
        if topic_id == -1:
            continue  # Skip outlier topics

        words = row["Representation"]
        prompt = f"""Generate a short and clear topic label (maximum 5 words) based on the following keywords:
{words}
The label must:
- Be in English
- Accurately represent the core meaning of the keywords
- Be concise and descriptive
- Return only the label text (no explanations)"""

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 20
        }

        try:
            response = requests.post(base_url, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                label = response.json()['choices'][0]['message']['content'].strip()
                auto_labels[topic_id] = label
                print(f"Topic {topic_id}: {label}")
            else:
                print(f"API Error for topic {topic_id}: {response.status_code}")
                auto_labels[topic_id] = f"Topic {topic_id}"
        except Exception as e:
            print(f"Error generating label for topic {topic_id}: {str(e)}")
            auto_labels[topic_id] = f"Topic {topic_id}"

    return auto_labels