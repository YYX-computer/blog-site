from flask import *
import shutil
import atexit
import random
import json
import os
@atexit.register
def atexit():
    with open('usr.json','w') as f:
        json.dump(userlist,f)
app = Flask(__name__)
userlist = json.load(open('usr.json'))
succeeded = {}
def cos(vector1,vector2):
    dot_product = 0.0
    normA = 0.0
    normB = 0.0
    for a,b in zip(vector1,vector2):
        dot_product += a*b
        normA += a**2
        normB += b**2
    if normA == 0.0 or normB==0.0:
        return None
    else:
        return dot_product / ((normA*normB)**0.5)
def cosSimular(s1,s2):
    arr1 = []
    arr2 = []
    for i in s1:
            arr1.append(ord(i))
    for i in s2:
            arr2.append(ord(i))
    if((not any(arr1)) or (not any(arr2))):
            arr1 = [i + 1 for i in arr1]
            arr2 = [i + 1 for i in arr2]
    return cos(arr1,arr2)
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/login')
def login():
    return render_template('login.html')
@app.route('/register')
def register():
    return render_template('register.html')
@app.route('/api/login/<usr>/<pwd>')
def login_api(usr,pwd):
    ip = request.remote_addr
    if(usr in userlist and userlist[usr] == pwd):
        succeeded[ip] = usr
    else:
        return '',401
    return '',200
@app.route('/api/delete/<usr>/<pwd>')
def delete_api(usr,pwd):
    ip = request.remote_addr
    if(usr in userlist and userlist[usr] == pwd):
        userlist.pop(usr)
        succeeded.pop(request.remote_addr)
        shutil.rmtree('templates/blog/' +usr)
    else:
        return '',410
    return '',200
@app.route('/api/register/<usr>/<pwd>')
def register_api(usr,pwd):
    ip = request.remote_addr
    if(usr in userlist):
        return '',409
    else:
        userlist[usr] = pwd
        os.mkdir('templates/blog/' + usr)
        f = open('templates/blog/' + usr + '/data.json','w')
        f.write('{}')
        f.close()
    return '',200
@app.route('/index')
def home():
    ip = request.remote_addr
    if(ip in succeeded):
        return render_template('home.html',usr=succeeded[ip])
    else:
        return render_template('home.html',usr='')
@app.route('/search')
def search():
    kw = request.args.get('key')
    if(kw == None):
        return '',400
    else:
        return render_template('search.html',kw=kw)
@app.route('/api/search/<kw>')
def search_api(kw):
    blogList = {}
    for i in userlist:
        data = open('templates/blog/' + i + '/data.json','r').read()
        data = json.loads(data)
        for j in data:
            if(kw in j):
                blogList[(j,f'/blog/{i}/{j}')] = data[j] * cosSimular(kw,j)
    sortedBlogs = sorted(blogList.keys(),key = lambda x:blogList[x],reverse = True)
    rint = random.randint(0,len(sortedBlogs) - 1)
    return str([list(i) for i in sortedBlogs[rint:rint + 1]])
@app.route('/api/home')
def home_api():
    blogList = {}
    for i in userlist:
        data = open('templates/blog/' + i + '/data.json','r').read()
        data = json.loads(data)
        for j in data:
            blogList[(j,f'/blog/{i}/{j}')] = data[j]
    sortedBlogs = sorted(blogList.keys(),key = lambda x:blogList[x],reverse = True)
    return str([list(i) for i in sortedBlogs[:20]])
@app.route('/blog/<usr>/<ts>')
def blog(usr,ts):
    if(not os.path.exists('templates/blog/{0}/{1}.html'.format(usr,ts))):
        return '',404
    data = json.load(open('templates/blog/{0}/data.json'.format(usr)))
    data[ts] += 1
    f = open('templates/blog/{0}/data.json'.format(usr),'w')
    json.dump(data,f)
    f.close()
    return render_template('blog/{0}/{1}.html'.format(usr,ts))
@app.route('/me')
def me():
    ip = request.remote_addr
    if(ip in succeeded):
        return render_template('me.html',usr=succeeded[ip])
    else:
        return '''<script>window.location.href='/login'</script>'''
@app.route('/api/blog')
def blog_api():
    ip = request.remote_addr
    if(ip in succeeded):
        usr = succeeded[ip]
        blogList = []
        for i in os.listdir(f'templates/blog/{usr}'):
            if(not (i.startswith('.') or i == 'data.json')):
                blogList.append(os.path.splitext(i)[0])
        return json.dumps({'blog':blogList})
    else:
        return '',401
@app.route('/api/logout')
def logout_api():
    ip = request.remote_addr
    if(ip in succeeded):
        succeeded.pop(ip)
        return '',200
    else:
        return '',401
@app.route('/write')
def write():
    ip = request.remote_addr
    if(ip in succeeded):
        return render_template('writeBlog.html')
    else:
        return '''<script>window.location.href='/login'</script>'''
@app.route('/edit/<name>')
def edit(name):
    ip = request.remote_addr
    if(ip in succeeded):
        return render_template('editBlog.html',name=name)
    else:
        return '''<script>window.location.href='/login'</script>'''
@app.route('/api/write/<name>',methods=["POST"])
def write_api(name):
    ip = request.remote_addr
    if(ip not in succeeded):
        return '',401
    usr = succeeded[ip]
    text = open(f'templates/blog/{usr}/data.json').read()
    text = json.loads(text)
    text[name] = 0
    f = open(f'templates/blog/{usr}/data.json','w')
    json.dump(text,f)
    f.close()
    method = request.args.get('method')
    content = request.json.get('content')
    if(method == 'write' and os.path.exists(f'templates/blog/{usr}/{name}.html')):
        return '',409
    elif(method == 'edit' and (not os.path.exists(f'templates/blog/{usr}/{name}.html'))):
        return '',410
    try:
        f = open(f'templates/blog/{usr}/{name}.html','w')
    except:
        return '',410
    if(not isinstance(content,str)):
        return '',400
    f.write(content)
    f.close()
    return ''
@app.route('/api/write/delete/<name>')
def deleteBlog_api(name):
    ip = request.remote_addr
    if(ip not in succeeded):
        return '',401
    usr = succeeded[ip]
    text = open(f'templates/blog/{usr}/data.json').read()
    text = json.loads(text)
    text.pop(name)
    f = open(f'templates/blog/{usr}/data.json','w')
    json.dump(text,f)
    f.close()
    try:
        os.remove(f'templates/blog/{usr}/{name}.html')
        return '',200
    except:
        return '',410
@app.route('/delPg/<name>')
def delPage(name):
    return render_template('del.html',name=name)
@app.route('/sha256.js')
def sha256JsFile():
    return render_template('sha256.js')
if(__name__ == '__main__'):
    app.run()

