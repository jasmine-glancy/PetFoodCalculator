from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, SelectField, IntegerField
from wtforms.validators import DataRequired


# Create a Flask Form for the Pet's signalment
class NewSignalment(FlaskForm):
    pet_name = StringField("Pet's Name:", validators=[DataRequired()])
    pet_age = IntegerField("Pet's Age in Years:", validators=[DataRequired()])
    pet_age_months = IntegerField("Pet's Age in Months:", validators=[DataRequired()])
    pet_species = SelectField(u"Pet's Species:",
                                  choices=[("default", "Please choose"),
                                            ("Canine", "Canine"),
                                            ("Feline", "Feline")],
                                  validators=[DataRequired()],
                                  render_kw={"option": {"default": {"disabled": ""}},
                                             "id": "species"})
    pet_sex = SelectField(u"Pet's Sex:",
                              choices=[("default", "Please choose"),
                              (1, "Female (Intact)"),
                              (2, "Female (Spayed)"),
                              (3, "Male (Intact)"),
                              (4, "Male (Neutered)")],
                              validators=[DataRequired()],
                              render_kw={"option": {"default": {"disabled": ""}},
                                         "id": "sex"})

# Obtain pet weight and BCS
class GetWeight(FlaskForm):
    pet_bcs = SelectField(u"Please Select Pet's Body Condition Score:", 
                                choices=[("default", "Please choose"),
                                         (1, "BCS 1"),                            
                                         (2, "BCS 2"),
                                         (3, "BCS 3"),
                                         (4, "BCS 4"),
                                         (5, "BCS 5"),
                                         (6, "BCS 6"),
                                         (7, "BCS 7"),
                                         (8, "BCS 8"),
                                         (9, "BCS 9")],
                                validators=[DataRequired()],
                                render_kw={"default": {"disabled": ""}})
    pet_weight = StringField("Pet's Weight:", validators=[DataRequired()])
    pet_units = SelectField(u"Is the weight you entered in pounds (lb) or kilograms (kg)?", 
                                choices=[("default", "Please choose"),
                                         ("lbs", "Pounds"),                            
                                         ("kgs", "Kilograms")],
                                validators=[DataRequired()],
                                render_kw={"default": {"disabled": ""}})

# Obtain breeding and nursing status
class ReproStatus(FlaskForm):
    pregnancy_status = SelectField(u"Is Your Pet Currently Pregnant?:",
                                  choices=[("default", "Please choose"),
                                            (0, "No"),
                                            (1, "Yes")],
                                  validators=[DataRequired()],
                                  render_kw={"default": {"disabled": ""},
                                             "id": "pregnancy_status"})
    weeks_gestation = SelectField(u"How Many Weeks Has Your Pet Been Pregnant?:",
                                  choices=[("default", "Please choose"),
                                            (0, "0"),
                                            (1, "1"),
                                            (2, "2"),
                                            (3, "3"),
                                            (4, "4"),
                                            (5, "5"),
                                            (6, "6"),
                                            (7, "7"),
                                            (8, "8"),
                                            (9, "9")],
                                  render_kw={"default": {"disabled": ""},
                                             "id": "gestating"})
    nursing_status = SelectField(u"Is Your Pet Currently Nursing?:",
                                  choices=[("default", "Please choose"),
                                            (0, "No"),
                                            (1, "Yes")],
                                  render_kw={"default": {"disabled": ""},
                                             "id": "nursing_status"})
    litter_size = IntegerField(u"Please Enter the Litter Size:",
                                  render_kw={"id": "litter_size"})
    weeks_nursing = SelectField(u"How Many Weeks Has Your Pet Been Nursing?:",
                                  choices=[("default", "Please choose"),
                                            (0, "0"),
                                            (1, "1"),
                                            (2, "2"),
                                            (3, "3"),
                                            (4, "4"),
                                            (5, "5"),
                                            (6, "6")],
                                  render_kw={"default": {"disabled": ""},
                                             "id": "weeks_nursing"})

# Obtain login info
class LoginForm(FlaskForm):
    username = StringField("Username:", validators=[DataRequired()])
    password = StringField("Password:", validators=[DataRequired()])
    submit = SubmitField("Log In")

# Obtain registration info
class RegisterForm(FlaskForm):
    username = StringField("Please Choose a Username:", validators=[DataRequired()])
    password = StringField("Please Choose a Password:", validators=[DataRequired()])
    confirm_password = StringField("Please Confirm Your Password:", validators=[DataRequired()])
    submit = SubmitField("Sign Up")
    
# Obtain activity info
class WorkForm(FlaskForm):
    light_work_minutes = IntegerField(
        "Approximately how many minutes of low-impact exercise does your pet get per day? Please enter 0 if none: ",
        validators=[DataRequired()])
    light_work_hours = IntegerField(
        "Approximately how many hours of low-impact exercise does your pet get per day? Please enter 0 if none: ",
        validators=[DataRequired()])
    heavy_work_minutes = IntegerField(
        "Approximately how many minutes of high-impact exercise does your pet get per day? Please enter 0 if none: ",
        validators=[DataRequired()])
    heavy_work_hours = IntegerField(
        "Approximately how many hours of high-impact exercise does your pet get per day? Please enter 0 if none: ",
        validators=[DataRequired()])

# Obtain food info
class FoodForm(FlaskForm):
    current_food_kcal = FloatField(
        "How many calories are in each cup (or can/pouch)* of your pet's current food?: ",
        validators=[DataRequired()])
    current_food_form = SelectField(u"What form of this diet do you feed?: ",
                                  choices=[("default", "Please choose"),
                                            (1, "Dry"),
                                            (2, "Canned"),
                                            (3, "Semi-Moist Pouches")],
                                  render_kw={"default": {"disabled": ""}})
    meals_per_day = FloatField(
        "How many meals per day* does your pet get?: ",
        validators=[DataRequired()])
    food_transition = SelectField(
        u"Are you planning on transitioning your pet to a new food?",
        choices=[("default", "Please choose"),
                 (0, "No"),
                 (1, "Yes")],
        render_kw={"default": {"disabled": ""}},
        validators=[DataRequired()])
    sensitive_stomach = SelectField(
        u"Does your pet have a sensitive stomach?",
        choices=[("default", "Please choose"),
                 (0, "No"),
                 (1, "Yes")],
        render_kw={"default": {"disabled": ""}},
        validators=[DataRequired()])
    
class NewFoodForm(FlaskForm):
    new_food_kcal = FloatField(
        "How many calories are in each cup (or can/pouch)* of your pet's new food?: ",
        validators=[DataRequired()])
    new_food_form = SelectField(u"What form of this diet do you feed?: ",
                                  choices=[("default", "Please choose"),
                                            (1, "Dry"),
                                            (2, "Canned"),
                                            (3, "Semi-Moist Pouches")],
                                  render_kw={"default": {"disabled": ""}})