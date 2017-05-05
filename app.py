from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
# from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'myflaskapp'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_PASSWORD'] = 'GVElKfLalbk2ggtH'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# init MYSQL
mysql = MySQL(app)

# importing local data
# Articles = Articles()

# index
@app.route('/')
def index():
    return render_template('home.html')

# about
@app.route('/about')
def about():
    return render_template('about.html')

# articles
@app.route('/articles')
def articles():
    # create cursor
    cur = mysql.connection.cursor()

    # get articles
    result = cur.execute("select * from articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No Articles Found.'
        return render_template('articles.html', msg=msg)
    # close connection
    cur.close()

# single article
@app.route('/article/<string:id>')
def article(id):
    # create cursor
    cur = mysql.connection.cursor()

    # get article
    result = cur.execute('select * from articles where (id = %s)', [id])

    article = cur.fetchone()

    return render_template('article.html', article=article)

# register form class
class RegisterForm(Form):
    name = StringField('Name', [validators.length(min=1, max=50)])
    username = StringField('Username', [validators.length(min=4, max=25)])
    email = StringField('Email', [validators.length(min=6, max=50)])
    password = PasswordField('PasswordField', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message="Passwords do not match.")
    ])
    confirm = PasswordField('Confirm Password')

# user register
@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # create cursor
        cur = mysql.connection.cursor()
        # execute query
        cur.execute("insert into users(name, email, username, password) values(%s, %s, %s, %s)", (name, email, username, password))
        # comit to db
        mysql.connection.commit()
        # close connection
        cur.close()

        flash('You are now registered and can log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

# user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # get form fields
        username = request.form['username']
        password_candidate = request.form['password']
        # create cursor
        cur = mysql.connection.cursor()
        # get user by username
        result = cur.execute("select * from users where username = %s", [username])

        if result > 0:
            # get stored hash
            data = cur.fetchone()
            password = data['password']
            # comparae passwords
            if sha256_crypt.verify(password_candidate, password):
                # passed
                session['logged_in'] = True
                session['username'] = username
                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid credentials'
                # app.logger.info('INVALID CREDENTIALS')
                return render_template('login.html', error=error)
        else:
            error = 'Invalid credentials'
            return render_template('login.html', error=error)

    return render_template('login.html')

# check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # create cursor
    cur = mysql.connection.cursor()

    # get articles
    result = cur.execute("select * from articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No articles Found'
        return render_template('dashboard.html', msg=msg)

    # close connection
    cur.close()

    return render_template('dashboard.html')

# article form class
class ArticleForm(Form):
    title = StringField('Title', [validators.length(min=1, max=200)])
    body = TextAreaField('Body', [validators.length(min=30)])

# add article
@app.route('/add_article', methods=['GET','POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # create cursor
        cur = mysql.connection.cursor()

        # execute
        cur.execute('insert into articles(title, body, author) values (%s, %s, %s)', (title, body, session['username']))

        # commit to DB
        mysql.connection.commit()

        # close connection
        cur.close()

        flash('Article Created', 'Success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)

# Edit Article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article by id
    result = cur.execute("select * from articles where id = %s", [id])

    article = cur.fetchone()
    cur.close()
    # Get form
    form = ArticleForm(request.form)

    # Populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # Create Cursor
        cur = mysql.connection.cursor()
        app.logger.info(title)
        # Execute
        cur.execute ("update articles set title=%s, body=%s where id=%s",(title, body, id))
        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Article Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)

# Delete Article
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("delete from articles where id = %s", [id])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    flash('Article Deleted', 'success')

    return redirect(url_for('dashboard'))

# we add debug=True so it updates the application without needing to
# to restart the serve
if __name__ == '__main__':
    app.secret_key="secret123"
    app.run(debug=True)
