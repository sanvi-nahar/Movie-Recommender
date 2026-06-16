from dotenv import load_dotenv
load_dotenv()
from supabase import create_client
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import os
import requests
from urllib.parse import quote
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
import threading
from concurrent.futures import ThreadPoolExecutor

# =========================
# POSTER CACHE SETUP
# =========================
POSTER_CACHE_FILE = "poster_cache.json"
poster_cache = {}
cache_lock = threading.Lock()

try:
    if os.path.exists(POSTER_CACHE_FILE):
        with open(POSTER_CACHE_FILE, "r", encoding="utf-8") as f:
            poster_cache = json.load(f)
except Exception as e:
    print("Error loading poster cache:", e)

def save_poster_cache():
    try:
        with open(POSTER_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(poster_cache, f, indent=4)
    except Exception as e:
        print("Error saving poster cache:", e)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
CORS(app)

# =========================
# LOAD DATA
# =========================
movies = pd.read_csv("data/tmdb_5000_movies.csv")

movies['overview'] = movies['overview'].fillna('')
movies['genres_list'] = movies['genres'].apply(
    lambda x: [i['name'] for i in eval(x)] if isinstance(x, str) else []
)

movies['tags'] = movies['overview'] + " " + movies['genres_list'].apply(lambda x: " ".join(x))

# =========================
# LAZY LOAD MODEL (FAST)
# =========================
similarity = None

def load_model():
    global similarity
    if similarity is None:
        print("Loading model...")
        tfidf = TfidfVectorizer(stop_words='english', max_features=2000)
        tfidf_matrix = tfidf.fit_transform(movies['tags'])
        similarity = cosine_similarity(tfidf_matrix)

# =========================
# POSTER API
# =========================
OMDB_API_KEY = "f4cd20e4"

def get_poster(title):
    with cache_lock:
        if title in poster_cache:
            return poster_cache[title]

    try:
        url = f"https://www.omdbapi.com/?t={quote(title)}&apikey={OMDB_API_KEY}"
        data = requests.get(url, timeout=5).json()
        poster = data.get("Poster", "N/A")
        
        if poster == "N/A" or not poster:
            poster = "https://via.placeholder.com/300x450"
        
        if poster != "https://via.placeholder.com/300x450":
            with cache_lock:
                poster_cache[title] = poster
                save_poster_cache()
                
        return poster
    except Exception as e:
        print("OMDb API error for", title, ":", e)
        return "https://via.placeholder.com/300x450"

# =========================
# RECOMMEND FUNCTION (FIXED)
# =========================
def recommend(movie, n=10):
    load_model()

    movie = movie.lower().strip()

    matches = movies[movies['title'].str.lower().str.contains(movie)]

    if matches.empty:
        return []

    idx = matches.index[0]

    scores = list(enumerate(similarity[idx]))
    scores = sorted(scores, key=lambda x: x[1], reverse=True)[1:n+1]

    # Fetch poster URLs in parallel to avoid sequential network requests bottleneck
    rows = [movies.iloc[i[0]] for i in scores]
    titles = [row['title'] for row in rows]
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        posters = list(executor.map(get_poster, titles))
        
    result = []
    for i, row in enumerate(rows):
        result.append({
            "title": row['title'],
            "poster": posters[i],
            "similarity": round(float(scores[i][1]) * 100, 1),
            "genres": row['genres_list'][:3],
            "overview": row['overview'] if pd.notna(row['overview']) else "",
            "vote_average": float(row['vote_average']) if pd.notna(row['vote_average']) else 0.0,
            "release_date": row['release_date'] if pd.notna(row['release_date']) else ""
        })

    return result

# =========================
# ROUTES
# =========================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/recommend")
def recommend_api():
    movie = request.args.get("movie", "")

    try:
        if movie:
            res = supabase.table("search_history").insert({
                "movie": movie
            }).execute()
            print("INSERT RESPONSE:", res)
    except Exception as e:
        print("DB ERROR:", e)

    return jsonify(recommend(movie))
    
@app.route("/history")
def history():
    response = supabase.table("search_history").select("*").order("created_at", desc=True).limit(10).execute()
    return jsonify(response.data)

@app.route("/trending")
def trending():
    top = movies.sort_values(by="popularity", ascending=False).head(20)
    
    rows = [row for _, row in top.iterrows()]
    titles = [row['title'] for row in rows]
    
    # Fetch trending posters in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        posters = list(executor.map(get_poster, titles))
        
    return jsonify([
        {
            "title": row['title'],
            "poster": posters[i],
            "genres": row['genres_list'][:3],
            "tagline": row['tagline'] if pd.notna(row['tagline']) else "",
            "overview": row['overview'] if pd.notna(row['overview']) else "",
            "vote_average": float(row['vote_average']) if pd.notna(row['vote_average']) else 0.0,
            "release_date": row['release_date'] if pd.notna(row['release_date']) else ""
        }
        for i, row in enumerate(rows)
    ])

# =========================
# RUN
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)