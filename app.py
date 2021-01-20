from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from tempfile import mkdtemp
import requests
import sqlite3
import os
from cs50 import SQL

from helpers import lookup, login_required, apology, flightprice, airports


# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///weather.db")

app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['SECRET_KEY'] = 'super secret key'
Session(app)

@app.route('/', methods=["GET", "POST", "DELETE"])
@login_required
def index():
  date = "2020-12"
  if request.form.get("delete"):
    db.execute("DELETE FROM locations WHERE user_id = :user_id AND name = :name",
                          user_id=session["user_id"], name=request.form.get("delete"))

  elif request.form.get("city"):
    airport = airports(request.form.get("city"), request.form.get("country"))[:-4]
    db.execute("UPDATE users SET airport = :airport WHERE id = :user",
                          user=session["user_id"], airport=airport)

  elif request.form.get("date"):
    date = request.form.get("date")

  elif request.method == "POST":
        name = request.form.get("location")
        weather = lookup(name)
        if not weather:
          return apology("Invalid location", 403)
        name = weather['name']
        country = weather['country']
        airport = airports(name, country)
        # Query database for location
        rows = db.execute("SELECT * FROM locations WHERE user_id = :user_id AND name = :name",
                          user_id=session["user_id"], name=name)

        # Error if location is duplicate
        if len(rows) != 0:
            return apology("Location is already saved", 403)

        # Create location
        db.execute("INSERT INTO locations (user_id, name, airport) VALUES (:user_id, :name, :airport)", user_id=session["user_id"], name=name, airport=airport)

  
  # User reached route via GET (as by clicking a link or via redirect)

  # Get home airport for user
  home = db.execute("SELECT airport FROM users WHERE id = :user_id", user_id=session["user_id"])[0]['airport']

  # Query database for all locations
  rows = db.execute("SELECT * FROM locations WHERE user_id = :user_id",
                    user_id=session["user_id"])
  
  locations = []
  for index, row in enumerate(rows):

    # Get Weather
    location = lookup(row['name'])

    # Get Airport
    airport = db.execute("SELECT airport FROM locations WHERE user_id = :user AND name = :name", user=session["user_id"], name=row['name'])[0]['airport']
    airport = airport[:-4]

    # Get flight price
    quotes = flightprice(home, airport, date)
    # Make a list with all the data of the location and attach it to another list indexing all the locations
    locations.append(list((location, airport, quotes, 2)))

  locations = locations[::-1]
  return render_template("index.html", locations=locations, home=home)



@app.route("/login", methods=["GET", "POST"])
def login():
  """Log user in"""
  # Forget any user_id
  session.clear()

  # User reached route via POST (as by submitting a form via POST)
  if request.method == "POST":

      # Ensure username was submitted
      if not request.form.get("username"):
          return apology("must provide username", 403)

      # Ensure password was submitted
      elif not request.form.get("password"):
          return apology("must provide password", 403)

      # Query database for username
      rows = db.execute("SELECT * FROM users WHERE username = :username",
                        username=request.form.get("username"))
      # Ensure username exists and password is correct
      if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
          return apology("invalid username and/or password", 403)

      # Remember which user has logged in
      session["user_id"] = rows[0]["id"]

      # Redirect user to home page
      return redirect("/")

  # User reached route via GET (as by clicking a link or via redirect)
  else:
      return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Ensure password was submitted
        elif not request.form.get("confirmation"):
            return apology("must provide password confirmation", 403)

        # Ensure password matches confirmation
        elif not (request.form.get("confirmation") == request.form.get("password")):
            return apology("password must match confirmation", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 0:
            return apology("username already exists", 403)

        # hash password
        hash = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)

        # Find airport
        airport = airports(request.form.get("city"), request.form.get("country"))[:-4]
        print(airport)

        # Create account
        db.execute("INSERT INTO users (username, hash, airport) VALUES (:username, :hash, :airport)", username=request.form.get("username"), hash=hash, airport=airport)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)