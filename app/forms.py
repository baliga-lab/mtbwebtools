from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, PasswordField, SubmitField, validators
from wtforms.validators import Required

class SearchForm(Form):
    search = TextField('search', validators = [Required()])

"""
class LoginForm(Form):
    openid = TextField('openid', validators = [Required()])
    remember_me = BooleanField('remember_me', default = False)
"""
