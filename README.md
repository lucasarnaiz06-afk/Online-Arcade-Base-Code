Online Arcade is a full-stack web platform that allows users to create accounts, connect with friends, and play a growing collection of interactive games including Plinko, Blackjack, Mines, and more. The platform integrates social networking features with a virtual coin economy and leaderboard system to recreate the fun and competition of an arcade environment directly in the browser.

As of October 28, 2025, the core site is fully functional. Users can register, log in, manage profiles, add friends, earn and spend coins, and view global and friend-based leaderboards. Most key features are stable, though new games, UI improvements, and social enhancements are actively in development.

The project is built with a Python Flask backend and a frontend based on HTML, CSS, and JavaScript. It uses Jinja2 templates for rendering and supports either SQLite or PostgreSQL for data management. The design emphasizes modularity, making it easy to add new games or expand existing features without restructuring the application.

To run the project locally, clone the repository from GitHub, install the required dependencies, and run the app.py file. You will also need a .env file containing a secret key, SQL database URI, and the username and password for an email address that will be used to send necessary emails to users. Once running, the site can be accessed through a local web browser that should be returned after you run app.py properly. 
.

Online Arcade was created and is maintained by Lucas Arnaiz, Roland Sui, and Julian Overton. The project is open for educational and non-commercial use, and contributions or feedback are welcome as development continues to evolve the platform into a complete online gaming and social experience.
