from models.todo import Todo
from routes import redirect, template, response_with_headers, error, current_user, login_required
from utils import log
import time


def formatted_time(time_stamp):
    time_array = time.localtime(time_stamp)
    other_style_time = time.strftime("%Y-%m-%d %H:%M:%S", time_array)
    return other_style_time


def index(request):
    """
    todo 首页的路由函数
    """

    u = current_user(request)
    todo_list = Todo.find_all(user_id=u.id)
    # 下面这行生成一个 html 字符串
    todo_html = """
    <h3>
        {} : {}
        <a href="/todo/edit?id={}">编辑</a>
        <a href="/todo/delete?id={}">删除</a>
        <div> 创建时间：{}</div>
        <div> 最后更新时间：{}</div>
    </h3>
    """
    todo_html = ''.join([
        todo_html.format(
            t.id, t.title, t.id, t.id, formatted_time(t.created_time), formatted_time(t.updated_time)
        ) for t in todo_list
    ])

    # 替换模板文件中的标记字符串
    body = template('todo_index.html')
    body = body.replace('{{todos}}', todo_html)

    # 下面 3 行可以改写为一条函数, 还把 headers 也放进函数中
    headers = {
        'Content-Type': 'text/html',
    }
    header = response_with_headers(headers)
    r = header + '\r\n' + body
    return r.encode()


def add(request):
    """
    用于增加新 todo 的路由函数
    """
    u = current_user(request)
    form = request.form()
    t = Todo.new(form)
    t.user_id = u.id
    t.created_time = int(time.time())
    t.updated_time = t.created_time
    t.save()
    # 浏览器发送数据过来被处理后, 重定向到首页
    # 浏览器在请求新首页的时候, 就能看到新增的数据了
    return redirect('/todo')


def edit(request):
    """
    todo 首页的路由函数
    """

    u = current_user(request)
    todo_id = int(request.query.get('id'))
    t = Todo.find_by(id=todo_id)

    if u.id == t.user_id:

        # 替换模板文件中的标记字符串
        body = template('todo_edit.html')
        body = body.replace('{{todo_id}}', str(t.id))
        body = body.replace('{{todo_title}}', t.title)

        # 下面可以改写为一条函数, 还把 headers 也放进函数中
        headers = {
            'Content-Type': 'text/html',
        }
        header = response_with_headers(headers)
        r = header + '\r\n' + body
        return r.encode()
    else:
        error(request)


def update(request):
    """
    用于增加新 todo 的路由函数
    """
    form = request.form()
    todo_id = int(form.get('id', -1))
    log('更新时获取todo_id成功', todo_id)
    t = Todo.find_by(id=todo_id)
    log('找到该todo成功')
    t.title = form.get('title')
    t.updated_time = int(time.time())
    t.save()
    # 浏览器发送数据过来被处理后, 重定向到首页
    # 浏览器在请求新首页的时候, 就能看到新增的数据了
    return redirect('/todo')

def delete(request):
    """
    用于增加新 todo 的路由函数
    """
    todo_id = int(request.query.get('id'))
    Todo.remove(todo_id)
    return redirect('/todo')

def route_dict():
    """
    路由字典
    key 是路由(路由就是 path)
    value 是路由处理函数(就是响应)
    """
    d = {
        '/todo': login_required(index),
        '/todo/add': login_required(add),
        '/todo/edit': login_required(edit),
        '/todo/update': login_required(update),
        '/todo/delete': login_required(delete),
    }
    return d
