import datetime
import functools
import sqlite3
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from dbfunc import connect_db,match_user_pwd,disconnect_db,get_domain,insert_user_pwd
from dbfunc import databasePATH,check_repeat
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
    dicdep = {}
    for cnt in range(len(departments)):
        i,j = departments[cnt][0],departments[cnt][1]
        dicdep[i] = j
    #print(dicdep)

    doctorfromdepartments = db.execute('''
                                            SELECT doc_id,d.department_id
                                            FROM doctor d INNER JOIN department e ON d.department_id == e.department_id 
                                        ''').fetchall()
    dfddic={}
    for cnt in range(len(doctorfromdepartments)):
        i,j = doctorfromdepartments[cnt][0],doctorfromdepartments[cnt][1]
        if dfddic.get(j) == None:
            dfddic[j] = [i]
        else:
            dfddic[j].append(i)

    alldoc = db.execute('''
                            SELECT e_id,name,phone,email,graduate_school,degree,technical_title,specialty
                            FROM employees
                        ''').fetchall()

    docdic = {}
    for cnt in range(len(alldoc)):
        i, j,k,l,m,n,o,p = alldoc[cnt][0], alldoc[cnt][1],alldoc[cnt][2],alldoc[cnt][3],alldoc[cnt][4],alldoc[cnt][5],alldoc[cnt][6],alldoc[cnt][7]
        if docdic.get(i) == None:
            docdic[i] = [j,k,l,m,n,o,p]

    return render_template('patient2departments.html', name = username,sidebarItems=patientItems,alldepartments = dicdep,dfd = dfddic,docdic = docdic)

@bp.route('/patient/?<string:username>/change_inf/',methods=['GET','POST'])
def change_inf(username):
    patient_id = get_id(db,username)
    if request.method == "POST":
        DOB = request.form['DOB']
        user = request.form['username']
        phone = request.form['phone']
        email = request.form['email']
        pwd = request.form['pwd']
        repwd = request.form['repwd']
        if pwd != repwd:
            flash('password is not equal to confirm_password!')
            return redirect(url_for('patient.patient'))
        if check_repeat(db, user):
            flash('The username already exists')
            return redirect(url_for('patient.patient'))
        if pwd != "NULL":
            db.execute('''UPDATE login_inf 
            SET username = ?, password=?
            WHERE username = ?''', (user, pwd, username))
            db.execute(
                "UPDATE patient SET DOB=?,phone=?,email=?,username=?,password=? WHERE patient_id=?",
                (DOB, phone, email, user, pwd, patient_id))
            db.commit()
        else:
            db.execute('''UPDATE login_inf 
                        SET username = ?
                        WHERE username = ?''', (user, username))
            db.execute(
                "UPDATE patient SET DOB=?,phone=?,email=?,username=? WHERE patient_id=?",
                (DOB, phone, email, user, patient_id))
            db.commit()
        flash('Successfully modified information')
        return redirect(url_for('patient.patient', username=user))


    allinf = db.execute('''
                                SELECT patient_id,name,DOB,passport,gender,phone,email,username
                                FROM patient
                                WHERE username =?   
                            ''',(username,)).fetchall()

    #print(allinf[0])
    i, j, k, l, m, n, o,p = allinf[0][0], allinf[0][1], allinf[0][2], allinf[0][3], allinf[0][4], allinf[0][5],allinf[0][6],allinf[0][7]

    infdic = [j, k, l, m, n, o,p]
    #print(infdic)
    return render_template('patient_change_inf.html', name = username,sidebarItems = patientItems,allinf = infdic)


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

@bp.route('/patient/?<string:username>/history',methods=['GET','POST'])
def history(username):
    patient_id = get_id(db, username)

    # 格式为(医生姓名，日期，药品名字，药品用量,体温，主诉，现病史，既往史，过敏史，发病时间，治疗情况，评估诊断)
    prescriptions_records = db.execute('''SELECT e.name,p.date,med_name,med_quantity,temperature,chief_complaint,
    present_illness_history,past_history, allergic_history， onset_date,current_treatment, diagnostic_assessment
    FROM prescription p INNER JOIN employees e ON e.e_id = p.doc_id
    INNER JOIN medicine m ON m.med_id = p.med_id 
    LEFT JOIN medical_record r ON p.app_id = r.app_id
    WHERE p.patient_id=? AND p.date<=? ORDER BY p.date DESC''', (patient_id, datetime.date.today())).fetchall()

    return render_template('xxx.html')




