import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import ast
import re

print("Loading data...")
movies = pd.read_csv('tmdb_5000_movies.csv')
credits = pd.read_csv('tmdb_5000_credits.csv')

movies = movies.merge(credits, on='title')

print("Processing features...")

# Extract genres
def get_genres(text):
    L = []
    for i in ast.literal_eval(str(text)):
        L.append(i['name'])
    return L

# Extract keywords
def get_keywords(text):
    L = []
    for i in ast.literal_eval(str(text)):
        L.append(i['name'])
    return L[:10]

# Extract top 3 cast
def get_cast(text):
    L = []
    for i in ast.literal_eval(str(text)):
        if L == 3:
            break
        L.append(i['name'])
    return L

# Extract director
def get_director(text):
    for i in ast.literal_eval(str(text)):
        if i.get('job') == 'Director':
            return [i['name']]
    return []

# Process columns
movies['genres_list'] = movies['genres'].apply(get_genres)
movies['keywords_list'] = movies['keywords'].apply(get_keywords)
movies['cast_list'] = movies['cast'].apply(get_cast)
movies['crew_list'] = movies['crew'].apply(get_director)

# Extract year from release_date
def get_year(row):
    try:
        if pd.notna(row):
            return str(row)[:4]
        return '2000'
    except:
        return '2000'

movies['year'] = movies['release_date'].apply(get_year)

# Get popularity score
def get_popularity_score(row):
    try:
        return float(row)
    except:
        return 0.0

movies['popularity_score'] = movies['popularity'].apply(get_popularity_score)

# Clean text function
def clean_text(text):
    if isinstance(text, list):
        text = ' '.join(text)
    text = re.sub(r'[^a-zA-Z]', ' ', str(text).lower())
    text = ' '.join(text.split())
    return text

# Create weighted tags
def create_weighted_tags(row):
    genres = ' '.join(row['genres_list']) * 3
    keywords = ' '.join(row['keywords_list']) * 2
    cast = ' '.join(row['cast_list']) * 3
    crew = ' '.join(row['crew_list']) * 2
    overview = clean_text(str(row['overview']))[:200]
    return f"{genres} {keywords} {cast} {crew} {overview}"

print("Creating feature vectors...")
movies['weighted_tags'] = movies.apply(create_weighted_tags, axis=1)

# Create final dataframe
new_df = movies[['movie_id', 'title', 'weighted_tags', 'genres_list', 'year', 'popularity_score']].copy()
new_df.dropna(subset=['title', 'weighted_tags'], inplace=True)
new_df.reset_index(drop=True, inplace=True)

print(f"Total movies: {len(new_df)}")

# TF-IDF Vectorization
print("Building TF-IDF vectors...")
tfidf = TfidfVectorizer(max_features=8000, stop_words='english', ngram_range=(1, 2))
tfidf_matrix = tfidf.fit_transform(new_df['weighted_tags'])

print(f"TF-IDF matrix shape: {tfidf_matrix.shape}")

# Calculate cosine similarity
print("Computing similarity matrix...")
similarity = cosine_similarity(tfidf_matrix, tfidf_matrix)

print("Model training complete!")

# Test recommendations
def recommend(movie, n=10):
    try:
        movie_index = new_df[new_df['title'] == movie].index[0]
    except:
        print(f"Movie '{movie}' not found")
        return
    
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:n+1]
    
    return movies_list
    
    print(f"\n=== Recommendations for '{movie}' ===")
    for idx, (i, score) in enumerate(movies_list, 1):
        title = new_df.iloc[i]['title']
        genres = ', '.join(new_df.iloc[i]['genres_list'][:3])
        print(f"{idx}. {title} ({score*100:.1f}% match) - [{genres}]")

# Test with different movies
recommend("Avatar", 10)
recommend("The Dark Knight", 10)
recommend("Iron Man", 10)

# Save model
import pickle
pickle.dump(new_df, open('movies.pkl', 'wb'))
pickle.dump(similarity, open('similarity.pkl', 'wb'))
pickle.dump(tfidf, open('tfidf.pkl', 'wb'))

print("\nModel saved!")