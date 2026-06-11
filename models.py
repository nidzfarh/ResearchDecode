from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Analysis(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    filename = db.Column(
        db.String(300)
    )

    summary = db.Column(
        db.Text
    )

    core_idea = db.Column(
        db.Text
    )

    tech_stack = db.Column(
        db.Text
    )

    implementation = db.Column(
        db.Text
    )

    folder_structure = db.Column(
        db.Text
    )