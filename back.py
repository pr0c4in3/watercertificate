from flask import Flask, request, send_file, render_template,send_from_directory
from web import web
from flask import Flask, render_template, request, redirect, url_for, flash, g, session #登录相关
from db_ctrl import login_db,ca_db #调用登录库，证书管理库
import json #调用json库

'''
后端主程序，负责页面的调用和管理
'''

app = Flask(__name__)
app.secret_key = 'your_secret_key'
DATABASE = 'login.db'
'''
登录相关
'''
def get_db(): #获取数据库
    if 'db' not in g:
        g.db = login_db(DATABASE)
    return g.db
# @app.teardown_appcontext    #关闭数据库
# def close_db(error):
#     db = g.pop('db', None)
#     if db is not None:
#         db.close()
'''
登入登出操作
'''

@app.route('/')
def home(): #主页，session存在则跳转至添加水印（目前），不存在则跳转至登录
    if 'username' in session:
        return render_template('index.html', username=session['username'])
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])   #登录
def login():
    if 'username' in session:
        session.pop('username',None)
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print(request.form)
        db = get_db()
        if db.authenticate_user(username, password):
            print('login success')
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            print('login fail')
            flash('Login failed. Check your username and password.', 'danger')
            return render_template('loginerror.html')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])    #注册
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        #print(request.form)#debug
        db = get_db()
        if db.register_user(username, password):
            print('success')
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            print('exist')
            flash('Username already exists. Please choose another.', 'danger')
            return render_template('registerror.html')
    #return render_template('register.html')

@app.route('/logout')#登出，这里暂时保留
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))
'''
证书管理
'''
@app.route('/management')
def management():
    username1=session['username']
    return render_template('management.html',username=username1)


@app.route('/showlist')
def showlist():
    print('use showlist')
    wm=request.form['watermark']
    a=request.form
    print(a)
    username1=session['username']   #当前用户名
    certificate_db=ca_db()
    if wm==None:
        result=certificate_db.get_certificate_by_user(username1)
        # res = json.dumps(result)      #debug
        # print(result)
        # print(res)
        return result
    else:
        result=certificate_db.get_certificate_by_wm_and_user(username1,wm)
        return result


# img_path=''
# img_name=''
@app.route('/pic', methods=['GET', 'POST'])
def pic():
    #username1=session['username']
    result1 = request.form
    ca=ca_db()
    session['img_name']=result1['image_name']
    ca1=ca.get_certificate_by_img(session['img_name'])
    session['img_path']=ca1['image_path']
    return {}
    # print(img_path+img_name)
    # return  render_template('pic.html',image=img_path+img_name)

@app.route('/del_pic', methods=['GET', 'POST'])
def del_pic():
    fca=web()
    #username1=session['username']
    result = request.form
    print(result['image_name'])
    ca=ca_db()
    answer = ca.delete_certificate_by_image_name(result['image_name'])
    if  answer:
        return {'status': 'ok'}
    else:
        return {'status': 'error'}

@app.route('/pic1', methods=['GET', 'POST'])
def pic1():
    #image=session['img_path']+session['img_name']
    print(session['img_path']+session['img_name'])
    # return render_template('pic.html',image=session['img_path']+session['img_name'])
    return send_from_directory(session['img_path'],session['img_name'])





'''
处理水印相关
'''


@app.route("/watermark_embed", methods=["GET", "POST"])  # 原来的增加水印
def index():
    username1=session['username']
    return render_template('index.html',username=username1)

@app.route("/watermark_trace", methods=["GET", "POST"])  # 水印追踪
def watermark_trace():
    username1=session['username']
    return render_template('trace.html',username=username1)



# @app.route("/project_introduce", methods=["GET", "POST"])  # 项目介绍
# def project_introduce():
#     return render_template('introduce.html')

# @app.route("/project_member", methods=["GET", "POST"])  # 项目成员
# def project_member():                                             #这两部分暂时不需要
#     return render_template('member.html')





@app.route("/embed", methods=["GET", "POST"])  # 插入水印的操作，结果是返回图片或者返回错误信息
def embed():
    if 'username' in session:
        username=session['username']
        ca=ca_db()
    else:
        return render_template(login.html)
    result = request.form
    file = request.files['file']
    water = web()
    if water.verify(file, result=result):
        return_data = water.embed(result)
        ca.add_certificate(username, water.path_in, water.filename_in, result['wm_text'], result['password_img'])
        return send_file(return_data, as_attachment=True, mimetype=water.mimetype, download_name=water.filename_out)
    else:
        return render_template('index.html', statu="error")


@app.route("/extract", methods=["GET", "POST"])  # 提取水印的操作，结果是返回水印或返回错误信息
def extract():
    result = request.form
    file = request.files['file']
    water = web()
    if water.verify(file, result=result):
        return_data=water.extract(result)
        return render_template('index.html',watermark=return_data)
    else:
        return render_template('index.html',statu="error")
    

    #之前的任务，这里暂时不管
    #改这里的页面文件
    #利用前端渲染这里的watermark和statu
    #error就用我上次给你的那个
    #watermark渲染直接利用{{watermark}}在前端显示出来
    #注意，前端的水印长度的名称继续用‘wm_text',后端解包时用的是和嵌入时的同一函数，如果不合适的话俩一起改！！！
if __name__ == "__main__":
    app.run(host="localhost", port=8080)
# def get_sum():
