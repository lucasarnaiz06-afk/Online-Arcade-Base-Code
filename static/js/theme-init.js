document.addEventListener('DOMContentLoaded', function () {
    // Get theme from localStorage or default to 'dark'
    let theme = localStorage.getItem('theme') || 'dark';

    // If user selected 'system', determine actual theme and store it
    if (theme === 'system') {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        theme = prefersDark ? 'dark' : 'light';
        localStorage.setItem('theme', theme);
    }

    // Apply the resolved theme
    applyTheme(theme);
});

// Reusable function to apply theme
function applyTheme(theme) {
    document.body.classList.remove('dark-theme');

    if (theme === 'dark') {
        document.body.classList.add('dark-theme');
    }
}
