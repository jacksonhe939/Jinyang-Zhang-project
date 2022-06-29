import socket
import select
from config import settings


class SelectServer(object):
    def __init__(self):
        self.host = settings.HOST
        self.port = settings.PORT
        self.socket_object_list = []
        self.conn_handler_map = {}

    def run(self, handler):
        server_object = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_object.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # non-blocking（ blocking error )
        # server_object.setblocking(False)
        server_object.setblocking(True)

        server_object.bind((self.host, self.port))
        server_object.listen(5)
        self.socket_object_list.append(server_object)

        while True:
            r, w, e = select.select(self.socket_object_list, [], [], 0.05)
            for sock in r:
                # new connection coming，run handler __init__ method
                if sock == server_object:
                    print("new connection coming")
                    conn, addr = server_object.accept()
                    self.socket_object_list.append(conn)
                    self.conn_handler_map[conn] = handler(conn)
                    continue

                # new data coming，run handler __call__ method
                handler_object = self.conn_handler_map[sock]
                # run handler execute method，if return False，close connection
                result = handler_object.execute()
                if not result:
                    self.socket_object_list.remove(sock)
                    del self.conn_handler_map[sock]
        sock.close()
