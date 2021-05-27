from flask import (
    Flask, render_template, request, redirect, flash, url_for, session, g
)

from werkzeug.security import check_password_hash, generate_password_hash

from werkzeug.exceptions import abort

from psycopg2 import (
        connect
)


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
 
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

 # "cookies"
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        conn = get_dbConn()
        cur = conn.cursor()
        cur.execute(
            'SELECT * FROM pa_user WHERE user_id = %s', (user_id,)
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
            error ='Please insert a valid value for the longitude 0<= lat <360'
         
        #check if something went wrong in compiling the form  
        if error is not None :
            flash(error)
            return redirect(url_for('index'))
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
        
        
@app.route('/create', methods=('GET', 'POST'))
def create_comment():
    if load_logged_in_user():
        if request.method == 'POST' :
            title = request.form['title']
            body = request.form['body']
            error = None
            
            if not title :
                error = 'Title is required!'
            if error is not None :
                flash(error)
                return redirect(url_for('index'))
            else : 
                conn = get_dbConn()
                cur = conn.cursor()
                cur.execute('INSERT INTO post (title, body, author_id) VALUES (%s, %s, %s)', 
                            (title, body, g.user[0])
                            )
                cur.close()
                conn.commit()
                return redirect(url_for('index'))
        else :
            return render_template('blog/create_comment.html')
    else :
        error = 'Only loggedin users can insert comments!'
        flash(error)
        return redirect(url_for('login'))
   
def get_comment(id):
    conn = get_dbConn()
    cur = conn.cursor()
    cur.execute(
        """SELECT *
           FROM comments
           WHERE comments.comment_id = %s""",
        (id,)
    )
    comment = cur.fetchone()
    cur.close()
    if comment is None:
        abort(404, "Comment id {0} doesn't exist.".format(id))

    if comment[1] != g.user[0]:
        abort(403)

    return comment

@app.route('/<int:id>/update', methods=('GET', 'POST'))
def update_comment(id):
    if load_logged_in_user():
        comment = get_comment(id)
        if request.method == 'POST' :
            title = request.form['title']
            body = request.form['body']
            error = None
            
            if not title :
                error = 'Title is required!'
            if error is not None :
                flash(error)
                return redirect(url_for('index'))
            else : 
                conn = get_dbConn()
                cur = conn.cursor()
                cur.execute('UPDATE comment SET title = %s, body = %s'
                               'WHERE comment_id = %s', 
                               (title, body, id)
                               )
                cur.close()
                conn.commit()
                return redirect(url_for('index'))
        else :
            return render_template('blog/update_comment.html', comment = comment)
    else :
        error = 'Only loggedin users can insert comments!'
        flash(error)
        return redirect(url_for('login'))

@app.route('/<int:id>/delete_comment', methods=('POST',))
def delete_comment(id):
    conn = get_dbConn()                
    cur = conn.cursor()
    cur.execute('DELETE FROM comments WHERE comment_id = %s', (id,))
    conn.commit()
    return redirect(url_for('index'))        
        
        
        
        if __name__ == '__main__':
    app.run(debug=True)
