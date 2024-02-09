import traceback

from flask import render_template, request, redirect, url_for, flash, session, make_response, jsonify
from sqlalchemy import func
from sqlalchemy.orm import aliased


from app.models import User, Survey, QuestionGroup, Question, QuestionType, QuestionOption, \
    Participant, Answer, SelectedOption, RatingScale, ConditionalLink

import logging
import pytz
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

from app import app, db

app.secret_key = "your-secret-key"
logging.basicConfig(filename='app.log', level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Enable SQLAlchemy query logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Configure logging
logging.basicConfig(filename='app.log', level=logging.DEBUG)

# Example: Log the value of a variable
question_text = "Sample question text"
logging.debug(f"Question Text: {question_text}")

# Create a logger for your Flask app
logger = logging.getLogger(__name__)

question_type_mapping = {
    'open-ended': 1,
    'multiple-choice': 2,
    'rating-scale': 3
}



@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the entered username and password match the admin credentials
        if username == 'admin' and password == 'admin':
            # Set a session variable to indicate that the user is logged in as an admin
            session['is_admin'] = True

            # You can also set the 'user_id' in the session if needed
            # In this example, we're setting it to 1 as an example
            session['user_id'] = 1  # Set the user_id to the admin's ID

            flash('Logged in as an admin!', 'success')
            return redirect(url_for('admin_dashboard'))

        # Handle incorrect login credentials
        flash('Invalid login credentials. Please try again.', 'danger')

    return render_template('index.html')  # Create a login form on the index page


@app.route('/admin_dashboard')
def admin_dashboard():
    # Check if the user is logged in as an admin
    if session.get('is_admin'):
        # Display the admin dashboard
        return render_template('admin_dashboard.html')

    # If not logged in as an admin, redirect to the login page
    flash('Access denied. Please log in as an admin.', 'danger')
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    # Clear the session and log the user out
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# # Route to display users (only accessible by Admin)
# @app.route('/users_list', methods=['GET'])
# def users_list():
#     admin = User.query.filter_by(username='admin').first()  # Assuming 'admin' is the username of the Admin
#     if admin and admin.role == ROLES.Admin:
#         users = User.query.filter(User.username != 'admin').all()  # Exclude the Admin user
#         return render_template('users_list.html', users=users)
#     else:
#         flash('Access denied. You must be logged in as an Admin.')
#         return redirect(url_for('index'))
#
#
# # Route to add a new user (only accessible by Admin)
# @app.route('/add_user', methods=['GET', 'POST'])
# def add_user():
#     admin = User.query.filter_by(username='admin').first()
#     if admin and admin.role == ROLES.Admin:
#         if request.method == 'POST':
#             # Get user data from the form
#             username = request.form.get('username')
#             password = request.form.get('password')
#             email = request.form.get('email')
#             role = request.form.get('role')
#
#             # Create a new user
#             new_user = User(username=username, password=password, email=email, role=role)
#             db.session.add(new_user)
#             db.session.commit()
#             flash('User added successfully.')
#             return redirect(url_for('view_users'))
#
#         return render_template('add_user.html')
#     else:
#         flash('Access denied. You must be logged in as an Admin.')
#         return redirect(url_for('index'))


@app.route('/enter_survey', methods=['POST'])
def enter_survey():
    survey_url = request.form['url']
    code = request.form['code']

    return redirect(url_for('index'))


# Read All Question Types
@app.route('/question_types', methods=['GET'])
def question_type_list():
    question_types = QuestionType.query.all()
    return render_template('question_type/question_type_list.html', question_types=question_types)


# Handle the lock/unlock action for question types
@app.route('/question_types/<int:id>/toggle_lock', methods=['POST'])
def toggle_question_type_lock(id):
    question_type = QuestionType.query.get_or_404(id)
    question_type.is_locked = not question_type.is_locked
    db.session.commit()
    return jsonify(isLocked=question_type.is_locked)


# View a specific question type
@app.route('/question_types/<int:id>', methods=['GET'])
def question_type_view(id):
    question_type = QuestionType.query.get_or_404(id)
    # Pass the is_locked status to the template
    return render_template('question_type/question_type_view.html', question_type=question_type, is_locked=question_type.is_locked)



# Create a New Question Type
@app.route('/question_types/create', methods=['GET', 'POST'])
def question_type_create():
    if request.method == 'POST':
        type_name = request.form['type_name']
        new_question_type = QuestionType(type_name=type_name)
        db.session.add(new_question_type)
        db.session.commit()
        return redirect(url_for('question_type_list'))
    return render_template('question_type/question_type_create.html')


# Update Question Type
@app.route('/question_types/<int:id>/update', methods=['GET', 'POST'])
def question_type_update(id):
    question_type = QuestionType.query.get(id)
    if request.method == 'POST':
        question_type.type_name = request.form['type_name']
        db.session.commit()
        return redirect(url_for('question_type_list'))
    return render_template('question_type/question_type_update.html', question_type=question_type)


# Delete Question Type
@app.route('/question_types/<int:id>/delete', methods=['POST'])
def question_type_delete(id):
    question_type = QuestionType.query.get(id)
    db.session.delete(question_type)
    db.session.commit()
    return redirect(url_for('question_type_list'))


# Route for displaying the survey list
@app.route('/survey_list')
def survey_list():
    sort_by = request.args.get('sort_by', 'created_at_desc')
    if sort_by == 'title_asc':
        surveys = Survey.query.order_by(Survey.survey_title.asc()).all()
    elif sort_by == 'title_desc':
        surveys = Survey.query.order_by(Survey.survey_title.desc()).all()
    elif sort_by == 'created_at_asc':
        surveys = Survey.query.order_by(Survey.created_at.asc()).all()
    elif sort_by == 'created_at_desc':
        surveys = Survey.query.order_by(Survey.created_at.desc()).all()
    elif sort_by == 'updated_at_asc':
        surveys = Survey.query.order_by(Survey.updated_at.asc()).all()
    elif sort_by == 'updated_at_desc':
        surveys = Survey.query.order_by(Survey.updated_at.desc()).all()
    else:
        surveys = Survey.query.all()  # Default case

    # Time zone conversion
    tz = pytz.timezone('Europe/Amsterdam')
    for survey in surveys:
        survey.created_at = survey.created_at.replace(tzinfo=pytz.utc).astimezone(tz)
        survey.updated_at = survey.updated_at.replace(tzinfo=pytz.utc).astimezone(tz)

    return render_template('survey/survey_list.html', surveys=surveys)


# Route for viewing a specific survey
@app.route('/surveys/<int:survey_id>/view', methods=['GET'])
def survey_view(survey_id):
    try:
        app.logger.info(f"Fetching survey with ID {survey_id}")
        survey = Survey.query.get_or_404(survey_id)
        tz = pytz.timezone('Europe/Amsterdam')

        question_groups = QuestionGroup.query.filter_by(survey_id=survey.id).all()
        question_data = {}
        conditional_question_ids = set()

        for group in question_groups:
            questions = Question.query.filter_by(group_id=group.id).all()
            group_data = []
            for question in questions:
                if question.id in conditional_question_ids:
                    continue

                question_dict = {
                    'question': question,
                    'options': [],
                    'rating_scale': None
                }

                if question.question_type_id == 2:  # Multiple-choice
                    options = QuestionOption.query.filter_by(question_id=question.id).all()
                    for option in options:
                        option_dict = {
                            'option': option,
                            'conditional_questions': []
                        }

                        conditional_links = ConditionalLink.query.filter_by(parent_option_id=option.id).all()
                        for link in conditional_links:
                            cond_question = Question.query.get(link.child_question_id)
                            if cond_question:
                                option_dict['conditional_questions'].append(cond_question)
                                conditional_question_ids.add(cond_question.id)
                        question_dict['options'].append(option_dict)

                elif question.question_type_id == 3:  # Rating scale
                    rating_scale = RatingScale.query.filter_by(question_id=question.id).first()
                    question_dict['rating_scale'] = rating_scale

                group_data.append(question_dict)

            question_data[group] = group_data

        # Determine sort order
        sort_by = request.args.get('sort_by', 'date_taken_desc')
        order_by = func.max(Answer.created_at).desc() if sort_by == 'date_taken_desc' else func.max(Answer.created_at).asc()

        survey_submissions = db.session.query(
            Participant.id,
            func.max(Answer.created_at).label('submission_time')
        ).join(Answer, Answer.participant_id == Participant.id) \
            .filter(Participant.survey_id == survey_id) \
            .group_by(Participant.id) \
            .order_by(order_by) \
            .all()

        # Convert submission times to Amsterdam time zone
        survey_submissions_converted = [
            (participant_id, submission_time.replace(tzinfo=pytz.utc).astimezone(tz))
            for participant_id, submission_time in survey_submissions
        ]

    except Exception as e:
        logging.error(f"An error occurred while fetching the survey details: {str(e)}")
        flash('An error occurred while fetching the survey details.', 'danger')
        return redirect(url_for('survey_list'))

    return render_template('survey/survey_view.html', survey=survey, question_groups=question_groups,
                           question_data=question_data, survey_submissions=survey_submissions_converted)


# Route for deleting a specific survey
@app.route('/survey/<int:survey_id>/delete', methods=['GET', 'POST'])
def survey_delete(survey_id):
    try:
        # Retrieve the survey from the database based on survey_id
        survey = Survey.query.get(survey_id)

        if not survey:
            # Handle the case where the survey does not exist
            flash('Survey not found.', 'danger')
            return redirect(url_for('survey_list'))  # Redirect to a list of surveys or another appropriate page

        # Check if the request method is POST (confirmation for deletion)
        if request.method == 'POST':
            # Delete the survey
            db.session.delete(survey)
            db.session.commit()

            flash('Survey deleted successfully.', 'success')

        return redirect(url_for('survey_list'))

    except Exception as e:
        # Print the error for debugging purposes
        print(f"An error occurred while deleting the survey (survey_id={survey_id}): {str(e)}")
        flash('An error occurred while deleting the survey.', 'danger')
        return redirect(url_for('survey_list'))  # Redirect to a list of surveys or another appropriate page


@app.route('/duplicate_survey/<int:survey_id>', methods=['GET'])
def duplicate_survey(survey_id):
    try:
        # Retrieve the original survey
        original_survey = Survey.query.get_or_404(survey_id)

        # Create a new survey instance with the same general information
        duplicated_survey = Survey(
            survey_title=original_survey.survey_title + " (Copy)",
            survey_description=original_survey.survey_description,
            welcome_message=original_survey.welcome_message,
            exit_message=original_survey.exit_message,
            created_by_id=session.get('user_id')
        )
        db.session.add(duplicated_survey)
        db.session.flush()

        # Duplicate question groups and their questions
        for group in original_survey.question_groups:
            new_group = QuestionGroup(
                group_name=group.group_name,
                group_description=group.group_description,
                survey_id=duplicated_survey.id
            )
            db.session.add(new_group)
            db.session.flush()

            # Duplicate questions
            for question in group.questions:
                new_question = Question(
                    question_text=question.question_text,
                    question_type_id=question.question_type_id,
                    group_id=new_group.id
                )
                db.session.add(new_question)
                db.session.flush()

                # Duplicate options for multiple-choice questions
                if question.question_type_id == question_type_mapping['multiple-choice']:
                    for option in question.question_options:
                        new_option = QuestionOption(
                            option_text=option.option_text,
                            question_id=new_question.id
                        )
                        db.session.add(new_option)

                # Duplicate rating scale parameters
                elif question.question_type_id == question_type_mapping['rating-scale']:
                    rating_scale = question.rating_scale
                    new_rating_scale = RatingScale(
                        min_value=rating_scale.min_value,
                        max_value=rating_scale.max_value,
                        step=rating_scale.step,
                        question_id=new_question.id
                    )
                    db.session.add(new_rating_scale)

        db.session.commit()
        flash('Survey duplicated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error duplicating survey: {str(e)}")
        flash('Failed to duplicate the survey.', 'danger')

    return redirect(url_for('survey_list'))


# Routes for Update a survey
@app.route('/update_survey/<int:survey_id>', methods=['GET', 'POST'])
def update_survey(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    if request.method == 'POST':
        try:
            survey.survey_title = request.form['survey_title']
            survey.survey_description = request.form['survey_description']
            survey.welcome_message = request.form['welcome_message']
            survey.exit_message = request.form['exit_message']

            update_question_groups(survey, request.form)
            db.session.commit()
            flash('Survey updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
            app.logger.error(f"Error updating survey: {e}\n{traceback.format_exc()}")

        return redirect(url_for('survey_list'))  # Assuming 'survey_list' is the correct route name
    else:
        # GET: Display the survey update form with existing data
        return render_template('survey/survey_update.html', survey=survey)


def update_question_groups(survey, form):
    # Track IDs of groups to retain
    existing_group_ids = {group.id for group in survey.question_groups}
    processed_group_ids = set()

    # Determine group indices from the form keys
    group_indices = {key.split('_')[1] for key in form.keys() if key.startswith('group_') and '_name' in key}
    for group_index in group_indices:
        group_id = form.get(f'group_{group_index}_id')
        group_name = form.get(f'group_{group_index}_name')
        group_description = form.get(f'group_{group_index}_description')

        if group_id.isdigit():
            # Update existing group
            group = QuestionGroup.query.get(int(group_id))
        else:
            # Create new group
            group = QuestionGroup(survey=survey)
            db.session.add(group)

        group.group_name = group_name
        group.group_description = group_description
        processed_group_ids.add(group.id)

        # Update questions within the group
        update_questions(group, form, group_index)

    # Remove groups that were not in the submitted form
    for group_id in existing_group_ids - processed_group_ids:
        QuestionGroup.query.filter_by(id=group_id).delete()



def update_questions(group, form, group_index):
    existing_question_ids = [question.id for question in group.questions.all()]
    processed_question_ids = []

    # Iterate over form data to find questions for this group
    for key, value in form.items():
        if key.startswith(f'group_{group_index}_question_') and key.endswith('_text'):
            question_index = key.split('_')[3]
            question_id_key = f'group_{group_index}_question_{question_index}_id'
            question_id = form.get(question_id_key, 'new')
            question_text = value
            question_type_key = f'group_{group_index}_question_{question_index}_type'
            question_type = question_type_mapping[form.get(question_type_key)]

            # Check if it's an existing question or a new one
            if question_id.isdigit():
                # Existing question
                question = Question.query.get(int(question_id))
            else:
                # New question
                question = Question(group_id=group.id)
                db.session.add(question)

            # Update question properties
            question.question_text = question_text
            question.question_type_id = question_type
            processed_question_ids.append(question.id)

            # Handle specific question types
            if question_type == question_type_mapping['multiple-choice']:
                update_options(question, form, group_index, question_index)
            elif question_type == question_type_mapping['rating-scale']:
                update_rating_scale(question, form, group_index, question_index)

    # Delete questions that were removed
    for question_id in set(existing_question_ids) - set(processed_question_ids):
        Question.query.filter_by(id=question_id).delete()

    db.session.commit()  # Commit at the end to make all changes permanent

def update_options(question, form, group_index, question_index):
    existing_option_ids = [option.id for option in question.question_options]
    processed_option_ids = []

    # Iterate over form data to find options for the given question
    for key in form.keys():
        if key.startswith(f'group_{group_index}_question_{question_index}_option_') and not key.endswith('_id'):
            option_index = key.split('_')[-1]
            option_text = form[key]
            option_id_key = f'group_{group_index}_question_{question_index}_option_{option_index}_id'
            option_id = form.get(option_id_key, 'new')

            if option_id.isdigit():
                # Existing option
                option = QuestionOption.query.get(int(option_id))
            else:
                # New option
                option = QuestionOption(question_id=question.id)
                db.session.add(option)

            option.option_text = option_text
            processed_option_ids.append(option.id)

    # Delete options that were removed
    for option_id in set(existing_option_ids) - set(processed_option_ids):
        QuestionOption.query.filter_by(id=option_id).delete()

    db.session.commit()  # Ensure to commit changes


def update_rating_scale(question, form, group_index, question_index):
    # Assuming there's at most one rating scale per question
    rating_scale = question.rating_scale or RatingScale(question_id=question.id)

    min_value_key = f'group_{group_index}_question_{question_index}_min_value'
    max_value_key = f'group_{group_index}_question_{question_index}_max_value'
    step_key = f'group_{group_index}_question_{question_index}_step'

    rating_scale.min_value = int(form.get(min_value_key, 1))  # Default to 1 if not provided
    rating_scale.max_value = int(form.get(max_value_key, 5))  # Default to 5 if not provided
    rating_scale.step = int(form.get(step_key, 1))  # Default to 1 if not provided

    db.session.add(rating_scale)  # Add or update the rating scale
    db.session.commit()  # Ensure to commit changes


# Route to create a new survey
@app.route('/create_survey', methods=['GET', 'POST'])
def create_survey():
    if not session.get('is_admin'):
        flash('Access denied. Please log in as an admin.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            survey_data = extract_survey_data(request.form)
            if survey_data:
                create_survey_in_database(survey_data)
                flash('Survey created successfully!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Failed to create the survey. Please fill in all required fields.', 'danger')
        except Exception as e:
            flash('Failed to create the survey. Please try again later.', 'danger')
            app.logger.error(f"Error creating survey: {str(e)}")

    return render_template("survey/survey_create.html")


def extract_survey_data(form_data):
    survey_title = form_data.get('survey_title')
    survey_description = form_data.get('survey_description')
    welcome_message = form_data.get('welcome_message')
    exit_message = form_data.get('exit_message')

    if not all([survey_title, survey_description, welcome_message, exit_message]):
        app.logger.warning("Survey creation failed - Missing basic survey details")
        return None

    question_groups = []
    group_count = 1

    while form_data.get(f'group_{group_count}_title'):
        group_name = form_data.get(f'group_{group_count}_title')
        group_description = form_data.get(f'group_{group_count}_description')

        questions = extract_questions(form_data, group_count)
        question_group = {
            'group_name': group_name,
            'group_description': group_description,
            'questions': questions
        }

        question_groups.append(question_group)
        group_count += 1

    return {
        'survey_title': survey_title,
        'survey_description': survey_description,
        'welcome_message': welcome_message,
        'exit_message': exit_message,
        'question_groups': question_groups
    }


def extract_questions(form_data, group_index):
    questions = []
    question_count = 1

    while True:
        question_text = form_data.get(f'group_{group_index}_question_{question_count}_text')
        question_type = form_data.get(f'group_{group_index}_question_{question_count}_type')

        if question_text is None:
            break

        question = {
            'question_text': question_text,
            'question_type': question_type
        }

        if question_type == 'multiple-choice':
            options, conditionals = extract_options(form_data, group_index, question_count)
            question['options'] = options
            question['conditionals'] = conditionals

        elif question_type == 'rating-scale':
            min_value = form_data.get(f'group_{group_index}_question_{question_count}_min_value')
            max_value = form_data.get(f'group_{group_index}_question_{question_count}_max_value')
            step = form_data.get(f'group_{group_index}_question_{question_count}_step')

            question['min_value'] = int(min_value) if min_value else None
            question['max_value'] = int(max_value) if max_value else None
            question['step'] = int(step) if step else None

        questions.append(question)
        question_count += 1

    return questions


def extract_options(form_data, group_index, question_index):
    options = []
    conditionals = {}
    option_count = 1

    while True:
        option_text = form_data.get(f'group_{group_index}_question_{question_index}_option_{option_count}')
        if option_text is None:
            break

        conditional_question_text = form_data.get(f'group_{group_index}_question_{question_index}_option_{option_count}_conditional_text')
        conditional_question_type = form_data.get(f'group_{group_index}_question_{question_index}_option_{option_count}_conditional_type')

        # Extract conditional question details
        conditional_details = {}
        if conditional_question_text and conditional_question_type:
            conditional_details['text'] = conditional_question_text
            conditional_details['type'] = conditional_question_type

            if conditional_question_type == 'multiple-choice':
                conditional_options = []
                conditional_option_count = 1
                while True:
                    conditional_option_text = form_data.get(
                        f'group_{group_index}_question_{question_index}_option_{option_count}_conditional_option_{conditional_option_count}')
                    if conditional_option_text is None:
                        break
                    conditional_options.append(conditional_option_text)
                    conditional_option_count += 1
                conditional_details['options'] = conditional_options

            elif conditional_question_type == 'rating-scale':
                min_value = form_data.get(f'group_{group_index}_question_{question_index}_option_{option_count}_conditional_min_value')
                max_value = form_data.get(f'group_{group_index}_question_{question_index}_option_{option_count}_conditional_max_value')
                step = form_data.get(f'group_{group_index}_question_{question_index}_option_{option_count}_conditional_step')

                conditional_details['min_value'] = int(min_value) if min_value else None
                conditional_details['max_value'] = int(max_value) if max_value else None
                conditional_details['step'] = int(step) if step else None

            conditionals[option_count] = conditional_details

        options.append(option_text)
        option_count += 1

    return options, conditionals


def create_survey_in_database(survey_data):
    try:
        db.session.begin()

        survey = Survey(
            survey_title=survey_data['survey_title'],
            survey_description=survey_data['survey_description'],
            welcome_message=survey_data['welcome_message'],
            exit_message=survey_data['exit_message'],
            created_by_id=session['user_id']
        )
        db.session.add(survey)
        db.session.flush()
        app.logger.info(f"Survey '{survey.survey_title}' created with ID {survey.id}")

        for group_data in survey_data['question_groups']:
            question_group = QuestionGroup(
                group_name=group_data['group_name'],
                group_description=group_data['group_description'],
                survey_id=survey.id
            )
            db.session.add(question_group)
            db.session.flush()
            app.logger.info(f"Question Group '{question_group.group_name}' created with ID {question_group.id}")

            for question_data in group_data['questions']:
                question = Question(
                    question_text=question_data['question_text'],
                    question_type_id=1 if question_data['question_type'] == 'open-ended' else 2 if question_data['question_type'] == 'multiple-choice' else 3,  # Update according to your IDs
                    group_id=question_group.id
                )
                db.session.add(question)
                db.session.flush()
                app.logger.info(f"Question '{question.question_text}' created with ID {question.id}")

                if question_data['question_type'] == 'multiple-choice':
                    for idx, option_text in enumerate(question_data['options'], start=1):
                        option = QuestionOption(
                            option_text=option_text,
                            question_id=question.id
                        )
                        db.session.add(option)
                        db.session.flush()
                        app.logger.info(f"Option '{option.option_text}' created for Question ID {question.id}")

                        # Handle conditional questions
                        if idx in question_data['conditionals']:
                            conditional_data = question_data['conditionals'][idx]
                            conditional_question = Question(
                                question_text=conditional_data['text'],
                                question_type_id=1 if conditional_data['type'] == 'open-ended' else 2 if
                                conditional_data['type'] == 'multiple-choice' else 3,
                                group_id=question_group.id
                            )
                            db.session.add(conditional_question)
                            db.session.flush()
                            app.logger.info(f"Conditional Question '{conditional_question.question_text}' created with ID {conditional_question.id}")

                            for cond_option_text in conditional_data.get('options', []):
                                cond_option = QuestionOption(
                                    option_text=cond_option_text,
                                    question_id=conditional_question.id
                                )
                                db.session.add(cond_option)
                                # No need to flush here as these are just options

                            # Handle rating scale for conditional questions
                            if conditional_data['type'] == 'rating-scale':
                                rating_scale = RatingScale(
                                    min_value=conditional_data['min_value'],
                                    max_value=conditional_data['max_value'],
                                    step=conditional_data['step'],
                                    question_id=conditional_question.id
                                )
                                db.session.add(rating_scale)

                            conditional_link = ConditionalLink(
                                parent_option_id=option.id,
                                child_question_id=conditional_question.id
                            )
                            db.session.add(conditional_link)

                elif question_data['question_type'] == 'rating-scale':
                    rating_scale = RatingScale(
                        min_value=question_data['min_value'],
                        max_value=question_data['max_value'],
                        step=question_data['step'],
                        question_id=question.id
                    )
                    db.session.add(rating_scale)
                    app.logger.info(f"Rating Scale created for Question ID {question.id}")

        db.session.commit()
        app.logger.info("Survey creation process completed successfully.")
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in creating survey: {e}\n{traceback.format_exc()}")
        raise


# Routes for taking the survey
@app.route('/take_survey/<int:survey_id>', methods=['GET', 'POST'])
def take_survey(survey_id):
    if request.method == 'GET':
        survey = Survey.query.get_or_404(survey_id)
        logging.info(f"Fetched survey: {survey.survey_title}")

        question_groups = []
        conditional_questions_mapping = {}
        conditional_questions_details = {}

        for group in survey.question_groups:
            questions = []
            for question in group.questions:
                if not any(link.parent_option_id for link in question.conditional_links):
                    questions.append(question)
                    for option in question.question_options:
                        conditional_link = ConditionalLink.query.filter_by(parent_option_id=option.id).first()
                        if conditional_link:
                            cond_question = Question.query.get(conditional_link.child_question_id)
                            conditional_questions_mapping[option.id] = conditional_link.child_question_id
                            if cond_question:
                                conditional_questions_details[conditional_link.child_question_id] = {
                                    'question_text': cond_question.question_text,
                                    'question_type_id': cond_question.question_type_id,
                                    'options': [{'option_text': opt.option_text} for opt in cond_question.question_options] if cond_question.question_type_id == 2 else None,
                                    'rating_scale': {
                                        'min_value': cond_question.rating_scale.min_value,
                                        'max_value': cond_question.rating_scale.max_value,
                                        'step': cond_question.rating_scale.step
                                    } if cond_question.question_type_id == 3 else None
                                }
            question_groups.append({'group': group, 'questions': questions})

        return render_template('submission/take_survey.html', survey=survey, question_groups=question_groups,
                               conditional_questions_mapping=conditional_questions_mapping,
                               conditional_questions_details=conditional_questions_details,
                               question_type_mapping=question_type_mapping)

    elif request.method == 'POST':
        logging.info(f"POST request for survey with ID: {survey_id}")
        new_participant = Participant(survey_id=survey_id)
        db.session.add(new_participant)
        db.session.flush()  # Flush to get the new participant's ID
        logging.info(f"New participant added with ID: {new_participant.id}")

        # First pass: Create and commit Answer records
        answer_ids = {}
        try:
            for key, value in request.form.items():
                if key.startswith('question_'):
                    question_id = int(key.split('_')[1])
                    question = Question.query.get(question_id)
                    if question:
                        answer = Answer(
                            survey_id=survey_id,
                            question_id=question_id,
                            participant_id=new_participant.id
                        )

                        if question.question_type_id == question_type_mapping['open-ended']:
                            answer.answer_text = value
                        elif question.question_type_id == question_type_mapping['rating-scale']:
                            answer.answer_rating = int(value)  # Ensure the value is stored as an integer

                        db.session.add(answer)
                        db.session.flush()  # Flush to get the answer's ID
                        answer_ids[question_id] = answer.id

            db.session.commit()
            logging.info("Answers committed to the database")

        except Exception as e:
            db.session.rollback()
            logging.error(f"Error in take_survey route: {e}")
            flash(f'An error occurred while submitting your survey: {e}', 'danger')
            return redirect(url_for('survey_view', survey_id=survey_id))

        # Second pass: Create SelectedOption records for multiple-choice questions
        try:
            for key, value in request.form.items():
                if key.startswith('question_'):
                    question_id = int(key.split('_')[1])
                    question = Question.query.get(question_id)
                    if question and question.question_type_id == question_type_mapping['multiple-choice']:
                        selected_option = QuestionOption.query.filter_by(question_id=question_id,
                                                                         option_text=value).first()
                        if selected_option:
                            selected_option_entry = SelectedOption(
                                answer_id=answer_ids[question_id],
                                question_option_id=selected_option.id
                            )
                            db.session.add(selected_option_entry)
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            logging.error(f"Error in take_survey route: {e}")
            flash(f'An error occurred while processing selected options: {e}', 'danger')

        flash('Thank you for completing the survey!', 'success')
        return redirect(url_for('survey_view', survey_id=survey_id))

    return 'Method Not Allowed', 405


@app.route('/survey_answers/<int:survey_id>/<int:participant_id>')
def survey_answers(survey_id, participant_id):
    survey = Survey.query.get_or_404(survey_id)
    participant = Participant.query.get_or_404(participant_id)

    answers = db.session.query(Answer, Question).join(Question).filter(
        Answer.survey_id == survey_id,
        Answer.participant_id == participant_id
    ).all()

    selected_options = {}
    for answer, question in answers:
        if question.question_type_id == 2:  # Multiple-choice
            selected_option = SelectedOption.query.filter_by(answer_id=answer.id).first()
            if selected_option:
                option_text = QuestionOption.query.get(selected_option.question_option_id).option_text
                selected_options[answer.id] = option_text

    return render_template('submission/survey_answers.html', survey=survey, participant=participant, answers=answers,
                           selected_options=selected_options)


@app.route('/delete_submission/<int:survey_id>/<int:participant_id>', methods=['POST'])
def delete_submission(survey_id, participant_id):
    try:
        # First, delete any SelectedOption records linked to the answers of this participant
        answers = Answer.query.filter_by(participant_id=participant_id, survey_id=survey_id).all()
        for answer in answers:
            SelectedOption.query.filter_by(answer_id=answer.id).delete()

        # Now, delete the Answer records themselves
        Answer.query.filter_by(participant_id=participant_id, survey_id=survey_id).delete()

        db.session.commit()
        flash('Submission deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error occurred while deleting the submission.', 'danger')
        logging.error(f"Error deleting submission: {e}")

    return redirect(url_for('survey_view', survey_id=survey_id))


@app.route('/generate_pdf/<int:survey_id>/<int:participant_id>')
def generate_pdf(survey_id, participant_id):
    logging.basicConfig(filename='pdf_generation.log', level=logging.INFO)
    logger = logging.getLogger('pdf_generation')

    survey = Survey.query.get_or_404(survey_id)
    participant = Participant.query.get_or_404(participant_id)
    answers = db.session.query(Answer, Question).join(Question).filter(
        Answer.survey_id == survey_id,
        Answer.participant_id == participant_id
    ).all()

    selected_options = {}
    for answer, question in answers:
        if question.question_type_id == 2:  # Multiple-choice
            selected_option = db.session.query(SelectedOption).filter_by(answer_id=answer.id).first()
            if selected_option:
                option_text = QuestionOption.query.get(selected_option.question_option_id).option_text
                selected_options[answer.id] = option_text

    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)

    styles = getSampleStyleSheet()
    customParagraphStyle = styles["BodyText"].clone('customParagraphStyle')
    customParagraphStyle.fontSize = 10
    customParagraphStyle.leading = 12

    # Custom style for group title with red text color
    groupTitleStyle = styles['Heading2'].clone('groupTitleStyle')
    groupTitleStyle.textColor = colors.HexColor("#ed1b34")


    elements = [
        Paragraph(survey.survey_title, styles['Title']),
        Spacer(1, 12),
        Paragraph(f'Participant ID: {participant.id}', styles['Normal'])
    ]

    # Define the adjusted table style here
    tableStyle = TableStyle([
        # Group title style
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),

        # Header style
        ('BACKGROUND', (0, 1), (-1, 1), colors.lightgrey),
        ('TEXTCOLOR', (0, 1), (-1, 1), colors.black),
        ('ALIGN', (0, 1), (-1, 1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),

        # Cell style
        ('BACKGROUND', (0, 2), (-1, -1), colors.whitesmoke),
        ('TEXTCOLOR', (0, 2), (-1, -1), colors.grey),
        ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
        ('WORDWRAP', (0, 0), (-1, -1), 'LTR'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ])

    groupIndex = 1  # Start group numbering
    for group in survey.question_groups:
        groupHeader = f'Group {groupIndex}: {group.group_name}'
        data = [[Paragraph(groupHeader, styles['Heading2']), '']]
        data += [['Question', 'Answer']]  # Column headers

        questionIndex = 1  # Start question numbering for each group
        for question in group.questions:
            found_answer = next((answer for answer in answers if answer[1].id == question.id), None)
            questionText = f'{questionIndex}. {question.question_text}'  # Prepend question number
            answer_text = 'No answer provided'
            if found_answer:
                if question.question_type_id == 1:
                    answer_text = found_answer[0].answer_text
                elif question.question_type_id == 2:
                    answer_text = selected_options.get(found_answer[0].id, 'No answer selected')
                elif question.question_type_id == 3:
                    answer_text = str(found_answer[0].answer_rating)
            data.append([Paragraph(questionText, customParagraphStyle), Paragraph(answer_text, customParagraphStyle)])
            questionIndex += 1  # Increment question number

        table = Table(data, colWidths=[3.5 * inch, 3.5 * inch])
        table.setStyle(tableStyle)
        elements.append(table)
        elements.append(Spacer(1, 12))
        groupIndex += 1  # Increment group number

    doc.build(elements)

    logger.info(f'Generated PDF for Survey ID: {survey_id}, Participant ID: {participant_id}')
    response = make_response(pdf_buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename="survey_answers_{participant_id}.pdf"'
    return response


if __name__ == '__main__':
    app.run(debug=True)
