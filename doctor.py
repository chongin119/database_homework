import datetime
import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from dbfunc import connect_db,match_user_pwd,disconnect_db,get_domain,insert_user_pwd
from dbfunc import databasePATH,check_repeat
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
def get_dept(db, id):
    department_id, department_name = db.execute("SELECT d.department_id, department_name \
                                From doctor d INNER JOIN department de ON de.department_id = d.department_id \
                                WHERE doc_id=?",(id,)).fetchone()
    return department_id,department_name

@bp.route('/doctor/?<string:username>', methods=['GET', 'POST'])
def doctor(username):
    if session.get(username) is not None:
        doctor = db.execute("SELECT * FROM employees WHERE username=?", (username,)).fetchall()
        return render_template('doctor.html', name=username, sidebarItems=doctorItems,doctor=doctor)
    return redirect(url_for('auth.login'))


@bp.route('/doctor/?<string:username>/history',methods=['GET','POST'])
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

@bp.route('/doctor/?<string:username>/change_inf/' , methods=['GET','POST'])
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
                (phone, email, user, pwd, graduate_school, degree, technical_title, specialty,doc_id))
            db.commit()
        else:
            db.execute('''UPDATE login_inf 
                        SET username = ?
                        WHERE username = ?''', (user, username))
            db.execute(
                "UPDATE employees SET phone=?,email=?,username=?,graduate_school=?\
                , degree=?, technical_title=?,specialty=?\
                 WHERE e_id=?",
                (phone, email, user, graduate_school, degree, technical_title, specialty,doc_id))
            db.commit()
        flash('Successfully modified information')
        return redirect(url_for('doctor.doctor', username=user))


    allinf = db.execute('''
                                SELECT e_id,name,passport,gender,phone,email,username,graduate_school
                                FROM employees
                                WHERE username =?   
                            ''',(username,)).fetchall()

    #print(allinf[0])
    i, j, k, l, m, n, o,p = allinf[0][0], allinf[0][1], allinf[0][2], allinf[0][3], allinf[0][4], allinf[0][5],allinf[0][6],allinf[0][7]

    infdic = [j, k, l, m, n, o,p]
    #print(infdic)
    return render_template('doctor_change_inf.html', name = username,sidebarItems = doctorItems,allinf = infdic)

@bp.route('/doctor/?<string:username>/diagnosis',methods=['GET', 'POST'])
def diagnosis(username):
    doc_id = get_id(db, username)
    appointments = db.execute("SELECT date , p.name, p.phone ,a.app_id FROM appointment a \
                                    INNER JOIN employees e ON e_id = doc_id \
                                    INNER JOIN patient p ON a.patient_id = p.patient_id \
                                    WHERE e_id=? and date = ? ORDER BY date DESC", (doc_id,datetime.date.today())).fetchall()
    total_app_num = len(appointments)
    done_app_num = db.execute("SELECT COUNT(a.app_id) FROM appointment a \
                                    INNER JOIN employees e ON e_id = a.doc_id \
                                    INNER JOIN patient p ON a.patient_id = p.patient_id \
                                    INNER JOIN medical_record r ON r.app_id = a.app_id\
                                    WHERE e_id=? and a.date = ?", (doc_id,datetime.date.today())).fetchone()[0]
    undo_app_num = total_app_num - done_app_num
    #print(appointments)

    allmedrec = db.execute('''
                            SELECT app_id 
                            FROM medical_record
                            ''').fetchall()

    las = db.cursor().execute('''
                                SELECT max(app_id) 
                                FROM appointment
                                ''').fetchall()


    finishdic = {}
    allmedrecc = []
    for i in allmedrec:
        allmedrecc.append(i[0])

    #print(allmedrecc)
    records = {}
    for cnt in range(len(appointments)):
        i,j,k,l = appointments[cnt][0],appointments[cnt][1],appointments[cnt][2],appointments[cnt][3]
        records[cnt] = [i,j,k,l]

    for cnt in range(1,las[0][0]+1):
        if l in allmedrecc:
            finishdic[cnt] = 'disabled'
        else:
            finishdic[cnt] = ""
    #print(finishdic)

    return render_template('doctor_diagnosis.html',name=username, sidebarItems=doctorItems,records=records,hav=len(appointments),finishdic = finishdic)

@bp.route('/doctor/?<string:username>/add_diagnosis/<id>',methods=['GET', 'POST'])
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
        #medicine_inf = db.execute("SELECT  * FROM medicine").fetchall()

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
                            present_illness_history,past_history,allergic_history,onset_date,current_treatment,
                            diagnosis_assessment,app_id)).lastrowid
        #db.commit()

        return render_template('doctor_diagnosis.html')

    medicine_inf = db.execute("SELECT  * FROM medicine").fetchall()
    meddic = {}

    for i in medicine_inf:
        meddic[i[0]] = i[1]
    return render_template('doctor_diagnosis_working.html', name=username,appid = app_id,meddic = meddic)








