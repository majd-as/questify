from datetime import datetime
from enum import Enum

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort
from sqlalchemy import func, desc

from app.models import User, Survey, QuestionGroup, Question, QuestionType, QuestionCondition, QuestionOption, \
    Participant, Answer, SelectedOption, RatingScale
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash
from sqlalchemy.exc import SQLAlchemyError
import logging

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


# @app.route('/', methods=['GET', 'POST'])
# def index():
#     if request.method == 'POST':
#         pass
#
#     return render_template('index.html')


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


# View a specific question type
@app.route('/question_types/<int:id>', methods=['GET'])
def question_type_view(id):
    question_type = QuestionType.query.get(id)
    return render_template('question_type/question_type_view.html', question_type=question_type)


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

    return render_template('survey_list.html', surveys=surveys)


# Route for viewing a specific survey
@app.route('/surveys/<int:survey_id>/view', methods=['GET'])
def survey_view(survey_id):
    survey_submissions = []  # Initialize it before the try block
    try:
        # Retrieve the survey and its related entities from the database based on survey_id
        survey = Survey.query.get(survey_id)

        if not survey:
            # Handle the case where the survey does not exist
            flash('Survey not found.', 'danger')
            return redirect(url_for('survey_list'))  # Redirect to a list of surveys or another appropriate page

        # Fetch related entities
        question_groups = QuestionGroup.query.filter_by(survey_id=survey.id).all()
        participants = Participant.query.filter_by(survey_id=survey.id).all()
        answers = Answer.query.filter_by(survey_id=survey.id).all()

        # Create a dictionary to store question data with options and conditional questions
        question_data = {}

        for group in question_groups:
            questions = Question.query.filter_by(group_id=group.id).all()
            question_data[group] = []

            for question in questions:
                question_dict = {'question': question, 'options': [], 'conditional_questions': []}

                if question.question_type_id == 2:  # Multiple-choice question
                    options = QuestionOption.query.filter_by(question_id=question.id).all()
                    for option in options:
                        option_dict = {'option': option, 'conditional_questions': []}

                        # Fetch conditional questions for this option if any
                        conditional_questions = Question.query.join(
                            QuestionCondition, Question.id == QuestionCondition.dependent_question_id
                        ).filter(QuestionCondition.parent_question_id == question.id,
                                 QuestionCondition.condition == option.option_text).all()

                        for cond_question in conditional_questions:
                            option_dict['conditional_questions'].append(cond_question)

                        question_dict['options'].append(option_dict)

                elif question.question_type_id == 3:  # Rating scale question
                    rating_scale = RatingScale.query.filter_by(question_id=question.id).first()
                    question_dict['rating_scale'] = rating_scale

                # Fetch conditional questions for this question if any
                conditional_questions = Question.query.join(
                    QuestionCondition, Question.id == QuestionCondition.dependent_question_id
                ).filter(QuestionCondition.parent_question_id == question.id).all()

                for cond_question in conditional_questions:
                    question_dict['conditional_questions'].append(cond_question)

                question_data[group].append(question_dict)

        # Fetch the timestamps of each survey submission
        survey_submissions = db.session.query(
            Participant.id,
            func.max(Answer.created_at).label('submission_time')
        ).join(Answer, Answer.participant_id == Participant.id) \
            .filter(Participant.survey_id == survey_id) \
            .group_by(Participant.id) \
            .order_by(func.max(Answer.created_at).desc()) \
            .all()

        # Sort by parameter
        sort_by = request.args.get('sort_by', 'date_taken_desc')
        survey_submissions_query = db.session.query(
            Participant.id,
            func.max(Answer.created_at).label('submission_time')
        ).join(Answer, Answer.participant_id == Participant.id) \
            .filter(Participant.survey_id == survey_id) \
            .group_by(Participant.id)

        # Apply sorting
        if sort_by == 'date_taken_asc':
            survey_submissions = survey_submissions_query.order_by('submission_time').all()
        elif sort_by == 'date_taken_desc':
            survey_submissions = survey_submissions_query.order_by(desc('submission_time')).all()
        else:
            survey_submissions = survey_submissions_query.order_by(desc('submission_time')).all()  # Default case

    except Exception as e:
        logging.error(f"An error occurred while fetching the survey details: {str(e)}")
        flash('An error occurred while fetching the survey details.', 'danger')
        return redirect(url_for('survey_list'))

    return render_template('survey_view.html', survey=survey, question_groups=question_groups,
                           participants=participants, answers=answers, question_data=question_data,
                           survey_submissions=survey_submissions)


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


# Route for updating a survey
@app.route('/survey_update/<int:survey_id>', methods=['GET', 'POST'])
def survey_update(survey_id):
    # Fetch the survey by its ID
    survey = Survey.query.get_or_404(survey_id)

    if request.method == 'POST':
        try:
            # Update the survey metadata
            survey.survey_title = request.form.get('survey_title')
            survey.survey_description = request.form.get('survey_description')
            survey.welcome_message = request.form.get('welcome_message')
            survey.exit_message = request.form.get('exit_message')

            # Process question groups and questions
            for group in survey.question_groups:
                group_title_key = f'group_{group.id}_title'
                group_description_key = f'group_{group.id}_description'
                group.group_name = request.form.get(group_title_key)
                group.group_description = request.form.get(group_description_key)

                # Process questions within the group
                for question in group.questions:
                    question_text_key = f'group_{group.id}_question_{question.id}_text'
                    question_type_key = f'group_{group.id}_question_{question.id}_type'
                    question_text = request.form.get(question_text_key)
                    question_type = request.form.get(question_type_key)

                    # Update question attributes
                    question.question_text = question_text
                    question_type_id = question_type_mapping.get(question_type, 1)  # Default to 1 if not found
                    question.question_type_id = question_type_id

                    if question_type_id == 2:
                        # Handle multiple-choice options
                        option_texts_key = f'group_{group.id}_question_{question.id}_options'
                        option_texts = request.form.getlist(option_texts_key)

                        # Clear existing options and add new ones
                        question.question_options = [QuestionOption(option_text=option_text) for option_text in
                                                     option_texts if option_text]

                    elif question_type_id == 3:
                        # Handle rating scale data
                        min_value_key = f'group_{group.id}_question_{question.id}_min_value'
                        max_value_key = f'group_{group.id}_question_{question.id}_max_value'
                        step_key = f'group_{group.id}_question_{question.id}_step'

                        min_value = request.form.get(min_value_key)
                        max_value = request.form.get(max_value_key)
                        step = request.form.get(step_key)

                        if min_value and max_value and step:
                            if question.rating_scale:
                                rating_scale = question.rating_scale
                            else:
                                rating_scale = RatingScale()
                                question.rating_scale = rating_scale

                            rating_scale.min_value = int(min_value)
                            rating_scale.max_value = int(max_value)
                            rating_scale.step = int(step)

                    elif not question_text:
                        # Delete question if text is empty
                        db.session.delete(question)

                # Delete question group if no name and no questions
                if not group.group_name and not group.questions:
                    db.session.delete(group)

            # Add new question groups
            new_group_names = request.form.getlist('new_group_name')
            new_group_descriptions = request.form.getlist('new_group_description')

            for group_name, group_description in zip(new_group_names, new_group_descriptions):
                if group_name and group_description:
                    new_group = QuestionGroup(group_name=group_name, group_description=group_description)
                    survey.question_groups.append(new_group)
                    db.session.add(new_group)

            # Add new questions
            new_question_texts = request.form.getlist('new_question_text')
            new_question_types = request.form.getlist('new_question_type')

            for question_text, question_type in zip(new_question_texts, new_question_types):
                if question_text and question_type:
                    new_question = Question(question_text=question_text, question_type_id=question_type)
                    db.session.add(new_question)

            db.session.commit()
            flash('Survey updated successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the survey. Please try again.', 'error')
            app.logger.error(str(e))

        return redirect(url_for('survey_update', survey_id=survey_id))

    return render_template('survey_update.html', survey=survey)


# Route to create a new survey
@app.route('/create_survey', methods=['GET', 'POST'])
def create_survey():
    # Handle GET request: Show survey creation form
    if request.method == 'GET':
        return render_template("survey_create.html")

    # Handle POST request: Process submitted form data
    elif request.method == 'POST':
        # Access control: Check if user is an admin
        if not session.get('is_admin'):
            flash('Access denied. Please log in as an admin.', 'danger')
            return redirect(url_for('index'))

        # Try to create survey from submitted data
        try:
            # Extract survey data from form input
            survey_data = extract_survey_data(request.form)
            # If data is valid, create survey in database
            if survey_data:
                create_survey_in_database(survey_data)
                flash('Survey created successfully!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Failed to create the survey. Please fill in all required fields.', 'danger')
        # Handle exceptions and log errors
        except Exception as e:
            flash('Failed to create the survey. Please try again later.', 'danger')
            app.logger.error(f"Error creating survey: {str(e)}")

    # Default response for GET request
    return render_template("survey_create.html")


# Function to extract and organize survey data from form
def extract_survey_data(form_data):
    # Retrieve basic survey details
    survey_title = form_data.get('survey_title')
    survey_description = form_data.get('survey_description')
    welcome_message = form_data.get('welcome_message')
    exit_message = form_data.get('exit_message')

    # Ensure all basic details are provided
    if not all([survey_title, survey_description, welcome_message, exit_message]):
        return None

    # Extract question groups and their details
    question_groups = []
    group_count = 1
    while form_data.get(f'group_{group_count}_title'):
        group_name = form_data.get(f'group_{group_count}_title')
        group_description = form_data.get(f'group_{group_count}_description')
        questions = extract_questions(form_data, group_count)
        question_groups.append({
            'group_name': group_name,
            'group_description': group_description,
            'questions': questions
        })
        group_count += 1

    # Return organized survey data
    return {
        'survey_title': survey_title,
        'survey_description': survey_description,
        'welcome_message': welcome_message,
        'exit_message': exit_message,
        'question_groups': question_groups
    }


# Function to extract and organize question details for each group
def extract_questions(form_data, group_index):
    questions = []
    question_count = 1
    while form_data.get(f'group_{group_index}_question_{question_count}_text'):
        question_text = form_data.get(f'group_{group_index}_question_{question_count}_text')
        question_type = form_data.get(f'group_{group_index}_question_{question_count}_type')

        # Organize question details
        question = {
            'question_text': question_text,
            'question_type': question_type
        }

        # Handle different question types and their specific data
        if question_type == 'multiple-choice':
            options = extract_options(form_data, group_index, question_count)
            question['options'] = options
        elif question_type == 'rating-scale':
            min_value = form_data.get(f'group_{group_index}_question_{question_count}_min_value')
            max_value = form_data.get(f'group_{group_index}_question_{question_count}_max_value')
            step = form_data.get(f'group_{group_index}_question_{question_count}_step')
            question['min_value'] = min_value
            question['max_value'] = max_value
            question['step'] = step

        questions.append(question)
        question_count += 1
    return questions


# Function to extract options for multiple-choice questions
def extract_options(form_data, group_index, question_index):
    options = []
    option_count = 1
    while form_data.get(f'group_{group_index}_question_{question_index}_option_{option_count}'):
        option_text = form_data.get(f'group_{group_index}_question_{question_index}_option_{option_count}')
        options.append(option_text)
        option_count += 1
    return options


# Function to create the survey in the database using the extracted data
def create_survey_in_database(survey_data):
    try:
        db.session.begin()
        # Create a new survey instance
        survey = Survey(
            survey_title=survey_data['survey_title'],
            survey_description=survey_data['survey_description'],
            welcome_message=survey_data['welcome_message'],
            exit_message=survey_data['exit_message'],
            created_by_id=session['user_id']
        )
        db.session.add(survey)
        db.session.flush()

        # Create question groups and questions for the survey
        for group_data in survey_data['question_groups']:
            question_group = QuestionGroup(
                group_name=group_data['group_name'],
                group_description=group_data['group_description'],
                survey_id=survey.id
            )
            db.session.add(question_group)
            db.session.flush()

            # Create questions and their specific details based on type
            for question_data in group_data['questions']:
                question = Question(
                    question_text=question_data['question_text'],
                    question_type_id=question_type_mapping[question_data['question_type']],
                    group_id=question_group.id
                )
                db.session.add(question)
                db.session.flush()

                # Handle creation of options for multiple-choice questions
                if question_data['question_type'] == 'multiple-choice':
                    for option_text in question_data.get('options', []):
                        option = QuestionOption(option_text=option_text, question_id=question.id)
                        db.session.add(option)

                # Handle creation of rating scale for rating-scale questions
                elif question_data['question_type'] == 'rating-scale':
                    rating_scale = RatingScale(
                        min_value=question_data['min_value'],
                        max_value=question_data['max_value'],
                        step=question_data['step'],
                        question_id=question.id
                    )
                    db.session.add(rating_scale)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating survey: {str(e)}")
        raise


# @app.route('/create_survey', methods=['GET', 'POST'])
# def create_survey():
#     if not session.get('is_admin'):
#         flash('Access denied. Please log in as an admin.', 'danger')
#         return redirect(url_for('index'))
#
#     if request.method == 'POST':
#         try:
#             survey_data = extract_survey_data(request.form)
#             if survey_data:
#                 create_survey_in_database(survey_data)
#                 flash('Survey created successfully!', 'success')
#                 return redirect(url_for('admin_dashboard'))
#             else:
#                 flash('Failed to create the survey. Please fill in all required fields.', 'danger')
#         except Exception as e:
#             flash('Failed to create the survey. Please try again later.', 'danger')
#             app.logger.error(f"Error creating survey: {str(e)}")
#
#     return render_template("survey_create.html")
#
#
# def extract_survey_data(form_data):
#     survey_title = form_data.get('survey_title')
#     survey_description = form_data.get('survey_description')
#     welcome_message = form_data.get('welcome_message')
#     exit_message = form_data.get('exit_message')
#
#     if not all([survey_title, survey_description, welcome_message, exit_message]):
#         return None
#
#     question_groups = []
#     group_count = 1
#
#     while True:
#         group_name = form_data.get(f'group_{group_count}_title')
#         group_description = form_data.get(f'group_{group_count}_description')
#
#         if group_name is None:
#             break
#
#         questions = extract_questions(form_data, group_count)
#         question_group = {
#             'group_name': group_name,
#             'group_description': group_description,
#             'questions': questions
#         }
#
#         question_groups.append(question_group)
#         group_count += 1
#
#     survey_data = {
#         'survey_title': survey_title,
#         'survey_description': survey_description,
#         'welcome_message': welcome_message,
#         'exit_message': exit_message,
#         'question_groups': question_groups
#     }
#
#     return survey_data
#
#
# def extract_questions(form_data, group_index):
#     questions = []
#     question_count = 1
#
#     while True:
#         question_text = form_data.get(f'group_{group_index}_question_{question_count}_text')
#         question_type = form_data.get(f'group_{group_index}_question_{question_count}_type')
#
#         if question_text is None:
#             break
#
#         question = {
#             'question_text': question_text,
#             'question_type': question_type,
#         }
#
#         if question_type == 'multiple-choice':
#             options = extract_options(form_data, group_index, question_count)
#             question['options'] = options
#
#         elif question_type == 'rating-scale':
#             min_value = form_data.get(f'group_{group_index}_question_{question_count}_min_value')
#             max_value = form_data.get(f'group_{group_index}_question_{question_count}_max_value')
#             step = form_data.get(f'group_{group_index}_question_{question_count}_step')
#
#             question['min_value'] = min_value
#             question['max_value'] = max_value
#             question['step'] = step
#
#         questions.append(question)
#         question_count += 1
#
#     return questions
#
#
# def extract_options(form_data, group_index, question_index):
#     options = []
#     option_count = 1
#
#     while True:
#         option_text = form_data.get(f'group_{group_index}_question_{question_index}_option_{option_count}')
#
#         if option_text is None:
#             break
#
#         options.append(option_text)
#         option_count += 1
#
#     return options
#
#
# def create_survey_in_database(survey_data):
#     try:
#         # Begin a transaction
#         db.session.begin()
#
#         # Create a new survey instance
#         survey = create_survey_instance(survey_data)
#         db.session.add(survey)
#         db.session.flush()  # Flush to generate the survey ID
#
#         for group_data in survey_data['question_groups']:
#             # Create a new question group instance
#             question_group = create_question_group_instance(group_data, survey.id)
#             db.session.add(question_group)
#             db.session.flush()  # Flush to generate the question group ID
#
#             for question_data in group_data['questions']:
#                 # Create a new question instance
#                 question = create_question_instance(question_data, question_group.id)
#                 db.session.add(question)
#                 db.session.flush()  # Flush to generate the question ID
#
#                 if question_data['question_type'] == 'multiple-choice':
#                     create_multiple_choice_options(question_data['options'], question.id)
#
#                 elif question_data['question_type'] == 'rating-scale':
#                     create_rating_scale(question_data, question.id)
#
#         # Commit the entire transaction
#         db.session.commit()
#
#     except Exception as e:
#         # Rollback the transaction if an error occurs
#         db.session.rollback()
#         app.logger.error(f"Error creating survey: {str(e)}")
#
#
# def create_survey_instance(survey_data):
#     return Survey(
#         survey_title=survey_data['survey_title'],
#         survey_description=survey_data['survey_description'],
#         welcome_message=survey_data['welcome_message'],
#         exit_message=survey_data['exit_message'],
#         created_by_id=session['user_id']
#     )
#
#
# def create_question_group_instance(group_data, survey_id):
#     return QuestionGroup(
#         group_name=group_data['group_name'],
#         group_description=group_data['group_description'],
#         survey_id=survey_id
#     )
#
#
# def create_question_instance(question_data, group_id):
#     return Question(
#         question_text=question_data['question_text'],
#         question_type_id=question_type_mapping[question_data['question_type']],
#         group_id=group_id
#     )
#
#
# def create_multiple_choice_options(options_data, question_id):
#     for option_text in options_data:
#         option = QuestionOption(
#             option_text=option_text,
#             question_id=question_id
#         )
#         db.session.add(option)
#         db.session.commit()
#
#
# def create_rating_scale(question_data, question_id):
#     rating_scale = RatingScale(
#         min_value=question_data['min_value'],
#         max_value=question_data['max_value'],
#         step=question_data['step'],
#         question_id=question_id
#     )
#     db.session.add(rating_scale)
#     db.session.commit()


# Routes for taking the survey
@app.route('/take_survey/<int:survey_id>', methods=['GET', 'POST'])
def take_survey(survey_id):
    if request.method == 'GET':
        survey = Survey.query.get_or_404(survey_id)
        return render_template('take_survey.html', survey=survey, question_type_mapping=question_type_mapping)

    elif request.method == 'POST':
        new_participant = Participant(survey_id=survey_id)
        db.session.add(new_participant)
        db.session.flush()  # Flush to get the new participant's ID

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

        except Exception as e:
            db.session.rollback()
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

    return render_template('survey_answers.html', survey=survey, participant=participant, answers=answers,
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


if __name__ == '__main__':
    app.run(debug=True)
