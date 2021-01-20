import requests
from flask import redirect, render_template, request, session
from functools import wraps
import datetime


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code

def lookup(location):
  # LOOK UP WEATHER

  # Contact API
  try:
    url = "https://weatherapi-com.p.rapidapi.com/current.json"
    querystring = {"q":{location}}
    headers = {
      'x-rapidapi-key': "d4ec8627famsh26fb54a69bdab24p160042jsn0cf45f13ba8b",
      'x-rapidapi-host': "weatherapi-com.p.rapidapi.com"
      }
    response = requests.request("GET", url, headers=headers, params=querystring)
  except requests.RequestException:
      return None
  
  # Parse response
  try:
    weather = response.json()
    return {
      "temp": weather["current"]["temp_c"],
      "country": weather["location"]["country"],
      "name": weather["location"]["name"],
      "time": weather["location"]["localtime"][-5:],
      "text": weather["current"]["condition"]["text"],
      "icon": weather["current"]["condition"]["icon"],

    }
    return response.json()
  except (KeyError, TypeError, ValueError):
      return None

def airports(name, country):
  url = "https://skyscanner-skyscanner-flight-search-v1.p.rapidapi.com/apiservices/autosuggest/v1.0/NL/EUR/en-US/"

  querystring = {"query":{name}}

  headers = {
      'x-rapidapi-key': "d4ec8627famsh26fb54a69bdab24p160042jsn0cf45f13ba8b",
      'x-rapidapi-host': "skyscanner-skyscanner-flight-search-v1.p.rapidapi.com"
      }

  response = requests.request("GET", url, headers=headers, params=querystring)
  if response.json()['Places']:
    data = response.json()
    return data['Places'][0]['PlaceId']
  else:
    querystring = {"query":{country}}
    response = requests.request("GET", url, headers=headers, params=querystring)
    if response.json()['Places']:
      data = response.json()
      return data['Places'][0]['PlaceId']
    else:
      return apology("City and/or country are invalid", 403)

def flightprice(home, des, date):
  url = "https://skyscanner-skyscanner-flight-search-v1.p.rapidapi.com/apiservices/browsequotes/v1.0/NL/EUR/nl-NL/{}/{}/{}".format(home, des, date)

  headers = {
    'x-rapidapi-key': "d4ec8627famsh26fb54a69bdab24p160042jsn0cf45f13ba8b",
    'x-rapidapi-host': "skyscanner-skyscanner-flight-search-v1.p.rapidapi.com"
    }

  response = requests.request("GET", url, headers=headers)

  direct = None
  indirect = None

  for i in response.json()['Quotes']:
    if i['Direct'] == True:
      if direct == None:
        direct = i
      else:
        if i['MinPrice'] < direct['MinPrice']:
          direct = i
    if i['Direct'] == False:
      if indirect == None:
        indirect = i
      else:
        if i['MinPrice'] < indirect['MinPrice']:
          indirect = i

  
  if direct != None:
    direct = {
      "price": direct['MinPrice'],
      "date": direct['OutboundLeg']['DepartureDate'][:-9],
      # "time": direct['OutboundLeg']['DepartureDate'][-8:]
    }
  if indirect != None:
    indirect = {
      "price": indirect['MinPrice'],
      "date": indirect['OutboundLeg']['DepartureDate'][:-9],
      # "time": indirect['OutboundLeg']['DepartureDate'][-8:]
    }
  return {
    "direct": direct,
    "indirect": indirect
  }

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function