import re
import os
import json
import socket
from config import settings
from utils import req


class Handler(object):
    def __init__(self):
        self.host = settings.HOST
        self.port = settings.PORT
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.username = None

    def run(self):
        self.conn.connect((self.host, self.port))
        welcome = """
        login：login username password
        register：register username password
        check：ls file
        upload：upload local file cloud file
        download：download local file cloud file 
        """
        print(welcome)

        method_map = {
            "login": self.login,
            "register": self.register,
            "ls": self.ls,
            "upload": self.upload,
            "download": self.download,
        }

        while True:
            hint = "({})>>> ".format(self.username or "not login")
            text = input(hint).strip()
            if not text:
                print("input can't be blank，please do it again。")
                continue

            if text.upper() == "Q":
                print("exit")
                req.send_data(self.conn, "q")
                break

            cmd, *args = re.split(r"\s+", text)
            method = method_map.get(cmd)
            if not method:
                print("order not exist，please enter again。")
                continue
            method(*args)

        self.conn.close()

    def login(self, *args):
        if len(args) != 2:
            print("wrong format，please do again。hint：login username password")
            return
        username, password = args
        req.send_data(self.conn, "login {} {}".format(username, password))
        reply = req.recv_data(self.conn).decode('utf-8')
        reply_dict = json.loads(reply)
        if reply_dict['status']:
            self.username = username
            print("successfully login")
            return
        print(reply_dict['error'])

    def register(self, *args):
        if len(args) != 2:
            print("wrong format，please do again。hint：register username password")
            return
        username, password = args

        req.send_data(self.conn, "register {} {}".format(username, password))
        reply = req.recv_data(self.conn).decode('utf-8')
        reply_dict = json.loads(reply)
        if reply_dict['status']:
            print("successfully registered")
            return
        print(reply_dict['error'])

    def ls(self, *args):
        if not self.username:
            print("login fist then check")
            return
        if not args:
            cmd = "ls"
        elif len(args) == 1:
            cmd = "ls {}".format(*args)
        else:
            print("wrong format，please do again。hint：ls or ls file ")
            return

        req.send_data(self.conn, cmd)
        reply = req.recv_data(self.conn).decode('utf-8')
        reply_dict = json.loads(reply)
        if reply_dict['status']:
            print(reply_dict['data'])
            return
        print(reply_dict['error'])

    def upload(self, *args):
        if not self.username:
            print("login then upload")
            return
        if len(args) != 2:
            print("wrong format，enter again。hint：upload local file cloud file")
            return
        local_file_path, remote_file_path = args
        if not os.path.exists(local_file_path):
            print("file{}not exist，please enter again。".format(local_file_path))
            return

        req.send_data(self.conn, "upload {}".format(remote_file_path))
        reply = req.recv_data(self.conn).decode('utf-8')
        reply_dict = json.loads(reply)
        if not reply_dict['status']:
            print(reply_dict['error'])
            return

        print("start upload")  # reply_dict['data']

        # start upload
        req.send_file(self.conn, local_file_path)

        print("upload finished")

    def download(self, *args):
        if not self.username:
            print("login then download")
            return
        if len(args) != 2:
            print("wrong format，please do again。hint：download local file cloud file")
            return

        local_file_path, remote_file_path = args
        seek = 0
        if not os.path.exists(local_file_path):
            # download v1.txt
            req.send_data(self.conn, "download {}".format(remote_file_path))
            mode = 'wb'
        else:
            choice = input("continue download（Y/N) ")
            if choice.upper() == 'Y':
                # download v1.txt 100
                seek = os.stat(local_file_path).st_size
                req.send_data(self.conn, "download {} {}".format(remote_file_path, seek))
                mode = 'ab'
            else:
                # download v1.txt
                req.send_data(self.conn, "download {}".format(remote_file_path))
                mode = 'wb'

        reply = req.recv_data(self.conn).decode('utf-8')
        reply_dict = json.loads(reply)
        if not reply_dict['status']:
            print(reply_dict['error'])
        else:
            print("start download")  # print(reply_dict['data'])
            req.recv_save_file_with_progress(self.conn, local_file_path, mode, seek=seek)
            print("download finished")


handler = Handler()
