import requests
import urllib.parse as urlparse
import json
import pandas as pd
import numpy as np
import csv
import time
import schedule
import datetime
import os
import sys

# 코드 실행 카운트 총 45번(2시간, 4분간격) 돌면 종료
cnt = 0

#nodeid and routeid load
serviceKey_file = pd.read_csv("key.csv")
routeId_BusStop = pd.read_csv("stop_info.csv") 
nodeId = routeId_BusStop["nodeid"]
routeId = routeId_BusStop["routeid"]

# key index
key_index = 0 

# params
cityCode = 34010 
numOfRows = 10 
_type = "json"

file_name = datetime.datetime.now().strftime('%Y_%m_%d') + "_test_output.csv"

# traffic save
def set_traffic():
    global key_index
    
    serviceKey_file.loc[key_index, "traffic"] = int(serviceKey_file["traffic"][key_index]) + 1 
    serviceKey_file.to_csv("key.csv", index=False, mode='w', encoding='utf-8-sig')

#check traffic
def check_traffic():
    global key_index
    set_traffic()
    
    #check traffic
    while( serviceKey_file['traffic'][key_index] > 950 ):
        key_index += 1
        print("traffic over -> key change")
    print("key_index: "+ str(key_index))   
    
    #serviceKey end..
    if(key_index >= 9):
        sys.exit("Error: there arn't usable traffic")
    else:    
        print("key: " + serviceKey_file['serviceKey'][key_index])
        print("traffic: " + str(serviceKey_file['traffic'][key_index]))

def save_data(data):
    df = pd.DataFrame(data = [data], columns = ("curr_date","curr_time", "routeno", "routeid", "nodeid", "nodenm", "arrtime", "arrprevstationcnt"))
    if not os.path.exists(file_name):
        df.to_csv(file_name, index=False, mode='w', encoding='utf-8-sig')
    else:
        df.to_csv(file_name, index=False, mode='a', encoding='utf-8-sig', header=False)

#url request
def get_request(params):
    global key_index
    url = "http://openapi.tago.go.kr/openapi/service/ArvlInfoInqireService/getSttnAcctoSpcifyRouteBusArvlPrearngeInfoList"
    params = urlparse.urlencode(params)
    url += '?' +"serviceKey=" + serviceKey_file['serviceKey'][key_index] + "&" + params
    return url
        
def get_data():
    global key_index
    global cnt
    print("cnt: " + str(cnt))
    
    # 120분 / 4분 = 30번씩
    if(cnt > 30): 
        sys.exit("================================ End ================================")
    else: 
        cnt += 1
        
    for nl, rl in zip(nodeId, routeId):
        params = {'cityCode':cityCode, 'nodeId': nl, 'routeId':rl, '_type': _type}
        try:
            check_traffic() # check traffic, if 950 < key -> change key
            
            date_time = datetime.datetime.now() 
            curr_date = date_time.strftime('%Y-%m-%d')
            curr_time = date_time.strftime('%H:%M:%S')
            
            request_query = get_request(params) #get url
            print('request_query:', request_query)
            
            response = requests.get(url = request_query) #get data
            print("response: " + str(response))
            
            r_dict = json.loads(response.text) 
            r_response = r_dict.get("response") 
            r_body = r_response.get("body") 
            r_items = r_body.get("items") 
            r_item = r_items.get("item") 
            
        except AttributeError as err:
            r_header = r_response.get("header")
            r_item = []
            e = r_header["resultMsg"]
            if(e == "NORMAL SERVICE."):
                print("NO DATA")
            else: 
                print("API ERROR: " + e)
            
        for item in r_item: 
            routeno = item.get("routeno")
            routeid = item.get("routeid")
            nodeid = item.get("nodeid")
            nodenm = item.get("nodenm")
            arrtime = item.get("arrtime")
            arrprevstationcnt = item.get("arrprevstationcnt") 

            data= [curr_date, curr_time, routeno, routeid, nodeid, nodenm, arrtime, arrprevstationcnt]
            save_data(data) 
            print("SAVE DATA")
            
#main#
if __name__ == "__main__":
    schedule.clear()
    print("코드 실행!")
    # 정각에 코드 시작하기
    get_data()
    #실행 이후 4분마다 data request and save data
    schedule.every(4).minutes.do(get_data)

    while True:  
        schedule.run_pending()
        time.sleep(1)
        