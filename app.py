from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import datetime
import uuid
from PIL import Image
import io
import base64
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

app = Flask(__name__)
app.config['SECRET_KEY'] = 'miramare_hotel_secret_key_2024'
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://miramare_hotel_user:uGU7iPjCJy2RHgn1NBunQmW5RIpC8K6p@dpg-d2jhejh5pdvs73f847i0-a.frankfurt-postgres.render.com/miramare_hotel')
USE_POSTGRES = POSTGRES_AVAILABLE and DATABASE_URL.startswith('postgresql')

# Template helper function for datetime formatting
@app.template_filter('format_datetime')
def format_datetime(value):
    """Format datetime for display in templates"""
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d alle %H:%M')
    elif isinstance(value, str):
        # Handle ISO format string from SQLite
        if 'T' in value:
            return value[:16].replace('T', ' alle ')
        return value[:10]
    return str(value)

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

def get_db_connection():
    """Get database connection based on configuration"""
    if USE_POSTGRES:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            return conn, 'postgres'
        except Exception as e:
            print(f"PostgreSQL connection failed: {e}")
            print("Falling back to SQLite...")
    
    # Fallback to SQLite
    try:
        db_path = os.path.join(os.getcwd(), 'miramare_products.db')
        conn = sqlite3.connect(db_path)
        return conn, 'sqlite'
    except Exception as e:
        print(f"SQLite connection failed: {e}")
        # Last resort: in-memory database
        conn = sqlite3.connect(':memory:')
        return conn, 'sqlite'

def init_db():
    """Initialize database tables"""
    conn, db_type = get_db_connection()
    
    if db_type == 'postgres':
        c = conn.cursor()
        # PostgreSQL syntax
        c.execute('''CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            category VARCHAR(100) NOT NULL,
            supplier VARCHAR(255) NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            currency VARCHAR(10) DEFAULT 'EUR',
            dimensions TEXT,
            weight DECIMAL(10,2),
            weight_unit VARCHAR(10) DEFAULT 'kg',
            color VARCHAR(100),
            material VARCHAR(255),
            description TEXT,
            notes TEXT,
            status VARCHAR(50) DEFAULT 'In Valutazione',
            created_date TIMESTAMP NOT NULL,
            updated_date TIMESTAMP NOT NULL
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS product_images (
            id SERIAL PRIMARY KEY,
            product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
            filename VARCHAR(255) NOT NULL,
            original_name VARCHAR(255) NOT NULL,
            upload_date TIMESTAMP NOT NULL
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS product_videos (
            id SERIAL PRIMARY KEY,
            product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
            filename VARCHAR(255) NOT NULL,
            original_name VARCHAR(255) NOT NULL,
            upload_date TIMESTAMP NOT NULL
        )''')
    else:
        # SQLite syntax
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
        
        conn, db_type = get_db_connection()
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
        
        # Handle empty numeric fields for PostgreSQL
        weight = float(weight) if weight and weight.strip() else None
        
        current_time = datetime.now().isoformat()
        
        # Insert product into database
        conn, db_type = get_db_connection()
        c = conn.cursor()
        
        if db_type == 'postgres':
            c.execute('''INSERT INTO products 
                         (name, category, supplier, price, currency, dimensions, weight, weight_unit, 
                          color, material, description, notes, status, created_date, updated_date)
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id''',
                      (name, category, supplier, price, currency, dimensions, weight, weight_unit,
                       color, material, description, notes, status, current_time, current_time))
            product_id = c.fetchone()[0]
        else:
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
                    conn, db_type = get_db_connection()
                    c = conn.cursor()
                    if db_type == 'postgres':
                        c.execute('INSERT INTO product_images (product_id, filename, original_name, upload_date) VALUES (%s, %s, %s, %s)',
                                  (product_id, unique_filename, filename, current_time))
                    else:
                        c.execute('INSERT INTO product_images (product_id, filename, original_name, upload_date) VALUES (?, ?, ?, ?)',
                                  (product_id, unique_filename, filename, current_time))
                    conn.commit()
                    conn.close()
                    
                elif allowed_file(filename, 'video'):
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'videos', unique_filename)
                    file.save(filepath)
                    
                    # Save to database
                    conn, db_type = get_db_connection()
                    c = conn.cursor()
                    if db_type == 'postgres':
                        c.execute('INSERT INTO product_videos (product_id, filename, original_name, upload_date) VALUES (%s, %s, %s, %s)',
                                  (product_id, unique_filename, filename, current_time))
                    else:
                        c.execute('INSERT INTO product_videos (product_id, filename, original_name, upload_date) VALUES (?, ?, ?, ?)',
                                  (product_id, unique_filename, filename, current_time))
                    conn.commit()
                    conn.close()
        
        flash('Prodotto aggiunto con successo!', 'success')
        return redirect(url_for('view_product', id=product_id))
    
    return render_template('add_product.html')

@app.route('/product/<int:id>')
def view_product(id):
    conn, db_type = get_db_connection()
    c = conn.cursor()
    
    # Get product details
    if db_type == 'postgres':
        c.execute('SELECT * FROM products WHERE id = %s', (id,))
    else:
        c.execute('SELECT * FROM products WHERE id = ?', (id,))
    product = c.fetchone()
    
    if not product:
        flash('Prodotto non trovato!', 'error')
        return redirect(url_for('index'))
    
    # Get images
    if db_type == 'postgres':
        c.execute('SELECT * FROM product_images WHERE product_id = %s ORDER BY upload_date', (id,))
    else:
        c.execute('SELECT * FROM product_images WHERE product_id = ? ORDER BY upload_date', (id,))
    images = c.fetchall()
    
    # Get videos
    if db_type == 'postgres':
        c.execute('SELECT * FROM product_videos WHERE product_id = %s ORDER BY upload_date', (id,))
    else:
        c.execute('SELECT * FROM product_videos WHERE product_id = ? ORDER BY upload_date', (id,))
    videos = c.fetchall()
    
    conn.close()
    
    return render_template('view_product.html', product=product, images=images, videos=videos)

@app.route('/edit_product/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    conn, db_type = get_db_connection()
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
        
        # Handle empty numeric fields for PostgreSQL
        weight = float(weight) if weight and weight.strip() else None
        
        current_time = datetime.now().isoformat()
        
        if db_type == 'postgres':
            c.execute('''UPDATE products SET 
                         name=%s, category=%s, supplier=%s, price=%s, currency=%s, dimensions=%s, 
                         weight=%s, weight_unit=%s, color=%s, material=%s, description=%s, notes=%s, 
                         status=%s, updated_date=%s WHERE id=%s''',
                      (name, category, supplier, price, currency, dimensions, weight, weight_unit,
                       color, material, description, notes, status, current_time, id))
        else:
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
    if db_type == 'postgres':
        c.execute('SELECT * FROM products WHERE id = %s', (id,))
    else:
        c.execute('SELECT * FROM products WHERE id = ?', (id,))
    product = c.fetchone()
    conn.close()
    
    if not product:
        flash('Prodotto non trovato!', 'error')
        return redirect(url_for('index'))
    
    return render_template('edit_product.html', product=product)

@app.route('/delete_product/<int:id>')
def delete_product(id):
    conn, db_type = get_db_connection()
    c = conn.cursor()
    
    # Get files to delete
    if db_type == 'postgres':
        c.execute('SELECT filename FROM product_images WHERE product_id = %s', (id,))
        images = c.fetchall()
        c.execute('SELECT filename FROM product_videos WHERE product_id = %s', (id,))
        videos = c.fetchall()
    else:
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
    if db_type == 'postgres':
        c.execute('DELETE FROM products WHERE id = %s', (id,))
    else:
        c.execute('DELETE FROM products WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    flash('Prodotto eliminato con successo!', 'success')
    return redirect(url_for('index'))

@app.route('/report')
def generate_report():
    conn, db_type = get_db_connection()
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
        conn, db_type = get_db_connection()
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
