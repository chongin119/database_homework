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

def get_name(db,user):
    cur = db.cursor()
    tt = cur.execute("select name \
                          from employees \
                          where username = '%s'" % user)
    for i in tt:
        return i[0]

def get_id2name(db,id):
    cur = db.cursor()
    tt = cur.execute("select name \
                              from employees \
                              where e_id = '%s'" % id)
    for i in tt:
        return i[0]

def get_id2user(db,id):
    cur = db.cursor()
    tt = cur.execute("select username \
                              from employees \
                              where e_id = '%s'" % id)
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
        realname = get_name(db,username)
        return render_template('chief.html', realname = realname,name=username, sidebarItems=chiefItems,chief=doctor,
                               department_name=department_name)
    return redirect(url_for('auth.login'))


@bp.route('/chief/?<string:username>/history',methods=['GET','POST'])
def history(username):
    doc_id = get_id(db, username)
    realname = get_name(db, username)
    # 格式为(病人姓名，日期，药品名字，药品用量,体温，主诉，现病史，既往史，过敏史，发病时间，治疗情况，评估诊断)
    prescriptions_records = db.execute('''SELECT pat.patient_id,pat.name,p.date,med_name,med_quantity,temperature,chief_complaint,
    present_illness_history,past_history, allergic_history, onset_date,current_treatment, diagnostic_assessment
    FROM prescription p INNER JOIN patient pat ON pat.patient_id = p.patient_id
    INNER JOIN medicine m ON m.med_id = p.med_id 
    LEFT JOIN medical_record r ON p.app_id = r.app_id
    WHERE p.doc_id=? AND p.date<=? ORDER BY p.date DESC''', (doc_id, datetime.date.today())).fetchall()

    recordsfordoc = {}
    for cnt in range(len(prescriptions_records)):
        i1, i2, i3, i4, i5, i6, i7, i8, i9, i10, i11, i12, i13 = prescriptions_records[cnt][0], \
                                                                 prescriptions_records[cnt][1], \
                                                                 prescriptions_records[cnt][2], \
                                                                 prescriptions_records[cnt][3], \
                                                                 prescriptions_records[cnt][4], \
                                                                 prescriptions_records[cnt][5], \
                                                                 prescriptions_records[cnt][6], \
                                                                 prescriptions_records[cnt][7], \
                                                                 prescriptions_records[cnt][8], \
                                                                 prescriptions_records[cnt][9], \
                                                                 prescriptions_records[cnt][10], \
                                                                 prescriptions_records[cnt][11], \
                                                                 prescriptions_records[cnt][12]
        if recordsfordoc.get(i1) == None:
            recordsfordoc[i1] = [[i2, i3, i4, i5, i6, i7, i8, i9, i10, i11, i12, i13]]
        else:
            recordsfordoc[i1].append([i2, i3, i4, i5, i6, i7, i8, i9, i10, i11, i12, i13])

    # print(recordsfordoc)

    records = {}
    for cnt in range(len(prescriptions_records)):
        i1, i2, i3, i4, i5, i6, i7, i8, i9, i10, i11, i12, i13 = prescriptions_records[cnt][0], \
                                                                 prescriptions_records[cnt][1], \
                                                                 prescriptions_records[cnt][2], \
                                                                 prescriptions_records[cnt][3], \
                                                                 prescriptions_records[cnt][4], \
                                                                 prescriptions_records[cnt][5], \
                                                                 prescriptions_records[cnt][6], \
                                                                 prescriptions_records[cnt][7], \
                                                                 prescriptions_records[cnt][8], \
                                                                 prescriptions_records[cnt][9], \
                                                                 prescriptions_records[cnt][10], \
                                                                 prescriptions_records[cnt][11], \
                                                                 prescriptions_records[cnt][12]
        if records.get(cnt) == None:
            cntt = countfunc(records, i1)
            records[cnt] = [i1, i2, i3, i4, i5, i6, i7, i8, i9, i10, i11, i12, i13, cntt]

    # print(records)
    alldoctor = db.execute('''
                                            SELECT name,patient_id
                                            FROM patient 
                                        ''').fetchall()
    dicdoctor = {}

    for cnt in range(len(alldoctor)):
        i, j = alldoctor[cnt][0], alldoctor[cnt][1]
        if dicdoctor.get(j) == None:
            dicdoctor[j] = i

    return render_template('chief_history.html',realname = realname,name = username,sidebarItems = chiefItems,alldoc = dicdoctor,records = records,rfordoc = recordsfordoc,hav = len(records))

@bp.route('/chief/?<string:username>/change_inf/' , methods=['GET','POST'])
def change_inf(username):
    doc_id = get_id(db,username)
    realname = get_name(db,username)
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
            return redirect(url_for('chief.change_inf', username=username))
        if check_repeat(db, user) and user != username :
            flash('The username already exists')
            return redirect(url_for('chief.change_inf', username=username))
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
        return redirect(url_for('chief.chief', username=user))


    allinf = db.execute('''
                                SELECT e_id,name,passport,gender,phone,email,username,graduate_school,degree,technical_title,specialty
                                FROM employees
                                WHERE username =?   
                            ''',(username,)).fetchall()

    #print(allinf[0])
    i, j, k, l, m, n, o,p,q,s,t = allinf[0][0], allinf[0][1], allinf[0][2], allinf[0][3], allinf[0][4], allinf[0][5],allinf[0][6],allinf[0][7],allinf[0][8],allinf[0][9],allinf[0][10]

    infdic = [j, k, l, m, n, o,p,q,s,t]
    #print(infdic)
    return render_template('chief_change_inf.html', name = username,realname =realname,sidebarItems = chiefItems,allinf = infdic)

@bp.route('/chief/?<string:username>/diagnosis',methods=['GET', 'POST'])
def diagnosis(username):
    doc_id = get_id(db, username)
    realname = get_name(db, username)
    appointments = db.execute("SELECT date , p.name, p.phone,a.app_id FROM appointment a \
                                    INNER JOIN employees e ON e_id = doc_id \
                                    INNER JOIN patient p ON a.patient_id = p.patient_id \
                                    WHERE e_id=? and date = ? ORDER BY date DESC", (doc_id,datetime.date.today())).fetchall()
    total_app_num = len(appointments)
    done_app_num = db.execute("SELECT COUNT(a.app_id) FROM appointment a \
                                        INNER JOIN employees e ON e_id = a.doc_id \
                                        INNER JOIN patient p ON a.patient_id = p.patient_id \
                                        INNER JOIN medical_record r ON r.app_id = a.app_id\
                                        WHERE e_id=? and a.date = ?", (doc_id, datetime.date.today())).fetchone()[0]
    undo_app_num = total_app_num - done_app_num
    # print(appointments)

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


    # print(allmedrecc)
    records = {}
    for cnt in range(len(appointments)):
        i, j, k, l = appointments[cnt][0], appointments[cnt][1], appointments[cnt][2], appointments[cnt][3]
        records[cnt] = [i, j, k, l]

    for cnt in range(1, las[0][0] + 1):
        if cnt in allmedrecc:
            finishdic[cnt] = 'disabled'
        else:
            finishdic[cnt] = ""
    #print(finishdic)
    return render_template('chief_diagnosis.html',realname = realname,name=username, sidebarItems=chiefItems,records=records,hav=len(appointments),finishdic = finishdic,total = total_app_num,undo = undo_app_num,done = done_app_num)

@bp.route('/chief/?<string:username>/add_diagnosis/<id>',methods=['GET', 'POST'])
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
                            ,diagnostic_assessment,app_id)
                           VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',
                           (patient_id, doc_id, datetime.date.today(), temperature, chief_complaint,
                            present_illness_history,past_history,allergic_history,onset_date,current_treatment,
                            diagnosis_assessment,app_id)).lastrowid
        med_price = db.execute('''SELECT med_price FROM medicine m INNER JOIN prescription r 
                                ON m.med_id = r.med_id WHERE m.med_id = ?''', (med_id,)).fetchone()[0]
        bill_id = db.execute('''INSERT INTO bill(patient_id, app_id, cost) VALUES(?,?,?)'''
                             , (patient_id, app_id, med_price * med_quantity)).lastrowid
        db.commit()
        return render_template('loading.html')

    medicine_inf = db.execute("SELECT  * FROM medicine").fetchall()
    meddic = {}

    for i in medicine_inf:
        meddic[i[0]] = i[1]

    return render_template('chief_diagnosis_working.html', name=username,appid = app_id,meddic = meddic)

@bp.route('/chief/?<string:username>/update_department',methods=['GET', 'POST'])
def update_department(username):
    chief_id = get_id(db, username)
    department_id, department_name = get_dept(db, chief_id)
    realname = get_name(db,username)
    des = db.execute('''
                    SELECT description
                    FROM department
                    WHERE department_id = ?
                    ''',(department_id,)).fetchall()
    des = des[0][0]
    if request.method == "POST":

        # department目前只有两个属性
        department_new_name = request.form['dept_name']
        description = request.form['description']
        db.execute('''UPDATE department 
                    SET department_name = ?, description=?
                    WHERE department_id = ?''', (department_new_name,description, department_id))
        flash('Successfully modified information')
        return redirect(url_for('chief.chief', username=username))
    return render_template('chief_change_depinf.html',realname = realname,name=username, sidebarItems=chiefItems,department_name= department_name,des=des)


# 查看下属的病历和处方
@bp.route('/chief/?<string:username>/subordinate_record',methods=['GET','POST'])
def subordinate(username):
    chief_id = get_id(db, username)
    department_id, department_name = get_dept(db, chief_id)
    realname = get_name(db,username)
    # 找出该部门的全部医生的病历和处方
    # 格式为(医生id,病历对应预约id，病人姓名，日期，药品名字，药品用量,体温，主诉，现病史，既往史，过敏史，发病时间，治疗情况，评估诊断，医生名字)
    prescriptions_records = db.execute('''SELECT e.e_id,p.app_id,pat.name,  p.date,med_name,med_quantity,temperature,chief_complaint,
    present_illness_history,past_history, allergic_history, onset_date,current_treatment, diagnostic_assessment,e.name
    FROM prescription p INNER JOIN patient pat ON pat.patient_id = p.patient_id
    INNER JOIN employees e ON e.e_id = p.doc_id 
    INNER JOIN medicine m ON m.med_id = p.med_id 
    LEFT JOIN medical_record r ON p.app_id = r.app_id
    WHERE p.doc_id IN (SELECT doc_id FROM doctor WHERE department_id=?)
    AND p.date<=? ORDER BY p.date DESC''', (department_id,  datetime.date.today())).fetchall()

    recordsfordoc = {}
    for cnt in range(len(prescriptions_records)):
        i1, i2, i3, i4, i5, i6, i7, i8, i9, i10, i11, i12, i13, i14, i15 = prescriptions_records[cnt][0], \
                                                                 prescriptions_records[cnt][1], \
                                                                 prescriptions_records[cnt][2], \
                                                                 prescriptions_records[cnt][3], \
                                                                 prescriptions_records[cnt][4], \
                                                                 prescriptions_records[cnt][5], \
                                                                 prescriptions_records[cnt][6], \
                                                                 prescriptions_records[cnt][7], \
                                                                 prescriptions_records[cnt][8], \
                                                                 prescriptions_records[cnt][9], \
                                                                 prescriptions_records[cnt][10], \
                                                                 prescriptions_records[cnt][11], \
                                                                 prescriptions_records[cnt][12], \
                                                                 prescriptions_records[cnt][13], \
                                                                 prescriptions_records[cnt][14]

        temp = {}
        if i1 == chief_id:
            continue
        if recordsfordoc.get(i1) == None:
            temp[i2] = [i3, i4, i5, i6, i7, i8, i9, i10, i11, i12, i13,i14,i15]
            recordsfordoc[i1] = temp
        else:
            recordsfordoc[i1][i2] = [i3, i4, i5, i6, i7, i8, i9, i10, i11, i12, i13,i14,i15]

    alldoctor = db.execute('''
                                            SELECT name,e_id
                                            FROM employees inner join doctor on doc_id == e_id
                                            WHERE department_id =?
                                        ''',(department_id,)).fetchall()
    dicdoctor = {}

    for cnt in range(len(alldoctor)):
        i, j = alldoctor[cnt][0], alldoctor[cnt][1]
        if j == chief_id:
            continue
        if dicdoctor.get(j) == None:
            dicdoctor[j] = i

    #print()
    '''for i in recordsfordoc:
        print(i)
        print(recordsfordoc[i])'''

    return render_template('chief_subordinate_appo.html',realname = realname,name=username, sidebarItems=chiefItems,allrecords = recordsfordoc,alldoc = dicdoctor)

@bp.route('/chief/?<string:username>/update_record/<id>',methods=['GET','POST'])
def update_record(username, id):
    chief_id = get_id(db, username)
    app_id = id
    department_id, department_name = get_dept(db, chief_id)

    # 给出该病历和处方的信息
    # 格式为(医生id,病历对应预约id，病人姓名，日期，药品名字，药品用量,体温，主诉，现病史，既往史，过敏史，发病时间，治疗情况，评估诊断，医生名字)
    prescription_record = db.execute('''SELECT e.e_id,p.app_id,pat.name, p.date,med_name,med_quantity,temperature,chief_complaint,
    present_illness_history,past_history, allergic_history, onset_date,current_treatment, diagnostic_assessment, e.name
    FROM prescription p INNER JOIN patient pat ON pat.patient_id = p.patient_id
    INNER JOIN employees e ON e.e_id = p.doc_id 
    INNER JOIN medicine m ON m.med_id = p.med_id 
    LEFT JOIN medical_record r ON p.app_id = r.app_id
    WHERE p.app_id = ?
    AND p.date<=? ORDER BY p.date DESC''', (app_id,  datetime.date.today())).fetchone()

    print(prescription_record)
    if request.method == "POST":
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

        db.execute(
            "UPDATE medical_record SET temperature=?,chief_complaint=?,present_illness_history=?,past_history=?\
            ,allergic_history=?,onset_date=?,current_treatment=?,diagnostic_assessment = ?\
             WHERE app_id=?",
            (temperature, chief_complaint, present_illness_history, past_history, allergic_history,
             onset_date, current_treatment, diagnosis_assessment, app_id))
        db.execute('''UPDATE prescription SET med_id = ?,med_quantity=?
                    WHERE app_id=?'''
                   ,(med_id,med_quantity,app_id))
        med_price = db.execute('''SELECT med_price FROM medicine m INNER JOIN prescription r 
                                ON m.med_id = r.med_id WHERE m.med_id = ?''', (med_id,)).fetchone()[0]
        db.execute('''UPDATE bill SET COST = ? WHERE app_id = ?''', (med_price * med_quantity, app_id))

        db.commit()
        flash('Successfully modified information')
        return render_template('loading.html')

    medicine_inf = db.execute("SELECT  * FROM medicine").fetchall()
    meddic = {}

    for i in medicine_inf:
        meddic[i[0]] = i[1]
    return render_template('chief_subordinate_working.html',inf=prescription_record,name=username,appid = app_id, meddic=meddic)

# 查看下属医生
@bp.route('/chief/?<string:username>/doctors',methods=['GET','POST'])
def doctors(username):
    chief_id = get_id(db, username)
    department_id, department_name = get_dept(db, chief_id)
    realname = get_name(db,username)
    # 找出该部门全部医生
    # 格式为(医生id,医生姓名，电话，邮箱)
    doctors = db.execute('''
                                    SELECT e_id,e.name,e.phone,e.email,e.username 
                                    FROM employees e 
                                    INNER JOIN doctor d ON d.doc_id = e_id 
                                    WHERE d.department_id=?
                                ''', (department_id,)).fetchall()

    docdic = {}
    for i in doctors:
        if i[0] == chief_id:
            continue
        if docdic.get(i[0]) == None:
            docdic[i[0]] = [i[1],i[2],i[3],i[4]]

    return render_template('chief_doctors.html',realname = realname,name=username,  sidebarItems=chiefItems, doctors=docdic)




@bp.route('/chief/?<string:username>/add_doctor',methods=['GET','POST'])
def add_doctor(username):
    chief_id = get_id(db, username)
    department_id, department_name = get_dept(db, chief_id)
    if request.method == "POST":
        name = request.form['name']
        passport = request.form['passport']
        gender = request.form['gender']
        phone = request.form['phone']
        email = request.form['email']
        user = request.form['username']
        pwd = request.form['pwd']
        graduate_school = request.form['school']
        degree = request.form['degree']
        technical_title = request.form['title']
        specialty = request.form['specialty']

        if check_repeat(db, user):
            flash('The username already exists')
            return redirect(url_for('chief.doctors'),username=username)
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

        flash('Successfully added information')
        return render_template('loading.html')

    return render_template('chief_doctors_add_working.html',name=username)


@bp.route('/chief/?<string:username>/update_doctor/<id>', methods=['GET', 'POST'])
def update_doctor(username, id):
    chief_id = get_id(db, username)
    doc_id = id

    docname = get_id2name(db, doc_id)
    docuser = get_id2user(db, doc_id)
    department_id, department_name = get_dept(db, chief_id)
    if request.method == "POST":
        name = request.form['name']
        passport = request.form['passport']
        gender = request.form['gender']
        phone = request.form['phone']
        email = request.form['email']
        user = request.form['username']
        pwd = request.form['pwd']
        repwd = request.form['repwd']
        graduate_school = request.form['school']
        degree = request.form['degree']
        technical_title = request.form['title']
        specialty = request.form['specialty']

        doctor_inf = db.execute('''SELECT username FROM employees WHERE e_id=?'''
                                ,(doc_id,)).fetchone()
        old_username = doctor_inf[0]
        if pwd != repwd:
            flash('password is not equal to confirm_password!')
            return render_template('loading.html')
        if check_repeat(db, user) and docuser != user:
            flash('The username already exists')
            return render_template('loading.html')
        if pwd != "NULL":
            db.execute('''UPDATE login_inf 
            SET username = ?, password=?
            WHERE username = ?''', (user, pwd, old_username))
            db.execute(
                "UPDATE employees SET name=?,passport=?,gender=?,phone=?,email=?,username=?,password=?,graduate_school=?\
                , degree=?, technical_title=?,specialty=?\
                 WHERE e_id=?",
                (name,passport,phone,gender, email, user, pwd, graduate_school, degree, technical_title, specialty,doc_id))
            db.commit()
        else:
            db.execute('''UPDATE login_inf 
                        SET username = ?
                        WHERE username = ?''', (user, old_username))
            db.execute(
                "UPDATE employees SET phone=?,email=?,username=?,graduate_school=?\
                , degree=?, technical_title=?,specialty=?\
                 WHERE e_id=?",
                (phone, email, user, graduate_school, degree, technical_title, specialty,doc_id))
            db.commit()
        flash('Successfully modified information')
        return render_template('loading.html')

    allinf = db.execute('''
                                    SELECT e_id,name,passport,gender,phone,email,username,graduate_school,degree,technical_title,specialty
                                    FROM employees
                                    WHERE username =?   
                                ''', (docuser,)).fetchall()

    # print(allinf[0])
    i, j, k, l, m, n, o, p, q, s, t = allinf[0][0], allinf[0][1], allinf[0][2], allinf[0][3], allinf[0][4], allinf[0][
        5], allinf[0][6], allinf[0][7], allinf[0][8], allinf[0][9], allinf[0][10]

    infdic = [j, k, l, m, n, o, p, q, s, t]

    return render_template('chief_doctors_change_working.html', name=username,docname = docname,allinf = infdic)

@bp.route('/chief/?<string:username>/delete_doctor/<id>', methods=['GET', 'POST'])
def delete_doctor(username, id):
    doc_id = id

    db.execute("DELETE FROM prescription WHERE doc_id=?", (doc_id,))
    db.execute("DELETE FROM medical_record WHERE doc_id=?", (doc_id,))
    db.execute("DELETE FROM appointment WHERE doc_id=?", (doc_id,))
    db.execute("DELETE FROM login_inf WHERE username=(SELECT username from employees WHERE e_id=?)", (doc_id,))
    db.execute("DELETE FROM doctor WHERE doc_id=?", (doc_id,))
    db.execute("DELETE FROM employees WHERE e_id=?", (doc_id,))

    db.commit()
    return render_template('loading.html')


def countfunc(dicc,iid):
    count = 0

    for i in dicc:
        if dicc[i][0] == iid:
            count = count + 1
    return count

