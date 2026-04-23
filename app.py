import pandas as pd
import json
import os
import requests
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from urllib.parse import quote
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
CORS(app)

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

# =========================
# LOAD DATA (NO PKL)
# =========================
movies = pd.read_csv("tmdb_5000_movies.csv")

movies['overview'] = movies['overview'].fillna('')
movies['genres_list'] = movies['genres'].apply(
    lambda x: [i['name'] for i in eval(x)] if isinstance(x, str) else []
)

# TF-IDF + similarity
tfidf = TfidfVectorizer(stop_words='english', max_features=5000)
tfidf_matrix = tfidf.fit_transform(movies['overview'])
similarity = cosine_similarity(tfidf_matrix)

# =========================
# POSTER CACHE
# =========================
OMDB_API_KEY = "f4cd20e4"

try:
    poster_cache = json.load(open('poster_cache.json'))
except:
    poster_cache = {}

def get_poster_url(title):
    if title in poster_cache:
        return poster_cache[title]

    try:
        url = f"https://www.omdbapi.com/?t={quote(title)}&apikey={OMDB_API_KEY}"
        response = requests.get(url, timeout=5)
        data = response.json()

        if data.get('Poster') and data['Poster'] != 'N/A':
            poster_cache[title] = data['Poster']
            json.dump(poster_cache, open('poster_cache.json', 'w'))
            return data['Poster']
    except:
        pass

    return "https://via.placeholder.com/300x450"

# =========================
# USER DATA
# =========================
user_ratings = {}
user_likes = {}
user_history = {}

# =========================
# RECOMMEND FUNCTION
# =========================
def recommend(movie, n=10):
    try:
        idx = movies[movies['title'] == movie].index[0]
    except:
        return []

    scores = list(enumerate(similarity[idx]))
    scores = sorted(scores, key=lambda x: x[1], reverse=True)[1:n+1]

    result = []
    for i in scores:
        title = movies.iloc[i[0]]['title']
        genres = movies.iloc[i[0]]['genres_list']

        result.append({
            'title': title,
            'poster': get_poster_url(title),
            'similarity': round(float(i[1]) * 100, 1),
            'genres': genres[:3]
        })

    return result

# =========================
# ROUTES
# =========================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/recommend')
def recommend_api():
    movie = request.args.get('movie', '')
    return jsonify(recommend(movie, 10))

@app.route('/search')
def search_movies():
    q = request.args.get('q', '')
    results = movies[movies['title'].str.contains(q, case=False, na=False)]

    return jsonify([
        {'title': row['title'], 'poster': get_poster_url(row['title'])}
        for _, row in results.head(10).iterrows()
    ])

@app.route('/trending')
def trending():
    top = movies.sort_values(by='popularity', ascending=False).head(20)

    return jsonify([
        {
            'title': row['title'],
            'poster': get_poster_url(row['title']),
            'genres': row['genres_list'][:3]
        }
        for _, row in top.iterrows()
    ])

# =========================
# RUN
# =========================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)