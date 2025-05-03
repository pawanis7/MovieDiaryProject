from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Index
from datetime import datetime

db = SQLAlchemy()

# Define the Movie model
class Movie(db.Model):
    __tablename__ = 'movie'
    movieID = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), unique=True, nullable=False)
    year = db.Column(db.Integer)
    genre = db.Column(db.String(50))
    director = db.Column(db.String(100))
    length = db.Column(db.Integer)
    description = db.Column(db.String(300))
    logs = db.relationship('Log', back_populates='movie') 

    # Create index for genre for faster search and filtering
    __table_args__ = (
        Index('ix_movie_genre', 'genre'),
    )


# Define the Log model
class Log(db.Model):
    __tablename__ = 'log'
    logID = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.movieID'), nullable=False)  # Link to Movie
    rating = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(500), nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    favorite = db.Column(db.Boolean, default=False)

    movie = db.relationship('Movie', back_populates='logs')  

    # Create index for rating for faster search and filtering
    __table_args__ = (
        Index('ix_log_rating', 'rating'),
    )

    