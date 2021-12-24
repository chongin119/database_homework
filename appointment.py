import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from dbfunc import connect_db,match_user_pwd,disconnect_db,get_domain,insert_user_pwd
from dbfunc import databasePATH
from sliderbaritem import patientItems
bp = Blueprint('appointment', __name__)

db = connect_db(databasePATH)
APP_NUM = 20
def get_id(db,user):
    cur = db.cursor()
    tt = cur.execute("select patient_id \
                      from patient \
                      where username = '%s'" %user)
    for i in tt:
        return i[0]

@bp.route('/patient/?<string:username>/patient_appointments',methods=['GET','POST'])
def patient_appointments(username):
    patient_id = get_id(db,username)
    appointments = db.execute(
        "SELECT date, department_name, name\
        FROM appointment a LEFT JOIN employees e ON e_id = doc_id \
        LEFT JOIN department d ON d.department_id = a.department_id \
        WHERE patient_id=? ORDER BY date DESC", (patient_id,)
    ).fetchall()
    print(patient_id)
    print(appointments)
    return render_template('patient_appointments.html', name = username,sidebarItems=patientItems,appointments=appointments,hav = len(appointments))

@bp.route('/patient/?<string:username>/add_appointment',methods=['GET','POST'])
def patient_add_appointment(username):
    patient_id = get_id(db,username)

    if request.method == 'POST':
        """api to add the appointment in the database"""
        app_date = request.form['date']
        patient_id = get_id(db,username)
        department_id = request.form['de_id']
        doc_id = request.form['doc_id']
        survey = None
        error = None
        number = db.execute("SELECT count(*) FROM appointment a \
                                INNER JOIN employees e ON e_id = doc_id \
                                INNER JOIN patient p ON a.patient_id = p.patient_id \
                                WHERE e_id=? ORDER BY date DESC", (doc_id,)).fetchall()
        number = number[0][0]
        if number >= APP_NUM:
            error = "The doctor's appointments are full that day"
        if error is not None:
            flash(error)
            redirect(url_for('appointment.patient_appointments'))
        app_id = db.execute('''INSERT INTO appointment(date,patient_id,department_id,doc_id,epidemic_survey)
                    VALUES(?,?,?,?,?)''', (app_date, patient_id, department_id, doc_id, survey)).lastrowid
        db.commit()
        return redirect(url_for('appointment.patient_appointments'))

    return render_template('patient_add_appointment.html', name = username,sidebarItems=patientItems)







