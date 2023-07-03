import os
import re
# from PyQt5.QtWidgets import *
# from PyQt5.QtCore import *
from PyQt5.QtWidgets import QWidget,QTableWidget,QTableWidgetItem,QAbstractItemView,QComboBox,QHBoxLayout,QVBoxLayout,QLineEdit,QLabel,QPushButton,QCheckBox,QApplication,QFileDialog,QMessageBox,QCalendarWidget
from PyQt5.QtCore import QTimer,QTime,QDate,QDateTime,Qt
from PyQt5.QtGui import QCursor
from config import Config
import mytimer
from log import log


class Schedule(QWidget):
    def __init__(self,par):
        super().__init__()
        self.par = par
        self.setWindowTitle("定时程序")
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setColumnWidth(0,60)
        self.table.setColumnWidth(1,50)
        self.table.setColumnWidth(2,163)
        self.table.setColumnWidth(3,50)
        self.table.setColumnWidth(4,145)
        self.table.setColumnWidth(5,120)
        #配置文件依次是：0动作、1时间、2重复、3状态、4内容、5上次执行/提醒时间、6下次执行时间。其中上次执行时间不在界面显示
        for i in range(len(Config.config["schedule"])):
            self.table.insertRow(i)
            self.table.setItem(i,0,QTableWidgetItem(Config.config["schedule"][i][0]))
            self.table.setItem(i,1,QTableWidgetItem(Config.config["schedule"][i][1]))
            self.table.setItem(i,2,QTableWidgetItem(Config.config["schedule"][i][2]))
            self.table.setItem(i,3,QTableWidgetItem(Config.config["schedule"][i][3]))
            self.table.setItem(i,4,QTableWidgetItem(Config.config["schedule"][i][4]))
            # if len(Config.config["schedule"][i]) >= 7:
            self.table.setItem(i,5,QTableWidgetItem(Config.config["schedule"][i][6]))
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setHorizontalHeaderLabels(["动作","时间","重复","状态","内容","下次执行时间"])
        self.table.doubleClicked.connect(self.edit)
        # self.table.resizeColumnsToContents()
        operate_hbox = QHBoxLayout()
        add_btn = QPushButton("新增..")
        add_btn.clicked.connect(self.add)
        edit_btn = QPushButton("编辑..")
        edit_btn.clicked.connect(self.edit)
        del_btn = QPushButton("删除")
        del_btn.clicked.connect(self.delete)
        ca_btn = QPushButton("查看日历...")
        ca_btn.clicked.connect(self.check_cal)
        operate_hbox.addWidget(add_btn)
        operate_hbox.addWidget(edit_btn)
        operate_hbox.addWidget(del_btn)
        operate_hbox.addWidget(ca_btn)
        self.startbtn = QPushButton("启动")
        self.startbtn.clicked.connect(self.start)  
        self.stopbtn = QPushButton("停止")
        self.stopbtn.clicked.connect(self.stop)  
        start_hbox = QHBoxLayout()
        start_hbox.addWidget(self.startbtn)
        start_hbox.addWidget(self.stopbtn)

        self.vbox = QVBoxLayout()
        self.vbox.addWidget(self.table)
        self.vbox.addLayout(operate_hbox)
        self.vbox.addLayout(start_hbox)
        self.setLayout(self.vbox)

        rect = par.geometry()
        self.setGeometry(rect.x(), rect.y(), 651, 300)#长度比表格长63就没有滚动条

    def add(self):
        self.add = Add(self)
        self.add.show()

    def edit(self):
        log("in edit")
        items = self.table.selectedItems()
        if len(items) == 0:
            return
        self.add = Add(self,True)
        self.add.show()

    def delete(self):
        row = self.table.currentRow()
        log(row)
        self.table.removeRow(row)
        Config.config["schedule"].remove(Config.config["schedule"][row])
        
    def check_cal(self):
        self.ca = Calender(self)
        self.ca.show()

    def closeEvent(self,e):
        # log(Config.config)
        Config.save()
       # self.start()

    def start(self):
        log("in start")
        QApplication.setQuitOnLastWindowClosed(False) #防止主程序最小化时，关闭弹框会导致程序退出
        diff = 86400000 + QTime.currentTime().msecsTo(QTime(0,1,0))#0点的时候重置一下计时器
        log(diff)
        QTimer.singleShot(diff,self.start) 
        self.msgbox = []   #所有弹框存起来，否则会被顶掉
        self.schedule_timer = []
        for row in range(len(Config.config["schedule"])):
            s = Config.config["schedule"][row]
            log(str(s))
            if s[3] == "禁用" or s[3] == "已过期":
                continue
            #过期提醒和更新下次执行时间
            nexttime = QDateTime.fromString(s[6],"yyyy-MM-dd hh:mm")
            print("###############",nexttime)
            if s[6] != "" and nexttime < QDateTime.currentDateTime():#已经过了下次时间则表明已过期
                if s[0] != "关机" and s[0] != "免打扰" and "小时" not in s[2]: #关机/免打扰/小时不提醒;
                    message = s[0]+":"+s[4]+"\n"+"时间:"+s[1]+"\n"+"重复:"+s[2]
                    log("以下日程已过期:"+message.replace("\n","   "))
                    msg = QMessageBox(QMessageBox.Information,"以下日程已过期",message)
                    msg.setWindowFlags(msg.windowFlags()|Qt.WindowStaysOnTopHint)
                    msg.open()
                    self.msgbox.append(msg)
                s[5] = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss") #更新提醒时间
                nexttime = self.updateNext(s) #更新下次时间
                s[6] = nexttime
                self.table.setItem(row,5,QTableWidgetItem(nexttime))
                Config.save()
            #启动计时器
            diff = -1
            if "小时" not in s[2]:
                if s[6].split(" ")[0] == QDateTime.currentDateTime().toString("yyyy-MM-dd"): #到了执行日期
                    diff = QTime.currentTime().msecsTo(QTime.fromString(s[1],"hh:mm"))
            else: #小时的单独计算
                settime = QTime.fromString(s[1],"hh:mm")
                curtime = QTime.currentTime()
                log(f'settime:{settime},curtime:{curtime}')
                diff = curtime.msecsTo(settime)
                if diff < 0: #如果已经过了指定时间，那么到了指定的分钟就执行
                    settime_secs = settime.minute()*60+settime.second()
                    curtime_secs = curtime.minute()*60+curtime.second()
                    log(f'settime_secs:{settime_secs},curtime_secs:{curtime_secs}')
                    if settime_secs > curtime_secs:
                        diff = (settime_secs - curtime_secs)*1000
                    else: #分钟数已过，延后1小时
                        diff = (settime_secs - curtime_secs + 3600)*1000
                #更新下次时间
                nexttime = QDateTime.currentDateTime().addMSecs(diff).toString("yyyy-MM-dd hh:mm")
                s[6] = nexttime
                self.table.setItem(row,5,QTableWidgetItem(nexttime))
                Config.save()                        
            log("diff:"+str(diff))
            if diff > 0:
                timer = mytimer.mytimer(s)
                self.schedule_timer.append(timer)
                timer.setSingleShot(True)
                timer.timeout.connect(self.schedule_ontimer)
                timer.start(diff+500) #有时候会早了一点点，这里延迟500ms  

        self.startbtn.setDisabled(True) 
        self.stopbtn.setDisabled(False) 
        
    def updateNext(self,s):
        if "小时" in s[2]:
            return "" #小时的单独设置
        if s[2].find("仅一次") == 0: #仅一次
            should_time = QDateTime.fromString(s[2].lstrip("仅一次:")+ " " + s[1] ,"yyyy/MM/dd hh:mm")
            if QDateTime.currentDateTime() > should_time: #过期了
                should_time = ""
        elif s[2] == "每天":
            should_time = QDateTime.fromString(QDateTime.currentDateTime().toString("yyyy-MM-dd ")+ s[1],"yyyy-MM-dd hh:mm")
            log(should_time)
            log(QDateTime.currentDateTime())
            if should_time < QDateTime.currentDateTime():
                should_time = should_time.addDays(1)
        elif s[2].find("每周") == 0: 
            week_enum = {"周一":1,"周二":2,"周三":3,"周四":4,"周五":5,"周六":6,"周日":7,}        
            today = QDateTime.currentDateTime().toString("ddd")
            week_list = s[2].strip().lstrip("每").split(" ")
            # log(week_list)
            i = 0
            while i < len(week_list): #找出后面最近的一天
                dt = QDateTime.currentDateTime().addDays(week_enum[week_list[i]]-week_enum[today])#该天日期
                log(dt)
                dt = QDateTime.fromString(f'{dt.toString("yyyy-MM-dd")} {s[1]}',"yyyy-MM-dd hh:mm") #具体时间
                log(dt)
                if dt>QDateTime.currentDateTime():
                    break
                i += 1
            if i >= len(week_list): #所有日期都比当前时间小，到下一周了，取第一个
                tmpdt = QDateTime.currentDateTime().addDays(week_enum[week_list[0]]-week_enum[today]).addDays(7)#该天日期
                should_time = QDateTime.fromString(f'{tmpdt.toString("yyyy-MM-dd")} {s[1]}',"yyyy-MM-dd hh:mm")#具体时间
            else:
                should_time = dt
        elif s[2].find("每月") == 0:
            today = int(QDateTime.currentDateTime().toString("dd"))
            date_list = s[2].strip("每月号").split(",")
            date_list = list(map(lambda x: int(x),date_list))
            date_list.sort()
            # log(date_list)
            i = 0
            while i < len(date_list): #找出后面最近的一天
                dt = QDateTime.currentDateTime().addDays(date_list[i]-today)#该天日期
                log(dt)
                dt = QDateTime.fromString(f'{dt.toString("yyyy-MM-dd")} {s[1]}',"yyyy-MM-dd hh:mm") #具体时间
                log(dt)
                if dt>QDateTime.currentDateTime():
                    break
                i += 1
            if i >= len(date_list): #所有日期都比当前时间小，到下个月了,取第一个
                tmpdt = QDateTime.currentDateTime().addDays(date_list[0]-today).addMonths(1)#该天日期
                should_time = QDateTime.fromString(f'{tmpdt.toString("yyyy-MM-dd")} {s[1]}',"yyyy-MM-dd hh:mm")#具体时间
            else:
                should_time = dt
        elif s[2].find("每年") == 0:
            moon = s[2].split("月")[0].strip("每年")
            date = s[2].split("月")[1].strip("日")
            time_str = f'{QDateTime.currentDateTime().toString("yyyy")}-{moon}-{date} {s[1]}'
            log(time_str)
            should_time = QDateTime.fromString(time_str,"yyyy-MM-d hh:mm")
            if should_time < QDateTime.currentDateTime():
                should_time = should_time.addYears(1)
            # log(should_time)
        else:
            if s[2].find("月") != -1:
                obj = re.search(".*?(\d+)月(\d+)号\(首次(.*)\)",s[2])
                dt = QDateTime.fromString(f'{obj.group(3)} {s[1]}',"yyyy/MM/dd hh:mm")
                today = QDateTime.currentDateTime()
                log(dt)
                while  dt < today:
                    dt = dt.addMonths(int(obj.group(1)))
                    log(dt)
                should_time = dt
                # should_time = dt.addMonths(0-int(obj.group(1)))
            elif s[2].find("周") != -1:
                obj = re.search(".*?(\d+)周周(\d)\(首次(.*)\)",s[2])
                dt = QDateTime.fromString(f'{obj.group(3)} {s[1]}',"yyyy/MM/dd hh:mm")
                today = QDateTime.currentDateTime()
                while  dt < today:
                    dt = dt.addDays(int(obj.group(1))*7)
                    log(dt)
                should_time = dt
                # should_time = dt.addDays(0-int(obj.group(1))*7)
            elif s[2].find("天") != -1:
                obj = re.search(".*?(\d+)天\(首次(.*)\)",s[2])
                dt = QDateTime.fromString(f'{obj.group(2)} {s[1]}',"yyyy/MM/dd hh:mm")
                today = QDateTime.currentDateTime()
                while  dt < today:
                    dt = dt.addDays(int(obj.group(1)))
                    log(dt)
                should_time = dt
                # should_time = dt.addDays(0-int(obj.group(1)))
        log(f"下次应该执行时间:{should_time}")
        if should_time != "":
            return should_time.toString("yyyy-MM-dd hh:mm")
        else:
            return ""
            
    def stop(self):
        self.schedule_timer = []
        self.startbtn.setDisabled(False) 
        self.stopbtn.setDisabled(True) 

    def schedule_ontimer(self):
        timer = self.sender()
        # log(timer)
        if self.par.resting:
            new_timer = mytimer.mytimer(timer.args)
            self.schedule_timer.append(new_timer)
            new_timer.setSingleShot(True)
            new_timer.timeout.connect(self.schedule_ontimer)
            new_timer.start(self.par.rest_timer.remainingTime()+1000)   
            return
        s = timer.args
        log("执行事件:"+str(s))
        if s[0] == "提醒":
            # msg = QMessageBox(QMessageBox.Information,"提醒",s[4])
            # msg.setWindowFlags(msg.windowFlags()|Qt.WindowStaysOnTopHint)
            # msg.open()
            # self.msgbox.append(msg)            
            
            # self.popup = QMessageBox(QMessageBox.Information,"提醒",s[4])
            # self.popup.setWindowTitle("提醒")
            # self.popup.setText("<font color=blue size=20>"+s[4]+"</font>")
            # okbtn = QPushButton("确定")
            # self.popup.addButton(okbtn,QMessageBox.AcceptRole)
            # delaybtn = QPushButton("10分钟后提醒")
            # delaybtn.setObjectName("|".join(s)) #用来传参
            # self.popup.addButton(delaybtn,QMessageBox.AcceptRole)
            # delaybtn.clicked.connect(self.delay)
            # self.popup.setWindowFlags(Qt.WindowStaysOnTopHint|Qt.WindowMaximizeButtonHint | Qt.MSWindowsFixedSizeDialogHint)
            # self.popup.open()
            popup = QMessageBox(QMessageBox.Information,"提醒",s[4])
            popup.setWindowTitle("提醒")
            popup.setText("<font color=blue size=20>"+s[4]+"</font>")
            okbtn = QPushButton("确定")
            popup.addButton(okbtn,QMessageBox.AcceptRole)
            delaybtn = QPushButton("10分钟后提醒")
            delaybtn.setObjectName("|".join(s)) #用来传参
            popup.addButton(delaybtn,QMessageBox.AcceptRole)
            delaybtn.clicked.connect(self.delay)
            popup.setWindowFlags(Qt.WindowStaysOnTopHint|Qt.WindowMaximizeButtonHint | Qt.MSWindowsFixedSizeDialogHint)
            popup.open()
            self.msgbox.append(popup)
        elif s[0] == "关机":
            os.popen("shutdown /s /t 60")
        elif s[0] == "执行程序":
            os.popen(s[4])
        elif s[0] == "免打扰":
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMute(1, None) 
            diff = QTime.currentTime().msecsTo(QTime.fromString(s[4].replace("结束时间:",""),"hh:mm"))
            log(diff)
            QTimer.singleShot(diff,self.setmute)
            
        itemlist = self.table.findItems(s[1],Qt.MatchExactly)
        foundrow = -1
        for i in itemlist: #更新提醒时间和下次时间
            log(i.text())
            row = self.table.row(i)
            log(f"{self.table.item(row,0).text()},{self.table.item(row,2).text()},{self.table.item(row,3).text()},{self.table.item(row,4).text()}")
            if s[0] == self.table.item(row,0).text()and s[2] == self.table.item(row,2).text()\
              and s[3] == self.table.item(row,3).text() and s[4] == self.table.item(row,4).text():
                log(f"found row:{row}")
                foundrow = row
                Config.config["schedule"][row][5] = QDateTime.currentDateTime().addSecs(10).toString("yyyy-MM-dd hh:mm:ss")#记录的时间会快一点，加10s
                nexttime = self.updateNext(Config.config["schedule"][row]) #更新下次时间
                Config.config["schedule"][row][6] = nexttime
                # log("here crash?")
                self.table.setItem(row,5,QTableWidgetItem(nexttime))
                # log("here crash2?")
                Config.save()
                # log("here crash3?")
                break
        if "小时" in s[2]:
            interval = 0        
            if s[2] == "每小时":
                interval = 3600
            elif re.match("每\d+.*小时",s[2]): #自定义小时
                if s[2].find("小时") != -1:
                    obj = re.search(".*?(\d+)小时",s[2])
                    interval += int(obj.group(1))*3600
                if s[2].find("分钟") != -1:
                    obj = re.search(".*?(\d+)分钟",s[2])
                    interval += int(obj.group(1))*60
            log(f'interval:{interval}')
            timer.start(interval*1000)
            #更新下次时间
            if foundrow != -1:
                nexttime = QDateTime.currentDateTime().addMSecs(interval*1000).toString("yyyy-MM-dd hh:mm")
                Config.config["schedule"][foundrow][6] = nexttime
                self.table.setItem(foundrow,5,QTableWidgetItem(nexttime))
                Config.save()
                
    def delay(self):
        btn = self.sender()
        log(btn.objectName())
        
        new_timer = mytimer.mytimer(btn.objectName().split("|"))
        self.schedule_timer.append(new_timer)
        new_timer.setSingleShot(True)
        new_timer.timeout.connect(self.schedule_ontimer)
        new_timer.start(10*60*1000)
            
    def setmute(self):
        log("关闭静音")
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMute(0, None) 
        
    def setdate(self,date):
        pass #empty function


class Add(QWidget):
    def __init__(self,par,editting = False):
        log(f"in add init,edit:{editting}")
        self.par = par
        self.editting =  editting
        super().__init__()
        if self.editting:
            self.setWindowTitle("编辑")
        else:
            self.setWindowTitle("新增")
        log(f"ui action")
        #动作
        action_hbox = QHBoxLayout()
        action_label = QLabel("动作:")
        action_label.setMaximumWidth(30)
        action_hbox.addWidget(action_label)
        self.action_combo = QComboBox()
        self.action_combo.addItems(["提醒","关机","执行程序","免打扰"])
        action_hbox.addWidget(self.action_combo)
        msg_hbox = QHBoxLayout()  #提醒
        msg_hbox.addWidget(QLabel("消息内容:"))
        self.msg_edit = QLineEdit()
        msg_hbox.addWidget(self.msg_edit)
        self.msg_wdiget = QWidget()
        self.msg_wdiget.setLayout(msg_hbox)
        exe_hbox = QHBoxLayout() #执行程序
        exe_hbox.addWidget(QLabel("程序:"))
        self.exe_edit = QLineEdit()
        exe_hbox.addWidget(self.exe_edit)
        exe_btn = QPushButton("选择程序")
        exe_btn.clicked.connect(self.open_exe)
        exe_hbox.addWidget(exe_btn)
        self.exe_wdiget = QWidget()
        self.exe_wdiget.setLayout(exe_hbox)
        self.exe_wdiget.hide()
        #重复
        log(f"ui repeat")
        repeat_hbox = QHBoxLayout()
        repeat_label = QLabel("重复:")
        repeat_label.setMaximumWidth(30)
        repeat_hbox.addWidget(repeat_label)
        log(f"ui repeat 1")
        self.repeat_combo = QComboBox()
        self.repeat_combo.addItems(["仅一次","每天","每周","每月","每年","每小时","自定义..."])
        repeat_hbox.addWidget(self.repeat_combo) 
        log(f"ui repeat 2")
        ##仅一次
        date_hbox = QHBoxLayout() 
        date_label = QLabel("日期:")
        date_label.setMaximumWidth(30)
        date_hbox.addWidget(date_label)
        log(f"ui repeat 3")
        self.year_combo = QComboBox() #年
        year = QDate.currentDate().year()
        self.year_combo.addItems(map(lambda x:str(x), list(range(year,year+5))))
        self.year_combo.setCurrentText(str(year))
        date_hbox.addWidget(self.year_combo)
        date_hbox.addWidget(QLabel("年"))
        self.month_combo = QComboBox() #月
        self.month_combo.addItems(map(lambda x:str(x), list(range(1,13))))
        self.month_combo.setCurrentText(str(QDate.currentDate().month()))
        date_hbox.addWidget(self.month_combo)
        date_hbox.addWidget(QLabel("月"))
        self.date_combo = QComboBox() #日
        self.date_combo.addItems(map(lambda x:str(x), list(range(1,32))))
        self.date_combo.setCurrentText(str(QDate.currentDate().day()))
        date_hbox.addWidget(self.date_combo)
        date_hbox.addWidget(QLabel("日"))
        log(f"ui repeat 4")
        self.date_wdiget = QWidget()
        self.date_wdiget.setLayout(date_hbox)
         ##每周
        self.Mon_checkbox = QCheckBox("周一")
        self.Tue_checkbox = QCheckBox("周二")
        self.Wed_checkbox = QCheckBox("周三")
        self.Thur_checkbox = QCheckBox("周四")
        self.Fri_checkbox = QCheckBox("周五")
        self.Sat_checkbox = QCheckBox("周六")
        self.Sun_checkbox = QCheckBox("周日")
        log(f"ui repeat 5")
        week_hbox = QHBoxLayout()
        week_hbox.addWidget(self.Mon_checkbox)
        week_hbox.addWidget(self.Tue_checkbox)
        week_hbox.addWidget(self.Wed_checkbox)
        week_hbox.addWidget(self.Thur_checkbox)
        week_hbox.addWidget(self.Fri_checkbox)
        week_hbox.addWidget(self.Sat_checkbox)
        week_hbox.addWidget(self.Sun_checkbox)
        self.week_wdiget = QWidget()
        self.week_wdiget.setLayout(week_hbox)
        self.week_wdiget.hide()
        log(f"ui repeat 6")
        ##每月
        moon_hbox = QHBoxLayout() 
        moon_hbox.addWidget(QLabel("每月"))
        self.moon_edit = QLineEdit()
        moon_hbox.addWidget(self.moon_edit)
        moon_hbox.addWidget(QLabel("号(多个用英文逗号,隔开)"))
        log(f"ui repeat 7")
        self.moon_wdiget = QWidget()
        self.moon_wdiget.setLayout(moon_hbox)
        self.moon_wdiget.hide()
        ##每年
        year_hbox = QHBoxLayout() 
        year_hbox.addWidget(QLabel("每年"))
        self.month_combo2 = QComboBox() #月
        self.month_combo2.addItems(map(lambda x:str(x), list(range(1,13))))
        self.month_combo2.setCurrentText(str(QDate.currentDate().month()))
        year_hbox.addWidget(self.month_combo2)
        year_hbox.addWidget(QLabel("月"))
        self.date_combo2 = QComboBox() #日
        self.date_combo2.addItems(map(lambda x:str(x), list(range(1,32))))
        self.date_combo2.setCurrentText(str(QDate.currentDate().day()))
        year_hbox.addWidget(self.date_combo2)
        year_hbox.addWidget(QLabel("日"))
        log(f"ui repeat 8")
        self.year_wdiget = QWidget()
        self.year_wdiget.setLayout(year_hbox)
        self.year_wdiget.hide()
        ##自定义
        custom_vbox = QVBoxLayout()
        custom_hbox = QHBoxLayout() 
        custom_hbox.addWidget(QLabel("间隔:每"))
        self.custom_edit = QLineEdit("3")
        self.custom_combo = QComboBox()
        self.custom_combo.addItems(["月","周","天","小时"])
        custom_hbox.addWidget(self.custom_edit)
        custom_hbox.addWidget(self.custom_combo)
        custom_moon_hbox = QHBoxLayout()#月
        self.custom_moon_combo =  QComboBox()
        self.custom_moon_combo.addItems(map(lambda x:str(x), list(range(1,32))))
        custom_moon_hbox.addWidget(self.custom_moon_combo)
        custom_moon_hbox.addWidget(QLabel("号"))
        self.custom_moon_widget = QWidget()
        self.custom_moon_widget.setLayout(custom_moon_hbox)
        custom_week_hbox = QHBoxLayout()#周
        self.custom_week_combo =  QComboBox()
        self.custom_week_combo.addItems(map(lambda x:str(x), list(range(1,8))))
        custom_week_hbox.addWidget(QLabel("周"))
        custom_week_hbox.addWidget(self.custom_week_combo)
        self.custom_week_widget = QWidget()
        self.custom_week_widget.setLayout(custom_week_hbox)
        self.custom_week_widget.hide()
        custom_hour_hbox = QHBoxLayout()#小时
        self.custom_hour_combo =  QComboBox()
        self.custom_hour_combo.addItems(map(lambda x:str(x), list(range(0,60))))
        custom_hour_hbox.addWidget(self.custom_hour_combo)
        custom_hour_hbox.addWidget(QLabel("分钟"))
        self.custom_hour_widget = QWidget()
        self.custom_hour_widget.setLayout(custom_hour_hbox)
        self.custom_hour_widget.hide()
        custom_hbox.addWidget(self.custom_moon_widget)
        custom_hbox.addWidget(self.custom_week_widget)
        custom_hbox.addWidget(self.custom_hour_widget)
        custom_vbox.addLayout(custom_hbox)
        custom_hbox2 = QHBoxLayout()
        log(f"ui repeat 9")
        custom_hbox2.addWidget(QLabel("首次执行日期:"))
        log(f"crash here?")
        self.custom_date_edit = QLineEdit(QDate.currentDate().toString('yyyy/MM/dd'))
        self.custom_select_btn = QPushButton("选择日期")
        self.custom_select_btn.clicked.connect(self.show_cal)
        '''
        # self.custom_date_edit = QDateEdit(QDate.currentDate()) #这里先用calendar，如果崩溃再改
        self.custom_date_edit = QDateEdit()
        log(f"crash here2?")
        # self.custom_date_edit.setDate(QDate.currentDate())
        self.custom_date_edit.setDateTime(QDateTime.currentDateTime())
        log(f"ui repeat 10")
        self.custom_date_edit.setCalendarPopup(True)
        log(f"ui repeat 11")
        # calendar = QCalendarWidget(self.custom_date_edit)
        # calendar = QCalendarWidget()
        # self.custom_date_edit.setCalendarWidget(calendar)
        '''
        custom_hbox2.addWidget(self.custom_date_edit)
        custom_hbox2.addWidget(self.custom_select_btn)
        log(f"ui repeat 12")
        self.custom_first_widget = QWidget()
        self.custom_first_widget.setLayout(custom_hbox2)
        custom_vbox.addWidget(self.custom_first_widget)
        self.custom_wdiget = QWidget()
        self.custom_wdiget.setLayout(custom_vbox)
        self.custom_wdiget.hide()
        #时间
        log(f"ui time")
        time_hbox = QHBoxLayout()
        time_label = QLabel("时间:") 
        time_label.setMaximumWidth(30)
        time_hbox.addWidget(time_label)
        self.hour_combo = QComboBox() #开始时间
        self.hour_combo.addItems(map(lambda x:str(x), list(range(24))))
        self.hour_combo.setCurrentText(str(QTime.currentTime().hour()))
        time_hbox.addWidget(self.hour_combo)
        time_hbox.addWidget(QLabel("时"))
        self.min_combo = QComboBox()
        self.min_combo.addItems(map(lambda x:str(x), list(range(60))))
        self.min_combo.setCurrentText(str(QTime.currentTime().minute()))
        time_hbox.addWidget(self.min_combo)
        time_hbox.addWidget(QLabel("分"))
        time_hbox2 = QHBoxLayout() #结束时间
        time_hbox2.addWidget(QLabel("至"))
        self.hour_combo2 = QComboBox()
        self.hour_combo2.addItems(map(lambda x:str(x), list(range(24))))
        self.hour_combo2.setCurrentText(str(QTime.currentTime().hour()))
        time_hbox2.addWidget(self.hour_combo2)
        time_hbox2.addWidget(QLabel("时"))
        self.min_combo2 = QComboBox()
        self.min_combo2.addItems(map(lambda x:str(x), list(range(60))))
        self.min_combo2.setCurrentText(str(QTime.currentTime().minute()))
        time_hbox2.addWidget(self.min_combo2)
        time_hbox2.addWidget(QLabel("分"))
        self.time_wdiget = QWidget()
        self.time_wdiget.setLayout(time_hbox2)
        self.time_wdiget.hide()
        time_hbox.addWidget(self.time_wdiget)
        #状态
        log(f"ui state")
        enable_hbox = QHBoxLayout()
        enable_label = QLabel("状态:")
        enable_label.setMaximumWidth(30)
        enable_hbox.addWidget(enable_label)
        self.enable_combo = QComboBox()
        self.enable_combo.addItems(["启用","禁用","已过期"])    
        enable_hbox.addWidget(self.enable_combo)  
        #按钮
        log(f"ui button")
        self.confirmbtn = QPushButton("确定")
        self.confirmbtn.clicked.connect(self.confirm)  
        self.canselbtn = QPushButton("取消")
        self.canselbtn.clicked.connect(self.cansel)  
        confirm_hbox = QHBoxLayout()
        confirm_hbox.addWidget(self.confirmbtn)
        confirm_hbox.addWidget(self.canselbtn)
        #外层layout
        log(f"ui layout")
        self.vbox = QVBoxLayout()
        self.vbox.addLayout(action_hbox)
        self.vbox.addWidget(self.msg_wdiget)
        self.vbox.addWidget(self.exe_wdiget)
        self.vbox.addLayout(repeat_hbox)
        self.vbox.addWidget(self.week_wdiget)
        self.vbox.addWidget(self.moon_wdiget)
        self.vbox.addWidget(self.date_wdiget)
        self.vbox.addWidget(self.year_wdiget)
        self.vbox.addWidget(self.custom_wdiget)
        self.vbox.addLayout(time_hbox)
        self.vbox.addLayout(enable_hbox)
        self.vbox.addLayout(confirm_hbox)
        self.setLayout(self.vbox)
        self.action_combo.currentTextChanged.connect(self.change_action)
        self.repeat_combo.currentTextChanged.connect(self.change_repeat)
        self.custom_combo.currentTextChanged.connect(self.change_custom)

        rect = par.geometry()
        self.setGeometry(rect.x(), rect.y(), 400, 150)
        log(f"ui done")
        
        if self.editting:  #编辑，要初始化
            table = self.par.table
            items = table.selectedItems()
            row = table.row(items[0])
            log(f"init action")
            action = table.item(row,0).text()
            self.action_combo.setCurrentText(action)
            if action == "提醒":
                self.msg_wdiget.show()
                self.exe_wdiget.hide()
                self.msg_edit.setText(table.item(row,4).text())
            elif action == "执行程序":
                self.msg_wdiget.hide()
                self.exe_wdiget.show()
                self.exe_edit.setText(table.item(row,4).text())
            elif action == "免打扰":
                self.time_wdiget.show()
                time2 = table.item(row,4).text().replace("结束时间:","")
                log(time2)
                hour2 = str(int(time2.split(":")[0])) #去0
                minute2 = str(int(time2.split(":")[1]))
                self.hour_combo2.setCurrentText(hour2)
                self.min_combo2.setCurrentText(minute2)
            else:
                self.msg_wdiget.hide()
                self.exe_wdiget.hide()
                
            log(f"init repeat")
            repeat = table.item(row,2).text()
            log(f'repeat:{repeat}')
            if repeat == "每天" or repeat == "每小时":
                self.repeat_combo.setCurrentText(repeat)
            elif repeat.find("每周") == 0:
                self.repeat_combo.setCurrentText("每周")
                self.week_wdiget.show()
                self.moon_wdiget.hide()
                self.custom_wdiget.hide()
                week_list = repeat.lstrip("每").split(" ")
                for i in week_list:
                    if i == "周一":
                        self.Mon_checkbox.setChecked(True)
                    elif i == "周二":
                        self.Tue_checkbox.setChecked(True)
                    elif i == "周三":
                        self.Wed_checkbox.setChecked(True)
                    elif i == "周四":
                        self.Thur_checkbox.setChecked(True)
                    elif i == "周五":
                        self.Fri_checkbox.setChecked(True)
                    elif i == "周六":
                        self.Sat_checkbox.setChecked(True)
                    elif i == "周日":
                        self.Sun_checkbox.setChecked(True)
            elif repeat.find("每月") == 0:
                self.repeat_combo.setCurrentText("每月")
                self.week_wdiget.hide()
                self.moon_wdiget.show()
                self.custom_wdiget.hide()
                self.moon_edit.setText(repeat.strip("每月号"))
            elif repeat.find("每年") == 0:
                self.repeat_combo.setCurrentText("每年")
                self.year_wdiget.show()
                self.month_combo2.setCurrentText(repeat.split("月")[0].strip("每年"))
                self.date_combo2.setCurrentText(repeat.split("月")[1].strip("日"))
            elif repeat.find("仅一次") == 0: #仅一次
                # dt = QDateTime.fromString(repeat.lstrip("仅一次:"),"yyyy/MM/dd")
                # log(dt.toString())
                # self.date_edit.setDateTime(dt)
                ymd = repeat.lstrip("仅一次:").split("/")
                log(ymd)
                self.year_combo.setCurrentText(ymd[0])
                self.month_combo.setCurrentText(ymd[1].lstrip("0"))
                self.date_combo.setCurrentText(ymd[2].lstrip("0"))
            else:
                self.repeat_combo.setCurrentText("自定义...")
                if repeat.find("月") != -1:
                    obj = re.search(".*?(\d+)月(\d+)号\(首次(.*)\)",repeat)
                    self.custom_edit.setText(obj.group(1))
                    self.custom_combo.setCurrentText("月")
                    self.custom_moon_combo.setCurrentText(obj.group(2))
                    # self.custom_date_edit.setDateTime(QDateTime.fromString(obj.group(3),"yyyy/MM/dd"))
                    self.custom_date_edit.setText(obj.group(3))
                elif repeat.find("周") != -1:
                    obj = re.search(".*?(\d+)周周(\d)\(首次(.*)\)",repeat)
                    self.custom_edit.setText(obj.group(1))
                    self.custom_combo.setCurrentText("周")
                    self.custom_week_combo.setCurrentText(obj.group(2))
                    # self.custom_date_edit.setDateTime(QDateTime.fromString(obj.group(3),"yyyy/MM/dd"))
                    self.custom_date_edit.setText(obj.group(3))
                elif repeat.find("天") != -1:
                    obj = re.search(".*?(\d+)天\(首次(.*)\)",repeat)
                    self.custom_edit.setText(obj.group(1))
                    self.custom_combo.setCurrentText("天")
                    # self.custom_date_edit.setDateTime(QDateTime.fromString(obj.group(2),"yyyy/MM/dd"))
                    self.custom_date_edit.setText(obj.group(2))
                elif repeat.find("小时") != -1:
                    obj = re.search(".*?(\d+)小时(\d+)分钟",repeat)
                    self.custom_edit.setText(obj.group(1))
                    self.custom_combo.setCurrentText("小时")
                    self.custom_hour_combo.setCurrentText(obj.group(2))
            log(f"init time")
            time =  table.item(row,1).text()
            log(time)
            hour = str(int(time.split(":")[0])) #去0
            minute = str(int(time.split(":")[1]))
            self.hour_combo.setCurrentText(hour)
            self.min_combo.setCurrentText(minute)
            self.enable_combo.setCurrentText(table.item(row,3).text())
            log(f"init done")

    def confirm(self):
        action = self.action_combo.currentText()
        repeat = ""
        repeat_text = self.repeat_combo.currentText()
        if repeat_text == "每周":
            repeat += "每"
            if self.Mon_checkbox.isChecked():
                repeat += "周一 "
            if self.Tue_checkbox.isChecked():
                repeat += "周二 "
            if self.Wed_checkbox.isChecked():
                repeat += "周三 "
            if self.Thur_checkbox.isChecked():
                repeat += "周四 "
            if self.Fri_checkbox.isChecked():
                repeat += "周五 "
            if self.Sat_checkbox.isChecked():
                repeat += "周六 "
            if self.Sun_checkbox.isChecked():
                repeat += "周日 "
            if repeat == "每": #没有勾选
                QMessageBox.information(None,"提示","请勾选每周几执行！")
                return
        elif repeat_text == "每月":
            repeat += "每月"
            moon = self.moon_edit.text()
            if moon != "":
                if re.match("^[\d,]+$",moon) is None:
                    QMessageBox.information(None,"提示","每月几号填写不正确！请注意是英文逗号隔开")
                    return
                date_list = moon.split(",")
                for i in date_list: #检查合法性
                    if int(i) < 1 or int(i) >31:
                        QMessageBox.information(None,"提示","每月几号日期不正确！")
                        return
                repeat += moon
                repeat += "号"
            else: #没有填日期
                QMessageBox.information(None,"提示","请填写每月几号执行！")
                return
        elif repeat_text == "每年":
            moon = self.month_combo2.currentText()
            date = self.date_combo2.currentText()
            repeat = f"每年{moon}月{date}日"
        elif repeat_text == "自定义...":
            count = self.custom_edit.text()
            # first = self.custom_date_edit.dateTime().toString("yyyy/MM/dd")
            first = self.custom_date_edit.text()
            if count != "" and first != "":
                custom = self.custom_combo.currentText()
                if custom == "月":
                    repeat = f"每{count}月{self.custom_moon_combo.currentText()}号(首次{first})"
                elif custom == "周":
                    repeat = f"每{count}周周{self.custom_week_combo.currentText()}(首次{first})"
                elif custom == "天":
                    repeat = f"每{count}天(首次{first})"
                elif custom == "小时":
                    repeat = f"每{count}小时{self.custom_hour_combo.currentText()}分钟"
            else: #没有填间隔
                QMessageBox.information(None,"提示","请填写间隔和首次执行时间！")
                return
        elif repeat_text == "仅一次":
            # repeat = "仅一次:"+self.date_edit.dateTime().toString("yyyy/MM/dd")
            dt =QDateTime.fromString(f"{self.year_combo.currentText()}/{self.month_combo.currentText()}/{self.date_combo.currentText()}","yyyy/M/d")
            log(dt)
            repeat = "仅一次:"+dt.toString("yyyy/MM/dd")
            # repeat = f"仅一次:{self.year_combo.currentText()}/{self.month_combo.currentText()}/{self.date_combo.currentText()}"
        else:
            repeat = repeat_text
        log(f'repeat:{repeat}')
                
        hour = self.hour_combo.currentText()
        if int(hour) < 10:
            hour = "0" + hour
        minitue = self.min_combo.currentText()
        if int(minitue) < 10:
            minitue = "0" + minitue
        time = hour+":" + minitue
        # time = self.dt_edit.dateTime().toString("hh:mm M/dd/yyyy")
                
        status = self.enable_combo.currentText()
        content = ""
        if action == "提醒":
            content = self.msg_edit.text()
            if content == "":
                QMessageBox.information(None,"提示","请填写消息内容！")
                return
        elif action == "执行程序":
            content = self.exe_edit.text()
            if content == "":
                QMessageBox.information(None,"提示","请填写程序路径！")
                return
        elif action == "免打扰":
            hour2 = self.hour_combo2.currentText()
            if int(hour2) < 10:
                hour2 = "0" + hour2
            minitue2 = self.min_combo2.currentText()
            if int(minitue2) < 10:
                minitue2 = "0" + minitue2
            time2 = hour2 + ":" + minitue2
            content = "结束时间:"+time2

        table = self.par.table
        if self.editting:
            items = table.selectedItems()
            row = table.row(items[0])
        else:
            row = table.rowCount()
            table.insertRow(row)
        #第6列是上一次执行时间，不在表格显示，只记录在配置文件
        if self.editting: 
            if time != Config.config["schedule"][row][1] or repeat != Config.config["schedule"][row][2]:#如果编辑了时间，则算执行了一次，并更新下次时间，否则保存不变
                exetime = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss") 
                nexttime = self.par.updateNext([action,time,repeat,status,content,exetime])
            else:
                exetime = Config.config["schedule"][row][5]
                nexttime = Config.config["schedule"][row][6]
            if Config.config["schedule"][row][3] == "禁用" and status == "启用": #禁用到启用，更新下次时间
                nexttime = self.par.updateNext([action,time,repeat,status,content,exetime])
            elif status == "禁用": #启用到禁用，下次时间置空
                nexttime = ""
            Config.config["schedule"][row] = [action,time,repeat,status,content,exetime,nexttime]
        else:#新增时算执行了一次，并更新下次时间
            exetime = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss") 
            nexttime = self.par.updateNext([action,time,repeat,status,content,exetime])
            Config.config["schedule"].append([action,time,repeat,status,content,exetime,nexttime])
            table.verticalScrollBar().setValue(table.verticalScrollBar().maximum())
        Config.save()
        table.setItem(row,0,QTableWidgetItem(action))
        table.setItem(row,1,QTableWidgetItem(time))
        table.setItem(row,2,QTableWidgetItem(repeat))
        table.setItem(row,3,QTableWidgetItem(status))
        table.setItem(row,4,QTableWidgetItem(content))
        table.setItem(row,5,QTableWidgetItem(nexttime))
        self.hide()
        # self.par.table.resizeColumnsToContents()
        self.par.start()

    def cansel(self):
        self.hide()

    def change_action(self):
        log("in change_action")
        text = self.action_combo.currentText()
        self.time_wdiget.hide()
        if text == "提醒":
            self.msg_wdiget.show()
            self.exe_wdiget.hide()
        elif text == "执行程序":
            self.msg_wdiget.hide()
            self.exe_wdiget.show()
        elif text == "免打扰":
            self.time_wdiget.show()
            self.msg_wdiget.hide()
            self.exe_wdiget.hide()
        else:
            self.msg_wdiget.hide()
            self.exe_wdiget.hide()
            
    def change_repeat(self):
        log("in change_repeat")
        text = self.repeat_combo.currentText()
        if text == "每周":
            self.week_wdiget.show()
            self.moon_wdiget.hide()
            self.custom_wdiget.hide()
            self.date_wdiget.hide()
            self.year_wdiget.hide()
        elif text == "每月":
            self.week_wdiget.hide()
            self.moon_wdiget.show()
            self.custom_wdiget.hide()
            self.date_wdiget.hide()
            self.year_wdiget.hide()
        elif text == "每年":
            self.week_wdiget.hide()
            self.moon_wdiget.hide()
            self.custom_wdiget.hide()
            self.date_wdiget.hide()
            self.year_wdiget.show()
        elif text == "自定义...":
            self.week_wdiget.hide()
            self.moon_wdiget.hide()
            self.custom_wdiget.show()
            self.date_wdiget.hide()
            self.year_wdiget.hide()
        elif text == "仅一次":
            self.week_wdiget.hide()
            self.moon_wdiget.hide()
            self.custom_wdiget.hide()
            self.date_wdiget.show()
            self.year_wdiget.hide()
        else:
            self.week_wdiget.hide()
            self.moon_wdiget.hide()
            self.custom_wdiget.hide()
            self.date_wdiget.hide()
            self.year_wdiget.hide()
            
    def change_custom(self):
        log("in change_custom")
        text = self.custom_combo.currentText()
        if text == "月":
            self.custom_moon_widget.show()
            self.custom_week_widget.hide()
            self.custom_hour_widget.hide()
            self.custom_first_widget.show()
        elif text == "周":
            self.custom_moon_widget.hide()
            self.custom_week_widget.show()
            self.custom_hour_widget.hide()
            self.custom_first_widget.show()
        elif text == "天":
            self.custom_moon_widget.hide()
            self.custom_week_widget.hide()
            self.custom_hour_widget.hide()
            self.custom_first_widget.show()
        elif text == "小时":
            self.custom_moon_widget.hide()
            self.custom_week_widget.hide()
            self.custom_hour_widget.show()
            self.custom_first_widget.hide()

    def open_exe(self):
        name = QFileDialog.getOpenFileName()
        log("name:"+str(name[0]))
        if name[0] != "":
            self.exe_edit.setText(name[0])  
            
    def show_cal(self):
        self.ca = Calender(self)
        self.ca.show()
    
    def setdate(self,date):
        self.custom_date_edit.setText(date.toString('yyyy/MM/dd'))


class Calender(QWidget):
    def __init__(self,par):
        super().__init__()
        cw = QCalendarWidget(self)
        cw.clicked.connect(par.setdate)
        # rect = par.geometry()
        # self.setGeometry(rect.x()+200, rect.y()+100, 250, 210)
        self.setGeometry(QCursor().pos().x(), QCursor().pos().y()-215, 250, 210)
        self.setWindowTitle("日历")
    
