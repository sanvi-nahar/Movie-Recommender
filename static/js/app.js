const API = window.location.origin;
let currentRecommendations = [];
let isSearching = false;

// Close details modal
function closeModal() {
  const modal = document.getElementById("details-modal");
  modal.classList.remove("active");
  document.body.style.overflow = "";
  modal.setAttribute("aria-hidden", "true");
  setTimeout(() => {
    if (!modal.classList.contains("active")) {
      modal.style.display = "none";
    }
  }, 220);
}

// Open details modal with recommendation properties
function openRecommendationDetails(index) {
  const movie = currentRecommendations[index];
  if (!movie) return;

  const poster = movie.poster && movie.poster !== "https://via.placeholder.com/300x450" 
    ? movie.poster 
    : "https://via.placeholder.com/300x450";
  const genres = (movie.genres || []).slice(0, 3).map(g => `<span class="badge">${g}</span>`).join("");
  const year = movie.release_date ? movie.release_date.substring(0, 4) : "N/A";
  const rating = movie.vote_average ? `${movie.vote_average.toFixed(1)}/10` : "N/A";

  document.getElementById("modal-poster").src = poster;
  document.getElementById("modal-poster").alt = movie.title + " Poster";
  document.getElementById("modal-title").innerText = movie.title;
  document.getElementById("modal-year").innerText = year;
  document.getElementById("modal-rating").innerHTML = `
    <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor" stroke="none" style="margin-right:2px; vertical-align:middle; display:inline-block; margin-top:-3px; fill:var(--accent);">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
    </svg>
    ${rating}
  `;
  document.getElementById("modal-genres").innerHTML = genres;
  document.getElementById("modal-overview").innerText = movie.overview || "No description available.";
  
  // Set up CTA button click in modal
  const ctaBtn = document.getElementById("modal-cta-btn");
  ctaBtn.onclick = function() {
    closeModal();
    reseed(movie.title);
  };

  const modal = document.getElementById("details-modal");
  modal.style.display = "flex";
  modal.setAttribute("aria-hidden", "false");
  // Trigger transition reflow
  setTimeout(() => {
    modal.classList.add("active");
  }, 10);
  
  // Disable body scroll when modal is active
  document.body.style.overflow = "hidden";
}

// Render Spotlight (Featured Banner)
function renderSpotlight(movie) {
  const container = document.getElementById("spotlight-container");
  if (!movie) {
    container.style.display = "none";
    return;
  }

  const poster = movie.poster && movie.poster !== "https://via.placeholder.com/300x450" 
    ? movie.poster 
    : "https://via.placeholder.com/300x450";
  const year = movie.release_date ? movie.release_date.substring(0, 4) : "";
  const rating = movie.vote_average ? `${movie.vote_average.toFixed(1)}` : "";
  const genresList = (movie.genres || []).slice(0, 3).join(", ");

  const metaParts = [];
  if (year) metaParts.push(`<span class="spotlight-year">${year}</span>`);
  if (rating) {
    metaParts.push(`
      <span class="spotlight-rating">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor" stroke="none" style="margin-right:2px; vertical-align:middle; display:inline-block; margin-top:-3px; fill:var(--accent);">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
        </svg>
        ${rating}/10
      </span>
    `);
  }
  if (genresList) metaParts.push(`<span class="spotlight-genres-text">${genresList}</span>`);
  const metadataLine = metaParts.join(" &bull; ");

  container.innerHTML = `
    <div class="spotlight-content">
      <div class="spotlight-info">
        <div class="spotlight-badge">EDITOR'S PICK</div>
        <h2 class="spotlight-title">${movie.title}</h2>
        <div class="spotlight-meta">
          ${metadataLine}
        </div>
        ${movie.tagline ? `<p class="spotlight-tagline">“${movie.tagline}”</p>` : ""}
        ${movie.overview ? `<p class="spotlight-overview">${movie.overview}</p>` : ""}
        <button class="btn-primary spotlight-btn" onclick="reseed('${movie.title.replace(/'/g, "\\'")}')">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right:4px;">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          Get Recommendations
        </button>
      </div>
      <div class="spotlight-poster-wrapper">
        <img class="spotlight-poster" src="${poster}" alt="${movie.title} Poster">
      </div>
    </div>
  `;
  container.style.display = "block";
}

// Show skeleton loaders in grid
function showLoader() {
  const grid = document.getElementById("results");
  document.getElementById("status").innerHTML = "";
  
  let html = "";
  for (let i = 0; i < 8; i++) {
    html += `
      <div class="skeleton-card">
        <div class="skeleton-poster"></div>
        <div class="skeleton-meta">
          <div class="skeleton-title"></div>
          <div class="skeleton-genre"></div>
        </div>
      </div>
    `;
  }
  grid.innerHTML = html;
}

// Render cards
function renderCards(list, titleText, helperText = "", isTrending = false) {
  const grid = document.getElementById("results");
  const title = document.getElementById("section-title");
  const helper = document.getElementById("helper");
  const spotlightContainer = document.getElementById("spotlight-container");

  title.innerText = titleText;
  helper.innerText = helperText;

  // Add fade-in animation on container
  grid.classList.remove("fade-in");
  void grid.offsetWidth; // Trigger layout reflow to restart animation
  grid.classList.add("fade-in");

  if (!list || list.length === 0) {
    grid.innerHTML = "";
    spotlightContainer.style.display = "none";
    document.getElementById("status").innerHTML = `<div class="center">No results found. Try another search term.</div>`;
    return;
  }

  document.getElementById("status").innerHTML = "";

  let displayList = list;

  // Render the spotlight block only for trending list
  if (isTrending && list.length > 0) {
    const featured = list[0];
    renderSpotlight(featured);
    displayList = list.slice(1);
  } else {
    spotlightContainer.style.display = "none";
    // Store in global variable for modal lookup
    currentRecommendations = list;
  }

  let html = "";
  displayList.forEach((m, index) => {
    const poster = m.poster && m.poster !== "https://via.placeholder.com/300x450" 
      ? m.poster 
      : "https://via.placeholder.com/300x450";
    const genres = (m.genres || []).slice(0,3).map(g => `<span class="badge">${g}</span>`).join("");
    
    // Icon for similarity
    const sim = (m.similarity !== undefined) 
      ? `<div class="sim">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" style="margin-right:2px;">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
            <polyline points="17 6 23 6 23 12"></polyline>
          </svg>
          ${m.similarity}% Match
         </div>` 
      : "";

    // Separated click behavior
    const clickHandler = isTrending 
      ? `reseed('${m.title.replace(/'/g, "\\'")}')` 
      : `openRecommendationDetails(${index})`;

    html += `
      <div class="card" onclick="${clickHandler}" aria-label="${isTrending ? 'Get recommendations like ' : 'View details of '}${m.title}">
        <div class="card-poster-wrapper">
          <img class="card-poster" src="${poster}" alt="${m.title} Poster" loading="lazy">
        </div>
        <div class="card-meta">
          <h3 class="card-title">${m.title}</h3>
          <div class="card-genres">${genres}</div>
          ${sim}
        </div>
      </div>
    `;
  });

  grid.innerHTML = html;
}

// Recommend from input search
async function recommend() {
  if (isSearching) return;

  const movieInput = document.getElementById("movie");
  const movie = movieInput.value.trim();
  if (!movie) return;

  isSearching = true;

  // Update button UI state
  const searchBtn = document.getElementById("search-btn");
  const searchBtnText = document.getElementById("search-btn-text");
  const spinner = document.getElementById("spinner");

  searchBtn.disabled = true;
  spinner.style.display = "inline-block";
  searchBtnText.innerText = "Finding Recommendations...";

  // Show loaders and hide spotlight immediately
  showLoader();
  document.getElementById("spotlight-container").style.display = "none";

  try {
    const res = await fetch(`${API}/recommend?movie=${encodeURIComponent(movie)}&n=10`);
    const data = await res.json();

    renderCards(
      data,
      `Because You Liked "${movie}"`,
      `${data.length} recommendations found`,
      false
    );
    
    // Smooth scroll to results
    document.getElementById("section").scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch (e) {
    document.getElementById("status").innerHTML = `
      <div class="error-message">
        Server error. Failed to load recommendations. Please try again.
      </div>
    `;
    document.getElementById("results").innerHTML = "";
  } finally {
    isSearching = false;
    searchBtn.disabled = false;
    spinner.style.display = "none";
    searchBtnText.innerText = "Find Recommendations";
  }
}

// Click card to re-seed search (from trending and modal CTA)
function reseed(title) {
  document.getElementById("movie").value = title;
  recommend();
}

// Fetch and load trending movies on load
async function loadTrending() {
  if (isSearching) return;
  showLoader();
  try {
    const res = await fetch(`${API}/trending`);
    const data = await res.json();

    renderCards(
      data,
      "Trending discovery",
      "Select a movie to get personalized recommendations.",
      true
    );
  } catch (e) {
    document.getElementById("status").innerHTML = `
      <div class="error-message">
        Failed to load trending movies.
      </div>
    `;
    document.getElementById("results").innerHTML = "";
  }
}

// Setup Modal event handlers
document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("details-modal");
  const closeBtn = modal.querySelector(".modal-close");

  closeBtn.addEventListener("click", closeModal);

  // Click outside to close
  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      closeModal();
    }
  });

  // ESC key to close
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && modal.classList.contains("active")) {
      closeModal();
    }
  });
});

// Support hitting enter in search field
document.getElementById("movie").addEventListener("keypress", (e) => {
  if (e.key === "Enter" && !isSearching) recommend();
});

// Initialize trending on page load
window.onload = loadTrending;