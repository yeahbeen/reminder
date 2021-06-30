import sys
import os
import time
import random
import json
import win32gui
from PyQt5.QtWidgets import *
from PyQt5.QtGui import (QIcon,QKeySequence,QPixmap,QGuiApplication,QPainter,QColor,QTextCharFormat,QBrush,QTextCursor,QFont)
from PyQt5.QtCore import *
from PyQt5.QtMultimedia import QMediaPlayer,QMediaContent,QMediaPlaylist
import schedule
from config import Config
import mytimer
# import ctypes
# from ctypes import wintypes

workdir = os.path.dirname(__file__)
print("workdir:"+workdir)

Config.init()
config = Config.config

class RemainderMain(QWidget):
    def __init__(self):
        super().__init__()
        #短暂休息界面
        self.shortRest = QGroupBox("短暂休息")
        self.shortRest.setCheckable(True)
        short_cd_hbox =  QHBoxLayout()
        self.shortHour = QLineEdit("1")
        self.shortMin = QLineEdit("0")
        self.shortSec = QLineEdit("0")
        self.shortHour.setPlaceholderText("0")
        self.shortMin.setPlaceholderText("0")
        self.shortSec.setPlaceholderText("0")
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel("休息间隔"))
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
        hbox2.addWidget(QLabel("休息时长"))
        hbox2.addWidget(self.shortHour2)
        hbox2.addWidget(QLabel("小时"))
        hbox2.addWidget(self.shortMin2)
        hbox2.addWidget(QLabel("分"))
        hbox2.addWidget(self.shortSec2)
        hbox2.addWidget(QLabel("秒"))
        self.shortSet = QPushButton('休息设置')
        self.shortSet.clicked.connect(self.showRestSetShort)
        vbox = QVBoxLayout()
        vbox.addLayout(short_cd_hbox)
        vbox.addLayout(hbox)
        vbox.addLayout(hbox2)
        vbox.addWidget(self.shortSet)
        self.shortRest.setLayout(vbox) 
        #长休息界面
        self.longRest = QGroupBox("长休息")
        self.longRest.setCheckable(True)
        long_cd_hbox =  QHBoxLayout()
        self.longHour = QLineEdit("3")
        self.longMin = QLineEdit("0")
        self.longSec = QLineEdit("0")
        self.longHour.setPlaceholderText("0")
        self.longMin.setPlaceholderText("0")
        self.longSec.setPlaceholderText("0")
        hbox3 = QHBoxLayout()
        hbox3.addWidget(QLabel("休息间隔"))
        hbox3.addWidget(self.longHour)
        hbox3.addWidget(QLabel("小时"))
        hbox3.addWidget(self.longMin)
        hbox3.addWidget(QLabel("分"))
        hbox3.addWidget(self.longSec)
        hbox3.addWidget(QLabel("秒"))
        self.longHour2 = QLineEdit("0")
        self.longMin2 = QLineEdit("5")
        self.longSec2 = QLineEdit("0")
        self.longHour2.setPlaceholderText("0")
        self.longMin2.setPlaceholderText("0")
        self.longSec2.setPlaceholderText("0")
        hbox4 = QHBoxLayout()
        hbox4.addWidget(QLabel("休息时长"))
        hbox4.addWidget(self.longHour2)
        hbox4.addWidget(QLabel("小时"))
        hbox4.addWidget(self.longMin2)
        hbox4.addWidget(QLabel("分"))
        hbox4.addWidget(self.longSec2)
        hbox4.addWidget(QLabel("秒"))
        longSet = QPushButton('休息设置')
        longSet.clicked.connect(self.showRestSetLong)
        vbox2 = QVBoxLayout()
        vbox2.addLayout(long_cd_hbox)
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

        self.startbtn = QPushButton("启动")
        self.startbtn.clicked.connect(self.start)
        self.stopbtn = QPushButton("停止")
        self.stopbtn.clicked.connect(self.stop)
        self.stopbtn.setDisabled(True)
        self.setbtn = QPushButton("设置...")
        self.setbtn.clicked.connect(self.showSet)
        self.schedulebtn = QPushButton("定时程序")
        self.schedulebtn.clicked.connect(self.showSchedule)
        start_hbox = QHBoxLayout()
        start_hbox.addWidget(self.startbtn)
        start_hbox.addWidget(self.stopbtn)
        start_hbox.addWidget(self.setbtn)
        start_hbox.addWidget(self.schedulebtn)

        #整体布局
        layout = QVBoxLayout()
        layout.addWidget(self.shortRest)
        layout.addWidget(self.longRest)
        layout.addLayout(countdown_hbox)
        layout.addLayout(start_hbox)
        self.setLayout(layout)
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
            self.longHour.setText(config["long"]["itvHour"]) 
            self.longMin.setText(config["long"]["itvMin"]) 
            self.longSec.setText(config["long"]["itvSec"]) 
            self.longHour2.setText(config["long"]["conHour"]) 
            self.longMin2.setText(config["long"]["conMin"]) 
            self.longSec2.setText(config["long"]["conSec"]) 

        self.quitAction = QAction("退出")
        self.quitAction.triggered.connect(QCoreApplication.quit)
        self.trayIconMenu = QMenu()
        self.trayIconMenu.addAction(self.quitAction)
        self.trayIcon = QSystemTrayIcon()
        self.trayIcon.setContextMenu(self.trayIconMenu)
        self.trayIcon.setIcon(QIcon(workdir+"\\cherry.ico"))
        self.trayIcon.activated.connect(self.showWin)
        self.trayIcon.show()

        screen = QGuiApplication.primaryScreen()
        rect = screen.geometry()
        self.setGeometry(rect.center().x()-150,rect.center().y()-150, 300, 300)
        self.setWindowTitle('护眼助手')  
        self.lastrestingtime = QTime.currentTime()
        print("lastrestingtime0:"+str(self.lastrestingtime))
        self.show()
        self.start()
        self.schedule = schedule.Schedule(self)
        self.schedule.start()
    
    def showWin(self,action):
        print("action:"+str(action))
        if action == QSystemTrayIcon.Trigger or action == QSystemTrayIcon.DoubleClick:
            self.showNormal()
            self.activateWindow()

    #启动
    def start(self):
        self.save_config()
        self.transwin = TransWin()
        self.rollwin = RollPic(self)
        # self.shorttimer = QTimer()
        # self.longtimer = QTimer()
        self.shorttimer = mytimer.mytimer("pop")
        self.longtimer = mytimer.mytimer("roll")
        #短暂休息
        if self.shortRest.isChecked(): 
            # if config["short"]["restset"]["ui"] == "pop":   
                # self.shorttimer.timeout.connect(self.lockScreen)
            # else:
                # self.shorttimer.timeout.connect(self.rollPic)
            if config["short"]["restset"]["ui"] == "pop":   
                self.shorttimer.set_args("pop")
            else:
                self.shorttimer.set_args("roll")
            self.shorttimer.timeout.connect(self.ontimer)
            short_hour = self.shortHour.text() if self.shortHour.text() != "" else "0" 
            short_min = self.shortMin.text() if self.shortMin.text() != "" else "0" 
            short_sec = self.shortSec.text() if self.shortSec.text() != "" else "0" 
            shorttimeout = (int(short_hour)*3600+int(short_min)*60+int(short_sec))*1000
            print(shorttimeout)
            self.shorttimer.setInterval(shorttimeout)
            self.shorttimer.start()
        #长休息
        if self.longRest.isChecked():
            # if config["long"]["restset"]["ui"] == "roll":   
                # self.longtimer.timeout.connect(self.rollPic)
            # else:
                # self.longtimer.timeout.connect(self.lockScreen)
            if config["long"]["restset"]["ui"] == "roll":   
                self.longtimer.set_args("roll")
            else:
                self.longtimer.set_args("pop")
            self.longtimer.timeout.connect(self.ontimer)
            long_hour = self.longHour.text() if self.longHour.text() != "" else "0" 
            long_min = self.longMin.text() if self.longMin.text() != "" else "0" 
            long_sec = self.longSec.text() if self.longSec.text() != "" else "0" 
            print(long_hour,long_min,long_sec)
            longtimeout = (int(long_hour)*3600+int(long_min)*60+int(long_sec))*1000
            print(longtimeout)
            self.longtimer.setInterval(longtimeout)
            self.longtimer.start()
        #更新倒计时
        self.update_countdown_timer = QTimer()
        self.update_countdown_timer.timeout.connect(self.update_countdown)
        self.update_countdown_timer.start(300)
        #更新tooltips
        self.tips_timer = QTimer()
        self.tips_timer.timeout.connect(self.update_tooltips)
        self.tips_timer.start(60000)    
        self.update_tooltips() #更新一次    
        self.shortRest.setDisabled(True)
        self.longRest.setDisabled(True)
        self.startbtn.setDisabled(True)
        self.stopbtn.setDisabled(False)
        self.resting = False
    #停止
    def stop(self):
        self.shortRest.setDisabled(False)
        self.longRest.setDisabled(False)
        self.startbtn.setDisabled(False)
        self.stopbtn.setDisabled(True)
        self.shorttimer.stop()
        self.longtimer.stop()
        self.update_countdown_timer.stop()
        self.short_cd_label2.setText("00:00:00")
        self.long_cd_label2.setText("00:00:00")


    def showSet(self):
        self.setting = Set(self)
        self.setting.show()

    def showSchedule(self):
        # self.schd = schedule.Schedule(self)
        # self.schd.show()
        self.schedule.show()
        
    def ontimer(self):
        print("in ontimer")
        #同时只有一个休息
        if self.resting == True:
            return
        #距离上一次长休息的时间较短就不休息
        if self.sender() == self.shorttimer:
            self.flag = "short"
            print(self.shorttimer.interval())
            print("lastrestingtime:"+str(self.lastrestingtime))
            print("QTime.currentTime():"+str(QTime.currentTime()))
            print(self.lastrestingtime.msecsTo(QTime.currentTime()))
            if self.lastrestingtime.msecsTo(QTime.currentTime()) < self.shorttimer.interval(): 
                print("just rest,not rest")
                return
        else:
            self.flag = "long"
            self.lastrestingtime = QTime.currentTime()
        #播放休息前提示音
        if config[self.flag]["restset"]["beforesound"]:
            self.play_music(config[self.flag]["restset"]["beforesoundpath"],False,config[self.flag]["restset"]["beforesoundvol"])
        #全屏不休息
        if self.check_fullscreen():
            print("full screen,not rest")
            return
        #停止计时
        if self.sender() == self.shorttimer:   
            short_hour = self.shortHour2.text() if self.shortHour2.text() != "" else "0" 
            short_min = self.shortMin2.text() if self.shortMin2.text() != "" else "0" 
            short_sec = self.shortSec2.text() if self.shortSec2.text() != "" else "0" 
            timeout = (int(short_hour)*3600+int(short_min)*60+int(short_sec))*1000
            print(timeout)
            self.restingtimer = self.shorttimer
        elif self.sender() == self.longtimer:       
            long_hour = self.longHour2.text() if self.longHour2.text() != "" else "0" 
            long_min = self.longMin2.text() if self.longMin2.text() != "" else "0" 
            long_sec = self.longSec2.text() if self.longSec2.text() != "" else "0" 
            timeout = (int(long_hour)*3600+int(long_min)*60+int(long_sec))*1000
            print(timeout)
            self.restingtimer = self.longtimer
        self.resting = True
        self.restingtimer.stop()
        #截屏
        self.screen = QGuiApplication.primaryScreen()
        self.filename = os.getenv("temp")+"\\screen.jpg"
        print(self.filename)
        self.screen.grabWindow(0).save(self.filename,"jpg")
        time.sleep(1)
        #播放声音
        if config[self.flag]["restset"]["insound"]:
            print("play insound")
            if os.path.splitext(config[self.flag]["restset"]["insoundpath"])[-1] in [".mp3",".wav",".wma",".flac"]:
                print("prefix")
                self.play_music(config[self.flag]["restset"]["insoundpath"],True,config[self.flag]["restset"]["insoundvol"]) 
        #展示界面
        if self.restingtimer.args == "pop":
            self.lockScreen(timeout)
        elif self.restingtimer.args == "roll":
            self.rollPic(timeout)

        
    #锁定屏幕，弹框
    def lockScreen(self,timeout):  
        '''
        print("in lockScreen")
        #同时只有一个休息
        if self.resting == True:
            return
        #播放休息前提示音
        if self.sender() == self.shorttimer:
            self.flag = "short"
            print(self.shorttimer.interval())
            print("lastrestingtime:"+str(self.lastrestingtime))
            print("QTime.currentTime():"+str(QTime.currentTime()))
            print(self.lastrestingtime.msecsTo(QTime.currentTime()))
            if self.lastrestingtime.msecsTo(QTime.currentTime()) < self.shorttimer.interval(): #距离上一次长休息的时间较短就不休息
                print("just rest,not rest")
                return
        else:
            self.flag = "long"
            self.lastrestingtime = QTime.currentTime()
        if config[self.flag]["restset"]["beforesound"]:
            self.play_music(config[self.flag]["restset"]["beforesoundpath"],False,config[self.flag]["restset"]["beforesoundvol"])
        #全屏不休息
        if self.check_fullscreen():
            print("full screen,not rest")
            return
        #停止计时
        if self.sender() == self.shorttimer:   
            short_hour = self.shortHour2.text() if self.shortHour2.text() != "" else "0" 
            short_min = self.shortMin2.text() if self.shortMin2.text() != "" else "0" 
            short_sec = self.shortSec2.text() if self.shortSec2.text() != "" else "0" 
            timeout = (int(short_hour)*3600+int(short_min)*60+int(short_sec))*1000
            print(timeout)
            self.restingtimer = self.shorttimer
        elif self.sender() == self.longtimer:       
            long_hour = self.longHour2.text() if self.longHour2.text() != "" else "0" 
            long_min = self.longMin2.text() if self.longMin2.text() != "" else "0" 
            long_sec = self.longSec2.text() if self.longSec2.text() != "" else "0" 
            timeout = (int(long_hour)*3600+int(long_min)*60+int(long_sec))*1000
            print(timeout)
            self.restingtimer = self.longtimer
        self.resting = True
        self.restingtimer.stop()

        #展示界面
        #先截屏
        self.screen = QGuiApplication.primaryScreen()
        self.filename = os.getenv("temp")+"\\screen.jpg"
        print(self.filename)
        self.screen.grabWindow(0).save(self.filename,"jpg")
        time.sleep(1)
        '''
        self.transwin.show()
        #播放声音
        # if config[self.flag]["restset"]["insound"]:
            # print("play insound")
            # if os.path.splitext(config[self.flag]["restset"]["insoundpath"])[-1] in [".mp3",".wav",".wma",".flac"]:
                # print("prefix")
                # self.play_music(config[self.flag]["restset"]["insoundpath"],True,config[self.flag]["restset"]["insoundvol"]) 
        #启动终止休息计时器
        self.pop_timer = QTimer()
        self.pop_timer.timeout.connect(self.recover_pop)
        self.pop_timer.setSingleShot(True)
        self.pop_timer.start(timeout)
        #展示弹框
        self.popup = QMessageBox()
        self.popup.setWindowTitle("休息中")
        self.popup.setText("正在休息中。。。(还剩"+str(timeout//1000)+"秒)")
        skipbtn = QPushButton("跳过")
        self.popup.addButton(skipbtn,QMessageBox.AcceptRole)
        skipbtn.clicked.connect(self.recover_pop)
        self.popup.setWindowFlags(Qt.WindowStaysOnTopHint|Qt.WindowMaximizeButtonHint | Qt.MSWindowsFixedSizeDialogHint)
        # setWindowFlags(Qt.WindowMaximizeButtonHint | Qt.MSWindowsFixedSizeDialogHint)
        # self.popup.setFixedSize(200,80)
        self.update_pop_cd_timer = QTimer()
        self.update_pop_cd_timer.timeout.connect(self.update_pop_cd)
        self.update_pop_cd_timer.start(300)
        self.popup.exec()
    #轮播图片    
    def rollPic(self,timeout):  
        '''
        print("in rollPic")
        #同时只有一个休息
        if self.resting == True:
            return
        #播放休息前提示音
        if self.sender() == self.shorttimer:
            self.flag = "short"
            print(self.shorttimer.interval())
            print("lastrestingtime:"+str(self.lastrestingtime))
            print("QTime.currentTime():"+str(QTime.currentTime()))
            print(self.lastrestingtime.msecsTo(QTime.currentTime()))
            if self.lastrestingtime.msecsTo(QTime.currentTime()) < self.shorttimer.interval(): #距离上一次长休息的时间较短就不休息
                print("just rest,not rest")
                return
        else:
            self.flag = "long"
            self.lastrestingtime = QTime.currentTime()
        if config[self.flag]["restset"]["beforesound"]:
            self.play_music(config[self.flag]["restset"]["beforesoundpath"],False,config[self.flag]["restset"]["beforesoundvol"])
        #全屏不休息
        if self.check_fullscreen():
            print("full screen,not rest")
            return
        #停止计时
        if self.sender() == self.shorttimer:
            short_hour = self.shortHour2.text() if self.shortHour2.text() != "" else "0" 
            short_min = self.shortMin2.text() if self.shortMin2.text() != "" else "0" 
            short_sec = self.shortSec2.text() if self.shortSec2.text() != "" else "0" 
            timeout = (int(short_hour)*3600+int(short_min)*60+int(short_sec))*1000
            self.restingtimer = self.shorttimer
        elif self.sender() == self.longtimer:
            long_hour = self.longHour2.text() if self.longHour2.text() != "" else "0" 
            long_min = self.longMin2.text() if self.longMin2.text() != "" else "0" 
            long_sec = self.longSec2.text() if self.longSec2.text() != "" else "0" 
            timeout = (int(long_hour)*3600+int(long_min)*60+int(long_sec))*1000
            self.restingtimer = self.longtimer
        print(timeout)
        self.resting = True
        self.restingtimer.stop()
        #展示界面
        #先截屏
        self.screen = QGuiApplication.primaryScreen()
        self.filename = os.getenv("temp")+"\\screen.jpg"
        print(self.filename)
        self.screen.grabWindow(0).save(self.filename,"jpg")
        time.sleep(1)
        '''
        self.rollwin.set_timer(self.restingtimer,self.flag)
        self.rollwin.show()
        self.rollwin.setCDText("还剩"+str(timeout//1000)+"秒,按Ctrl+D退出") #初始化
        #播放声音
        # if config[self.flag]["restset"]["insound"]:
            # print("play insound")
            # if os.path.splitext(config[self.flag]["restset"]["insoundpath"])[-1] in [".mp3",".wav",".wma",".flac"]:
                # print("prefix")
                # self.play_music(config[self.flag]["restset"]["insoundpath"],True,config[self.flag]["restset"]["insoundvol"]) 
        #启动终止休息计时器
        self.roll_timer = QTimer()
        self.roll_timer.timeout.connect(self.recover_roll)
        self.roll_timer.setSingleShot(True)
        self.roll_timer.start(timeout)
        #轮播图片
        self.update_roll_cd_timer = QTimer()
        self.update_roll_cd_timer.timeout.connect(self.update_roll_cd)
        self.update_roll_cd_timer.start(10000)
    #播放音乐
    def play_music(self,music,loop = True,volume = 20):
        self.player =QMediaPlayer()
        print("music："+music)
        self.playlist = QMediaPlaylist()
        if loop:
            self.playlist.setPlaybackMode(QMediaPlaylist.Loop)
        self.playlist.addMedia(QMediaContent(QUrl.fromLocalFile(music)))
        self.player.setPlaylist(self.playlist)
        print(config["short"]["restset"]["beforesoundvol"])
        print("volume:"+str(volume))
        self.player.setVolume(volume)
        if loop:
            self.player.play()
        else:
            self.player.play()
            time.sleep(2)
    #休息结束
    def recover_pop(self):
        self.pop_timer.stop()
        self.popup.close()
        self.player.stop()
        self.transwin.hide()
        self.restingtimer.start()
        self.resting = False
        print("end")
    def recover_roll(self,timer = None):
        self.roll_timer.stop()
        self.player.stop()
        self.rollwin.hide()
        if timer != None:
            timer.start()
        else:
            self.restingtimer.start()
        self.resting = False
        print("end")
    #休息设置
    def showRestSetShort(self):
        self.restset = RestSet(self,"short")
        self.restset.show()

    def showRestSetLong(self):
        self.restset = RestSet(self,"long")
        self.restset.show()
    #更新倒计时
    def update_countdown(self):
        if self.shorttimer.isActive():
            short_countdown = self.shorttimer.remainingTime()
            self.short_cd_label2.setText(str(short_countdown//1000//3600)+":"+str(short_countdown//1000%3600//60)+":"+str(short_countdown//1000%60))
        if self.longtimer.isActive():
            long_countdown = self.longtimer.remainingTime()
            self.long_cd_label2.setText(str(long_countdown//1000//3600)+":"+str(long_countdown//1000%3600//60)+":"+str(long_countdown//1000%60))
    #更新tooltips
    def update_tooltips(self):
        tooltips = ""
        if self.shorttimer.isActive():
            short_countdown = self.shorttimer.remainingTime()
            # self.short_cd_label2.setText(str(short_countdown//1000//3600)+":"+str(short_countdown//1000%3600//60)+":"+str(short_countdown//1000%60))
            tooltips += "短休息:"+str(short_countdown//1000//3600)+"时"+str(short_countdown//1000%3600//60)+"分\n"
        if self.longtimer.isActive():
            long_countdown = self.longtimer.remainingTime()
            # self.long_cd_label2.setText(str(long_countdown//1000//3600)+":"+str(long_countdown//1000%3600//60)+":"+str(long_countdown//1000%60))
            tooltips += "长休息:"+str(long_countdown//1000//3600)+"时"+str(long_countdown//1000%3600//60)+"分"

        self.trayIcon.setToolTip(tooltips)
        

    #休息时更新倒计时
    def update_pop_cd(self):
        cd = self.pop_timer.remainingTime()
        self.popup.setText("正在休息中。。。(还剩"+str(cd//1000)+"秒)")

    def update_roll_cd(self):
        cd = self.roll_timer.remainingTime()
        if cd >= 0:
            self.rollwin.setCDText("还剩"+str(cd//1000)+"秒,按Ctrl+D退出")
        self.rollwin.update()
    #检查全屏
    def check_fullscreen(self):
        fg_win = win32gui.GetForegroundWindow()
        print(fg_win)
        title = win32gui.GetWindowText(fg_win)
        print(title)
        # pid = wintypes.DWORD()
        # tid = ctypes.windll.user32.GetWindowThreadProcessId(fg_win, ctypes.byref(pid))
        # print(tid,pid)
        if title == "":
            print("desktop")
            return False
        rect = win32gui.GetWindowRect(fg_win)
        print(rect)
        screen = QGuiApplication.primaryScreen()
        rect2 = screen.geometry()
        print(rect2)
        print(rect[2] ,rect2.width(),rect[3],rect2.height())
        if rect[2] == rect2.width() and rect[3] == rect2.height():
            return True
        else:
            return False
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
        config["long"]["itvHour"] = self.longHour.text() if self.longHour.text() != "" else "0" 
        config["long"]["itvMin"] = self.longMin.text() if self.longMin.text() != "" else "0" 
        config["long"]["itvSec"] = self.longSec.text() if self.longSec.text() != "" else "0" 
        config["long"]["conHour"] = self.longHour2.text() if self.longHour2.text() != "" else "0" 
        config["long"]["conMin"] = self.longMin2.text() if self.longMin2.text() != "" else "0" 
        config["long"]["conSec"] = self.longSec2.text() if self.longSec2.text() != "" else "0" 
        Config.save()
        # with open(configfile,"w") as f:
        #     f.write(json.dumps(config,indent=4))

    def closeEvent(self,e):
        self.save_config()
        self.hide()
        e.ignore()

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
        inOpenSoundbtn = QPushButton("打开...")
        inOpenSoundbtn.setMaximumWidth(60)
        inOpenSoundbtn.clicked.connect(self.in_open_sound)
        self.inVolbtn = QPushButton("音量")
        self.inVolbtn.setMaximumWidth(40)
        self.inVolbtn.clicked.connect(self.in_open_vol)
        in_hbox = QHBoxLayout()
        in_hbox.addWidget(self.inSoundCheck)
        in_hbox.addWidget(self.inSoundEdit)
        in_hbox.addWidget(inOpenSoundbtn)
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
        dirname = QFileDialog.getExistingDirectory()
        if dirname != "":
            self.picEdit.setText(dirname)

    def before_open_sound(self):
        name = QFileDialog.getOpenFileName(None,None,None,"*.mp3 *.wav *.wma")
        print("name:"+str(name[0]))
        if name[0] != "":
            self.beforeSoundEdit.setText(name[0])    

    def in_open_sound(self):
        name = QFileDialog.getOpenFileName(None,None,None,"*.mp3 *.wav *.wma *.flac")
        print("name:"+str(name[0]))
        if name[0] != "":
            self.inSoundEdit.setText(name[0])           

    def before_open_vol(self):
        if self.beforeVol.isHidden():
            print(self.geometry().x(),self.geometry().y())
            print(self.sound_gb.x(),self.sound_gb.y())
            print(self.beforeVolbtn.x(),self.beforeVolbtn.y())
            self.beforeVol.setGeometry(self.geometry().x()+self.sound_gb.x()+self.beforeVolbtn.x(),self.geometry().y()+self.sound_gb.y()+self.beforeVolbtn.y()-50,120,50)
            self.beforeVol.show()
        else:
            self.beforeVol.hide()

    def in_open_vol(self):
        if self.inVol.isHidden():
            print(self.geometry().x(),self.geometry().y())
            print(self.sound_gb.x(),self.sound_gb.y())
            print(self.inVolbtn.x(),self.inVolbtn.y())
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
        print(value)
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
        self.setGeometry(rect.x()+50,rect.y()+50,200,100)
        self.autorun = QCheckBox("开机启动")
        self.autorun.stateChanged.connect(self.setAutorun)
        settings = QSettings("HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run",QSettings.NativeFormat)
        print("allkeys:"+str(settings.allKeys()))
        if os.path.splitext(os.path.basename(__file__))[0] in settings.allKeys():
            self.autorun.setChecked(True)
        else:
            self.autorun.setChecked(False)
        hbox = QHBoxLayout()
        hbox.addWidget(self.autorun)
        self.setLayout(hbox)

    def setAutorun(self,state):
        'HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run'
        settings = QSettings("HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run",QSettings.NativeFormat)
        if state == Qt.Checked:
            settings.setValue(os.path.splitext(os.path.basename(__file__))[0], os.path.abspath(__file__))
        elif state == Qt.Unchecked:
            settings.remove(os.path.splitext(os.path.basename(__file__))[0])

#锁定屏幕窗口
class TransWin(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint)
        # self.setAttribute(Qt.WA_TranslucentBackground)
        self.screen = QGuiApplication.primaryScreen()
        self.filename = os.getenv("temp")+"\\screen.jpg"
        print(self.filename)
        self.rect = self.screen.geometry()
        self.setGeometry(self.rect)

    def paintEvent(self,e):
        painter = QPainter(self)
        print("paintevent")
        # self.screen.grabWindow(0).save(self.filename,"jpg")
        # time.sleep(1)
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
        self.cdlabel = QLabel("按Ctrl+D退出")
        hbox.addWidget(self.cdlabel)
        QShortcut(QKeySequence("Ctrl+D"),self).activated.connect(self.recover)
        hbox.setAlignment(Qt.AlignHCenter|Qt.AlignTop)
        self.setLayout(hbox)
        self.rect = screen.geometry()
        self.setGeometry(self.rect)

    def paintEvent(self,e):
        painter = QPainter(self)
        print("paintevent")
        if len(self.filelist) == 0:
            path = os.getenv("temp")+"\\screen.jpg"
            # screen = QGuiApplication.primaryScreen()
            # screen.grabWindow(0).save(path,"jpg")  
        else:  
            path = self.filelist[random.randint(0,len(self.filelist)-1)]
        print(path)
        sec = str(random.randint(0,1000))
        painter.drawPixmap(self.rect,QPixmap(path))

    def setCDText(self,text):
        self.cdlabel.setText(text)

    def set_timer(self,timer,flag):
        self.timer = timer
        self.filelist = []
        tmplist = []
        picdir = config[flag]["restset"]["uipic"]
        tmplist = os.listdir(picdir)  
        for file in tmplist:
            path = os.path.join(picdir, file)
            if os.path.isdir(path):
                continue
            if os.path.splitext(file)[-1] in [".jpg",".jpeg",".png",".bmp"]:
                self.filelist.append(path)

    def recover(self):
        self.par.recover_roll(self.timer)

if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    ex = RemainderMain()
    sys.exit(app.exec_())