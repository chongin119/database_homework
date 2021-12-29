import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from dbfunc import connect_db,match_user_pwd,disconnect_db,get_domain,insert_user_pwd
from dbfunc import databasePATH
from sliderbaritem import doctorItems
bp = Blueprint('admin', __name__)

db = connect_db(databasePATH)

@bp.route('/patients',methods=['GET','POST'])

def patients():
    patients = db.execute("SELECT * FROM patient").fetchall()
    return render_template('patients.html', patients=patients)

@bp.route('/add_patient',methods=['GET','POST'])

def add_patient():
    if request.method == 'POST':
        """api to add the patient in the database"""
        pat_name = request.form['pat_name']
        pat_date = request.form['pat_date']
        pat_passport = request.form['passport']
        pat_gender = request.form['pat_gender']
        pat_phone = request.form['pat_phone']
        pat_email = request.form['pat_email']
        pat_username = request.form['pat_username']
        pat_password = request.form['pat_password']
        error=None
        try:
            request.form['pat_id'] = db.execute('''INSERT INTO patient(name,DOB,passport,gender,phone,email,username,password)
                        VALUES(?,?,?,?,?,?,?,?)''', (
            pat_name, pat_date, pat_passport, pat_gender, pat_phone,pat_email,pat_username,pat_password)).lastrowid
            db.execute('''INSERT INTO login_inf(username, password, domain)
                        VALUES(?,?,?)''',(pat_username,pat_password,2))
            db.commit()
        except:
            error = 'something got wrong'
        if error is not None:
            flash(error)
        return redirect(url_for('patient.patients'))
    return render_template('add_patient.html')



@bp.route('/patients/<id>',methods=['POST','GET'])
def update_patients(id):
    patient = db.execute("SELECT * FROM patient WHERE pat_id=?", (id,)).fetchall()
    if request.method == 'POST':
        pat_name = request.form['pat_name']
        pat_date = request.form['pat_date']
        pat_passport = request.form['passport']
        pat_gender = request.form['pat_gender']
        pat_phone = request.form['pat_phone']
        pat_email = request.form['pat_email']
        pat_username = request.form['pat_username']
        # pat_password = request.form['pat_password']
        db.execute(
            "UPDATE patient SET name=?,DOB=?,passport=?,gender=?,phone=?,email=?,username=?  WHERE patient_id=?",
            (pat_name, pat_date, pat_passport, pat_gender, pat_phone, pat_email, pat_username))
        db.execute('''UPDATE login_inf 
                    SET username = ?
                    WHERE username = ?''', (pat_username,))
        db.commit()
        return redirect(url_for('patient.patients'))
    return render_template('update_patient.html',patient=patient)