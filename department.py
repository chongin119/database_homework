import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from dbfunc import connect_db,match_user_pwd,disconnect_db,get_domain,insert_user_pwd
from dbfunc import databasePATH

bp = Blueprint('department', __name__)

db = connect_db(databasePATH)

@bp.route('/department/<id>')
def department(id):
    appointments = db.execute("SELECT * FROM patient WHERE department_id=?", (id,)).fetchall()
    department = db.execute("SELECT * FROM department WHERE department_id=?", (id,)).fetchall()
    return render_template('department.html', department=department)


