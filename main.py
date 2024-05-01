from flask import Flask, render_template, request, redirect, url_for, flash, send_file, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os
import base64

# Create a Flask application
app = Flask(__name__)

app = Flask(__name__, static_url_path='/static')
# Set the secret key for the application"
app.secret_key = 'its_secret_key'

# Set the upload folder configuration
app.config['UPLOAD_FOLDER'] = 'uploads'

# Configure the database connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@127.0.0.1:3308/dbms'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the SQLAlchemy object for database operations
db = SQLAlchemy(app)

# Initialize Flask-Login for user authentication
login_manager = LoginManager(app)

# Define the User model for authentication
class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))

# Define the Event model for storing event information
class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    file_data = db.Column(db.LargeBinary)  # Storing file data as binary
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('Users', backref=db.backref('events', lazy=True))

class Club(db.Model):
    __tablename__ = 'clubs'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    logo_data = db.Column(db.LargeBinary)  # Store logo data as binary
    about = db.Column(db.Text)  # Added for club information

# Define the user_loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Get form data
        username = request.form['username']
        password = request.form['password']
        
        # Check if username already exists
        existing_user = Users.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'error')
            return redirect(url_for('signup'))  # Redirect back to signup page
        
        # Create a new user object
        new_user = Users(username=username, password=password)
        
        # Add the new user to the database
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))  # Redirect to login page
    
    return render_template('signup.html')


# Route to display the delete club form
@app.route('/delete_club', methods=['GET', 'POST'])
@login_required
def delete_club():
    if request.method == 'POST':
        # Retrieve form data
        username = request.form.get('username')
        password = request.form.get('password')
        club_name = request.form.get('club_name')
        
        # Check if username and password are correct
        if username == 'head' and password == '1234':
            # Query the club by name
            club = Club.query.filter_by(name=club_name).first()
            if club:
                try:
                    # Delete the club from the database
                    db.session.delete(club)
                    db.session.commit()  # Persist the deletion
                    flash('Club deleted successfully!', 'success')
                except Exception as e:
                    # Handle any exceptions that might occur during the deletion
                    flash(f'Error deleting club: {str(e)}', 'error')
            else:
                flash('Club not found!', 'error')
        else:
            flash('Invalid username or password!', 'error')

        return redirect(url_for('clubs'))  # Redirect to clubs page regardless of deletion success or failure

    # Render the delete club form for GET requests
    return render_template('delete_club.html')

@app.route('/events')
@login_required
def events():
    # Fetch events from the database
    events = Event.query.order_by(Event.id.desc()).all()
    return render_template('events.html', events=events)

# Define the route for the clubs page
@app.route('/clubs')
@login_required
def clubs():
    clubs = Club.query.all()
    for club in clubs:
        if club.logo_data:
            club.logo_data = base64.b64encode(club.logo_data).decode('utf-8')  # Convert binary to base64 string
    return render_template('clubs.html', clubs=clubs)

@app.route('/add_club', methods=['GET', 'POST'])
@login_required
def add_club():
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        description = request.form['description']
        logo_data = request.files['logo'].read() if 'logo' in request.files else None
        
        # Create a new Club object with the form data
        new_club = Club(name=name, description=description, logo_data=logo_data)
        
        # Add the new club to the database
        db.session.add(new_club)
        db.session.commit()
        
        flash('Club added successfully!', 'success')
        return redirect(url_for('clubs'))
    
    return render_template('add_club.html')


@app.route('/club/<int:club_id>')
@login_required
def club_detail(club_id):
    club = Club.query.get_or_404(club_id)
    return render_template('club_detail.html', club=club)

@app.route('/edit_club/<int:club_id>', methods=['GET', 'POST'])
@login_required
def edit_club(club_id):
    club = Club.query.get_or_404(club_id)
    
    # Check if username and password are correct
    if request.method == 'POST' and request.form['username'] == 'club' and request.form['password'] == '1234':
        # Update club details
        club.name = request.form['name']
        club.description = request.form['description']
        club.about = request.form['about']
        db.session.commit()
        flash('Club updated successfully!', 'success')
        return redirect(url_for('club_detail', club_id=club.id))
    elif request.method == 'POST':
        flash('Invalid username or password!', 'error')
    
    return render_template('edit_club.html', club=club)

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('events'))
    return redirect(url_for('login'))

@app.route('/post_event', methods=['GET', 'POST'])
@login_required
def post_event():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'username' and password == '1234':
            event_title = request.form['event_title']
            event_description = request.form['event_description']
            file = request.files['event_file']
            
            if file:
                file_data = file.read()  # Read file data as binary
            else:
                file_data = None
            
            new_event = Event(title=event_title, description=event_description, file_data=file_data, user_id=current_user.id)
            db.session.add(new_event)
            db.session.commit()
            
            flash('Event posted successfully!', 'success')
            return redirect(url_for('events'))
        else:
            abort(403)  # Forbidden access if credentials are incorrect

    return render_template('post_event.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Users.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password!', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/download_file/<int:event_id>')
@login_required
def download_file(event_id):
    event = Event.query.get_or_404(event_id)
    file_data = event.file_data

    # Check if file_data exists
    if file_data:
        # Generate file path
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f'event_{event_id}.pdf')

        # Save file data to file
        with open(file_path, 'wb') as file:
            file.write(file_data)

        # Send file for download
        return send_file(file_path, as_attachment=True)
    else:
        flash('File not found!', 'error')
        return redirect(url_for('events'))

# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)











































