from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import datetime
import uuid
from PIL import Image
import io
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = 'miramare_hotel_secret_key_2024'
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Ensure upload directory exists
try:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'images'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'videos'), exist_ok=True)
except Exception as e:
    print(f"Warning: Could not create upload directories: {e}")

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm'}

def allowed_file(filename, file_type):
    if file_type == 'image':
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS
    elif file_type == 'video':
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS
    return False

def init_db():
    try:
        db_path = os.path.join(os.getcwd(), 'miramare_products.db')
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
    except Exception as e:
        print(f"Database error: {e}")
        # Fallback to in-memory database for read-only environments
        conn = sqlite3.connect(':memory:')
        c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        supplier TEXT NOT NULL,
        price REAL NOT NULL,
        currency TEXT DEFAULT 'EUR',
        dimensions TEXT,
        weight REAL,
        weight_unit TEXT DEFAULT 'kg',
        color TEXT,
        material TEXT,
        description TEXT,
        notes TEXT,
        status TEXT DEFAULT 'In Valutazione',
        created_date TEXT NOT NULL,
        updated_date TEXT NOT NULL
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS product_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        filename TEXT NOT NULL,
        original_name TEXT NOT NULL,
        upload_date TEXT NOT NULL,
        FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS product_videos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        filename TEXT NOT NULL,
        original_name TEXT NOT NULL,
        upload_date TEXT NOT NULL,
        FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
    )''')
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    try:
        # Ensure database is initialized
        init_db()
        
        db_path = os.path.join(os.getcwd(), 'miramare_products.db')
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''SELECT p.*, 
                     (SELECT COUNT(*) FROM product_images WHERE product_id = p.id) as image_count,
                     (SELECT COUNT(*) FROM product_videos WHERE product_id = p.id) as video_count
                     FROM products p ORDER BY p.updated_date DESC''')
        products = c.fetchall()
        conn.close()
        return render_template('index.html', products=products)
    except Exception as e:
        print(f"Homepage error: {e}")
        return f"<h1>Hotel Miramare - Sistema Gestione Arredamento</h1><p>Errore: {str(e)}</p><p><a href='/health'>Health Check</a></p>"

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        category = request.form['category']
        supplier = request.form['supplier']
        price = float(request.form['price'])
        currency = request.form['currency']
        dimensions = request.form['dimensions']
        weight = request.form['weight']
        weight_unit = request.form['weight_unit']
        color = request.form['color']
        material = request.form['material']
        description = request.form['description']
        notes = request.form['notes']
        status = request.form['status']
        
        current_time = datetime.now().isoformat()
        
        # Insert product into database
        conn = sqlite3.connect('miramare_products.db')
        c = conn.cursor()
        c.execute('''INSERT INTO products 
                     (name, category, supplier, price, currency, dimensions, weight, weight_unit, 
                      color, material, description, notes, status, created_date, updated_date)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (name, category, supplier, price, currency, dimensions, weight, weight_unit,
                   color, material, description, notes, status, current_time, current_time))
        
        product_id = c.lastrowid
        conn.commit()
        conn.close()
        
        # Handle file uploads
        uploaded_files = request.files.getlist('files')
        for file in uploaded_files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                
                if allowed_file(filename, 'image'):
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'images', unique_filename)
                    file.save(filepath)
                    
                    # Save to database
                    conn = sqlite3.connect('miramare_products.db')
                    c = conn.cursor()
                    c.execute('INSERT INTO product_images (product_id, filename, original_name, upload_date) VALUES (?, ?, ?, ?)',
                              (product_id, unique_filename, filename, current_time))
                    conn.commit()
                    conn.close()
                    
                elif allowed_file(filename, 'video'):
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'videos', unique_filename)
                    file.save(filepath)
                    
                    # Save to database
                    conn = sqlite3.connect('miramare_products.db')
                    c = conn.cursor()
                    c.execute('INSERT INTO product_videos (product_id, filename, original_name, upload_date) VALUES (?, ?, ?, ?)',
                              (product_id, unique_filename, filename, current_time))
                    conn.commit()
                    conn.close()
        
        flash('Prodotto aggiunto con successo!', 'success')
        return redirect(url_for('view_product', id=product_id))
    
    return render_template('add_product.html')

@app.route('/product/<int:id>')
def view_product(id):
    conn = sqlite3.connect('miramare_products.db')
    c = conn.cursor()
    
    # Get product details
    c.execute('SELECT * FROM products WHERE id = ?', (id,))
    product = c.fetchone()
    
    if not product:
        flash('Prodotto non trovato!', 'error')
        return redirect(url_for('index'))
    
    # Get images
    c.execute('SELECT * FROM product_images WHERE product_id = ? ORDER BY upload_date', (id,))
    images = c.fetchall()
    
    # Get videos
    c.execute('SELECT * FROM product_videos WHERE product_id = ? ORDER BY upload_date', (id,))
    videos = c.fetchall()
    
    conn.close()
    
    return render_template('view_product.html', product=product, images=images, videos=videos)

@app.route('/edit_product/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    conn = sqlite3.connect('miramare_products.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        # Update product
        name = request.form['name']
        category = request.form['category']
        supplier = request.form['supplier']
        price = float(request.form['price'])
        currency = request.form['currency']
        dimensions = request.form['dimensions']
        weight = request.form['weight']
        weight_unit = request.form['weight_unit']
        color = request.form['color']
        material = request.form['material']
        description = request.form['description']
        notes = request.form['notes']
        status = request.form['status']
        
        current_time = datetime.now().isoformat()
        
        c.execute('''UPDATE products SET 
                     name=?, category=?, supplier=?, price=?, currency=?, dimensions=?, 
                     weight=?, weight_unit=?, color=?, material=?, description=?, notes=?, 
                     status=?, updated_date=? WHERE id=?''',
                  (name, category, supplier, price, currency, dimensions, weight, weight_unit,
                   color, material, description, notes, status, current_time, id))
        conn.commit()
        conn.close()
        
        flash('Prodotto aggiornato con successo!', 'success')
        return redirect(url_for('view_product', id=id))
    
    # Get product for editing
    c.execute('SELECT * FROM products WHERE id = ?', (id,))
    product = c.fetchone()
    conn.close()
    
    if not product:
        flash('Prodotto non trovato!', 'error')
        return redirect(url_for('index'))
    
    return render_template('edit_product.html', product=product)

@app.route('/delete_product/<int:id>')
def delete_product(id):
    conn = sqlite3.connect('miramare_products.db')
    c = conn.cursor()
    
    # Get files to delete
    c.execute('SELECT filename FROM product_images WHERE product_id = ?', (id,))
    images = c.fetchall()
    c.execute('SELECT filename FROM product_videos WHERE product_id = ?', (id,))
    videos = c.fetchall()
    
    # Delete files from filesystem
    for image in images:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], 'images', image[0]))
        except:
            pass
    
    for video in videos:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], 'videos', video[0]))
        except:
            pass
    
    # Delete from database
    c.execute('DELETE FROM products WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    flash('Prodotto eliminato con successo!', 'success')
    return redirect(url_for('index'))

@app.route('/report')
def generate_report():
    conn = sqlite3.connect('miramare_products.db')
    c = conn.cursor()
    c.execute('''SELECT p.*, 
                 (SELECT COUNT(*) FROM product_images WHERE product_id = p.id) as image_count,
                 (SELECT COUNT(*) FROM product_videos WHERE product_id = p.id) as video_count
                 FROM products p ORDER BY p.category, p.name''')
    products = c.fetchall()
    conn.close()
    
    return render_template('report.html', products=products)

@app.route('/health')
def health_check():
    try:
        import sys
        return jsonify({
            'status': 'ok',
            'python_version': sys.version,
            'cwd': os.getcwd(),
            'upload_folder': app.config['UPLOAD_FOLDER'],
            'files': os.listdir(os.getcwd())[:10]  # First 10 files
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products')
def api_products():
    try:
        db_path = os.path.join(os.getcwd(), 'miramare_products.db')
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('SELECT * FROM products ORDER BY updated_date DESC')
        products = c.fetchall()
        conn.close()
        return jsonify(products)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
