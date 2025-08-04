from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import qrcode
from PIL import Image
import os
import io
import base64
import string
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

db = SQLAlchemy(app)

# Database Models
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
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }

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

@app.route('/')
def index():
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    
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
    
    items = query.order_by(Item.created_at.desc()).all()
    categories = db.session.query(Item.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    return render_template('inventory_index.html', 
                         items=items, 
                         search=search, 
                         categories=categories,
                         selected_category=category)

@app.route('/item/<code>')
def item_detail(code):
    item = Item.query.filter_by(code=code).first_or_404()
    return render_template('item_detail.html', item=item)

@app.route('/add', methods=['GET', 'POST'])
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
            status=request.form.get('status', 'available')
        )
        
        db.session.add(item)
        db.session.commit()
        
        return redirect(url_for('item_detail', code=item.code))
    
    return render_template('add_item.html')

@app.route('/edit/<code>', methods=['GET', 'POST'])
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
    app.run(debug=True, host='0.0.0.0', port=8080)