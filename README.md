# CineMatch

A content-based movie recommendation platform with an editorial UI inspired by Letterboxd, A24, and the Criterion Collection.

Search for a film you love and discover a curated list of similar films — ranked by cosine similarity across TF-IDF feature vectors built from plot overviews and genre metadata.

## Demo

![CineMatch Demo](screenshots/demo.gif)

## Features

- **Content-based recommendations** — TF-IDF vectorization + cosine similarity on movie descriptions and genres
- **Featured film spotlight** — editorially presented trending movie with tagline, rating, and overview
- **Movie details modal** — click any recommendation to view full details and re-seed a new search
- **Parallel poster fetching** — concurrent OMDB API calls with persistent JSON cache
- **Loading skeletons** — smooth skeleton loaders during data fetching
- **Responsive layout** — editorial grid adapts from desktop to mobile
- **Search history tracking** — optional Supabase integration for logging searches

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Flask |
| Frontend | HTML, CSS, JavaScript |
| ML | Scikit-learn (TF-IDF, Cosine Similarity) |
| Data | TMDB 5000 Movies Dataset |
| Posters | OMDB API |
| Database | Supabase (optional) |
| Deployment | Render / Gunicorn |

## Project Structure

```
CineMatch/
├── app.py                  # Flask application (routes, recommendation engine)
├── requirements.txt        # Python dependencies
├── .gitignore
├── .env                    # API keys (not tracked)
│
├── data/
│   └── tmdb_5000_movies.csv    # TMDB dataset (4,803 movies)
│
├── templates/
│   └── index.html          # HTML structure
│
├── static/
│   ├── css/
│   │   └── style.css       # Editorial design system
│   └── js/
│       └── app.js          # Client-side application logic
│
└── screenshots/
    └── README.md           # Screenshot documentation
```

## Installation

```bash
# Clone the repository
git clone https://github.com/sanvi-nahar/Movie-Recommender.git
cd Movie-Recommender

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Add your SUPABASE_URL and SUPABASE_KEY (optional)

# Run the application
python app.py
```

The app will be available at `https://movie-recommender-eef4.onrender.com/`.

## How It Works

1. Movie data is loaded from the TMDB 5000 dataset
2. Text features (overview + genres) are combined into tags
3. TF-IDF vectorization converts tags into numerical feature vectors
4. Cosine similarity measures the angle between vectors to find similar movies
5. Results are ranked by similarity score and returned with posters

## Screenshots

| View | Description |
|------|-------------|
| Home | Trending grid with featured spotlight |
| Search Results | Recommendations ranked by similarity |
| Movie Modal | Detailed view with overview and genres |
| Mobile | Responsive editorial layout |


## Future Improvements

- User accounts and personalized watchlists
- Hybrid recommendation model (collaborative + content-based)
- Genre and year filtering
- Movie trailers integration
- Extended dataset with more recent films

## Author

**Sanvi Nahar** — [GitHub](https://github.com/sanvi-nahar)
