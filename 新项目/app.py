from datetime import datetime
import markdown
from email.policy import default
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app  =  Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:159357@localhost/试'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

db=SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager= LoginManager()
login_manager.init_app(app)
login_manager.login_view='login'

class User(db.Model,UserMixin):
    __tablename__  =  'user'
    id  =  db.Column(db.Integer,primary_key = True,nullable=False,autoincrement=True,comment='用户唯一id')
    username  =  db.Column(db.String(100),unique=True,nullable=False,comment='用户名字')
    email  =  db.Column(db.String(100),unique=True,nullable=False,comment='用户邮箱')
    password_hash  =  db.Column(db.String(258),nullable=False,comment='用户密码')
    avatar  =  db.Column(db.String(100),comment='用户头像路径')
    bio  =  db.Column(db.String(1000),comment='用户个人简介')
    created_at  =  db.Column(db.DateTime, default=datetime.utcnow, comment='用户注册时间')

    def set_password(self,password):
        self.password_hash  =  generate_password_hash(password)

    def check_password(self,password):
        return check_password_hash(self.password_hash,password)

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.username}>'

class Blog(db.Model):
    __tablename__ = 'blog'
    id  =  db.Column(db.Integer,primary_key = True, nullable = False, autoincrement = True, comment = '文章的唯一标识')
    title  =  db.Column(db.String(100), nullable = False, comment = '文章标题')
    author_id = db.Column(db.Integer, db.ForeignKey('user.id') ,nullable = False, comment = '编写文章的用户')
    category_id = db.Column(db.Integer,  db.ForeignKey('category.id') ,nullable = False, comment = '文章id')
    content  =  db.Column(db.Text, nullable = False, comment = '文章内容')
    create_time  =  db.Column(db.DateTime, default = datetime.utcnow,nullable = False, comment = '创建时间')
    update_time  =  db.Column(db.DateTime, default = datetime.utcnow,onupdate = datetime.utcnow,nullable = False, comment = '修改时间')
    user  =  db.relationship('User' , backref='blogs' , foreign_keys = [author_id] )
    category  =  db.relationship('Category' , backref='blogs' , foreign_keys = [category_id])

    def __repr__(self):
        return f'<{self.__class__.__name__}{self.title}>'

class Category(db.Model):
    __tablename__ = 'category'
    id  =  db.Column(db.Integer, primary_key = True, nullable = False , autoincrement = True, comment = '分类id')
    category_name  =  db.Column(db.String(100), nullable = False , comment  =  '分类标题')
    category_user_id  =  db.Column(db.Integer , nullable = False , comment = '创建用户的id')

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.category_name}>'

class Links(db.Model):
    __tablename__ = 'links'
    id  =  db.Column(db.Integer ,primary_key = True, nullable = False ,comment = '友链id')
    links  =  db.Column(db.String(100), nullable = False ,comment = '网站名称')
    href = db.Column(db.String(2000), nullable = False ,comment = '网站链接')
    sort  =  db.Column(db.Integer, nullable = False ,comment = '排序')

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.links}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register',methods=['GET','POST'])
def register():        #注册
    if request.method == 'GET':
        return render_template('register.html')
    else:
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if not username or not email or not password:
            return f'请填写所有必填项' , 400

        if User.query.filter_by(username=username).first():
            return f'该用户名已存在',400
        if User.query.filter_by(email=email).first():
            return f'该邮箱已被注册',400

        new_user=User(
            username = username,
            email = email
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('home'))

@app.route('/categories')
def category_list():    #分类列表
    categories = Category.query.all()
    return render_template('category_list.html',categories = categories)

@app.route('/category/add' , methods=['GET','POST'])
def category_add():    #添加类别
    if request.method == 'POST':

       category_name  =  request.form.get('category_name')
       category_user_id  =  1

       if not category_name:
           return '分类名不能为空' , 400

       new_category = Category(
           category_name = category_name,
           category_user_id = category_user_id
       )
       db.session.add(new_category)
       db.session.commit()

       return redirect(url_for('category_list'))

    return render_template('category_add.html')

@app.route('/category/edit/<int:id>',methods=['GET','POST'])
def category_edit(id):    #分类编辑
    category = Category.query.get_or_404(id)

    if request.method == 'POST':
        category.category_name = request.form.get('category_name')

        db.session.commit()

        return redirect(url_for('category_list'))

    return render_template('category_edit.html',category = category)

@app.route('/category/delete/<int:id>', methods=['POST'])
def category_delete(id):   #删除分类
    category = Category.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    return redirect(url_for('category_list'))

@app.route('/blogs')
def blog_list():
    blogs = Blog.query.order_by(Blog.create_time.desc()).all()
    return render_template('blog_list.html' , blogs = blogs)


@app.route('/blog/<int:id>')
def blog_detail(id):
    blog = Blog.query.get_or_404(id)
    blog.content_html = markdown.markdown(blog.content , extensions=['extra'])
    return render_template('blog_detail.html',blog = blog)

@app.route('/blog/add',methods=['GET','POST'])
@login_required
def blog_add():
    if request.method  ==  'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category_id = request.form.get('category_id')

        author_id = current_user.id

        if not title or not content or not category_id:
            return "请填写所有项目" , 400

        new_blog = Blog(
            title = title,
            content = content,
            category_id = category_id,
            author_id = author_id
        )
        db.session.add(new_blog)
        db.session.commit()
        return redirect(url_for('blog_list'))
    categories = Category.query.all()
    return render_template('blog_add.html',categories = categories)

@app.route('/blog/<int:id>/edit' , methods = ['GET' , 'POST'])
@login_required
def blog_edit(id):
    blog = Blog.query.get_or_404(id)

    if blog.author_id != current_user.id:
        return "你没有权限编辑这篇文章" , 403


    if request.method == 'POST':
        blog.title = request.form.get('title')
        blog.content = request.form.get('content')
        blog.category_id = request.form.get('category_id')

        db.session.commit()
        return redirect(url_for('blog_detail' , id = blog.id))
    categories = Category.query.all()
    return render_template('blog_edit.html' , categories = categories , blog = blog)

@app.route('/blog/delete/<int:id>' , methods = ['POST'])
@login_required
def blog_delete(id):
    blog = Blog.query.get_or_404(id)

    if blog.author_id != current_user.id:
        return "你没有权限删除这篇文章" , 403

    db.session.delete(blog)
    db.session.commit()
    return redirect(url_for('blog_list'))

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username = username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('blog_list'))
        else:
            return '用户名或者密码错误' , 400
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('blog_list'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html',user=current_user)

@app.route('/profile/edit',methods=['GET','POST'])
@login_required
def edit_profile():
    if request.method  == 'POST':
        current_user.email = request.form.get('email')
        current_user.bio  =  request.form.get('bio')

        db.session.commit()
        return redirect(url_for('profile'))
    return render_template('edit_profile.html' , user=current_user)

@app.route('/change-password',methods=['GET','POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm = request.form.get('confirm_password')
        if not current_user.check_password(old_password):
            return '原密码错误', 400
        if new_password != confirm:
            return '两次新密码不一致',400
        current_user.set_password(new_password)
        db.session.commit()
        return redirect(url_for('profile'))
    return render_template('change_password.html')

if __name__  ==  '__main__':
    app.run(debug=True)