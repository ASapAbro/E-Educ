from flask_wtf import FlaskForm
from wtforms import DecimalField, SubmitField
from wtforms.validators import DataRequired, NumberRange


class GradeForm(FlaskForm):
    note = DecimalField(
        "Note (/20)", validators=[DataRequired(), NumberRange(min=0, max=20)]
    )
    submit = SubmitField("Enregistrer la note")
