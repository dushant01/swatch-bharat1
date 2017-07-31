# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

# Create your views here.

from django.shortcuts import render, redirect
from datetime import datetime
from  myapp.forms import SignUpForm,LoginForm,PostForm,LikeForm,CommentForm
from myapp.models import User,SessionToken,PostModel,LikeModel,CommentModel
from datetime import timedelta
from django.utils import timezone
from myproject.settings import BASE_DIR
from django.contrib.auth.hashers import make_password,check_password
from django.http import HttpResponseRedirect
from django.contrib.auth import logout
import smtplib
from constants import constant


from imgurpython import ImgurClient

client_id = "b866621832527b5"
client_sec = "296a3fb33f4cfff095f07a8f24f50e930361445c"


# Create your views here.
def signup_view(request) :
    #Business Logic starts here

    if request.method=='GET' :  #IF GET REQUEST IS RECIEVED THEN DISPLAY THE SIGNUP FORM
        #today=datetime.now()
        form = SignUpForm()
        #template_name='signup.html'
        return render(request,'signup.html',{'form':form})

    elif request.method=='POST' :
        form = SignUpForm(request.POST)
        if form.is_valid() : #Checks While Valid Entries Is Performed Or Not
            username=form.cleaned_data['username']
            email=form.cleaned_data['email']
            name=form.cleaned_data['name']
            password=form.cleaned_data['password']
            #here above cleaned_data is used so that data could be extracted in safe manner,checks SQL injections

            #following code inserts data into database

            new_user=UserModel(name=name,password=make_password(password),username=username,email=email)
            new_user.save()   #finally saves the data in database


            #sending welcome Email To User That Have Signup Successfull	
	    message="Welcome!! you Creating Your Account in swatchbharat clean india  by dushant kumar.You Have " \
                      "Successfully Registered.It is correct place for show people about your work how you clean ur india.We Are Happy To Get You" \
                      "as one of our member "
            server = smtplib.SMTP('smtp.gmail.com',587)
            server.starttls()
            server.login('dushantk1@gmail.com',constant)
            server.sendmail('dushantk1@gmail.com',email,message)
            #   WOW!!!SUCCESSFULLY SEND EMAIL TO THE USER WHO HAS SIGNUP.USER CAN CHECK INBOX OR SPAM
            # THIS IS ACCURATLY WORKING
        return render(request,'success.html',{'form': form})




def login_view(request) :
    response_data = {}
    if request.method == 'GET' :#display form
        template='login.html'    #it will redirect to login page
        form = LoginForm()       #object


    elif request.method =='POST' :
        form = LoginForm(request.POST)
        if form.is_valid() :             #checks whether entriesd in form is valid or not
            username=form.cleaned_data['username']      #extracting username and password in secure way
            password=form.cleaned_data['password']      #which was entered by user in login form
            #check user exists in database or not
            user=UserModel.objects.filter(username=username).first()    #reads data from database
            #Above SELECT * from user model where username=username
            #This is SQL Querie for above statement

            if user :  #checks whether user exist in database or not
                #comparison of password here
                #comparison sof password here
                if check_password(password,user.password) :
                    #login successful here

                    new_token = SessionToken(user=user)
                    new_token.create_token()
                    new_token.save()
                    #response = redirect('feed/')
                    response=redirect('/feed/')
                    response.set_cookie(key='session_token', value = new_token.session_token)
                    #template = 'login_success.html'
                    return response
                    #return render(request,template,{'form':form},response)
                else:
                    #password is incorrects
                    template = 'login_fail.html'
                    response_data['message'] = "Incorrect Password!!!Try Again"
            else :
                template ='login_fail.html'
    response_data['form'] = form
    return render(request,template,{'form':form})


def feed_view(request) :
    user = check_validation(request)
    if user:

        posts = PostModel.objects.all().order_by('-created_on')

        for post in posts:
            existing_like = LikeModel.objects.filter(post_id=post.id, user=user).first()
            if existing_like:
                post.has_liked = True

        return render(request, 'feeds.html', {'posts': posts})
    else:

        return redirect('/login/')


#For Validation Of the Session In THe SErver

#For validating the session
def check_validation(request):
    if request.COOKIES.get('session_token'):
        session = SessionToken.objects.filter(session_token=request.COOKIES.get('session_token')).first()
        if session:
            time_to_live = session.created_on + timedelta(days=1)
            if time_to_live > timezone.now():
                return session.user
    else:
        return None



def post_view(request) :
    user = check_validation(request)

    if user :
        if request.method == 'POST' :
            form = PostForm(request.POST, request.FILES)
            if form.is_valid() :
                image = form.cleaned_data.get('image')
                caption = form.cleaned_data.get('caption')
                post = PostModel(user=user, image=image, caption=caption)
                post.save()

                path = str(BASE_DIR +"//"+ post.image.url)

                client = ImgurClient(client_id,client_sec)
                post.image_url = client.upload_from_path(path, anon=True)['link']
                post.save()


                return redirect('/feed/')

        else :
            form = PostForm()
        return render(request, 'posts.html', {'form' : form})

    else :
        return redirect('/login/')


def like_view(request):
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


def comment_view(request):
    user = check_validation(request)
    if user and request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            post_id = form.cleaned_data.get('post').id
            comment_text = form.cleaned_data.get('comment_text')
            comment = CommentModel.objects.create(user=user, post_id=post_id, comment_text=comment_text)
            comment.save()
            return redirect('/feed/')
        else:
            return redirect('/feed/')
    else:
        return redirect('/login')


def logout_page(request):
    logout(request)
    return HttpResponseRedirect('/login/')

