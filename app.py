from flask import Flask, g

app = Flask("__name__")

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



if __name__ == "__main__":
      app.run(host="0.0.0.0", debug=True)
