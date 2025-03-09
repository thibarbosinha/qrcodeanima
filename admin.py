from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from models import User, db
import os

admin_bp = Blueprint('admin', __name__, static_folder='predefined_gifs', static_url_path='/static/predefined_gifs')
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('admin.dashboard'))
        flash('Credenciais inválidas')
    
    return render_template('admin/login.html')

@admin_bp.route('/admin/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('admin.login'))

@admin_bp.route('/admin/dashboard')
@login_required
def dashboard():
    page = request.args.get('page', 1, type=int)
    items_per_page = 12
    gifs = get_predefined_gifs()
    total_gifs = len(gifs)
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    total_pages = (total_gifs + items_per_page - 1) // items_per_page
    return render_template('admin/dashboard.html', 
                          gifs=gifs,
                          start_idx=start_idx,
                          end_idx=end_idx,
                          current_page=page,
                          total_pages=total_pages)

@admin_bp.route('/admin/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not current_password or not new_password or not confirm_password:
        flash('Todos os campos de senha são obrigatórios', 'error')
        return redirect(url_for('admin.dashboard'))

    if new_password != confirm_password:
        flash('As novas senhas não coincidem', 'error')
        return redirect(url_for('admin.dashboard'))

    if not current_user.check_password(current_password):
        flash('A senha atual está incorreta', 'error')
        return redirect(url_for('admin.dashboard'))

    current_user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    flash('Senha alterada com sucesso', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/admin/upload', methods=['POST'])
@admin_required
def upload_gif():
    if 'gif' not in request.files:
        flash('Nenhum arquivo enviado')
        return redirect(url_for('admin.dashboard'))
    
    file = request.files['gif']
    if file.filename == '':
        flash('Nenhum arquivo selecionado')
        return redirect(url_for('admin.dashboard'))
    
    if not file.filename.lower().endswith('.gif'):
        flash('Apenas arquivos GIF são permitidos')
        return redirect(url_for('admin.dashboard'))
    
    try:
        filename = secure_filename(file.filename)
        file.save(os.path.join('predefined_gifs', filename))
        flash('GIF enviado com sucesso')
    except Exception as e:
        flash(f'Erro ao enviar arquivo: {str(e)}')
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/admin/delete/<filename>')
@admin_required
def delete_gif(filename):
    try:
        os.remove(os.path.join('predefined_gifs', filename))
        flash('GIF excluído com sucesso')
    except Exception as e:
        flash(f'Erro ao excluir arquivo: {str(e)}')
    
    return redirect(url_for('admin.dashboard'))

def get_predefined_gifs():
    predefined_gifs_dir = 'predefined_gifs'
    if not os.path.exists(predefined_gifs_dir):
        os.makedirs(predefined_gifs_dir)
    
    gifs = []
    for filename in os.listdir(predefined_gifs_dir):
        if filename.lower().endswith('.gif'):
            gifs.append({
                'filename': filename,
                'url': url_for('static', filename=f'predefined_gifs/{filename}')
            })
    return gifs