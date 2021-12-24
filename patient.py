import functools
import sqlite3
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from dbfunc import connect_db,match_user_pwd,disconnect_db,get_domain,insert_user_pwd
from dbfunc import databasePATH
from sliderbaritem import patientItems
bp = Blueprint('patient', __name__)

db = connect_db(databasePATH)

def get_id(db,user):
    cur = db.cursor()
    tt = cur.execute("select patient_id \
                      from patient \
                      where username = '%s'" %user)
    for i in tt:
        return i[0]

@bp.route('/patient/?<string:username>',methods=['GET','POST'])
def patient(username):
    if session.get(username) is not None:
        patient = db.execute("SELECT * FROM patient WHERE username=?", (username,)).fetchall()
        return render_template('patient.html',name = username,sidebarItems=patientItems, patient=patient)
    return redirect(url_for('auth.login'))

@bp.route('/patient/?<string:username>/departments')
def departments(username):
    departments = db.execute("SELECT * FROM department").fetchall()
    return render_template('patient_departments.html', departments=departments)

@bp.route('/patient/?<string:username>/department/<id>')
def department(username,id):
    department = db.execute('SELECT * FROM department WHERE department_id=?', (id,)).fetchall()
    return render_template('patient_department.html', department=department)

@bp.route('/patient/?<string:username>/doctors')
def doctors(username):
    doctors = db.execute("SELECT * FROM employees").fetchall()
    return render_template('patient_doctors.html', doctors=doctors)

@bp.route('/patient/?<string:username>/doctor/<id>')
def doctor(username, id):
    doctor = db.execute('SELECT * FROM employees WHERE e_id=?', (id,)).fetchall()
    return render_template('patient_doctor.html', doctor=doctor)


