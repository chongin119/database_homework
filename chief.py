import datetime
import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from dbfunc import connect_db,match_user_pwd,disconnect_db,get_domain,insert_user_pwd
from dbfunc import databasePATH,check_repeat
from sliderbaritem import chiefItems
db = connect_db(databasePATH)
bp = Blueprint('chief', __name__)

def get_id(db,user):
    cur = db.cursor()
    tt = cur.execute("select e_id \
                      from employees \
                      where username = '%s'" %user)
    for i in tt:
        return i[0]
def get_dept(db, id):
    department_id, department_name = db.execute("SELECT c.department_id, department_name \
                                From chief c INNER JOIN department de ON de.department_id = c.department_id \
                                WHERE chief_id=?",(id,)).fetchone()
    return department_id,department_name

@bp.route('/chief/?<string:username>', methods=['GET', 'POST'])
def chief(username):
    if session.get(username) is not None:
        chief_id = get_id(db, username)
        doctor = db.execute("SELECT * FROM employees WHERE username=?", (username,)).fetchall()
        department_id, department_name = get_dept(db, chief_id)
        return render_template('chief.html', name=username, sidebarItems=chiefItems,doctor=doctor,
                               department_name=department_name)
    return redirect(url_for('auth.login'))


@bp.route('/chief/?<string:username>/history',methods=['GET','POST'])
def history(username):
    doc_id = get_id(db, username)

    # 格式为(病人姓名，日期，药品名字，药品用量,体温，主诉，现病史，既往史，过敏史，发病时间，治疗情况，评估诊断)
    prescriptions_records = db.execute('''SELECT pat.name,p.date,med_name,med_quantity,temperature,chief_complaint,
    present_illness_history,past_history, allergic_history, onset_date,current_treatment, diagnostic_assessment
    FROM prescription p INNER JOIN patient pat ON pat.patient_id = p.patient_id
    INNER JOIN medicine m ON m.med_id = p.med_id 
    LEFT JOIN medical_record r ON p.app_id = r.app_id
    WHERE p.doc_id=? AND p.date<=? ORDER BY p.date DESC''', (doc_id, datetime.date.today())).fetchall()

    return render_template('xxx.html')

@bp.route('/chief/?<string:username>/change_inf/' , methods=['GET','POST'])
def change_inf(username):
    doc_id = get_id(db,username)
    if request.method == "POST":
        user = request.form['username']
        phone = request.form['phone']
        email = request.form['email']
        pwd = request.form['pwd']
        repwd = request.form['repwd']
        graduate_school = request.form['school']
        degree = request.form['degree']
        technical_title = request.form['title']
        specialty = request.form['specialty']
        if pwd != repwd:
            flash('password is not equal to confirm_password!')
            return redirect(url_for('doctor.doctor'))
        if check_repeat(db, user):
            flash('The username already exists')
            return redirect(url_for('doctor.doctor'))
        if pwd != "NULL":
            db.execute('''UPDATE login_inf 
            SET username = ?, password=?
            WHERE username = ?''', (user, pwd, username))
            db.execute(
                "UPDATE employees SET phone=?,email=?,username=?,password=?,graduate_school=?\
                , degree=?, technical_title=?,specialty=?\
                 WHERE e_id=?",
                (phone, email, user, pwd, graduate_school, degree, technical_title, specialty))
            db.commit()
        else:
            db.execute('''UPDATE login_inf 
                        SET username = ?
                        WHERE username = ?''', (user, username))
            db.execute(
                "UPDATE employees SET phone=?,email=?,username=?,graduate_school=?\
                , degree=?, technical_title=?,specialty=?\
                 WHERE e_id=?",
                (phone, email, user, graduate_school, degree, technical_title, specialty))
            db.commit()
        flash('Successfully modified information')
        return redirect(url_for('chief.chief', username=user))


    allinf = db.execute('''
                                SELECT e_id,name,passport,gender,phone,email,username,graduate_school
                                FROM employees
                                WHERE username =?   
                            ''',(username,)).fetchall()

    #print(allinf[0])
    i, j, k, l, m, n, o,p = allinf[0][0], allinf[0][1], allinf[0][2], allinf[0][3], allinf[0][4], allinf[0][5],allinf[0][6],allinf[0][7]

    infdic = [j, k, l, m, n, o,p]
    #print(infdic)
    return render_template('doctor_change_inf.html', name = username,sidebarItems = chiefItems,allinf = infdic)

@bp.route('/chief/?<string:username>/diagnosis',methods=['GET', 'POST'])
def diagnosis(username):
    doc_id = get_id(db, username)
    appointments = db.execute("SELECT date , p.name, p.phone FROM appointment a \
                                    INNER JOIN employees e ON e_id = doc_id \
                                    INNER JOIN patient p ON a.patient_id = p.patient_id \
                                    WHERE e_id=? and date = ? ORDER BY date DESC", (doc_id,datetime.date.today())).fetchall()
    return render_template('doctor_diagnosis.html',name=username, sidebarItems=chiefItems,appointments=appointments)

@bp.route('/chief/?<string:username>/diagnosis/<id>',methods=['GET', 'POST'])
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
        return redirect(url_for('chief.diagnosis', username=username))



    return render_template('add_diagnosis.html', name=username)

@bp.route('/chief/?<string:username>/update_department',methods=['GET', 'POST'])
def update_department(username):
    chief_id = get_id(db, username)
    department_id, department_name = get_dept(db, chief_id)
    if request.method == "POST":

        # department目前只有一个属性
        department_new_name = request.form['dept_name']
        db.execute('''UPDATE department 
                    SET department_name = ?
                    WHERE department_id = ?''', (department_new_name, department_id))
        flash('Successfully modified information')
        return redirect(url_for('chief.chief', username=username))
    return render_template('update_department.html',name=username, sidebarItems=chiefItems,department_name= department_name)


# 查看下属的病历和处方
@bp.route('/chief/?<string:username>/subordinate_record',methods=['GET','POST'])
def subordinate(username):
    chief_id = get_id(db, username)
    department_id, department_name = get_dept(db, chief_id)
    # 找出该部门的全部医生的病历和处方
    # 格式为(病人姓名，医生名字，日期，药品名字，药品用量,体温，主诉，现病史，既往史，过敏史，发病时间，治疗情况，评估诊断)
    prescriptions_records = db.execute('''SELECT pat.name, e.name, p.date,med_name,med_quantity,temperature,chief_complaint,
    present_illness_history,past_history, allergic_history, onset_date,current_treatment, diagnostic_assessment
    FROM prescription p INNER JOIN patient pat ON pat.patient_id = p.patient_id
    INNER JOIN employees e ON e.e_id = p.doc_id 
    INNER JOIN medicine m ON m.med_id = p.med_id 
    LEFT JOIN medical_record r ON p.app_id = r.app_id
    WHERE p.doc_id IN (SELECT doc_id FROM doctor WHERE department_id=?)
    AND p.date<=? ORDER BY p.date DESC''', (department_id,  datetime.date.today())).fetchall()

    return render_template('xxx.html')

# 查看科室看过病的病人的病历和处方
@bp.route('/chief/?<string:username>/patient_record',methods=['GET','POST'])
def patient_record(username):
    chief_id = get_id(db, username)
    department_id, department_name = get_dept(db, chief_id)
    # 找出该部门的全部病人的病历和处方
    # 格式为(病人姓名，医生名字，日期，药品名字，药品用量,体温，主诉，现病史，既往史，过敏史，发病时间，治疗情况，评估诊断)
    prescriptions_records = db.execute('''SELECT pat.name, e.name, p.date,med_name,med_quantity,r.temperature,chief_complaint,
    present_illness_history,past_history, allergic_history, onset_date,current_treatment, diagnostic_assessment
    FROM prescription p INNER JOIN patient pat ON pat.patient_id = p.patient_id
    INNER JOIN appointment a ON a.app_id = p.app_id
    INNER JOIN employees e ON e.e_id = p.doc_id 
    INNER JOIN medicine m ON m.med_id = p.med_id 
    LEFT JOIN medical_record r ON p.app_id = r.app_id
    WHERE a.department_id = ?
    AND p.date<=? ORDER BY p.date DESC''', (department_id,  datetime.date.today())).fetchall()

    return render_template('xxx.html')


# 查看下属医生
@bp.route('/chief/?<string:username>/doctors',methods=['GET','POST'])
def doctors(username):
    chief_id = get_id(db, username)
    department_id, department_name = get_dept(db, chief_id)
    # 找出该部门全部医生
    # 格式为(医生id,医生姓名，电话，邮箱)
    doctors = db.execute('''
                                    SELECT e_id,e.name,e.phone,e.email 
                                    FROM employees e 
                                    INNER JOIN doctor d ON d.doc_id = e_id 
                                    WHERE d.department_id=?
                                ''', (department_id,)).fetchall()


    return render_template('chief_doctors.html',name=username,  sidebarItems=chiefItems, doctors=doctors)


@bp.route('/chief/?<string:username>/doctors',methods=['GET','POST'])
def doctors(username):
    chief_id = get_id(db, username)
    department_id, department_name = get_dept(db, chief_id)
    # 找出该部门全部医生
    # 格式为(医生id,医生姓名，电话，邮箱...)
    doctors = db.execute('''
                                    SELECT e_id,e.name,e.phone,e.email,graduate_school,degree,technical_title,specialty
                                    FROM employees e 
                                    INNER JOIN doctor d ON d.doc_id = e_id 
                                    WHERE d.department_id=?
                                ''', (department_id,)).fetchall()


    return render_template('chief_doctors.html',name=username,  sidebarItems=chiefItems, doctors=doctors)

@bp.route('/chief/?<string:username>/add_doctor',methods=['GET','POST'])
def add_doctor(username):
    chief_id = get_id(db, username)
    department_id, department_name = get_dept(db, chief_id)
    # 找出该部门全部医生
    # 格式为(医生id,医生姓名，电话，邮箱...)
    doctors = db.execute('''
                                    SELECT e_id,e.name,e.phone,e.email,graduate_school,degree,technical_title,specialty
                                    FROM employees e 
                                    INNER JOIN doctor d ON d.doc_id = e_id 
                                    WHERE d.department_id=?
                                ''', (department_id,)).fetchall()



