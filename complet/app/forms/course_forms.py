from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    DecimalField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, NumberRange


class CourseForm(FlaskForm):
    titre = StringField("Titre", validators=[DataRequired(), Length(max=150)])
    description = TextAreaField("Description", validators=[DataRequired(), Length(max=2000)])
    categorie = StringField("Catégorie", validators=[DataRequired(), Length(max=80)])
    prix = DecimalField("Prix (€)", validators=[DataRequired(), NumberRange(min=0)])
    duree = IntegerField("Durée (heures)", validators=[DataRequired(), NumberRange(min=1)])
    capacite_max = IntegerField(
        "Capacité maximale", validators=[DataRequired(), NumberRange(min=1)]
    )
    formateur_id = SelectField("Formateur responsable", validators=[DataRequired()])
    date_debut = DateField("Date de début", validators=[DataRequired()])
    date_fin = DateField("Date de fin", validators=[DataRequired()])
    statut = SelectField(
        "Statut",
        choices=[("ouverte", "Ouverte"), ("fermee", "Fermée"), ("terminee", "Terminée")],
        validators=[DataRequired()],
    )
    submit = SubmitField("Enregistrer")
