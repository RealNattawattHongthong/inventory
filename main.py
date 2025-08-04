import qrcode
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os
import random
import string

# Constants
LOGO_SIZE = (80, 80)
QR_SIZE = (80, 80)
QR_VERSION = 1
LOGO_FILE_NAME = 'github-logo.png'
OUTPUT_PDF = 'QR_Codes.pdf'
DEFAULT_COLUMN_SIZE = 8

def generate_item_code():
    """Generate a random 6-character alphanumeric code for items."""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(6))

def generate_qr_code_with_logo(item_id, qr_canvas, x_position, y_position):
    """Generate a QR code with a logo and place it on the PDF canvas.

    Args:
        item_id (int): The ID of the current item.
        qr_canvas: The ReportLab canvas for the PDF.
        num_columns (int): The number of columns in the layout.
        x_position (float): The x-coordinate for placing the QR code.
        y_position (float): The y-coordinate for placing the QR code.
    """

    qr_code = qrcode.QRCode(
        version=QR_VERSION,
        error_correction=qrcode.constants.ERROR_CORRECT_H
    )

    # Generate a unique item code
    item_code = generate_item_code()

    # Combine item ID and item code for QR code data
    data_to_encode = f'Item ID: {item_id}\nItem Code: {item_code}'
    qr_code.add_data(data_to_encode)
    qr_code.make(fit=True)

    # Make a QR code image
    qr_code_image = qr_code.make_image().convert('RGB')

    try:
        # Open and resize the logo image
        logo_path = os.path.join(os.getcwd(), LOGO_FILE_NAME)
        logo = Image.open(logo_path)
        logo_resized = logo.resize(LOGO_SIZE)

        # Calculate the logo position
        logo_x_position = (qr_code_image.size[0] - logo_resized.size[0]) // 2
        logo_y_position = (qr_code_image.size[1] - logo_resized.size[1]) // 2
        logo_position = (logo_x_position, logo_y_position)

        # Paste the logo on the QR code image
        qr_code_image.paste(logo_resized, logo_position)

        # Draw the QR code image on the PDF canvas
        qr_canvas.drawInlineImage(qr_code_image, x_position, y_position, width=QR_SIZE[0], height=QR_SIZE[1])

        # Draw the item ID at the bottom of the QR code
        qr_canvas.setFont("Helvetica", 10)
        code_text = f'{item_code}'
        text_width = qr_canvas.stringWidth(code_text, "Helvetica", 10)
        x_text_position = x_position + (QR_SIZE[0] - text_width) / 2
        y_text_position = y_position - 10
        qr_canvas.drawString(x_text_position, y_text_position, code_text)

    except Exception as e:
        print(f'An error occurred: {e}')



if __name__ == "__main__":
    # Create a canvas for the PDF with portrait orientation
    c = canvas.Canvas(OUTPUT_PDF, pagesize=A4) 

    # Number of items to generate QR codes for
    num_items = 32 

    # Number of columns in the layout
    num_columns = DEFAULT_COLUMN_SIZE
    
    # Calculate the number of full columns and the remaining items for the last column
    num_full_columns = num_items // num_columns
    remaining_items = num_items % num_columns

    # Generate QR codes for full columns
    for column in range(num_full_columns):
        for row in range(num_columns):
            item_id = column * num_columns + row + 1

            x_position = 20 + column * (QR_SIZE[0] + 20)
            y_position = A4[1] - 40 - row * (QR_SIZE[1] + 20) - QR_SIZE[1]

            generate_qr_code_with_logo(item_id, c, x_position, y_position)

    # Generate QR codes for the last column
    for row in range(remaining_items):
        item_id = num_full_columns * num_columns + row + 1

        x_position = 20 + num_full_columns * (QR_SIZE[0] + 20)
        y_position = A4[1] - 40 - row * (QR_SIZE[1] + 20) - QR_SIZE[1]

        generate_qr_code_with_logo(item_id, c, x_position, y_position)


    # Save the PDF
    c.save()
    print(f'QR codes saved in {OUTPUT_PDF}!')