import time

from utils import log
from models.message import Message
from models.user import User
from models.session import Session

import random


def random_string():
    """
    生成一个随机的字符串
    """
    seed = 'bdjsdlkgjsklgelgjelgjsegker234252542342525g'
    s = ''
    for i in range(16):
        random_index = random.randint(0, len(seed) - 2)
        s += seed[random_index]
    return s


def template(name):
    """
    根据名字读取 templates 文件夹里的一个文件并返回
    """
    path = 'templates/' + name
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def current_user(request):
    session_id = request.cookies.get('session_id')
    if session_id is not None:
        s = Session.find_by(session_id=session_id)
        now = time.time()
        if s.expired_time > now:
            u = User.find_by(id=s.user_id)
            log('current user 1', u)
            return u
        else:
            return User.guest()
    else:
        return User.guest()


def route_index(request):
    """
    主页的处理函数, 返回主页的响应
    """
    header = 'HTTP/1.x 210 VERY OK\r\nContent-Type: text/html\r\n'
    body = template('index.html')
    u = current_user(request)
    body = body.replace('{{username}}', u.username)
    r = header + '\r\n' + body
    return r.encode()


def response_with_headers(headers, code=200):
    """
    Content-Type: text/html
    Set-Cookie: user=gua
    """
    header = 'HTTP/1.x {} GUA\r\n'.format(code)
    header += ''.join([
        '{}: {}\r\n'.format(k, v) for k, v in headers.items()
    ])
    return header


def route_login(request):
    """
    登录页面的路由函数
    """
    headers = {
        'Content-Type': 'text/html',
    }
    log('login, headers', request.headers)
    log('login, cookies', request.cookies)

    if request.method == 'POST':
        form = request.form()
        username = form.get('username')
        password = form.get('password')
        if User.validate_login(username, password):
            u = User.find_by(username=username)
            # session 会话
            # token 令牌
            # 设置一个随机字符串来当令牌使用
            session_id = random_string()
            form = dict(
                session_id=session_id,
                user_id=u.id,
            )
            s = Session.new(form)
            s.save()
            headers['Set-Cookie'] = 'session_id={}'.format(
                session_id
            )
            result = '登录成功'
        else:
            result = '用户名或者密码错误'
            u = User.guest()
    else:
        result = ''
        u = User.guest()

    body = template('login.html')
    body = body.replace('{{result}}', result)
    body = body.replace('{{username}}', u.username)
    # 1. response header
    # 2. headers
    # 3. body
    header = response_with_headers(headers)
    r = header + '\r\n' + body
    log('login 的响应', r)
    return r.encode()


def route_register(request):
    """
    注册页面的路由函数
    """
    header = 'HTTP/1.x 210 VERY OK\r\nContent-Type: text/html\r\n'
    if request.method == 'POST':
        form = request.form()
        u = User.new(form)
        if u.validate_register():
            u.save()
            result = '注册成功<br> <pre>{}</pre>'.format(User.all())
        else:
            result = '用户名或者密码长度必须大于2'
    else:
        result = ''
    body = template('register.html')
    body = body.replace('{{result}}', result)
    r = header + '\r\n' + body
    return r.encode()


def route_message(request):
    """
    主页的处理函数, 返回主页的响应
    GET /messages?message=123&author=gua HTTP/1.1
    Host: localhost:3000
    """
    log('本次请求的 method', request.method)
    u = current_user(request)
    log('本次请求的 username', u.username)
    if u.id == -1:
        return error(request)
    else:
        form = request.query
        if len(form) > 0:
            m = Message.new(form)
            log('get', form)
            m.save()

        header = 'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n'
        body = template('messages.html')
        ms = '<br>'.join([str(m) for m in Message.all()])
        body = body.replace('{{messages}}', ms)
        r = header + '\r\n' + body
        return r.encode()


def route_message_add(request):
    """
    主页的处理函数, 返回主页的响应
    POST /messages HTTP/1.1
    Host: localhost:3000
    Content-Type: application/x-www-form-urlencoded

    message=123&author=gua
    """
    log('本次请求的 method', request.method)
    form = request.form()
    m = Message.new(form)
    log('post', form)
    # 应该在这里保存 message_list
    m.save()

    return redirect('/messages')


def route_static(request):
    """
    静态资源的处理函数, 读取图片并生成响应返回
    """
    filename = request.query.get('file', 'doge.gif')
    path = 'static/' + filename
    with open(path, 'rb') as f:
        header = b'HTTP/1.x 200 OK\r\nContent-Type: image/gif\r\n\r\n'
        img = header + f.read()
        return img


def route_admin_user(request):
    u = current_user(request)
    if u.role == 1:
        user_list = User.all()
        # 下面这行生成一个 html 字符串
        user_html = """
            <h3>
                <div>ID : {}</div>
                <div>Role : {}</div>
                <div>Username:{}</div>
                <div>Password:{}</div>
            </h3>
            <br>
            """
        todo_html = ''.join([
                                user_html.format(
                                    u.id, u.role, u.username, u.password
                                ) for u in user_list
                                ])

        # 替换模板文件中的标记字符串
        body = template('users.html')
        body = body.replace('{{users}}', todo_html)

        # 下面 3 行可以改写为一条函数, 还把 headers 也放进函数中
        headers = {
            'Content-Type': 'text/html',
        }
        header = response_with_headers(headers)
        r = header + '\r\n' + body
        return r.encode()
    else:
        return redirect('/login')


def route_admin_update(request):
    """
    用于修改用户密码的路由函数
    """
    if request.method == 'POST':
        form = request.form()
        log('form成功')
        user_id = int(form.get('id', -1))
        log('从表中获取user_id成功', user_id)
        u = User.find_by(id=user_id)
        u.password = form.get('password')
        log('更新密码成功', u.password)
        u.save()
        return redirect('/admin/users')
    else:
        error(request)


def route_dict():
    """
    路由字典
    key 是路由(路由就是 path)
    value 是路由处理函数(就是响应)
    """
    d = {
        '/': route_index,
        '/login': route_login,
        '/register': route_register,
        '/messages': route_message,
        '/messages/add': route_message_add,
        '/admin/users': route_admin_user,
        '/admin/users/update': admin_required(route_admin_update),
    }
    return d


def error(request, code=404):
    """
    根据 code 返回不同的错误响应
    目前只有 404
    """
    e = {
        404: b'HTTP/1.x 404 NOT FOUND\r\n\r\n<h1>NOT FOUND</h1>',
    }
    return e.get(code, b'')


def redirect(url):
    """
    浏览器在收到 302 响应的时候
    会自动在 HTTP header 里面找 Location 字段并获取一个 url
    然后自动请求新的 url
    """
    headers = {
        'Location': url,
    }
    # 增加 Location 字段并生成 HTTP 响应返回
    # 注意, 没有 HTTP body 部分
    r = response_with_headers(headers, 302) + '\r\n'
    return r.encode()


def login_required(route_function):
    def f(request):
        u = current_user(request)
        if u.id == -1:
            log('非登录用户 redirect')
            return redirect('/login')
        else:
            return route_function(request)
    return f


def current_user_required(route_function):
    def f(request):
        u = current_user(request)
        # if u.id == todo.user.id:
        #     pass
        # else:
        #     pass
    return f


def admin_required(route_function):
    """
    只有 role 为 1(管理员) 的用户可以访问这个页面, 其他用户访问会定向到 /login
    """
    def f(request):
        u = current_user(request)
        if u.role != 1:
            log('非管理员 redirect')
            return redirect('/login')
        else:
            return route_function(request)
    return f
