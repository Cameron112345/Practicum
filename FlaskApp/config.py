import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'very-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'sql/app.db')
    #SQLALCHEMY_DATABASE_URI = "mysql+mysqldb://camcole:8915@localhost/db"
    #SQLALCHEMY_DATABASE_URI = "mysql+mysqldb://" + os.environ.get('DATABASE_USER') + ":" + os.environ.get("DATABASE_PASSWORD") + "@localhost/db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False