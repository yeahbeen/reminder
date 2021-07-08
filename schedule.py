from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from config import Config
import os
import mytimer


class Schedule(QWidget):
    def __init__(self,par):
        super().__init__()
        self.setWindowTitle("定时程序")
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        # for i in range(self.table.columnCount()):
            # self.table.setColumnWidth(i,60)
        self.table.setColumnWidth(0,60)
        self.table.setColumnWidth(1,110)
        self.table.setColumnWidth(2,50)
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
        self.setGeometry(rect.x(), rect.y(), 410, 300)


    def add(self):
        self.add = Add(self)
        self.add.show()

    def edit(self):
        print("in edit")
        items = self.table.selectedItems()
        print(str(items))
        if len(items) == 0:
            return
        self.add = Add(self,True)
        self.add.show()

    def delete(self):
        row = self.table.currentRow()
        print(row)
        self.table.removeRow(row)
        Config.config["schedule"].remove(Config.config["schedule"][row])

    def closeEvent(self,e):
        Config.save()
        self.start()

    def start(self):
        print("in start")
        diff = 86400000 + QTime.currentTime().msecsTo(QTime(0,0,1))
        print(diff)
        QTimer.singleShot(diff,self.start) #0点的时候重置一下计时器
        self.schedule_timer = []
        for row in range(len(Config.config["schedule"])):      
            s = Config.config["schedule"][row]
            print(str(s))
            if s[3] == "禁用" or s[3] == "已过期":
                continue
            dt = QDateTime.fromString(s[1],"hh:mm M/dd/yyyy")
            print("dt "+str(dt))
            #过期提醒
            if s[5] == "":  #为空表示是新增的，只提醒“仅一次”的，其他的不提醒
                if s[2] == "仅一次":
                    nexttime = dt
                else:
                    nexttime = dt.addYears(100)  
            else:
                lasttime = QDateTime.fromString(s[5],"yyyy-MM-dd hh:mm:ss")
                print(lasttime)
                if s[2] == "每天":
                    nexttime = lasttime.addDays(1)
                elif s[2] == "每周":
                    nexttime = lasttime.addDays(7)
                elif s[2] == "每月":
                    nexttime = lasttime.addMonths(1)
                elif s[2] == "仅一次":
                    nexttime = lasttime.addYears(100)
                print(nexttime)
            if QDateTime.currentDateTime() > nexttime:
                QMessageBox.information(None,"以下日程已过期","内容:"+s[0]+" "+s[4]+"\n"+"时间:"+s[1]+"\n"+"重复:"+s[2])
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
                    print(nexttime)
                s[5] = nexttime0.toString("yyyy-MM-dd hh:mm:ss")
            # if s[2] == "每周" or s[2] == "每月":
            flag = False
            if s[2] == "每周":
                date1 = dt.toString("ddd")
                date2 = QDateTime.currentDateTime().toString("ddd")
                print(date1,date2)
                if date1 == date2:
                    flag = True
            if s[2] == "每月":
                day1 = dt.toString("dd")
                day2 = QDateTime.currentDateTime().toString("dd")
                print(day1,day2)
                if day1 == day2:
                    flag = True
            if flag or s[2] == "仅一次" or s[2] == "每天": #到了指定日期则启动计时器
                diff = QTime.currentTime().msecsTo(dt.time())
                print("diff:"+str(diff))
                if diff >= 0:
                    timer = mytimer.mytimer(s)
                    self.schedule_timer.append(timer)
                    timer.setSingleShot(True)
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
        print(timer)
        s = timer.args
        print("执行事件:"+str(s))
        if s[0] == "提醒":
            QApplication.setQuitOnLastWindowClosed(False)
            self.msg = QMessageBox(QMessageBox.Information,"提醒",s[4])
            self.msg.setWindowFlags(self.msg.windowFlags()|Qt.WindowStaysOnTopHint)
            self.msg.open()
            # QMessageBox.information(None,"提醒",s[4])
        elif s[0] == "关机":
            os.popen("shutdown /s /t 60")
        elif s[0] == "执行程序":
            os.popen(s[4])
            
        itemlist = self.table.findItems(s[1],Qt.MatchExactly)
        for i in itemlist:
            print(i)
            row = self.table.row(i)
            if s[2] == "仅一次":
                self.table.setItem(row,3,QTableWidgetItem("已过期"))
                Config.config["schedule"][row][3] = "已过期"
            Config.config["schedule"][row][5] = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        Config.save()


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
        time_hbox = QHBoxLayout()
        time_label = QLabel("时间:")
        time_label.setMaximumWidth(30)
        time_hbox.addWidget(time_label)
        calendar = QCalendarWidget()
        self.dt_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.dt_edit.setCalendarPopup(True)
        self.dt_edit.setCalendarWidget(calendar)
        time_hbox.addWidget(self.dt_edit)
        repeat_hbox = QHBoxLayout()
        repeat_label = QLabel("重复:")
        repeat_label.setMaximumWidth(30)
        repeat_hbox.addWidget(repeat_label)
        self.repeat_combo = QComboBox()
        self.repeat_combo.addItems(["仅一次","每天","每周","每月"])    
        repeat_hbox.addWidget(self.repeat_combo)  
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
        self.vbox.addLayout(time_hbox)
        self.vbox.addLayout(repeat_hbox)
        self.vbox.addLayout(enable_hbox)
        self.vbox.addLayout(confirm_hbox)
        self.setLayout(self.vbox)
        self.action_combo.currentTextChanged.connect(self.change_action)

        rect = par.geometry()
        self.setGeometry(rect.x(), rect.y(), 300, 150)
        
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
            print(table.item(row,1).text())
            dt = QDateTime.fromString(table.item(row,1).text(),"hh:mm M/dd/yyyy")
            print(dt.toString())
            self.dt_edit.setDateTime(QDateTime.fromString(table.item(row,1).text(),"hh:mm M/dd/yyyy"))
            self.repeat_combo.setCurrentText(table.item(row,2).text())
            self.enable_combo.setCurrentText(table.item(row,3).text())


    def confirm(self):
        table = self.par.table
        if self.editting:
            items = table.selectedItems()
            row = table.row(items[0])
        else:
            row = table.rowCount()
            table.insertRow(row)
        action = self.action_combo.currentText()
        # time = self.hour_combo.currentText()+"时"+self.min_combo.currentText()+"分"
        time = self.dt_edit.dateTime().toString("hh:mm M/dd/yyyy")
        repeat = self.repeat_combo.currentText()
        status = self.enable_combo.currentText()
        content = ""
        if action == "提醒":
            content = self.msg_edit.text()
        elif action == "执行程序":
            content = self.exe_edit.text()
        table.setItem(row,0,QTableWidgetItem(action))
        table.setItem(row,1,QTableWidgetItem(time))
        table.setItem(row,2,QTableWidgetItem(repeat))
        table.setItem(row,3,QTableWidgetItem(status))
        table.setItem(row,4,QTableWidgetItem(content))
        table.verticalScrollBar().setValue(table.verticalScrollBar().maximum())
        if self.editting:
            Config.config["schedule"][row] = [action,time,repeat,status,content,Config.config["schedule"][row][5]]
        else:
            # table.setItem(row,3,QTableWidgetItem("启用"))
            Config.config["schedule"].append([action,time,repeat,status,content,""])
        self.hide()
        
    def cansel(self):
        self.hide()

    def change_action(self):
        print("in change_action")
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

    def open_exe(self):
        name = QFileDialog.getOpenFileName()
        print("name:"+str(name[0]))
        if name[0] != "":
            self.exe_edit.setText(name[0])  
