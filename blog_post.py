from flask import Flask ,render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
import json
from datetime import datetime
from flask_mail import Mail
import os
from werkzeug.utils import secure_filename
import math
local_server=True
with open('config.json','r') as c:
    params=json.load(c)["params"]
app = Flask(__name__)
app.secret_key = "0802me131048"
app.config["upload_folder"]=params["upload_location"]
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT="465",
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params["gmail_user"],
    MAIL_PASSWORD=params["gmail_pass"]
)
mail=Mail(app)
if (local_server):
    app.config["SQLALCHEMY_DATABASE_URI"] = params["local_uri"]
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params["prod_uri"]
db = SQLAlchemy(app)

class Contact(db.Model):
    # SNO,Name,Email,Phone Number,Message,Date
    SNO = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(80), nullable=False)
    Email = db.Column(db.String(20), nullable=False)
    Phone_Number = db.Column(db.String(12),nullable=False)
    Message = db.Column(db.String(120),nullable=False)
    Date = db.Column(db.String(12),nullable=True)
class Posts(db.Model):
    # SNO,Name,Email,Phone Number,Message,Date
    SNO = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    Content = db.Column(db.String(120),nullable=False)
    Date = db.Column(db.String(12),nullable=True)
    img_file = db.Column(db.String(12),nullable=True)
    tag_line = db.Column(db.String(12),nullable=True)

@app.route('/')
def home():
    posts=Posts.query.filter_by().all()
    #[0:params["no_of_posts"]]
    last=math.ceil(len(posts)/int(params["no_of_posts"]))
    page=request.args.get('page')
    if (not str(page).isnumeric()):
        page=1
    page=int(page)
    posts=posts[(page-1)*int(params["no_of_posts"]):(page-1)*int(params["no_of_posts"])+int(params["no_of_posts"])]
    if (page==1):
        prev='#'
        next="/?page="+str(page+1)
    elif (page==last):
        prev="/?page="+str(page-1)
        next='#'
    else:
        prev="/?page="+str(page-1)
        next="/?page="+str(page+1)
    
    return render_template('index.html',params=params,posts=posts,prev=prev,next=next)
@app.route('/about')
def about():
    return render_template('about.html',params=params)

@app.route('/dashbord',methods=["GET","POST"])
def dashbord():
    if ("user" in session and session["user"]==params["admin_user"]):
        post=Posts.query.all()
        return render_template('dashboard.html',params=params,posts=post)
    if request.method=='POST':
        username=request.form.get('uname')
        userword=request.form.get('pass')
        if (username==params["admin_user"] and userword==params["password"]):
           session["user"]=username
           post=Posts.query.all()
           return render_template('dashboard.html',params=params,posts=post)
        else:
           return render_template('login.html',params=params)
    else:
        return render_template('login.html',params=params)
@app.route("/edit/<string:SNO>",methods=["GET","POST"])
def edit(SNO):
    if ("user" in session and session["user"]==params["admin_user"]):
        if(request.method=="POST"):
            box_title=request.form.get("title")
            tagline=request.form.get("tline")
            slug=request.form.get("slug")
            content=request.form.get("content")
            image=request.form.get("image")
            if SNO=="0":
                post=Posts(title=box_title,tag_line=tagline,slug=slug,Content=content,img_file=image,Date=datetime.now())
                db.session.add(post)
                db.session.commit()
            else:
                post=Posts.query.filter_by(SNO=SNO).first()
                post.title=box_title
                post.tag_line=tagline
                post.slug=slug
                post.Content=content
                post.img_file=image
                post.Date=datetime.now()
                db.session.commit()
                return redirect("/edit/"+SNO)
        post=Posts.query.filter_by(SNO=SNO).first()
        return render_template('edit.html',params=params,post=post)
@app.route('/uploader',methods=["GET","POST"])
def uploader():
    if ("user" in session and session["user"]==params["admin_user"]):
            if(request.method=="POST"):
                f=request.files["file1"]
                f.save(os.path.join(app.config["upload_folder"],secure_filename(f.filename)))
                return "uploaded successfullly"

@app.route('/contact',methods=["GET","POST"])
def contact():
    if(request.method=="POST"):
        '''Add Data in Database'''
        name=request.form.get('name')
        email=request.form.get('email')
        phone=request.form.get('phone')
        message=request.form.get('message')
        entry=Contact(Name=name,Phone_Number=phone,Date=datetime.now(),Email=email,Message=message)
        db.session.add(entry)
        db.session.commit()
        mail.send_message("New Message From"+name,sender=email,recipients=[params["gmail_user"]],
                         body=message+"\n"+phone)    
    return render_template('contact.html',params=params)

@app.route("/delete/<string:SNO>",methods=["GET","POST"])
def delete(SNO):
    if ("user" in session and session["user"]==params["admin_user"]):
        post=Posts.query.filter_by(SNO=SNO).first()
        db.session.delete(post)
        db.session.commit()
    return redirect("/dashbord") 
@app.route('/post')
def post():
    return render_template('post.html',params=params)
@app.route('/logout')
def logout():
    session.pop("user")
    return redirect("/dashbord")
@app.route("/post/<string:post_slug>",methods=["GET"])
def post_new(post_slug):
    post=Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html',params=params,post=post)
app.run(debug=True)