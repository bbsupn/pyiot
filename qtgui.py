# 导入必要的系统和PyQt5库
import asyncio
import json
import os
import random
import sys
import time
from threading import Thread
import re

import aiohttp
import cv2
import ffmpeg
import numpy as np
import requests
from PyQt5 import uic, QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from aiohttp import ClientSession
from qt_material import apply_stylesheet, QtStyleTools

cty=''
prarams=''
token=''
stream_url='http://192.168.10.200:81/videostream.cgi?loginuse=admin&loginpas=admin'+ '&' + str(time.time()) + str(random.randint(2000, 8000000))
snapshot_url='http://192.168.10.200:81/snapshot.cgi?user=admin&pwd=admin'+ '&' + str(time.time()) + str(random.randint(2000, 8000000))
info_url='http://192.168.10.200:81/get_status.cgi?loginuse=admin&loginpas=admin'+ '&' + str(time.time()) + str(random.randint(2000, 8000000))


def get_token():
    global prarams
    global token
    try:
        login_data = {
            'Account': '13925698710',
            'Password': '114514'
        }
        response = requests.post('http://192.168.0.138/users/login', data=login_data)
        data = response.json()
        json_data = json.dumps(data)
        items = json.loads(json_data)
        token = items["ResultObj"]["AccessToken"]

        with open('token.json', encoding='utf-8') as f:
            data_dict = json.load(f)
            f.close()

        data_dict["AccessToken"] = token

        with open('token.json', 'w', encoding='utf-8') as df:
            json.dump(data_dict, df)
            df.close()


        with open("token.json", 'r', encoding='UTF-8') as load:
            prarams = json.load(load)
            token=prarams["AccessToken"]
            load.close()
    except Exception as e:
        QMessageBox.warning(QWidget(),'Error','连接失败，无法更新token，请检查地址以及端口是否正确。\n异常信息：\n'+str(e))
        QMessageBox.warning(QWidget(),'WARN','将使用本地已有token！如本地token已过期将无法正常使用某些功能！')

ff = None
r=0
y=0
g=0
st=False
rs=False
ys=False
gs=False
f1=0
f2=0
wp=0
l1=0
l2=0



def remove_parentheses(lst):
    return [item for sublist in lst for item in sublist] if any(isinstance(i, tuple) for i in lst) else lst



class WindowEvent(QWidget,QtStyleTools):
    def __init__(self):
        super().__init__()
        self.close_signal=pyqtSignal()
        with open("record.txt", 'w', encoding='UTF-8') as file:
            file.write('')
            file.close()
        self.qthread = QThread()
        self.init_ui()
        self.stime()
        self.thread = QThread()
        self.timer = QTimer()



    def init_ui(self):
        self.ui=uic.loadUi("t1.ui")
        self.ui1=uic.loadUi("t2.ui")
        self.ui2=uic.loadUi("t3.ui")
        self.record =self.ui1.textEdit
        self.getinfo_btn=self.ui.pushButton
        self.show_warn_history_btn=self.ui.pushButton_2
        self.applyid=self.ui.pushButton_3
        self.tempvar=self.ui.textEdit
        self.wetvar=self.ui.textEdit_2
        self.airq=self.ui.textEdit_3
        self.fire_state=self.ui.label_18
        self.fan_state=self.ui.label_19
        self.fan1_state=self.ui.label_13
        self.time=self.ui.label_3
        self.rygled=self.ui.label_8
        self.waterpump=self.ui.label_10
        self.idvar=self.ui.textEdit_4
        self.opencamsys=self.ui.pushButton_4
        self.play=self.ui2.pushButton
        self.kplay=self.ui2.pushButton_2
        self.play_area = self.ui2.label
        self.up=self.ui2.pushButton_3
        self.down=self.ui2.pushButton_6
        self.left=self.ui2.pushButton_4
        self.right=self.ui2.pushButton_5
        self.screenshot=self.ui2.pushButton_7
        self.screenrecord=self.ui2.pushButton_8
        self.maru=self.ui2.label_4
        self.model=self.ui2.label_6
        self.fmv=self.ui2.label_8
        self.wlanmac=self.ui2.label_10
        self.etmac=self.ui2.label_12
        self.redled=self.ui.pushButton_5
        self.yellowled=self.ui.pushButton_7
        self.greenled=self.ui.pushButton_6
        self.fan=self.ui.pushButton_8
        self.waterpumpp=self.ui.pushButton_10
        self.fan1=self.ui.pushButton_12
        self.start_update=self.ui.pushButton_14
        self.center=self.ui2.pushButton_9
        self.reboot=self.ui2.pushButton_12
        self.stop_record=self.ui2.pushButton_13
        self.light=self.ui.textEdit_5
        self.led1=self.ui.label_21
        self.led2=self.ui.label_26
        self.led1p=self.ui.pushButton_9
        self.led2p=self.ui.pushButton_11





        self.getinfo_btn.clicked.connect(self.get)
        self.applyid.clicked.connect(self.set)
        self.show_warn_history_btn.clicked.connect(self.show_warn_window)
        self.opencamsys.clicked.connect(self.opensys)
        self.play.clicked.connect(self.plays)
        self.kplay.clicked.connect(self.stop_play)
        self.record.setReadOnly(True)
        self.tempvar.setReadOnly(True)
        self.wetvar.setReadOnly(True)
        self.airq.setReadOnly(True)
        self.screenshot.clicked.connect(self.handlePrintScreen)
        self.screenrecord.clicked.connect(self.handleStartRecord)
        self.up.pressed.connect(self.handleButtonPress)
        self.down.pressed.connect(self.handleButtonPress)
        self.left.pressed.connect(self.handleButtonPress)
        self.right.pressed.connect(self.handleButtonPress)
        self.up.released.connect(self.handleButtonRelease)
        self.down.released.connect(self.handleButtonRelease)
        self.left.released.connect(self.handleButtonRelease)
        self.right.released.connect(self.handleButtonRelease)
        self.redled.clicked.connect(self.control)
        self.yellowled.clicked.connect(self.control)
        self.greenled.clicked.connect(self.control)
        self.fan.clicked.connect(self.control)
        self.waterpumpp.clicked.connect(self.control)
        self.fan1.clicked.connect(self.control)
        self.led1p.clicked.connect(self.control)
        self.led2p.clicked.connect(self.control)
        self.start_update.clicked.connect(self.startupdate)
        self.center.clicked.connect(self.handleButtonPress)
        self.reboot.clicked.connect(self.handleButtonPress)
        self.stop_record.clicked.connect(self.stop_sign)

    def startupdate(self):
        id = self.idvar.toPlainText()
        if id == '':
            QMessageBox.warning(QWidget(), '提示', 'id还没有被正确设置!无法继续！')
            return
        if id != '':
            p = {'AccessToken': token, 'devIds': id}
            font = ' http://192.168.0.138:81/Devices/Status'
            response = requests.get(font, params=p)
            data = response.json()
            json_data = json.dumps(data)
            items = json.loads(json_data)
            list = items["ResultObj"]
            if len(list) == 0:
                QMessageBox.warning(QWidget(), '提示', '无法找到此id相关联的设备！')
                return
            if list[0]["Name"] != 'gwm':
                QMessageBox.warning(QWidget(), '提示',
                                    '你似乎使用了其他已有设备的id，请使用适用于该项目名为"gwm"的网关设备id！')
                return
        self.getu()
    def stop_sign(self):
        global st
        if not Camera_Thread.isRunning(QThread()):
            QMessageBox.warning(QWidget(), '提示', 'IP摄像头不可用，请检查摄像头是否正常！')
            return
        st=True
        record_thread.terminate(QThread())

    def control(self):
        global r
        global y
        global g
        global f1
        global f2
        global wp
        global l1
        global l2
        id=self.idvar.toPlainText()
        if id == '':
            QMessageBox.warning(QWidget(),'提示','id还没有被正确设置!无法继续！')
            return
        if id != '':
            p = {'AccessToken': token,'devIds': id}
            font = ' http://192.168.0.138:81/Devices/Status'
            response = requests.get(font,params=p)
            data = response.json()
            json_data = json.dumps(data)
            items = json.loads(json_data)
            list = items["ResultObj"]
            if len(list) == 0:
                QMessageBox.warning(QWidget(),'提示','无法找到此id相关联的设备！')
                return
            if list[0]["Name"] != 'gwm':
                QMessageBox.warning(QWidget(), '提示', '你似乎使用了其他已有设备的id，请使用适用于该项目名为"gwm"的网关设备id！')
                return
        url_prefix='http://192.168.0.138/Cmds?deviceId='+id+'&apiTag='
        header= {"AccessToken": token, "Content-Type": "application/json"}
        if self.sender()==self.redled and r==0:
            re=requests.post(url_prefix+'rgb_red',data="1",headers=header)
            r=1
            print("red:"+str(re))
        elif self.sender()==self.redled and r==1:
            re=requests.post(url_prefix+'rgb_red', data="0",headers=header)
            r=0
            print("red:"+str(re))
        elif self.sender()==self.yellowled and y==0:
            re=requests.post(url_prefix+'rgb_yellow', data="1",headers=header)
            y=1
            print("yellow:"+str(re))
        elif self.sender()== self.yellowled and y == 1:
            re=requests.post(url_prefix+'rgb_yellow', data="0",headers=header)
            y = 0
            print("yellow:"+str(re))
        elif self.sender()==self.greenled and g==0:
            re=requests.post(url_prefix+'rgb_green', data="1",headers=header)
            g=1
            print("green:"+str(re))
        elif self.sender()== self.greenled and g == 1:
            re=requests.post(url_prefix+'rgb_green', data="0",headers=header)
            g=0
            print("green:"+str(re))
        elif self.sender()==self.fan and f1==0:
            re=requests.post(url_prefix+'fan', data="1",headers=header)
            f1=1
            print("fan1:"+str(re))
        elif self.sender()==self.fan and f1==1:
            re=requests.post(url_prefix+'fan', data="0",headers=header)
            f1=0
            print("fan1:"+str(re))
        elif self.sender()==self.waterpumpp and wp==0:
            re=requests.post(url_prefix+'MWATERPUMP', data="1",headers=header)
            wp=1
            print("waterpump:"+str(re))
        elif self.sender()==self.waterpumpp and wp==1:
            re=requests.post(url_prefix+'MWATERPUMP', data="0",headers=header)
            wp=0
            print("waterpump:"+str(re))
        elif self.sender()==self.fan1 and f2==0:
            re=requests.post(url_prefix+'fan1', data="1",headers=header)
            f2=1
            print("fan2:"+str(re))
        elif self.sender()==self.fan1 and f2==1:
            re=requests.post(url_prefix+'fan1', data="0",headers=header)
            f2=0
            print("fan2:"+str(re))
        elif self.sender()==self.led1p and l1==0:
            re=requests.post(url_prefix+'led1', data="1",headers=header)
            l1=1
            print("led1:"+str(re))
        elif self.sender()==self.led1p and l1==1:
            re=requests.post(url_prefix+'led1', data="0",headers=header)
            l1=0
            print("led1:"+str(re))
        elif self.sender()==self.led2p and l2==0:
            re=requests.post(url_prefix+'led2', data="1",headers=header)
            l2=1
            print("led2:"+str(re))
        elif self.sender()==self.led2p and l2==1:
            re=requests.post(url_prefix+'led2', data="0",headers=header)
            l2=0
            print("led2:"+str(re))

    def handleButtonRelease(self):
        global cty
        if not Camera_Thread.isRunning(QThread()):
            return
        control_url = 'http://192.168.10.200:81/decoder_control.cgi?loginuse=admin&loginpas=admin&command=' + cty + '&onestep=0' + '&' + str(time.time()) + str(random.randint(2000, 8000000))
        if self.sender() == self.up:
            try:
                cty = '0'
                req = requests.get(control_url)
                result = re.findall(r'var result=\"(.+?)\";', str(req))
            except Exception as e:
                if result:
                    print('up is released\n')
                else:
                    raise Exception(str(e))
        elif self.sender() == self.down:
            try:
                cty = '2'
                req = requests.get(control_url)
                result = re.findall(r'var result=\"(.+?)\";', str(req))
            except Exception as e:
                if result:
                    print('down is released\n')
                else:
                    raise Exception(str(e))
        elif self.sender() == self.left:
            try:
                cty = '4'
                req = requests.get(control_url)
                result = re.findall(r'var result=\"(.+?)\";', str(req))
            except Exception as e:
                if result:
                    print('left is released\n')
                else:
                    raise Exception(str(e))
        elif self.sender() == self.right:
            try:
                cty = '6'
                req = requests.get(control_url)
                result = re.findall(r'var result=\"(.+?)\";', str(req))
            except Exception as e:
                if result:
                    print('right is released\n')
                else:
                    raise Exception(str(e))
        QApplication.processEvents()

    def handleButtonPress(self):
        global cty
        if not Camera_Thread.isRunning(QThread()):
            QMessageBox.warning(QWidget(), '提示', 'IP摄像头不可用，请检查摄像头是否正常！')
            return
        control_url = 'http://192.168.10.200:81/decoder_control.cgi?loginuse=admin&loginpas=admin&command=' + cty + '&onestep=0' + '&' + str(time.time()) + str(random.randint(2000, 8000000))
        if self.sender() == self.up:
            try:
                cty = '1'
                req = requests.get(control_url)
                result = re.findall(r'var result=\"(.+?)\";', str(req))
            except Exception as e:
                if result:
                    print('up is ok\n')
                else:
                    raise Exception(str(e))
        elif self.sender() == self.down:
            try:
                cty = '3'
                req = requests.get(control_url)
                result = re.findall(r'var result=\"(.+?)\";', str(req))
            except Exception as e:
                if result:
                    print('down is ok\n')
                else:
                    raise Exception(str(e))
        elif self.sender() == self.left:
            try:
                cty = '5'
                req = requests.get(control_url)
                result = re.findall(r'var result=\"(.+?)\";', str(req))
            except Exception as e:
                if result:
                    print('left is ok\n')
                else:
                    raise Exception(str(e))
        elif self.sender() == self.right:
            try:
                cty = '7'
                req = requests.get(control_url)
                result = re.findall(r'var result=\"(.+?)\";', str(req))
            except Exception as e:
                if result:
                    print('right is ok\n')
                else:
                    raise Exception(str(e))
        elif self.sender() == self.center:
            try:
                cty = '25'
                req = requests.get(control_url)
                result = re.findall(r'var result=\"(.+?)\";', str(req))
            except Exception as e:
                if result:
                    print('center is ok\n')
                else:
                    raise Exception(str(e))
        elif self.sender() == self.reboot:
            requests.get('http://192.168.10.200:81/reboot.cgi?next_url=reboot.htm&loginuse=admin&loginpas=admin')
        QApplication.processEvents()


    def handlePrintScreen(self):
        global snapshot_url
        if not Camera_Thread.isRunning(QThread()):
            QMessageBox.warning(QWidget(), '提示', 'IP摄像头不可用，请检查摄像头是否正常！')
            return
        camera=cv2.VideoCapture(snapshot_url)
        if os.path.exists('./screenshot'):
            imgfile = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])),'screenshot',
                               time.strftime("%Y%m%d%H%M%S", time.localtime()) + ".png")
            print(imgfile)
            ret, img = camera.read()
            if ret:
                cur_frame = cv2.imwrite(imgfile.format(0), img)
                print(cur_frame)
            camera.release()
        else:
            os.mkdir('./screenshot')
            imgfile = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'screenshot',
                                   time.strftime("%Y%m%d%H%M%S", time.localtime()) + ".png")
            print(imgfile)
            ret, img = camera.read()
            if ret:
                cur_frame = cv2.imwrite(imgfile.format(0), img)
                print(cur_frame)
            camera.release()

    def handleStartRecord(self):
        if Camera_Thread.isRunning(QThread()):
            t=record_thread()
            t.start()
        else:
            QMessageBox.warning(QWidget(), '提示', 'IP摄像头不可用，请检查摄像头是否正常！')

    def stime(self):
        thread=Thread(target=self.time_real)
        thread.daemon=True
        thread.start()



    def stop_play(self):
        if Camera_Thread.isRunning(QThread()):
            self.camera_thread.terminate()
            ff.kill()
            self.play_area.setPixmap(QPixmap(""))
        else:
            QMessageBox.warning(QWidget(), '提示', '摄像头还未启动！')

    def opensys(self):
        QMessageBox.warning(QWidget(),'实验性警告','注意！你正在使用一项实验性功能！可能包含不可预料的错误在内，尚未经过广泛测试，如遇到任何问题请不要发起issue！\n')
        self.ui2.show()

    def check_camera_host(self):
        try:
            requests.get(info_url,timeout=2.5)
            return True
        except:
            return False

    def plays(self):
        if not self.check_camera_host():
            QMessageBox.warning(QWidget(), '提示', 'IP摄像头不可用，请检查摄像头是否正常！')
            return
        self.camera_thread = Camera_Thread(self.play_area)
        self.camera_thread.start()
        req=requests.get(info_url)
        pattern = re.compile("var (.+?)=\"(.+?)\";")
        matches = re.findall(pattern, req.text)
        res = remove_parentheses(matches)
        list = []
        for match in res:
            list.append(match)
        self.maru.setText(list[1])
        self.model.setText(list[3])
        self.fmv.setText(list[5])
        self.wlanmac.setText(list[9])
        self.etmac.setText(list[7])



    def set(self):
        id_var = self.idvar
        monitor_instance = Monitor(id_var, parent=self)
        monitor_instance.monitoringError.connect(self.on_monitoring_error)
        monitor_instance.start_monitoring()

    def on_monitoring_error(self, error):
        # 显示错误消息或其他处理
        QMessageBox.critical(QWidget(), '错误', error)

    def get(self):
        id = self.idvar.toPlainText()
        if id == '':
            QMessageBox.warning(QWidget(),'提示','id还没有被正确设置!无法继续！')
            return
        if id != '':
            p = {'AccessToken': token,'devIds': id}
            font = ' http://192.168.0.138:81/Devices/Status'
            response = requests.get(font,params=p)
            data = response.json()
            json_data = json.dumps(data)
            items = json.loads(json_data)
            list = items["ResultObj"]
            if len(list) == 0:
                QMessageBox.warning(QWidget(),'提示','无法找到此id相关联的设备！')
                return
            if list[0]["Name"] != 'gwm':
                QMessageBox.warning(QWidget(), '提示', '你似乎使用了其他已有设备的id，请使用适用于该项目名为"gwm"的网关设备id！')
                return
        led_state = {"red": "", "yellow": "", "green": ""}
        font = 'http://192.168.0.138/devices/'
        end = '/sensors/'
        self.rygled.setText("未启动")
        response = requests.get(
            font + str(id) + end + 'temp',
            params=prarams
        )
        data = response.json()
        json_data = json.dumps(data)
        items = json.loads(json_data)
        value = str(items["ResultObj"]["Value"])
        self.tempvar.setPlainText(value)

        response = requests.get(
            font + str(id) + end + 'wet',
            params=prarams
        )
        data = response.json()
        json_data = json.dumps(data)
        items = json.loads(json_data)
        value = str(items["ResultObj"]["Value"])
        self.wetvar.setPlainText(value)

        response = requests.get(
            font + str(id) + end + 'airq',
            params=prarams
        )
        data = response.json()
        json_data = json.dumps(data)
        items = json.loads(json_data)
        value = str(items["ResultObj"]["Value"])
        self.airq.setPlainText(value)

        response = requests.get(
            font + str(id) + end + 'light',
            params=prarams
        )
        data = response.json()
        json_data = json.dumps(data)
        items = json.loads(json_data)
        value = str(items["ResultObj"]["Value"])
        self.light.setPlainText(value)

        response = requests.get(
            font + str(id) + end + 'fire',
            params=prarams
        )
        data = response.json()
        json_data = json.dumps(data)
        items = json.loads(json_data)
        value = items["ResultObj"]["Value"]
        if 0 <= value < 1:
            self.fire_state.setText("正常")
        if value >= 1:
            self.fire_state.setText("警告")

        response = requests.get(
            font + str(id) + end + 'fan',
            params=prarams
        )
        data = response.json()
        json_data = json.dumps(data)
        items = json.loads(json_data)
        value = items["ResultObj"]["Value"]
        if value == 0:
            self.fan_state.setText("已关闭")
        if value == 1:
            self.fan_state.setText("已打开")

        response = requests.get(
            font + str(id) + end + 'fan1',
            params=prarams
        )
        data = response.json()
        json_data = json.dumps(data)
        items = json.loads(json_data)
        value = items["ResultObj"]["Value"]
        if value == 0:
            self.fan1_state.setText("已关闭")
        if value == 1:
            self.fan1_state.setText("已打开")

        response = requests.get(
            font + str(id) + end + 'rgb_red',
            params=prarams
        )
        data = response.json()
        json_data = json.dumps(data)
        items = json.loads(json_data)
        value = items["ResultObj"]["Value"]
        if value == 1:
            led_state["red"] = "红灯"
            self.rygled.setText(led_state["red"] + ' ' + led_state["yellow"] + ' ' + led_state["green"])

        response = requests.get(
            font + str(id) + end + 'rgb_yellow',
            params=prarams
        )
        data = response.json()
        json_data = json.dumps(data)
        items = json.loads(json_data)
        value = items["ResultObj"]["Value"]
        if value == 1:
            led_state["yellow"] = "黄灯"
            self.rygled.setText(led_state["red"] + ' ' + led_state["yellow"] + ' ' + led_state["green"])

        response = requests.get(
            font + str(id) + end + 'rgb_green',
            params=prarams
        )
        data = response.json()
        json_data = json.dumps(data)
        items = json.loads(json_data)
        value = items["ResultObj"]["Value"]
        if value == 1:
            led_state["green"] = "绿灯"
            self.rygled.setText(led_state["red"] + ' ' + led_state["yellow"] + ' ' + led_state["green"])

        response = requests.get(
            font + str(id) + end + 'MWATERPUMP',
            params=prarams
        )
        data = response.json()
        json_data = json.dumps(data)
        items = json.loads(json_data)
        value = items["ResultObj"]["Value"]
        if value == 0:
            self.waterpump.setText("已关闭")
        if value == 1:
            self.waterpump.setText("已打开")

        response = requests.get(
            font + str(id) + end + 'led1',
            params=prarams
        )
        data = response.json()
        json_data = json.dumps(data)
        items = json.loads(json_data)
        value = items["ResultObj"]["Value"]
        if value == 0:
            self.led1.setText("已关闭")
        if value == 1:
            self.led1.setText("已打开")

        response = requests.get(
            font + str(id) + end + 'led2',
            params=prarams
        )
        data = response.json()
        json_data = json.dumps(data)
        items = json.loads(json_data)
        value = items["ResultObj"]["Value"]
        if value == 0:
            self.led2.setText("已关闭")
        if value == 1:
            self.led2.setText("已打开")

        QApplication.processEvents()

    def getu(self):
        self.setup_periodic_updates()

    def show_warn_window(self):
        self.ui1.show()
        with open("record.txt", 'r',encoding='UTF-8') as f:
            self.record.setText(f.read())
            f.close()

    def time_real(self):
        while True:
            self.time.setText(time.asctime())
            time.sleep(1)

    def setup_periodic_updates(self):
        font = 'http://192.168.0.138/devices/'
        self.worker = UpdateWorker(font, self.idvar.toPlainText(), prarams)  # 初始化工作线程
        self.worker.moveToThread(self.thread)  # 将工作线程移动到新线程
        self.thread = PeriodicUpdateThread(self.worker)
        self.worker.update_finished.connect(self.handle_update_results)  # 接收更新结果
        self.thread.start()  # 启动线程


    @pyqtSlot()
    def stop_updates(self):
        """停止周期性更新"""
        self.thread.stop()
        self.thread.quit()  # 确保线程能够安全退出
        self.thread.wait()

    def handle_update_results(self, update_info):
        global rs
        global ys
        global gs
        """处理从工作线程传来的更新信息"""
        endpoint = update_info["endpoint"]
        value = update_info["value"]
        led_state = update_info["led_state"]
        # 根据endpoint更新对应的UI元素
        if endpoint == 'temp':
            self.tempvar.setPlainText(str(value))
        elif endpoint == 'wet':
            self.wetvar.setPlainText(str(value))
        elif endpoint == 'airq':
            self.airq.setPlainText(str(value))
        elif endpoint == 'light':
            self.light.setPlainText(str(value))
        elif endpoint == 'fire':
            if 0 <= value < 1:
                self.fire_state.setText("正常")
            if value >= 1:
                self.fire_state.setText("警告")
        elif endpoint == 'fan':
            if value == 0:
                self.fan_state.setText("已关闭")
            if value == 1:
                self.fan_state.setText("已打开")
        elif endpoint == 'led1':
            if value == 0:
                self.led1.setText("已关闭")
            if value == 1:
                self.led1.setText("已打开")
        elif endpoint == 'led2':
            if value == 0:
                self.led2.setText("已关闭")
            if value == 1:
                self.led2.setText("已打开")
        elif endpoint == 'fan1':
            if value == 0:
                self.fan1_state.setText("已关闭")
            if value == 1:
                self.fan1_state.setText("已打开")
        elif endpoint == 'rgb_red':
            if value:
                self.rygled.setText(led_state["red"] + ' ' + led_state["yellow"] + ' ' + led_state["green"])
                rs=value
            else:
                rs=value
        elif endpoint == 'rgb_yellow':
            if value:
                self.rygled.setText(led_state["red"] + ' ' + led_state["yellow"] + ' ' + led_state["green"])
                ys=value
            else:
                ys=value
        elif endpoint == 'rgb_green':
            if value:
                self.rygled.setText(led_state["red"] + ' ' + led_state["yellow"] + ' ' + led_state["green"])
                gs=value
            else:
                gs=value
        elif endpoint == 'MWATERPUMP':
            if value == 0:
                self.waterpump.setText("已关闭")
            if value == 1:
                self.waterpump.setText("已打开")


        if not rs and not ys and not gs:
            self.rygled.setText("未启动")



        if len(self.rygled.text())==0:
            self.rygled.setText("未启动")



class PeriodicUpdateThread(QThread):
    updateFinished = pyqtSignal()

    def __init__(self, worker, interval_ms=500):
        super().__init__()
        self.worker = worker
        self.interval_ms = interval_ms
        self.stop_flag = False

    def run(self):
        while not self.stop_flag:
            self.worker.run_updates()
            self.msleep(self.interval_ms)

    def stop(self):
        self.stop_flag = True


class UpdateWorker(QObject):
    update_finished = pyqtSignal(dict)  # 信号，用于通知UI线程更新已完成

    def __init__(self, font,deviceid,params):
        super().__init__()
        self.font = font
        self.device_id = deviceid
        self.params = params


    def run_updates(self):
        led_state = {"red": "", "yellow": "", "green": ""}
        endpoints = [
            'temp', 'wet', 'airq', 'light', 'fire', 'fan','led1','led2', 'fan1',
            'rgb_red', 'rgb_yellow', 'rgb_green', 'MWATERPUMP'
        ]
        for endpoint in endpoints:
            full_url = self.font+self.device_id+'/sensors/'+endpoint
            response = requests.get(full_url, params=self.params)
            data = response.json()
            value = data["ResultObj"]["Value"]

            if endpoint.startswith('rgb_'):
                color = endpoint.split('_')[1]
                if value == 1:
                    if color == 'red':
                        led_state[color] = "红灯"
                    if color == 'yellow':
                        led_state[color] = "黄灯"
                    if color == 'green':
                        led_state[color] = "绿灯"


            # 发出信号，包含所有必要的更新信息
            self.update_finished.emit({
                "endpoint": endpoint,
                "value": value,
                "led_state": led_state,
            })
            # 确保UI有机会处理事件，避免UI冻结
            QApplication.processEvents()

class record_thread(QThread,WindowEvent):
    def __init__(self):
        super().__init__()

    def run(self):
        global st
        global stream_url
        camera = cv2.VideoCapture(stream_url)
        # 获取视频帧率
        frame_rate = camera.get(cv2.CAP_PROP_FPS)
        QApplication.processEvents()
        if os.path.exists('./screenrecord'):

            savefile = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])),'screenrecord',
                                time.strftime("%Y%m%d%H%M%S", time.localtime()) + ".mp4")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(savefile, fourcc, frame_rate,(int(camera.get(3)), int(camera.get(4))))

            while True:
                ret, frame = camera.read()
                if ret:
                    out.write(frame)
                if st:
                    st=False
                    break
            out.release()
            camera.release()
        else:
            os.mkdir('./screenrecord')
            savefile = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'screenrecord',
                                    time.strftime("%Y%m%d%H%M%S", time.localtime()) + ".mp4")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(savefile, fourcc, frame_rate, (int(camera.get(3)), int(camera.get(4))))

            while True:
                ret, frame = camera.read()
                if ret:
                    out.write(frame)
                if st:
                    st=False
                    break
            out.release()
            camera.release()


class Camera_Thread(QThread,WindowEvent):
    def __init__(self,playarea):
        super().__init__()
        self.play_area=playarea

    def run(self):
        global ff
        global stream_url
        probe = ffmpeg.probe(stream_url)
        video_info = next(stream for stream in probe['streams'] if stream['codec_type'] == 'video')
        width = video_info['width']
        height = video_info['height']

        ffmpeg_cmd = (
            ffmpeg
            .input(stream_url, hwaccel='cuda', vcodec='mjpeg_cuvid')
            .output('pipe:', format='rawvideo', pix_fmt='bgr24',loglevel='quiet')
            .run_async(pipe_stdout=True)
        )
        ff=ffmpeg_cmd
        while True:
            in_bytes = ffmpeg_cmd.stdout.read(width * height * 3)
            frame = (
                np
                .frombuffer(in_bytes, np.uint8)
                .reshape([height, width, 3])
            )
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            image = QImage(frame, width, height, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(image)
            self.play_area.setPixmap(pixmap)
            self.play_area.setScaledContents(True)
            self.play_area.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            del (frame)
            QApplication.processEvents()

class MonitorWorker(QThread):
    errorOccurred = pyqtSignal(str)

    def __init__(self, coroutine, *args):
        super().__init__()
        self.coroutine = coroutine
        self.args = args

    def run(self):
        # 创建一个新的 asyncio 事件循环，而非使用 QEventLoop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # 使用创建的事件循环运行协程
            task = loop.create_task(self.coroutine(*self.args))
            loop.run_until_complete(task)
        except Exception as e:
            self.errorOccurred.emit(f'监控过程中发生错误: {str(e)}')


class Monitor(QObject):  # 使用QObject而非QThread
    monitoringError = pyqtSignal(str)

    def __init__(self, id_var, parent=None):
        super().__init__(parent)
        self.id_var = id_var
        self.token = token

    async def fetch_device_status(self, id):
        font = 'http://192.168.0.138:81/Devices/Status'
        params = {'AccessToken': self.token, 'devIds': id}
        async with ClientSession() as session:
            async with session.get(font, params=params) as response:
                data = await response.json()
                return data

    async def check_fire_alert(self, id):
        font = 'http://192.168.0.138/devices/'
        end = '/sensors/fire'
        async with ClientSession() as session:
            while True:
                async with session.get(font + str(id) + end, params=prarams) as response:
                    data = await response.json()
                    value = data["ResultObj"]["Value"]
                    if value >= 1:
                        with open("record.txt", 'a+', encoding='UTF-8') as file:
                            file.write('火焰告警' + '     ' + time.asctime() + '\n')
                        await asyncio.sleep(10)  # 使用asyncio的sleep而非time.sleep

    def start_monitoring(self):
        id = self.id_var.toPlainText()
        if not id:
            self.monitoringError.emit('ID不能为空！')
            return
        # 创建并启动一个新的工作线程来执行异步任务
        self.worker_thread = MonitorWorker(self.async_monitor, id)
        self.worker_thread.errorOccurred.connect(self.handle_error)
        self.worker_thread.start()

    def handle_error(self, error):
        self.monitoringError.emit(error)

    async def async_monitor(self, id):
        try:
            data = await self.fetch_device_status(id)
            items = data["ResultObj"]
            if not items:
                QMessageBox.warning(QWidget(), '提示', '无法找到此ID相关联的设备！')
                return
            if items[0]["Name"] != 'gwm':
                QMessageBox.warning(QWidget(), '提示','你似乎使用了其他已有设备的ID，请使用适用于该项目名为"gwm"的网关设备ID！')
                return

            await self.check_fire_alert(id)
        except aiohttp.ClientError as e:
            print(f"网络错误: {e}")




if __name__ == '__main__':
    # 创建应用程序实例并传入命令行参数
    app = QApplication(sys.argv)
    get_token()
    WindowEvent()
    w=WindowEvent()
    apply_stylesheet(app, theme='dark_cyan.xml')
    w.ui.show()
    if not w.ui1.isVisible():
        w.ui1.close()
    if not w.ui.isVisible():
        w.ui.close()
    if not w.ui2.isVisible():
        w.ui2.close()
    # 启动事件循环
    sys.exit(app.exec_())