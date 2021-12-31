import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from dbfunc import connect_db,match_user_pwd,disconnect_db,get_domain,insert_user_pwd,get_id
from dbfunc import databasePATH
from sliderbaritem import patientItems,doctorItems,chiefItems,adminItems,fever_doctorItems
from address import addressdic

bp = Blueprint('appointment', __name__)

db = connect_db(databasePATH)
APP_NUM = 20

def get_pname(db,user):
    cur = db.cursor()
    tt = cur.execute("select name \
                          from patient \
                          where username = '%s'" % user)
    for i in tt:
        return i[0]

def get_ename(db,user):
    cur = db.cursor()
    tt = cur.execute("select name \
                          from employees \
                          where username = '%s'" % user)
    for i in tt:
        return i[0]

def get_eid(db,user):
    cur = db.cursor()
    tt = cur.execute("select e_id \
                      from employees \
                      where username = '%s'" %user)
    for i in tt:
        return i[0]

def get_pid(db,user):
    cur = db.cursor()
    tt = cur.execute("select patient_id \
                      from patient \
                      where username = '%s'" %user)
    for i in tt:
        return i[0]

@bp.route('/doctor/?<string:username>/doctor_appointments',methods=['GET', 'POST'])
def doctor_appointments(username):
    doc_id = get_eid(db,username)
    realname = get_ename(db,username)
    appointments = db.execute("SELECT date , p.name, p.phone FROM appointment a \
                                INNER JOIN employees e ON e_id = doc_id \
                                INNER JOIN patient p ON a.patient_id = p.patient_id \
                                WHERE e_id=? ORDER BY date DESC", (doc_id,)).fetchall()

    return render_template('doctor_appointments.html',realname = realname,name = username,sidebarItems=doctorItems,appointments=appointments,hav = len(appointments))

@bp.route('/chief/?<string:username>/chief_appointments',methods=['GET', 'POST'])
def chief_appointments(username):
    doc_id = get_eid(db,username)
    realname = get_ename(db,username)
    appointments = db.execute("SELECT date , p.name, p.phone FROM appointment a \
                                INNER JOIN employees e ON e_id = doc_id \
                                INNER JOIN patient p ON a.patient_id = p.patient_id \
                                WHERE e_id=? ORDER BY date DESC", (doc_id,)).fetchall()

    return render_template('chief_appointments.html',realname = realname,name = username,sidebarItems=chiefItems,appointments=appointments,hav = len(appointments))

@bp.route('/patient/?<string:username>/patient_appointments',methods=['GET','POST'])
def patient_appointments(username):
    patient_id = get_pid(db,username)
    realname = get_pname(db, username)
    appointments = db.execute(
        "SELECT date, department_name, name\
        FROM appointment a LEFT JOIN employees e ON e_id = doc_id \
        LEFT JOIN department d ON d.department_id = a.department_id \
        WHERE patient_id=? ORDER BY date DESC", (patient_id,)
    ).fetchall()
    #print(patient_id)
    #print(appointments)
    return render_template('patient_appointments.html', realname = realname,name = username,sidebarItems=patientItems,appointments=appointments,hav = len(appointments))

@bp.route('/patient/?<string:username>/add_appointment',methods=['GET','POST'])
def patient_add_appointment(username):
    patient_id = get_pid(db,username)
    realname = get_pname(db, username)
    if request.method == 'POST':
        """api to add the appointment in the database"""
        patient_id = get_id(db,username)

        app_date = request.form['date']
        department_id = request.form['de_id']
        doc_id = request.form['doc_id']
        print(doc_id)
        survey = None
        error = None

        temperature = request.form['temperature']
        province = request.form['province']
        city = request.form['city']
        district = request.form['district']
        symptom = request.form['rm']#返回为有症状或无症状
        risk = request.form['r14']#返回为曾到或未曾到

        address = f'省：{province}；城市：{city}；区：{district}；'

        app_id = db.execute('''INSERT INTO appointment(date,patient_id,department_id,doc_id,temperature,address,symptom,risk)
                            VALUES(?,?,?,?,?,?,?,?)''',
                            (app_date, patient_id, department_id, doc_id, temperature,address,symptom,risk)).lastrowid
        db.commit()
        #先不提交
        
        

        return redirect(url_for('appointment.patient_appointments',username = username))


    name_and_passport_phone = db.execute('''
                                    SELECT name,passport,phone
                                    FROM patient
                                    where username=?
                                ''',(username,)).fetchall()
    npldic = {'name':name_and_passport_phone[0][0],'passport':name_and_passport_phone[0][1],'phone':name_and_passport_phone[0][2]}
    alldepartments = db.execute('''
                                    SELECT department_name,department_id
                                    FROM department
                                    WHERE department_id != 5
                                ''').fetchall()
    dicdep = {}
    for cnt in range(len(alldepartments)):
        i,j = alldepartments[cnt][0],alldepartments[cnt][1]
        if dicdep.get(i) == None:
            dicdep[i] = j

    alldoctor = db.execute('''
                                SELECT name,department_name,e_id
                                FROM appointment a 
                                INNER JOIN employees e ON e_id = doc_id
                                INNER JOIN department m ON a.department_id = m.department_id
                                WHERE m.department_id != 5
                            ''').fetchall()
    dicdoctor={}

    for cnt in range(len(alldoctor)):
        tempjudge = False
        i,j,k = alldoctor[cnt][0],alldoctor[cnt][1],alldoctor[cnt][2]
        if dicdoctor.get(j) == None:
            dicdoctor[j] = [[k,i]]
        else:
            for z in dicdoctor[j]:
                if z[0] == k:
                    tempjudge = True
            if tempjudge == False:
                dicdoctor[j].append([k,i])


    appointments = db.execute('''
                                SELECT date,name,department_name,e_id
                                FROM appointment a 
                                INNER JOIN employees e ON e_id = doc_id
                                INNER JOIN department m ON a.department_id = m.department_id
                                WHERE m.department_id != 5
                            ''').fetchall()
    #print(appointments)
    dic={}
    for cnt in range(len(appointments)):
        i,j,k,l = appointments[cnt][0],appointments[cnt][1],appointments[cnt][2],appointments[cnt][3]
        #print(i,j,k)
        if dic.get(i+','+k) == None:
            dic[i+','+k] = [[j,1,l]]
        else:
            for z in dic[i+','+k]:
                if z[2] == l:
                    z[1] = z[1] + 1
            if z[2] != l:
                dic[i+','+k].append([j,1,l])

    #print(dicdoctor)
    #print(dic)
    #print(npldic)
    return render_template('patient_add_appointment.html',addressdic = addressdic,realname = realname,name = username,sidebarItems = patientItems,appointments = dic,sum = APP_NUM,alldepartments = dicdep,alldoctor = dicdoctor,npldic = npldic)




@bp.route('/admin/?<string:username>/appointments',methods=['GET', 'POST'])
def admin_appointments(username):
    # 格式(app_id,日期，病人姓名，病人id，医生姓名，医生id，体温，症状，地址，是否到高风险地区)
    appointments = db.execute("SELECT app_id,date , p.name, a.patient_id, e.name,e_id, a.temperature,symptom,address,risk \
                                FROM appointment a \
                                INNER JOIN employees e ON e_id = doc_id \
                                INNER JOIN patient p ON a.patient_id = p.patient_id", ).fetchall()

    return render_template('admin_appointments.html',name = username,sidebarItems=adminItems,appointments=appointments,hav = len(appointments))


@bp.route('/admin/?<string:username>/add_appointment',methods=['GET', 'POST'])
def admin_add_appointment(username):
    # 给出病人列表
    patient_list = db.execute('''SELECT patient_id,name FROM patient''')
    # 给出部门列表
    all_departments = db.execute('''
                                        SELECT department_name,department_id
                                        FROM department
                                    ''').fetchall()
    # 给出医生列表
    all_doctors = db.execute('''
                                SELECT name,department_name,e_id
                                FROM appointment a 
                                INNER JOIN employees e ON e_id = doc_id
                                INNER JOIN department m ON a.department_id = m.department_id
                            ''').fetchall()

    if request.method == 'POST':
        """api to add the appointment in the database"""

        patient_id = request.form['patient']
        app_date = request.form['date']
        department_id = request.form['de_id']
        doc_id = request.form['doc_id']
        temperature = request.form['temperature']
        province = '北京'  # 未完成 先设为这个
        city = '市辖区'  # 未完成 先设为这个
        district = '海淀区'  # 未完成 先设为这个
        symptom = request.form['rm']  # 返回为有症状或无症状
        risk = request.form['r14']  # 返回为曾到或未曾到

        address = f'省：{province}；\n城市：{city}；\n区：{district}；'

        app_id = db.execute('''INSERT INTO appointment(date,patient_id,department_id,doc_id,temperature,address,symptom,risk)
                           VALUES(?,?,?,?,?,?,?,?)''',
                           (app_date, patient_id, department_id, doc_id, temperature,address,symptom,risk)).lastrowid
        db.commit()

        return redirect(url_for('appointment.admin_appointments',username=username))

    return render_template('patient_add_appointment.html', name = username,sidebarItems = adminItems,patient_list=patient_list,all_doctors=all_doctors,all_departments=all_departments)


@bp.route('/admin/?<string:username>/update_appointment/<id>', methods=['GET', 'POST'])
def admin_update_appointment(username,id):
    app_id = id
    # 给出部门列表
    all_departments = db.execute('''
                                        SELECT department_name,department_id
                                        FROM department
                                    ''').fetchall()
    # 给出医生列表
    all_doctors = db.execute('''
                                SELECT name,department_name,e_id
                                FROM appointment a 
                                INNER JOIN employees e ON e_id = doc_id
                                INNER JOIN department m ON a.department_id = m.department_id
                            ''').fetchall()

    if request.method == 'POST':
        """api to add the appointment in the database"""

        app_date = request.form['date']
        department_id = request.form['de_id']
        doc_id = request.form['doc_id']
        temperature = request.form['temperature']
        province = '北京'  # 未完成 先设为这个
        city = '市辖区'  # 未完成 先设为这个
        district = '海淀区'  # 未完成 先设为这个
        symptom = request.form['rm']  # 返回为有症状或无症状
        risk = request.form['r14']  # 返回为曾到或未曾到

        address = f'省：{province}；\n城市：{city}；\n区：{district}；'
        db.execute('''UPDATE appointment SET date=?,department_id=?,doc_id=?,temperature=?,address=?,symptom=?,risk=?
                    WHERE app_id=? '''
                   , (app_date, department_id, doc_id, temperature, address, symptom, risk,app_id))
        db.commit()

        return redirect(url_for('appointment.admin_appointments', username=username))

    return render_template('patient_add_appointment.html', name=username, sidebarItems=adminItems
                           , all_doctors=all_doctors, all_departments=all_departments)

@bp.route('/admin/?<string:username>/delete_appointment/<id>', methods=['GET', 'POST'])
def admin_delete_appointment(username):
    app_id = id

    db.execute("DELETE FROM appointment WHERE app_id=?", (app_id,))
    db.execute("DELETE FROM prescription WHERE app_id=?", (app_id,))
    db.execute("DELETE FROM medical_record WHERE app_id=?", (app_id,))

    db.commit()

    return redirect(url_for('appointment.admin_appointments', username=username))


@bp.route('/patient/?<string:username>/add_fever_appointment', methods=['GET', 'POST'])
def patient_add_fever_appointment(username):
    patient_id = get_pid(db, username)
    realname = get_pname(db, username)
    if request.method == 'POST':
        """api to add the appointment in the database"""
        patient_id = get_id(db, username)

        app_date = request.form['date']

        # 发热门诊预约只能选择发热门诊
        department_id = 5
        doc_id = request.form['doc_id']

        temperature = request.form['temperature']
        province = '北京'  # 未完成 先设为这个
        city = '市辖区'  # 未完成 先设为这个
        district = '海淀区'  # 未完成 先设为这个
        symptom = request.form['rm']  # 返回为有症状或无症状
        risk = request.form['r14']  # 返回为曾到或未曾到

        address = f'省：{province}；城市：{city}；区：{district}；'

        app_id = db.execute('''INSERT INTO appointment(date,patient_id,department_id,doc_id,temperature,address,symptom,risk)
                            VALUES(?,?,?,?,?,?,?,?)''',
                            (app_date, patient_id, department_id, doc_id, temperature,address,symptom,risk)).lastrowid
        db.commit()
        # 先不提交

        return redirect(url_for('appointment.patient_appointments',username=username))

    name_and_passport_phone = db.execute('''
                                    SELECT name,passport,phone
                                    FROM patient
                                    where username=?
                                ''', (username,)).fetchall()
    npldic = {'name': name_and_passport_phone[0][0], 'passport': name_and_passport_phone[0][1],
              'phone': name_and_passport_phone[0][2]}

    fever_doctor = db.execute('''
                                SELECT name,department_name,e_id
                                FROM appointment a 
                                INNER JOIN employees e ON e_id = doc_id
                                INNER JOIN department m ON a.department_id = m.department_id
                                WHERE m.department_id=5
                            ''').fetchall()
    dicdoctor = {}

    for cnt in range(len(fever_doctor)):
        tempjudge = False
        i, j, k = fever_doctor[cnt][0], fever_doctor[cnt][1], fever_doctor[cnt][2]
        if dicdoctor.get(j) == None:
            dicdoctor[j] = [[k, i]]
        else:
            for z in dicdoctor[j]:
                if z[0] == k:
                    tempjudge = True
            if tempjudge == False:
                dicdoctor[j].append([k, i])

    appointments = db.execute('''
                                SELECT date,name,department_name,e_id
                                FROM appointment a 
                                INNER JOIN employees e ON e_id = doc_id
                                INNER JOIN department m ON a.department_id = m.department_id
                                WHERE m.department_id=5
                            ''').fetchall()
    # print(appointments)
    dic = {}
    for cnt in range(len(appointments)):
        i, j, k, l = appointments[cnt][0], appointments[cnt][1], appointments[cnt][2], appointments[cnt][3]
        # print(i,j,k)
        if dic.get(i + ',' + k) == None:
            dic[i + ',' + k] = [[j, 1, l]]
        else:
            for z in dic[i + ',' + k]:
                if z[2] == l:
                    z[1] = z[1] + 1
            if z[2] != l:
                dic[i + ',' + k].append([j, 1, l])

    # print(dicdoctor)
    # print(dic)
    # print(npldic)
    return render_template('patient_add_fever_appointment.html', addressdic = addressdic,realname=realname, name=username, sidebarItems=patientItems,
                           appointments=dic, sum=APP_NUM, alldoctor=dicdoctor, npldic=npldic)


@bp.route('/fever_doctor/?<string:username>/doctor_appointments',methods=['GET', 'POST'])
def fever_appointments(username):
    doc_id = get_eid(db,username)
    realname = get_ename(db,username)
    # 多传入一个app_id用于转诊
    appointments = db.execute("SELECT app_id, date , p.name, p.phone FROM appointment a \
                                INNER JOIN employees e ON e_id = doc_id \
                                INNER JOIN patient p ON a.patient_id = p.patient_id \
                                WHERE e_id=? ORDER BY date DESC", (doc_id,)).fetchall()

    return render_template('fever_doctor_appointments.html',realname = realname,name = username,sidebarItems=fever_doctorItems,appointments=appointments,hav = len(appointments))


