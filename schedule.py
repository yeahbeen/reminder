import os
import re
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from config import Config
import mytimer
from log import log


class Schedule(QWidget):
    def __init__(self,par):
        super().__init__()
        self.setWindowTitle("定时程序")
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        # for i in range(self.table.columnCount()):
            # self.table.setColumnWidth(i,60)
        self.table.setColumnWidth(0,60)
        self.table.setColumnWidth(1,50)
        self.table.setColumnWidth(2,100)
        self.table.setColumnWidth(3,50)
        self.table.setColumnWidth(4,100)
        for i in range(len(Config.config["schedule"])):
            self.table.insertRow(i)
            self.table.setItem(i,0,QTableWidgetItem(Config.config["schedule"][i][0]))
            self.table.setItem(i,1,QTableWidgetItem(Config.config["schedule"][i][1]))
            self.table.setItem(i,2,QTableWidgetItem(Config.config["schedule"][i][2]))
            self.table.setItem(i,3,QTableWidgetItem(Config.config["schedule"][i][3]))
            self.table.setItem(i,4,QTableWidgetItem(Config.config["schedule"][i][4]))
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setHorizontalHeaderLabels(["动作","时间","重复","状态","内容"])
        self.table.doubleClicked.connect(self.edit)
        operate_hbox = QHBoxLayout()
        add_btn = QPushButton("新增..")
        add_btn.clicked.connect(self.add)
        edit_btn = QPushButton("编辑..")
        edit_btn.clicked.connect(self.edit)
        del_btn = QPushButton("删除")
        del_btn.clicked.connect(self.delete)
        operate_hbox.addWidget(add_btn)
        operate_hbox.addWidget(edit_btn)
        operate_hbox.addWidget(del_btn)
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
        self.setGeometry(rect.x(), rect.y(), 417, 300)


    def add(self):
        self.add = Add(self)
        self.add.show()

    def edit(self):
        log("in edit")
        items = self.table.selectedItems()
        log(str(items))
        if len(items) == 0:
            return
        self.add = Add(self,True)
        self.add.show()

    def delete(self):
        row = self.table.currentRow()
        log(row)
        self.table.removeRow(row)
        Config.config["schedule"].remove(Config.config["schedule"][row])

    def closeEvent(self,e):
        Config.save()
        self.start()

    def start(self):
        log("in start")
        QApplication.setQuitOnLastWindowClosed(False) #防止主程序最小化时，关闭弹框会导致程序退出
        diff = 86400000 + QTime.currentTime().msecsTo(QTime(0,1,0))
        log(diff)
        QTimer.singleShot(diff,self.start) #0点的时候重置一下计时器
        self.msgbox = []   #所有弹框存起来，否则会被顶掉
        self.schedule_timer = []
        for row in range(len(Config.config["schedule"])):
            s = Config.config["schedule"][row]
            log(str(s))
            if s[3] == "禁用" or s[3] == "已过期":
                continue
            # dt = QDateTime.fromString(s[1],"hh:mm M/dd/yyyy")
            # log("dt "+str(dt))
            #过期提醒
            if s[5] == "":  #为空表示是新增的，只提醒“仅一次”的，其他的不提醒
                if s[2] == "仅一次":
                    # nexttime = dt
                    nexttime = QDateTime.fromString(s[1]+" "+s[2],"hh:mm M/dd/yyyy")
                else:
                    # nexttime = dt.addYears(100)  
                    nexttime = QDateTime.currentDateTime().addYears(100)  
            else: #找出下一次应该执行的时间
                lasttime = QDateTime.fromString(s[5],"yyyy-MM-dd hh:mm:ss")
                log(lasttime)
                if s[2] == "每天":
                    nexttime = lasttime.addDays(1)
                elif s[2] == "每周":
                    nexttime = lasttime.addDays(7)
                elif s[2] == "每月":
                    nexttime = lasttime.addMonths(1)
                # elif s[2] == "仅一次":
                else: #每小时/自定义/仅一次不提醒
                    nexttime = lasttime.addYears(100)
                log(nexttime)
            if s[0] != "关机" and QDateTime.currentDateTime() > nexttime : #当前时间大于下一次的时间则表明已过期;关机不提醒;
                msg = QMessageBox(QMessageBox.Information,"以下日程已过期","内容:"+s[0]+" "+s[4]+"\n"+"时间:"+s[1]+"\n"+"重复:"+s[2])
                msg.setWindowFlags(msg.windowFlags()|Qt.WindowStaysOnTopHint)
                msg.open()
                self.msgbox.append(msg)
                # QMessageBox.information(None,"以下日程已过期","内容:"+s[0]+" "+s[4]+"\n"+"时间:"+s[1]+"\n"+"重复:"+s[2])
                #更新提醒时间
                while QDateTime.currentDateTime() > nexttime:  #防止时间比较长，一直提示，找出最近的一次
                    nexttime0 = nexttime
                    if s[2] == "每天":
                        nexttime = nexttime0.addDays(1)
                    elif s[2] == "每周":
                        nexttime = nexttime0.addDays(7)
                    elif s[2] == "每月":
                        nexttime = nexttime0.addMonths(1)
                    elif s[2] == "仅一次":
                        nexttime = nexttime0.addYears(100)
                    log(nexttime)
                s[5] = nexttime0.toString("yyyy-MM-dd hh:mm:ss")
            #启动计时器
            flag = False
            if s[2].find("每周") == 0:
                week_list = s[2].lstrip("每").split(" ")
                for i in week_list:
                    day = QDateTime.currentDateTime().toString("ddd")
                    log(i)
                    log(day)                
                    if i == day:
                        flag = True
                        break
            if s[2].find("每月") == 0:
                date_list = s[2].strip("每月号").split(",")
                for i in date_list:
                    # day1 = dt.toString("dd")
                    date = QDateTime.currentDateTime().toString("dd")
                    log(f'{i},{date}')
                    if i == date:
                        flag = True
                        break
                        
            if re.match("\d+/\d+/\d+",s[2]): #仅一次
                date = QDateTime.currentDateTime().toString("yyyy/MM/dd")
                log(f'date:{date}')
                if s[2] == date:
                    flag = True
                    
            if flag or s[2] == "每天": #到了指定日期则启动计时器
                diff = QTime.currentTime().msecsTo(QTime.fromString(s[1],"hh:mm"))
                log("diff:"+str(diff))
                if diff > 0:
                    timer = mytimer.mytimer(s)
                    self.schedule_timer.append(timer)
                    timer.setSingleShot(True)
                    timer.timeout.connect(self.schedule_ontimer)
                    timer.start(diff)   
            '''
            if re.match("每\d+.*",s[2]): #自定义
                interval = 0
                # if s[2].find("天") != -1:
                    # obj = re.search(".*?(\d+)天",s[2])
                    # interval += int(obj.group(1))*24*3600
                if s[2].find("小时") != -1:
                    obj = re.search(".*?(\d+)小时",s[2])
                    interval += int(obj.group(1))*3600
                if s[2].find("分钟") != -1:
                    obj = re.search(".*?(\d+)分钟",s[2])
                    interval += int(obj.group(1))*60
                # lasttime = QDateTime.fromString(s[5],"yyyy-MM-dd hh:mm:ss")
                # curtime = QDateTime.currentDateTime()
                # howlong = lasttime.secsTo(curtime)
                diff = QTime.currentTime().msecsTo(QTime.fromString(s[1],"hh:mm"))
                if diff <= 0:
                    diff = interval + diff
                log(f'diff:{diff}')
                timer = mytimer.mytimer(s)
                self.schedule_timer.append(timer)
                # timer.setSingleShot(True)
                timer.timeout.connect(self.schedule_ontimer)
                timer.start(diff*1000)  
                '''
            if s[2] == "每小时" or re.match("每\d+.*",s[2]):
                settime = QTime.fromString(s[1],"hh:mm")
                curtime = QTime.currentTime()
                log(f'settime:{settime},curtime:{curtime}')
                settime_secs = settime.minute()*60+settime.second()
                curtime_secs = curtime.minute()*60+curtime.second()
                log(f'settime_secs:{settime_secs},curtime_secs:{curtime_secs}')
                if settime_secs > curtime_secs:
                    diff = (settime_secs - curtime_secs)*1000
                else:
                    diff = (settime_secs - curtime_secs + 3600)*1000
                log("diff:"+str(diff))
                if diff > 0:
                    timer = mytimer.mytimer(s)
                    self.schedule_timer.append(timer)
                    # timer.setSingleShot(True)
                    timer.timeout.connect(self.schedule_ontimer)
                    timer.start(diff)   
            
        self.startbtn.setDisabled(True) 
        self.stopbtn.setDisabled(False) 

    def stop(self):
        self.schedule_timer = []
        self.startbtn.setDisabled(False) 
        self.stopbtn.setDisabled(True) 

    def schedule_ontimer(self):
        timer = self.sender()
        log(timer)
        s = timer.args
        log("执行事件:"+str(s))
        if s[0] == "提醒":
            msg = QMessageBox(QMessageBox.Information,"提醒",s[4])
            msg.setWindowFlags(msg.windowFlags()|Qt.WindowStaysOnTopHint)
            msg.open()
            self.msgbox.append(msg)
            # QMessageBox.information(None,"提醒",s[4])
        elif s[0] == "关机":
            os.popen("shutdown /s /t 60")
        elif s[0] == "执行程序":
            os.popen(s[4])
            
        itemlist = self.table.findItems(s[1],Qt.MatchExactly)
        for i in itemlist:
            log(i)
            row = self.table.row(i)
            if s[2] == "仅一次":
                self.table.setItem(row,3,QTableWidgetItem("已过期"))
                Config.config["schedule"][row][3] = "已过期"
            Config.config["schedule"][row][5] = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        Config.save()
        if s[2] == "每小时":
            timer.start(3600*1000)
        if re.match("每\d+.*",s[2]): #自定义
            interval = 0
            # if s[2].find("天") != -1:
                # obj = re.search(".*?(\d+)天",s[2])
                # interval += int(obj.group(1))*24*3600
            if s[2].find("小时") != -1:
                obj = re.search(".*?(\d+)小时",s[2])
                interval += int(obj.group(1))*3600
            if s[2].find("分钟") != -1:
                obj = re.search(".*?(\d+)分钟",s[2])
                interval += int(obj.group(1))*60
            log(f'interval:{interval}')
            timer.start(interval*1000)


class Add(QWidget):
    def __init__(self,par,editting = False):
        self.par = par
        self.editting =  editting
        super().__init__()
        if self.editting:
            self.setWindowTitle("编辑")
        else:
            self.setWindowTitle("新增")
            
        action_hbox = QHBoxLayout()
        action_label = QLabel("动作:")
        action_label.setMaximumWidth(30)
        action_hbox.addWidget(action_label)
        self.action_combo = QComboBox()
        self.action_combo.addItems(["提醒","关机","执行程序"])
        action_hbox.addWidget(self.action_combo)
        exe_hbox = QHBoxLayout()
        exe_hbox.addWidget(QLabel("程序:"))
        self.exe_edit = QLineEdit()
        exe_hbox.addWidget(self.exe_edit)
        exe_btn = QPushButton("选择程序")
        exe_btn.clicked.connect(self.open_exe)
        exe_hbox.addWidget(exe_btn)
        self.exe_wdiget = QWidget()
        self.exe_wdiget.setLayout(exe_hbox)
        self.exe_wdiget.hide()
        msg_hbox = QHBoxLayout()
        msg_hbox.addWidget(QLabel("消息内容:"))
        self.msg_edit = QLineEdit()
        msg_hbox.addWidget(self.msg_edit)
        self.msg_wdiget = QWidget()
        self.msg_wdiget.setLayout(msg_hbox)

        repeat_hbox = QHBoxLayout()
        repeat_label = QLabel("重复:")
        repeat_label.setMaximumWidth(30)
        repeat_hbox.addWidget(repeat_label)
        self.repeat_combo = QComboBox()
        self.repeat_combo.addItems(["仅一次","每天","每周","每月","每小时","自定义小时数"])
        
        repeat_hbox.addWidget(self.repeat_combo) 
        self.Mon_checkbox = QCheckBox("周一")
        self.Tue_checkbox = QCheckBox("周二")
        self.Wed_checkbox = QCheckBox("周三")
        self.Thur_checkbox = QCheckBox("周四")
        self.Fri_checkbox = QCheckBox("周五")
        self.Sat_checkbox = QCheckBox("周六")
        self.Sun_checkbox = QCheckBox("周日")
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
        moon_hbox = QHBoxLayout()
        moon_hbox.addWidget(QLabel("每月"))
        self.moon_edit = QLineEdit()
        moon_hbox.addWidget(self.moon_edit)
        moon_hbox.addWidget(QLabel("号(多个用英文逗号,隔开)"))
        self.moon_wdiget = QWidget()
        self.moon_wdiget.setLayout(moon_hbox)
        self.moon_wdiget.hide()
        custom_hbox = QHBoxLayout()
        custom_hbox.addWidget(QLabel("每"))
        # self.day_edit = QLineEdit("0")
        # custom_hbox.addWidget(self.day_edit)
        # custom_hbox.addWidget(QLabel("天"))
        self.hour_edit = QLineEdit("0")
        custom_hbox.addWidget(self.hour_edit)
        custom_hbox.addWidget(QLabel("小时"))
        self.min_edit = QLineEdit("0")
        custom_hbox.addWidget(self.min_edit)
        custom_hbox.addWidget(QLabel("分钟"))
        self.custom_wdiget = QWidget()
        self.custom_wdiget.setLayout(custom_hbox)
        self.custom_wdiget.hide()
        
        date_hbox = QHBoxLayout()
        date_label = QLabel("日期:")
        date_label.setMaximumWidth(30)
        date_hbox.addWidget(date_label)
        calendar = QCalendarWidget()
        # self.date_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setCalendarWidget(calendar)
        date_hbox.addWidget(self.date_edit)
        self.date_wdiget = QWidget()
        self.date_wdiget.setLayout(date_hbox)
        # self.date_wdiget.hide()
        
        time_hbox = QHBoxLayout()
        time_label = QLabel("时间:")
        time_label.setMaximumWidth(30)
        time_hbox.addWidget(time_label)
        self.hour_combo = QComboBox()
        self.hour_combo.addItems(map(lambda x:str(x), list(range(24))))
        self.hour_combo.setCurrentText(str(QTime.currentTime().hour()))
        time_hbox.addWidget(self.hour_combo)
        time_hbox.addWidget(QLabel("时"))
        self.min_combo = QComboBox()
        self.min_combo.addItems(map(lambda x:str(x), list(range(60))))
        self.min_combo.setCurrentText(str(QTime.currentTime().minute()))
        time_hbox.addWidget(self.min_combo)
        time_hbox.addWidget(QLabel("分"))
        
        enable_hbox = QHBoxLayout()
        enable_label = QLabel("状态:")
        enable_label.setMaximumWidth(30)
        enable_hbox.addWidget(enable_label)
        self.enable_combo = QComboBox()
        self.enable_combo.addItems(["启用","禁用","已过期"])    
        enable_hbox.addWidget(self.enable_combo)  
        
        self.confirmbtn = QPushButton("确定")
        self.confirmbtn.clicked.connect(self.confirm)  
        self.canselbtn = QPushButton("取消")
        self.canselbtn.clicked.connect(self.cansel)  
        confirm_hbox = QHBoxLayout()
        confirm_hbox.addWidget(self.confirmbtn)
        confirm_hbox.addWidget(self.canselbtn)

        self.vbox = QVBoxLayout()
        self.vbox.addLayout(action_hbox)
        self.vbox.addWidget(self.msg_wdiget)
        self.vbox.addWidget(self.exe_wdiget)
        self.vbox.addLayout(repeat_hbox)
        self.vbox.addWidget(self.week_wdiget)
        self.vbox.addWidget(self.moon_wdiget)
        self.vbox.addWidget(self.date_wdiget)
        self.vbox.addWidget(self.custom_wdiget)
        self.vbox.addLayout(time_hbox)
        
        self.vbox.addLayout(enable_hbox)
        self.vbox.addLayout(confirm_hbox)
        self.setLayout(self.vbox)
        self.action_combo.currentTextChanged.connect(self.change_action)
        self.repeat_combo.currentTextChanged.connect(self.change_repeat)

        rect = par.geometry()
        self.setGeometry(rect.x(), rect.y(), 400, 150)
        
        if self.editting:
            table = self.par.table
            items = table.selectedItems()
            row = table.row(items[0])
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
            else:
                self.msg_wdiget.hide()
                self.exe_wdiget.hide()
                
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
            elif re.match("\d+/\d+/\d+",repeat): #仅一次
                dt = QDateTime.fromString(repeat,"yyyy/MM/dd")
                log(dt.toString())
                self.date_edit.setDateTime(dt)
            else:
                self.repeat_combo.setCurrentText("自定义小时数")
                self.week_wdiget.hide()
                self.moon_wdiget.hide()
                self.custom_wdiget.show()
                # if repeat.find("天") != -1:
                    # obj = re.search(".*?(\d+)天",repeat)
                    # self.day_edit.setText(obj.group(1))
                if repeat.find("小时") != -1:
                    obj = re.search(".*?(\d+)小时",repeat)
                    self.hour_edit.setText(obj.group(1))
                if repeat.find("分钟") != -1:
                    obj = re.search(".*?(\d+)分钟",repeat)
                    self.min_edit.setText(obj.group(1))
                    
            time =  table.item(row,1).text()
            log(time)
            hour = str(int(time.split(":")[0])) #去0
            minute = str(int(time.split(":")[1]))
            self.hour_combo.setCurrentText(hour)
            self.min_combo.setCurrentText(minute)
            # dt = QDateTime.fromString(table.item(row,1).text(),"hh:mm M/dd/yyyy")
            # log(dt.toString())
            # self.dt_edit.setDateTime(QDateTime.fromString(table.item(row,1).text(),"hh:mm M/dd/yyyy"))
            
            self.enable_combo.setCurrentText(table.item(row,3).text())


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
        elif repeat_text == "自定义小时数":
            repeat += "每"
            # if self.day_edit.text() != "0" and self.day_edit.text() != "":
                # repeat += self.day_edit.text()
                # repeat += "天"
            if self.hour_edit.text() != "0" and self.hour_edit.text() != "":
                repeat += self.hour_edit.text()
                repeat += "小时"
            if self.min_edit.text() != "0" and self.min_edit.text() != "":
                repeat += self.min_edit.text()
                repeat += "分钟"
            if repeat == "每": #没有填写
                QMessageBox.information(None,"提示","请填写每隔多长时间执行！")
                return
        elif repeat_text == "仅一次":
            repeat = self.date_edit.dateTime().toString("yyyy/MM/dd")
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
                
        table = self.par.table
        if self.editting:
            items = table.selectedItems()
            row = table.row(items[0])
        else:
            row = table.rowCount()
            table.insertRow(row)
        table.setItem(row,0,QTableWidgetItem(action))
        table.setItem(row,1,QTableWidgetItem(time))
        table.setItem(row,2,QTableWidgetItem(repeat))
        table.setItem(row,3,QTableWidgetItem(status))
        table.setItem(row,4,QTableWidgetItem(content))
        table.verticalScrollBar().setValue(table.verticalScrollBar().maximum())
        if self.editting: #第6列时上一次执行时间，不在表格显示，只记录在配置文件
            Config.config["schedule"][row] = [action,time,repeat,status,content,Config.config["schedule"][row][5]]
        else:
            # table.setItem(row,3,QTableWidgetItem("启用"))
            Config.config["schedule"].append([action,time,repeat,status,content,""])
        self.hide()
        
    def cansel(self):
        self.hide()

    def change_action(self):
        log("in change_action")
        text = self.action_combo.currentText()
        if text == "提醒":
            self.msg_wdiget.show()
            self.exe_wdiget.hide()
        elif text == "执行程序":
            self.msg_wdiget.hide()
            self.exe_wdiget.show()
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
        elif text == "每月":
            self.week_wdiget.hide()
            self.moon_wdiget.show()
            self.custom_wdiget.hide()
            self.date_wdiget.hide()
        elif text == "自定义小时数":
            self.week_wdiget.hide()
            self.moon_wdiget.hide()
            self.custom_wdiget.show()
            self.date_wdiget.hide()
        elif text == "仅一次":
            self.week_wdiget.hide()
            self.moon_wdiget.hide()
            self.custom_wdiget.hide()
            self.date_wdiget.show()
        else:
            self.week_wdiget.hide()
            self.moon_wdiget.hide()
            self.custom_wdiget.hide()
            self.date_wdiget.hide()

    def open_exe(self):
        name = QFileDialog.getOpenFileName()
        log("name:"+str(name[0]))
        if name[0] != "":
            self.exe_edit.setText(name[0])  
