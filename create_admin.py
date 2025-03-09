from app import app, db
from models import User

with app.app_context():
    if not User.query.filter_by(username='admin').first():
        user = User(username='admin')
        user.set_password('admin')
        db.session.add(user)
        db.session.commit()
        print('Admin user created successfully')
    else:
        print('Admin user already exists')