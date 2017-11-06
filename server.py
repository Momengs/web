import socket
import urllib.parse
import _thread

from routes import route_dict
from routes import route_static
from utils import log
from routes import error
from routes_todo import route_dict as routes_todo


class Request(object):
    def __init__(self, raw_data):
        header, self.body = raw_data.split('\r\n\r\n', 1)
        h = header.split('\r\n')

        parts = h[0].split()
        self.method = parts[0]
        path = parts[1]
        self.path = ""
        self.query = {}
        self.parse_path(path)

        self.headers = {}
        self.cookies = {}
        self.add_headers(h[1:])
        self.add_cookies()

    def add_cookies(self):
        cookies = self.headers.get('Cookie', '')
        kvs = cookies.split('; ')
        log('cookie', kvs)
        for kv in kvs:
            if '=' in kv:
                k, v = kv.split('=')
                self.cookies[k] = v

    def add_headers(self, header):
        lines = header
        for line in lines:
            k, v = line.split(': ', 1)
            self.headers[k] = v

    def form(self):
        body = urllib.parse.unquote(self.body)
        print('form', self.body)
        args = body.split('&')
        f = {}
        for arg in args:
            k, v = arg.split('=')
            f[k] = v
        print('form()', f)
        return f

    def parse_path(self, path):
        index = path.find('?')
        if index == -1:
            self.path = path
            self.query = {}
        else:
            path, query_string = path.split('?', 1)
            args = query_string.split('&')
            query = {}
            for arg in args:
                k, v = arg.split('=')
                query[k] = v
            self.path = path
            self.query = query


def response_for_path(request):
    r = {
        '/static': route_static,
    }
    r.update(route_dict())
    r.update(routes_todo())
    response = r.get(request.path, error)
    return response(request)


def process_request(connection):
    try:
        r = connection.recv(1024)
        r = r.decode()
        log('request log:\n'.format(r))
        request = Request(r)
        response = response_for_path(request)
        log("response log:\n", response)
        connection.sendall(response)
        connection.close()
    except Exception as e:
        connection.close()
        raise e


def run(host='', port=3000):
    log('开始运行于', '{}:{}'.format(host, port))
    with socket.socket() as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen()
        # 无限循环来处理请求
        while True:
            connection, address = s.accept()
            # 第二个参数类型必须是 tuple
            log('ip {}'.format(address))
            _thread.start_new_thread(process_request, (connection,))


if __name__ == '__main__':
    # 生成配置并且运行程序
    config = dict(
        host='127.0.0.1',
        port=3000,
    )
    run(**config)
