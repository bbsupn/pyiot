import base64
import re
import time
from itertools import groupby

import requests
import json
import os
import cv2
import serial
from PyQt5.QtSerialPort import QSerialPortInfo, QSerialPort
from requests.auth import HTTPDigestAuth
'''

from openpyxl import Workbook

'''

login_data={
    'Account':'13377815672',
    'Password':'114514'
}
response=requests.post('http://api.nlecloud.com/users/login',data=login_data)
data=response.json()
json_data=json.dumps(data)
items=json.loads(json_data)
token=items["ResultObj"]["AccessToken"]

with open('token.json', encoding='utf-8')as f:
    data_dict=json.load(f)
    f.close()

data_dict["AccessToken"]=token

with open('token.json','w',encoding='utf-8') as df:
    json.dump(data_dict,df)
    df.close()

with open("token.json", 'r', encoding='UTF-8') as load:
    prarams = json.load(load)
    token = prarams["AccessToken"]
    load.close()

'''
prarams={
    'AccessToken': 'FC8C0998F015A9B569F0FAFBB32DD521DDDA466B92D8727D27CC6B59F4ABF634BFF051D1DB3A725AA4FF01ADA9117BC197BFB5669580954FD02D04B7EF748CF5E2D83CB2E3D5A3301641BDC8693EDAC9FA71FF4F2A450F55DEBD226651B5160B44BD3F2C822F13539EC9B5688914B99909BA34D5AA634DB513565D04EB072F215AA673AD72BBEBA11DF5DAEEDA481E06D791C319A324EB10EB7E3E033E791A05EFE83D34961B76FFCFA70D018A86DAFDCF6AF9C6C6236305101F1136B475D3DD4BCD762B9A9E3651CEE704D29D438F30F0D18B8E9532A4FC4F94D640280BA02A'
}
response=requests.get(
    'http://api.nlecloud.com/Projects/1065176',
    params=prarams
)
print(response.text)

response=requests.get(
    'http://api.nlecloud.com/devices/1128871/Datas',
    params=prarams
)
data=response.json()
json_data=json.dumps(data)
items=json.loads(json_data)
print(items["ResultObj"]["DataPoints"])
header = ["ApiTag","PointDTO","Value","RecordTime"]

# 创建一个新的Workbook对象
wb = Workbook()
sheet = wb.active  # 明确获取活动工作表

header = ["ApiTag", "Value", "RecordTime"]
sheet.append(header)  # 现在可以安全地使用append了


if os.path.exists(r'data.xlsx'):
    os.remove(r'data.xlsx')

for row in items["ResultObj"]["DataPoints"]:
    tag = row["ApiTag"]
    # 确保PointDTO存在且是一个非空列表，并且取第一个元素作为示例
    if "PointDTO" in row and isinstance(row["PointDTO"], list) and row["PointDTO"]:
        point_dto = row["PointDTO"][0]
        # 直接提取Value和RecordTime的值，确保它们能被正确写入Excel
        value = str(point_dto.get("Value", ""))  # 使用str以防Value不是字符串
        time = str(point_dto.get("RecordTime", ""))  # 同上，确保RecordTime可以被写入
    else:
        value = ""
        time = ""

    # 现在将提取的值作为字符串写入Excel
    sheet.append([tag, value, time])

wb.save('data.xlsx')
'''

id = 1164821
prarams={
    'AccessToken': token
}

font = ' http://api.nlecloud.com/devices/'
response = requests.get(
    font+str(id)+'/sensors/'+'rgb_yellow',
    params=prarams
)
data = response.json()
print(data)
json_data = json.dumps(data)
items = json.loads(json_data)

'''
print(items)
list = items["ResultObj"]
if len(list)==0:
    print("empty")
else:
    value=list[0]["Tag"]
    print(value)
'''
'''
'''

value = items["ResultObj"]["Value"]
print(value)

'''
if 0 <= value < 1:
    print(value)
'''


'''
camera=ONVIFCamera('192.168.10.200',8080,'admin','admin')
media = camera.create_media_service()
profiles = media.GetProfiles()
ptz=camera.create_ptz_service()
class CameraHandler:
    def __init__(self, ip, port, usr, pwd,needSnapImg=True):
        self.ip = ip
        self.port = port
        self.usr = usr
        self.pwd = pwd
        self.profiles = profiles
        self.media=media
        self.needSnapImg=needSnapImg

    def get_rtsp(self):
        """
        获取RTSP地址等
        参考文档：https://www.onvif.org/onvif/ver10/media/wsdl/media.wsdl#op.GetStreamUri
        """
        result = []
        StreamSetup = {'Stream': 'RTP-Unicast', 'Transport': {'Protocol': 'RTSP'}}
        for profile in self.profiles:
            obj = self.media.create_type('GetStreamUri')
            obj.StreamSetup = StreamSetup
            obj.ProfileToken = profile.token
            res_uri = self.media.GetStreamUri(obj)['Uri']
            if 'rtsp://' in res_uri and '@' not in res_uri:
                res_uri = res_uri.replace('rtsp://', 'rtsp://%s:%s@' % (self.usr, self.pwd))
            result.append({
                'source': profile.VideoSourceConfiguration.SourceToken,
                'node': profile.PTZConfiguration.NodeToken if profile.PTZConfiguration is not None else None,
                'uri': res_uri,
                'token': profile.token,
                'videoEncoding': profile.VideoEncoderConfiguration.Encoding,
                'Resolution': serialize_object(profile.VideoEncoderConfiguration.Resolution),
                'img': self.snip_image(profile.token) if self.needSnapImg else None
            })
        sortedResult = sorted(result, key=lambda d: d['source'])
        groupData = groupby(sortedResult, key=lambda x: x['source'])
        return [{'source': key, 'data': [item for item in group]} for key, group in groupData]

    def snip_image(self, token=None):
        """
        截图，如果在浏览器上访问，可在img的src填入[data:image/jpeg;base64,%s]，%s处填写return值
        参考文档：https://www.onvif.org/onvif/ver10/media/wsdl/media.wsdl#op.GetSnapshotUri
        :param token:
        :return: base64转码之后的图片
        """
        token = token if token is not None else self.token
        res = self.media.GetSnapshotUri({'ProfileToken': token})
        auth = HTTPDigestAuth(self.usr, self.pwd)
        rsp = requests.get(res.Uri, auth=auth)
        return base64.b64encode(rsp.content).decode('utf-8')

camera_handler = CameraHandler('192.168.10.200', 8080, 'admin', 'admin')
resp=camera.devicemgmt.GetHostname()
print(str(resp.Name))
rtsp_info = camera_handler.get_rtsp()  # 直接获取返回的字典结构
url=''
# 确保rtsp_info是一个非空列表且至少有一个元素
if rtsp_info and rtsp_info[0].get("data"):  # 检查返回结构是否符合预期
    first_rtsp = rtsp_info[0]["data"][0]  # 假设我们只需要第一个source的第一个uri
    url = first_rtsp["uri"]
print(url)
'''
'''
def remove_parentheses(lst):
    return [item for sublist in lst for item in sublist] if any(isinstance(i, tuple) for i in lst) else lst

url='http://192.168.10.200:81/get_status.cgi?loginuse=admin&loginpas=admin'
req=requests.get(url)
pattern= re.compile("var (.+?)=\"(.+?)\";")
matches=re.findall(pattern,req.text)
print(matches)
res=remove_parentheses(matches)
print(res)
list=[]
for match in res:
    list.append(match)
print(list[1])
print(list[9])
'''


