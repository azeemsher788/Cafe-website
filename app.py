import os
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, PasswordField, SelectField
from wtforms.validators import DataRequired, URL, Length
from typing import List, Optional

# --- Configuration ---
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
# In a real production app, this should be an environment variable.
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', '8BYkEfBA6O6donzWlSihBXox7C0sKR6b')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'cafes.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Models ---
class Cafe(db.Model): # type: ignore
    __tablename__ = "cafe"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    seats = db.Column(db.String(250), nullable=False)
    has_toilet = db.Column(db.Boolean, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False)
    has_sockets = db.Column(db.Boolean, nullable=False)
    can_take_calls = db.Column(db.Boolean, nullable=False)
    coffee_price = db.Column(db.String(250), nullable=True)

# --- Forms ---
class CafeForm(FlaskForm):
    """Form to add a new cafe."""
    name = StringField('Cafe Name', validators=[DataRequired(), Length(max=250)])
    map_url = StringField('Cafe Location on Google Maps (URL)', validators=[DataRequired(), URL(), Length(max=500)])
    img_url = StringField('Image URL', validators=[DataRequired(), URL(), Length(max=500)])
    location = StringField('Neighborhood/City', validators=[DataRequired(), Length(max=250)])
    seats = SelectField('Approximate Seats', choices=['0-10', '10-20', '20-30', '30-40', '50+'], validators=[DataRequired()])
    coffee_price = StringField('Coffee Price (e.g., £2.50)', validators=[DataRequired(), Length(max=250)])
    has_toilet = BooleanField('Has Toilet?')
    has_wifi = BooleanField('Has WiFi?')
    has_sockets = BooleanField('Has Sockets?')
    can_take_calls = BooleanField('Can Take Calls?')
    submit = SubmitField('Add Cafe')

class DeleteForm(FlaskForm):
    """Form to delete a cafe, requires admin password."""
    api_key = PasswordField('Admin API Key', validators=[DataRequired()])
    submit = SubmitField('Delete Cafe')

# --- Routes ---

@app.route('/')
def home():
    """Render the homepage displaying all cafes."""
    try:
        # Use scalar/scalars for modern SQLAlchemy 2.0 style if desired, but query.all() is still fine in 1.4/2.0
        cafes: List[Cafe] = Cafe.query.all()
        return render_template('index.html', cafes=cafes)
    except Exception as e:
        # Catch DB connection errors or issues
        app.logger.error(f"Error fetching cafes: {e}")
        return render_template('error.html', message="Could not connect to the database. Please try again later."), 500

@app.route('/add', methods=['GET', 'POST'])
def add_cafe():
    """Render the add cafe form and handle submission."""
    form = CafeForm()
    if form.validate_on_submit():
        new_cafe = Cafe(
            name=form.name.data,
            map_url=form.map_url.data,
            img_url=form.img_url.data,
            location=form.location.data,
            seats=form.seats.data,
            has_toilet=form.has_toilet.data,
            has_wifi=form.has_wifi.data,
            has_sockets=form.has_sockets.data,
            can_take_calls=form.can_take_calls.data,
            coffee_price=form.coffee_price.data,
        )
        try:
            db.session.add(new_cafe)
            db.session.commit()
            flash("Cafe added successfully!", "success")
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error adding cafe: {e}")
            flash("Error adding cafe. It may already exist.", "error")

    return render_template('add.html', form=form)

@app.route('/delete/<int:cafe_id>', methods=['GET', 'POST'])
def delete_cafe(cafe_id: int):
    """Securely delete a cafe via a mock 'Admin' requirement."""
    cafe: Optional[Cafe] = Cafe.query.get_or_404(cafe_id)
    form = DeleteForm()
    
    if form.validate_on_submit():
        if form.api_key.data == "TopSecretAdminKey":
            try:
                db.session.delete(cafe)
                db.session.commit()
                flash(f"Cafe '{cafe.name}' deleted.", "success")
                return redirect(url_for('home'))
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Error deleting cafe: {e}")
                flash("Error deleting cafe. Please try again.", "error")
        else:
            flash("Invalid API Key. You are not authorized to delete cafes.", "error")
            
    return render_template('delete.html', form=form, cafe=cafe)

# --- Error Handlers ---
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', message="An internal server error occurred."), 500

if __name__ == '__main__':
    # When deployed, debug should be set to False
    app.run(debug=True, port=5000)
