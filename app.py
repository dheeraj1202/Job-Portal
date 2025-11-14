from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

print("\U0001F4C1 Using database file:", os.path.abspath("job_portal.db"))

app.secret_key = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///job_portal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# -----------------------------
# Models
# -----------------------------

# User Table
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    user_type = db.Column(db.String(20))  # job_seeker / recruiter

# Job Table
class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    company = db.Column(db.String(100))
    location = db.Column(db.String(100))
    description = db.Column(db.Text)

# Application Table
class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'))

# -----------------------------
# Seed Dummy Jobs
# -----------------------------

@app.before_request
def seed_jobs():
    if not Job.query.first():
        jobs = [
            Job(title="Python Developer", company="Tech Corp", location="Hyderabad", description="Build REST APIs and backend services using Flask."),
            Job(title="Frontend Engineer", company="DesignX", location="Bangalore", description="Build beautiful UIs with React and Tailwind CSS."),
            Job(title="Data Analyst", company="DataPro", location="Remote", description="Analyze data trends and create dashboards in Excel/PowerBI."),
        ]
        db.session.add_all(jobs)
        db.session.commit()
        print("\u2705 Dummy jobs added to the database.")

# -----------------------------
# Routes
# -----------------------------

@app.route('/')
def welcome():
    return render_template('homepage.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        user_type = request.form['user_type']

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return redirect(url_for('register'))

        user = User(name=name, email=email, password=password, user_type=user_type)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful!", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email, password=password).first()

        if user:
            session['user_id'] = user.id
            session['user_type'] = user.user_type
            session['user_name'] = user.name

            if user.user_type == 'job_seeker':
                return redirect(url_for('job_details'))
            else:
                return redirect(url_for('post_job'))
        else:
            flash("Invalid email or password", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/job-details')
def job_details():
    if 'user_id' not in session or session['user_type'] != 'job_seeker':
        return redirect(url_for('login'))

    jobs = Job.query.all()
    return render_template('job_details.html', jobs=jobs)

@app.route('/my-applications')
def my_applications():
    if 'user_id' not in session or session['user_type'] != 'job_seeker':
        flash("Please login as a job seeker to view applications.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']
    applications = Application.query.filter_by(user_id=user_id).all()
    applied_jobs = []

    for app_obj in applications:
        job = Job.query.get(app_obj.job_id)
        if job:
            applied_jobs.append(job)

    return render_template('my_applications.html', jobs=applied_jobs)

@app.route('/apply/<int:job_id>', methods=['POST'])
def apply(job_id):
    if 'user_id' not in session or session['user_type'] != 'job_seeker':
        flash("Please login first.", "warning")
        return redirect(url_for('login'))

    existing = Application.query.filter_by(user_id=session['user_id'], job_id=job_id).first()
    if existing:
        flash("You already applied to this job.", "info")
    else:
        new_app = Application(user_id=session['user_id'], job_id=job_id)
        db.session.add(new_app)
        db.session.commit()
        flash("Applied successfully!", "success")

    return redirect(url_for('job_details'))

@app.route('/post_job', methods=['GET', 'POST'])
def post_job():
    if 'user_id' not in session or session['user_type'] != 'recruiter':
        flash("Access denied. Only recruiters can post jobs.", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        company = request.form['company']
        location = request.form['location']
        description = request.form['description']

        job = Job(title=title, company=company, location=location, description=description)
        db.session.add(job)
        db.session.commit()

        flash("Job posted successfully!", "success")
        return redirect(url_for('post_job'))

    return render_template('post_job.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully", "info")
    return redirect(url_for('welcome'))

# -----------------------------
# Run the App
# -----------------------------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)