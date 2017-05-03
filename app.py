#!/usr/bin/python
#from flask import Flask, Response, render_template, url_for, send_from_directory, session, g

import os
import json
import pprint

from flask import url_for, session, redirect, jsonify, render_template, send_from_directory
from flask_oauth import OAuth

from flask import request as xx
import requests as yy

##
from urllib import quote
from urllib import urlencode
import flask_login as flask_login
import argparse
##
###for login
from flask_wtf import Form
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired
from flask_googlemaps import GoogleMaps
from flask_googlemaps import Map

from flask import Flask
app = Flask(__name__)
app.config.from_object('config')

app.config.update(
    DEBUG = True,
)

app.secret_key = app.config["SECRET_KEY"]

CSRF_ENABLED = True

# setting up the database
from pymongo import MongoClient
client = MongoClient('localhost', 27017)
# make a database called saved


db = client.saved


# yelp search database
#saved_search = db.saved
yelpdb = db.yelpdb
# user names database
users = db.users
bar_search3 = db.bar_search3

client.drop_database('bar_search2')
#
#for post in bar_search3.find():
#    pprint.pprint(post)
#print("*****")

login_manager = flask_login.LoginManager()
login_manager.init_app(app)

#
class User(flask_login.UserMixin):
    pass

#forms that are used
class LoginForm(Form):
    username = StringField('username', validators=[DataRequired()])
    password = StringField('password', validators=[DataRequired()])
    email = StringField('email', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)

class SearchForm(Form):
    search_term = StringField('name', validators=[DataRequired()])
    location = StringField('location', validators=[DataRequired()])

class RegisterForm(Form):
    username = StringField('username', validators=[DataRequired()])
    password = StringField('password', validators=[DataRequired()])
    email = StringField('email', validators=[DataRequired()])
    height = StringField('height', validators=[DataRequired()])
    weight = StringField('weight', validators=[DataRequired()])
    gender = StringField('gender')
    
class bar_searchForm(Form):
    drunk_level = StringField('drunk_level')
    area = StringField('area', validators=[DataRequired()])

# API constants, you shouldn't have to change these.
API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
BUSINESS_PATH = '/v3/businesses/'  # Business ID will come after slash.
TOKEN_PATH = '/oauth2/token'
GRANT_TYPE = 'client_credentials'
SEARCH_LIMIT = 5

CLIENT_ID = app.config['CLIENT_ID']
CLIENT_SECRET = app.config['CLIENT_SECRET']
#app.config['CLIENT_SECRET']

app.config['GOOGLEMAPS_KEY']

#array thing for google maps yelp combo thing
#zips = {
#    "West Roxbury": "02132","Jamaica Plain": "02130","Boston": "02121","Boston": "02122","Boston":"02125","Boston":"02119","South Boston": "02127","South End": "02118","Mission Hill": "02120","Fenway": "02215","Back Bay": "02216","Seaport": "02210","Downtown Boston": "02108",
#    "Downtown Boston":"02110","Downtown Boston":"02203","Downtown Boston":"02109","Downtown Boston":"02222",
#    "Charlestown":"02129", "Brighton":"02135", "Allston": "02134",
#    "Cambridge":"02139","Cambridge":"02141","Cambridge":"02140", "Harvard Square": "02138","Somerville":"02145","Somerville":"02143","Davis Square":"02144" 
#}


@login_manager.user_loader
def load_user(email):
    find_user = users.find_one({"email":email})
    if not find_user:
        return
    user = User()
    user.id = email

    return user

#
@app.route('/')
@app.route('/index')

def index():
    return render_template('homepage.html',
                            title='Home')

@app.route('/search', methods=['GET','POST'])
@flask_login.login_required
def search():
     form = SearchForm()
     # in the database
     uid = (flask_login.current_user.id)
     if form.validate_on_submit():
        
        search_term = form.search_term.data
        location = form.location.data
        
        test1 = yelpdb.find_one({"search":search_term})
        test2 = yelpdb.find_one({"location":location})
        if(test1 and test2):
            print("already in the database")
            print(test1)
            return render_template('index.html',
                            search_term = search_term,
                            results = test2)
            
        else:
            print("not in the database yet")
            results = query_api(search_term, location)#query_api(search_term, location)
            new_post = {"search": search_term,
                            "location": location,
                            "rest1":results[1],
                            "rest2": results[2],
                            "rest3": results[3],
                            "rest4": results[4]}
            yelpdb.insert(new_post)
            test4 = yelpdb.find_one({"location":location})
            
            if(test4):
                return render_template('index.html',
                        search_term = search_term,
                        results = test4)

     return render_template('search.html',
                            title='Search',
                            form = form)
@app.route('/logout')
@flask_login.login_required
def logout():
#    #uid = (flask_login.current_user.id)
    flask_login.logout_user()
    return render_template('homepage.html')
#
## index view function suppressed for brevity

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
         # see if its in the database

        find_user = users.find_one({"email":email})
        #usename = users.find_one({"email":email}, {'username': 1})

        if(find_user):
            # now check if its the right password
            pwd = users.find_one({"email":email}, {'password': 1})

            if (password == pwd['password']):
                user = User()
                user.id = email
                print(flask_login.login_user(user))#, remember =True)
                flask_login.login_user(user)
                
                print("user already registed in the database" )
                #return redirect(url_for('mapview'))

                #return render_template('maptest.html', username = usename["username"])#, username = usename["username"])
                return redirect(url_for('facebook_login'))
            else:
                # if not the right password
                return 'Bad Login'

        else:
            print("user name not in the database yet")
            return "<a href='/login'>Try again</a>\
                    </br><a href='/register'>or make an account</a>"

    return render_template('login.html',
                           title='Sign In',
                           form=form)
#
def getuseridfromemail(email):
    uid = users.find_one({"email":'bob.test.com'}, {'username':1})
    return uid
    #cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
    #return cursor.fetchone()[0]

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('unauth.html')

@app.route("/register", methods=['GET','POST'])
def register_user():
    form = RegisterForm()
    username = form.username.data
    password = form.password.data
    email = form.email.data
    height = form.height.data
    weight = form.weight.data
    gender =  form.gender.data
    if(gender):
        print("gender!!!!! " + gender)
    test =  isemailUnique(email)

    if test:
        new_post = {
            "username":username,
            "password":password,
            "email": email,
            "height": height,
            "weight": weight,
            "gender": gender
        }
        user = User()
        user.id = email
        flask_login.login_user(user, remember = True)

        users.insert(new_post)
        uid = (flask_login.current_user.id)

        return redirect(url_for('facebook_login'))#zrender_template("maptest.html", username = username)
    else:
        print("couldn't find all tokens")
        return render_template('register.html',
                                title='Register',
                                form = form)

    return render_template('register.html',
                            title='Register',
                            form = form)

def isemailUnique(email):
    #use this to check if a email has already been registered
    find_user = users.find_one({"email":email})
    if find_user:
        #this means there are greater than zero entries with that email
        return False
    else:
        return True

#--------------------------------------
#facebook authentication
#--------------------------------------
from flask import url_for, request, session, redirect
from flask_oauth import OAuth

FACEBOOK_APP_ID = app.config["FACEBOOK_APP_ID"]#""
FACEBOOK_APP_SECRET = app.config["FACEBOOK_APP_SECRET"]


oauth = OAuth()

facebook = oauth.remote_app('facebook',
    base_url='https://graph.facebook.com/',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    consumer_key=FACEBOOK_APP_ID,
    consumer_secret=FACEBOOK_APP_SECRET,
    request_token_params={'scope': ('email, ')}
)

@facebook.tokengetter
def get_facebook_token():
    return session.get('facebook_token')

def pop_login_session():
    session.pop('logged_in', None)
    session.pop('facebook_token', None)
    

@app.route("/facebook_login")
def facebook_login():
    return facebook.authorize(callback=url_for('facebook_authorized',
        next= xx.args.get('next'), _external=True))

@app.route("/facebook_authorized")
@facebook.authorized_handler
def facebook_authorized(resp):
    next_url = xx.args.get('next') or url_for('added_marker')
    if resp is None or 'access_token' not in resp:
        return redirect(next_url)

    session['logged_in'] = True
    session['facebook_token'] = (resp['access_token'], '')

    return redirect(next_url)
#
#@app.route("/fb_logout")
#def logout():
#    pop_login_session()
#    return redirect(url_for('homepage'))


##Querying information from facebook
def get_facebook_name():
	data = facebook.get('/me').data
	print data
	if 'id' in data and 'name' in data:
		user_id = data['id']
		user_name = data['name']
		return user_name

def get_facebook_friend_appuser():
	data = facebook.get('/me?fields=friends{first_name,last_name}').data
	print data
	return data

def get_facebook_profile_url():
    data = facebook.get('/me?fields=picture{url}').data
    if 'picture' in data:
        print data['picture']
        json_str = json.dumps(data['picture'])
        resp = json.loads(json_str)
        print "json object"
        user_picture_url = data['picture']
        return data['picture']['data']['url']


#--------------------------------------
#yelp authentication
#--------------------------------------

import sys

def obtain_bearer_token(host, path):
    """Given a bearer token, send a GET request to the API.
    """
    url = '{0}{1}'.format(host, quote(path.encode('utf8')))
    #assert CLIENT_ID, "Please supply your client_id."
    #assert CLIENT_SECRET, "Please supply your client_secret."
    data = urlencode({
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': GRANT_TYPE,
    })
    headers = {
        'content-type': 'application/x-www-form-urlencoded',
    }
    response = yy.request('POST', url, data=data, headers=headers)
    bearer_token = response.json()['access_token']
    return bearer_token
#
def request(host, path, bearer_token, url_params=None):

    url_params = url_params or {}
    url = '{0}{1}'.format(host, quote(path.encode('utf8')))
    headers = {
        'Authorization': 'Bearer %s' % bearer_token,
    }

    print(u'Querying {0} ...'.format(url))

    response = yy.request('GET', url, headers=headers, params=url_params)

    return response.json()

def search(bearer_token, term, location):

    url_params = {
        'term': term.replace(' ', '+'),
        'location': location.replace(' ', '+'),
        'limit': SEARCH_LIMIT
    }
    return request(API_HOST, SEARCH_PATH, bearer_token, url_params=url_params)

def get_business(bearer_token, business_id):

    """Query the Business API by a business ID.
    Args:
        business_id (str): The ID of the business to query.
    Returns:
        dict: The JSON response from the request.
    """
    business_path = BUSINESS_PATH + business_id
    return request(API_HOST, business_path, bearer_token)
#
def query_api(term, location):

    bearer_token = obtain_bearer_token(API_HOST, TOKEN_PATH)
    response = search(bearer_token, term, location)
    businesses = response.get('businesses')

    if not businesses:
        x = (u'No businesses for {0} in {1} found.'.format(term, location))
        return x

    business_id = businesses[0]['id']
    array_ret = [None]*SEARCH_LIMIT

    for i in range(SEARCH_LIMIT):

        business_id = businesses[i]['id']
        business_name = businesses[i]['name']
        business_pic = businesses[i]['image_url']
        business_price = businesses[i]['price']
        business_rating = businesses[i]['rating']

        array_ret[i] = (business_id,business_name,business_pic,business_price,str(business_rating))

    print(u'{0} businesses found, querying business info ' \
        'for the top result "{1}" ...'.format(
            len(businesses), business_id))
    response = get_business(bearer_token, business_id)

    print(u'Result for business "{0}" found:'.format(business_id))
    #pprint.pprint(response, indent=2)
    return(array_ret)

def search2(bearer_token, term, location):

    url_params = {
        'term': term.replace(' ', '+'),
        'location': location.replace(' ', '+'),
        'limit': 20
    }
    return request(API_HOST, SEARCH_PATH, bearer_token, url_params=url_params)

zips = [
    "West Roxbury","Jamaica Plain","South Boston","South End","Mission Hill","Fenway",
    "Back Bay","Downtown","Charlestown", "Brighton", "Allston", "Cambridge","Harvard Square","Somerville","Davis Square" 
]
def query_api_2():

    bearer_token = obtain_bearer_token(API_HOST, TOKEN_PATH)
    response = search2(bearer_token, "bars", "Davis Square")
    businesses = response.get('businesses')

    if not businesses:
        x = (u'No businesses for {0} in {1} found.'.format(term, location))
        return x

    business_id = businesses[0]['id']
    array_ret = [None]*20

    for i in range(20):

        business_url = businesses[i]['url']
        business_name = businesses[i]['name']
        business_long = businesses[i]['coordinates']['longitude']
        business_lat = businesses[i]['coordinates']['latitude']

        array_ret[i] = (business_url,business_name,business_long,business_lat)

    print(u'{0} businesses found, querying business info ' \
        'for the top result "{1}" ...'.format(
            len(businesses), business_id))
    response = get_business(bearer_token, business_id)

    print(u'Result for business "{0}" found:'.format(business_id))
    #pprint.pprint(response, indent=2)
    return(array_ret)


##--------------------------------------
##google maps authentication
##--------------------------------------
#

GoogleMaps(app)
##google map testing
@app.route("/mapview")
@flask_login.login_required
def mapview():
    uid = (flask_login.current_user.id)
    height = users.find_one({"email":uid}, {'height': 1})
    weight = users.find_one({"email":uid}, {'weight': 1})
    
    print("logged in as" +uid)
    return render_template('maptest.html', 
                           username = uid, 
                           user_picture_url = get_facebook_profile_url(),
                           height = height,
                           weight = weight)
##


@app.route("/added_marker", methods = ['GET', 'POST'])
@flask_login.login_required
def added_marker():
    form = bar_searchForm()
    
    if form.validate_on_submit():
        #message = form.message.data
        area = form.area.data
        drunk_level = form.drunk_level.data
        uid = flask_login.current_user.id
        height = users.find_one({"email":uid}, {'height': 1})
        weight = users.find_one({"email":uid}, {'weight': 1})
        #gender = users.find_one({"email":uid}, {'gender': 1})
        
        
        #print(height["height"])
        print("logged in as" +uid)
#        zip_ = [v for (k,v) in zips.items() if k == area]
#        zipcode = zip_[0]
#        print(zipcode)
        
## so this is me manually getting the database going for this
#        results = query_api_2()
#        for i in range(len(results)):
#            new_post = {"location": area + str(i),
#                            "about":results[i]}
#            bar_search3.insert(new_post)

        markers = [None]*15
        for i in range(15):
            x = area + str(i)
            test1 = bar_search3.find_one({"location":x})
            #url = (test1["about"][0])
            name = (test1["about"][1])
            lat = (test1["about"][2])
            long = (test1["about"][3])
            new = [lat, long, name]
            markers[i] = new
            
       
        # trying to get this map to work
#        
        return render_template(('maptest2.html'), user_picture_url = get_facebook_profile_url(),username = uid ,height = height, weight = weight, drunk_level = drunk_level, Marker = markers)
    
    return render_template('getting_location.html',
                            title='Getting Location',
                            form = form)
@app.route("/map_unsafe")
def map_unsafe():
    
    return render_template('maptest.html')

if __name__ == '__main__':

    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
