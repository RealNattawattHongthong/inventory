from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from authlib.integrations.flask_client import OAuth
from datetime import datetime
import pytz
import qrcode
from PIL import Image
import os
import io
import base64
import string
import random
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set timezone
TIMEZONE = pytz.timezone('Asia/Bangkok')  # GMT+7

def to_local_time(utc_dt):
    """Convert UTC datetime to local timezone"""
    if utc_dt:
        return pytz.utc.localize(utc_dt).astimezone(TIMEZONE)
    return None

app = Flask(__name__)

# Add timezone filter for templates
@app.template_filter('localtime')
def localtime_filter(utc_dt):
    """Template filter to convert UTC to local time"""
    local_dt = to_local_time(utc_dt)
    if local_dt:
        return local_dt.strftime('%B %d, %Y at %I:%M %p GMT+7')
    return ''

# Database configuration - use PostgreSQL on Heroku, SQLite locally
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    # Fix for Heroku postgres URL
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# GitHub OAuth Config - You need to set these environment variables
app.config['GITHUB_CLIENT_ID'] = os.environ.get('GITHUB_CLIENT_ID', '')
app.config['GITHUB_CLIENT_SECRET'] = os.environ.get('GITHUB_CLIENT_SECRET', '')

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in with GitHub to access this page.'

# OAuth setup
oauth = OAuth(app)
github = oauth.register(
    name='github',
    client_id=app.config['GITHUB_CLIENT_ID'],
    client_secret=app.config['GITHUB_CLIENT_SECRET'],
    access_token_url='https://github.com/login/oauth/access_token',
    access_token_params=None,
    authorize_url='https://github.com/login/oauth/authorize',
    authorize_params=None,
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'},
)

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    github_id = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    avatar_url = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    location = db.Column(db.String(200))
    quantity = db.Column(db.Integer, default=1)
    status = db.Column(db.String(50), default='available')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_by = db.relationship('User', backref='items')
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'location': self.location,
            'quantity': self.quantity,
            'status': self.status,
            'created_at': to_local_time(self.created_at).strftime('%Y-%m-%d %H:%M:%S GMT+7') if self.created_at else None,
            'updated_at': to_local_time(self.updated_at).strftime('%Y-%m-%d %H:%M:%S GMT+7') if self.updated_at else None,
            'created_by': self.created_by.username if self.created_by else None
        }

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def generate_item_code():
    """Generate a unique item code"""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Item.query.filter_by(code=code).first():
            return code

def generate_qr_code_image(item_code, item_name):
    """Generate QR code for an item"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    
    # Create URL for item detail page
    base_url = request.host_url.rstrip('/')
    item_url = f"{base_url}/item/{item_code}"
    
    qr.add_data(item_url)
    qr.make(fit=True)
    
    qr_image = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    
    # Try to add logo if exists
    try:
        logo_path = os.path.join(os.getcwd(), '02.jpg')
        if os.path.exists(logo_path):
            logo = Image.open(logo_path)
            logo_size = (60, 60)
            logo_resized = logo.resize(logo_size)
            
            logo_x = (qr_image.size[0] - logo_resized.size[0]) // 2
            logo_y = (qr_image.size[1] - logo_resized.size[1]) // 2
            
            qr_image.paste(logo_resized, (logo_x, logo_y))
    except Exception as e:
        print(f'Logo error: {e}')
    
    return qr_image

# Auth Routes
@app.route('/login')
def login():
    if not app.config['GITHUB_CLIENT_ID'] or not app.config['GITHUB_CLIENT_SECRET']:
        flash('GitHub OAuth is not configured. Please set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET environment variables.', 'error')
        return redirect(url_for('index'))
    redirect_uri = url_for('authorize', _external=True)
    return github.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    token = github.authorize_access_token()
    resp = github.get('user', token=token)
    user_info = resp.json()
    
    # Get user email
    email_resp = github.get('user/emails', token=token)
    emails = email_resp.json()
    primary_email = next((e['email'] for e in emails if e['primary']), None)
    
    # Create or update user
    user = User.query.filter_by(github_id=str(user_info['id'])).first()
    if not user:
        user = User(
            github_id=str(user_info['id']),
            username=user_info['login'],
            email=primary_email,
            avatar_url=user_info['avatar_url']
        )
        db.session.add(user)
    else:
        user.username = user_info['login']
        user.email = primary_email
        user.avatar_url = user_info['avatar_url']
    
    db.session.commit()
    login_user(user)
    
    next_page = request.args.get('next')
    return redirect(next_page) if next_page else redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Public Routes
@app.route('/')
def index():
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    status = request.args.get('status', '')
    
    query = Item.query
    
    if search:
        query = query.filter(
            db.or_(
                Item.name.contains(search),
                Item.code.contains(search),
                Item.description.contains(search)
            )
        )
    
    if category:
        query = query.filter_by(category=category)
    
    if status:
        query = query.filter_by(status=status)
    
    items = query.order_by(Item.created_at.desc()).all()
    categories = db.session.query(Item.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    statuses = db.session.query(Item.status).distinct().all()
    statuses = [s[0] for s in statuses if s[0]]
    
    return render_template('inventory_auth_index.html', 
                         items=items, 
                         search=search, 
                         categories=categories,
                         selected_category=category,
                         statuses=statuses,
                         selected_status=status)

@app.route('/item/<code>')
def item_detail(code):
    item = Item.query.filter_by(code=code).first_or_404()
    return render_template('item_auth_detail.html', item=item)

# Protected Routes
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == 'POST':
        code = request.form.get('code') or generate_item_code()
        
        # Check if code already exists
        if Item.query.filter_by(code=code).first():
            return render_template('add_item.html', error='Item code already exists')
        
        item = Item(
            code=code,
            name=request.form.get('name'),
            description=request.form.get('description'),
            category=request.form.get('category'),
            location=request.form.get('location'),
            quantity=int(request.form.get('quantity', 1)),
            status=request.form.get('status', 'available'),
            created_by=current_user
        )
        
        db.session.add(item)
        db.session.commit()
        
        return redirect(url_for('item_detail', code=item.code))
    
    return render_template('add_item.html')

@app.route('/edit/<code>', methods=['GET', 'POST'])
@login_required
def edit_item(code):
    item = Item.query.filter_by(code=code).first_or_404()
    
    if request.method == 'POST':
        item.name = request.form.get('name')
        item.description = request.form.get('description')
        item.category = request.form.get('category')
        item.location = request.form.get('location')
        item.quantity = int(request.form.get('quantity', 1))
        item.status = request.form.get('status')
        item.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return redirect(url_for('item_detail', code=item.code))
    
    return render_template('edit_item.html', item=item)

@app.route('/delete/<code>', methods=['POST'])
@login_required
def delete_item(code):
    item = Item.query.filter_by(code=code).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/qr/<code>')
def generate_qr(code):
    item = Item.query.filter_by(code=code).first_or_404()
    
    qr_image = generate_qr_code_image(item.code, item.name)
    
    buffered = io.BytesIO()
    qr_image.save(buffered, format="PNG")
    buffered.seek(0)
    
    return send_file(buffered, mimetype='image/png', 
                     as_attachment=True,
                     download_name=f'qr_{item.code}.png')

# API Routes
@app.route('/api/items')
def api_items():
    items = Item.query.all()
    return jsonify([item.to_dict() for item in items])

@app.route('/api/item/<code>')
def api_item(code):
    item = Item.query.filter_by(code=code).first_or_404()
    return jsonify(item.to_dict())

# Create tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    if not app.config['GITHUB_CLIENT_ID'] or not app.config['GITHUB_CLIENT_SECRET']:
        print("\n⚠️  WARNING: GitHub OAuth is not configured!")
        print("To enable GitHub authentication, you need to:")
        print("1. Create a GitHub OAuth App at https://github.com/settings/applications/new")
        print("2. Set the Authorization callback URL to: http://localhost:8080/authorize")
        print("3. Set these environment variables:")
        print("   export GITHUB_CLIENT_ID='your-client-id'")
        print("   export GITHUB_CLIENT_SECRET='your-client-secret'\n")
    
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)