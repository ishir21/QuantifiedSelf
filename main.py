from flask import Flask,render_template, url_for,redirect,request,flash,get_flashed_messages
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, ForeignKey , DateTime
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField,SubmitField
from wtforms.validators import InputRequired,Length,ValidationError
from flask_bcrypt import Bcrypt
from datetime import datetime
import matplotlib
import matplotlib.pyplot as plt


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///final_project.sqlite3'
app.config['SECRET_KEY'] = 'ishir21'
db = SQLAlchemy()
db.init_app(app)
bcrypt = Bcrypt(app)
app.app_context().push()




login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
  return User.query.get(int(user_id))

class User(db.Model,UserMixin):
  id =Column(Integer,primary_key = True)
  username = Column(String,unique=True,nullable=False)
  password = Column(String,nullable=False)
  members = relationship("Tracker")

class Tracker(db.Model):
  T_ID = Column(Integer,primary_key=True)
  uid = Column(Integer,ForeignKey("user.id"),nullable=False)
  name = Column(String,nullable=False)
  description = Column(String,nullable=False)
  TrackerType = Column(String,nullable=False)
  settings = Column(String,nullable=True,default=None)
  last_tracked = Column(String,nullable=True)
  datas = relationship('Trackerd')


class Trackerd(db.Model):
  data_id = Column(Integer,primary_key=True)
  time = Column(String,nullable=False)
  value = Column(String,nullable=False)
  notes = Column(String)
  tracker_id = Column(Integer,ForeignKey("tracker.T_ID"),nullable=False)

class RegisterForm(FlaskForm):
  username = StringField(validators=[InputRequired(),Length(min=3,max=50)], render_kw ={"placeholder": "Username"})
  password = PasswordField(validators=[InputRequired(),Length(min=4)],render_kw={"placeholder":"Password"})
  submit = SubmitField("Register")

  # def validate_username(self,username):
  #   existingUser_username = User.query.filter_by(username =username.data).first()
  #   print(existingUser_username)

  #   if existingUser_username:
  #     flash("The email entered already exists. Please choose a different one.")

        

class LoginForm(FlaskForm):
  
  username = StringField(validators=[Length(min=3,max=50)], render_kw ={"placeholder": "Username"})

  password = PasswordField(validators=[Length(min=4,max=10)],render_kw={"placeholder":"Password"})

  submit = SubmitField("Login")

@app.route('/',methods=['GET','POST'])
def home():
  return render_template("home.html")


@app.route('/login',methods=['GET','POST'])
def login():
  form = LoginForm()
  if form.validate_on_submit():
    user = User.query.filter_by(username=form.username.data).first()
    if user:
      if bcrypt.check_password_hash(user.password,form.password.data):
        login_user(user)
        return redirect("/dashboard/{}".format(user.id))
      else:
        flash("Wrong Password")
    else:
      flash("User Does Not Exist")
    
        
  return render_template("login.html",form=form)

@app.route('/register',methods=['GET','POST'])
def register():
  form = RegisterForm()
  existingUser_username = User.query.filter_by(username =form.username.data).first()
  if existingUser_username:
     flash("User already exists")
  if form.validate_on_submit() and not existingUser_username:
    hashed_password = bcrypt.generate_password_hash(form.password.data)
    new_user = User(username = form.username.data,password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('login'))

   

  # if form.errors!={}:
  #   for err_msg in form.error.values():
  #     flash(f"There was an error with creating a user:{err_msg}")
  return render_template("register.html",form=form)
 
  

@app.route('/dashboard/<int:id>',methods=['GET','POST'])
@login_required 
def dashboard(id):
  name = current_user.username
  # print(current_user.username)
  members = User.query.filter_by(id=id).first()
  # print(members.id)
  return render_template("dashboard.html",name=name,members=members.members,id=members.id)

@app.route('/logout',methods=['GET','POST'])
@login_required
def logout():
  logout_user()
  return redirect(url_for('login'))

@app.route('/add/<int:uid>',methods=['GET','POST'])
@login_required
def addTracker(uid):
  user = User.query.filter(User.id==uid).first()
  if request.method=='POST':
    t_name = request.form['t_name']
    t_desc = request.form['t_desc']
    t_type = request.form['t_type']
    if(t_type=="multiple"):
      t_settings= request.form['t_settings']
      track =  Tracker(name=t_name,description=t_desc,TrackerType=t_type,uid=uid,settings=t_settings)
    else:
      track = Tracker(name=t_name,description=t_desc,TrackerType=t_type,uid=uid) 
    db.session.add(track)
    db.session.commit()
    return redirect("/dashboard/{}".format(uid))

  return render_template("addTracker.html")

@app.route('/log/<int:t_id>',methods=['GET','POST'])
@login_required
def log(t_id):
  tracker_details = Tracker.query.filter_by(T_ID=t_id).first()
  now = datetime.now() 
  date_time = now.strftime("%Y/%m/%d %H:%M")
  # print(tracker_details.TrackerType)
  if request.method=='POST':
    # time=request.form['time']
   
    notes = request.form['notes']
    if(tracker_details.TrackerType == "multiple"):
      tracker_details.last_tracked=date_time
      t_Val = request.form["t_Val"]
      data = Trackerd(time=date_time,value=t_Val,notes=notes,tracker_id=t_id)
    else:
      tracker_details.last_tracked=date_time
      value = request.form['value']
      data = Trackerd(time=date_time,value=value,notes=notes,tracker_id=t_id)
    db.session.add(tracker_details)
    db.session.add(data)
    db.session.commit()
    return redirect("/dashboard/{}".format(tracker_details.uid))
  return render_template("log.html",date_time=date_time,tracker_details=tracker_details)

@app.route('/updateTracker/<int:t_id>',methods=['GET','POST'])
@login_required
def updateT(t_id):
  trackerupd = Tracker.query.filter_by(T_ID=t_id).first()
  if(request.method=='GET'):
    return render_template("update_tracker.html",trackerupd=trackerupd)
  else:
    t_newname = request.form.get('t_newname')
    t_newdesc = request.form.get('t_newdesc')

    trackerupd.name = t_newname
    trackerupd.description = t_newdesc
    db.session.add(trackerupd)
    db.session.commit()
    return redirect("/dashboard/{}".format(trackerupd.uid))

@app.route('/deleteTracker/<int:t_id>',methods=['GET','POST'])
@login_required
def deleteT(t_id):
  trackerdel = Tracker.query.filter_by(T_ID=t_id).first()
  members = User.query.filter_by(id=trackerdel.uid).first()
  trackerLog = Trackerd.query.filter_by(tracker_id=t_id).first()
  # db.session.delete(trackerdel)
  Tracker.query.filter_by(T_ID=t_id).delete()
  Trackerd.query.filter_by(tracker_id=t_id).delete()
  # db.session.delete(trackerLog)
  db.session.commit()
  return redirect("/dashboard/{}".format(trackerdel.uid))

@app.route('/viewlogs/<int:t_id>',methods=['GET','POST'])
@login_required
def view(t_id):
  name = current_user.username
  tracker_details = Tracker.query.filter_by(T_ID=t_id).first()
  log_details=Trackerd.query.filter_by(tracker_id=t_id).all()
  log_details_delete=Trackerd.query.filter_by(tracker_id=t_id).first()
  if tracker_details.TrackerType=="numerical":
    num_graph(tracker_details.T_ID, log_details)
  else:
    multi_graph(tracker_details.T_ID,log_details)
  return render_template("view_log.html",log_details=log_details,name=name,tracker_details=tracker_details,log_details_delete=log_details_delete)

@app.route('/updateLog/<int:t_id>/<int:d_id>',methods=['GET','POST'])
@login_required
def updateL(t_id,d_id):
  tracker_details = Tracker.query.filter_by(T_ID=t_id).first()  
  log_details = Trackerd.query.filter_by(tracker_id=t_id).all()
  log = Trackerd.query.filter_by(data_id=d_id).first()
  # data = Trackerd.query.filter_by(data_id=d_id).first()
  if (request.method=='GET'):
    return render_template('update_log.html',log_details=log_details,tracker_details=tracker_details,log=log)
  else:
    newtime = request.form.get('newtime')
    newtime_final = newtime.replace('T',' ')
    # format_time = newtime.strftime("%Y/%m/%d, %H:%M:%S")
    # format_time_final = datetime.strptime(newtime_final, '%d/%m/%y %H:%M:%S')
    newnotes = request.form.get('newnotes')
    tracker_details.last_tracked= newtime_final
    log.time = newtime_final
    log.notes = newnotes
    if(tracker_details.TrackerType=="multiple"):
      newt_Val = request.form.get('newt_Val')
      log.value = newt_Val
    else:
      newvalue = request.form.get('newvalue')
      log.value = newvalue
    db.session.add(tracker_details)
    db.session.add(log)
    db.session.commit()
    return redirect("/viewlogs/{}".format(tracker_details.T_ID))

@app.route('/deleteLog/<int:d_id>',methods=['GET','POST'])
@login_required
def deleteL(d_id):
  log_details = Trackerd.query.filter_by(data_id=d_id).first()
  Trackerd.query.filter_by(data_id=d_id).delete()
  db.session.commit()
  return redirect("/viewlogs/{}".format(log_details.tracker_id))  

def num_graph(t_id,logs):
  x_list=[]
  y_list=[]
  values={}

  for i in logs:
    x_list.append(i.time)
    y_list.append(int(i.value))
  
  # values_final = sorted(values.items(), key=lambda x: x[1])
  # print(values_final)

  # for key in sorted(values):
  #   x_list.append(key)
  #   y_list.append(values[key])
    
  print(x_list)
  print(y_list)
  plt.xlabel("Timestamp")
  plt.ylabel("Values")
  plt.title("Summary")
  plt.xticks(rotation=20) 
  plt.plot(x_list,y_list,color='red')
  plt.tight_layout(pad=3)
  filename = "static/images/numerical_graph_"+str(t_id)+".png"
  plt.savefig(filename)
  plt.close()

  return filename

def multi_graph(t_id,logs):
    # log_details=Trackerd.query.filter_by(tracker_id=t_id).all()
  tracker_details = Tracker.query.filter_by(T_ID=t_id).first()
  choices_val = tracker_details.settings.split(',')
  print(choices_val)  
  choices_dict= dict.fromkeys(choices_val,0)
  print(choices_dict)

  # for choice in choices_val:
  #   choices_dict[choices_val] = 0
  
  for log in logs:
    choice = log.value.split(',')
    for i in choice:
      choices_dict[i]+=1

  x_list = choices_dict.keys()
  y_list = choices_dict.values()

  plt.xlabel("Choices")
  plt.ylabel("Frequency")

  y_range = [i for i in range(0,100)]
  plt.yticks(y_range)
  plt.bar(x_list,y_list,color=['blue','green','yellow','purple'])
  filename = "static/images/multiple_graph_"+str(t_id)+".png"
  plt.savefig(filename)
  plt.close()

  return filename




if __name__ == '__main__':
  app.run(debug=True)