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

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
CORS(app)

# =========================
# LOAD DATA
# =========================
movies = pd.read_csv("tmdb_5000_movies.csv")

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
        print("⚡ Loading model...")
        tfidf = TfidfVectorizer(stop_words='english', max_features=2000)
        tfidf_matrix = tfidf.fit_transform(movies['tags'])
        similarity = cosine_similarity(tfidf_matrix)

# =========================
# POSTER API
# =========================
OMDB_API_KEY = "f4cd20e4"

def get_poster(title):
    try:
        url = f"https://www.omdbapi.com/?t={quote(title)}&apikey={OMDB_API_KEY}"
        data = requests.get(url, timeout=5).json()
        return data.get("Poster", "https://via.placeholder.com/300x450")
    except:
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

    result = []

    for i in scores:
        title = movies.iloc[i[0]]['title']
        genres = movies.iloc[i[0]]['genres_list']

        result.append({
            "title": title,
            "poster": get_poster(title),
            "similarity": round(float(i[1]) * 100, 1),
            "genres": genres[:3]
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
        print("❌ DB ERROR:", e)

    return jsonify(recommend(movie))
    
@app.route("/history")
def history():
    response = supabase.table("search_history").select("*").order("created_at", desc=True).limit(10).execute()
    return jsonify(response.data)

@app.route("/trending")
def trending():
    top = movies.sort_values(by="popularity", ascending=False).head(20)
    return jsonify([
        {
            "title": row['title'],
            "poster": get_poster(row['title']),
            "genres": row['genres_list'][:3]
        }
        for _, row in top.iterrows()
    ])

# =========================
# RUN
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)