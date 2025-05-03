from flask import Flask, render_template, request, redirect, url_for
from sqlalchemy import text
from sqlalchemy.orm import joinedload
from models import db, Movie, Log


app = Flask(__name__, template_folder='templates', static_folder='static')

# Configure SQLite Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///moviediary.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Initialize database
db.init_app(app)


def seed_data():
    # Check if sample data already exists
    if Movie.query.count() == 0:
        print("Seeding database with sample data...")

        # Sample Movies
        movie1 = Movie(title="Inception", year=2010, genre="Sci-Fi", director="Christopher Nolan", length=148, description="A mind-bending thriller.")
        movie2 = Movie(title="The Godfather", year=1972, genre="Crime", director="Francis Ford Coppola", length=175, description="A classic mafia story.")
        movie3 = Movie(title="Parasite", year=2019, genre="Thriller", director="Bong Joon-ho", length=132, description="A gripping social satire.")

        # Add to database
        db.session.add_all([movie1, movie2, movie3])
        db.session.commit()

        print("Database seeded successfully.")
    else:
        print("Database already contains data.")

# Create Tables
with app.app_context():
    db.create_all()
    seed_data()

# Home page
@app.route('/')
def index():
    logs = Log.query.all()
    movies = Movie.query.all()
    return render_template('index.html', logs=logs, movies=movies)

# Add a new log
@app.route('/add', methods=['GET', 'POST'])
def add_log():
    if request.method == 'POST':
        movie_title = request.form['movie'].strip()  # user input
        review = request.form['review']
        rating = int(request.form['rating'])
        favorite = 'favorite' in request.form

        # Find existing movie by title
        movie = Movie.query.filter_by(title=movie_title).first()

        # If not found, create it
        if not movie:
            movie = Movie(title=movie_title)
            db.session.add(movie)
            db.session.commit()

        # Now create the log with movie_id
        new_log = Log(movie_id=movie.movieID, review=review, rating=rating, favorite=favorite)
        db.session.add(new_log)
        db.session.commit()

        # Redirect to the index page after adding a log
        return redirect(url_for('index'))

    return render_template('add_log.html')

# Edit a log
@app.route('/logs/edit/<int:id>', methods=['GET', 'POST'])
def edit_log(id):
    log = Log.query.get(id)
    if not log:
        return render_template('edit_log.html', error="Log not found")

    if request.method == 'POST':
        try:
            log.rating = int(request.form['rating']) # User input
            log.review = request.form['review']
            log.favorite = 'favorite' in request.form  # Checkbox sends 'on' if checked

            db.session.commit()
            return redirect(url_for('index'))  # Redirect to home after successful edit
        except Exception as e:
            db.session.rollback()
            return render_template('edit_log.html', error=f"Error updating log: {e}", log=log)

    # Render the edit form for GET requests
    return render_template('edit_log.html', log=log)


# Delete a log
@app.route('/logs/delete/<int:id>', methods=['POST'])
def delete_log(id):
    log = Log.query.get(id)
    if not log:
        return render_template('index.html', error="Log not found")

    db.session.delete(log)
    db.session.commit()

    return redirect(url_for('index'))  # Redirect back to the index page after deletion


'''
# Filter entries - Uses Raw SQL query inputed into ORM but this is not the best practice
@app.route('/filter_logs', methods=['GET', 'POST'])
def filter_logs():
    if request.method == 'POST':
        # Base SQL query
        sql = """
            SELECT log.*, movie.*
            FROM log
            JOIN movie ON log.movie_id = movieID
            WHERE 1=1
        """

        # Initialize the parameters for the query
        params = {}

        # Genre filter
        genre = request.form.get('genre')
        if genre:
            sql += " AND movie.genre = :genre"
            params['genre'] = genre

        # Director filter
        director = request.form.get('director')
        if director:
            sql += " AND movie.director = :director"
            params['director'] = director

        # Year filter
        year = request.form.get('year')
        if year:
            sql += " AND movie.year = :year"
            params['year'] = int(year)

        # Rating range filter
        rating_min = request.form.get('rating_min')
        if rating_min:
            sql += " AND log.rating >= :rating_min"
            params['rating_min'] = int(rating_min)
        
        rating_max = request.form.get('rating_max')
        if rating_max:
            sql += " AND log.rating <= :rating_max"
            params['rating_max'] = int(rating_max)

        # Date range filter
        date_min = request.form.get('date_min')
        if date_min:
            sql += " AND log.date >= :date_min"
            params['date_min'] = date_min

        date_max = request.form.get('date_max')
        if date_max:
            sql += " AND log.date <= :date_max"
            params['date_max'] = date_max

        # Favorite checkbox filter
        favorite = request.form.get('favorite')
        if favorite == 'true':
            sql += " AND log.favorite = :favorite"
            params['favorite'] = True

        # Execute the query
        query = text(sql)
        logs = db.session.execute(query, params).fetchall()

        # Retrieve list of directors for the dropdown
        directors = db.session.query(Movie.director).distinct().all()
        director_list = [director[0] for director in directors]

        # Return the rendered template with filtered logs and directors
        return render_template('filtered_logs.html', logs=logs, movies=director_list)

    # If it's a GET request, just render the empty form
    else:
        genres = db.session.query(Movie.genre).distinct().all()
        directors = db.session.query(Movie.director).distinct().all()
        years = db.session.query(Movie.year).distinct().all()

        # Convert to lists of values
        genre_list = [genre[0] for genre in genres]
        director_list = [director[0] for director in directors]
        year_list = [year[0] for year in years]

        return render_template('filtered_logs.html', genres=genre_list, directors=director_list, years=year_list)

'''

# Filter entries - Uses ORM with joinedload for better performance and readability
# Projects against injection attacks and SQL errors
@app.route('/filter_logs', methods=['GET', 'POST'])
def filter_logs():
    # Always get distinct values for dropdowns
    directors = [d[0] for d in db.session.query(Movie.director).distinct().all()]
    genres = [g[0] for g in db.session.query(Movie.genre).distinct().all()]
    years = [y[0] for y in db.session.query(Movie.year).distinct().order_by(Movie.year).all()]

    logs = []

    if request.method == 'POST':
        query = db.session.query(Log).join(Movie)
        filters = []

        genre = request.form.get('genre')
        if genre:
            filters.append(Movie.genre == genre)

        director = request.form.get('director')
        if director:
            filters.append(Movie.director == director)

        year = request.form.get('year')
        if year:
            filters.append(Movie.year == int(year))

        rating_min = request.form.get('rating_min')
        if rating_min:
            filters.append(Log.rating >= int(rating_min))

        rating_max = request.form.get('rating_max')
        if rating_max:
            filters.append(Log.rating <= int(rating_max))

        date_min = request.form.get('date_min')
        if date_min:
            filters.append(Log.date >= date_min)

        date_max = request.form.get('date_max')
        if date_max:
            filters.append(Log.date <= date_max)

        favorite = request.form.get('favorite')
        if favorite == 'true':
            filters.append(Log.favorite == True)

        # Execute the query with filters, uses joinedLoad to optimize performance
        logs = db.session.query(Log).options(joinedload(Log.movie)).join(Movie).filter(*filters).all()

    # Render the template with filtered logs and dropdowns
    return render_template(
        'filtered_logs.html',
        logs=logs,
        directors=directors,
        genres=genres,
        years=years,
        page_class='filter-logs'
    )

# Edit a movie - Used for after a movie is added to the database through the add log page
@app.route('/movies/edit/<int:id>', methods=['GET', 'POST'])
def edit_movie(id):
    movie = Movie.query.get(id)
    if not movie:
        return render_template('edit_movie.html', error="Movie not found")

    if request.method == 'POST':
        try:
            movie.title = request.form['title']
            movie.year = int(request.form['year']) if request.form['year'] else None
            movie.genre = request.form['genre']
            movie.director = request.form['director']
            movie.description = request.form['description']

            db.session.commit()
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            return render_template('edit_movie.html', error=f"Error updating movie: {e}", movie=movie)

    return render_template('edit_movie.html', movie=movie)


# Clears the database and reseeds it with sample data
@app.route('/reset')
def reset_data():
    # Delete all data
    try:
        db.session.query(Log).delete()
        db.session.query(Movie).delete()
        db.session.commit()
        print("All data deleted.")
        
        # Reseed data
        seed_data()
        return "Database reset and reseeded successfully!"
    except Exception as e:
        db.session.rollback()
        return f"Error: {e}"
    

if __name__ == '__main__':
    app.run(debug=True)