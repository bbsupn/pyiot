# 导入必要的系统和PyQt5库
import asyncio
import json
import os
import random
import sys
import time
from threading import Thread
import re

import aiofiles
import aiohttp
import cv2
import ffmpeg
import numpy as np
import requests
import res_rc
from PyQt5 import uic, QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from aiohttp import ClientSession
from concurrent.futures import ThreadPoolExecutor

prarams=''
token=''
stream_url='http://192.168.10.200:81/videostream.cgi?loginuse=admin&loginpas=admin'+ '&' + str(time.time()) + str(random.randint(2000, 8000000))
snapshot_url='http://192.168.10.200:81/snapshot.cgi?user=admin&pwd=admin'+ '&' + str(time.time()) + str(random.randint(2000, 8000000))
info_url='http://192.168.10.200:81/get_status.cgi?loginuse=admin&loginpas=admin'+ '&' + str(time.time()) + str(random.randint(2000, 8000000))
reboot_url='http://192.168.10.200:81/reboot.cgi?next_url=reboot.htm&loginuse=admin&loginpas=admin'


def get_token():
    global prarams
    global token
    try:
        login_data = {
            'Account':'13377815672',
            'Password':'114514'
        }
        with requests.post('http://api.nlecloud.com/users/login', data=login_data) as response:
            data = response.json()
            json_data = json.dumps(data)
            items = json.loads(json_data)
            token = items["ResultObj"]["AccessToken"]

        with open('token.json', encoding='utf-8') as f:
            data_dict = json.load(f)

        data_dict["AccessToken"] = token

        with open('token.json', 'w', encoding='utf-8') as df:
            json.dump(data_dict, df)


        with open("token.json", 'r', encoding='UTF-8') as load:
            prarams = json.load(load)
            token=prarams["AccessToken"]

    except Exception as e:
        QMessageBox.warning(QWidget(),'Error','连接失败，无法更新token，请检查地址以及端口是否正确。\n异常信息：\n'+str(e))
        QMessageBox.warning(QWidget(),'WARN','将使用本地已有token！如本地token已过期将无法正常使用某些功能！')

ff = None
st = False



def remove_parentheses(lst):
    return [item for sublist in lst for item in sublist] if any(isinstance(i, tuple) for i in lst) else lst

class NetworkWorker(QObject):
    """
    网络请求工作线程。
    """
    requestFinished = pyqtSignal(str, str)

    def __init__(self, url, data, headers):
        super().__init__()
        self.url = url
        self.data = data
        self.headers = headers

    def run_request(self):
        try:
            with requests.post(self.url, data=self.data, headers=self.headers) as response:
                response.raise_for_status()
        except Exception as e:
            self.requestFinished.emit(self.url, f"失败: {str(e)}")

class NetworkThread(QThread):
    """
    网络请求线程。
    """
    requestFinished = pyqtSignal(str, str)

    def __init__(self, url, data, headers):
        super().__init__()
        self.worker = NetworkWorker(url, data, headers)
        self.worker.requestFinished.connect(self.requestFinished)

    def run(self):
        self.worker.run_request()

class WindowEvent(QWidget):
    def __init__(self):
        super().__init__()
        self.close_signal=pyqtSignal()
        self.init_ui()
        self.stime()
        self.thread = QThread()
        self.thread1=QThread()
        self.timer = QTimer()
        self.camera_thread = None
        self.executor = ThreadPoolExecutor(max_workers=5)  # 创建线程池

        self.r = 0
        self.y = 0
        self.g = 0
        self.rs = False
        self.ys = False
        self.gs = False
        self.f1 = 0
        self.f2 = 0
        self.wp = 0
        self.l1 = 0
        self.l2 = 0
        self.state=0

    def init_ui(self):
        self.ui=uic.loadUi("t1.ui")
        self.ui1=uic.loadUi("t2.ui")
        self.ui2=uic.loadUi("t3.ui")
        self.record =self.ui1.textEdit
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
        self.idvar=self.ui.label_56
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
        self.stop_record=self.ui2.pushButton_10
        self.light=self.ui.textEdit_5
        self.led1=self.ui.label_21
        self.led2=self.ui.label_26
        self.led1p=self.ui.pushButton_9
        self.led2p=self.ui.pushButton_11
        self.car_num=self.ui.label_53
        self.m_water=self.ui.label_59
        self.play_area.setAutoFillBackground(True)
        self.warn_info=self.ui.label_55
        self.record_state=self.ui2.label_13
        self.record_state.setVisible(False)






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

        self.ui.label_27.setPixmap(QPixmap(":/res/温度.svg"))
        self.ui.label_28.setPixmap(QPixmap(":/res/湿度.svg"))
        self.ui.label_29.setPixmap(QPixmap(":/res/空气质量.svg"))
        self.ui.label_30.setPixmap(QPixmap(":/res/光照度.svg"))
        self.ui.label_31.setPixmap(QPixmap(":/res/id.svg"))
        self.ui.label_32.setPixmap(QPixmap(":/res/红灯.svg"))
        self.ui.label_33.setPixmap(QPixmap(":/res/黄灯.svg"))
        self.ui.label_34.setPixmap(QPixmap(":/res/绿灯.svg"))
        self.ui.label_35.setPixmap(QPixmap(":/res/Fill_1.svg"))
        self.ui.label_36.setPixmap(QPixmap(":/res/三色灯.svg"))
        self.ui.label_37.setPixmap(QPixmap(":/res/照明灯.svg"))
        self.ui.label_38.setPixmap(QPixmap(":/res/照明灯.svg"))
        self.ui.label_45.setPixmap(QPixmap(":/res/照明灯.svg"))
        self.ui.label_46.setPixmap(QPixmap(":/res/照明灯.svg"))
        self.ui.label_39.setPixmap(QPixmap(":/res/风扇_.svg"))
        self.ui.label_40.setPixmap(QPixmap(":/res/风扇_.svg"))
        self.ui.label_41.setPixmap(QPixmap(":/res/风扇_.svg"))
        self.ui.label_42.setPixmap(QPixmap(":/res/风扇_.svg"))
        self.ui.label_43.setPixmap(QPixmap(":/res/水泵.svg"))
        self.ui.label_44.setPixmap(QPixmap(":/res/水泵.svg"))
        self.ui.label_47.setPixmap(QPixmap(":/res/获取.svg"))
        self.ui.label_48.setPixmap(QPixmap(":/res/日志.svg"))
        self.ui.label_49.setPixmap(QPixmap(":/res/5摄像头.svg"))
        self.ui.label_51.setPixmap(QPixmap(":/res/车辆管理.svg"))
        self.ui.label_58.setPixmap(QPixmap(":/res/液位.svg"))

    def check_camera_thread(self):
        if self.camera_thread and self.camera_thread.isRunning():
            return True
        return False

    def startupdate(self):
        id = self.idvar.text()
        if id == '':
            QMessageBox.warning(QWidget(), '提示', 'id还没有被正确设置!无法继续！')
            return
        if id != '':
            p = {'AccessToken': token, 'devIds': id}
            font = ' http://api.nlecloud.com/Devices/Status'
            try:
                with requests.get(font, params=p) as response:
                    data = response.json()
                    json_data = json.dumps(data)
                    items = json.loads(json_data)
                    list = items["ResultObj"]
                    if len(list) == 0:
                        QMessageBox.warning(QWidget(), '提示', '无法找到此id相关联的设备！')
                        return
                    if list[0]["Name"] != '智慧隧道':
                        QMessageBox.warning(QWidget(), '提示','你似乎使用了其他已有设备的id，请使用适用于该项目名为"智慧隧道"的网关设备id！')
                        return
            except Exception as e:
                print(f"startupdate:一个未捕获的异常：{e}")
                return
        self.getu()
    def stop_sign(self):
        global st
        if not self.check_camera_thread():
            QMessageBox.warning(QWidget(), '提示', 'IP摄像头不可用，请检查摄像头是否正常！')
            return
        st=True
        record_thread.terminate(QThread())
        self.record_state.setVisible(False)

    def control(self):
        id = self.idvar.text()
        if id == '':
            QMessageBox.warning(QWidget(), '提示', 'id还没有被正确设置!无法继续！')
            return
        if id != '':
            p = {'AccessToken': token, 'devIds': id}
            font = ' http://api.nlecloud.com/Devices/Status'
            try:
                with requests.get(font, params=p) as response:
                    data = response.json()
                    json_data = json.dumps(data)
                    items = json.loads(json_data)
                    list = items["ResultObj"]
                    if len(list) == 0:
                        QMessageBox.warning(QWidget(), '提示', '无法找到此id相关联的设备！')
                        return
                    if list[0]["Name"] != '智慧隧道':
                        QMessageBox.warning(QWidget(), '提示',
                                            '你似乎使用了其他已有设备的id，请使用适用于该项目名为"智慧隧道"的网关设备id！')
                        return
            except Exception as e:
                print(f"control:一个未捕获的异常：{e}")
                return
        url_prefix = 'http://api.nlecloud.com/Cmds?deviceId=' + id + '&apiTag='
        header = {"AccessToken": token, "Content-Type": "application/json"}
        d = ''
        if self.sender() == self.redled and self.r == 0:
            self.executor.submit(self.send_request, url_prefix + 'rgb_red', '1', header, 'red', 1)
        elif self.sender() == self.redled and self.r == 1:
            self.executor.submit(self.send_request, url_prefix + 'rgb_red', '0', header, 'red', 0)
        elif self.sender() == self.yellowled and self.y == 0:
            self.executor.submit(self.send_request, url_prefix + 'rgb_yellow', '1', header, 'yellow', 1)
        elif self.sender() == self.yellowled and self.y == 1:
            self.executor.submit(self.send_request, url_prefix + 'rgb_yellow', '0', header, 'yellow', 0)
        elif self.sender() == self.greenled and self.g == 0:
            self.executor.submit(self.send_request, url_prefix + 'rgb_green', '1', header, 'green', 1)
        elif self.sender() == self.greenled and self.g == 1:
            self.executor.submit(self.send_request, url_prefix + 'rgb_green', '0', header, 'green', 0)
        elif self.sender() == self.fan and self.f1 == 0:
            self.executor.submit(self.send_request, url_prefix + 'fan', '1', header, 'fan', 1)
        elif self.sender() == self.fan and self.f1 == 1:
            self.executor.submit(self.send_request, url_prefix + 'fan', '0', header, 'fan', 0)
        elif self.sender() == self.waterpumpp and self.wp == 0:
            self.executor.submit(self.send_request, url_prefix + 'MWATERPUMP', '1', header, 'waterpump', 1)
        elif self.sender() == self.waterpumpp and self.wp == 1:
            self.executor.submit(self.send_request, url_prefix + 'MWATERPUMP', '0', header, 'waterpump', 0)
        elif self.sender() == self.fan1 and self.f2 == 0:
            self.executor.submit(self.send_request, url_prefix + 'fan1', '1', header, 'fan1', 1)
        elif self.sender() == self.fan1 and self.f2 == 1:
            self.executor.submit(self.send_request, url_prefix + 'fan1', '0', header, 'fan1', 0)
        elif self.sender() == self.led1p and self.l1 == 0:
            self.executor.submit(self.send_request, url_prefix + 'led1', '1', header, 'led1', 1)
        elif self.sender() == self.led1p and self.l1 == 1:
            self.executor.submit(self.send_request, url_prefix + 'led1', '0', header, 'led1', 0)
        elif self.sender() == self.led2p and self.l2 == 0:
            self.executor.submit(self.send_request, url_prefix + 'led2', '1', header, 'led2', 1)
        elif self.sender() == self.led2p and self.l2 == 1:
            self.executor.submit(self.send_request, url_prefix + 'led2', '0', header, 'led2', 0)

    def send_request(self, url, data, headers, var_name, value):
        try:
            with requests.post(url, data=data, headers=headers) as response:
                response.raise_for_status()
                print(f"{var_name}:{str(response.text)}")
                globals()[var_name] = value
        except Exception as e:
            print(f"send_request:一个未捕获的异常：{e}")

    def handleButtonRelease(self):
        if not self.check_camera_thread():
            return
        control_url = 'http://192.168.10.200:81/decoder_control.cgi?loginuse=admin&loginpas=admin&command='
        if self.sender() == self.up:
            try:
                with requests.get(control_url + '1' + '&onestep=0' + '&' + str(time.time()) + str(random.randint(2000, 8000000))):pass
            except Exception as e:
                print(f"handleButtonRelease:一个未捕获的异常：{e}")
        elif self.sender() == self.down:
            try:
                with requests.get(control_url + '3' + '&onestep=0' + '&' + str(time.time()) + str(random.randint(2000, 8000000))):pass
            except Exception as e:
                print(f"handleButtonRelease:一个未捕获的异常：{e}")
        elif self.sender() == self.left:
            try:
                with requests.get(control_url + '5' + '&onestep=0' + '&' + str(time.time()) + str(random.randint(2000, 8000000))):pass
            except Exception as e:
                print(f"handleButtonRelease:一个未捕获的异常：{e}")
        elif self.sender() == self.right:
            try:
                with requests.get(control_url + '7' + '&onestep=0' + '&' + str(time.time()) + str(random.randint(2000, 8000000))):pass
            except Exception as e:
                print(f"handleButtonRelease:一个未捕获的异常：{e}")
        QApplication.instance().processEvents()

    def handleButtonPress(self):
        if not self.check_camera_thread():
            return
        control_url = 'http://192.168.10.200:81/decoder_control.cgi?loginuse=admin&loginpas=admin&command='
        try:
            if self.sender() == self.up:
                    with requests.get(control_url + '0' + '&onestep=0' + '&' + str(time.time()) + str(random.randint(2000, 8000000))):pass
            elif self.sender() == self.down:
                    with requests.get(control_url + '2' + '&onestep=0' + '&' + str(time.time()) + str(random.randint(2000, 8000000))):pass
            elif self.sender() == self.left:
                    with requests.get(control_url + '4' + '&onestep=0' + '&' + str(time.time()) + str(random.randint(2000, 8000000))):pass
            elif self.sender() == self.right:
                    with requests.get(control_url + '6' + '&onestep=0' + '&' + str(time.time()) + str(random.randint(2000, 8000000))):pass
            elif self.sender() == self.center:
                    with requests.get(control_url + '25' + '&onestep=0' + '&' + str(time.time()) + str(random.randint(2000, 8000000))):pass
            elif self.sender() == self.reboot:
                with requests.get(reboot_url):pass
            QApplication.instance().processEvents()
        except Exception as e:
            print(f"handleButtonPress:一个未捕获的异常：{e}")

    def handlePrintScreen(self):
        global snapshot_url
        if not self.check_camera_thread():
            QMessageBox.warning(QWidget(), '提示', 'IP摄像头不可用，请检查摄像头是否正常！')
            return
        camera = cv2.VideoCapture(snapshot_url)
        if os.path.exists('./screenshot'):
            imgfile = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'screenshot',
                                   time.strftime("%Y%m%d%H%M%S", time.localtime()) + ".png")
            print(imgfile)
            ret, img = camera.read()
            if ret:
                self.executor.submit(self.save_image, imgfile, img)
            camera.release()
        else:
            os.mkdir('./screenshot')
            imgfile = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'screenshot',
                                   time.strftime("%Y%m%d%H%M%S", time.localtime()) + ".png")
            print(imgfile)
            ret, img = camera.read()
            if ret:
                self.executor.submit(self.save_image, imgfile, img)
            camera.release()

    def save_image(self, imgfile, img):
        try:
            cur_frame = cv2.imwrite(imgfile, img)
            print(cur_frame)
        except Exception as e:
            print(f"save_image:一个未捕获的异常：{e}")

    def handleStartRecord(self):
        if self.check_camera_thread():
            t=record_thread()
            t.start()
            self.record_state.setVisible(True)
        else:
            QMessageBox.warning(QWidget(), '提示', 'IP摄像头不可用，请检查摄像头是否正常！')

    def stime(self):
        thread=Thread(target=self.time_real)
        thread.daemon=True
        thread.start()



    def stop_play(self):
        if self.check_camera_thread():
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
            with requests.get(info_url,timeout=2.5):
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
        """
        设置周期性更新，定期获取设备状态。
        """
        font = 'http://api.nlecloud.com/devices/'
        self.worker = UpdateWorker(font, self.idvar.text(), prarams)
        self.worker1 = lora(font, prarams)
        self.worker.moveToThread(self.thread)
        self.worker1.moveToThread(self.thread1)
        self.thread = PeriodicUpdateThread(self.worker,800)
        self.thread1=PeriodicUpdateThread(self.worker1,800)
        self.worker.update_finished.connect(self.handle_update_results)  # 接收更新结果
        self.worker1.update_finished.connect(self.updates)
        self.thread.started.connect(self.worker.run_updates)
        self.thread1.started.connect(self.worker1.run_updates)
        self.thread.start()
        self.thread1.start()

    @pyqtSlot()
    def stop_updates(self):
        """
        停止周期性更新。
        """
        self.thread.requestInterruption()
        self.thread.quit()
        self.thread.wait()
        self.thread1.requestInterruption()
        self.thread1.quit()
        self.thread1.wait()

    def updates(self, update_info):
        """
        处理从工作线程传来的更新信息。
        """
        id = self.idvar.text()
        url_prefix = f'http://api.nlecloud.com/Cmds?deviceId={id}&apiTag='
        header = {"AccessToken": token, "Content-Type": "application/json"}
        endpoint = update_info["endpoint"]
        value = update_info["value"]
        led_state = update_info["led_state"]

        try:
            if endpoint == 'car_number':
                self.car_num.setText(str(value))
                self.set_rgb_led(value, url_prefix, header, led_state)
            elif endpoint == 'm_water':
                self.m_water.setText(str(int(value)))
                self.handle_water_pump(value, url_prefix, header)
        except Exception as e:
            print(f"updates:一个未捕获的异常：{e}")

    def handle_update_results(self, update_info):
        """
        处理从工作线程传来的更新信息。
        """
        id = self.idvar.text()
        endpoint = update_info["endpoint"]
        value = update_info["value"]
        led_state = update_info["led_state"]

        try:
            if endpoint == 'temp':
                self.tempvar.setPlainText(str(value))
            elif endpoint == 'wet':
                self.wetvar.setPlainText(str(value))
            elif endpoint == 'airq':
                self.airq.setPlainText(str(value))
            elif endpoint == 'light':
                self.light.setPlainText(str(value))
            elif endpoint == 'fire':
                self.fire_state.setText("警告" if value >= 1 else "正常")
                if value>=1:
                    self.fire_state.setStyleSheet('QLabel{font: 75 14pt "黑体";color: rgb(255, 0, 0);}')
                else:
                    self.fire_state.setStyleSheet('QLabel{font: 75 14pt "黑体"}')
                self.warn_info.setText('火焰告警' + '     ' + time.asctime() if value >=1 else "")
            elif endpoint == 'fan':
                self.fan_state.setText("已打开" if value == 1 else "已关闭")
            elif endpoint == 'led1':
                self.led1.setText("已打开" if value == 1 else "已关闭")
            elif endpoint == 'led2':
                self.led2.setText("已打开" if value == 1 else "已关闭")
            elif endpoint == 'fan1':
                self.fan1_state.setText("已打开" if value == 1 else "已关闭")
            elif endpoint == 'rgb_red':
                self.set_rgb_led_state('red', value, led_state)
            elif endpoint == 'rgb_yellow':
                self.set_rgb_led_state('yellow', value, led_state)
            elif endpoint == 'rgb_green':
                self.set_rgb_led_state('green', value, led_state)
            elif endpoint == 'MWATERPUMP':
                self.waterpump.setText("已打开" if value == 1 else "已关闭")
            if led_state['red']=='Red灯':
                led_state["red"] = '红灯'
            if led_state['yellow']=='Yellow灯':
                led_state["yellow"] = '黄灯'
            if led_state['green']=='Green灯':
                led_state["green"] = '绿灯'
            self.update_rgb_led(led_state)
        except Exception as e:
            print(f"handle_update_results:一个未捕获的异常：{e}")

    def set_rgb_led(self, value, url_prefix, header, led_state):
        """
        根据车辆数量设置RGB LED状态。
        """
        if 0 < value <= 40:
            self.set_rgb_color('rgb_green', '1', url_prefix, header)
            self.set_rgb_color('rgb_red', '0', url_prefix, header)
            self.set_rgb_color('rgb_yellow', '0', url_prefix, header)
            led_state["green"] = "绿灯"
            led_state["red"] = ""
            led_state["yellow"] = ""
        elif 40 < value <= 60:
            self.set_rgb_color('rgb_green', '0', url_prefix, header)
            self.set_rgb_color('rgb_red', '0', url_prefix, header)
            self.set_rgb_color('rgb_yellow', '1', url_prefix, header)
            led_state["green"] = ""
            led_state["red"] = ""
            led_state["yellow"] = "黄灯"
        elif value > 60:
            self.set_rgb_color('rgb_green', '0', url_prefix, header)
            self.set_rgb_color('rgb_red', '1', url_prefix, header)
            self.set_rgb_color('rgb_yellow', '0', url_prefix, header)
            led_state["green"] = ""
            led_state["red"] = "红灯"
            led_state["yellow"] = ""

    def handle_water_pump(self, value, url_prefix, header):
        """
        根据水位设置水泵状态。
        """
        if value >= 70:
            self.set_water_pump('1', url_prefix, header)
        elif 0 <= value < 30:
            self.set_water_pump('0', url_prefix, header)

    def set_rgb_led_state(self, color, value, led_state):
        """
        设置RGB LED状态。
        """
        if value == 1:
            if color.capitalize() == 'red':
                led_state[color] = "红灯"
            if color.capitalize() == 'yellow':
                led_state[color] = "黄灯"
            if color.capitalize() == 'green':
                led_state[color] = "绿灯"
        else:
            led_state[color] = ""

    def update_rgb_led(self, led_state):
        """
        更新RGB LED显示。
        """
        # 构建RGB LED状态字符串
        rgb_status = ' '.join(filter(None, led_state.values()))
        if not rgb_status:
            rgb_status = "未启动"
        self.rygled.setText(rgb_status)

    def set_water_pump(self, value, url_prefix, header):
        """
        设置水泵状态。
        """
        url = url_prefix + 'MWATERPUMP'
        data = value
        thread = NetworkThread(url, data, header)
        thread.requestFinished.connect(self.handle_request_finished)
        thread.start()
    def set_rgb_color(self, endpoint, value, url_prefix, header):
        """
        设置RGB LED颜色。
        """
        url = url_prefix + endpoint
        data = value
        thread = NetworkThread(url, data, header)
        thread.requestFinished.connect(self.handle_request_finished)
        thread.start()

    def handle_request_finished(self, url, result):
        """
        处理网络请求完成后的结果。
        """
        print(f"请求 {url} {result}")


class PeriodicUpdateThread(QThread):
    """
    周期性更新线程。
    """
    updateFinished = pyqtSignal()

    def __init__(self, worker, interval_ms):
        super().__init__()
        self.worker = worker
        self.interval_ms = interval_ms

    def run(self):
        while not self.isInterruptionRequested():
            self.worker.run_updates()
            self.msleep(self.interval_ms)


class UpdateWorker(QObject):
    """
    更新工作线程。
    """
    update_finished = pyqtSignal(dict)  # 信号，用于通知UI线程更新已完成

    def __init__(self, font, device_id, params):
        super().__init__()
        self.font = font
        self.device_id = device_id
        self.params = params
        self.led_state = {"red": "", "yellow": "", "green": ""}

    def run_updates(self):
        """
        运行更新任务。
        """
        endpoints = [
            'temp', 'wet', 'airq', 'light', 'fire', 'fan', 'led1', 'led2', 'fan1',
            'rgb_red', 'rgb_yellow', 'rgb_green', 'MWATERPUMP'
        ]
        try:
            for endpoint in endpoints:
                full_url = f"{self.font}{self.device_id}/sensors/{endpoint}"
                with requests.get(full_url, params=self.params) as response:
                    data = response.json()
                    value = data["ResultObj"]["Value"]

                if endpoint.startswith('rgb_'):
                    color = endpoint.split('_')[1]
                    if value:
                        self.led_state[color] = f"{color.capitalize()}灯"
                    else:
                        self.led_state[color] = ""

                self.update_finished.emit({
                    "endpoint": endpoint,
                    "value": value,
                    "led_state": self.led_state.copy(),
                })
        except Exception as e:
            print(f"update worker:一个未捕获的异常：{e}")

class lora(QObject):
    """
    LoRa工作线程。
    """
    update_finished = pyqtSignal(dict)

    def __init__(self, font, params):
        super().__init__()
        self.font = font
        self.params = params
        self.led_state = {"red": "", "yellow": "", "green": ""}

    def is_valid_json(self, json_string):
        """
        检查字符串是否为有效的JSON。
        """
        try:
            json.loads(json_string)
        except Exception as e:
            return False
        return True

    def run_updates(self):
        """
        运行更新任务。
        """
        endpoints = ['car_number', 'm_water']
        try:
            for endpoint in endpoints:
                url = f"{self.font}1164823/sensors/{endpoint}"
                with requests.get(url, params=self.params) as response:
                    if self.is_valid_json(response.text):
                        data = response.json()
                        if data["ResultObj"] is not None:
                            value = data["ResultObj"]["Value"]
                            self.update_finished.emit({
                                "endpoint": endpoint,
                                "value": value,
                                "led_state": self.led_state.copy(),
                            })
        except Exception as e:
            print(f"lora worker:一个未捕获的异常：{e}")

class record_thread(QThread,WindowEvent):
    def __init__(self):
        super().__init__()

    def run(self):
        global st
        global stream_url
        camera = cv2.VideoCapture(stream_url)
        # 获取视频帧率
        frame_rate = camera.get(cv2.CAP_PROP_FPS)
        QApplication.instance().processEvents()
        if os.path.exists('./screenrecord'):
            try:

                savefile = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'screenrecord',
                                        time.strftime("%Y%m%d%H%M%S", time.localtime()) + ".mp4")
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(savefile, fourcc, frame_rate, (int(camera.get(3)), int(camera.get(4))))

                while True:
                    ret, frame = camera.read()
                    if ret:
                        out.write(frame)
                    if st:
                        st = False
                        break
            except Exception as e:
                print(f"record_thread:一个未捕获的异常：{e}")
            finally:
                out.release()
                camera.release()
        else:
            os.mkdir('./screenrecord')
            try:
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
            except Exception as e:
                print(f"record_thread:一个未捕获的异常：{e}")
            finally:
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
        try:
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
                QApplication.instance().processEvents()
        except Exception as e:
            print(f"camera_thread:一个未捕获的异常：{e}")

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
            self.errorOccurred.emit(f'monitor监控过程中发生错误: {str(e)}')
        finally:
            # 确保事件循环被关闭
            loop.close()

class Monitor(QObject):  # 使用QObject而非QThread
    monitoringError = pyqtSignal(str)

    def __init__(self, id_var, parent=None):
        super().__init__(parent)
        self.id_var = id_var
        self.token = token
        self._is_stopped=False

    async def fetch_device_status(self, id, session):
        font = 'http://api.nlecloud.com/Devices/Status'
        params = {'AccessToken': self.token, 'devIds': id}
        try:
            async with session.get(font, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                return data
        except aiohttp.ClientError as e:
            print(f"monitor网络错误: {e}")
            return None
        except Exception as e:
            print(f"monitor其他错误: {e}")
            return None

    async def check_fire_alert(self, id, session):
        font = 'http://api.nlecloud.com/devices/'
        end = '/sensors/fire'
        while True:
            try:
                async with session.get(font + str(id) + end, params=prarams) as response:
                    response.raise_for_status()
                    data = await response.json()
                    value = data["ResultObj"]["Value"]
                    if value >= 1:
                        async with aiofiles.open("record.txt", 'a+', encoding='UTF-8') as file:
                            await file.write('火焰告警' + '     ' + time.asctime() + '\n')
                        await asyncio.sleep(10)  # 使用asyncio的sleep而非time.sleep
            except aiohttp.ClientError as e:
                print(f"monitor网络错误: {e}")
                await asyncio.sleep(10)  # 重试间隔
            except Exception as e:
                print(f"monitor其他错误: {e}")
                await asyncio.sleep(10)  # 重试间隔

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

    def stop_monitoring(self):
        self._is_stopped = True
        self.worker_thread.quit()
        self.worker_thread.wait()

    async def async_monitor(self, id):
        async with aiohttp.ClientSession() as session:
            try:
                data = await self.fetch_device_status(id, session)
                if data is None:
                    return
                items = data["ResultObj"]
                if not items:
                    QMessageBox.warning(QWidget(), '提示', '无法找到此ID相关联的设备！')
                    return
                if items[0]["Name"] != '智慧隧道':
                    QMessageBox.warning(QWidget(), '提示', '你似乎使用了其他已有设备的ID，请使用适用于该项目名为"智慧隧道"的网关设备ID！')
                    return

                while not self._is_stopped:  # 添加一个停止标志
                    await self.check_fire_alert(id, session)
                    await asyncio.sleep(10)  # 使用asyncio的sleep而非time.sleep

                await self.check_fire_alert(id, session)
            except aiohttp.ClientError as e:
                print(f"monitor网络错误: {e}")
            except Exception as e:
                print(f"monitor其他错误: {e}")




if __name__ == '__main__':
    # 创建应用程序实例并传入命令行参数
    sys.setrecursionlimit(3000)
    app = QApplication(sys.argv)
    get_token()

    w=WindowEvent()
    w.ui.show()
    if not w.ui1.isVisible():
        w.ui1.close()
    if not w.ui.isVisible():
        w.ui.close()
    if not w.ui2.isVisible():
        w.ui2.close()
    # 启动事件循环
    sys.exit(app.exec_())