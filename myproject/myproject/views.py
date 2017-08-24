# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# Create your views here.

from django.shortcuts import render, redirect
from datetime import datetime
from myapp.forms import SignUpForm, LoginForm, PostForm, LikeForm, CommentForm
from myapp.models import User, SessionToken, PostModel, LikeModel, CommentModel
from datetime import timedelta
from django.utils import timezone
from myproject.settings import BASE_DIR
from django.contrib.auth.hashers import make_password, check_password
from django.http import HttpResponseRedirect
from django.contrib.auth import logout
import smtplib
from constants import constant
import ctypes
from clarifai.rest import ClarifaiApp
from clarifai import rest
from clarifai.rest import Image as ClImage

from imgurpython import ImgurClient

client_id = "b866621832527b5"
client_sec = "296a3fb33f4cfff095f07a8f24f50e930361445c"


# Create your views here.
def signup_view(request):
    # Business Logic starts here

    if request.method == 'GET':  # IF GET REQUEST IS RECIEVED THEN DISPLAY THE SIGNUP FORM
        # today=datetime.now()
        form = SignUpForm()
        # template_name='signup.html'
        return render(request, 'signup.html', {'form': form})

    elif request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():  # Checks While Valid Entries Is Performed Or Not
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            name = form.cleaned_data['name']
            password = form.cleaned_data['password']
            # here above cleaned_data is used so that data could be extracted in safe manner,checks SQL injections

            # following code inserts data into database

            new_user = User(name=name, password=make_password(password), username=username, email=email)
            new_user.save()  # finally saves the data in database

            # sending welcome Email To User That Have Signup Successfull
            message = "Welcome!! you Creating Your Account in swatchbharat clean india  by dushant kumar.You Have " \
                      "Successfully Registered.It is correct place for show people about your work how you clean ur india.We Are Happy To Get You" \
                      "as one of our member "
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login('dushantk1@gmail.com', constant)
            server.sendmail('dushantk1@gmail.com', email, message)
            #   WOW!!!SUCCESSFULLY SEND EMAIL TO THE USER WHO HAS SIGNUP.USER CAN CHECK INBOX OR SPAM
            # THIS IS ACCURATLY WORKING

            return redirect('/login/')
        return render(request,'success.html',{'form': form})

        return render(request, 'success.html', {'form': form})


# -------------------------------------create a new function for login  user---------------------------------------------------------
def login_view(request):
    # ----------------------------------here is the function logic-----------------------------------------------------------------
    if request.method == 'GET':
        # Display Login Page
        login_form = LoginForm()
        template_name = 'login.html'
    # ---------------------------------------Elif part---------------------------------------------------------------------------------
    elif request.method == 'POST':
        # Process The Data
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            # Validation Success
            username = login_form.cleaned_data['username']
            password = login_form.cleaned_data['password']
            # read Data From db
            user = User.objects.filter(username=username).first()
            if user:
                # compare Password
                if check_password(password, user.password):
                    token = SessionToken(user=user)
                    token.create_token()
                    token.save()
                    response = redirect('/feed/')
                    response.set_cookie(key='session_token', value=token.session_token)
                    return response
                    # successfully Login

                    template_name = 'login_success.html'
                else:

                    # Failed
                    template_name = 'login_fail.html'
            else:
                # user doesn't exist
                template_name = 'login_fail.html'
        else:
            # Validation Failed
            template_name = 'login_fail.html'

    return render(request, template_name, {'login_form': login_form})


# -------------------------------------------Create a new function for post --------------------------------------------------------------
def post_view(request):
    # -----------------------------------------here is the function logic------------------------------------------------------------
    user = check_validation(request)

    if user:
        if request.method == 'POST':
            form = PostForm(request.POST, request.FILES)
            if form.is_valid():
                image = form.cleaned_data.get('image')
                caption = form.cleaned_data.get('caption')
                post = PostModel(user=user, image=image, caption=caption)
                post.save()

                path = str(BASE_DIR + "//" + post.image.url)

                client = ImgurClient(client_id, client_sec)
                post.image_url = client.upload_from_path(path, anon=True)['link']
                post.save()

                return redirect('/feed/')

        else:
            form = PostForm()

        return render(request, 'posts.html', {'form' : form})

        return render(request, 'posts.html', {'form': form})

    else:
        return redirect('/login/')


# --------------------------------------------Create a new functions to show the all post of user--------------------------------------
def feed_view(request):
    user = check_validation(request)
    if user:
        # -------------------------------------here is the functions logic---------------------------------------------------------------

        posts = PostModel.objects.all().order_by('-created_on', )

        for post in posts:

            existing_like = LikeModel.objects.filter(post_id=post.id, user=user).first()
            if existing_like:
                post.has_liked = True


        return render(request, 'feeds.html', {'posts': posts})
    else:

        return redirect('/login/')


# ----------------------------------------------Create a new functions to like the user post-------------------------------------------
def like_view(request):
    # -------------------------------------------here is the function logic------------------------------------------------------------
    user = check_validation(request)
    if user and request.method == 'POST':
        form = LikeForm(request.POST)
        if form.is_valid():
            post_id = form.cleaned_data.get('post').id
            existing_like = LikeModel.objects.filter(post_id=post_id, user=user).first()
            if not existing_like:
                LikeModel.objects.create(post_id=post_id, user=user)
            else:
                existing_like.delete()

            return redirect('/feed/')

    else:
        return redirect('/login/')


# ------------------------------------------------Create a new functions to comment on a user post---------------------------------------
def comment_view(request):
    # ----------------------------------------------here is the function logic-------------------------------------------------------
    user = check_validation(request)
    if user and request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            post_id = form.cleaned_data.get('post').id
            comment_text = form.cleaned_data.get('comment_text')
            comment = CommentModel.objects.create(user=user, post_id=post_id, comment_text=comment_text)
            comment.save()
            # TODO: ADD MESSAGE TO INDICATE SUCCESS
            return redirect('/feed/')
        else:
            # TODO: ADD MESSAGE FOR FAILING TO POST COMMENT
            return redirect('/feed/')
    else:
        return redirect('/login')

def add_category(post):
    app = ClarifaiApp(api_key='{cf613fcdc74449948a0a7cfa7fb363bf}')

    # Logo model

    model = app.models.get('general-v1.3')
    response = model.predict_by_url(url=post.image_url)

    if response["status"]["code"] == 10000:
        if response["outputs"]:
            if response["outputs"][0]["data"]:
                if response["outputs"][0]["data"]["concepts"]:
                    for index in range(0, len(response["outputs"][0]["data"]["concepts"])):
                        category = CategoryModel(post=post,
                                                 category_text=response["outputs"][0]["data"]["concepts"][index][
                                                     "name"])
                        category.save()
                else:
                    print "No concepts list error."
            else:
                print "No data list error."
        else:
            print "No output lists error."
    else:
	print "Response code error."



# -----------------------------------------------Create a functions for validating the session---------------------------------------------
def check_validation(request):
    # ----------------------------------------------here is the function logic----------------------------------------------------------
    if request.COOKIES.get('session_token'):
        session = SessionToken.objects.filter(session_token=request.COOKIES.get('session_token')).first()
        if session:
            time_to_live = session.created_on + timedelta(days=1)
            if time_to_live > timezone.now():
                return session.user
    else:
        return None


def logout_page(request):
    logout(request)

