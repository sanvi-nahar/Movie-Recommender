import pickle
import pandas as pd
import json
import os
import requests
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from urllib.parse import quote

app = Flask(__name__)
CORS(app)

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

movies = pickle.load(open('movies.pkl', 'rb'))
similarity = pickle.load(open('similarity.pkl', 'rb'))

OMDB_API_KEY = "f4cd20e4"
try:
    poster_cache = json.load(open('poster_cache.json'))
except:
    poster_cache = {}

# User data storage (in production, use SQLite)
user_ratings = {}
user_likes = {}
user_history = {}

def load_user_data():
    global user_ratings, user_likes, user_history
    try:
        if os.path.exists('user_ratings.json'):
            user_ratings = json.load(open('user_ratings.json'))
        if os.path.exists('user_likes.json'):
            user_likes = json.load(open('user_likes.json'))
        if os.path.exists('user_history.json'):
            user_history = json.load(open('user_history.json'))
    except:
        pass

def save_user_data():
    try:
        json.dump(user_ratings, open('user_ratings.json', 'w'))
        json.dump(user_likes, open('user_likes.json', 'w'))
        json.dump(user_history, open('user_history.json', 'w'))
    except:
        pass

load_user_data()

def get_poster_url(title):
    if title in poster_cache:
        return poster_cache[title]
    
    try:
        url = f"https://www.omdbapi.com/?t={quote(title)}&apikey={OMDB_API_KEY}"
        response = requests.get(url, timeout=5, verify=False)
        data = response.json()
        if data.get('Poster') and data['Poster'] != 'N/A':
            poster_cache[title] = data['Poster']
            json.dump(poster_cache, open('poster_cache.json', 'w'))
            return data['Poster']
    except:
        pass
    return None

def recommend(movie, n=10):
    try:
        movie_index = movies[movies['title'] == movie].index[0]
    except:
        return []
    
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:n+1]

    result = []
    for i in movies_list:
        title = movies.iloc[i[0]]['title']
        genres = movies.iloc[i[0]].get('genres_list', [])
        result.append({
            'title': title,
            'poster': get_poster_url(title),
            'similarity': round(float(i[1]) * 100, 1),
            'genres': genres[:3] if isinstance(genres, list) else []
        })
    return result

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api')
def api():
    return jsonify({
        'name': 'StreamFlix API',
        'version': '3.0',
        'endpoints': ['/movies', '/all-movies', '/recommend', '/search', '/genres', '/movie-details', '/rate', '/like', '/for-you']
    })

@app.route('/movies')
def get_movies():
    limit = request.args.get('limit', 10, type=int)
    offset = request.args.get('offset', 0, type=int)
    genre = request.args.get('genre', '')
    year = request.args.get('year', '')
    
    filtered = movies.copy()
    
    if genre:
        filtered = filtered[filtered['genres_list'].apply(lambda x: genre.lower() in [g.lower() for g in x] if isinstance(x, list) else False)]
    
    if year:
        filtered = filtered[filtered['year'] == year]
    
    titles = filtered['title'].tolist()[offset:offset+limit]
    result = []
    for title in titles:
        row = movies[movies['title'] == title]
        if len(row) > 0:
            genres = row.iloc[0].get('genres_list', [])
            result.append({
                'title': title,
                'poster': get_poster_url(title),
                'genres': genres[:3] if isinstance(genres, list) else []
            })
    return jsonify(result)

@app.route('/all-movies')
def get_all_movies():
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    all_titles = movies['title'].tolist()[offset:offset+limit]
    result = []
    for title in all_titles:
        result.append({
            'title': title,
            'poster': get_poster_url(title)
        })
    return jsonify(result)

@app.route('/genres')
def get_genres():
    all_genres = set()
    for genres in movies['genres_list']:
        if isinstance(genres, list):
            all_genres.update(genres)
    
    return jsonify(sorted(list(all_genres)))

@app.route('/years')
def get_years():
    years = movies['year'].dropna().unique().tolist()
    years = [y for y in years if y]
    return jsonify(sorted(years, reverse=True))

@app.route('/search')
def search_movies():
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
    results = movies[movies['title'].str.contains(query, case=False, na=False)]
    result = []
    for _, row in results.head(15).iterrows():
        genres = row.get('genres_list', [])
        result.append({
            'title': row['title'],
            'poster': get_poster_url(row['title']),
            'genres': genres[:3] if isinstance(genres, list) else [],
            'year': row.get('year', '')
        })
    return jsonify(result)

@app.route('/recommend')
def recommend_api():
    movie = request.args.get('movie', '')
    n = request.args.get('n', 10, type=int)
    
    if not movie:
        return jsonify([])
    
    try:
        result = recommend(movie, n)
        return jsonify(result)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify([])

# ========== NEW: RATINGS ==========
@app.route('/rate', methods=['POST', 'GET'])
def rate_movie():
    if request.method == 'POST':
        data = request.json
        title = data.get('title', '')
        rating = data.get('rating', 0)
        
        if not title or rating < 1 or rating > 10:
            return jsonify({'error': 'Invalid data'}), 400
        
        if title not in user_ratings:
            user_ratings[title] = []
        user_ratings[title].append(rating)
        save_user_data()
        
        return jsonify({'success': True, 'title': title, 'rating': rating})
    
    # GET: return ratings for a movie
    title = request.args.get('title', '')
    if title in user_ratings:
        ratings = user_ratings[title]
        avg = sum(ratings) / len(ratings) if ratings else 0
        return jsonify({
            'ratings': ratings,
            'count': len(ratings),
            'average': round(avg, 1)
        })
    return jsonify({'ratings': [], 'count': 0, 'average': 0})

# ========== NEW: LIKES ==========
@app.route('/like', methods=['POST', 'GET', 'DELETE'])
def like_movie():
    if request.method == 'POST':
        data = request.json
        title = data.get('title', '')
        
        if not title:
            return jsonify({'error': 'Invalid data'}), 400
        
        if 'likes' not in user_likes:
            user_likes['likes'] = []
        if title not in user_likes['likes']:
            user_likes['likes'].append(title)
            save_user_data()
        
        return jsonify({'success': True, 'liked': True})
    
    if request.method == 'DELETE':
        data = request.json
        title = data.get('title', '')
        
        if 'likes' in user_likes and title in user_likes['likes']:
            user_likes['likes'].remove(title)
            save_user_data()
        
        return jsonify({'success': True, 'liked': False})
    
    # GET: return all liked movies
    likes = user_likes.get('likes', [])
    result = []
    for title in likes:
        result.append({
            'title': title,
            'poster': get_poster_url(title)
        })
    return jsonify(result)

@app.route('/liked')
def get_liked():
    return like_movie()

# ========== NEW: WATCH HISTORY ==========
@app.route('/history', methods=['POST', 'GET'])
def watch_history():
    if request.method == 'POST':
        data = request.json
        title = data.get('title', '')
        
        if not title:
            return jsonify({'error': 'Invalid data'}), 400
        
        if 'history' not in user_history:
            user_history['history'] = []
        
        # Remove if already exists (to move to front)
        if title in user_history['history']:
            user_history['history'].remove(title)
        
        user_history['history'].append(title)
        
        # Keep last 20
        user_history['history'] = user_history['history'][-20:]
        save_user_data()
        
        return jsonify({'success': True})
    
    # GET: return watch history
    history = user_history.get('history', [])
    result = []
    for title in reversed(history):
        result.append({
            'title': title,
            'poster': get_poster_url(title)
        })
    return jsonify(result)

# ========== NEW: PERSONALIZED RECOMMENDATIONS ==========
@app.route('/for-you')
def for_you():
    """Generate personalized recommendations based on user history and likes"""
    watched = user_history.get('history', [])
    liked = user_likes.get('likes', [])
    
    if not watched and not liked:
        # Fallback to trending if no history
        return trending()
    
    # Get movies user has watched/liked
    watched_movies = set(watched + liked)
    
    # Get recommendations for each watched movie
    all_recommendations = []
    for movie in list(watched_movies)[:5]:
        recs = recommend(movie, 5)
        all_recommendations.extend(recs)
    
    # Remove duplicates and watched movies
    seen = set(watched_movies)
    unique_recs = []
    for m in all_recommendations:
        if m['title'] not in seen:
            unique_recs.append(m)
            seen.add(m['title'])
    
    # Sort by similarity and return top 10
    unique_recs.sort(key=lambda x: x['similarity'], reverse=True)
    return jsonify(unique_recs[:10])

@app.route('/movie-details')
def movie_details():
    title = request.args.get('title', '')
    if not title:
        return jsonify({})
    
    try:
        url = f"https://www.omdbapi.com/?t={quote(title)}&apikey={OMDB_API_KEY}&plot=full"
        response = requests.get(url, timeout=5, verify=False)
        data = response.json()
        
        if data.get('Response') == 'True':
            row = movies[movies['title'] == title]
            if len(row) > 0:
                data['genres'] = row.iloc[0].get('genres_list', [])[:3]
                data['year'] = row.iloc[0].get('year', '')
            
            data['similar'] = recommend(title, 6)
            
            # Add user-specific data
            data['user_data'] = {
                'liked': title in user_likes.get('likes', []),
                'user_rating': user_ratings.get(title, [None])[-1] if user_ratings.get(title) else None,
                'community_rating': sum(user_ratings.get(title, [])) / len(user_ratings.get(title, [1])) if user_ratings.get(title) else None
            }
            
            return jsonify(data)
        return jsonify({})
    except:
        return jsonify({})

@app.route('/trending')
def trending():
    popular = movies.nlargest(20, 'popularity_score')[['title', 'genres_list', 'popularity_score']]
    result = []
    for _, row in popular.iterrows():
        result.append({
            'title': row['title'],
            'poster': get_poster_url(row['title']),
            'genres': row['genres_list'][:3] if isinstance(row['genres_list'], list) else []
        })
    return jsonify(result)

if __name__ == '__main__':
    print(f"Loaded {len(movies)} movies")
    print(f"User ratings: {sum(len(v) for v in user_ratings.values())}")
    print(f"User likes: {len(user_likes.get('likes', []))}")
    app.run(debug=True, port=5000)