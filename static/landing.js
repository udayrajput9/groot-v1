// Generate random stars
function generateStars() {
    const starsContainer = document.getElementById('stars');
    for (let i = 0; i < 100; i++) {
        const star = document.createElement('div');
        star.className = 'star';
        star.style.left = Math.random() * 100 + '%';
        star.style.top = Math.random() * 100 + '%';
        star.style.animationDelay = Math.random() * 3 + 's';
        starsContainer.appendChild(star);
    }
}
generateStars();

function openCenterSearch() {
    document.getElementById('centerSearchModal').classList.add('active');
    document.getElementById('centerSearchInput').focus();
}

function closeCenterSearch() {
    document.getElementById('centerSearchModal').classList.remove('active');
}

function centerQuickSearch() {
    const searchTerm = document.getElementById('centerSearchInput').value.trim();
    if (!searchTerm) {
        alert('Please enter an asteroid name!');
        return;
    }
    // Redirect to search page with query
    window.location.href = `/search?query=${encodeURIComponent(searchTerm)}`;
}

// Close modal when clicking outside
    document.addEventListener('click', function(e) {
    const modal = document.getElementById('centerSearchModal');
    if (e.target === modal) {
        closeCenterSearch();
    }
});

// Allow Escape key to close modal
    document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeCenterSearch();
    }
});

function quickSearch() {
    const searchTerm = document.getElementById('quickSearchInput').value.trim();
    if (!searchTerm) {
        alert('Please enter an asteroid name!');
        return;
    }
    window.location.href = `/search?query=${encodeURIComponent(searchTerm)}`;
}
