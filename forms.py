from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, SelectField, URLField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, URL, NumberRange, Length, EqualTo, Optional

class UserRegisterForm(FlaskForm):
    name = StringField('Full Name', validators=[
        DataRequired(message="Name is required."),
        Length(min=2, max=100)
    ])
    email = StringField('Email Address', validators=[
        DataRequired(message="Email is required."),
        Email(message="Please enter a valid email address.")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required."),
        Length(min=6, message="Password must be at least 6 characters.")
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message="Passwords must match.")
    ])
    submit = SubmitField('Create Account')


class UserLoginForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')


class AdminLoginForm(FlaskForm):
    email = StringField('Admin Email', validators=[DataRequired(), Email()])
    password = PasswordField('Admin Password', validators=[DataRequired()])
    submit = SubmitField('Login to Admin Portal')


class AddCafeForm(FlaskForm):
    name = StringField('Cafe Name', validators=[
        DataRequired(message="Cafe name is required."),
        Length(min=2, max=100)
    ])
    location = StringField('Neighborhood / Area', validators=[DataRequired(), Length(max=150)])
    zip_code = StringField('ZIP / Postal Code', validators=[Optional(), Length(max=20)])
    address = StringField('Full Street Address', validators=[DataRequired(), Length(max=255)])
    google_maps_url = URLField('Google Maps Share Link (Optional)', validators=[Optional(), URL()])
    img_url = URLField('Image URL (Optional)', validators=[Optional(), URL()])
    opening_hours = StringField('Opening Hours', validators=[DataRequired()])
    price_range = SelectField('Price Tier', choices=[
        ('Budget-friendly', 'Budget-friendly'),
        ('Moderate', 'Moderate'),
        ('Flexible', 'Flexible')
    ], validators=[DataRequired()])
    seating_capacity = StringField('Seating Capacity Description', validators=[DataRequired()])

    has_backup_power = SelectField('Backup Power / Generator Available?', choices=[
        ('1', 'Yes — Generator / Inverter On-Site'),
        ('0', 'No — Main Power Grid Only')
    ], default='1', validators=[DataRequired()])
    socket_accessibility = SelectField('Power Socket Density', choices=[
        ('Abundant At Every Table', 'Abundant At Every Table'),
        ('Moderate Access', 'Moderate Access'),
        ('Limited Sockets', 'Limited Sockets')
    ], default='Moderate Access', validators=[DataRequired()])
    is_meeting_friendly = SelectField('Suitable for Remote Calls & Meetings?', choices=[
        ('1', 'Yes — Quiet / Meeting Friendly'),
        ('0', 'No — High Ambient Noise / Social')
    ], default='0', validators=[DataRequired()])

    wifi_speed_mbps = IntegerField('Wi-Fi Speed (Mbps)', validators=[DataRequired(), NumberRange(min=1, max=1000)])
    wifi_quality_score = FloatField('Wi-Fi Quality Rating (0 - 10)', validators=[DataRequired(), NumberRange(min=0.0, max=10.0)])
    power_outlet_score = FloatField('Power Outlet Availability (0 - 10)', validators=[DataRequired(), NumberRange(min=0.0, max=10.0)])
    noise_level_score = FloatField('Quiet Atmosphere Score (0 - 10)', validators=[DataRequired(), NumberRange(min=0.0, max=10.0)])
    seating_comfort_score = FloatField('Seating Comfort (0 - 10)', validators=[DataRequired(), NumberRange(min=0.0, max=10.0)])
    affordability_score = FloatField('Affordability Score (0 - 10)', validators=[DataRequired(), NumberRange(min=0.0, max=10.0)])
    opening_hours_score = FloatField('Hours Convenience Score (0 - 10)', validators=[DataRequired(), NumberRange(min=0.0, max=10.0)])

    submit = SubmitField('Submit Cafe for Approval')


class VerificationReportForm(FlaskForm):
    reporter_name = StringField('Your Name / Contributor Handle (Optional)', validators=[Optional(), Length(max=100)])
    wifi_speed_mbps = IntegerField('Latest Tested Wi-Fi Speed in Mbps (Optional)', validators=[Optional(), NumberRange(min=1, max=1000)])
    price_range = SelectField('Current Price Range (Optional)', choices=[
        ('', 'Select Price Tier (Unchanged)'),
        ('Budget-friendly', 'Budget-friendly'),
        ('Moderate', 'Moderate'),
        ('Flexible', 'Flexible')
    ], validators=[Optional()])
    opening_hours = StringField('Updated Operating Hours (Optional)', validators=[Optional(), Length(max=100)])
    notes = TextAreaField('Verification Details / What Changed?', validators=[DataRequired(), Length(min=5, max=500)])
    submit = SubmitField('Submit Re-verification Request')


class ReviewForm(FlaskForm):
    rating = SelectField('Overall Rating', choices=[
        (5, '5 Stars — Excellent Workspace'),
        (4, '4 Stars — Very Good'),
        (3, '3 Stars — Average / Okay'),
        (2, '2 Stars — Needs Improvement'),
        (1, '1 Star — Poor Workspace')
    ], coerce=int, validators=[DataRequired()])
    comment = TextAreaField('Your Review / Work Session Experience', validators=[
        DataRequired(message="Please write a brief comment about your experience."),
        Length(min=5, max=1000, message="Comment must be between 5 and 1000 characters.")
    ])
    submit = SubmitField('Post Review')


class ReplyForm(FlaskForm):
    comment = TextAreaField('Your Reply', validators=[
        DataRequired(message="Please enter a reply."),
        Length(min=2, max=500, message="Reply must be between 2 and 500 characters.")
    ])
    submit = SubmitField('Post Reply')