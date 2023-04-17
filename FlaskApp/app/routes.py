from flask import render_template, flash, redirect, url_for
from app import app, db
from app.forms import LoginForm, AddUserForm, AddArchiveForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Archive
from werkzeug.urls import url_parse
from flask import request
import os
import shutil
from threading import Thread, Event
from archivePackage import archive
from app import globals



#------------MISC------------------------------
@app.route('/users')
@login_required
def users():
    if not current_user.isAdmin:
        return unauthorized()
    
    users = User.query.all()
    return render_template("users.html", users=users)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/index')
@login_required
def index():
    user = {'username': 'Miguel'}
    return render_template("index.html", user=user, title='Title')



@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/archives')
@login_required
def archives():
    archives = Archive.query.all()
    return render_template("archives.html", archives=archives, busy=globals.thread.is_alive())
#------------------------------------------------------------------------



#---------------ADD ROUTES----------------------------------------------
@app.route('/addUser', methods=['GET', 'POST'])
@login_required
def addUser():
    form = AddUserForm()
    if not current_user.isAdmin:
        return redirect(url_for('index'))
    

    if form.validate_on_submit():
        user = User(username = form.username.data,
                    email = form.email.data,
                    isAdmin = form.isAdmin.data)
        user.set_password(form.password1.data)
        db.session.add(user)
        db.session.commit()
        flash("User has been added!")
        return redirect(url_for('users'))

    return render_template('addUser.html', form=form)



@app.route('/createArchive', methods=['GET', 'POST'])
@login_required
def createArchive():
    form = AddArchiveForm()

    if not current_user.isAdmin:
        return unauthorized()
    
    if form.validate_on_submit():
        global thread
        global thread_archive_id
        if not globals.thread.is_alive():
            newArchive = Archive(user_id=str(current_user.id))
            db.session.add(newArchive)
            db.session.commit()
            globals.thread_archive_id = newArchive.id
            globals.thread = Thread(target=archive.run, args=(newArchive.id, form.prefix.data, form.recursive.data))
            globals.thread.start()
        else:
            flash('Thread already started!')
        return redirect(url_for('archives'))
    return render_template('addArchive.html', form=form)
#-------------------------------------------------------------------------------



#----------------------DELETE ROUTES-----------------------------------------
@app.route('/removeArchive/<id>')
@login_required
def removeArchive(id):
    if not current_user.isAdmin:
        return unauthorized()
    
    a = Archive.query.filter_by(id=id).first()
    if a is not None:
        db.session.delete(a)
        db.session.commit()
    else:
        flash("That archive does not exist")

    flash("thread_archive_id:" + str(globals.thread_archive_id))
    flash("id:" + str(id))
    if str(globals.thread_archive_id) == str(id):
        globals.event.set()
        globals.thread.join()
        globals.event.clear()

    if os.path.isdir(f"{os.getcwd()}/archives/{id}"):
        
        shutil.rmtree(f'archives/{id}')
        
    flash('Archive has been deleted')
    return redirect(url_for('archives'))


@app.route('/removeUser/<username>')
@login_required
def removeUser(username):
    user = User.query.filter_by(username=username).first()
    if current_user.username == user.username:
        flash("You cannot remove the currently logged in user")
        return redirect(url_for('users'))
    

    db.session.delete(user)
    db.session.commit()

    return redirect(url_for('users'))
#----------------------------------------------------------------------



#-------------------ERROR ROUTES---------------------------------------------
@app.errorhandler(401)
def unauthorized():
    return render_template('401.html'), 401
#---------------------------------------------------------------


