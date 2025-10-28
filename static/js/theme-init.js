document.addEventListener('DOMContentLoaded', function () {
    initializeTheme();
    
    // Listen for theme changes in localStorage (cross-tab)
    window.addEventListener('storage', function(e) {
        if (e.key === 'theme') {
            applyTheme(e.newValue);
        }
    });
    
    // Check for theme changes periodically (for server-side updates)
    setInterval(checkThemeUpdate, 500);
});

let lastKnownTheme = null;

function initializeTheme() {
    let theme = localStorage.getItem('theme');
    
    // If no theme is stored (first visit or logged out user), default to dark
    if (!theme) {
        theme = 'dark';
        localStorage.setItem('theme', theme);
    }

    if (theme === 'system') {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        theme = prefersDark ? 'dark' : 'light';
        localStorage.setItem('theme', theme);
    }

    lastKnownTheme = theme;
    applyTheme(theme);
}

function checkThemeUpdate() {
    const currentTheme = localStorage.getItem('theme');
    if (currentTheme && currentTheme !== lastKnownTheme) {
        lastKnownTheme = currentTheme;
        applyTheme(currentTheme);
    }
}

function applyTheme(theme) {
    if (!theme) return;
    
    document.body.classList.remove('dark-theme');
    document.querySelectorAll('.card, .list-group-item').forEach(item =>
        item.classList.remove('dark-mode')
    );

    if (theme === 'dark') {
        document.body.classList.add('dark-theme');
        document.querySelectorAll('.card, .list-group-item').forEach(item =>
            item.classList.add('dark-mode')
        );
    }
}