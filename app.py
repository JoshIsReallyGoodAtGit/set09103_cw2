from flask import Flask, g, session, render_template, flash, url_for, request, redirect
from wand.image import Image
import string
import random
import sqlite3
import os


app = Flask("__name__")

#set the secret key to something so secret, even I don't know what it is!
app.secret_key = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(6))


#specify database location
dbLocation = 'data/globe.db'


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
      if 'userName' in session:
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
            userPassword = request.form['password']
            #check that none of the entries are blank, if they are notify the user
            if userName == "" or userPassword == "":
                  #user didn't post anything we can use, flash them (not literally!!)
                  return 'empty!'
            else:
                  #now would be a good time to sanitise the input...
                  return add_user(userName, userPassword)
      else:
            #the user is accessing this via GET, which they probably shouldn't be able to do, so send 'em away
            return redirect('/')

def add_user(userName, userPassword):
      #add data to the record
            db = get_db()
            usernameHardcoded = 'jt3'
            #manually assign a username for now
            db.cursor().execute("INSERT INTO GLB_Accounts ('Username', 'Email', 'Password') VALUES (?, ?, ?)", [usernameHardcoded, userName, userPassword])
            db.commit()
            #check the user has been added
            sql="SELECT Username FROM GLB_Accounts WHERE Username = 'jt3'"
            for row in db.cursor().execute(sql):
                  if row is not None:
                        #now the user has created an account, they will be auto-logged in
                        return start_sesh(userName)
                  else:
                        return "oh no!"
            db.close()
            
      
def start_sesh(userName):
      #start the session
      session['userName'] = userName
      #redirect the user
      return determine_user_path()

@app.route("/login", methods=['POST'])
def log_in():
      #retrieve the form
      if request.method == 'POST':
            userName = request.form['login-email']
            userPassword = request.form['login-password']
            #check that none of the entries are blank, if they are notify the user
            if userName == "" or userPassword == "":
                  #user didn't post anything we can use, flash them
                  return 'empty!'
            else:
                  #check the user exists and that the password is correct
                  return auth_user_login(userName, userPassword)
      else:
            #the user is accessing this via GET, which they probably shouldn't be able to do, so send 'em away
            return redirect('/')
      

      
def auth_user_login(userName, userPassword):
      #check the user exists first
      db = get_db()
      sql = "SELECT Password FROM GLB_Accounts where Email = ?"
      counter = 0
      for row in db.cursor().execute(sql, [userName]):
            counter =+ 1
      
      if counter > 0:
            userActualPass = row
      else:
            return "user does not exist!"
      
      #I'm really not proud of this, but it works
      check = "(u'" + userPassword + "',)"
      
      if str(userActualPass) == str(check):
            #if the passwords match, then the user is who they say they are, log them in 
            return start_sesh(userName)
      else:
            #the passwords dont match, so flash the user
            return 'incorrect password'
      
      db.close()

@app.route("/logout")
def close_sesh():
      #check if a user is actually in a session first
      if 'userName' in session:
            session.pop('userName', None)
            #check the user was actually logged out
            if 'userName' in session:
                  return "Logout failed! :("
            else:
                  return "Logged out successfully!"
      else:
            #return them to /
            return determine_user_path()
      
@app.route("/hard-login")
def debug_log_in():
      #used to force log in until the user accounts are built
      session['userName'] = 'jt4'
      return session['userName']

@app.route("/profile/<username>")
def load_profile(username = None):
      count = 0
      #check that the user exists, if not, send the user a 404
      db = get_db()
      sql = "SELECT * from GLB_User_Profiles WHERE Username = ?"
      for row in db.cursor().execute(sql, [username]):
            #count how many rows there are
            count =+ 1
      #if theres a row, the user exists
      if count == 1:
            #get the user's basic profile elements like name, bio and country
            user = username
            userForename = row[2]
            userSurname = row[1]
            userBio = row[3]
            userCountry = row[4]
            
            #now, grab the user's posts
            #reset count
            count = 0
            sqlGetUsersPosts = "SELECT Image_Path FROM GLB_User_Posts WHERE Username = ?"
            
            for row in db.cursor().execute(sqlGetUsersPosts, [username]):
                  count =+ 1
                  
            if count > 0:
                  imageCount = count
                  userImage = row[0]
                  return render_template("profile.html", user = user, userForename = userForename, userSurname = userSurname, userBio = userBio, userCountry = userCountry, userImage = userImage, imageCount = imageCount)
            else:
                  return 'user has not posted anything'
            
      else:
            #return an error
            return session['userName']
      
      db.close()
     

@app.route("/profile/")
def redirect_user():
      #check if the user is logged in, if they are, send them to their profile, if not, send them to the index page
      if 'userName' in session:
            username = "'" + session['userName'] + "'"
            return  load_profile(username)
      else:
            return go_to_index()

            
            

#update profile actions
@app.route("/profile/update/pic", methods=['POST', 'GET'])
def get_users_profile_pic():
      session['userName'] = "jt4"
      #check if the user posted something first
      if request.method == "POST":
            userFile = request.files['updateProfilePic']
            #grab the filename, too
            userFileName = userFile.filename
            
            #check if userFile is empty
            if userFile is not None:
                  folder = "static/user-uploads/" + session['userName'] + "/profile/"
                  fileType = 'profile-pic.jpg'
                  return update_profile_pic(folder, fileType, userFile, userFileName)
            else:
                  return "upload failed, file doesn't exist!"
            
      else:
            return "didnt get anything. you used GET, didnt you?"


def update_profile_pic(folder, fileType, userFile, userFileName):
      #check if the user is still logged in first
      session['userName'] = "jt4"
      
      if 'userName' in session:
            #check if the folder exists
            if os.path.isdir(folder):
                  #if it does, check if the actual file exists
                  for thisFile in os.listdir(folder):
                        if thisFile == fileType:
                              fileToRemove = folder + fileType
                              os.remove(fileToRemove)
                              
                  #save the new image with it's dodgy name and extension
                  saveFilePath = folder + userFileName
                 
                  userFile.save(saveFilePath)

                  #now convert the image 
                  #saveFilePath = 'static/user-uploads/<username>/profile/filenameUserUploaded.png'
                  
                  #this next bit basically makes a 'save as' operation, without overwrite, so clone the image and save it as a jpeg, then delete the original png or whatever. 
                  #three hours later, this now works
                  with Image(filename=saveFilePath) as img:
                        img.format = "jpg"
                        newFile = folder + fileType
                        
                        #before we save the file, double-check that there's no file called 'profile-picture.jpg'. The chances of this are very small, but just to be safe
                        for thisFile in os.listdir(folder):
                              if thisFile == fileType:
                                    fileToRemove = newFile
                                    os.remove(fileToRemove)
                        
                        #good to save now
                        img.save(filename=newFile)
                        
                  #now remove the old file (the dodgy one)
                  os.remove(saveFilePath)
                        
                  #now list the directory, to check that it's worked
                  for eachFile in os.listdir(folder):
                       print eachFile
                  
                  #now the picture has been updated, reload the page
                  return redirect_user()
      else:
            return "you're not logged in!"
      

@app.route("/profile/update/bg", methods=['POST', 'GET'])
def get_cover_photo():
      session['userName'] = "jt4"
       #check if the user posted something first
      if request.method == "POST":
            userFile = request.files['coverPhoto']
            #grab the file name, too
            userFileName = userFile.filename
            #this will come in handy later
            coverOptions = request.form['bgPosition']
            
            #check if userFile is empty
            if userFile is not None:
                  folder = "static/user-uploads/" + session['userName'] + "/profile/"
                  fileType = 'cover-pic.jpg'
                  return update_profile_pic(folder, fileType, userFile, userFileName)
            else:
                  return "upload failed, file doesn't exist!"
            
      else:
            return "didnt get anything. you used GET, didnt you?"
      

if __name__ == "__main__":
      app.run(host="0.0.0.0", debug=True)
