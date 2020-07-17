# all the imports
import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, IntegerField
from functools import wraps


app = Flask(__name__) # create the application instance :)

app.config.from_object(__name__) # load config from this file , flaskr.py


# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'flaskr.db'),
    SECRET_KEY='development key',
    NAME='admin',
    EMAIL='admin@gmail.com',
    USERNAME='admin',
    PASSWORD='default' ))

app.config.from_envvar('FLASKR_SETTINGS', silent=True)

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

#initizle db       
def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')

# Home 
@app.route('/')
def index():
    return render_template('home.html')


# About
@app.route('/about')
def about():
    return render_template('about.html')

# Bloodfacts
@app.route('/bloodfacts')
def bloodfacts():
    return render_template('bloodfacts.html')


# Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    lastname = StringField('LastName', [validators.Length(min=1, max=50)])
    zipcode = StringField('Blood Type', [validators.Length(min=1, max=6)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

    # User Register
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        form = RegisterForm(request.form)
        if request.method == 'POST' and form.validate():
            # Data from from 
            name = form.name.data
            lastname = form.lastname.data
            zipcode = form.zipcode.data
            email = form.email.data
            username = form.username.data
            password = form.password.data
    
            # Create cursor
            cur = get_db()
    
            # Execute query
            cur.execute("INSERT INTO entries(name,lastname,zipcode, email, username, password) VALUES(?,?,?,?,?,?)" , (name,lastname, zipcode, email, username, password))
    
            # Commit to DB
            cur.commit()
    
            # Close connection
            cur.close()
    
            flash('You are now registered and can log in', 'success')
    
            return redirect(url_for('login'))
        return render_template('register.html', form=form)

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']
        
        # Create cursor
        cur = get_db()
       
        # Get user by username
        result = cur.execute("SELECT * FROM entries WHERE username = ?", [username])
    
        if result != None:
            # Get stored hash
            data = result.fetchone()
            print(data)
            if data != None:
                password = data['password']
                print(password)
                # Compare Passwords
                if password_candidate == password:
                    # Passed
                    session['logged_in'] = True
                    session['username'] = username
            
                    flash('You are now logged in', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    error = 'Invalid login'
                    return render_template('login.html', error=error)
                # Close connection
                cur.close()
            else:
                error = 'Username not found'
                return render_template('login.html', error=error)                
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)
    return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap	

# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('index'))	



# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    user = session['username']
    # Create cursor
    cur = get_db()

    # Get 
    result = cur.execute("SELECT * FROM entries WHERE  username = ?", [user])

    users = result.fetchone()
    
    if result != None:
        return render_template('dashboard.html', users=users)
    else:
        msg = 'No Users Found'
        return render_template('dashboard.html', msg=msg)
    # Close connection
    cur.close()
    return render_template('dashboard.html')
   

if __name__ == "__main__":
    app.run(debug=True)