from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from models import db, Movie, Log

# Create a blueprint for routing
app_routes = Blueprint('app_routes', __name__)

# Home route - show all logs
@app_routes.route('/')
def index():
    logs = Log.query.all()
    return render_template('index.html', logs=logs)

# Add a new log - show form and handle submission
@app_routes.route('/add', methods=['GET', 'POST'])
def add_log():
    if request.method == 'POST':
        #userID = request.form['userID']
        title = request.form['movieTitle']
        rating = request.form['rating']
        review = request.form['review']
        favorite = 'favorite' in request.form  # checkbox for favorite (True/False)

        # Retrieve user and movie objects
        #user = User.query.get(userID)
        movie = Movie.query.get(title)

        #if not user or not movie:
        #    return render_template('add_log.html', error="Invalid user or movie ID")
        if not movie:
            return render_template('add_log.html', error="Movie not found")

        # Add the new log to the database
        new_log = Log(title=movie.title, rating=rating, review=review, favorite=favorite)
        db.session.add(new_log)
        db.session.commit()

        return redirect(url_for('app_routes.index'))  # Redirect to the index page after adding

    return render_template('add_log.html')  # GET request - Show the add log form

# Update a log - show form to edit and handle submission
@app_routes.route('/logs/edit/<int:id>', methods=['GET', 'POST'])
def edit_log(id):
    log = Log.query.get(id)
    if not log:
        return render_template('edit_log.html', error="Log not found")

    if request.method == 'POST':
        log.rating = request.form['rating']
        log.review = request.form['review']
        log.favorite = 'favorite' in request.form  # checkbox for favorite (True/False)
        db.session.commit()

        return redirect(url_for('app_routes.index'))  # Redirect to the index page after editing

    return render_template('edit_log.html', log=log)  # GET request - Show the edit log form

# Delete a log
@app_routes.route('/logs/delete/<int:id>', methods=['POST'])
def delete_log(id):
    log = Log.query.get(id)
    if not log:
        return render_template('index.html', error="Log not found")

    db.session.delete(log)
    db.session.commit()

    return redirect(url_for('app_routes.index'))  # Redirect back to the index page after deletion


# API Section - Serve JSON responses
api = Blueprint('api', __name__)

# Get all logs in JSON format
@api.route('/api/logs', methods=['GET'])
def get_logs():
    logs = Log.query.all()
    return jsonify([{
        'logID': log.logID,
        #'userID': log.userID,
        'title': log.title,
        'rating': log.rating,
        'review': log.review,
        'date': log.date,
        'favorite': log.favorite
    } for log in logs])

# Add a new log via API (POST request)
@api.route('/api/logs', methods=['POST'])
def add_log_api():
    data = request.json
    #user = User.query.get(data.get('userID'))
    movie = Movie.query.get(data.get('title'))

    #if not user or not movie:
    #    return jsonify({"error": "Invalid user or movie ID"}), 400

    if not movie:
        return jsonify({"error": "Movie not found"}), 404

    new_log = Log(
        #userID=user.userID,
        title=movie.title,
        rating=data.get('rating'),
        review=data.get('review'),
        favorite=data.get('favorite', False)
    )
    db.session.add(new_log)
    db.session.commit()
    return jsonify({"message": "Log added successfully"}), 201

# Update a log via API (PUT request)
@api.route('/api/logs/<int:id>', methods=['PUT'])
def update_log_api(id):
    log = Log.query.get(id)
    if not log:
        return jsonify({"error": "Log not found"}), 404

    data = request.json
    log.rating = data.get('rating', log.rating)
    log.review = data.get('review', log.review)
    log.favorite = data.get('favorite', log.favorite)

    db.session.commit()
    return jsonify({"message": "Log updated successfully"})

# Delete a log via API (DELETE request)
@api.route('/api/logs/<int:id>', methods=['POST'])
def delete_log_api(id):
    if request.form.get('_method') == 'DELETE':
        log = Log.query.get(id)
        if not log:
            return render_template('index.html', error="Log not found")

        db.session.delete(log)
        db.session.commit()
        return redirect(url_for('index'))  # Redirect to home
    return jsonify({"error": "Invalid method"}), 405
