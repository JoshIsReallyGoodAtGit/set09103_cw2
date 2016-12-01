from flask import Flask, g, session, render_template, flash, url_for, request, redirect
from datetime import date
from werkzeug.utils import secure_filename
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
            #grab the user's details
            userForename = request.form['user-forename']
            userSurname = request.form['user-surname']
            userEmail = request.form['email']
            userPassword = request.form['password']
            
            #check that none of the entries are blank, if they are notify the user
            if userForename == "" or userSurname == "" or userEmail == "" or userPassword == "":
                  #user didn't post anything we can use, flash them (not literally!!)
                  return 'empty!'
            else:
                  #now would be a good time to sanitise the input...
                  return add_user(userForename, userSurname, userEmail, userPassword)
      else:
            #the user is accessing this via GET, which they probably shouldn't be able to do, so send 'em away
            return redirect('/')

def add_user(userForename, userSurname, userEmail, userPassword):
      #add data to the record
            db = get_db()
            
            #create a username for the user. Format: forename.surname.123x
            userNameA = userForename + "." + userSurname + str(random.randint(1,10))
            print str(userNameA)
            
            #manually assign a username for now
            db.cursor().execute("INSERT INTO GLB_Accounts ('Username', 'Email', 'Password') VALUES (?, ?, ?)", [userNameA, userEmail, userPassword])
            db.commit()
            
            #check the user has been added
            sql="SELECT Username FROM GLB_Accounts WHERE Username = ?"
            for row in db.cursor().execute(sql, [userNameA]):
                  if row is not None:
                        userBio = "Say something about yourself."
                        userCountry  = "Earth"
                        

                        #now thats done, we need to add the user's personal profile
                        db.cursor().execute("INSERT INTO GLB_User_Profiles ('Username', 'Surname', 'Forename', 'Bio', 'Country')  VALUES (?, ?, ?, ?, ?)", [userNameA, userSurname, userForename, userBio, userCountry])
                        db.commit()
                        
                        #now the user has created an account, they will be auto-logged in
                        return start_sesh(userNameA)
                  else:
                        return something_went_wrong()
            db.close()
            
      
      
@app.route("/account") 
def display_options_to_user():
      #this function displays different options to the user based in whether or not they're logged in
      if 'userName' in session:
            #show a 'logout' and 'view profile'
            return render_template("account.html")
      
      else:
            #if not, show a log in form
            return redirect(url_for("log_in"))


@app.route("/login", methods=['POST', 'GET'])
def log_in():
      #retrieve the form
      if request.method == 'POST':
            userName = request.form['login-username']
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
            return render_template("login.html")

            
      
      
def auth_user_login(userName, userPassword):
      #check the user exists first
      db = get_db()
      sql = "SELECT Password FROM GLB_Accounts where Username = ?"
      counter = 0
      for row in db.cursor().execute(sql, [userName]):
            counter =+ 1
      
      if counter > 0:
            userActualPass = row[0]
            if str(userActualPass) == str(userPassword):
                  #if the passwords match, then the user is who they say they are, log them in
                  return start_sesh(userName)
            else:
                  #the passwords dont match, so flash the user
                  flash('Incorrect Email Or Password :(')
                  return redirect(url_for("log_in"))
      else:
           #the email address doesnt exist in the database, so flash the user
            flash('Incorrect Email Or Password :(')
            return redirect(url_for("log_in"))
      
     
      db.close()

      
def start_sesh(userName):
      #start the session
      session['userName'] = userName
      #redirect the user
      flash("Logged in!", 'success')
      return redirect(url_for("get_feed"))


      
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


@app.route("/profile/<username>")
def load_profile(username):

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
                  return something_went_wrong(403)
      
      db.close()
     

@app.route("/profile/")
def load_profile_if_logged_in():
      #check if the user is logged in, if they are, send them to their profile, if not, send them to the index page
      if 'userName' in session:
            username = session['userName']
            return  load_profile(username)
      else:
            return not_today(403)
      

#update profile actions
@app.route("/profile/update/pic", methods=['POST', 'GET'])
def get_users_profile_pic():
      if 'userName' in session:
            #check if the user posted something first
            if request.method == "POST":
                  file = request.files['updateProfilePic']
                  #grab the filename, too
                  filename = file.filename
                  
                   #check if userFile is empty
                  if file is not None:
                        folderType = "profile"
                        fileType = 'profile-pic'
                        
                        #save the file first, then once thats done, add the post to the database, then reload the feed
                        if setup_folders(file, filename, folderType, fileType):
                            return load_profile_if_logged_in()
                  
                  else:
                        return something_went_wrong()
            
            else:
                  return something_went_wrong()
      else:
             return not_today(403)


@app.route("/profile/update/bg", methods=['POST', 'GET'])
def get_cover_photo():
      #check if the user is still logged in first
      if 'userName' in session:
            #check if the user posted something first
            if request.method == "POST":
                  file = request.files['coverPhoto']
                  #grab the file name, too
                  filename = file.filename
            
                  #check if userFile is empty
                  if file is not None:
                        folderType = "profile"
                        fileType = 'cover-pic'
                        
                        #save the file first, then once thats done, add the post to the database, then reload the feed
                        if setup_folders(file, filename, fileType, folderType):
                            return 'done'
                        
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
      if 'userName' in session:
            #check if the user posted something
            if request.method == "POST":
                  postDesc = request.form['postDesc']
                  postLocation = request.form['postLocation']
                  file = request.files['postPhoto']
                  #grab the filename too
                  filename = file.filename
                  
                  #check if userFile is empty
                  if file is not None:
                        folderType = 'posts'
                        #before we prep the image, we need to create a PostID used in the image name and in the database
                        #PostID = username-random string
                        postID = str(session['userName']) +  "-" + ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(6)) 
                        
                        
                        #prep the image and save it
                        fileType = postID
                        
                        #save the file first, then once thats done, add the post to the database, then reload the feed
                        if setup_folders(file, filename, fileType, folderType):
                              if add_user_post(postID, postDesc, postLocation):
                                    return get_feed()
                              
                  else:
                        return something_went_wrong()
            
            else:
                  return something_went_wrong()
            
      else:
            return not_today(403)
            
            
def add_user_post(postID, postDesc, postLocation):
      db = get_db()
      
      #check if postDesc is empty
      if postDesc == "":
            postDesc = "null"
            
      #grab the username
      postAuthor = session['userName']
      
      #grab todays date 
      todaysDate = date.today()
      
      #write the query and execute it
      db.cursor().execute("INSERT INTO GLB_User_Posts ('Post_ID', 'Post_Author','Date_Posted', 'Post_Desc','Post_Loc') VALUES (?, ?, ?, ?, ?)", [postID, postAuthor, todaysDate, postDesc, postLocation])
      db.commit()
      
      #do the next function, in this case, return the user to their feed
      return True



#update profile location and bio
@app.route("/profile/update/loc", methods=['POST'])
def update_user_country():
      if 'userName' in session:
            if request.method == "POST":
                  #grab the file
                  newLocation = request.form['userCountry']
                  #write the query
                  db = get_db()
                  username = session['userName']
            
                  db.cursor().execute("""UPDATE GLB_User_Profiles 
                                                                   SET Country = ?
                                                                   WHERE Username = ?""", (newLocation, username))
                  db.commit()
                  return load_profile_if_logged_in()
      
            else:
                  return not_today(403)
            
      else:
            return not_today(504)
      
#update profile location and bio
@app.route("/profile/update/bio", methods=['POST'])
def update_user_bio():
      if 'userName' in session:
            if request.method == "POST":
                  #grab the file
                  newBio = request.form['userBio']
                  #write the query
                  db = get_db()
                  username = session['userName']
            
                  db.cursor().execute("""UPDATE GLB_User_Profiles 
                                                                   SET Bio = ?
                                                                   WHERE Username = ?""", (newBio, username))
                  db.commit()
                  return load_profile_if_logged_in()
      
            else:
                  return not_today(403)
            
      else:
            return not_today(403)

@app.route("/search/", methods=["POST", "GET"])
def get_search_results():
      if request.method == "POST":
            #grab the search text
            #add .get to the request.form function, otherwise it will break!
            searchQuery = request.form.get("searchTxt")
            
            db = get_db()
            counter = 0
            #create the query
            sql = """SELECT Username, Forename, Surname, Country 
                                                                                    FROM GLB_User_Profiles 
                                                                                    WHERE Username LIKE '%{term}%' """.format(term = searchQuery)
            
            rows = db.cursor().execute( """SELECT Username, Forename, Surname, Country 
                                                                                    FROM GLB_User_Profiles 
                                                                                    WHERE Username LIKE '%{term}%' """.format(term = searchQuery))
            
            for row in db.cursor().execute(sql):
                  counter = counter + 1
                  
            if counter > 0:
                  queryHasResults = True
            else:
                  queryHasResults = False
                  
            userPosted = True
            return render_template("search.html", rows = rows, queryHasResults = queryHasResults, userPosted = userPosted)
            
      else:
            #dont abort the page, the user just wants to search on this page
            queryHasResults = False
            userPosted = False
            rows = "0"
            return render_template("search.html", rows = rows, queryHasResults = queryHasResults, userPosted = userPosted)
            
            
            
#image handling
def parent_folder_exists(parentFolder):
      if os.path.isdir(parentFolder):
            return True
            
      else:
            #make the folder
            os.mkdir(parentFolder)
            return True
            
            
def  child_folder_exists(childFolder):
      if os.path.isdir(childFolder):
            return True
            
      else:
            #make the folder
            os.mkdir(childFolder)
            return True
      
      

      
def setup_folders(file, filename, fileType, folderType):
#check if they've got a folder
      parentFolder = "static/user-uploads/" + session['userName'] + "/"
      childFolder = parentFolder + folderType + "/"
            
      if parent_folder_exists(parentFolder):
            if child_folder_exists(childFolder):
                  #now the folder exists, save the file
                  if save_file(childFolder, file, filename, fileType):
                        return True
                  
            else:
                  return "child not created"
                  
      else:
            return "parent not created"
      
      
def allowed_file(file, filename, allowedExts, childFolder, fileType):
      #check the user isn't doing anything fishy by checking the file extension
      return "." in filename and filename.rsplit('.', 1)[1] in allowedExts


def save_file(childFolder, file, filename, fileType):
      #specify the safe/allowed file extensions
      allowedExts = set(['jpg', 'jpeg', 'gif', 'png'])
            
      if file and allowed_file(file, filename, allowedExts, childFolder, fileType):
                                    #path/            somepic-jpg
            fileToSave = childFolder + filename
            #fileToSave = secure_filename(fileToSave)
            
            #print str(fileToSave)
            file.save(fileToSave)
            
            #now we need to delete any old files with the same name, to prevent storing two files wih the same name but different extension, which one should the user see?
            
            for file in os.listdir(childFolder):
                  #to check if the file matches, need to grab the filename
                  path = childFolder + file
                  base = os.path.basename(path)
                  thisFileName = os.path.splitext(base)[0]
                        #profile-pic         profile-pic
                  if thisFileName == fileType:
                        os.remove(path)
                        print 'deleted: ' + str(path)
                  else:
                        print 'not found'
                        
            #now thats done, we can rename the file
            #grab the extension of the old name of the file
            base = os.path.basename(fileToSave)
            ext = os.path.splitext(base)[1]
            
            fileRename = childFolder + fileType + ext
            os.rename(fileToSave, fileRename)            
            
                        
            return True
            
      else:
            return not_today(403)
      
      
      
#error handlers      
@app.errorhandler(404)
def uhOh(error):
      return render_template("404.html")

@app.errorhandler(405)
def not_today(error):
      return render_template("403.html")

@app.errorhandler(403)
def not_today(error):
      return render_template("403.html")


#for when SHTF
def something_went_wrong():
      return render_template("stuck.html")


if __name__ == "__main__":
      app.run(host="0.0.0.0")