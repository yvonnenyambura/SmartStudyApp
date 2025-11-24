from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, User, Subject, Topic, Subtopic
from datetime import datetime, date

app = Flask(__name__)

app.secret_key = 'smartstudy_app_secret_key_2025_very_secure_123'

# database 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

def get_user_id():
    """Retrieves the current logged-in user's ID from the session."""
    return session.get('user_id')


def update_topic_progress(topic_id):
    """Calculates and updates Topic progress based on its Subtopics."""
    topic = db.session.get(Topic, topic_id)  
    if not topic:
        return

    topic.total_subtopics = topic.subtopics.count()
    topic.completed_subtopics = topic.subtopics.filter_by(is_completed=True).count()
    
    topic.is_completed = (topic.total_subtopics > 0 and topic.completed_subtopics == topic.total_subtopics)
    
    db.session.commit()
    update_subject_progress(topic.subject_id)


def update_subject_progress(subject_id):
    """Calculates and updates Subject progress based on its Topics."""
    subject = db.session.get(Subject, subject_id) 
    if not subject:
        return

    subject.total_topics = subject.topics.count()
    subject.completed_topics = subject.topics.filter_by(is_completed=True).count()
    
    db.session.commit()


@app.route('/dashboard')
def dashboard():
    user_id = get_user_id()
    if not user_id:
        flash('Please log in to view the dashboard.')
        return redirect(url_for('login'))
    
    user = db.session.get(User, user_id)  
    
    # Fetch user's subjects
    subjects = Subject.query.filter_by(user_id=user_id).order_by(Subject.priority.desc(), Subject.deadline.asc()).all()
    
    total_subjects = len(subjects)
    total_topics = sum(subject.total_topics for subject in subjects)
    completed_topics = sum(subject.completed_topics for subject in subjects)
    completion_percentage = int((completed_topics / total_topics * 100) if total_topics > 0 else 0)

    study_streak = 0 

    # AI recommendation 
    next_topic = None
    for subject in subjects:
        for topic in subject.topics:
            if not topic.is_completed:
                next_topic = topic
                break
        if next_topic:
            break
    if next_topic:
        ai_recommendation = {'topic': next_topic.name, 'reason': 'Deadline approaching / Low completion rate'}
    else:
        ai_recommendation = {'topic': 'N/A', 'reason': 'All topics completed!'}

    # Chart data
    completed_count = completed_topics
    pending_count = total_topics - completed_topics

    return render_template(
        'dashboard.html',
        user=user,
        subjects=subjects,
        total_subjects=total_subjects,
        total_topics=total_topics,
        topics_completed=completed_topics,
        completion_percentage=completion_percentage,
        study_streak=study_streak,
        ai_recommendation=ai_recommendation,
        chart_data={'completed': completed_count, 'pending': pending_count}
    )


@app.route('/')
def home():
    if get_user_id():
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

    
        db.session.add(new_user)
        db.session.commit()

     
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
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.') 
            
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out successfully.')
    return redirect(url_for('login'))
    
@app.route('/subjects', defaults={'subject_id': None}, methods=['GET', 'POST'])
@app.route('/subjects/<int:subject_id>', methods=['GET', 'POST'])
def subjects(subject_id):
    user_id = get_user_id()
    if not user_id:
        flash('Please log in to manage subjects.')
        return redirect(url_for('login'))

    user_subjects = Subject.query.filter_by(user_id=user_id).order_by(Subject.priority.desc(), Subject.deadline.asc()).all()
    selected_subject = None
    
   
    if request.method == 'POST':
        
        action = request.form.get('action')

        if action == 'add_subject':
            subject_name = request.form.get('subject_name')
            deadline_str = request.form.get('deadline')
            priority = request.form.get('priority')
            
            try:
                deadline_date = datetime.strptime(deadline_str, '%Y-%m-%d').date() if deadline_str else None
            except ValueError:
                flash("Invalid deadline format.", 'error')
                return redirect(url_for('subjects'))

            if not subject_name:
                flash("Subject name is required.", 'error')
                return redirect(url_for('subjects'))

            new_subject = Subject(
                name=subject_name,
                deadline=deadline_date,
                priority=priority,
                user_id=user_id
            )
            db.session.add(new_subject)
            db.session.commit()
            flash(f'Subject "{subject_name}" added successfully!')
           
            return redirect(url_for('subjects', subject_id=new_subject.id))


        elif action == 'add_topic':
            topic_name = request.form.get('topic_name')
            difficulty = request.form.get('difficulty')
            parent_subject_id = request.form.get('subject_id')
            
            if not topic_name or not parent_subject_id:
                flash("Topic name and subject ID are required.", 'error')
                return redirect(url_for('subjects', subject_id=parent_subject_id))

            new_topic = Topic(
                name=topic_name,
                difficulty=difficulty,
                subject_id=parent_subject_id
            )
            db.session.add(new_topic)
            db.session.commit()
            flash(f'Topic "{topic_name}" added.')
            update_subject_progress(parent_subject_id)
            return redirect(url_for('subjects', subject_id=parent_subject_id))

        elif action == 'add_subtopic':
            subtopic_name = request.form.get('subtopic_name')
            parent_topic_id = request.form.get('topic_id')
            
            if not subtopic_name or not parent_topic_id:
                flash("Subtopic name and Topic ID are required.", 'error')
                return redirect(url_for('subjects', subject_id=subject_id))
            
            topic = db.session.get(Topic, parent_topic_id)  
            if not topic or topic.subject.user_id != user_id:
                 flash("Invalid Topic or access denied.", 'error')
                 return redirect(url_for('subjects', subject_id=subject_id))


            new_subtopic = Subtopic(
                name=subtopic_name,
                topic_id=parent_topic_id
            )
            db.session.add(new_subtopic)
            db.session.commit()
            flash(f'Subtopic "{subtopic_name}" added.')
            update_topic_progress(parent_topic_id) 
            return redirect(url_for('subjects', subject_id=topic.subject.id)) 

       
        elif action == 'delete_subject':
            subject_id_to_delete = request.form.get('subject_id')
            
            if not subject_id_to_delete:
                flash("Deletion failed: Missing subject ID.", 'error')
                return redirect(url_for('subjects'))
                
            try:
                
                subject = Subject.query.filter_by(id=subject_id_to_delete, user_id=user_id).first()
                
                if subject:
                    subject_name = subject.name
                    
               
                    db.session.delete(subject)
                    
            
                    db.session.commit()
                    flash(f"Subject '{subject_name}' and all its content deleted successfully.", 'success')
                    
                else:
                    flash("Error: Subject not found or unauthorized for deletion.", 'error')

            except Exception as e:
            
                db.session.rollback()
                
              
                print(f"--- DATABASE DELETION ERROR ---")
                print(f"Error deleting subject {subject_id_to_delete}: {e}")
                print(f"-------------------------------")

            return redirect(url_for('subjects'))
     


    if subject_id:
        selected_subject = Subject.query.filter_by(id=subject_id, user_id=user_id).first()
        if not selected_subject:
            flash("Subject not found or access denied.", 'error')
            return redirect(url_for('subjects'))
        
       
        update_subject_progress(subject_id)

    
    if not selected_subject and user_subjects:
        return redirect(url_for('subjects', subject_id=user_subjects[0].id))

    return render_template(
        'subjects.html', 
        subjects=user_subjects, 
        selected_subject=selected_subject,
        Topic=Topic 
    )

@app.route('/toggle_subtopic/<int:subtopic_id>', methods=['POST'])
def toggle_subtopic(subtopic_id):
    user_id = get_user_id()
    if not user_id:
        return redirect(url_for('login'))

    subtopic = db.session.get(Subtopic, subtopic_id)  
    
  
    if not subtopic or subtopic.topic.subject.user_id != user_id:
        flash("Subtopic not found or access denied.", 'error')
        return redirect(url_for('dashboard'))

  
    subtopic.is_completed = not subtopic.is_completed
    subtopic.date_completed = datetime.now() if subtopic.is_completed else None
    
    db.session.commit()
    
   
    update_topic_progress(subtopic.topic_id)
    
    flash(f'Subtopic "{subtopic.name}" marked {"Completed" if subtopic.is_completed else "Pending"}.')
    return redirect(url_for('subjects', subject_id=subtopic.topic.subject_id))

@app.route('/reports')
def reports():
    user_id = get_user_id()
    if not user_id:
        flash("Please log in to view Reports.", "error")
        return redirect(url_for('login'))

    # Fetch subjects and topics 
    subjects = Subject.query.filter_by(user_id=user_id).all()
    subject_progress = []
    recent_subtopics = Subtopic.query.join(Topic).join(Subject)\
                        .filter(Subject.user_id==user_id)\
                        .order_by(Subtopic.date_completed.desc())\
                        .limit(5).all()

    for subject in subjects:
        total_topics = subject.topics.count()
        completed_topics = subject.topics.filter_by(is_completed=True).count()
        progress = int((completed_topics / total_topics) * 100) if total_topics > 0 else 0
        subject_progress.append({'name': subject.name, 'progress': progress})

    return render_template(
        'reports.html',
        subjects=subjects,
        subject_progress=subject_progress,
        recent_subtopics=recent_subtopics
    )

if __name__ == '__main__':
    app.run(debug=True)