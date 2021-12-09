import sqlite3
import logging
from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

db_accesses = 0
# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection

# Function to get a post using its ID
def get_post(post_id):
    global db_accesses
    db_accesses = db_accesses + 1
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Define the Flask application
logging.basicConfig(format='%(levelname)s: %(asctime)s %(message)s', level=logging.DEBUG)
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'


@app.route('/healthz')
def status():
    response = app.response_class(
            response=json.dumps({"result":"OK - healthy"}),
            status=200,
            mimetype='application/json'
    )

    return response

@app.route('/metrics')
def metrics():
    global db_accesses
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    response = app.response_class(
            response=json.dumps({"db_connection_count":db_accesses,"post_count":len(posts)}),
            status=200,
            mimetype='application/json'
    )

    return response

# Define the main route of the web application 
@app.route('/')
def index():
    global db_accesses
    db_accesses = db_accesses + 1
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      logging.info('Tried to access a non-existent article. Id = %s', post_id)
      return render_template('404.html'), 404
    else:
      logging.info('An existing title has been retrieved. Title name is "%s"', post['title'])
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    logging.warning('The "About Page" has been retrieved')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    global db_accesses
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            db_accesses = db_accesses + 1
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()

            logging.info('A new title has been created. Title name is "%s"', title)

            return redirect(url_for('index'))

    return render_template('create.html')

# start the application on port 3111
if __name__ == "__main__":
   app.run(host='0.0.0.0', port='3111')
