# -*- coding: utf-8 -*-
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, redirect, url_for, abort, \
     render_template, flash, _app_ctx_stack

# configuration
DATABASE = '/tmp/flaskr.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'
UPLOAD_FOLDER = '/static/images/'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

# create the application 
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

def init_db():
    """Creates the database tables."""
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    top = _app_ctx_stack.top
    if not hasattr(top, 'sqlite_db'):
        sqlite_db = sqlite3.connect(app.config['DATABASE'])
        sqlite_db.row_factory = sqlite3.Row
        top.sqlite_db = sqlite_db

    return top.sqlite_db

@app.teardown_appcontext
def close_db_connection(exception):
    """Closes the database again at the end of the request."""
    top = _app_ctx_stack.top
    if hasattr(top, 'sqlite_db'):
        top.sqlite_db.close()

@app.route('/')
def show_orders():
    db = get_db()
    cur = db.execute('select pid, email, merchandise_id, merchandise_name, quantity, cost, order_date from orders order by pid asc')
    orders = cur.fetchall()
    return render_template('show_orders.html', orders=orders)

@app.route('/add', methods=['GET','POST'])
def add_order():
    db = get_db()
    cur = db.execute('select pid, name, price from merchandise order by pid asc')
    merchandise = cur.fetchall()
    if request.method == 'POST':
        if not session.get('logged_in'):
            abort(401)
        orderlist=[]
        for item in merchandise:
            pid = str(item['pid'])
            quantity = (request.form[pid])
            if not (quantity=='0' or quantity==''):
                cost = "{0:.2f}".format(float((float(item['price']))*int(quantity)))
                orderlist.append([int(pid), item['name'], int(quantity), cost])
            email = request.form['email']
            date = request.form['date']
        for x in orderlist:
            db = get_db()
            db.execute('insert into orders (email, merchandise_id, merchandise_name, quantity, cost, order_date) values (?, ?, ?, ?, ?, ?)',
                         [email, x[0], x[1], x[2], x[3], date])
        if orderlist:
            db.commit()
            flash('New order was successfully posted')
            return redirect(url_for('show_orders'))
        else:
            flash('Please order at least one item')

    return render_template('add_order.html', merchandise=merchandise)

@app.route('/add_merchandise', methods=['GET','POST'])
def add_merchandise():
    db = get_db()
    cur = db.execute('select pid, name, price from merchandise order by pid asc')
    merchandise = cur.fetchall()
    if request.method=='POST':
        db.execute('insert into merchandise (name, price) values(?, ?)',
                     [request.form['name'], "{0:.2f}".format(float(request.form['price']))])
        db.commit()
        flash('New merchandise successfully added')
        return redirect(url_for('show_merchandise'))
    return render_template('add_merchandise.html', merchandise=merchandise)

@app.route('/show_merchandise', methods=['GET' , 'POST'])
def show_merchandise(): #delete_merchandise also
    db = get_db()
    cur = db.execute('select pid, name, price, image from merchandise order by pid asc')
    merchandise = cur.fetchall()
    if request.method=='POST':
        merchandise_id = request.form['delete']
        db.execute("DELETE FROM merchandise WHERE pid=(?)",[merchandise_id])
        db.execute("DELETE FROM orders WHERE merchandise_id=(?)",[merchandise_id])
        db.commit()
        flash('Successfully Deleted')
        return redirect(url_for('show_merchandise'))
    return render_template('show_merchandise.html', merchandise=merchandise)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email == app.config['USERNAME'] and password == app.config['PASSWORD']:
            session['logged_in'] = email
            flash('You were logged in')
            return redirect(url_for('show_orders'))
        db = get_db()
        cur = db.execute('select email, password from user')
        emails = cur.fetchall()
        for e in emails:
            if e[0]==email:
                if password != e[1]:
                    error = 'Invalid'
                else:
                    session['logged_in'] = email
                    flash('You were logged in')
                    return redirect(url_for('show_orders'))
        else:
            error = 'Invalid'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_orders'))

@app.route('/register', methods=['GET','POST'])
def register():
    error=None
    if request.method == 'POST':
        db = get_db()
        cur = db.execute('select email, password from user')
        email = request.form['email']
        emails = cur.fetchall()
        for e in emails:
            if e[0]==email:
                error = 'Email currently in use'
                break
        else:
            db.execute('insert into user (email, password) values (?, ?)',
                     [request.form['email'], request.form['password']])
            db.commit()
            flash('Successfully registered')
            session['logged_in'] = email
            return redirect(url_for('add_order'))
    return render_template('register.html', error=error)

if __name__ == '__main__':
    init_db()
    app.run()
