from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask import flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///marketplace.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)

migrate = Migrate(app, db)

from models import User, Driver, Business, Request

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Should ideally redirect to the login page if there is already a users. Consider this logic for later
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        user_type = request.form['user_type']
        business_name = request.form.get('business_name', None) if user_type == 'business' else None

        # Check if the username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists. Please choose another one.", "danger")
            return redirect(url_for('register'))

        # Create a new user
        new_user = User(username=username, password=password, user_type=user_type, business_name=business_name)
        db.session.add(new_user)
        db.session.commit()

        if user_type == 'driver':
            new_driver = Driver(
                user_id=new_user.id,
                company_name=request.form['company_name'],
                phone_number=request.form['phone_number'],
                email=request.form['email']
            )
            db.session.add(new_driver)
        elif user_type == 'business':
            new_business = Business(user_id=new_user.id, business_name=business_name, address=request.form['address'])
            db.session.add(new_business)

        db.session.commit()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/request_access', methods=['POST'])
def request_access():
    if 'user_id' not in session or session['user_type'] != 'driver':
        return redirect(url_for('login'))

    driver = Driver.query.filter_by(user_id=session['user_id']).first()
    business_id = request.form['business_id']
    arrival_time = request.form['arrival_time']
    print(f"arrival_time is {arrival_time}")

    if not driver:
        flash("Driver profile not found!", "danger")
        return redirect(url_for('driver_dashboard'))

    # Convert arrival time to datetime format
    try:
        if "T" in arrival_time:  # Fix for datetime-local input format
            arrival_time = datetime.strptime(arrival_time, "%Y-%m-%dT%H:%M")
        else:  # Backup format check
            arrival_time = datetime.strptime(arrival_time, "%Y-%m-%d %H:%M")
    except ValueError:
        flash("Invalid arrival time format! Use YYYY-MM-DD HH:MM.", "danger")
        return redirect(url_for('driver_dashboard'))

    new_request = Request(driver_id=driver.id, business_id=business_id, arrival_time=arrival_time)
    db.session.add(new_request)
    db.session.commit()

    flash("Request submitted successfully!", "success")
    return redirect(url_for('driver_dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        # import ipdb; ipdb.set_trace()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_type'] = user.user_type
            print(f"Login successful for {user.username}, user_type: {user.user_type}")  # Debugging

            # Redirect to the correct dashboard
            if user.user_type == 'driver':
                print(f"Redirecting {user.username} to their driver dashboard...")
                return redirect(url_for('driver_dashboard'))
            elif user.user_type == 'business':
                print(f"Redirecting {user.username} to their business dashboard...")
                return redirect(url_for('business_dashboard'))
        else:
            print(f"Password incorrect for {user.username}")  # Debugging
            flash("Invalid username or password", "danger")


        flash("Invalid username or password", "danger")

    return render_template('login.html')


@app.route('/approve_request', methods=['POST'])
def approve_request():
    if 'user_id' not in session or session['user_type'] != 'business':
        return redirect(url_for('login'))

    request_id = request.form['request_id']
    req = Request.query.get(request_id)
    
    if req:
        req.status = 'approved'
        db.session.commit()
        flash("Request approved successfully!", "success")
    else:
        flash("Request not found!", "danger")
    
    return redirect(url_for('business_dashboard'))

@app.route('/deny_request', methods=['POST'])
def deny_request():
    if 'user_id' not in session or session['user_type'] != 'business':
        return redirect(url_for('login'))

    request_id = request.form['request_id']
    req = Request.query.get(request_id)
    
    if req:
        req.status = 'denied'
        db.session.commit()
        flash("Request denied successfully!", "warning")
    else:
        flash("Request not found!", "danger")
    
    return redirect(url_for('business_dashboard'))

@app.route('/driver_dashboard')
def driver_dashboard():
    if 'user_id' not in session or session['user_type'] != 'driver':
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    driver = Driver.query.filter_by(user_id=user.id).first()
    requests = Request.query.filter_by(driver_id=driver.id).all()
    businesses = Business.query.all()  # Fetch available businesses for the driver
    return render_template('driver_dashboard.html', user=user, businesses=businesses, requests=requests)

@app.route('/business_dashboard')
def business_dashboard():
    if 'user_id' not in session or session['user_type'] != 'business':
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    business = Business.query.filter_by(user_id=user.id).first()

    if not business:
        flash("Business profile not found!", "danger")
        return redirect(url_for('login'))

    requests = Request.query.filter_by(business_id=business.id).all()

    return render_template('business_dashboard.html', user=user, business=business, requests=requests)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
