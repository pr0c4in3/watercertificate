from flask import Flask, request, send_file, render_template
from web import web
from flask import Flask, render_template, request, redirect, url_for, flash, g, session #登录相关
from db_ctrl import login_db #调用登录库
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
def home():
    if 'username' in session:
        return render_template('embed.html', username=session['username'])
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
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
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
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

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))


'''
处理水印相关
'''


@app.route("/watermark_embed", methods=["GET", "POST"])  # 原来的增加水印
def index():
    return render_template('embed.html')

@app.route("/watermark_trace", methods=["GET", "POST"])  # 水印追踪
def watermark_trace():
    return render_template('trace.html')



# @app.route("/project_introduce", methods=["GET", "POST"])  # 项目介绍
# def project_introduce():
#     return render_template('introduce.html')

# @app.route("/project_member", methods=["GET", "POST"])  # 项目成员
# def project_member():                                             #这两部分暂时不需要
#     return render_template('member.html')





@app.route("/embed", methods=["GET", "POST"])  # 插入水印的操作，结果是返回图片或者返回错误信息
def embed():
    result = request.form
    file = request.files['file']
    water = web()
    if water.verify(file, result=result):
        return_data = water.embed(result)
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
