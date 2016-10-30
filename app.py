from flask import Flask, g, session, render_template, flash, url_for, request
import string
import random

app = Flask("__name__")

#set the secret key to something so secret, even I don't know what it is!
app.secret_key = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(6))


#specify database location
dbLocation = 'data/globe.db'

#underscores for functions, 

def get_db():
      db = getattr(g, 'db', None)
      if db is None:
            db = sqlite3.connect(dbLocation)
            g.gb = db
      return db

@app.teardown_appcontext
def close_db_connection(exception):
      db = getattr(g, 'db', None)
      if db is not None:
            db.close()
            
#check if the user is logged in, i.e. a session is running, if not, send the user to the index page 
@app.route("/")
def determine_user_path():
      #session['username'] = 'Josh'
      if 'username' in session:
           return go_to_feed()
      else:
            return go_to_index()

@app.route("/feed/")
def go_to_feed():
      return render_template('feed.html')

def go_to_index():
      return render_template('index.html')
                              
                                                                        #Add GET too, otherwise we wont be able to access the template!
@app.route("/register/", methods=['GET', 'POST'])
def register_account():
      #if user post'd something
      if request.method == 'POST':
            userName = request.form['email']
            return userName
      else:
            return "Get"

if __name__ == "__main__":
      app.run(host="0.0.0.0")
