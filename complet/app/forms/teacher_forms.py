from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length


class TeacherForm(FlaskForm):
    nom = StringField("Nom", validators=[DataRequired(), Length(max=80)])
    prenom = StringField("Prénom", validators=[DataRequired(), Length(max=80)])
    email = StringField("Email", validators=[DataRequired(), Email(check_deliverability=False), Length(max=120)])
    specialite = StringField("Spécialité", validators=[DataRequired(), Length(max=120)])
    statut = SelectField(
        "Statut", choices=[("actif", "Actif"), ("inactif", "Inactif")], validators=[DataRequired()]
    )
    submit = SubmitField("Enregistrer")
