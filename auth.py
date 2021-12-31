import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from dbfunc import connect_db,match_user_pwd,disconnect_db,get_domain,insert_user_pwd,insert_patient_inf
from dbfunc import databasePATH
bp = Blueprint('auth', __name__)


@bp.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = connect_db(databasePATH)
        judge = match_user_pwd(db, username, password)
        disconnect_db(db)

        if judge == True:

            if session.get(username) is None:
                session[username] = username
                session.permanent = True

            db = connect_db(databasePATH)
            domain = int(get_domain(db, username))
            disconnect_db(db)


            if domain == 0:
                return redirect(url_for('admin.admin', username=username))
            elif domain == 1:
                return redirect(url_for('doctor.doctor', username=username))
            elif domain == 2:
                return redirect(url_for('patient.patient', username=username))
            elif domain == 3:
                return redirect(url_for('chief.chief', username=username))
            elif domain == 4:
                return redirect(url_for('fever_doctor.doctor', username=username))
        else:
            flash('login failed!')
            return redirect(url_for('auth.login'))
    return render_template('login.html')


@bp.route('/logout')
@bp.route('/logout?<string:username>')
def logout(username=None):
    if session.get('username') == username:
        session.pop('username')
    return redirect(url_for('auth.login'))


@bp.route('/forget_password')
def forget_password():
    return render_template('forget_password.html')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        repeat_password = request.form['repeat_password']
        pat_name = request.form['pat_name']
        pat_date = request.form['pat_date']
        pat_passport = request.form['passport']
        pat_gender = request.form['pat_gender']
        pat_phone = request.form['pat_phone']
        pat_email = request.form['email']
        # domain = request.form['domain']
        if password != repeat_password:
            flash('password is not equal to confirm_password!')
            return redirect(url_for('auth.register'))

        db = connect_db(databasePATH)
        judge = insert_user_pwd(db, username, password, 2)



        if judge == True:
            flash('Register Success!')
            patient_id = insert_patient_inf(db,pat_name, pat_date, pat_passport, pat_gender, pat_phone, pat_email, username,password)
            disconnect_db(db)
            return redirect(url_for('auth.login'))
        else:
            flash('something wrong')
            return redirect(url_for('auth.register'))
    return render_template('register.html')



def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view