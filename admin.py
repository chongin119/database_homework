import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from dbfunc import connect_db,match_user_pwd,disconnect_db,get_domain,insert_user_pwd
from dbfunc import databasePATH,check_repeat
from sliderbaritem import adminItems
import datetime
bp = Blueprint('admin', __name__)

db = connect_db(databasePATH)

def get_dept(db, id):
    department_id, department_name = db.execute("SELECT d.department_id, department_name \
                                From doctor d INNER JOIN department de ON de.department_id = d.department_id \
                                WHERE doc_id=?",(id,)).fetchone()
    return department_id,department_name

def get_id2pname(db,id):
    cur = db.cursor()
    tt = cur.execute("select name \
                              from patient \
                              where patient_id = '%s'" % id)
    for i in tt:
        return i[0]

@bp.route('/admin/?<string:username>',methods=['GET','POST'])
def admin(username):
    if session.get(username) is not None:
        # doctor = db.execute("SELECT * FROM employees WHERE username=?", (username,)).fetchall()
        return render_template('admin.html',name=username, sidebarItems=adminItems)
    return redirect(url_for('auth.login',username = username))

@bp.route('/admin/?<string:username>/patients',methods=['GET','POST'])
def patients(username):
    patients = db.execute("SELECT * FROM patient").fetchall()

    patdic = {}
    for i in patients:
        patdic[i[0]] = [i[1],i[2],i[3],i[4],i[5],i[6],i[7],i[8]]
    return render_template('admin_patients.html', patients=patdic,name=username,sidebarItems=adminItems,hav=len(patients))

@bp.route('/admin/?<string:username>/add_patient',methods=['GET','POST'])

def add_patient(username):
    if request.method == 'POST':
        """api to add the patient in the database"""
        real_name = request.form['realname']
        DOB = request.form['DOB']
        passport = request.form['passport']
        gender = request.form['gender']
        phone = request.form['phone']
        email = request.form['email']
        user = request.form['username']
        password = request.form['password']

        if check_repeat(db, user):
            flash('The username already exists')
            return redirect(url_for('admin.patients',username=username))

        request.form['pat_id'] = db.execute('''INSERT INTO patient(name,DOB,passport,gender,phone,email,username,password)
                    VALUES(?,?,?,?,?,?,?,?)''', (
        real_name, DOB, passport, gender, phone,email,user,password)).lastrowid
        login_id = db.execute('''INSERT INTO login_inf(username, password, domain)
                    VALUES(?,?,?)''',(user,password,2)).lastrowid
        db.commit()
        flash('Successfully add patient')
        return render_template('loading.html')

    return render_template('admin_patient_add_working.html',name=username)



@bp.route('/admin/?<string:username>/update_patients/<id>',methods=['POST','GET'])
def update_patient(username,id):
    # 待修改的病人的数据
    patient_id = id
    patient_inf = db.execute("SELECT * FROM patient WHERE patient_id=?", (id,)).fetchone()
    old_username = patient_inf[7]
    patname = get_id2pname(db,id)

    if request.method == 'POST':
        real_name = request.form['realname']
        DOB = request.form['DOB']
        passport = request.form['passport']
        gender = request.form['gender']
        phone = request.form['phone']
        email = request.form['email']
        user = request.form['username']
        password = request.form['pwd']

        if check_repeat(db, user) and old_username != user:
            flash('The username already exists')
            return redirect(url_for('admin.patients',username=username))
        if password != "NULL":
            db.execute('''UPDATE login_inf 
            SET username = ?, password=?
            WHERE username = ?''', (user, password, old_username))
            db.execute(
                "UPDATE patient SET name=?, DOB=?,passport=?,gender=?,phone=?,email=?,username=?,password=? \
                WHERE patient_id=?",
                (real_name,DOB, passport, gender,phone, email, user, password, patient_id))
            db.commit()
        else:
            db.execute('''UPDATE login_inf 
                        SET username = ?
                        WHERE username = ?''', (user, old_username))
            db.execute(
                "UPDATE patient SET name=?, DOB=?,passport=?,gender=?,phone=?,email=?,username=? \
                WHERE patient_id=?",
                (real_name, DOB, passport, gender, phone, email, user, patient_id))
            db.commit()
        flash('Successfully modified information')
        return render_template('loading.html')

    return render_template('admin_patient_change_working.html',allinf=patient_inf,name=username,patname = patname)

@bp.route('/admin/?<string:username>/delete_patient/<id>', methods=['GET', 'POST'])
def delete_patient(username, id):
    patient_id = id
    db.execute("DELETE FROM appointment WHERE patient_id=?", (patient_id,))
    db.execute("DELETE FROM login_inf WHERE username=(SELECT username from patient WHERE patient_id=?)", (patient_id,))
    db.execute("DELETE FROM patient WHERE patient_id=?", (patient_id,))
    db.commit()
    return render_template('loading.html')


@bp.route('/admin/?<string:username>/doctors',methods=['GET','POST'])
def doctors(username):
    # 找出全部医生，不包括科长
    # 格式为(医生id,医生姓名，电话，邮箱，科室)
    doctors = db.execute('''
                                    SELECT e_id,e.name,e.phone,e.email, department_name
                                    FROM employees e 
                                    INNER JOIN doctor d ON d.doc_id = e_id
                                    INNER JOIN department de ON d.department_id = de.department_id
                                    WHERE e_id NOT IN (SELECT chief_id FROM chief)  
                                ''', ).fetchall()

    return render_template('admin_doctors.html',name=username,  sidebarItems=adminItems, doctors=doctors)



@bp.route('/admin/?<string:username>/add_doctor',methods=['GET','POST'])
def add_doctor(username):
    # 给出科室信息，用于选择医生所属科室
    departments = db.execute("SELECT * FROM department").fetchall()

    if request.method == "POST":
        name = request.form['name']
        passport = request.form['passport']
        gender = request.form['gender']
        phone = request.form['phone']
        email = request.form['email']
        user = request.form['username']
        pwd = request.form['password']
        graduate_school = request.form['school']
        degree = request.form['degree']
        technical_title = request.form['title']
        specialty = request.form['specialty']
        department = request.form['department']

        department_id = db.execute('''SELECT department_id FROM department WHERE department_name = ?''',
                                   (department,)).fetchone()[0]
        if check_repeat(db, user):
            flash('The username already exists')
            return redirect(url_for('chief.doctors', username=username))
        e_id = db.execute('''
                    INSERT INTO employees(name,passport,gender,phone,email,username,password,
                    graduate_school,degree,technical_title,specialty) VALUES(?,?,?,?,?,?,?,?,?,?,?)'''
                   , (name,passport,gender,phone,email,user,pwd,graduate_school,degree,technical_title,specialty)).lastrowid
        db.execute('''
                            INSERT INTO doctor(doc_id,department_id) VALUES(?,?)'''
                   , (e_id,department_id))
        login_id = db.execute('''
                    INSERT INTO login_inf(username,password) VALUES(?,?)'''
                   , (user, pwd)).lastrowid

        db.commit()

        flash('Successfully add doctor')
        return redirect(url_for('admin.doctors', username=username))

    return render_template('chief_add_doctor.html',name=username,departments=departments)


@bp.route('/admin/?<string:username>/update_doctor/<id>', methods=['GET', 'POST'])
def update_doctor(username, id):
    doc_id = id
    department_id, department_name = get_dept(db, doc_id)
    doctor_inf = db.execute('''SELECT * FROM employees WHERE e_id=?'''
                            , (doc_id,)).fetchone()
    # 给出科室列表，用于修改科室
    departments = db.execute('''SELECT department_id,department_name FROM department'''
                            , (doc_id,)).fetchall()
    if request.method == "POST":
        name = request.form['name']
        passport = request.form['passport']
        gender = request.form['gender']
        phone = request.form['phone']
        email = request.form['email']
        user = request.form['username']
        pwd = request.form['password']
        repwd = request.form['repwd']
        graduate_school = request.form['school']
        degree = request.form['degree']
        technical_title = request.form['title']
        specialty = request.form['specialty']
        department_id = request.form['department']

        old_username = doctor_inf[6]
        if pwd != repwd:
            flash('password is not equal to confirm_password!')
            return redirect(url_for('admin.doctors',username=username))
        if check_repeat(db, user):
            flash('The username already exists')
            return redirect(url_for('admin.doctors'))
        if pwd != "NULL":
            db.execute('''UPDATE login_inf 
            SET username = ?, password=?
            WHERE username = ?''', (user, pwd, old_username))
            db.execute(
                "UPDATE employees SET name=?,passport=?,gender=?,phone=?,email=?,username=?,password=?,graduate_school=?\
                , degree=?, technical_title=?,specialty=?\
                 WHERE e_id=?",
                (name,passport,phone,gender, email, user, pwd, graduate_school, degree, technical_title, specialty,doc_id))
        else:
            db.execute('''UPDATE login_inf 
                        SET username = ?
                        WHERE username = ?''', (user, old_username))
            db.execute(
                "UPDATE employees SET phone=?,email=?,username=?,graduate_school=?\
                , degree=?, technical_title=?,specialty=?\
                 WHERE e_id=?",
                (phone, email, user, graduate_school, degree, technical_title, specialty,doc_id))
        db.execute('''
                               UPDATE doctor SET department_id=?
                               WHERE doc_id = ?
                               ''', (department_id, doc_id))
        db.commit()
        flash('Successfully modified information')
        return redirect(url_for('admin.doctors', username=username))

    return render_template('admin_update_doctor.html', name=username,doctor_inf=doctor_inf,departments=departments)

@bp.route('/admin/?<string:username>/delete_doctor/<id>', methods=['GET', 'POST'])
def delete_doctor(username, id):
    doc_id = id

    db.execute("DELETE FROM prescription WHERE doc_id=?", (doc_id,))
    db.execute("DELETE FROM medical_record WHERE doc_id=?", (doc_id,))
    db.execute("DELETE FROM appointment WHERE doc_id=?", (doc_id,))
    db.execute("DELETE FROM login_inf WHERE username=(SELECT username from employees WHERE e_id=?)", (doc_id,))
    db.execute("DELETE FROM doctor WHERE doc_id=?", (doc_id,))
    db.execute("DELETE FROM employees WHERE e_id=?", (doc_id,))

    db.commit()
    return redirect(url_for('admin.doctors',username=username))

@bp.route('/admin/?<string:username>/departments',methods=['GET','POST'])
def departments(username):

    # 找出全部科长和其科室的信息
    # 格式为(医生id,医生姓名，电话，邮箱，科室,科室_id,科室描述)
    chief_departments = db.execute('''
                                    SELECT e_id,e.name,e.phone,e.email, department_name,d.department_id,description
                                    FROM employees e 
                                    INNER JOIN doctor d ON d.doc_id = e_id
                                    INNER JOIN department de ON d.department_id = de.department_id
                                    WHERE e_id IN (SELECT chief_id FROM chief)  
                                ''', ).fetchall()

    return render_template('admin_departments.html',name=username,  sidebarItems=adminItems, department=chief_departments)


@bp.route('/admin/?<string:username>/add_department',methods=['GET','POST'])
def add_department(username):
    # 给出不是科长的医生作为候选的科长
    candidate_chief = db.execute('''
                                        SELECT e_id,e.name
                                        FROM employees e 
                                        WHERE e_id NOT IN (SELECT chief_id FROM chief)  
                                    ''', ).fetchall()

    if request.method == "POST":
        name = request.form['name']
        description = request.form['description']
        chief_id = request.form['chief']

        department_id = db.execute('''
        INSERT INTO department(department_name,description)
        VALUES(?,?)
        ''', (name,description)).lastrowid
        db.execute('''
                INSERT INTO department(chief_id,department_id)
                VALUES(?,?)
                ''', (chief_id, department_id))
        db.execute('''
                        UPDATE doctor SET department_id=?
                        WHERE doc_id = ?
                        ''', (department_id, chief_id))
        db.commit()

        flash('Successfully add department')
        return redirect(url_for('admin.departments', username=username))

    return render_template('chief_add_department.html',name=username,candidate_chief=candidate_chief)


@bp.route('/admin/?<string:username>/update_department/<id>', methods=['GET', 'POST'])
def update_department(username, id):
    department_id = id
    # 给出科长和科室的信息(科长id，科长姓名，科室名字，科室id，科室描述)
    chief_departments = db.execute('''
                                        SELECT e_id,e.name, department_name,d.department_id,description
                                        FROM employees e 
                                        INNER JOIN doctor d ON d.doc_id = e_id
                                        INNER JOIN department de ON d.department_id = de.department_id
                                        WHERE e_id IN (SELECT chief_id FROM chief)  AND d.department_id=?
                                    ''', (department_id,)).fetchone()
    # 给出不是科长的医生作为候选的科长
    candidate_chief = db.execute('''
                                            SELECT e_id,e.name
                                            FROM employees e 
                                            WHERE e_id NOT IN (SELECT chief_id FROM chief)  
                                        ''', ).fetchall()
    if request.method == "POST":
        name = request.form['name']
        description = request.form['description']
        chief_id = request.form['chief']

        db.execute('''UPDATE department SET department_name = ?,description=? WHERE department_id =?''',
                   (name, description, department_id))
        db.execute('''UPDATE chief SET chief_id = ?,department_id=? WHERE department_id =?''',
                   (chief_id, department_id, department_id))
        db.execute('''UPDATE doctor SET department_id=? WHERE doc_id =?''',
                   (chief_id, department_id, chief_id))

        flash('Successfully modified information')
        return redirect(url_for('admin.departments', username=username))

    return render_template('admin_update_department.html', name=username,chief_departments=chief_departments,candidate_chief=candidate_chief)


# @bp.route('/admin/?<string:username>/delete_department/<id>', methods=['GET', 'POST'])
# def delete_department(username, id):
#     department_id = id
#
#     db.execute("DELETE FROM chief WHERE department_id=?", (department_id,))
#     db.execute("DELETE FROM department WHERE department_id=?", (department_id,))
#
#     db.commit()
#     return redirect(url_for('admin.doctors',username=username))

@bp.route('/admin/?<string:username>/records',methods=['GET', 'POST'])
def records(username):
    # 给出所有病历和药方数据，格式(app_id,日期，病人姓名，病人id，医生姓名，医生id，体温，症状，地址，是否到高风险地区)
    prescriptions_records = db.execute('''SELECT p.app_id,pat.name, e.name, p.date,med_name,med_quantity,temperature,chief_complaint,
        present_illness_history,past_history, allergic_history, onset_date,current_treatment, diagnostic_assessment
        FROM prescription p INNER JOIN patient pat ON pat.patient_id = p.patient_id
        INNER JOIN employees e ON e.e_id = p.doc_id 
        INNER JOIN medicine m ON m.med_id = p.med_id 
        LEFT JOIN medical_record r ON p.app_id = r.app_id
        ORDER BY p.date DESC''').fetchall()

    return render_template('admin_records.html',name = username,sidebarItems=adminItems,records=prescriptions_records)

@bp.route('/admin/?<string:username>/add_record',methods=['GET', 'POST'])
def add_record(username):
    # 给出还没有处方和病历的就诊记录
    app_list = db.execute('''SELECT app_id
        FROM appointment 
        WHERE app_id NOT IN (SELECT app_id FROM medical_record)
        AND p.date<=? ORDER BY p.date DESC''', (datetime.date.today(),)).fetchall()

    if len(app_list)==0:
        flash('所有就诊都有记录')
        return redirect(url_for('admin.records', username=username))
    if request.method == "POST":
        app_id = request.form['appointment']
        appointment_inf = db.execute("SELECT  a.patient_id,a.date,a.doc_id FROM appointment a \
                                            INNER JOIN employees e ON e_id = doc_id \
                                            INNER JOIN patient p ON a.patient_id = p.patient_id \
                                            WHERE app_id=?", (app_id,)).fetchone()
        patient_id = appointment_inf[0]
        doc_id = appointment_inf[2]
        app_date = appointment_inf[1]

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
                                    ,diagnostic_assessment,app_id)
                                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',
                          (patient_id, doc_id, datetime.date.today(), temperature, chief_complaint,
                           present_illness_history, past_history, allergic_history, onset_date, current_treatment,
                           diagnosis_assessment, app_id)).lastrowid
        db.commit()
        flash('Successfully add record')
        return redirect(url_for('admin.records', username=username))
    medicine_inf = db.execute("SELECT  * FROM medicine").fetchall()
    meddic = {}

    for i in medicine_inf:
        meddic[i[0]] = i[1]
    return render_template('admin_add_record.html', name=username, meddic=meddic)


@bp.route('/admin/?<string:username>/update_record/<id>',methods=['GET', 'POST'])
def update_record(username, id):
    app_id = id


    # 给出该病历和处方的信息
    prescription_record = db.execute('''SELECT p.app_id,pat.name, e.name, p.date,med_name,med_quantity,temperature,chief_complaint,
        present_illness_history,past_history, allergic_history, onset_date,current_treatment, diagnostic_assessment
        FROM prescription p INNER JOIN patient pat ON pat.patient_id = p.patient_id
        INNER JOIN employees e ON e.e_id = p.doc_id 
        INNER JOIN medicine m ON m.med_id = p.med_id 
        LEFT JOIN medical_record r ON p.app_id = r.app_id
        WHERE p.app_id = ?
        AND p.date<=? ORDER BY p.date DESC''', (app_id, datetime.date.today())).fetchone()
    # 给出药的信息
    medicine_inf = db.execute("SELECT  * FROM medicine").fetchall()
    if request.method == "POST":

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

        db.execute(
            "UPDATE medical_record SET temperature=?,chief_complaint=?,present_illness_history=?,past_history=?\
            ,allergic_history=?,onset_date=?,current_treatment=?,diagnosis_assessment\
            , degree=?, technical_title=?,specialty=?\
             WHERE app_id=?",
            (temperature, chief_complaint, present_illness_history, past_history, allergic_history,
             onset_date, current_treatment, diagnosis_assessment, app_id))
        db.execute('''UPDATE prescription SET med_id = ?,med_quantity=?
                        WHERE app_id=?'''
                   , (med_id, med_quantity, app_id))
        db.commit()
        flash('Successfully modified information')
        return redirect(url_for('admin.records'))

    return render_template('admin_update_record.html', prescription_record=prescription_record, name=username,medicine_inf=medicine_inf)



@bp.route('/admin/?<string:username>/delete_appointment/<id>', methods=['GET', 'POST'])
def delete_record(username, id):
    app_id = id
    db.execute("DELETE FROM prescription WHERE app_id=?", (app_id,))
    db.execute("DELETE FROM medical_record WHERE app_id=?", (app_id,))

    db.commit()

    return redirect(url_for('admin.records', username=username))


