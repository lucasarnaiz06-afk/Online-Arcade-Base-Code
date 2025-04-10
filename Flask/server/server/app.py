from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer as Serializer
import os, datetime

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
csrf = CSRFProtect(app)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
mail = Mail(app)

# Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=datetime.datetime.now)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False)
    coins = db.Column(db.Integer, default=100)
    games = db.relationship('UserGame', backref='user', lazy=True)
    scores = db.relationship('Score', backref='user', lazy=True)

    def get_reset_token(self):
        s = Serializer(app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})
    
    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=1800)['user_id']
        except:
            return None
        return User.query.filter_by(id=user_id).first()

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, default=0)
    users = db.relationship('UserGame', backref='game', lazy=True)
    scores = db.relationship('Score', backref='game', lazy=True)

class UserGame(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    purchase_date = db.Column(db.DateTime, default=datetime.datetime.now)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=datetime.datetime.now)

class FriendRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, declined
    created = db.Column(db.DateTime, default=datetime.datetime.now)

# Helper functions
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def send_email(subject, recipients, text_body, html_body):
    msg = Message(subject, sender=os.getenv('MAIL_USERNAME'), recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)

# Routes
@app.route('/')
def home():
    games = Game.query.limit(4).all()  # Featured games
    return render_template('home.html', games=games)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password, password):
            flash('Please check your login details and try again.', 'danger')
            return redirect(url_for('login'))
            
        login_user(user, remember=remember)
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('profile'))
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        user_check = User.query.filter_by(username=username).first()
        if user_check:
            flash('Username already exists.', 'danger')
            return redirect(url_for('register'))
            
        email_check = User.query.filter_by(email=email).first()
        if email_check:
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))
            
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))
            
        # Create new user
        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password, method='pbkdf2:sha256')
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/profile')
@login_required
def profile():
    user_games = UserGame.query.filter_by(user_id=current_user.id).all()
    games = [game.game for game in user_games]
    
    top_scores = Score.query.filter_by(user_id=current_user.id) \
                           .order_by(Score.score.desc()) \
                           .limit(5) \
                           .all()
    
    return render_template('profile.html', games=games, top_scores=top_scores)

@app.route('/store')
@login_required
def store():
    all_games = Game.query.all()
    user_games = [game.game_id for game in UserGame.query.filter_by(user_id=current_user.id).all()]
    
    return render_template('store.html', games=all_games, user_games=user_games)

@app.route('/buy_game/<int:game_id>', methods=['POST'])
@login_required
def buy_game(game_id):
    game = Game.query.get_or_404(game_id)
    
    # Check if user already owns the game
    if UserGame.query.filter_by(user_id=current_user.id, game_id=game_id).first():
        flash('You already own this game!', 'warning')
        return redirect(url_for('store'))
    
    # Check if user has enough coins
    if current_user.coins < game.price:
        flash('Not enough coins to purchase this game!', 'danger')
        return redirect(url_for('store'))
    
    # Process purchase
    current_user.coins -= game.price
    user_game = UserGame(user_id=current_user.id, game_id=game_id)
    
    db.session.add(user_game)
    db.session.commit()
    
    flash(f'You have successfully purchased {game.name}!', 'success')
    return redirect(url_for('profile'))

@app.route('/play_game/<int:game_id>')
@login_required
def play_game(game_id):
    game = Game.query.get_or_404(game_id)
    
    # Check if user owns the game
    user_game = UserGame.query.filter_by(user_id=current_user.id, game_id=game_id).first()
    if not user_game and game.price > 0:
        flash('You need to purchase this game before playing!', 'warning')
        return redirect(url_for('store'))
    
    return render_template(f'games/{game.name.lower().replace(" ", "_")}.html', game=game)

@app.route('/submit_score/<int:game_id>', methods=['POST'])
@login_required
def submit_score(game_id):
    score_value = request.form.get('score', type=int)
    
    if not score_value:
        flash('Invalid score submission.', 'danger')
        return redirect(url_for('play_game', game_id=game_id))
    
    new_score = Score(user_id=current_user.id, game_id=game_id, score=score_value)
    db.session.add(new_score)
    db.session.commit()
    
    flash('Score submitted successfully!', 'success')
    return redirect(url_for('leaderboard', game_id=game_id))

@app.route('/leaderboard/<int:game_id>')
def leaderboard(game_id):
    game = Game.query.get_or_404(game_id)
    
    scores = db.session.query(Score, User) \
                      .join(User) \
                      .filter(Score.game_id == game_id) \
                      .order_by(Score.score.desc()) \
                      .limit(20) \
                      .all()
    
    return render_template('leaderboard.html', game=game, scores=scores)

@app.route('/friends')
@login_required
def friends():
    # Get accepted friend requests where current user is either the requester or the receiver
    friend_requests = FriendRequest.query.filter(
        ((FriendRequest.user_id == current_user.id) | 
         (FriendRequest.friend_id == current_user.id)) &
        (FriendRequest.status == 'accepted')
    ).all()
    
    friends = []
    for fr in friend_requests:
        if fr.user_id == current_user.id:
            friends.append(User.query.get(fr.friend_id))
        else:
            friends.append(User.query.get(fr.user_id))
    
    # Get pending friend requests where current user is the receiver
    pending_requests = FriendRequest.query.filter_by(
        friend_id=current_user.id,
        status='pending'
    ).all()
    
    return render_template('friends.html', friends=friends, pending_requests=pending_requests)

@app.route('/add_friend', methods=['POST'])
@login_required
def add_friend():
    username = request.form.get('username')
    
    if not username:
        flash('Please enter a username.', 'danger')
        return redirect(url_for('friends'))
    
    friend = User.query.filter_by(username=username).first()
    
    if not friend:
        flash('User not found.', 'danger')
        return redirect(url_for('friends'))
    
    if friend.id == current_user.id:
        flash('You cannot add yourself as a friend.', 'danger')
        return redirect(url_for('friends'))
    
    # Check if friend request already exists
    existing_request = FriendRequest.query.filter(
        ((FriendRequest.user_id == current_user.id) & (FriendRequest.friend_id == friend.id)) |
        ((FriendRequest.user_id == friend.id) & (FriendRequest.friend_id == current_user.id))
    ).first()
    
    if existing_request:
        flash('Friend request already exists or you are already friends.', 'warning')
        return redirect(url_for('friends'))
    
    # Create friend request
    friend_request = FriendRequest(user_id=current_user.id, friend_id=friend.id)
    db.session.add(friend_request)
    db.session.commit()
    
    flash(f'Friend request sent to {friend.username}!', 'success')
    return redirect(url_for('friends'))

@app.route('/accept_friend/<int:request_id>')
@login_required
def accept_friend(request_id):
    friend_request = FriendRequest.query.get_or_404(request_id)
    
    if friend_request.friend_id != current_user.id:
        flash('You are not authorized to accept this friend request.', 'danger')
        return redirect(url_for('friends'))
    
    friend_request.status = 'accepted'
    db.session.commit()
    
    friend = User.query.get(friend_request.user_id)
    flash(f'You are now friends with {friend.username}!', 'success')
    return redirect(url_for('friends'))

@app.route('/reset_request', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = user.get_reset_token()
            reset_url = url_for('reset_token', token=token, _external=True)
            
            html_body = f'''
            <p>To reset your password, please visit the following link:</p>
            <p><a href="{reset_url}">Reset Password</a></p>
            <p>If you did not make this request, please ignore this email.</p>
            '''
            
            text_body = f'''
            To reset your password, please visit the following link:
            {reset_url}
            If you did not make this request, please ignore this email.
            '''
            
            send_email('Password Reset Request', [email], text_body, html_body)
        
        flash('If an account with that email exists, we\'ve sent instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    
    return render_template('reset_request.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    user = User.verify_reset_token(token)
    if not user:
        flash('Invalid or expired token.', 'warning')
        return redirect(url_for('reset_request'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('reset_token', token=token))
        
        user.password = generate_password_hash(password, method='pbkdf2:sha256')
        db.session.commit()
        
        flash('Your password has been updated! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_token.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create sample games if none exist
        if not Game.query.first():
            games = [
                Game(name='Snake', description='Classic snake game. Eat food and grow longer without hitting walls or yourself!', 
                     icon='snake.png', price=0),
                Game(name='Tetris', description='Arrange falling blocks to create complete lines and score points.', 
                     icon='tetris.png', price=50),
                Game(name='Pacman', description='Navigate through a maze while collecting dots and avoiding ghosts.', 
                     icon='pacman.png', price=75),
                Game(name='Space Invaders', description='Defend Earth from alien invaders in this classic arcade shooter.', 
                     icon='space_invaders.png', price=100)
            ]
            db.session.add_all(games)
            db.session.commit()
    
    app.run(debug=True, port=5000, host='0.0.0.0')