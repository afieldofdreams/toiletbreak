from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    user_type = db.Column(db.String(10), nullable=False)  # 'driver' or 'business'
    business_name = db.Column(db.String(200), nullable=True)  # Only for businesses

class Driver(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company_name = db.Column(db.String(200), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    rating = db.Column(db.Float, default=0.0)
    user = db.relationship('User', backref=db.backref('driver', lazy=True))

class Business(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    business_name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(300), nullable=False)
    toilet_availability = db.Column(db.Boolean, default=True)
    user = db.relationship('User', backref=db.backref('business', lazy=True))

class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'), nullable=False)
    business_id = db.Column(db.Integer, db.ForeignKey('business.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, denied
    arrival_time = db.Column(db.DateTime, nullable=False)
    driver = db.relationship('Driver', backref=db.backref('requests', lazy=True))
    business = db.relationship('Business', backref=db.backref('requests', lazy=True))