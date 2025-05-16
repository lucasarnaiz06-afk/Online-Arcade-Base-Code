from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer as Serializer
import os, datetime
from werkzeug.utils import secure_filename
import random
import json
import os
import secrets
from PIL import Image
from functools import wraps
from plinko_routes import plinko_bp


load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/images/avatars')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max upload
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
csrf = CSRFProtect(app)


# Register blueprints
app.register_blueprint(plinko_bp)


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')
mail = Mail(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=datetime.datetime.now)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False)
    coins = db.Column(db.Integer, default=100)
    is_admin = db.Column(db.Boolean, default=False)
    avatar = db.Column(db.String(100), default='default_avatar.png')
    bio = db.Column(db.Text, nullable=True)
    theme = db.Column(db.String(20), default='light')
    accent_color = db.Column(db.String(20), default='blue')
    notification_settings = db.Column(db.Text, default='{"email": ["friend_requests", "game_invites", "new_games", "leaderboard_updates"], "push": ["all"]}')
    games = db.relationship('UserGame', backref='user', lazy=True)
    scores = db.relationship('Score', backref='user', lazy=True)
    email_confirmed = db.Column(db.Boolean, default=False)


    def get_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id}, salt='email-confirm')
    
    def get_reset_token(self):
        s = Serializer(app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id}, salt='password-reset')
    
    @staticmethod
    def verify_email_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, salt='email-confirm', max_age=86400)['user_id']  # 24 hours
        except:
            return None
        return User.query.get(user_id)

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, salt='password-reset', max_age=1800)['user_id']  # 30 minutes
        except:
            return None
        return User.query.get(user_id)

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
    try:
        msg = Message(subject, sender=app.config['MAIL_DEFAULT_SENDER'], recipients=recipients)
        msg.body = text_body
        msg.html = html_body
        mail.send(msg)
        return True
    except Exception as e:
        app.logger.error(f"Email sending failed: {e}")
        return False

@csrf.exempt
@app.route('/set_coins', methods=['GET', 'POST'])
@login_required
def set_coins():
    # if not current_user.is_admin:
    #     flash("Access denied. Admins only.", "danger")
    #     return redirect(url_for('home'))
    if request.method == 'POST':
        coin_id = request.form['user_id']
        coin_amount = request.form['new_amount']
        
        # Find the user
        user = User.query.get(coin_id)
        if user:
            user.coins = int(coin_amount)
            db.session.commit()
            flash(f"Updated {user.username}'s coins to {coin_amount}.", 'success')
        else:
            flash('User not found.', 'danger')
        
        return redirect(url_for('set_coins'))
        
    return render_template('set_coins.html')
 
# Routes
@app.route('/')
def home():
    print("home")
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
        
        if not user.email_confirmed:
            flash('Please verify your email before logging in. Check your inbox for the verification link.', 'warning')
            
            # Option to resend verification email
            resend_url = url_for('resend_confirmation')
            flash(f'If you did not receive the email, <a href="{resend_url}">click here to resend</a>.', 'info')
            return redirect(url_for('login'))
        
        login_user(user, remember=remember)
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('home'))
    
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
            password=generate_password_hash(password, method='pbkdf2:sha256'),
            email_confirmed=False
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Generate token and send verification email
        token = new_user.get_token()
        verify_url = url_for('confirm_email', token=token, _external=True)
        
        html_body = f'''
        <h2>Welcome to Online Arcade!</h2>
        <p>Thank you for registering. To complete your registration and verify your email address, please click the link below:</p>
        <p><a href="{verify_url}">Verify Email Address</a></p>
        <p>This link will expire in 24 hours.</p>
        <p>If you did not create an account, please ignore this email.</p>
        '''
        
        text_body = f'''
        Welcome to Online Arcade!
        
        Thank you for registering. To complete your registration and verify your email address, please click the link below:
        
        {verify_url}
        
        This link will expire in 24 hours.
        
        If you did not create an account, please ignore this email.
        '''
        
        email_sent = send_email('Verify Your Email Address', [email], text_body, html_body)
        
        if email_sent:
            flash('Your account has been created! Please check your email to verify your account.', 'success')
        else:
            flash('Your account has been created, but we could not send a verification email. Please contact support.', 'warning')
            
        return redirect(url_for('login'))
    
    return render_template('register.html')


# New route for email confirmation
@app.route('/confirm_email/<token>')
def confirm_email(token):
    user = User.verify_email_token(token)
    
    if not user:
        flash('The confirmation link is invalid or has expired.', 'danger')
        return redirect(url_for('login'))
        
    if user.email_confirmed:
        flash('Your email has already been verified. Please login.', 'info')
        return redirect(url_for('login'))
        
    user.email_confirmed = True
    db.session.commit()
    
    flash('Your email has been verified! You can now log in.', 'success')
    return redirect(url_for('login'))

@app.route('/resend_confirmation', methods=['GET', 'POST'])
def resend_confirmation():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user and not user.email_confirmed:
            token = user.get_token()
            verify_url = url_for('confirm_email', token=token, _external=True)
            
            html_body = f'''
            <h2>Email Verification</h2>
            <p>To verify your email address, please click the link below:</p>
            <p><a href="{verify_url}">Verify Email Address</a></p>
            <p>This link will expire in 24 hours.</p>
            <p>If you did not create an account, please ignore this email.</p>
            '''
            
            text_body = f'''
            Email Verification
            
            To verify your email address, please click the link below:
            
            {verify_url}
            
            This link will expire in 24 hours.
            
            If you did not create an account, please ignore this email.
            '''
            
            email_sent = send_email('Verify Your Email Address', [email], text_body, html_body)
            
            if email_sent:
                flash('A new verification email has been sent. Please check your inbox.', 'success')
            else:
                flash('We could not send a verification email. Please try again later.', 'danger')
        else:
            # Don't reveal if email exists for security
            flash('If this email is registered and not verified, a new verification link has been sent.', 'info')
            
        return redirect(url_for('login'))
    
    return render_template('resend_confirmation.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/games')
@login_required
def games():
    all_games = Game.query.all()
    user_games = [game.game_id for game in UserGame.query.filter_by(user_id=current_user.id).all()]
    
    return render_template('games.html', games=all_games, user_games=user_games)

@app.route('/play_game/<int:game_id>')
@login_required
def play_game(game_id):
    game = Game.query.get_or_404(game_id)
    
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
    
    # Create a list of request senders
    request_senders = []
    for request in pending_requests:
        request_senders.append(User.query.get(request.user_id))
    
    return render_template('friends.html', friends=friends, pending_requests=pending_requests, 
                           request_senders=request_senders, User=User)


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
            <h2>Password Reset Request</h2>
            <p>To reset your password, please click the link below:</p>
            <p><a href="{reset_url}">Reset Password</a></p>
            <p>This link will expire in 30 minutes.</p>
            <p>If you did not make this request, please ignore this email and your password will remain unchanged.</p>
            '''
                
            text_body = f'''
            Password Reset Request
            
            To reset your password, please click the link below:
            
            {reset_url}
            
            This link will expire in 30 minutes.
            
            If you did not make this request, please ignore this email and your password will remain unchanged.
            '''
            
            email_sent = send_email('Password Reset Request', [email], text_body, html_body)
            
            if not email_sent:
                app.logger.error(f"Failed to send password reset email to {email}")
        
        # Don't reveal if email exists for security
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

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def save_picture(form_picture):
    # Generate a random filename to avoid collisions
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.config['UPLOAD_FOLDER'], picture_fn)
    
    # Resize image - optional, but helps save space and load time
    output_size = (150, 150)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    
    # Create directories if they don't exist
    os.makedirs(os.path.dirname(picture_path), exist_ok=True)
    
    # Save the picture
    i.save(picture_path)
    
    return picture_fn

@app.route('/settings')
@login_required
def settings():
    # Pass the current time for displaying session info
    current_time = datetime.datetime.now()
    
    # Load notification settings from JSON string to dict
    if current_user.notification_settings:
        try:
            notifications = json.loads(current_user.notification_settings)
        except:
            notifications = {"email": [], "push": []}
    else:
        notifications = {"email": [], "push": []}
    
    return render_template('settings.html', current_time=current_time, notifications=notifications)

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    if request.method == 'POST':
        # Validate username uniqueness if it's changed
        new_username = request.form.get('username')
        if new_username != current_user.username:
            user_check = User.query.filter_by(username=new_username).first()
            if user_check:
                flash('Username already exists.', 'danger')
                return redirect(url_for('settings'))
        
        # Validate email uniqueness if it's changed
        new_email = request.form.get('email')
        if new_email != current_user.email:
            email_check = User.query.filter_by(email=new_email).first()
            if email_check:
                flash('Email already registered.', 'danger')
                return redirect(url_for('settings'))
            
            # Email changed, need to verify again
            current_user.email_confirmed = False
            current_user.email = new_email
            
            # Send verification email
            token = current_user.get_token()
            verify_url = url_for('confirm_email', token=token, _external=True)
            
            html_body = f'''
            <h2>Email Verification</h2>
            <p>To verify your new email address, please click the link below:</p>
            <p><a href="{verify_url}">Verify Email Address</a></p>
            <p>This link will expire in 24 hours.</p>
            <p>If you did not make this change, please contact support immediately.</p>
            '''
            
            text_body = f'''
            Email Verification
            
            To verify your new email address, please click the link below:
            
            {verify_url}
            
            This link will expire in 24 hours.
            
            If you did not make this change, please contact support immediately.
            '''
            
            email_sent = send_email('Verify Your Email Address', [new_email], text_body, html_body)
            
            if email_sent:
                flash('Email updated! Please verify your new email address. Check your inbox.', 'warning')
            else:
                flash('Email updated but verification email could not be sent. Please contact support.', 'warning')
        
        # Update username
        current_user.username = new_username
        
        # Update bio
        current_user.bio = request.form.get('bio', '')
        
        # Handle profile picture upload
        if 'avatar' in request.files:
            avatar_file = request.files['avatar']
            if avatar_file and avatar_file.filename:
                if allowed_file(avatar_file.filename):
                    # If user already has a custom avatar, delete it (unless it's the default)
                    if current_user.avatar != 'default_avatar.png' and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], current_user.avatar)):
                        try:
                            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], current_user.avatar))
                        except:
                            pass  # We can continue even if deletion fails
                    
                    # Save the new picture
                    picture_file = save_picture(avatar_file)
                    current_user.avatar = picture_file
                else:
                    flash('Invalid file type. Please upload PNG, JPG, JPEG, or GIF files.', 'danger')
                    return redirect(url_for('settings'))
        
        # Save all changes
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('settings'))

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Verify current password
        if not check_password_hash(current_user.password, current_password):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('settings'))
        
        # Verify new passwords match
        if new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
            return redirect(url_for('settings'))
        
        current_user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
        db.session.commit()
        
        flash('Your password has been updated!', 'success')
        return redirect(url_for('settings'))

@app.route('/update_appearance', methods=['POST'])
@login_required
def update_appearance():
    if request.method == 'POST':
        theme = request.form.get('theme', 'light')
        accent_color = request.form.get('accent_color', 'blue')
        
        current_user.theme = theme
        current_user.accent_color = accent_color
        db.session.commit()
        
        flash('Appearance settings saved!', 'success')
        return redirect(url_for('settings'))

@app.route('/update_notifications', methods=['POST'])
@login_required
def update_notifications():
    if request.method == 'POST':
        email_notifications = request.form.getlist('notifications[]')
        push_notifications = request.form.getlist('push_notifications[]')
        
        notification_settings = {
            'email': email_notifications,
            'push': push_notifications
        }
        
        current_user.notification_settings = json.dumps(notification_settings)
        db.session.commit()
        
        flash('Notification settings updated!', 'success')
        return redirect(url_for('settings'))

@app.route('/logout_all', methods=['POST'])
@login_required
def logout_all():
    # In a real application, you'd invalidate all sessions here
    # For this example, we'll just log out the current user
    logout_user()
    flash('You have been logged out from all devices.', 'info')
    return redirect(url_for('login'))

@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    password = request.form.get('password')
    
    # Verify password
    if not check_password_hash(current_user.password, password):
        flash('Password is incorrect.', 'danger')
        return redirect(url_for('settings'))
    
    
    user_id = current_user.id
    
    logout_user()
    
    # Delete user's data 
    user = User.query.get(user_id)
    
    # Delete avatar if not default
    if user.avatar != 'default_avatar.png':
        avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], user.avatar)
        try:
            if os.path.exists(avatar_path):
                os.remove(avatar_path)
        except:
            pass  # Continue even if file deletion fails
    
    # Delete user from database
    db.session.delete(user)
    db.session.commit()
    
    flash('Your account has been permanently deleted.', 'info')
    return redirect(url_for('home'))

def ensure_avatar_directory_exists():
    avatar_dir = os.path.join(app.root_path, 'static/images/avatars')
    if not os.path.exists(avatar_dir):
        os.makedirs(avatar_dir)

def save_picture(form_picture):
    # Generate a random filename to avoid collisions
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.config['UPLOAD_FOLDER'], picture_fn)
    
    # Resize image - optional, but helps save space and load time
    output_size = (150, 150)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    
    # Create directories if they don't exist
    ensure_avatar_directory_exists()
    
    i.save(picture_path)
    
    return picture_fn

@app.route('/games/mines', methods=['GET', 'POST'])
@login_required
def mines():
    import random

    # Reset game session if user clicks "Play Again"
    if request.method == 'GET' and request.args.get('reset') == 'true':
        session.pop('mines_game', None)

    # Start a new game
    if request.method == 'POST':
        try:
            bet = int(request.form.get('bet', 0))
            mine_count = int(request.form.get('mines', 3))
        except ValueError:
            flash("Invalid input.", "danger")
            return redirect(url_for('mines'))

        # Validate inputs
        if bet <= 0 or bet > current_user.coins or not (1 <= mine_count <= 24):
            flash("Invalid bet or number of mines (1–24 allowed).", "danger")
            return redirect(url_for('mines'))

        # Deduct bet and initialize game board
        current_user.coins -= bet
        db.session.commit()

        grid_size = 25
        mine_positions = random.sample(range(grid_size), mine_count)

        session['mines_game'] = {
            'bet': bet,
            'mines': mine_count,
            'mine_positions': mine_positions,
            'safe_revealed': [],
            'grid_size': grid_size,
            'active': True
        }

        return redirect(url_for('mines'))

    # Load existing game
    game = session.get('mines_game')
    multiplier = None

    # Calculate multiplier if game is active
    if game and game['active']:
        revealed = len(game['safe_revealed'])
        t = game['grid_size']
        m = game['mines']
        s=t+m
        multiplier = 1.0
        for i in range(revealed):
            multiplier *= (s - i) / (t - i)

        # Ensure multiplier never drops below 1.0 if at least 1 safe tile was hit
        if revealed > 0 and multiplier < 1.0:
            multiplier = 1.0


    return render_template('games/mines.html', game=game, current_user=current_user, multiplier=multiplier)


@app.route('/games/mines/pick/<int:tile>')
@login_required
def mines_pick(tile):
    game = session.get('mines_game')
    if not game or not game['active']:
        return redirect(url_for('mines'))

    if tile in game['safe_revealed']:
        return redirect(url_for('mines'))

    if tile in game['mine_positions']:
        game['active'] = False
    else:
        game['safe_revealed'].append(tile)

    session['mines_game'] = game
    return redirect(url_for('mines'))

@app.route('/games/mines/cashout')
@login_required
def mines_cashout():
    game = session.get('mines_game')
    if not game or not game['active']:
        return redirect(url_for('mines'))

    # Extract game data
    revealed = len(game['safe_revealed'])
    t = game['grid_size']
    m = game['mines']
    bet = game['bet']
    s=t+m
    multiplier = 1.0
    for i in range(revealed):
        multiplier *= (s - i) / (t - i)

        # Ensure multiplier never drops below 1.0 if at least 1 safe tile was hit
    if revealed > 0 and multiplier < 1.0:
        multiplier = 1.0


    # Compute winnings and update user balance
    winnings = int(bet * multiplier)
    current_user.coins += winnings
    db.session.commit()

    # End game and clear session
    session.pop('mines_game', None)
    print(winnings)
    print(multiplier)
    print(bet)
    return redirect(url_for('mines'))


@app.route('/games/slots_animated')
@login_required
def slots_animated():
    return render_template('games/slots_animated.html')
@app.route('/games/slots/spin', methods=['POST'])
@login_required
@csrf.exempt
def slots_spin():
    import random
    data = request.get_json()
    bet = int(data.get('bet', 0))

    if bet <= 0 or bet > current_user.coins:
        return jsonify({'error': 'Invalid bet'}), 400

    current_user.coins -= bet

    symbols = ['🍒', '🍋', '💎', '🍉', '🍌']  # 🍌 = no payout
    weights = [0.30, 0.15, 0.05, 0.20, 0.30]

    spin = random.choices(symbols, weights, k=3)

    win = 0
    if spin == ['💎', '💎', '💎']:
        win = bet * 1000
    elif spin == ['🍒', '🍒', '🍒']:
        win = bet * 10
    elif spin == ['🍋', '🍋', '🍋']:
        win = bet * 20
    elif spin == ['🍉', '🍉', '🍉']:
        win = bet * 5
    elif spin.count('🍒') == 2:
        win = bet * 2

    current_user.coins += win
    db.session.commit()

    return jsonify({'symbols': spin, 'win': win, 'coins': current_user.coins})

@app.route('/games/blackjack', methods=['GET', 'POST'])
@login_required
def blackjack():
    import random
    if request.args.get('action') == 'new':
        session.pop('deck', None)
        session.pop('player_hands', None)
        session.pop('active_hand', None)
        session.pop('dealer', None)
        session.pop('bets', None)
        session.pop('game_over', None)
        session.pop('message', None)
        session.pop('can_split', None)
        session.pop('can_double', None)
        return redirect(url_for('blackjack'))

    def calculate_score(hand):
        score = sum(min(card, 10) for card in hand)
        aces = hand.count(1)
        while aces > 0 and score + 10 <= 21:
            score += 10
            aces -= 1
        return score

    if request.method == 'POST':
        bet = int(request.form.get('bet', 0))
        if bet <= 0 or bet > current_user.coins:
            flash("Invalid bet amount", "danger")
            return redirect(url_for('blackjack'))

        # Create and shuffle the deck
        deck = [1,2,3,4,5,6,7,8,9,10,10,10,10]*4
        random.shuffle(deck)

        # Initial deal
        player_hands = [[deck.pop(), deck.pop()]]
        dealer = [deck.pop(), deck.pop()]

        # Check if player can split initially
        can_split = min(player_hands[0][0], 10) == min(player_hands[0][1], 10) and current_user.coins >= bet * 2
        
        # Player can always double initially if they have enough coins
        can_double = current_user.coins >= bet * 2

        session['deck'] = deck
        session['player_hands'] = player_hands
        session['active_hand'] = 0
        session['dealer'] = dealer
        session['bets'] = [bet]  # List to store bet for each hand
        session['game_over'] = False
        session['message'] = ""
        session['can_split'] = can_split
        session['can_double'] = can_double
        def get_face_value(card):
            if card == 10:
                return random.choice(['10', 'J', 'Q', 'K'])
            elif card == 1:
                return 'A'
            else:
                return str(card)

        session['dealer_faces'] = [get_face_value(c) for c in dealer]

        return redirect(url_for('blackjack'))

    # Restore session state
    deck = session.get('deck', [])
    player_hands = session.get('player_hands', [[]])
    active_hand = session.get('active_hand', 0)
    dealer = session.get('dealer', [])
    bets = session.get('bets', [0])
    game_over = session.get('game_over', True)
    message = session.get('message', "")
    can_split = session.get('can_split', False)
    can_double = session.get('can_double', False)
 # Helper function for dealer's turn
    def dealer_turn():
        nonlocal dealer, deck
        
        # Dealer draws until reaching at least 17
        while calculate_score(dealer) < 17:
            dealer.append(deck.pop())
        session['dealer'] = dealer
        
        # Determine outcomes for all hands
        dealer_score = calculate_score(dealer)
        results = []
        total_win = 0
        
        for i, hand in enumerate(player_hands):
            player_score = calculate_score(hand)
            
            if player_score > 21:
                # Player busted
                result = "Busted"
                total_win -= bets[i]
            elif dealer_score > 21 or player_score > dealer_score:
                # Player wins
                result = "Win"
                total_win += bets[i]
            elif player_score < dealer_score:
                # Dealer wins
                result = "Loss"
                total_win -= bets[i]
            else:
                # Push (tie)
                result = "Push"
            
            results.append(result)
        
        # Update player's coins
        current_user.coins += total_win
        db.session.commit()
        
        # Prepare message with results
        if len(results) == 1:
            if results[0] == "Busted":
                session['message'] = "You busted! Dealer wins."
            elif results[0] == "Win":
                session['message'] = "You win!"
            elif results[0] == "Loss":
                session['message'] = "Dealer wins!"
            else:
                session['message'] = "It's a push!"
        else:
            # Multiple hands
            wins = results.count("Win")
            losses = results.count("Loss") + results.count("Busted")
            pushes = results.count("Push")
            
            message_parts = []
            if wins > 0:
                message_parts.append(f"{wins} win{'s' if wins > 1 else ''}")
            if losses > 0:
                message_parts.append(f"{losses} loss{'es' if losses > 1 else ''}")
            if pushes > 0:
                message_parts.append(f"{pushes} push{'es' if pushes > 1 else ''}")
            
            session['message'] = "Game over! Results: " + ", ".join(message_parts) + f". Net change: {total_win} coins."
        
        session['game_over'] = True
    
    
    # Process player actions
    if deck and not game_over:
        # HIT action
        if request.args.get('action') == 'hit':
            # Deal a card to the active hand
            player_hands[active_hand].append(deck.pop())
            session['player_hands'] = player_hands
            session['deck'] = deck
            
            # After hitting, player can no longer double or split
            session['can_split'] = False
            session['can_double'] = False
            
            # Check if the active hand busted
            if calculate_score(player_hands[active_hand]) > 21:
                if active_hand < len(player_hands) - 1:
                    session['active_hand'] = active_hand + 1
                    session['can_double'] = True
                    
                    new_active_hand = player_hands[active_hand + 1]
                    if len(new_active_hand) == 2 and min(new_active_hand[0], 10) == min(new_active_hand[1], 10) and current_user.coins >= bets[active_hand + 1] * 2:
                        session['can_split'] = True
                    else:
                        session['can_split'] = False
                else:
                    # Check if all player hands are busted
                    all_busted = all(calculate_score(hand) > 21 for hand in player_hands)
                    
                    if all_busted:
                        # End game without playing dealer
                        session['game_over'] = True
                        session['message'] = "All hands busted. Dealer doesn't need to play."
                    else:
                        dealer_turn()
            dealer_score = calculate_score(session.get('dealer', []))
            
            # If the hand has exactly 2 cards of the same value after hitting, can no longer split
            if len(player_hands[active_hand]) > 2:
                session['can_split'] = False
                session['can_double'] = False
            
            # If it's AJAX, return updated state
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return render_template("games/_blackjack_partial.html",
                            player_hands=player_hands,
                            active_hand=session['active_hand'],
                            dealer=dealer,
                            game_over=session.get('game_over', False),
                            bets=bets,
                            message=session.get('message', ""),
                            scores=[calculate_score(hand) for hand in player_hands],
                            can_split=session['can_split'],
                            dealer_score = dealer_score,
                            can_double=session['can_double'])
            else:
                return redirect(url_for('blackjack'))

        # STAND action
        elif request.args.get('action') == 'stand':
            if active_hand < len(player_hands) - 1:
                # Move to the next hand
                session['active_hand'] = active_hand + 1
                session['can_double'] = True  # Can double on the first move of the new hand
                
                # Check if can split the new active hand
                new_active_hand = player_hands[active_hand + 1]
                if len(new_active_hand) == 2 and min(new_active_hand[0], 10) == min(new_active_hand[1], 10) and current_user.coins >= bets[active_hand + 1] * 2:
                    session['can_split'] = True
                else:
                    session['can_split'] = False
            else:
                # All hands played, dealer's turn
                dealer_turn()
            
            return redirect(url_for('blackjack'))
        
        # DOUBLE action
        elif request.args.get('action') == 'double':
            # Double the bet for the active hand
            if bets[active_hand] * 2 <= current_user.coins and can_double:
                # Double the bet
                bets[active_hand] *= 2
                session['bets'] = bets
                
                # Deal one more card
                player_hands[active_hand].append(deck.pop())
                session['player_hands'] = player_hands
                session['deck'] = deck
                
                # Move to next hand or dealer's turn
                if active_hand < len(player_hands) - 1:
                    session['active_hand'] = active_hand + 1
                    session['can_double'] = True  # Reset for next hand
                    
                    # Check if can split the new active hand
                    new_active_hand = player_hands[active_hand + 1]
                    if len(new_active_hand) == 2 and min(new_active_hand[0], 10) == min(new_active_hand[1], 10) and current_user.coins >= bets[active_hand + 1] * 2:
                        session['can_split'] = True
                    else:
                        session['can_split'] = False
                else:
                    # All hands played, dealer's turn
                    dealer_turn()
                
                return redirect(url_for('blackjack'))
        
        # SPLIT action
        elif request.args.get('action') == 'split':
            # Check if the player can split
            current_hand = player_hands[active_hand]
            current_bet = bets[active_hand]
            
            if len(current_hand) == 2 and min(current_hand[0], 10) == min(current_hand[1], 10) and current_user.coins >= current_bet * 2 and can_split:
                # Create two new hands from the split pair
                card1 = current_hand[0]
                card2 = current_hand[1]
                
                # Replace the current hand with just the first card
                player_hands[active_hand] = [card1, deck.pop()]
                
                # Add a new hand with the second card
                player_hands.insert(active_hand + 1, [card2, deck.pop()])
                
                # Add the same bet for the new hand
                bets.insert(active_hand + 1, current_bet)
                
                # Update session
                session['player_hands'] = player_hands
                session['bets'] = bets
                session['deck'] = deck
                
                # Can no longer split the current hand
                session['can_split'] = False
                
                return redirect(url_for('blackjack'))
    
   
    # Prepare data for template
    player_scores = [calculate_score(hand) for hand in player_hands]
    dealer_score = calculate_score(session.get('dealer', []))
    dealer_faces = session.get('dealer_faces', [])

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render_template("games/_blackjack_partial.html",
                           player_hands=player_hands,
                           active_hand=active_hand,
                           dealer=dealer,
                           game_over=game_over,
                           bets=bets,
                           message=message,
                           scores=player_scores,
                           can_split=can_split,
                           can_double=can_double,
                           dealer_score=dealer_score,
                           dealer_faces=dealer_faces)

    return render_template('games/blackjack.html',
                           player_hands=player_hands,
                           active_hand=active_hand,
                           dealer=dealer,
                           game_over=game_over,
                           bets=bets,
                           message=message,
                           scores=player_scores,
                           can_split=can_split,
                           can_double=can_double,
                           dealer_score=dealer_score,
                           dealer_faces=dealer_faces)
if __name__ == '__main__':
    with app.app_context():
        # Ensure avatar directory exists
        ensure_avatar_directory_exists()
        db.create_all()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
    
        if not Game.query.first():
            games = [
                # Game(name='Snake', description='Classic snake game. Eat food and grow longer without hitting walls or yourself!', 
                #      icon='snake.png', price=0),
                # Game(name='Tetris', description='Arrange falling blocks to create complete lines and score points.', 
                #      icon='tetris.png', price=50),
                # Game(name='Pacman', description='Navigate through a maze while collecting dots and avoiding ghosts.', 
                #      icon='pacman.png', price=75),
                # Game(name='Space Invaders', description='Defend Earth from alien invaders in this classic arcade shooter.', 
                #      icon='space_invaders.png', price=100)
            ]
            db.session.add_all(games)
            db.session.commit()
    
    app.run(debug=True, port=8000, host='0.0.0.0')

