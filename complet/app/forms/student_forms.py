from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length


class StudentForm(FlaskForm):
    nom = StringField("Nom", validators=[DataRequired(), Length(max=80)])
    prenom = StringField("Prénom", validators=[DataRequired(), Length(max=80)])
    email = StringField("Email", validators=[DataRequired(), Email(check_deliverability=False), Length(max=120)])
    niveau = SelectField(
        "Niveau",
        choices=[
            ("Licence 1", "Licence 1"),
            ("Licence 2", "Licence 2"),
            ("Licence 3", "Licence 3"),
            ("Master 1", "Master 1"),
            ("Master 2", "Master 2"),
        ],
        validators=[DataRequired()],
    )
    statut = SelectField(
        "Statut", choices=[("actif", "Actif"), ("inactif", "Inactif")], validators=[DataRequired()]
    )
    submit = SubmitField("Enregistrer")
