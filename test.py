# import datetime

# timestamp = begin = datetime.datetime.strptime("21-05-26 10:00", "%y-%m-%d %H:%M")
# now = datetime.datetime.today()
# diff = (now - timestamp).total_seconds()
# if diff > 60*60:
#     diff_str = str(int(diff/3600)) + " H "+ str(int((diff%3600)/60)) +" Min"
# else:
#     diff_str = str(int(diff/60)) + " Min"
# print(diff_str)

# import json

# dat1 = {"chargepoint": {"id": 1, "name": "Hof", "rfid": 1234}}

# dat2 = {"chargepoint": {"id": 2, "name": "Hof", "rfid": 1234}}

# with open("test_file.json", "a") as outfile:
#     json.dump(dat1, outfile)

# with open("test_file.json", "a") as outfile:
#     json.dump(dat2, outfile)

# data = [json.loads(line) for line in open('data.json', 'r')]
# print(data)

# import json

# data = {}
# data['people'] = []
# data['people'].append({
#     'name': 'Scott',
#     'website': 'stackabuse.com',
#     'from': 'Nebraska'
# })
# data['people'].append({
#     'name': 'Larry',
#     'website': 'google.com',
#     'from': 'Michigan'
# })
# data['people'].append({
#     'name': 'Tim',
#     'website': 'apple.com',
#     'from': 'Alabama'
# })

# with open('data.json', 'a') as outfile:
#     json.dump(data, outfile)

# with open('data.json') as json_file:
#     data = json.load(json_file)
#     for p in data['people']:
#         print('Name: ' + p['name'])
#         print('Website: ' + p['website'])
#         print('From: ' + p['from'])
#         print('')

# import json
# import fileinput

# add_list = "["+'\n'+"]"
# add_dict = { 'word':50, 'line':10, 'page':5 }

# with open ('mydatafile.json', 'a') as jf:
#     jf.write(add_list)

# # with open ('mydatafile.json', 'a') as jf:
# #     dict = json.dumps(add_dict)
# #     jf.write('\n')
# #     jf.write(dict)

# for line in fileinput.FileInput('mydatafile.json',inplace=1):
#     if "]" in line:
#         dict = json.dumps(add_dict)
#         line=line.replace(line, dict+line)
#     print(line,)
    
# for line in reversed(fileinput.FileInput('mydatafile.json',inplace=1)):
#     if "]" in line:
#         dict = json.dumps(add_dict)
#         line=line.replace(line, dict+line)
#     print(line,)

# with open('mydatafile.json', 'r') as jf:
#     lines = jf.readlines()
# print(lines)

# import json
# import os

# add_list = [{"tset":5}]
# add_dict = { 'word':50, 'line':10, 'page':5 }

# with open ('mydatafile.json', 'w') as jf:
#     list = json.dumps(add_list)
#     jf.write(list)
#     jf.seek(0, os.SEEK_END)              # seek to end of file; f.seek(0, 2) is legal
#     a = jf.tell()
#     print(a)

# with open ('mydatafile.json', 'a+') as jf:
#     jf.seek(0, os.SEEK_END)              # seek to end of file; f.seek(0, 2) is legal
#     a = jf.tell()
#     print(a)
#     jf.seek((jf.tell() - 2), os.SEEK_SET)
#     b = jf.tell()
#     print(b)
#     dict = json.dumps(add_dict)
#     jf.write(","+'\n')
#     jf.write(dict)
    

# with open('mydatafile.json', 'r') as jf:
#     lines = jf.readlines()
# print(lines)

# import os

# with open("test2.txt", "w") as f:
#     f.write("abc")

# with open("test2.txt", "a+") as f:
#     f.seek(0, os.SEEK_END)              # seek to end of file; f.seek(0, 2) is legal
#     a = f.tell()
#     print(a)
#     f.seek((f.tell() - 2), os.SEEK_SET)
#     b = f.tell()
#     print(b)
#     f.write("d")

# with open("test2.txt", "r") as f:
#     lines = f.readlines()
# print(lines)

# Python program to demonstrate
# seek() method
  
  
# # Opening "GfG.txt" text file
# f = open("GfG.txt", "a+")
  
# # Second parameter is by default 0
# # sets Reference point to twentieth 
# # index position from the beginning
# f.seek(20)
  
# # prints current postion
# print(f.tell())
# f.write("aa")
# print(f.readline()) 
# f.close()

# # Opening "GfG.txt" text file
# f = open("GfG.txt", "r")
  
# # Second parameter is by default 0
# # sets Reference point to twentieth 
# # index position from the beginning
# f.seek(20)
  
# # prints current postion
# print(f.tell())
  
# print(f.readline()) 
# f.close()

# from random import random
# import threading
# import time

# result = None
# result_available = threading.Event()

# def background_calculation():
#     # here goes some long calculation
#     #time.sleep(random() * 5 * 60)

#     # when the calculation is done, the result is stored in a global variable
#     global result
#     result = 42
#     time.sleep(15)
#     result_available.set()

#     # do some more work before exiting the thread
    

# def main():
#     thread = threading.Thread(target=background_calculation)
#     thread.start()

#     # wait here for the result to be available before continuing
#     result_available.wait(10.2)

#     print('The result is', result)

# main()

# import json
# import pathlib

# add_list = {"tset":5}
# add_dict = { 'word':50, 'line':10, 'page':5 }

# pathlib.Path('./data').mkdir(mode = 0o755, parents=True, exist_ok=True)

# try:
#     with open("./data/replayScript.json", "r") as jsonFile:
#         data = json.load(jsonFile)
# except FileNotFoundError:
#     with open("./data/replayScript.json", "w") as jsonFile:
#         json.dump([], jsonFile)
#     with open("./data/replayScript.json", "r") as jsonFile:
#         data = json.load(jsonFile)
# data.append(add_list)
# with open("./data/replayScript.json", "w") as jsonFile:
#     json.dump(data, jsonFile)

# try:
#     with open("/data/replayScript.json", "r") as jsonFile:
#         data = json.load(jsonFile)
# except FileNotFoundError:
#     with open("/data/replayScript.json", "w") as jsonFile:
#         json.dump([], jsonFile)
# data.append(add_dict)
# with open("/data/replayScript.json", "w") as jsonFile:
#     json.dump(data, jsonFile)

# with open("/data/replayScript.json", "r") as jsonFile:
#     data2 = json.load(jsonFile)
# print(data2)