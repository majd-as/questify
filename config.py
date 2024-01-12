import os


class Config(object):
    # General Flask Config
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    DEBUG = False
    TESTING = False

    # Database Config
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or ('postgresql://questify_user:questifypass@localhost'
                                                                 '/questy1_2')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
