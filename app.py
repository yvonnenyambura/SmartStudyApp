from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, User 

app = Flask (__name__)

app.secret_key = 'your_secret_key_here'

# database 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# routes
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        firstname = request.form.get('first_name')  
        lastname = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # check if passwords match
        if password != confirm_password:
            flash("Passwords do not match!")
            return redirect(url_for('signup'))  

   
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('An account with this email already exists!')
            return redirect(url_for('signup'))

       
        new_user = User(first_name=firstname, last_name=lastname, email=email, password=password)

        # add to database
        db.session.add(new_user)
        db.session.commit()

        # redirect to login
        flash('Account created successfully! Please login.')
        return redirect(url_for('login'))
    
    return render_template('signup.html') 

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
      
        if user and user.password == password: 
            session['user_id'] = user.id  
            flash(f'Welcome back, {user.first_name}!') 
            return redirect(url_for('dashboard'))
        else:
        
            flash('Invalid email or password.') 
            
    return render_template('login.html') 



@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out successfully.')
    return redirect(url_for('login'))
    

if __name__ == '__main__':
    app.run(debug=True)