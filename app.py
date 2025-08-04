from flask import Flask, render_template, request, jsonify, send_file
import qrcode
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os
import random
import string
import io
import base64
from datetime import datetime

app = Flask(__name__)

# Constants
LOGO_SIZE = (80, 80)
QR_SIZE = (200, 200)
QR_VERSION = 1
LOGO_FILE_NAME = 'github-logo.png'

def generate_item_code():
    """Generate a random 6-character alphanumeric code for items."""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(6))

def generate_qr_code_image(item_id, item_code):
    """Generate a QR code image with logo."""
    qr = qrcode.QRCode(
        version=QR_VERSION,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    
    # Combine item ID and item code for QR code data
    data_to_encode = f'Item ID: {item_id}\nItem Code: {item_code}'
    qr.add_data(data_to_encode)
    qr.make(fit=True)
    
    # Make a QR code image
    qr_image = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    
    try:
        # Open and resize the logo image
        logo_path = os.path.join(os.getcwd(), LOGO_FILE_NAME)
        if os.path.exists(logo_path):
            logo = Image.open(logo_path)
            logo_resized = logo.resize(LOGO_SIZE)
            
            # Calculate the logo position
            logo_x = (qr_image.size[0] - logo_resized.size[0]) // 2
            logo_y = (qr_image.size[1] - logo_resized.size[1]) // 2
            logo_position = (logo_x, logo_y)
            
            # Paste the logo on the QR code image
            qr_image.paste(logo_resized, logo_position)
    except Exception as e:
        print(f'Logo error: {e}')
    
    return qr_image

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    data = request.json
    item_id = data.get('item_id', 1)
    custom_code = data.get('custom_code', '')
    
    # Use custom code if provided, otherwise generate random code
    if custom_code and custom_code.strip():
        item_code = custom_code.strip().upper()
    else:
        item_code = generate_item_code()
    
    # Generate QR code image
    qr_image = generate_qr_code_image(item_id, item_code)
    
    # Convert image to base64 for display
    buffered = io.BytesIO()
    qr_image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return jsonify({
        'success': True,
        'item_id': item_id,
        'item_code': item_code,
        'qr_image': f'data:image/png;base64,{img_str}'
    })

@app.route('/generate_batch', methods=['POST'])
def generate_batch():
    data = request.json
    num_items = data.get('num_items', 32)
    
    qr_codes = []
    for i in range(1, num_items + 1):
        item_code = generate_item_code()
        qr_image = generate_qr_code_image(i, item_code)
        
        # Convert to base64
        buffered = io.BytesIO()
        qr_image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        qr_codes.append({
            'item_id': i,
            'item_code': item_code,
            'qr_image': f'data:image/png;base64,{img_str}'
        })
    
    return jsonify({
        'success': True,
        'qr_codes': qr_codes
    })

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    data = request.json
    num_items = data.get('num_items', 32)
    num_columns = data.get('num_columns', 8)
    
    # Create PDF in memory
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=A4)
    
    # PDF generation logic (similar to original main.py)
    QR_PDF_SIZE = (80, 80)
    
    # Calculate the number of full columns and remaining items
    num_full_columns = num_items // num_columns
    remaining_items = num_items % num_columns
    
    # Generate QR codes for full columns
    for column in range(num_full_columns):
        for row in range(num_columns):
            item_id = column * num_columns + row + 1
            item_code = generate_item_code()
            
            x_position = 20 + column * (QR_PDF_SIZE[0] + 20)
            y_position = A4[1] - 40 - row * (QR_PDF_SIZE[1] + 20) - QR_PDF_SIZE[1]
            
            # Generate QR code
            qr_image = generate_qr_code_image(item_id, item_code)
            
            # Draw QR code on PDF
            img_buffer = io.BytesIO()
            qr_image.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            c.drawInlineImage(qr_image, x_position, y_position, 
                            width=QR_PDF_SIZE[0], height=QR_PDF_SIZE[1])
            
            # Draw item code text
            c.setFont("Helvetica", 10)
            text_width = c.stringWidth(item_code, "Helvetica", 10)
            x_text = x_position + (QR_PDF_SIZE[0] - text_width) / 2
            y_text = y_position - 10
            c.drawString(x_text, y_text, item_code)
    
    # Generate QR codes for the last column
    for row in range(remaining_items):
        item_id = num_full_columns * num_columns + row + 1
        item_code = generate_item_code()
        
        x_position = 20 + num_full_columns * (QR_PDF_SIZE[0] + 20)
        y_position = A4[1] - 40 - row * (QR_PDF_SIZE[1] + 20) - QR_PDF_SIZE[1]
        
        # Generate QR code
        qr_image = generate_qr_code_image(item_id, item_code)
        
        # Draw QR code on PDF
        c.drawInlineImage(qr_image, x_position, y_position, 
                        width=QR_PDF_SIZE[0], height=QR_PDF_SIZE[1])
        
        # Draw item code text
        c.setFont("Helvetica", 10)
        text_width = c.stringWidth(item_code, "Helvetica", 10)
        x_text = x_position + (QR_PDF_SIZE[0] - text_width) / 2
        y_text = y_position - 10
        c.drawString(x_text, y_text, item_code)
    
    # Save PDF
    c.save()
    pdf_buffer.seek(0)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'QR_Codes_{timestamp}.pdf'
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)