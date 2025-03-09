import os
import datetime
from flask import Flask, render_template, request, send_from_directory, session, redirect, url_for
import segno
from werkzeug.utils import secure_filename
from admin import admin_bp, login_manager, get_predefined_gifs
from models import db, User

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SECRET_KEY'] = 'dj38dj3k2l1m4n5b6v7c8x9z0'  # Secure secret key for session management
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/app.db'  # Use instance folder for database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Ensure upload directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize SQLAlchemy
db.init_app(app)

# Initialize Flask-Login
login_manager.init_app(app)
login_manager.login_view = 'admin.login'

# Register the admin blueprint
app.register_blueprint(admin_bp)

# Create database tables
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        print(f"Error creating database tables: {e}")

# Ensure required directories exist with proper permissions
for directory in ['predefined_gifs']:
    if not os.path.exists(directory):
        try:
            os.makedirs(directory, mode=0o777, exist_ok=True)
        except OSError as e:
            print(f"Warning: Could not create directory {directory}: {e}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'gif'

# Add datetime to all templates
@app.context_processor
def inject_now():
    return {'now': datetime.datetime.now}

@app.route('/step1')
def step1():
    return render_template('step1.html', url=session.get('url', ''))

@app.route('/step2', methods=['POST'])
def step2():
    url = request.form.get('url')
    if not url:
        return render_template('step1.html', error='URL is required')
    
    session['url'] = url
    predefined_gifs = get_predefined_gifs()
    return render_template('step2.html', url=url, predefined_gifs=predefined_gifs)

@app.route('/step3', methods=['POST'])
def step3():
    url = session.get('url')
    if not url:
        return redirect(url_for('step1'))
    
    gif_choice = request.form.get('gif_choice')
    if not gif_choice:
        return render_template('step2.html', error='Please select or upload a GIF')
    
    try:
        if gif_choice.startswith('predefined:'):
            # Use predefined GIF
            background_filename = gif_choice.split(':', 1)[1]
            # Use absolute path for predefined GIFs
            background_path = os.path.join(os.getcwd(), 'predefined_gifs', background_filename)
            if not os.path.exists(background_path):
                return render_template('step2.html', error='Predefined GIF not found')
        else:
            # Handle uploaded file
            if 'custom_gif' not in request.files:
                return render_template('step2.html', error='No file uploaded')
            
            file = request.files['custom_gif']
            if file.filename == '':
                return render_template('step2.html', error='No file selected')
            
            if not allowed_file(file.filename):
                return render_template('step2.html', error='Only GIF files are allowed')
            
            background_filename = secure_filename(file.filename)
            background_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp', background_filename)
            os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'temp'), exist_ok=True)
            file.save(background_path)
        
        scale = int(request.form.get('scale', 8))
        
        # Generate QR code
        qr = segno.make(url, error='h')
        output_filename = f'qr_output_{os.path.splitext(background_filename)[0]}.gif'
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp', output_filename)
        
        # Create QR code with background
        qr.to_artistic(
            background=background_path,
            target=output_path,
            scale=scale,
            dark='#33333366',
            finder_dark='#333333',
            finder_light='#FFFFFF'
        )
        
        # Move the generated QR code to uploads directory
        final_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        os.rename(output_path, final_path)
        
        # Clean up temporary files
        if not gif_choice.startswith('predefined:'):
            try:
                os.remove(background_path)
            except OSError:
                pass
        
        # Use the local URL for the QR code
        qr_code_url = url_for('uploaded_file', filename=output_filename)
        
        return render_template('step3.html', qr_code=qr_code_url, background_filename=background_filename, gif_choice=gif_choice)
    
    except Exception as e:
        print(f"Error in step3: {str(e)}")  # Add logging for debugging
        # Clean up any temporary files
        if 'background_path' in locals() and os.path.exists(background_path):
            try:
                os.remove(background_path)
            except OSError:
                pass
        if 'output_path' in locals() and os.path.exists(output_path):
            try:
                os.remove(output_path)
            except OSError:
                pass
        return render_template('step2.html', error=str(e))

@app.route('/')
def index():
    return redirect(url_for('step1'))

@app.route('/generate', methods=['POST'])
def generate_qr():
    if 'background' not in request.files:
        return render_template('index.html', error='No file uploaded')
    
    file = request.files['background']
    if file.filename == '':
        return render_template('index.html', error='No file selected')
    
    if not allowed_file(file.filename):
        return render_template('index.html', error='Only GIF files are allowed')
    
    url = request.form.get('url')
    if not url:
        return render_template('index.html', error='URL is required')
    
    scale = int(request.form.get('scale', 8))  # Decreased scale for faster generation
    
    try:
        # Generate QR code
        qr = segno.make(url, error='h')
        output_filename = f'qr_output_{background_filename}'
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        # Create QR code with background
        qr.to_artistic(
            background=background_path,
            target=output_path,
            scale=scale,
            dark='#33333366',  # Semi-transparent dark modules
            finder_dark='#333333',  # Solid dark for finder patterns
            finder_light='#FFFFFF'  # Solid white for finder patterns
        )
        
        return render_template('index.html', qr_code=f'/uploads/{output_filename}', background_filename=background_filename)
    
    except Exception as e:
        return render_template('index.html', error=str(e))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)