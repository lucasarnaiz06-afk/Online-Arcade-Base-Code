from flask import *
from flask_sqlalchemy import SQLAlchemy
from flask_login import *
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import os, datetime, secrets

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=datetime.datetime.now)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    print("a")
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000, host='0.0.0.0')