from flask import Flask, request, send_from_directory, jsonify, redirect, url_for,render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os
import shutil
import secrets

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost:5432/nuvE'
app.config['SECRET_KEY'] = secrets.token_urlsafe(16)
db = SQLAlchemy(app)

login_manager = LoginManager(app)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)
    size = db.Column(db.Integer, nullable=False)
    mimetype = db.Column(db.String(255), nullable=False)
    iduser = db.Column(db.Integer, nullable=False)
    share_link = db.Column(db.String(255))

    def __repr__(self):
        return f'<File {self.filename}>'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return redirect(url_for('register'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            return 'Username already exists'
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    else:
        return render_template('register.html')
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('list_files'))
        else:
            return 'Invalid username or password'
    else:
        return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/files', methods=['GET'])
@login_required
def list_files():
    files = File.query.filter_by(iduser=current_user.id).all()
    return render_template('list_files.html', files=files)

@app.route('/files', methods=['POST'])
@login_required
def upload_file():
    try:
        file = request.files['file']
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        filepath = os.path.normpath(filepath)
        file.save(filepath)
        size = os.path.getsize(filepath)
        mimetype = file.mimetype
        iduser = current_user.id
        share_link = secrets.token_urlsafe(16)
        new_file = File(filename=filename, filepath=filepath, size=size, mimetype=mimetype,iduser=iduser,share_link=share_link)
        db.session.add(new_file)
        db.session.commit()
        return redirect(url_for('list_files'))
    except:
        return redirect(url_for('list_files'))

@app.route('/files/<int:id>/download', methods=['GET'])
@login_required
def download(id):
    file = File.query.get_or_404(id)
    return send_from_directory(os.path.dirname(file.filepath), file.filename, as_attachment=True)

@app.route('/files/<int:id>/delete', methods=['GET', 'POST', 'DELETE'])
@login_required
def delete_file(id):
    if request.method == 'POST' or request.method == 'DELETE':
        file = File.query.filter_by(id=id, iduser=current_user.id).first_or_404()  
        filepath = file.filepath
        db.session.delete(file)
        db.session.commit()
        os.remove(filepath)
        return redirect(url_for('list_files'))
    else:
        return redirect(url_for('list_files'))

@app.route('/files/share/<string:share_link>', methods=['GET'])
def share_file(share_link):
    file = File.query.filter_by(share_link=share_link).first_or_404()
    return render_template('share_file.html', file=file)

if __name__ == '__main__':
    app.run(debug=True)