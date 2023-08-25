from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse, request
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from .models import CarModel
from .restapis import *
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime 
import logging
import json

# get an instance of a logger
logger = logging.getLogger(__name__)

# create an `about` view to render a static about page
def about(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'djangoapp/about.html', context)

# create a `contact` view to return a static contact page
def contact(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'djangoapp/contact.html', context)

# create a `login_request` view to handle sign in request
def login_request(request):
    context = {}
    # handles POST request
    if request.method == "POST":
        # get username and password from request.POST dictionary
        username = request.POST['username']
        password = request.POST['psw']
        # try to check if provide credential can be authenticated
        user = authenticate(username=username, password=password)
        if user is not None:
            # if user is valid, call login method to login current user
            login(request, user)
            return redirect('/djangoapp/')
        else:
            # if not, return to login page again
            return render(request, 'djangoapp/user_login.html', context)
    else:
        return render(request, 'djangoapp/user_login.html', context)

# create a `logout_request` view to handle sign out request
def logout_request(request):
    # get the user object based on session id in request
    print("Log out the user `{}`".format(request.user.username))
    # logout user in the request
    logout(request)
    # redirect user back to course list view
    return redirect('/djangoapp')

# create a `registration_request` view to handle sign up request
def registration_request(request):
    context = {}
    # if it is a GET request, just render the registration page
    if request.method == 'GET':
        return render(request, 'djangoapp/registration.html', context)
    # if it is a POST request
    elif request.method == 'POST':
        # get user information from request.POST
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            # check if user already exists
            User.objects.get(username=username)
            user_exist = True
        except:
            # if not, simply log this is a new user
            logger.debug("{} is new user".format(username))
        # If it is a new user
        if not user_exist:
            # create user in auth_user table
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            # login the user and redirect to course list page
            login(request, user)
            return redirect("/djangoapp/")
        else:
            return render(request, 'djangoapp/registration.html', context)

# update the `get_dealerships` view to render the index page with a list of dealerships
def get_dealerships(request):
    context = {}
    if request.method == "GET":
        url = "https://us-south.functions.appdomain.cloud/api/v1/web/5394383b-e89b-48d5-95c2-e01bbaee52b5/dealership-package/get-all-dealership.json"
        context["dealerships"] = get_dealers_from_cf(url)
        return render(request, 'djangoapp/index.html', context)

def get_dealers_from_cf(url, **kwargs):
    results = []
    json_result = get_request(url)
    if json_result:
        dealers = json_result["dealerships"]
        for doc in dealers:
            results.append(doc)        
    return results

def get_request(url, **kwargs):
    print(kwargs)
    print("GET from {} ".format(url))
    try:
        response = requests.get(
            url, headers={'Content-Type': 'application/json'}, params=kwargs)
    except:
        print("Network exception occurred")
    status_code = response.status_code
    print("With status {} ".format(status_code))
    json_data = json.loads(response.text)
    return json_data

# create a `get_dealer_details` view to render the reviews of a dealer
def get_dealer_details(request, dealer_id):
    context = {}
    if request.method == "GET":
        url = 'https://us-south.functions.appdomain.cloud/api/v1/web/5394383b-e89b-48d5-95c2-e01bbaee52b5/dealership-package/get-all-review.json'
        reviews = get_dealer_reviews_from_cf(url, dealer_id=dealer_id)
        context = {
            "reviews":  reviews, 
            "dealer_id": dealer_id
        }
        return render(request, 'djangoapp/dealer_details.html', context)

def get_dealer_reviews_from_cf(url, dealer_id, **kwargs):
    results = []
    json_result = get_request(url)
    if json_result:
        reviews = json_result["reviews"]
        for doc in reviews:
            if dealer_id == 3:
                results.append(doc)      
    return results

# create a `add_review` view to submit a review
def add_review(request, dealer_id):
    # user must be logged in before posting a review
    if request.user.is_authenticated:
        # GET request renders the page with the form for filling out a review
        if request.method == "GET":
            url = "https://us-south.functions.appdomain.cloud/api/v1/web/5394383b-e89b-48d5-95c2-e01bbaee52b5/dealership-package/all-dealership.json"
            dealerships = get_dealers_from_cf(url)
            # get dealer details from the API
            if dealer_id == 3:
                context = {
                    "cars": CarModel.objects.all(),
                    "dealer": dealerships,
                }
            return render(request, 'djangoapp/add_review.html', context)
        # POST request posts the content in the review submission form to the Cloudant DB using the post_review Cloud Function
        if request.method == "POST":
            form = request.POST
            review = dict()
            review["name"] = f"{request.user.first_name} {request.user.last_name}"
            review["dealership"] = dealer_id
            review["review"] = form["content"]
            review["purchase"] = form.get("purchasecheck")
            if review["purchase"]:
                review["purchase_date"] = datetime.strptime(form.get("purchasedate"), "%m/%d/%Y").isoformat()
            car = CarModel.objects.get(pk=form["car"])
            review["car_make"] = car.car_make.name
            review["car_model"] = car.name
            review["car_year"] = car.year            
            # if the user bought the car, get the purchase date
            if form.get("purchasecheck"):
                review["purchase_date"] = datetime.strptime(form.get("purchasedate"), "%m/%d/%Y").isoformat()
            else: 
                review["purchase_date"] = None
            url = "https://us-south.functions.appdomain.cloud/api/v1/web/5394383b-e89b-48d5-95c2-e01bbaee52b5/dealership-package/get-review.json"  # API Cloud Function route
            json_payload = {"review": review}  # create a JSON payload that contains the review data
            # performing a POST request with the review
            result = post_request(url, json_payload, dealerId=dealer_id)
            if int(result.status_code) == 200:
                print("Review posted successfully.")
            # after posting the review the user is redirected back to the dealer details page
            return redirect("djangoapp:dealer_details", dealer_id=dealer_id)
    else:
        # if user isn't logged in, redirect to login page
        print("User must be authenticated before posting a review. Please log in.")
        return redirect("/djangoapp/login")