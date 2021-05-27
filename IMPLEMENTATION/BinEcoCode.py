from flask import (
    Flask, render_template, request, redirect, flash, url_for, session, g
)

from werkzeug.security import check_password_hash, generate_password_hash

from werkzeug.exceptions import abort

from psycopg2 import (
        connect
)

from shapely.geometry import Point

# Create the application instance
app = Flask(__name__, template_folder="templates")
# Set the secret key to some random bytes. Keep this really secret!
app.secret_key = '_5#y2L"F4Q8z\n\xec]/'

def get_dbConn():
    if 'dbConn' not in g:
        myFile = open('dbConfig.txt')
        connStr = myFile.readline()
        g.dbConn = connect(connStr)
    
    return g.dbConn

def close_dbConn():
    if 'dbConn' in g:
        g.dbComm.close()
        g.pop('dbConn')
        
        
 #Add your function here
 #registration
@app.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        postal_code = request.form['postal_code']
        municipality = request.form['municipality']
        password = request.form['password']
        error = None

        commands= (
                'SELECT postal_code FROM pa_user WHERE postal_code = %s', (postal_code,),
                'SELECT postal_code FROM pa_data WHERE postal_code = %s', (postal_code,),
                'SELECT municipality FROM pa_data WHERE postal_code = %s', (postal_code),
                )
        if not username:
            error = 'postal_code is required.'
        elif not password:
            error = 'Password is required.'
        elif not municipality:
            error = 'municipality is required.'
        else:
            conn = get_dbConn()
            cur = conn.cursor()
            cur.execute('SELECT postal_code FROM pa_user WHERE postal_code = %s', (postal_code,))
            if cur.fetchone() is not None:
                error = 'User {} is already registered.'.format(postal_code)
                cur.close()
            else:
                cur.execute('SELECT postal_code FROM pa_data WHERE postal_code = %s', (postal_code,))
                if cur.fetchone() is not None:
                    error = 'User {} does not exist'.format(postal_code)
                    cur.close()
                else:
                  cur.execute('SELECT municipality FROM pa_data WHERE postal_code = %s', (postal_code),)
                  if cur.fetchone()!= municipality:
                      error = '{} and {} does not correspond'.format(postal_code,municipality)
                      cur.close()

        if error is None:
            conn = get_dbConn()
            cur = conn.cursor()
            cur.execute(
                'INSERT INTO pa_user (postal_code,municipality,password) VALUES (%s, %s, %s)',
                (postal_code,municipality, generate_password_hash(password))
            )
            cur.close()
            conn.commit()
            return redirect(url_for('login'))

        flash(error)

    return render_template('/register.html')
 
#login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        postal_code = request.form['postal_code']
        password = request.form['password']
        conn = get_dbConn()
        cur = conn.cursor()
        error = None
        cur.execute(
            'SELECT * FROM pa_user WHERE postal_code = %s', (postal_code,)
        )
        user = cur.fetchone()
        cur.close()
        conn.commit()
    
    if user is None:
        error = 'Incorrect postal code.'
    elif not check_password_hash(user[2], password):
        error = 'Incorrect password.'
   
    if error is None:
        session.clear()
        session['user_id'] = user[0]
        return redirect(url_for('index'))
    
    flash(error)

    return render_template('/login.html')

#logout
def logout():
    # remove the username from the session if it's there
    session.clear()
    return redirect(url_for('index'))
 
# "cookies"
def load_logged_in_user():
    postal_code = session.get('postal_code')

    if postal_code is None:
        g.user = None
    else:
        conn = get_dbConn()
        cur = conn.cursor()
        cur.execute(
            'SELECT * FROM pa_user WHERE postal_code = %s', (postal_code,)
        )
        g.user = cur.fetchone()
        cur.close()
        conn.commit()
    if g.user is None:
        return False
    else: 
        return True
    
# Create a URL route in our application for "/"
@app.route('/')
@app.route('/index')
def index():
    if load_logged_in_user():
        return render_template('index.html')
    else:
        return render_template('about.html')


# UC.3 Pa enters new data about the bin
@app.route('/newBin', methods=('GET', 'POST'))
def new_bin():
    if request.method == 'POST' :
        lon = request.form['lon']
        lat = request.form['lat']
        infographic = request.form['infographic']
        
        geom = Point(lon,lat)    
        error = None
       
        # check if the data inserted are correct
        if (not lon or not lat):
            error = '*this data is required!'
        elif (float(lat)<-90 or float(lat)>90):
            error ='Please insert a valid value for the latitude -90<= lat <=90'
        elif(float(lon)<0 or float(lon)>=360):
            error ='Please insert a valid value for the longitude 0<= lon <360'
         
        #check if something went wrong in compiling the form  
        if error is not None :
            flash(error)
            return redirect(url_for('newBin'))
        #everything in the form is ok, database connection is allowed
        else : 
            conn = get_dbConn()
            cur = conn.cursor()
            cur.execute('INSERT INTO bin (lon, lat, infographic, geom ) VALUES (%f, %f, %s, ST_Point(%(geom)s))', 
                        (lon, lat, infographic, geom)
                        )
            cur.close()
            conn.commit()
            return redirect(url_for('index'))
    else :
        return render_template('blog/newBin.html')       
        
        
        
        
        
        
if __name__ == '__main__':
    app.run(debug=True)
