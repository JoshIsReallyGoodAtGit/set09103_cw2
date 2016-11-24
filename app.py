from flask import Flask, g, session, render_template, flash, url_for, request, redirect
from wand.image import Image
from datetime import date
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
            #set up rows for queries
            db.row_factory = sqlite3.Row
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
           return get_feed()
      else:
            return go_to_index()

@app.route("/feed/")
def get_feed():
      #check if the user's logged in, if not, they can't access the 'post' button
      if 'userName' in session:
            userCanPost = True
      else:
            userCanPost = False
            
      #now there's posts in the database, the app can access and display them
      db = get_db()
      
      sql = """SELECT * FROM GLB_User_Posts
                        ORDER BY Date_Posted DESC"""
      
      rows = db.cursor().execute(sql).fetchall()
            
      #now the values have been retrieved, send the user to the feed
      return render_template('feed.html', rows = rows, userCanPost = userCanPost)

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
                        return something_went_wrong()
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
            return something_went_wrong()
      
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
                  return something_went_wrong()
            else:
                  return determine_user_path()
            
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
      if 'userName' in session:
            #if the username entered in the URL is the same as the user that's logged in, the user has control
            if username == str(session['userName']):
                  userHasControl = 1
                  #otherwise, lock the user from making changes
            else:
                  userHasControl = 0
                  
      #just in case
      #end if userName in session
      else:
            userHasControl = 0
            
      count = 0
      #check that the user exists, if not, send the user a 404
      db = get_db()
      sql = """SELECT * from GLB_User_Profiles 
                        WHERE Username = ?"""
      
      for row in db.cursor().execute(sql, [username]):
            if row is not None:
                  rowsForProfile = db.cursor().execute(sql, [username]).fetchone()
                  
                  #do the second query. grab the user's post data
                  sqlGetUsersPosts = "SELECT * FROM GLB_User_Posts WHERE Post_Author = ?"
                  rowsForPosts = db.cursor().execute(sqlGetUsersPosts, [username]).fetchall()
                  
                  return render_template("profile.html", userHasControl = userHasControl, rowsForPosts = rowsForPosts, rowsForProfile = rowsForProfile)
      
            else:
                  #end if row is not none
                  #the user doesn't exist
                  return something_went_wrong()
      
      db.close()
     

@app.route("/profile/")
def redirect_user():
      #check if the user is logged in, if they are, send them to their profile, if not, send them to the index page
      if 'userName' in session:
            username = session['userName']
            return  load_profile(username)
      else:
            return not_today(403)

#update profile actions
@app.route("/profile/update/pic", methods=['POST', 'GET'])
def get_users_profile_pic():
      if ['userName'] in session:
            #check if the user posted something first
            if request.method == "POST":
                  userFile = request.files['updateProfilePic']
                  #grab the filename, too
                  userFileName = userFile.filename
                  
                  #check if userFile is empty
                  if userFile is not None:
                        folder = "static/user-uploads/" + session['userName'] + "/profile/"
                        fileType = 'profile-pic.jpg'
                        return prep_user_image(folder, fileType, userFile, userFileName)  
                  
                        #now the picture has been updated, reload the page
                        return redirect_user()
                  
                  else:
                        return something_went_wrong()
            
            else:
                  return something_went_wrong()
      else:
             return not_today(403)


@app.route("/profile/update/bg", methods=['POST', 'GET'])
def get_cover_photo():
      #check if the user is still logged in first
      if ['userName'] in session:
            #check if the user posted something first
            if request.method == "POST":
                  userFile = request.files['coverPhoto']
                  #grab the file name, too
                  userFileName = userFile.filename
            
                  #check if userFile is empty
                  if userFile is not None:
                        folder = "static/user-uploads/" + session['userName'] + "/profile/"
                        fileType = 'cover-pic.jpg'
                        return prep_user_image(folder, fileType, userFile, userFileName)
                        
                  else:
                        return something_went_wrong()
            
            else:
                   return not_today(403)
      else:
             return not_today(403)


#post handlers
@app.route("/post/add", methods=['POST', 'GET'])
def get_post():
      #check the user's still logged in 
      #hard code it for dev
      session['userName'] = "jt4"
      if 'userName' in session:
            #check if the user posted something
            if request.method == "POST":
                  postDesc = request.form['postDesc']
                  postLocation = request.form['postLocation']
                  userFile = request.files['postPhoto']
                  #grab the filename too
                  userFileName = userFile.filename
                  
                  #check if userFile is empty
                  if userFile is not None:
                        folder = "static/user-uploads/" + session['userName'] + "/posts/"
                        fileType = 'post'
                        #before we prep the image, we need to create a PostID used in the image name and in the database
                        #PostID = username-random string
                        postID = str(session['userName']) +  "-" + ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(6)) 
                        
                        
                        #prep the image and save it
                        #need to pass the parameters for writing the sql query, but they wont be used in this function - 
                        #they're the last two parameters.
                        return prep_user_image(folder, fileType, userFile, userFileName, postID, postDesc, postLocation)
                        
                        
                  else:
                        return something_went_wrong()
            
            else:
                  return something_went_wrong()
            
      else:
            return not_today(403)
      
def add_user_post(postID, postDesc, postLocation, newFile):
      db = get_db()
      
      #check if postDesc is empty
      if postDesc == "":
            postDesc = "null"
            
      #grab the username
      postAuthor = session['userName']
      #grab the user's full name
      sql  = "SELECT Forename, Surname FROM GLB_User_Profiles WHERE Username = ?"
      counter = 0
      for row in db.cursor().execute(sql, [postAuthor]):
            counter =+ 1
      
      if counter > 0:
            postAuthor = str(row[0]) + " " + str(row[1])
      else:
           return something_went_wrong()
      
      #grab todays date 
      todaysDate = date.today()
      
      #write the query and execute it
      db.cursor().execute("INSERT INTO GLB_User_Posts ('Post_ID', 'Post_Author','Date_Posted', 'Post_Desc','Post_Loc') VALUES (?, ?, ?, ?, ?)", [postID, postAuthor, todaysDate, postDesc, postLocation])
      db.commit()
      
      #the post has been added, reload the feed
      return render_template('feed.html')


def prep_user_image(folder, fileType, userFile, userFileName, postID, postDesc, postLocation):
      #last to parameters not used in this function, only here to I can call the next function in the sequence
      
      #check if the user is still logged in first
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
                  
                  #this next bit basically makes a 'save as' operation, without overwrite, so clone the image and save it as a jpeg, then delete the original png or whatever. 
                  #three hours later, this now works
                  with Image(filename=saveFilePath) as img:
                        img.format = "jpg"
                        #now, resize the image so it looks okay, a cover photo should at least be 1000 x 200, a profile pic at least 100 x 100
                        if fileType == "cover-pic.jpg":
                              img.crop(10, 20, width=1920, height=500)
                              
                        elif  fileType == "profile-pic.jpg":
                              img.resize(200, 200, 'undefined')
                              
                        elif fileType == "post":
                              #do stuff
                              print 'post'
                         
                        #set the path and filename for the new file, fileType is determined in the previous function (its either a cover photo or a profile pic)
                        
                        #this added bit prevents the app from breaking if the picture uploaded is for a post
                        if fileType == "post":
                              #if it's for a post, then alter the name of the image to post_<postID>.jpg
                              newFile = folder + "post_" + postID + ".jpg"
                              
                        else:
                              #otherwise, just carry on as normal
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
                  
                  #determine where to send the user now
                  if fileType == "post":
                        #now the image has been saved, update the database
                        return add_user_post(postID, postDesc, postLocation, newFile)
                              
                  else:
                        #just a profile action
                        #now the picture has been updated, reload the page
                        return redirect_user()
                  
      else:
            return not_today(403)
      

#error handlers
      
@app.errorhandler(404)
def uhOh(error):
      return render_template("404.html")

@app.errorhandler(403)
def not_today(error):
      return render_template("403.html")


#for when SHTF
def something_went_wrong():
      return render_template("stuck.html")




if __name__ == "__main__":
      app.run(host="0.0.0.0", debug=True)