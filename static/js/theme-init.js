document.addEventListener('DOMContentLoaded', function () {
    let theme = localStorage.getItem('theme') || 'system';

    function applyTheme(theme) {
        document.body.classList.remove('dark-theme');

        if (theme === 'dark') {
            document.body.classList.add('dark-theme');
        } else if (theme === 'system') {
            if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
                document.body.classList.add('dark-theme');
            }
        }
    }

    applyTheme(theme);
});
