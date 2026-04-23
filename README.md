# 🎬 StreamFlix: Movie Recommendation System

A web-based movie recommendation system that suggests similar movies based on user input using content-based filtering. It analyzes movie descriptions and genres to generate relevant recommendations.

---

## 🚀 Features

- 🎯 Content-based movie recommendations  
- 🎬 Real-time poster fetching using OMDB API  
- ⚡ Fast and optimized backend (lazy loading)  
- 💻 Interactive and responsive UI  
- ☁️ Deployed on Render  

---

## 🧠 How It Works

- Movie data is loaded from TMDB dataset  
- Text features (overview + genres) are processed  
- TF-IDF vectorization is applied  
- Cosine similarity is used to find similar movies  
- Recommendations are returned based on similarity score  

---

## 🛠️ Tech Stack

- Backend: Python, Flask  
- Frontend: HTML, CSS, JavaScript  
- Machine Learning: Scikit-learn (TF-IDF, Cosine Similarity)  
- API: OMDB API (for movie posters)  

---

## 📂 Project Structure

MovieRecommendation/
│
├── app.py
├── templates/
│   └── index.html
├── tmdb_5000_movies.csv
├── tmdb_5000_credits.csv
├── requirements.txt
└── .gitignore

---

## ⚙️ Installation & Setup

# Clone repository
git clone https://github.com/your-username/movie-recommender.git

# Go to project folder
cd movie-recommender

# Install dependencies
pip install -r requirements.txt

# Run app
python app.py

---

## 🌐 Usage

1. Enter a movie name  
2. Click "Recommend"  
3. Get similar movies with posters  

---

## ☁️ Deployment (Render)

Start command:
gunicorn app:app

---

## 📌 Future Improvements

- Better recommendation accuracy  
- Bollywood + Hollywood support  
- User-based personalization  
- Netflix-style UI  

---

## 👩‍💻 Author

Sanvi Nahar
