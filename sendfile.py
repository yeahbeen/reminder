import os
import re
import threading
import socket
import time
import inspect
import ctypes
from PyQt5.QtWidgets import QFileDialog,QHBoxLayout,QLabel,QLineEdit,QMessageBox,QProgressBar,QPushButton,QTextEdit,QVBoxLayout,QWidget
from PyQt5.QtCore import QTimer,Qt,pyqtSignal
from config import Config
import mytimer
from log import log

class SendFile(QWidget):

    updated = pyqtSignal(str)
    
    def __init__(self,par):
        super().__init__()
        self.updated.connect(self.updateText)
        self.par = par
        self.setWindowTitle("传送文件")
        
        iphbox = QHBoxLayout()
        iphbox.addWidget(QLabel("本机IP"))
        self.iplabel = QLabel()
        iphbox.addWidget(self.iplabel)
        ephbox = QHBoxLayout()
        ephbox.addWidget(QLabel("对端IP"))
        self.eplabel = QLabel()
        ephbox.addWidget(self.eplabel)
        
        # self.infolabel = QLabel()        
        self.infoEdit = QTextEdit()
        self.infoEdit.textChanged.connect(self.autoScroll)
        self.infoEdit.setReadOnly(True)
        
        self.pgbar = QProgressBar()
        self.pgbar.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        bar_hbox = QHBoxLayout()
        bar_hbox.addWidget(QLabel("进度:"))
        bar_hbox.addWidget(self.pgbar)
        self.speed = QLabel("0KB/s")
        self.speed.setMaximumWidth(100)
        bar_hbox.addWidget(self.speed)
        
        self.outpathEdit = QLineEdit()
        if "sendfile" not in Config.config.keys():
            Config.config["sendfile"] = {}
            Config.config["sendfile"]["outpath"] = Config.workdir + "\\ReceiveFiles"
        self.outpathEdit.setText(Config.config["sendfile"]["outpath"])
        if not os.path.exists(Config.config["sendfile"]["outpath"]):
            os.makedirs(Config.config["sendfile"]["outpath"])
        
        self.outpathbtn = QPushButton("选择")
        self.outpathbtn.setMaximumWidth(50)
        self.outpathbtn.clicked.connect(self.choosepath)
        outhbox = QHBoxLayout()
        outhbox.addWidget(QLabel("保存目录:"))
        outhbox.addWidget(self.outpathEdit)
        outhbox.addWidget(self.outpathbtn)
        
        hbox = QHBoxLayout()
        self.sendbtn = QPushButton("发送文件")
        self.sendbtn.clicked.connect(self.sendfile)
        self.startbtn = QPushButton("开始监听")
        self.startbtn.clicked.connect(self.start)
        self.stopbtn = QPushButton("停止监听")
        self.stopbtn.clicked.connect(self.stop)
        self.onlinebtn = QPushButton("刷新")
        self.onlinebtn.clicked.connect(self.init)
        self.openbtn = QPushButton("打开文件夹")
        self.openbtn.clicked.connect(self.opendir)
        hbox.addWidget(self.sendbtn)
        hbox.addWidget(self.startbtn)
        hbox.addWidget(self.stopbtn)
        hbox.addWidget(self.onlinebtn)
        hbox.addWidget(self.openbtn)
        vbox = QVBoxLayout()
        vbox.addLayout(iphbox)
        vbox.addLayout(ephbox)
        vbox.addWidget(self.infoEdit)
        vbox.addLayout(bar_hbox)
        vbox.addLayout(outhbox)
        vbox.addLayout(hbox)
        self.setLayout(vbox)

        rect = par.geometry()
        # log(rect)
        self.setGeometry(rect.x(), rect.y(), 300, 300)
        self.connectting = False
        self.ip = None
        self.endpoint = None
        self.port = 6066
        self.setAcceptDrops(True)
        
    def updateText(self,text):
        self.infoEdit.append(text)
        
    def choosepath(self):
        curpath = self.outpathEdit.text()
        dirname = QFileDialog.getExistingDirectory(self, "打开文件夹", curpath)
        log("dirname:"+str(dirname))
        if dirname != "":
            self.outpathEdit.setText(dirname)
            Config.config["sendfile"]["outpath"] = dirname

    def opendir(self):
        os.system("start explorer.exe "+self.outpathEdit.text())

    def autoScroll(self):
        # log("in autoScroll")
        self.infoEdit.verticalScrollBar().setValue(self.infoEdit.verticalScrollBar().maximum())

    #发送广播，告知对方自己的ip
    def init(self):
        if not self.ip:
            # QMessageBox(QMessageBox.Information,"错误","获取不到本机ip，请尝试重新监听")
            self.infoEdit.append(f"获取不到本机ip，请尝试重新监听")
            return
        #构造广播地址
        ip_arr = self.ip.split(".")
        ip_arr[3] = "255"
        dest=(".".join(ip_arr),self.port)
        log(f'broadcast addr:{dest}')
        st = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        st.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
        self.infoEdit.append(f"广播本机上线消息。")
        st.sendto("reminderonline".encode(),dest)
        st.close()
        
    #监听广播消息，获取对端ip地址
    def onlineThread(self):
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.settimeout(5)
        s.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
        s.bind(('0.0.0.0',self.port))
        while True:
            try:
                msg,addr=s.recvfrom(1024)
                log(f'receive broadcast message ({msg.decode()}) from {addr}')
                if addr[0] != self.ip:
                    self.endpoint = addr[0]
                    self.eplabel.setText(self.endpoint)
                    # self.infoEdit.append(f"获取到对端ip:"+self.endpoint)
                    self.updated.emit("获取到对端ip:"+self.endpoint)
                    if msg.decode() == "reminderonline": #如果是对方上线的消息，要回复一下
                        s.sendto("reminderroger".encode(),(addr[0],self.port))
            except Exception as e:
                # print(e)
                # print("online check stop..")
                if self.running == False:
                    break
                else:
                    continue
                
        s.close()
       
    def sendThread(self,file):
        if not self.endpoint:
            # self.infoEdit.append(f"获取不到对端ip，请尝试重新上线")
            self.updated.emit(f"获取不到对端ip，请尝试重新上线")
            return
        self.connectting = True
        s = socket.socket()         
        # host = "192.168.1.102"
        host = self.endpoint
        port = self.port                
        s.settimeout(10)
        # self.infoEdit.append(f"正在连接{host}:{port},请稍候..")
        self.updated.emit(f"正在连接{host}:{port},请稍候..")
        try:
            s.connect((host, port))
        except Exception as e:
            log(e)
            # self.infoEdit.append(f"连接失败，请确认对方是否在线")
            self.updated.emit(f"连接失败，请确认对方是否在线")
            self.connectting = False
            return
        self.connectting = False
        filename = os.path.basename(file)
        # time.sleep(3)
        # self.infoEdit.append(f"发送文件:{os.path.basename(file)}...")
        self.updated.emit(f"发送文件:{filename}...")
        msg = "sendfile|"+filename+"|"+str(os.path.getsize(file))
        log(msg)
        try:
            s.send(msg.encode())
            rss = s.recv(1024).decode()
            log(rss)
            if "receivefile" in rss:
                with open(file,"rb") as f:
                    # self.sendf = open(file,"rb")
                    # self.filesize = os.path.getsize(file)
                    self.alive_th[file][1] = f
                    rs = f.read(1024)
                    while len(rs)>0:
                        s.send(rs)
                        rs = f.read(1024)
                        # print(len(rs))
                # self.sendf.close()
                log("fileover")
                # self.infoEdit.append(f"发送完成")
                self.updated.emit(f"{filename}发送完成")
        except Exception as e:
            log(e)
            if not self.sendf:
                self.sendf.close()
            # self.infoEdit.append(f"发送失败:{str(e)}")
            self.updated.emit(f"发送失败:{str(e)}")
        s.close()

    def changeprogress(self):
        # print("in changeprogress")
        nowall = 0
        allsize = 0
        not_finish = False
        for file in self.alive_th:
            f = self.alive_th[file][1]
            size = self.alive_th[file][0]
            # print(size)
            allsize += size
            if f:
                if not f.closed:
                    not_finish = True
                    now = f.tell()
                    # print(now)
                    nowall += now
                else:
                    nowall += size
        if not_finish:
            self.pgbar.setValue(nowall/allsize*100)
            # print(f'{(nowall - self.nowsize)/1024}KB/s')
            if (nowall - self.nowsize)/1024/1024 > 1:
                self.speed.setText(f'{round((nowall - self.nowsize)/1024/1024,2)}MB/s')
            else:
                self.speed.setText(f'{round((nowall - self.nowsize)/1024,0)}KB/s')
            self.nowsize = nowall
        else:
            self.pgbar.setValue(100)
            self.sendtimer.stop()
            self.alive_th.clear()
            self.speed.setText("0KB/s")

    def sendfile(self):
        if self.connectting:
            log("正在连接，请稍后重试")
            return
        if not self.endpoint:
            # QMessageBox(QMessageBox.Information,"提醒","对方未在线，请稍后再试")
            log("对方未在线，请稍后再试")
            self.infoEdit.append("对方未在线，请稍后再试")
            return
        name = QFileDialog.getOpenFileNames(self,"打开文件")
        log(name)
        if name[0] == []:
            return
        self.infoEdit.append("准备开始传送...")
        for file in name[0]:
            time.sleep(0.5)
            self.sendonefile(file)
    
    def sendonefile(self,file):
        if len(self.alive_th)==0:
            self.nowsize = 0
            self.sendtimer.start(1000)
            self.pgbar.reset()            
        st = threading.Thread(target=self.sendThread,args=(file,))
        self.alive_th[file] = [os.path.getsize(file),None]
        st.start()        
        
    def recvThread(self,c):
        string = c.recv(1024).decode()
        log(string)
        if "sendfile" in string:
            filename = string.split("|")[1]
            filesize = int(string.split("|")[2])
            log(filename)
            log(filesize)
            # self.infoEdit.append(f"接收文件{filename}..")
            self.updated.emit(f"接收文件{filename}..")
            c.send("receivefile".encode())
            string = c.recv(1024)
            count = 0
            with open(self.outpathEdit.text()+"\\"+filename,"wb") as f:
                while True:
                    f.write(string)
                    count += len(string)
                    # print(count)
                    if count>=filesize:
                        break;                    
                    string = c.recv(1024)

            log(count)
            # self.infoEdit.append(f"接收完成")
            self.updated.emit(f"{filename}接收完成")
            log("fileover")
        c.close()
        
    def acceptThread(self):
        if not self.ip:
            #QMessageBox(QMessageBox.Information,"错误","获取不到本机ip")
            return
        s = socket.socket()        
        # host = "192.168.1.116"
        host = self.ip
        port = self.port                
        s.bind((host, port))       
        s.listen()                
        s.settimeout(5)
        # self.infoEdit.append(f"在{host}:{port}上监听接收文件..")
        self.updated.emit(f"在{host}:{port}上监听接收文件..")
        while True:
            try:
                c,addr = s.accept()    
            except socket.timeout as e:
                # print(e)
                # print("accept check stop..")
                if self.running == False:
                    # self.infoEdit.append(f"已停止监听..")
                    self.updated.emit(f"已停止监听..")
                    self.stopbtn.setDisabled(True)
                    self.startbtn.setDisabled(False)
                    break
                else:
                    continue
            log(c)
            log(addr)
            # _thread.start_new_thread(recvThread,(c,))
            threading.Thread(target=self.recvThread,args=(c,)).start()
            
    def start(self):
        log("start send file init..")
        self.startbtn.setDisabled(False)
        self.stopbtn.setDisabled(True)
        self.onlinebtn.setDisabled(True)
        #获取自身ip
        st = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:       
            st.connect(('10.255.255.255', 1))
            self.ip = st.getsockname()[0]
            log(f'local ip:{self.ip}')
            self.iplabel.setText(self.ip)
            self.infoEdit.append("获取到本机IP:"+self.ip)
        except Exception:
            self.infoEdit.append("获取不到本机ip，启动失败，请稍后尝试刷新。")
            return
        self.running = True
        #先监听对端上线消息
        self.oth = threading.Thread(target=self.onlineThread)
        self.oth.start()        
        #发送自己上线消息，对方会回复
        self.init()                
        #监听发文件消息
        self.th = threading.Thread(target=self.acceptThread)
        self.th.start()
        self.alive_th = {}
        self.sendtimer = QTimer()
        self.sendtimer.timeout.connect(self.changeprogress)
        self.startbtn.setDisabled(True)
        self.stopbtn.setDisabled(False)
        self.onlinebtn.setDisabled(False)
        

    def stop(self):
        self.running = False
        self.infoEdit.append("正在停止,请稍候..")
        # stop_thread(self.oth)
        # stop_thread(self.th)

    def closeEvent(self,e):
        Config.save()
        
    def dragEnterEvent(self,event):
        event.acceptProposedAction()
        
    def dropEvent(self,event):
        files = event.mimeData().urls()
        log(files)
        self.dragSendfile(files)


    def dragSendfile(self,files):
        for url in files:
            time.sleep(0.5)
            log(url)
            file = url.toString().replace("file:///","")
            log(file)
            self.sendonefile(str(file))
            # st = threading.Thread(target=self.sendThread,args=(str(file),))
            # st.start()
            



