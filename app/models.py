from app import db
from sqlalchemy import Enum, DateTime
from datetime import datetime

# Define roles
ROLES = Enum('Admin', 'Creator', name='roles')


# User model
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    email = db.Column(db.String(120))
    role = db.Column(ROLES)

    # Relationships
    surveys_created = db.relationship('Survey', backref='creator', lazy='dynamic')


# Survey model
class Survey(db.Model):
    __tablename__ = 'survey'
    id = db.Column(db.Integer, primary_key=True)
    survey_title = db.Column(db.String(150))
    survey_description = db.Column(db.String(1000))
    welcome_message = db.Column(db.String(1000))
    exit_message = db.Column(db.String(1000))
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationships
    question_groups = db.relationship('QuestionGroup', backref='survey', lazy='dynamic', cascade='all, delete-orphan')
    participants = db.relationship('Participant', backref='survey', lazy='dynamic', cascade='all, delete-orphan')
    answers = db.relationship('Answer', backref='survey', lazy='dynamic', cascade='all, delete-orphan')


# ShareSurvey model
class ShareSurvey(db.Model):
    __tablename__ = 'share_survey'
    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'), nullable=False)
    share_url = db.Column(db.String(300))
    share_code = db.Column(db.String(50))


# QuestionType model
class QuestionType(db.Model):
    __tablename__ = 'question_type'
    id = db.Column(db.Integer, primary_key=True)
    type_name = db.Column(db.String(255), unique=True, nullable=False)


# QuestionGroup model
class QuestionGroup(db.Model):
    __tablename__ = 'question_group'
    id = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.String(100))
    group_description = db.Column(db.String(500))
    survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'), nullable=False)

    # Relationships
    questions = db.relationship('Question', backref='group', lazy='dynamic', cascade='all, delete-orphan')


# Question Model
class Question(db.Model):
    __tablename__ = 'question'
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(500), nullable=False)
    question_type_id = db.Column(db.Integer, db.ForeignKey('question_type.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('question_group.id'))

    # Relationships
    parent_conditions = db.relationship('QuestionCondition', foreign_keys='QuestionCondition.parent_question_id',
                                        backref='parent_question', lazy='dynamic')
    dependent_conditions = db.relationship('QuestionCondition', foreign_keys='QuestionCondition.dependent_question_id',
                                           backref='dependent_question', lazy='dynamic')
    question_options = db.relationship('QuestionOption', backref='question', lazy='dynamic')
    rating_scale = db.relationship('RatingScale', uselist=False, backref='question')


# ConditionalQuestion Model (QuestionCondition)
class QuestionCondition(db.Model):
    __tablename__ = 'question_conditions'
    id = db.Column(db.Integer, primary_key=True)
    parent_question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    dependent_question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    condition = db.Column(db.String(255), nullable=False)
    condition_value = db.Column(db.String(255), nullable=False)


# QuestionOption model
class QuestionOption(db.Model):
    __tablename__ = 'question_option'
    id = db.Column(db.Integer, primary_key=True)
    option_text = db.Column(db.String(500))
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))


# RatingScale model
class RatingScale(db.Model):
    __tablename__ = 'rating_scale'
    id = db.Column(db.Integer, primary_key=True)
    min_value = db.Column(db.Integer)
    max_value = db.Column(db.Integer)
    step = db.Column(db.Integer)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))


# Participant model
class Participant(db.Model):
    __tablename__ = 'participant'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'), nullable=False)
    answers = db.relationship('Answer', backref='participant', lazy='dynamic', cascade='all, delete-orphan')


# SelectedOption model
class SelectedOption(db.Model):
    __tablename__ = 'selected_option'
    id = db.Column(db.Integer, primary_key=True)
    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'))
    question_option_id = db.Column(db.Integer, db.ForeignKey('question_option.id'))


# Answer model
class Answer(db.Model):
    __tablename__ = 'answer'
    id = db.Column(db.Integer, primary_key=True)
    answer_text = db.Column(db.String(500), nullable=True)  # Text for open questions
    answer_rating = db.Column(db.Integer, nullable=True)  # Rating for Rating Scale
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'))
    selected_options = db.relationship('SelectedOption', backref='answer', lazy='dynamic', cascade='all, delete-orphan')
    rating_scale_id = db.Column(db.Integer, db.ForeignKey('rating_scale.id'))
