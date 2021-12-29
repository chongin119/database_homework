from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class DepartmentForm(FlaskForm):
    """
    Form for admin to add or edit a department
    """
    de_id = StringField('科室编号', validators=[DataRequired()])
    che_id = StringField('主任编号', validators=[DataRequired()])
    submit = SubmitField('Submit')

class AppointmentForm(FlaskForm):

    date = StringField('日期', validators=[DataRequired()])
    pat_id = StringField('患者编号', validators=[DataRequired()])
    de_id = StringField('科室编号', validators=[DataRequired()])
    doc_id = StringField('医生编号', validators=[DataRequired()])
    temp = StringField('体温', validators=[DataRequired()])
    symptom = StringField('症状', validators=[DataRequired()])
    address = StringField('地址', validators=[DataRequired()])
    risk = StringField('有无风险', validators=[DataRequired()])
    submit = SubmitField('Submit')