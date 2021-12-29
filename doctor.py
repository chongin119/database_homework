import datetime
import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from dbfunc import connect_db,match_user_pwd,disconnect_db,get_domain,insert_user_pwd
from dbfunc import databasePATH
from sliderbaritem import doctorItems
bp = Blueprint('doctor', __name__)

db = connect_db(databasePATH)

def get_id(db,user):
    cur = db.cursor()
    tt = cur.execute("select e_id \
                      from employees \
                      where username = '%s'" %user)
    for i in tt:
        return i[0]

@bp.route('/doctor/?<string:username>', methods=['GET', 'POST'])
def doctor(username):
    if session.get(username) is not None:
        doctor = db.execute("SELECT * FROM employees WHERE username=?", (username,)).fetchall()
        return render_template('doctor.html', name=username, sidebarItems=doctorItems,doctor=doctor)
    return redirect(url_for('auth.login'))


@bp.route('/doctor/?<string:username>/history',methods=['GET', 'POST'])
def history(username):
    doc_id = get_id(db, username)
    prescription = db.execute("SELECT date , p.name, p.phone, med_id, med_quantity, med_name,  FROM prescription pre \
                                INNER JOIN patient p ON p.patient_id = pre.patient_id \
                                WHERE e_id=? ORDER BY date DESC", (doc_id,)).fetchall()
    return render_template('doctor_pre.html', prescription=prescription)

@bp.route('/doctor/?<string:username>/diagnosis',methods=['GET', 'POST'])
def diagnosis(username):
    doc_id = get_id(db, username)
    appointments = db.execute("SELECT date , p.name, p.phone FROM appointment a \
                                    INNER JOIN employees e ON e_id = doc_id \
                                    INNER JOIN patient p ON a.patient_id = p.patient_id \
                                    WHERE e_id=?,date = ? ORDER BY date DESC", (doc_id,datetime.date.today())).fetchall()
    return render_template('diagnosis.html',appointments=appointments)

@bp.route('/doctor/?<string:username>/diagnosis/<id>',methods=['GET', 'POST'])
def add_diagnosis(username, id):
    doc_id = get_id(db, username)
    app_id = id
    appointment_inf = db.execute("SELECT  a.patient_id,a.date FROM appointment a \
                                            INNER JOIN employees e ON e_id = doc_id \
                                            INNER JOIN patient p ON a.patient_id = p.patient_id \
                                            WHERE app_id=?", (app_id,)).fetchone()
    patient_id = appointment_inf[0]
    app_date = appointment_inf[1]
    if request.method == 'POST':
        # 该信息给出所有药品，药品的格式为(med_id,med_name,med_price),选药品的时候可以加一个下拉框选择
        medicine_inf = db.execute("SELECT  * FROM medicine").fetchall()

        temperature = request.form['temperature']
        chief_complaint = request.form['chc']
        present_illness_history = request.form['pih']
        past_history = request.form['phistory']
        allergic_history = request.form['ahistory']
        onset_date = request.form['ondate']
        current_treatment = request.form['ctreat']
        diagnosis_assessment = request.form['assess']
        med_id = request.form['medid']
        med_quantity = request.form['quantity']

        pre_id = db.execute('''INSERT INTO prescription(patient_id,doc_id,date,med_id,med_quantity,app_id)
                           VALUES(?,?,?,?,?,?)''',
                           (patient_id, doc_id, datetime.date.today(), med_id, med_quantity, app_id)).lastrowid
        m_id = db.execute('''INSERT INTO medical_record(patient_id,doc_id,date,temperature,chief_complaint
                            ,present_illness_history,past_history,allergic_history,onset_date,current_treatment
                            ,diagnosis_assessment,app_id)
                           VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',
                           (patient_id, doc_id, datetime.date.today(), temperature, chief_complaint,
                            present_illness_history,past_history,allergic_history,onset_date,
                            diagnosis_assessment,app_id)).lastrowid
        db.commit()
        return redirect(url_for('doctor.diagnosis', username=username))

    return render_template('add_diagnosis.html', name=username)








