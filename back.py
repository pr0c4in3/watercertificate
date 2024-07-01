from flask import Flask, request, send_file, render_template
from web import web

'''
后端主程序，负责页面的调用和管理
'''



app = Flask(__name__)



@app.route("/", methods=["GET", "POST"])  # 主页
def index():
    return render_template('index.html')


@app.route("/project_introduce", methods=["GET", "POST"])  # 项目介绍
def project_introduce():
    return render_template('introduce.html')


@app.route("/project_member", methods=["GET", "POST"])  # 项目成员
def project_member():
    return render_template('member.html')


@app.route("/watermark_trace", methods=["GET", "POST"])  # 水印追踪
def watermark_trace():
    return render_template('trace.html')


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
