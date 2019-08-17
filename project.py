#!/usr/bin/env python3

from flask import Flask, render_template, request, redirect
from flask import jsonify, url_for, flash, g
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from db_setup import Base, Category, Items, Users
from flask import session as login_session
from functools import wraps
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Category Item Catalog"

engine = create_engine('sqlite:///appitemcatalog.db',
                       connect_args={'check_same_thread': False})
Base.metadata.bind = engine

# Creating anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data

    try:
        # Upgrading the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # validating the access token
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1].decode('utf-8'))
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    g_id = credentials.id_token['sub']
    if result['user_id'] != g_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for the given application.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_g_id = login_session.get('g_id')
    if stored_access_token is not None and g_id == stored_g_id:
        response = make_response(json.dumps('Current user is already \
            connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Storing this access token in the session
    login_session['access_token'] = credentials.access_token
    login_session['g_id'] = g_id

    # Getting user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h2>Hello, '
    output += login_session['username']
    output += '!!</h2>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 200px; height: 200px;border-radius: \
    150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output


def createUser(login_session):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    new_user = Users(name=login_session['username'], email=login_session[
        'email'])
    session.add(new_user)
    session.commit()
    user = session.query(Users).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    user = session.query(Users).filter_by(id=user_id).one()
    return user


def getUserID(email):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    try:
        user = session.query(Users).filter_by(email=email).one()
        return user.id
    except NoResultFound:
        return None

# DISCONNECT
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's session.
        del login_session['access_token']
        del login_session['g_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(
            json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # If the given token was invalid notice the user.
        response = make_response(
            json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON API
@app.route('/catalog.json')
def catalogJSON():
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    categorylist = session.query(Category).all()
    return jsonify(categoryList=[r.serialize for r in categorylist])


@app.route('/catalog/category<int:category_id>/json')
def categoryJSON(category_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    category = session.query(Category).filter_by(id=category_id).one()
    item = session.query(Items).filter_by(category_id=category.id)
    return jsonify(item=[i.serialize for i in item])


@app.route('/catalog/category<int:category_id>/item<int:item_id>/json')
def itemJSON(category_id, item_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    item = session.query(Items).filter_by(id=item_id).one()
    return jsonify(ItemDetails=[item.serialize])


# Login Required function
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' in login_session:
            return f(*args, **kwargs)
        else:
            flash("Unauthorized access")
            return redirect('/login')
    return decorated_function


# Home Page
@app.route('/')
@app.route('/catalog')
def showCatalog():
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    category = session.query(Category).all()
    item = session.query(Items).order_by(
        Items.id.desc()).limit(10)
    if 'username' not in login_session:
        return render_template('public_catalog.html', category=category,
                               item=item)
    else:
        return render_template('catalog.html', category=category,
                               item=item)


# Adding new item
@app.route('/catalog/new', methods=['GET', 'POST'])
@login_required
def newItem():
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    if request.method == 'POST':
        newItem = Items(name=request.form['name'],
                        description=request.form['description'],
                        category_id=request.form['category_id'],
                        user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash("New Item Added!")
        return redirect(url_for('showCatalog'))
    else:
        return render_template('new_item.html')


# show the items in respective category
@app.route('/catalog/<int:category_id>')
def showCategory(category_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    totalcategory = session.query(Category).all()
    category = session.query(Category).filter_by(id=category_id).one()
    item = session.query(Items).filter_by(category_id=category.id)
    return render_template('category.html', category=category, item=item,
                           totalcategory=totalcategory)


# Show the item details
@app.route('/catalog/<int:category_id>/<int:item_id>')
def showItem(category_id, item_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    category = session.query(Category).filter_by(id=category_id).one()
    item = session.query(Items).filter_by(id=item_id).one()
    if 'username' not in login_session or \
            item.user_id != login_session['user_id']:
        return render_template('public_item.html', category=category,
                               item=item)
    else:
        return render_template('item.html', category=category, item=item)


# Edit item
@app.route('/catalog/<int:category_id>/<int:item_id>/edit',
           methods=['GET', 'POST'])
@login_required
def editItem(category_id, item_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    editedItem = session.query(Items).filter_by(id=item_id).one()
    if editedItem.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized"\
            "to edit this item. Please add your item in order to edit.');"\
            "window.location = '/';}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name'] == "":
            editedItem.name = editedItem.name
        else:
            editedItem.name = request.form['name']

        if request.form['description'] == "":
            editedItem.description = editedItem.description
        else:
            editedItem.description = request.form['description']

        if request.form['category_id'] == "":
            editedItem.category_id = editedItem.category_id
        else:
            editedItem.category_id = request.form['category_id']

        session.add(editedItem)
        session.commit()
        flash("item edited successfully!")
        return redirect(url_for('showItem', category_id=category_id,
                                item_id=item_id))
    else:
        return render_template('edit_item.html', category_id=category_id,
                               item_id=item_id, item=editedItem)


# Delete the item
@app.route('/catalog/<int:category_id>/<int:item_id>/delete',
           methods=['GET', 'POST'])
@login_required
def deleteItem(category_id, item_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    itemToDelete = session.query(Items).filter_by(id=item_id).one()
    if itemToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized "\
         "to delete this item. Please add your item in order to delete"\
         " .');window.location = '/';}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash("item deleted successfully!")
        return redirect(url_for('showCategory', category_id=category_id))
    else:
        return render_template('delete_item.html', category_id=category_id,
                               item_id=item_id, item=itemToDelete)


# logout
@app.route('/disconnect')
def disconnect():
    if 'username' in login_session:
        gdisconnect()
        flash("You have been logged out.")
        return redirect(url_for('showCatalog'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showCatalog'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
