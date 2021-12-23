import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from dbfunc import connect_db,match_user_pwd,disconnect_db,get_domain,insert_user_pwd
from dbfunc import databasePATH
from sliderbaritem import doctorItems
bp = Blueprint('appointment', __name__)

db = connect_db(databasePATH)

def get_id(db,user):
    cur = db.cursor()
    tt = cur.execute("select patient_id \
                      from patient \
                      where username = '%s'" %user)
    for i in tt:
        return i[0]

@bp.route('/patient/?<string:username>/appointments',methods=['GET','POST'])
def appointments(username):
    appointments = db.execute(
        '''SELECT date, department_name, name
        FROM appointment a LEFT JOIN employees e ON e_id = doc_id 
        LEFT JOIN department d ON d.department_id = a.department_id 
         ORDER BY date DESC'''
    ).fetchall()
    return render_template('appointments.html', appointments=appointments)

@bp.route('/patient/?<string:username>/add_appointment',methods=['GET','POST'])
def add_appointment(username):
    if request.method == 'POST':
        """api to add the patient in the database"""
        app_date = request.form['date']
        patient_id = get_id(db,username)
        department_id = request.form['de_id']
        doc_id = request.form['doc_id']
        survey = None
        app_id = db.execute('''INSERT INTO appointment(date,patient_id,department_id,doc_id,epidemic_survey)
                    VALUES(?,?,?,?,?)''', (app_date, patient_id, department_id, doc_id, survey)).lastrowid
        db.commit()
        return redirect(url_for('appointment.appointments'))






