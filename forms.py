from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, IntegerField
from wtforms.validators import DataRequired, URL, Email
from flask_ckeditor import CKEditorField


##WTForm
class CreateProductForm(FlaskForm):
    name = StringField("Name of the product", validators=[DataRequired()])
    price = IntegerField("Price of the product", validators=[DataRequired()])
    stock = IntegerField("Stock", validators=[DataRequired()])
    image = StringField("Product Image URL", validators=[DataRequired(), URL()])
    description = CKEditorField("Description", validators=[DataRequired()])
    submit = SubmitField("Add product")


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Sign me up!")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log me in!")
