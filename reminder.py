import sys
import os
import time
import random
import json
import win32gui
import socket
import threading
# import PyHook3 as pyHook
import pyWinhook as pyHook
# from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QWidget,QGroupBox,QHBoxLayout,QVBoxLayout,QLineEdit,QLabel,QPushButton,QRadioButton,QCheckBox,QApplication,QAction,QMenu,QSystemTrayIcon,QShortcut,QSlider,QFileDialog,QMessageBox
from PyQt5.QtGui import QIcon,QKeySequence,QPixmap,QGuiApplication,QPainter,QColor,QTextCharFormat,QBrush,QTextCursor,QFont
# from PyQt5.QtCore import *
from PyQt5.QtCore import QTimer,QTime,QCoreApplication,QSettings,QUrl,pyqtSignal,Qt
from PyQt5.QtMultimedia import QMediaPlayer,QMediaContent,QMediaPlaylist
import schedule
import sendfile
from config import Config
import mytimer
from log import log

#一些常量
IDLE_TIME = 600 #无动作多长时间算空闲，单位秒
COUNTDOWN_TIME = 300 #界面上倒计时更新时间,单位毫秒
TOOLTIPS_TIME = 60000 #托盘倒计时更新时间，单位毫秒
FULLSCREEN_CHECK_TIME = 90000 #全屏检查时间，单位毫秒
IDLE_CHECK_TIME = 60000 #空闲状态检查时间，单位毫秒


log(sys.argv)
workdir = os.path.dirname(os.path.abspath(sys.argv[0]))
log("workdir:"+workdir)

Config.init()
config = Config.config

class RemainderMain(QWidget):
    
    restnow = pyqtSignal()

    def __init__(self):
        super().__init__()
        log("begin main")
        #初始化界面
        self.initUI()
        #全屏显示时间
        log("prepare show time")
        self.showtime = ShowTime()
        if Config.config["set"]["fsshowtime"]:
            self.fstimeAction.setText("关闭全屏显示时间")
            self.showtime.start()
        #不最小化则显示窗口
        if not Config.config["set"]["minimize"]:
            self.show()
            
        # self.start()
        
        log("startting....")
        #先初始化各种变量
        self.resting = False
        self.store_flag = None
        self.idle_store_flag = None
        self.rest_count = 0        
        self.passed_time = 0
        ##休息窗口
        self.transwin = TransWin()
        self.rollwin = RollPic(self)
        ##休息间隔计时器
        self.shorttimer = mytimer.mytimer("pop")
        # self.longtimer = mytimer.mytimer("roll")
        self.shorttimer.timeout.connect(self.ontimer)
        ##更新倒计时
        self.update_countdown_timer = QTimer()
        self.update_countdown_timer.timeout.connect(self.update_countdown)
        self.tips_timer = QTimer()
        self.tips_timer.timeout.connect(self.update_tooltips)
        ##退出全屏时休息，每30秒检查一次
        self.checkfulltimer = QTimer()
        self.checkfulltimer.timeout.connect(self.real_check_fullscreen)
        #监听鼠标键盘，判断空闲状态
        self.hm = pyHook.HookManager()
        self.hm.KeyDown = self.onKeyboardEvent
        self.hm.MouseAll = self.onMouseEvent
        self.hm.HookMouse()
        self.hm.HookKeyboard()
        self.lastActiveTime = time.time()
        #退出空闲状态时休息，每60秒检查一次
        self.check_idle_timer = QTimer()
        self.check_idle_timer.timeout.connect(self.check_idle)
        #检查配置是否正确
        if not self.check_config():
            self.show()
            return    
        self.startbtn.setText("暂停")
        self.save_config()
        self.get_shorttimeout()
        self.start_timers(self.shorttimeout)
        
        #设置对话框
        self.setting = Set(self)            
        #定时程序
        self.schedule = schedule.Schedule(self)
        self.schedule.start()
        #发送文件
        self.sendfile = sendfile.SendFile(self)
        self.sendfile.start()
        self.setAcceptDrops(True)
        #接受休息请求
        self.th = threading.Thread(target=self.acceptThread)
        self.th.start()
        
    def initUI(self):
        self.shortRest = QGroupBox("短暂休息")
        self.shortRest.setCheckable(True)
        # short_cd_hbox =  QHBoxLayout()
        self.shortHour = QLineEdit("1")
        self.shortMin = QLineEdit("0")
        self.shortSec = QLineEdit("0")
        self.shortHour.setPlaceholderText("0")
        self.shortMin.setPlaceholderText("0")
        self.shortSec.setPlaceholderText("0")
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel("休息间隔:"))
        hbox.addWidget(self.shortHour)
        hbox.addWidget(QLabel("小时"))
        hbox.addWidget(self.shortMin)
        hbox.addWidget(QLabel("分"))
        hbox.addWidget(self.shortSec)
        hbox.addWidget(QLabel("秒"))
        self.shortHour2 = QLineEdit("0")
        self.shortMin2 = QLineEdit("0")
        self.shortSec2 = QLineEdit("30")
        self.shortHour2.setPlaceholderText("0")
        self.shortMin2.setPlaceholderText("0")
        self.shortSec2.setPlaceholderText("0")
        hbox2 = QHBoxLayout()
        hbox2.addWidget(QLabel("休息时长:"))
        hbox2.addWidget(self.shortHour2)
        hbox2.addWidget(QLabel("小时"))
        hbox2.addWidget(self.shortMin2)
        hbox2.addWidget(QLabel("分"))
        hbox2.addWidget(self.shortSec2)
        hbox2.addWidget(QLabel("秒"))
        self.shortSet = QPushButton('休息设置')
        self.shortSet.clicked.connect(self.showRestSetShort)
        vbox = QVBoxLayout()
        # vbox.addLayout(short_cd_hbox)
        vbox.addLayout(hbox)
        vbox.addLayout(hbox2)
        vbox.addWidget(self.shortSet)
        self.shortRest.setLayout(vbox) 
        #长休息界面
        self.longRest = QGroupBox("长休息")
        self.longRest.setCheckable(True)
        self.longHour2 = QLineEdit("0")
        self.longMin2 = QLineEdit("5")
        self.longSec2 = QLineEdit("0")
        self.longHour2.setPlaceholderText("0")
        self.longMin2.setPlaceholderText("0")
        self.longSec2.setPlaceholderText("0")
        hbox4 = QHBoxLayout()
        hbox4.addWidget(QLabel("休息时长:"))
        hbox4.addWidget(self.longHour2)
        hbox4.addWidget(QLabel("小时"))
        hbox4.addWidget(self.longMin2)
        hbox4.addWidget(QLabel("分"))
        hbox4.addWidget(self.longSec2)
        hbox4.addWidget(QLabel("秒"))
        
        hbox3 = QHBoxLayout()
        hbox3.addWidget(QLabel("休息间隔:"))
        self.longitv = QLineEdit("3")
        hbox3.addWidget(self.longitv)
        hbox3.addWidget(QLabel("次短休息后长休息"))
        longSet = QPushButton('休息设置')
        longSet.clicked.connect(self.showRestSetLong)
        vbox2 = QVBoxLayout()
        # vbox2.addLayout(long_cd_hbox)
        vbox2.addLayout(hbox3)
        vbox2.addLayout(hbox4)
        vbox2.addWidget(longSet)
        self.longRest.setLayout(vbox2)   
        #启动，停止，倒计时界面
        countdown_hbox = QHBoxLayout()
        countdown_hbox.addWidget(QLabel("休息倒计时："))
        short_cd_label = QLabel("短暂休息:")
        self.short_cd_label2 = QLabel("00:00:00")
        long_cd_label = QLabel("长休息:")
        self.long_cd_label2 = QLabel("00:00:00")
        countdown_hbox.addWidget(short_cd_label)
        countdown_hbox.addWidget(self.short_cd_label2)
        countdown_hbox.addWidget(long_cd_label)
        countdown_hbox.addWidget(self.long_cd_label2)

        self.startbtn = QPushButton("继续")
        # self.startbtn.setDisabled(True)
        self.startbtn.clicked.connect(self.start_pause)
        self.stopbtn = QPushButton("重新开始")
        self.stopbtn.clicked.connect(self.start)
        # self.stopbtn.setDisabled(True)
        self.setbtn = QPushButton("设置...")
        self.setbtn.clicked.connect(self.showSet)
        start_hbox = QHBoxLayout()
        start_hbox.addWidget(self.startbtn)
        start_hbox.addWidget(self.stopbtn)
        start_hbox.addWidget(self.setbtn)
        
        self.schedulebtn = QPushButton("定时程序")
        self.schedulebtn.clicked.connect(self.showSchedule)        
        self.sendbtn = QPushButton("传送文件")
        self.sendbtn.clicked.connect(self.showSend)        
        tool_hbox = QHBoxLayout()
        tool_hbox.addWidget(self.schedulebtn)
        tool_hbox.addWidget(self.sendbtn)

        #整体布局
        layout = QVBoxLayout()
        layout.addWidget(self.shortRest)
        layout.addWidget(self.longRest)
        layout.addLayout(countdown_hbox)
        layout.addLayout(start_hbox)
        layout.addLayout(tool_hbox)
        self.setLayout(layout)
        log("init config")
        #初始化
        if config != {}:   
            self.shortRest.setChecked(config["short"]["enable"])
            self.shortHour.setText(config["short"]["itvHour"]) 
            self.shortMin.setText(config["short"]["itvMin"]) 
            self.shortSec.setText(config["short"]["itvSec"]) 
            self.shortHour2.setText(config["short"]["conHour"]) 
            self.shortMin2.setText(config["short"]["conMin"]) 
            self.shortSec2.setText(config["short"]["conSec"]) 

            self.longRest.setChecked(config["long"]["enable"])
            # self.longHour.setText(config["long"]["itvHour"]) 
            # self.longMin.setText(config["long"]["itvMin"]) 
            # self.longSec.setText(config["long"]["itvSec"]) 
            if "itvCount" in config["long"].keys():
                self.longitv.setText(config["long"]["itvCount"]) 
            self.longHour2.setText(config["long"]["conHour"]) 
            self.longMin2.setText(config["long"]["conMin"]) 
            self.longSec2.setText(config["long"]["conSec"]) 
        #托盘
        self.quitAction = QAction("退出")
        # self.quitAction.triggered.connect(QCoreApplication.quit)
        self.quitAction.triggered.connect(self.quitapp)
        self.shortrestnowAction = QAction("立即短休息")
        self.shortrestnowAction.triggered.connect(self.shortrestnow)
        self.restnow.connect(self.shortrestnow) #其他程序调起
        self.longrestnowAction = QAction("立即长休息")
        self.longrestnowAction.triggered.connect(self.longrestnow)
        self.fstimeAction = QAction("开启全屏显示时间")
        self.fstimeAction.triggered.connect(self.openfstime)
        self.sendfileAction = QAction("发送文件")
        self.sendfileAction.triggered.connect(self.menuSendfile)
        self.scheduleAction = QAction("定时程序")
        self.scheduleAction.triggered.connect(self.showSchedule)
        self.trayIconMenu = QMenu()
        self.trayIconMenu.addAction(self.shortrestnowAction)
        self.trayIconMenu.addAction(self.longrestnowAction)
        self.trayIconMenu.addAction(self.fstimeAction)
        self.trayIconMenu.addAction(self.sendfileAction)
        self.trayIconMenu.addAction(self.scheduleAction)
        self.trayIconMenu.addAction(self.quitAction)
        self.trayIcon = QSystemTrayIcon()
        self.trayIcon.setContextMenu(self.trayIconMenu)
        self.trayIcon.setIcon(QIcon(workdir+"\\cherry.ico"))
        self.trayIcon.activated.connect(self.showWin)
        self.trayIcon.show()
        #程序图标
        self.setWindowIcon(QIcon(workdir+"\\cherry.ico"))
        screen = QGuiApplication.primaryScreen()
        rect = screen.geometry()
        self.setGeometry(rect.center().x()-150,rect.center().y()-150, 300, 300)
        self.setWindowTitle('护眼助手')  
        
    def onMouseEvent(self,event):
        # 监听鼠标事件
        self.lastActiveTime = time.time()
        # print('Time:',event.Time)
        # print ("MessageName:", event.MessageName)
        # print ("WindowName:", event.WindowName)
        # print ("Position:", event.Position)
        return True

    def onKeyboardEvent(self,event):
        self.lastActiveTime = time.time()
        # print('Time:',event.Time)
        # print ("MessageName:", event.MessageName)
        # print ("WindowName:", event.WindowName)
        # print ("Ascii:", event.Ascii, chr(event.Ascii))
        # print ("Key:", event.Key)
        # print ("ScanCode:", event.ScanCode)
        # print ("Alt", event.Alt)
        return True

    def check_idle(self):
        # log(f'time.time()-self.lastActiveTime:{time.time()-self.lastActiveTime}')
        if time.time()-self.lastActiveTime > IDLE_TIME:
            return True
        else:
            if self.idle_store_flag is not None:
                log("check not idle and has store,rest")
                self.ontimer(self.idle_store_flag)
                
    def showWin(self,action):
        log("action:"+str(action))
        if action == QSystemTrayIcon.Trigger or action == QSystemTrayIcon.DoubleClick:
            self.showNormal()
            self.activateWindow()
            
    def shortrestnow(self):
        self.ontimer("shortnow")
        
    def longrestnow(self):
        self.ontimer("longnow")
        
    def openfstime(self):
        if Config.config["set"]["fsshowtime"]:
            self.fstimeAction.setText("开启全屏显示时间")
            Config.config["set"]["fsshowtime"] = False
            self.setting.fsshowtime.setChecked(False)
            # self.showtime.stop()
        else:
            self.fstimeAction.setText("关闭全屏显示时间")
            Config.config["set"]["fsshowtime"] = True
            self.setting.fsshowtime.setChecked(True)
            # self.showtime.start()
            
    def menuSendfile(self):
        self.sendfile.sendfile()

    #启动
    def start(self):
        pass

    def start_pause(self):
        if self.startbtn.text() == "继续":
            if not self.check_config(): return
            self.startbtn.setText("暂停")
            self.save_config()            
            self.get_shorttimeout()
            if self.shorttimeout>self.passed_time:
                time_out = self.shorttimeout-self.passed_time
            else:
                stime_out =  self.shorttimeout
            self.start_timers(time_out)
        elif self.startbtn.text() == "暂停":
            self.startbtn.setText("继续")
            self.remain_time = self.shorttimer.remainingTime()
            self.passed_time = self.shorttimeout - self.shorttimer.remainingTime()
            log(self.remain_time)
            log(self.passed_time)
            self.shortRest.setDisabled(False)
            self.longRest.setDisabled(False)
            # self.startbtn.setDisabled(False)
            # self.stopbtn.setDisabled(True)
            self.stop_timers()
            
    #检查配置是否正确
    def check_config(self):
        shortflag = longflag = False #文件不存在弹框
        #短暂休息
        if self.shortRest.isChecked(): 
            msg = "短暂休息:\n"
            if not os.path.exists(config["short"]["restset"]["uipic"]):
                shortflag = True
                msg+= "图片目录不存在！\n"
            if not os.path.exists(config["short"]["restset"]["beforesoundpath"]):
                shortflag = True
                msg+= "休息前声音文件不存在！\n"
            if not os.path.exists(config["short"]["restset"]["insoundpath"]):
                shortflag = True
                msg+= "休息中声音文件不存在！\n"
            msg+= "请在“休息设置”中重新设置。"
            if shortflag:
                QMessageBox.warning(None,"警告",msg)
        #长休息
        if self.longRest.isChecked():
            msg = "长休息:\n"
            if not os.path.exists(config["long"]["restset"]["uipic"]):
                longflag = True
                msg+= "图片目录不存在！\n"
            if not os.path.exists(config["long"]["restset"]["beforesoundpath"]):
                longflag = True
                msg+= "休息前声音文件不存在！\n"
            if not os.path.exists(config["long"]["restset"]["insoundpath"]):
                longflag = True
                msg+= "休息中声音文件不存在！\n"
            msg+= "请在“休息设置”中重新设置。"
            if longflag:
                QMessageBox.warning(None,"警告",msg)
        if shortflag or longflag:
            return False
        if not self.longRest.isChecked() and not self.shortRest.isChecked():
            QMessageBox.warning(None,"警告","短休息和长休息至少要选择一个")
            return False
        return True
        
    #获取休息间隔
    def get_shorttimeout(self):
        if config["short"]["restset"]["ui"] == "pop":   
            self.shorttimer.set_args("pop")
        else:
            self.shorttimer.set_args("roll")
        short_hour = self.shortHour.text() if self.shortHour.text() != "" else "0" 
        short_min = self.shortMin.text() if self.shortMin.text() != "" else "0" 
        short_sec = self.shortSec.text() if self.shortSec.text() != "" else "0" 
        self.shorttimeout = (int(short_hour)*3600+int(short_min)*60+int(short_sec))*1000
        log(self.shorttimeout)
        return self.shorttimeout
        
    #启动各种计时器
    def start_timers(self,shorttimeout):
        #休息计时器
        self.shorttimer.start(shorttimeout)
        self.shortRest.setDisabled(True)
        self.longRest.setDisabled(True)        
        #更新倒计时
        self.update_countdown_timer.start(COUNTDOWN_TIME)
        #更新tooltips
        self.tips_timer.start(TOOLTIPS_TIME)    
        self.update_tooltips() #更新一次    
        #退出全屏时休息，每30秒检查一次
        if "set" not in config.keys() or config["set"]["afterfullscreen"] == True: 
            self.checkfulltimer.start(FULLSCREEN_CHECK_TIME)
        #退出空闲状态时休息，每60秒检查一次
        if "set" not in config.keys() or config["set"]["afteridle"] == True: 
            self.check_idle_timer.start(IDLE_CHECK_TIME)
            
    def stop_timers(self):
        self.shorttimer.stop()
        # self.longtimer.stop()
        self.update_countdown_timer.stop()
        self.checkfulltimer.stop()
        self.check_idle_timer.stop()



    def showSet(self):
        # self.setting = Set(self)
        self.setting.show()

    def showSchedule(self):
        # self.schd = schedule.Schedule(self)
        # self.schd.show()
        self.schedule.show()
        
    def showSend(self):
        # self.schd = schedule.Schedule(self)
        # self.schd.show()
        self.sendfile.show()
        
    def ontimer(self,flag=None):
        log("in ontimer-------------------------------")
        #同时只有一个休息
        if self.resting == True:
            return
        #带flag的：全屏出来、立即短休息、立即长休息
        log(f'flag:{flag}')
        if flag:
            if "now" in flag:
                flag = flag.replace("now","")
                if self.rest_count < int(self.longitv.text()):
                    self.rest_count += 1 #立即休息的累加，全屏出来的不累加
                
            self.flag = flag
            if flag == "long":
                self.rest_count = 0
        else:
            self.rest_count += 1 #不管实际有没有休息都累加
            log(f'rest_count:{self.rest_count}')
            if self.rest_count <= int(self.longitv.text()):
                self.flag = "short"
            else:
                self.flag = "long"
                self.rest_count = 0
            if self.flag == "short" and not self.shortRest.isChecked():  #不短休息，直接返回
                return
            if self.flag == "long" and not self.longRest.isChecked(): #不长休息，改成短休息
                self.flag = "short"
        log(f'self.flag:{self.flag}')
        #播放休息前提示音
        if config[self.flag]["restset"]["beforesound"]:
            self.play_music(config[self.flag]["restset"]["beforesoundpath"],False,config[self.flag]["restset"]["beforesoundvol"])
        #全屏不休息
        if "set" not in config.keys() or config["set"]["fullscreen"] == True:
            if self.check_fullscreen():
                log("full screen,not rest")
                if self.store_flag != "long":
                    self.store_flag = self.flag
                # log(f'store_flag:{self.store_flag}')
                return
        #空闲不休息
        if "set" not in config.keys() or config["set"]["idle"] == True:
            if time.time()-self.lastActiveTime > IDLE_TIME:
                log("idle,not rest")
                if self.idle_store_flag != "long":
                    self.idle_store_flag = self.flag
                return
        self.store_flag = None
        self.idle_store_flag = None
        #停止计时
        # if timer == self.shorttimer:   
        if self.flag == "short":
            short_hour = self.shortHour2.text() if self.shortHour2.text() != "" else "0" 
            short_min = self.shortMin2.text() if self.shortMin2.text() != "" else "0" 
            short_sec = self.shortSec2.text() if self.shortSec2.text() != "" else "0" 
            rest_time = (int(short_hour)*3600+int(short_min)*60+int(short_sec))*1000
            log(f'rest_time:{rest_time}ms')
            # self.restingtimer = self.shorttimer
        # elif timer == self.longtimer:       
        elif self.flag == "long":
            long_hour = self.longHour2.text() if self.longHour2.text() != "" else "0" 
            long_min = self.longMin2.text() if self.longMin2.text() != "" else "0" 
            long_sec = self.longSec2.text() if self.longSec2.text() != "" else "0" 
            rest_time = (int(long_hour)*3600+int(long_min)*60+int(long_sec))*1000
            log(rest_time)
            # self.restingtimer = self.longtimer
        self.restingtimer = self.shorttimer
        self.resting = True
        self.restingtimer.stop()
        #截屏
        self.filename = os.getenv("temp")+"\\screen.jpg"
        log(f'screenshot path:{self.filename}')
        self.screen = QGuiApplication.primaryScreen()
        self.screen.grabWindow(0).save(self.filename,"jpg")
        time.sleep(1)
        #播放声音
        if config[self.flag]["restset"]["insound"]:
            log("play resting music...")
            self.play_music(config[self.flag]["restset"]["insoundpath"],True,config[self.flag]["restset"]["insoundvol"]) 
        #启动终止休息计时器
        self.rest_timer = QTimer()        
        self.rest_timer.setSingleShot(True)
        self.rest_timer.start(rest_time)        
        #展示界面        
        if config[self.flag]["restset"]["ui"] == "pop":   
            self.rest_timer.timeout.connect(self.recover_pop)
            self.lockScreen(rest_time)
        elif config[self.flag]["restset"]["ui"] == "roll":   
            self.rest_timer.timeout.connect(self.recover_roll)
            self.rollPic(rest_time)
        
        
    #锁定屏幕，弹框
    def lockScreen(self,rest_time):  
        self.transwin.show()
        #启动终止休息计时器
        # self.pop_timer = QTimer()
        # self.pop_timer.timeout.connect(self.recover_pop)
        # self.pop_timer.setSingleShot(True)
        # self.pop_timer.start(rest_time)
        #展示弹框
        self.popup = QMessageBox()
        self.popup.setWindowTitle("休息中")
        self.popup.setText("正在休息中。。。(还剩"+str(rest_time//1000)+"秒)")
        skipbtn = QPushButton("跳过")
        self.popup.addButton(skipbtn,QMessageBox.AcceptRole)
        skipbtn.clicked.connect(self.recover_pop)
        if not Config.config["set"]["allowskip"]:
            skipbtn.hide()
        self.popup.setWindowFlags(Qt.WindowStaysOnTopHint|Qt.WindowMaximizeButtonHint | Qt.MSWindowsFixedSizeDialogHint)
        # self.popup.setFixedSize(200,80)
        self.update_pop_cd_timer = QTimer()
        self.update_pop_cd_timer.timeout.connect(self.update_pop_cd)
        self.update_pop_cd_timer.start(400)
        self.popup.exec()
    #轮播图片    
    def rollPic(self,rest_time):  
        self.rollwin.set_timer(self.restingtimer,self.flag)
        self.rollwin.show()
        self.rollwin.setCDText("还剩"+str(rest_time//1000)+"秒,按Ctrl+X退出") #初始化
        #启动终止休息计时器
        # self.roll_timer = QTimer()
        # self.roll_timer.timeout.connect(self.recover_roll)
        # self.roll_timer.setSingleShot(True)
        # self.roll_timer.start(rest_time)
        #轮播图片
        self.update_roll_cd_timer = QTimer()
        self.update_roll_cd_timer.timeout.connect(self.update_roll_cd)
        self.update_roll_cd_timer.start(20000)
    #播放音乐
    def play_music(self,music,loop = True,volume = 20):
        self.player = QMediaPlayer()
        self.player.currentMediaChanged.connect(self.mediaChange)
        log("music："+music)
        self.playlist = QMediaPlaylist()
        if loop:
            self.playlist.setPlaybackMode(QMediaPlaylist.Loop)
        if os.path.isfile(music):
            self.playlist.addMedia(QMediaContent(QUrl.fromLocalFile(music)))
        else:
            filelist = []
            for i in os.listdir(music): #filter
                ext = os.path.splitext(i)[1]
                # log(ext)
                if ext in [".mp3",".wav",".wma",".flac"]:
                    filelist.append(music+"\\"+i)
            while len(filelist)>0:
                file = filelist.pop(random.randint(0,len(filelist)-1))
                # log("add music："+file)
                self.playlist.addMedia(QMediaContent(QUrl.fromLocalFile(file)))
        self.player.setPlaylist(self.playlist)
        log("volume:"+str(volume))
        self.player.setVolume(volume)
        if loop:
            log("playing music...")
            self.player.play()
        else:
            self.player.play()
            time.sleep(2)
    def mediaChange(self,media):
        log(f"current media:{media.request().url().fileName()}")
            
    #休息结束
    def recover_pop(self):
        self.resting = False
        # self.pop_timer.stop()
        self.rest_timer.stop()
        self.popup.close()
        self.player.stop()
        self.transwin.hide()
        self.restingtimer.start(self.shorttimeout)
        self.update_tooltips() #更新一次    
        log("rest end")
    def recover_roll(self,timer = None):
        self.resting = False
        # self.roll_timer.stop()
        self.rest_timer.stop()
        self.player.stop()
        self.rollwin.hide()
        if timer != None:
            timer.start(self.shorttimeout)
        else:
            self.restingtimer.start(self.shorttimeout)
        self.update_tooltips() #更新一次    
        log("rest end")
    #休息设置
    def showRestSetShort(self):
        self.restset = RestSet(self,"short")
        self.restset.show()

    def showRestSetLong(self):
        self.restset = RestSet(self,"long")
        self.restset.show()
    #更新倒计时
    def update_countdown(self):
        # if self.shorttimer.isActive():
        if self.shortRest.isChecked():
            short_countdown = self.shorttimer.remainingTime()
            # log(short_countdown)
            if int(self.longitv.text()) != 0 and int(self.longitv.text()) == self.rest_count: #下次是长休息了，加一个间隙
                short_countdown += self.shorttimeout
            self.short_cd_label2.setText(str(short_countdown//1000//3600)+":"+str(short_countdown//1000%3600//60)+":"+str(short_countdown//1000%60))
        # if self.longtimer.isActive():
        if self.longRest.isChecked():
            long_countdown = (int(self.longitv.text()) - self.rest_count) * self.shorttimeout + self.shorttimer.remainingTime()
            self.long_cd_label2.setText(str(long_countdown//1000//3600)+":"+str(long_countdown//1000%3600//60)+":"+str(long_countdown//1000%60))
    #更新tooltips
    def update_tooltips(self):
        tooltips = ""
        
        if self.shortRest.isChecked():
            short_countdown = self.shorttimer.remainingTime()
            if int(self.longitv.text()) == self.rest_count: #下次是长休息了，加一个间隙
                short_countdown += self.shorttimeout
            tooltips += "短休息:"+str(short_countdown//1000//3600)+"时"+str(short_countdown//1000%3600//60)+"分\n"
        if self.longRest.isChecked():
            long_countdown = (int(self.longitv.text()) - self.rest_count) * self.shorttimeout + self.shorttimer.remainingTime()
            tooltips += "长休息:"+str(long_countdown//1000//3600)+"时"+str(long_countdown//1000%3600//60)+"分"
        self.trayIcon.setToolTip(tooltips)
        

    #更新休息结束倒计时
    def update_pop_cd(self):
        # cd = self.pop_timer.remainingTime()
        cd = self.rest_timer.remainingTime()
        self.popup.setText("正在休息中。。。(还剩"+str(cd//1000)+"秒)")
        #self.popup.setWindowFlags(Qt.WindowStaysOnTopHint|Qt.WindowMaximizeButtonHint | Qt.MSWindowsFixedSizeDialogHint)

    def update_roll_cd(self):
        # cd = self.roll_timer.remainingTime()
        cd = self.rest_timer.remainingTime()
        if cd >= 0:
            self.rollwin.setCDText("还剩"+str(cd//1000)+"秒,按Ctrl+X退出")
        self.rollwin.update() #引起paintevent，更新图片
        #self.rollwin.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint)
    #检查全屏
    def check_fullscreen(self):
        fg_win = win32gui.GetForegroundWindow()
        # log(fg_win)
        title = win32gui.GetWindowText(fg_win)
        # log(title)
        if title == "":
            # log("desktop")
            return False
        rect = win32gui.GetWindowRect(fg_win)
        # log(rect)
        screen = QGuiApplication.primaryScreen().geometry()
        # log(screen)
        fgwin_width = rect[2]-rect[0]
        fgwin_height = rect[3]-rect[1]
        # log(f'({fgwin_width} ,{fgwin_height})--({screen.width()},{screen.height()})')
        
        # screen = QGuiApplication.primaryScreen()
        # rect2 = screen.geometry()
        # log(rect2)
        # log(f'{rect[2]},{rect2.width()},{rect[3]},{rect2.height()}')
        # if rect[2] == rect2.width() and rect[3] == rect2.height():
        if fgwin_width == screen.width() and fgwin_height == screen.height():        
            return True
        else:
            return False
            
    def real_check_fullscreen(self):
        if self.check_fullscreen():
            return
        # log(f'store_flag:{self.store_flag}')
        if self.store_flag is not None:
            log("check not fullscreen and has store,rest")
            self.ontimer(self.store_flag)
        
            
    #保存配置
    def save_config(self):
        if "short" not in config.keys():
            config["short"] = {}
        config["short"]["enable"] = self.shortRest.isChecked()
        config["short"]["itvHour"] = self.shortHour.text() if self.shortHour.text() != "" else "0" 
        config["short"]["itvMin"] = self.shortMin.text() if self.shortMin.text() != "" else "0" 
        config["short"]["itvSec"] = self.shortSec.text() if self.shortSec.text() != "" else "0" 
        config["short"]["conHour"] = self.shortHour2.text() if self.shortHour2.text() != "" else "0" 
        config["short"]["conMin"] = self.shortMin2.text() if self.shortMin2.text() != "" else "0" 
        config["short"]["conSec"] = self.shortSec2.text() if self.shortSec2.text() != "" else "0" 
        if "long" not in config.keys():
            config["long"] = {}
        config["long"]["enable"] = self.longRest.isChecked()
        # config["long"]["itvHour"] = self.longHour.text() if self.longHour.text() != "" else "0" 
        # config["long"]["itvMin"] = self.longMin.text() if self.longMin.text() != "" else "0" 
        # config["long"]["itvSec"] = self.longSec.text() if self.longSec.text() != "" else "0" 
        config["long"]["itvCount"] = self.longitv.text() if self.longitv.text() != "" else "0" 
        config["long"]["conHour"] = self.longHour2.text() if self.longHour2.text() != "" else "0" 
        config["long"]["conMin"] = self.longMin2.text() if self.longMin2.text() != "" else "0" 
        config["long"]["conSec"] = self.longSec2.text() if self.longSec2.text() != "" else "0" 
        Config.save()
        # with open(configfile,"w") as f:
        #     f.write(json.dumps(config,indent=4))
    def quitapp(self):
        self.hm.UnhookMouse()
        self.hm.UnhookKeyboard()
        log(config)
        self.save_config()
        self.game_rest = False
        self.sendfile.stop()
        QCoreApplication.quit()

    def closeEvent(self,e):
        # log(config)
        self.save_config()
        self.hide()
        e.ignore()
        
    def dragEnterEvent(self,event):
        event.acceptProposedAction()
        
    def dropEvent(self,event):
        files = event.mimeData().urls()
        log(files)
        self.sendfile.dragSendfile(files)
        
    def acceptThread(self):
        s = socket.socket()        
        host = "localhost"
        port = 11233
        s.bind((host, port))
        s.listen()                
        s.settimeout(5)
        self.game_rest = True
        while True:
            try:
                c,addr = s.accept()    
            except socket.timeout as e:
                # print(e)
                # print("reminder accept check stop..")
                if self.game_rest == False: #退出线程
                    break
                else:
                    continue
            log(f'rest request from {addr}')
            # print(c)
            # print(addr)
            self.restnow.emit()



#休息设置对话框     
class RestSet(QWidget):
    def __init__(self,par,flag):
        super().__init__()
        self.flag = flag
        self.setWindowTitle("休息设置")
        rect = par.geometry()
        self.setGeometry(rect.x(), rect.y(), 450, 200)
        #界面
        self.pop = QRadioButton("提示框")
        self.roll = QRadioButton("轮播图片")
        label = QLabel("   图片目录")
        self.picEdit = QLineEdit()
        openDlg = QPushButton("打开...")
        openDlg.setMaximumWidth(60)
        openDlg.clicked.connect(self.openDir)
        hbox = QHBoxLayout()
        hbox.addWidget(label)
        hbox.addWidget(self.picEdit)
        hbox.addWidget(openDlg)
        ui_vbox = QVBoxLayout()
        ui_vbox.addWidget(self.pop)
        ui_vbox.addWidget(self.roll)
        ui_vbox.addLayout(hbox)
        ui_gb = QGroupBox("界面")
        ui_gb.setLayout(ui_vbox)
        #声音
        self.beforeSoundCheck = QCheckBox("休息前")
        self.beforeSoundEdit = QLineEdit()
        beforeOpenSoundbtn = QPushButton("打开...")
        beforeOpenSoundbtn.setMaximumWidth(60)
        beforeOpenSoundbtn.clicked.connect(self.before_open_sound)
        self.beforeVolbtn = QPushButton("音量")
        self.beforeVolbtn.setMaximumWidth(40)
        self.beforeVolbtn.clicked.connect(self.before_open_vol)
        before_hbox = QHBoxLayout()
        before_hbox.addWidget(self.beforeSoundCheck)
        before_hbox.addWidget(self.beforeSoundEdit)
        before_hbox.addWidget(beforeOpenSoundbtn)
        before_hbox.addWidget(self.beforeVolbtn)

        self.inSoundCheck = QCheckBox("休息中")
        self.inSoundEdit = QLineEdit()
        inOpenSoundbtn = QPushButton("打开")
        inOpenSoundbtn.setMaximumWidth(40)
        inOpenSoundbtn.clicked.connect(self.in_open_sound)
        inOpenFolderSoundbtn = QPushButton("打开文件夹")
        inOpenFolderSoundbtn.setMaximumWidth(70)
        inOpenFolderSoundbtn.clicked.connect(self.in_openfolder_sound)
        self.inVolbtn = QPushButton("音量")
        self.inVolbtn.setMaximumWidth(40)
        self.inVolbtn.clicked.connect(self.in_open_vol)
        in_hbox = QHBoxLayout()
        in_hbox.addWidget(self.inSoundCheck)
        in_hbox.addWidget(self.inSoundEdit)
        in_hbox.addWidget(inOpenSoundbtn)
        in_hbox.addWidget(inOpenFolderSoundbtn)
        in_hbox.addWidget(self.inVolbtn)

        self.sound_gb = QGroupBox("声音")
        sound_vbox = QVBoxLayout()
        sound_vbox.addLayout(before_hbox)
        sound_vbox.addLayout(in_hbox)
        self.sound_gb.setLayout(sound_vbox)

        vbox = QVBoxLayout()
        vbox.addWidget(ui_gb)
        vbox.addWidget(self.sound_gb)
        self.setLayout(vbox)

        if self.flag == "short":
            self.beforeVol = Volume(1)
            self.inVol = Volume(2)
        else:
            self.beforeVol = Volume(3)
            self.inVol = Volume(4)            

        #初始化
        if self.flag == "short":
            if  config["short"]["restset"]["ui"] == "pop":
                self.pop.setChecked(True)
            else:
                self.roll.setChecked(True)
            self.picEdit.setText(config["short"]["restset"]["uipic"])
            self.beforeSoundCheck.setChecked(config["short"]["restset"]["beforesound"])
            self.beforeSoundEdit.setText(config["short"]["restset"]["beforesoundpath"])
            self.inSoundCheck.setChecked(config["short"]["restset"]["insound"])
            self.inSoundEdit.setText(config["short"]["restset"]["insoundpath"])
        elif self.flag == "long":
            if  config["long"]["restset"]["ui"] == "pop":
                self.pop.setChecked(True)
            else:
                self.roll.setChecked(True)
            self.picEdit.setText(config["long"]["restset"]["uipic"])
            self.beforeSoundCheck.setChecked(config["long"]["restset"]["beforesound"])
            self.beforeSoundEdit.setText(config["long"]["restset"]["beforesoundpath"])
            self.inSoundCheck.setChecked(config["long"]["restset"]["insound"])
            self.inSoundEdit.setText(config["long"]["restset"]["insoundpath"])

    def openDir(self):
        curpath = self.picEdit.text()
        dirname = QFileDialog.getExistingDirectory(self, "打开文件夹", curpath)
        log("dirname:"+str(dirname))
        if dirname != "":
            self.picEdit.setText(dirname)

    def before_open_sound(self):
        curpath = self.beforeSoundEdit.text()
        name = QFileDialog.getOpenFileName(self,"打开文件",curpath,"*.mp3 *.wav *.wma")
        log("name:"+str(name[0]))
        if name[0] != "":
            self.beforeSoundEdit.setText(name[0])    

    def in_open_sound(self):
        curpath = self.inSoundEdit.text()
        name = QFileDialog.getOpenFileName(self,"打开文件",curpath,"*.mp3 *.wav *.wma *.flac")
        log("name:"+str(name[0]))
        if name[0] != "":
            self.inSoundEdit.setText(name[0])           
            
    def in_openfolder_sound(self):
        curpath = self.inSoundEdit.text()
        dirname = QFileDialog.getExistingDirectory(self, "打开文件夹", curpath)
        log("dirname:"+str(dirname))
        if dirname != "":
            self.inSoundEdit.setText(dirname)           

    def before_open_vol(self):
        if self.beforeVol.isHidden():
            log(f'{self.geometry().x()},{self.geometry().y()}')
            log(f'{self.sound_gb.x()},{self.sound_gb.y()}')
            log(f'{self.beforeVolbtn.x()},{self.beforeVolbtn.y()}')
            self.beforeVol.setGeometry(self.geometry().x()+self.sound_gb.x()+self.beforeVolbtn.x(),self.geometry().y()+self.sound_gb.y()+self.beforeVolbtn.y()-50,120,50)
            self.beforeVol.show()
        else:
            self.beforeVol.hide()

    def in_open_vol(self):
        if self.inVol.isHidden():
            log(f'{self.geometry().x()},{self.geometry().y()}')
            log(f'{self.sound_gb.x()},{self.sound_gb.y()}')
            log(f'{self.inVolbtn.x()},{self.inVolbtn.y()}')
            self.inVol.setGeometry(self.geometry().x()+self.sound_gb.x()+self.inVolbtn.x(),self.geometry().y()+self.sound_gb.y()+self.inVolbtn.y()-50,120,50)
            self.inVol.show()
        else:
            self.inVol.hide()

    def closeEvent(self,e):
        if self.beforeVol.isVisible():
            self.beforeVol.hide()
        if self.pop.isChecked():
            config[self.flag]["restset"]["ui"] = "pop"
        elif self.roll.isChecked():
            config[self.flag]["restset"]["ui"] = "roll"
        config[self.flag]["restset"]["uipic"] = self.picEdit.text()
        config[self.flag]["restset"]["beforesound"] = self.beforeSoundCheck.isChecked()
        config[self.flag]["restset"]["beforesoundpath"] = self.beforeSoundEdit.text()
        config[self.flag]["restset"]["insound"] = self.inSoundCheck.isChecked()
        config[self.flag]["restset"]["insoundpath"] = self.inSoundEdit.text()
        Config.save()
        # with open(configfile,"w") as f:
        #     f.write(json.dumps(config,indent=4))

class Volume(QWidget):
    def __init__(self,flag):
        super().__init__()
        self.flag = flag
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint)
        # self.setGeometry(100,100,50,100)
        hbox = QHBoxLayout()
        slider = QSlider(Qt.Horizontal)
        if flag == 1:
            value = config["short"]["restset"]["beforesoundvol"]
        elif flag == 2:
            value = config["short"]["restset"]["insoundvol"]
        elif flag == 3:
            value = config["long"]["restset"]["beforesoundvol"]
        elif flag == 4:
            value = config["long"]["restset"]["insoundvol"]
        log(value)
        slider.setValue(value)
        slider.valueChanged.connect(self.changevalue)
        self.label = QLabel(str(slider.value()))
        hbox.addWidget(slider)
        hbox.addWidget(self.label)
        self.setLayout(hbox)
        
    def changevalue(self,value):
        self.label.setText(str(value))
        if self.flag == 1:
             config["short"]["restset"]["beforesoundvol"]  = value
        elif self.flag == 2:
            config["short"]["restset"]["insoundvol"] = value
        elif self.flag == 3:
            config["long"]["restset"]["beforesoundvol"] = value
        elif self.flag == 4:
            config["long"]["restset"]["insoundvol"] = value       

#设置对话框     
class Set(QWidget):
    def __init__(self,par):
        super().__init__()
        self.setWindowTitle("设置")
        rect = par.geometry()
        self.par = par
        self.setGeometry(rect.x()+50,rect.y()+50,200,100)
        self.autorun = QCheckBox("开机启动")
        self.autorun.stateChanged.connect(self.setAutorun)
        self.nocmd = QCheckBox("开机启动后不显示命令行窗口")
        self.nocmd.stateChanged.connect(self.setNocmd)
        self.minimize = QCheckBox("启动后最小化")
        self.minimize.stateChanged.connect(self.setMinimize)
        self.fullscreen = QCheckBox("全屏时不休息只提醒")
        self.fullscreen.stateChanged.connect(self.setfsrest)
        self.afterfs = QCheckBox("退出全屏后立即休息")
        self.afterfs.stateChanged.connect(self.setafterfs)
        self.idle = QCheckBox("空闲时不休息（空闲指10分钟无动作）")
        self.idle.stateChanged.connect(self.setidlerest)
        self.afteridle = QCheckBox("退出空闲状态后立即休息")
        self.afteridle.stateChanged.connect(self.setafteridle)
        self.allowskip = QCheckBox("允许跳过休息")
        self.allowskip.stateChanged.connect(self.setAllowskip)
        self.fsshowtime = QCheckBox("全屏程序显示时间")
        if "set" not in Config.config.keys():
            Config.config["set"] = {}
            # self.autorun.setChecked(True)
            # self.minimize.setChecked(True)
            # self.fullscreen.setChecked(True)
            # self.afterfs.setChecked(True)
            # self.idle.setChecked(True)
            # self.afteridle.setChecked(True)
            # self.allowskip.setChecked(True)
            # self.fsshowtime.setChecked(True)
        # else:
        if "autorun" not in Config.config["set"]:
            Config.config["set"]["autorun"] = True             
        self.autorun.setChecked(Config.config["set"]["autorun"])
        if "nocmd" not in Config.config["set"]:
            Config.config["set"]["nocmd"] = False 
        self.nocmd.setChecked(Config.config["set"]["nocmd"])
        if "minimize" not in Config.config["set"]:
            Config.config["set"]["minimize"] = True
        self.minimize.setChecked(Config.config["set"]["minimize"])
        if "fullscreen" not in Config.config["set"]:
            Config.config["set"]["fullscreen"] = True            
        self.fullscreen.setChecked(Config.config["set"]["fullscreen"])
        if "afterfullscreen" not in Config.config["set"]:
            Config.config["set"]["afterfullscreen"] = True              
        self.afterfs.setChecked(Config.config["set"]["afterfullscreen"])
        if "idle" not in Config.config["set"]:
            Config.config["set"]["idle"] = True              
        self.idle.setChecked(Config.config["set"]["idle"])
        if "afteridle" not in Config.config["set"]:
            Config.config["set"]["afteridle"] = True              
        self.afteridle.setChecked(Config.config["set"]["afteridle"])
        if "allowskip" not in Config.config["set"]:
            Config.config["set"]["allowskip"] = True
        self.allowskip.setChecked(Config.config["set"]["allowskip"])
        if "fsshowtime" not in Config.config["set"]:
            Config.config["set"]["fsshowtime"] = True
        self.fsshowtime.setChecked(Config.config["set"]["fsshowtime"])
            
        self.fsshowtime.stateChanged.connect(self.setFsshowtime) #放后面，防止自动触发
            
        vbox = QVBoxLayout()
        vbox.addWidget(self.autorun)
        vbox.addWidget(self.nocmd)
        vbox.addWidget(self.minimize)
        vbox.addWidget(self.fullscreen)
        hbox = QHBoxLayout()
        label = QLabel(" ")
        label.setMaximumWidth(10)
        hbox.addWidget(label)
        hbox.addWidget(self.afterfs)
        vbox.addLayout(hbox)
        
        vbox.addWidget(self.idle)
        hbox2 = QHBoxLayout()
        label2 = QLabel(" ")
        label2.setMaximumWidth(10)
        hbox2.addWidget(label2)
        hbox2.addWidget(self.afteridle)
        vbox.addLayout(hbox2)
        
        vbox.addWidget(self.allowskip)
        vbox.addWidget(self.fsshowtime)
        self.setLayout(vbox)

    def setAutorun(self,state):
        log(sys.argv)
        'HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run'
        settings = QSettings("HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run",QSettings.NativeFormat)
        if state == Qt.Checked:
            Config.config["set"]["autorun"] = True
            if "nocmd" in Config.config["set"].keys() and Config.config["set"]["nocmd"]:
                path = os.path.dirname(os.path.abspath(sys.argv[0]))+"\\reminderw.bat"
            else:
                path = os.path.dirname(os.path.abspath(sys.argv[0]))+"\\reminder.bat"
            log(f'{os.path.splitext(os.path.basename(sys.argv[0]))[0]}, {path}')
            settings.setValue(os.path.splitext(os.path.basename(sys.argv[0]))[0],path)
            # settings.setValue(os.path.splitext(os.path.basename(__file__))[0], os.path.abspath(__file__))
        elif state == Qt.Unchecked:
            Config.config["set"]["autorun"] = False
            settings.remove(os.path.splitext(os.path.basename(sys.argv[0]))[0])
            # settings.remove(os.path.splitext(os.path.basename(__file__))[0])

    def setNocmd(self,state):
        if state == Qt.Checked:
            Config.config["set"]["nocmd"] = True
        elif state == Qt.Unchecked:
            Config.config["set"]["nocmd"] = False  
        if Config.config["set"]["autorun"]:
            self.setAutorun(Qt.Checked)        

    def setMinimize(self,state):
        if state == Qt.Checked:
            Config.config["set"]["minimize"] = True
        elif state == Qt.Unchecked:
            Config.config["set"]["minimize"] = False
            
    def setfsrest(self,state):
        if state == Qt.Checked:
            Config.config["set"]["fullscreen"] = True
        elif state == Qt.Unchecked:
            Config.config["set"]["fullscreen"] = False
            Config.config["set"]["afterfullscreen"] = False
            self.par.checkfulltimer.stop()
            self.afterfs.setChecked(False)
            
    def setafterfs(self,state):
        if state == Qt.Checked:
            Config.config["set"]["fullscreen"] = True
            Config.config["set"]["afterfullscreen"] = True
            self.par.checkfulltimer.start(FULLSCREEN_CHECK_TIME)
            self.fullscreen.setChecked(True)
        elif state == Qt.Unchecked:
            Config.config["set"]["afterfullscreen"] = False
            self.par.checkfulltimer.stop()
            self.afterfs.setChecked(False)
            
    def setidlerest(self,state):
        if state == Qt.Checked:
            Config.config["set"]["idle"] = True
        elif state == Qt.Unchecked:
            Config.config["set"]["idle"] = False
            Config.config["set"]["afteridle"] = False
            self.par.check_idle_timer.stop()
            self.afteridle.setChecked(False)
            
    def setafteridle(self,state):
        if state == Qt.Checked:
            Config.config["set"]["idle"] = True
            Config.config["set"]["afteridle"] = True
            self.par.check_idle_timer.start(IDLE_CHECK_TIME)
            self.idle.setChecked(True)
        elif state == Qt.Unchecked:
            Config.config["set"]["afteridle"] = False
            self.par.check_idle_timer.stop()
            self.afteridle.setChecked(False)
            
    def setAllowskip(self,state):
        if state == Qt.Checked:
            Config.config["set"]["allowskip"] = True
        elif state == Qt.Unchecked:
            Config.config["set"]["allowskip"] = False
    def setFsshowtime(self,state):
        if state == Qt.Checked:
            Config.config["set"]["fsshowtime"] = True
            self.par.fstimeAction.setText("关闭全屏显示时间")
            self.par.showtime.start()
        elif state == Qt.Unchecked:
            Config.config["set"]["fsshowtime"] = False
            self.par.fstimeAction.setText("开启全屏显示时间")
            self.par.showtime.stop()
            
    def closeEvent(self,e):
        Config.save()

#锁定屏幕窗口
class TransWin(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint)
        # self.setAttribute(Qt.WA_TranslucentBackground)
        self.screen = QGuiApplication.primaryScreen()
        self.filename = os.getenv("temp")+"\\screen.jpg"
        log(self.filename)
        self.rect = self.screen.geometry()
        self.setGeometry(self.rect)

    def paintEvent(self,e):
        painter = QPainter(self)
        # log("paintevent")
        painter.drawPixmap(self.rect,QPixmap(self.filename))

#轮播图片窗口
class RollPic(QWidget):
    def __init__(self,par):
        super().__init__()
        self.par = par
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint)
        # self.setAttribute(Qt.WA_TranslucentBackground)
        screen = QGuiApplication.primaryScreen()
        hbox = QHBoxLayout()
        self.cdlabel = QLabel("按Ctrl+X退出")
        hbox.addWidget(self.cdlabel)
        QShortcut(QKeySequence("Ctrl+X"),self).activated.connect(self.recover)
        hbox.setAlignment(Qt.AlignHCenter|Qt.AlignTop)
        self.setLayout(hbox)
        self.rect = screen.geometry()
        self.setGeometry(self.rect)

    def paintEvent(self,e):
        painter = QPainter(self)
        # log("paintevent")
        if len(self.filelist) == 0:
            path = os.getenv("temp")+"\\screen.jpg"
        else:  
            path = self.filelist[random.randint(0,len(self.filelist)-1)]
        # log(path)
        sec = str(random.randint(0,1000))
        painter.drawPixmap(self.rect,QPixmap(path))

    def setCDText(self,text):
        self.cdlabel.setText(text)

    def set_timer(self,timer,flag):
        self.timer = timer
        self.filelist = []
        tmplist = []
        picdir = config[flag]["restset"]["uipic"]
        log(f'picture dir:{picdir}')
        tmplist = os.listdir(picdir)  
        for file in tmplist:
            path = os.path.join(picdir, file)
            if os.path.isdir(path):
                continue
            if os.path.splitext(file)[-1] in [".jpg",".jpeg",".png",".bmp"]:
                self.filelist.append(path)

    def recover(self):
        if Config.config["set"]["allowskip"]:
            self.par.recover_roll(self.timer)

class ShowTime(QWidget):
    def __init__(self):
        log("in show time init")
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint|Qt.SubWindow)
        self.setAttribute(Qt.WA_TranslucentBackground)
        # self.setWindowOpacity(1)
        self.m_bDrag = False
        screen = QGuiApplication.primaryScreen()
        vbox = QVBoxLayout()
        self.cdlabel = QLabel(time.strftime("%H:%M", time.localtime()))
        # self.cdlabel.setMaximumHeight(20)
        self.cdlabel.setStyleSheet("color: #dfdfdf;font-size: 13px;font-family: 微软雅黑;")
        vbox.addWidget(self.cdlabel)
        # self.btn = QPushButton("3333")
        # self.btn.clicked.connect(self.setmyFont)
        # vbox.addWidget(self.btn)
        self.systimer = QTimer()
        self.systimer.timeout.connect(self.updatetime)
        self.systimer.setInterval(3000)
        self.systimer.start()
        vbox.setAlignment(Qt.AlignHCenter)
        self.setLayout(vbox)
        # vbox.setSpacing(0)
        # log(vbox.spacing())
        self.rect = screen.geometry()
        # print(self.rect)
        # print(self.rect.right(),self.rect.top())
        # log(self.cdlabel.margin())
        # log(self.cdlabel.indent())
        # log(self.cdlabel.frameWidth())
        # log(vbox.margin())
        # log(self.frameWidth())
        # self.setGeometry(rect.center().x(),rect.center().y(),40,20)
        self.setCursor(Qt.SizeAllCursor)
        self.chkfstimer = QTimer()
        self.chkfstimer.timeout.connect(self.check_fullscreen)
        self.chkfstimer.setInterval(3000)
        # self.chkfstimer.start()
        self.showstate = False
        self.setGeometry(self.rect.right()-55,self.rect.top(),40,40)
        self.setWindowTitle("showtime")

    # def setmyFont(self):
        # font = QFontDialog.getFont(self.cdlabel.font())
        # log(font)
        # qi = QFontInfo(font[0])
        # log(str(qi.family(),qi.styleName(),qi.pointSize()))
        # if font[1]:
            # self.cdlabel.setFont(font[0])
        
    def start(self):
        log("show time timer start")
        self.chkfstimer.start()
        
    def stop(self):
        log("show time timer stop")
        self.chkfstimer.stop()
        self.hide()
        
    def updatetime(self):
        self.cdlabel.setText(time.strftime("%H:%M", time.localtime())) 
        
    #检查全屏
    def check_fullscreen(self):
        self.fg_win = win32gui.GetForegroundWindow()
        # log(self.fg_win)
        title = win32gui.GetWindowText(self.fg_win)
        # log(title)
        if title == "" or title == "iTop Easy Desktop": #桌面分组软件
            # log("desktop")
            if not self.isHidden():
                log("desktop,hide time")
                self.hide()
            return False
        rect = win32gui.GetWindowRect(self.fg_win)
        # log(rect)
        screen = QGuiApplication.primaryScreen().geometry()
        # log(screen)
        fgwin_width = rect[2]-rect[0]
        fgwin_height = rect[3]-rect[1]
        # log(f'({fgwin_width} ,{fgwin_height})--({screen.width()},{screen.height()})')
        if fgwin_width == screen.width() and fgwin_height == screen.height():
            # log("full screen")
            if self.isHidden():
                self.show()
                # log("show time")
                win32gui.SetForegroundWindow(self.fg_win)
                # if not self.isHidden(): #无效
                    # hd = win32gui.FindWindow("Qt5152QWindowIcon","showtime")
                    # print(hex(hd))
                    # win32gui.SetForegroundWindow(hd)
        else:
            # log("not full screen")
            if not self.isHidden():
                self.hide()
                # log("hide time")
            # if self.isHidden():
                # self.show()
                
        
    def mousePressEvent(self,event):
        if event.button() == Qt.LeftButton:
            self.chkfstimer.stop()
            self.m_bDrag = True
            self.mouseStartPoint = event.globalPos()
            self.windowTopLeftPoint = self.frameGeometry().topLeft()

    def mouseMoveEvent(self,event):
        if self.m_bDrag:
            distance = event.globalPos() - self.mouseStartPoint
            self.move(self.windowTopLeftPoint + distance)

    def mouseReleaseEvent(self,event):
        log("in mouse release event")
        if event.button() == Qt.LeftButton:
            win32gui.SetForegroundWindow(self.fg_win)
            self.chkfstimer.start()
            self.m_bDrag = False
            




if __name__ == '__main__':
    log(sys.argv)
    app = QApplication(sys.argv)
    ex = RemainderMain()
    sys.exit(app.exec_())