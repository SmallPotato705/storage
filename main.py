import tkinter as tk
from tkinter import PhotoImage, messagebox
import csv
import os
import requests
from PIL import Image, ImageTk
from io import BytesIO
from paddleocr import PaddleOCR
from pyzbar.pyzbar import decode
from pyzbar.pyzbar import ZBarSymbol
import threading
import time
import serial
from datetime import datetime
from tkinter import ttk
from bs4 import BeautifulSoup
import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import sys
import uvicorn
from uvicorn import Server
# =============================================================================
# 3.3V                  |  5V
#                       |  5V
#                       |  GND
# =============================================================================
                      
# =============================================================================
# GPIO 6  - Port01 Arm  |  GPIO 12   
# GPIO 13 - Port02 Arm  |  GPIO GND
# GPIO 19 - Port03 Arm  |  GPIO 16  - Port01 CST
# GPIO 26 - USC         |  GPIO 20  - Port02 CST
# GND                   |  GPIO 21  - Port03 CST   
# =============================================================================

# =============================================================================
# 
# =============================================================================
THRESHOLD = 3
DELAYTIME = 1
timeInterval = 120
OA_TEST = False

img_path = "image.jpg"
img_path02 = "image02.jpg"
img_path03 = "image03.jpg"
img_path04 = "image04.jpg"

# =============================================================================
#  URL
# =============================================================================
if OA_TEST == True:
    urlVideo = ["http://172.20.10.2:8000/Video0", "http://172.20.10.2:8000/Video2", "http://172.20.10.2:8000/Video4", "http://172.20.10.2:8000/Arm"]
    # urlGpioCST = ["http://172.20.10.2:8000/gpio21", "http://172.20.10.2:8000/gpio20", "http://172.20.10.2:8000/gpio16", "http://172.20.10.2:8000/gpio12"]
    
    urlGpioArmStatus = ["http://172.20.10.2:8000/gpio06", "http://172.20.10.2:8000/gpio13", "http://172.20.10.2:8000/gpio19", "http://172.20.10.2:8000/gpio26"]
    urlGpioArmSignal = ["http://172.20.10.2:8000/gpio23", "http://172.20.10.2:8000/gpio24"]
    
else:
    urlVideo = ["http://192.168.68.121:8000/Video0", "http://192.168.68.121:8000/Video2", "http://192.168.68.121:8000/Video4", "http://172.20.10.121:8000/Arm"]
    # urlGpioCST = ["http://192.168.68.121:8000/gpio21", "http://192.168.68.121:8000/gpio20", "http://192.168.68.121:8000/gpio16", "http://172.20.10.121:8000/gpio12"]
    
    urlGpioArmStatus = ["http://192.168.68.121:8000/gpio06", "http://192.168.68.121:8000/gpio13", "http://192.168.68.121:8000/gpio19", "http://172.20.10.121:8000/gpio26"]
    urlGpioArmSignal = ["http://192.168.68.121:8000/gpio23", "http://192.168.68.121:8000/gpio24"]

# =============================================================================
# 
# =============================================================================
paddleOCR = PaddleOCR(show_log = False, det = False, lang="en", use_angle_cls=True)
paddleOCR = PaddleOCR()

def get_cassette_id(img_path):
    paddleResult = paddleOCR.ocr(img_path, cls=False)

    if paddleResult[0] != None:
        return paddleResult[0][0][1][0]

    return None

# =============================================================================
# 
# =============================================================================
SERIAL_PORT = "COM4"

relay_on = bytearray(b"\xA0\x01\x01\xA2")
relay_off = bytearray(b"\xA0\x01\x00\xA1")

try:
    ser = serial.Serial(SERIAL_PORT, 9600, timeout = 0)
    ser.write(relay_off)
    # ser.close()
except:
    print("Serial Port 異常")

# =============================================================================
# 
# =============================================================================
app = FastAPI()

@app.post("/get_Port01_Mode")
def get_Port01_Mode():
    mode = mode01Label.cget("text")
    print(mode)
    return mode

@app.post("/get_Port02_Mode")
def get_Port02_Mode():
    mode = mode02Label.cget("text")
    print(mode)
    return mode

@app.post("/get_Port03_Mode")
def get_Port03_Mode():
    mode = mode03Label.cget("text")
    print(mode)
    return mode

def run_fastapi():
    
    uvicorn.run(app, host="192.168.68.112", port=8000)
    

# def on_closing():
#     server = Server()
#     server.should_exit  = True
#     sys.exit()
#     window.destroy()
    
def process_image(index, image_label, cstid_label, lotid_label, mode_label, countSameAnswer, lastCasID, lotId):
    if index != "Null":
        for i in range(THRESHOLD+1):
            try:
                response = requests.get(urlVideo[int(index)])
                if response.status_code == 200:
                    image_bytes = response.content
                    original_image = Image.open(BytesIO(image_bytes))
                    resized_image = original_image  # 可以選擇調整大小
                    photo_image = ImageTk.PhotoImage(resized_image)
                    image_label.config(image=photo_image)
                    image_label.image = photo_image
    
                    img_path = "temp_image" + str(index) + ".jpg"
               
                    resized_image.save(img_path)
                    
                    CassetteId = []
                    detecteBarCode = decode(resized_image, symbols=[ZBarSymbol.CODE39])
                    
                    if detecteBarCode != []:
                        for barcode in detecteBarCode:
                            barcodeResult = barcode.data.decode('utf-8')
                            CassetteId = barcodeResult
                    else:
                        CassetteId = get_cassette_id(img_path)
    
                    current_time = datetime.now().strftime("%Y%m%d%H%M")
                    
                    if CassetteId != None:
                        if len(CassetteId) == 6 and lastCasID == CassetteId:
                            countSameAnswer += 1
                        else:
                            countSameAnswer = 0
                        
                    lastCasID = CassetteId

                    if countSameAnswer == THRESHOLD:
                        lotId = save_and_display_results(CassetteId, resized_image, current_time, cstid_label, lotid_label, mode_label)
                        print(lotId)
                        mode = set_Mode(lotId, mode_label)
                        
                        print(mode)
    
                        print("CassetteId:", CassetteId)
                        
                    elif countSameAnswer > THRESHOLD:
                        mode = set_Mode(lotId, mode_label)
                        print(mode)
        
                    os.remove(img_path)
                    
                    return countSameAnswer, lastCasID, lotId
                else:
                    handle_error(cstid_label, lotid_label, mode_label, "無法獲取照片")
                    image_label.config(image=blank_image)

            except Exception as e:
                handle_error(cstid_label, lotid_label, mode_label, "異常: " + str(e))
                image_label.config(image=blank_image)
    else:
        handle_error(cstid_label, lotid_label, mode_label, "Nan")
        image_label.config(image=blank_image)
        
    lastCasID = ""
    countSameAnswer = 0
    lotId = "Nan"
    
    return countSameAnswer, lastCasID, lotId



def save_and_display_results(CassetteId, resized_image, current_time, cstid_label, lotid_label, mode_label):
    """保存結果並顯示在標籤上"""
    
    cstid_label.config(text=f"CST ID: {CassetteId}")
    
    
    try:
        # url = "http://l3cedaserver.corpnet.auo.com/L5Report/Array/LotInquery/lotinfo.asp?casetid=" + str(CassetteId) + "&lotid=&submit1=Query"
        url="http://10.84.70.169:8080/cst2lot"

        payload = json.dumps({
          "CST":[CassetteId],
        })
        
        
        headers = {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
        
        response = requests.request("POST", url, headers=headers, data=payload ,proxies={"http":"http://10.84.66.6:8080"})
        
        if(response.status_code==200):
            print("Post Success!")
            dataBytes = response.content
            dataStr = dataBytes.decode()
            dataJson = json.loads(dataStr)
            
            if dataJson["LOT"] != "None":
                LotID = dataJson["LOT"]
                lotid_label.config(text="LOT ID: "+str(LotID))
                resized_image.save(f"辨識結果/Camera_{current_time}_{CassetteId}_{LotID}.jpg")
                return LotID
       
        LotID = "搜尋不到"
        lotid_label.config(text="LOT ID: 搜尋不到")
        resized_image.save(f"辨識結果/Camera_{current_time}_{CassetteId}_{LotID}.jpg")
        return "Nan"
        
    except Exception as e:
        lotid_label.config(text="LOT ID: 網址有錯")
        mode_label.config(text="MODE: Nan")
        cstid_label.config(text="CST ID: Nan")
        print(e)
        return "Nan"
    
def set_Mode(lotId, mode_label):

    if lotId != "Nan":
        for cleanList in Lstbox1.get(0, tk.END):
            for i in range(len(lotId) - 1):
                if cleanList == lotId[0 + i : 2 + i]:
                    mode_label.config(text="MODE: 一般模式 (N+)")
                    
                    return "MODE: 一般模式 (N+)"
                
    mode_label.config(text="MODE: 清洗模式 (非N+)")
    
    return "MODE: 清洗模式 (非N+)"


def handle_error(cstid_label, lotid_label, mode_label, message):
    """處理錯誤情況"""
    cstid_label.config(text="CST ID: Nan")
    lotid_label.config(text="LOT ID: Nan")
    mode_label.config(text="MODE: Nan")
    print(message)
    # 這裡假設 blank_image 已經定義
    # image_label.config(image=blank_image)

def captureImageFromVideo0():
    lastCasID = ""
    countSameAnswer = 0
    lotId = "Nan"
    while True:
        Index = box01.get()
        countSameAnswer, lastCasID, lotId = process_image(Index, image01Label, cstid01Label, lotid01Label, mode01Label, countSameAnswer, lastCasID, lotId)
        time.sleep(DELAYTIME)

def captureImageFromVideo2():
    lastCasID = ""
    countSameAnswer = 0
    lotId = "Nan"
    while True:
        Index = box02.get()

        countSameAnswer, lastCasID, lotId = process_image(Index, image02Label, cstid02Label, lotid02Label, mode02Label, countSameAnswer, lastCasID, lotId)
        time.sleep(DELAYTIME)

def captureImageFromVideo4():
    lastCasID = ""
    countSameAnswer = 0
    lotId = "Nan"
    while True:
        Index = box03.get()
        
        countSameAnswer, lastCasID, lotId = process_image(Index, image03Label, cstid03Label, lotid03Label, mode03Label, countSameAnswer, lastCasID, lotId)
        time.sleep(DELAYTIME)
        
        
def armStatus():
    
    last_reading_time = time.time()
    
    while True:
        
        port01API = requests.get(urlGpioArmStatus[0])
        port02API = requests.get(urlGpioArmStatus[1])
        port03API = requests.get(urlGpioArmStatus[2])
        uscAPI = requests.get(urlGpioArmStatus[3])
        
        if port01API.status_code == 200 and port02API.status_code == 200 and port03API.status_code == 200 and uscAPI.status_code == 200:
            port01gpioRaw = port01API.content
            port01gpioDecode = int(port01gpioRaw.decode('utf-8').split(":")[1].strip())
            
            port02gpioRaw = port02API.content
            port02gpioDecode = int(port02gpioRaw.decode('utf-8').split(":")[1].strip())
            
            port03gpioRaw = port03API.content
            port03gpioDecode = int(port03gpioRaw.decode('utf-8').split(":")[1].strip())
            
            uscgpioRaw = uscAPI.content
            uscgpioDecode = int(uscgpioRaw.decode('utf-8').split(":")[1].strip())
            
            
                
            if port01gpioDecode == 1:
                last_reading_time = time.time()
                text = mode01Label.cget("text")
                resultIndexLabel.config(text = "Port01: ")
                resultLabel.config(text = text)
                
            elif port02gpioDecode == 1:
                last_reading_time = time.time()
                text = mode02Label.cget("text")
                resultIndexLabel.config(text = "Port02: ")
                resultLabel.config(text = text)
                
            elif port03gpioDecode == 1:
                last_reading_time = time.time()
                text = mode03Label.cget("text")
                resultIndexLabel.config(text = "Port03: ")
                resultLabel.config(text = text)
                
            elif uscgpioDecode == 1:
                last_reading_time = time.time()
                text = resultLabel.cget("text")
                
                try:
                    if text == "MODE: 清洗模式 (非N+)":
                        if toggle_button.config('text')[-1] == '【關閉】PLC功能':
                            ser.write(relay_off)
                        print("MODE: 清洗模式 (非N+)")
                        
                    elif text == "MODE: 一般模式 (N+)":
                        if toggle_button.config('text')[-1] == '【關閉】PLC功能':
                            ser.write(relay_on)
                        print("MODE: 一般模式 (N+)")
                        
                    elif text == "MODE: Nan":
                        if toggle_button.config('text')[-1] == '【關閉】PLC功能':
                            ser.write(relay_off)
                        print("MODE: Nan")

                except:
                    print("Serial Port 異常")
            else:
                current_time = time.time()
                
                if current_time - last_reading_time >= timeInterval:
                    
                    resultIndexLabel.config(text = "Result: ")
                    resultLabel.config(text = "Nan")
        
        time.sleep(0.2)

def ini():
    Lstbox1.delete(0, tk.END)
    with open('清洗清單.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            Lstbox1.insert(tk.END, row[0])

def ins():
    if entry.get() != '':
        if Lstbox1.curselection() == ():
            Lstbox1.insert(tk.END, entry.get())
        else:
            Lstbox1.insert(Lstbox1.curselection(), entry.get())

def delt():
    if Lstbox1.curselection() != ():
        Lstbox1.delete(Lstbox1.curselection())


# =============================================================================
# 
# =============================================================================
def Simpletoggle():
    result = messagebox.askyesno("確認", "確定要切換嗎？")
    
    try:
        # ser = serial.Serial(SERIAL_PORT, 9600, timeout = 0)
        
        if result:
            
            if toggle_button.config('text')[-1] == '【開啟】PLC功能':
                toggle_button.config(text='【關閉】PLC功能')
                # ser.write(relay_on)
                # ser.close()
                
            else:
                toggle_button.config(text='【開啟】PLC功能')
                # ser.write(relay_off)
                # ser.close()
    except:
        print("Serial Port 異常")
        
        

def ManualSimpletoggle():
    result = messagebox.askyesno("確認", "確定要切換嗎？")
    
    try:
        # ser = serial.Serial(SERIAL_PORT, 9600, timeout = 0)
        
        if result:
            
            if Manual_toggle_button.config('text')[-1] == '手動開啟':
                Manual_toggle_button.config(text='手動關閉')
                ser.write(relay_on)
                # ser.close()
                
            else:
                Manual_toggle_button.config(text='手動開啟')
                ser.write(relay_off)
                # ser.close()
    except:
        print("Serial Port 異常")

# if __name__ == "__main__":



# =============================================================================
# 
# =============================================================================

window = tk.Tk()
window.title('GUI')
window.geometry('1440x760+0+0')
window.configure(bg='#111111')
window.resizable(False, False)

blank_image = tk.PhotoImage(width=1, height=1)


# 設置列和行權重
for i in range(3):
    window.columnconfigure(i, weight=4)

window.rowconfigure(0, weight=5)
for i in range(1, 6):
    window.rowconfigure(i, weight=1)

# =============================================================================
# 創建框架
# =============================================================================

frameModifyCleanList = tk.Frame(window, relief=tk.RAISED, bg='#333333')
frameGPIO = tk.Frame(window, relief=tk.RAISED, bg='#333333')
framePredict = tk.Frame(window, relief=tk.RAISED, bg='#333333')
frameResult = tk.Frame(window, relief=tk.RAISED, bg='#333333')

image01Label = tk.Label(window, width=10, height=20, bg='#333333')

image02Label = tk.Label(window, width=10, height=20, bg='#333333')

image03Label = tk.Label(window, width=10, height=20, bg='#333333')


cstid01Label = tk.Label(window, bg='#333333', fg='white', font=('Arial', 16, 'bold'), text='CST ID: Nan')
cstid02Label = tk.Label(window, bg='#333333', fg='white', font=('Arial', 16, 'bold'), text='CST ID: Nan')
cstid03Label = tk.Label(window, bg='#333333', fg='white', font=('Arial', 16, 'bold'), text='CST ID: Nan')

resultLabel = tk.Label(frameResult, bg='#333333', fg='white', font=('Arial', 16, 'bold'), text='Nan')
resultIndexLabel = tk.Label(frameResult, bg='#333333', fg='white', font=('Arial', 16, 'bold'), text='Result: ')

lotid01Label = tk.Label(window, bg='#333333', fg='white', font=('Arial', 16, 'bold'), text='LOT ID: Nan')
lotid02Label = tk.Label(window, bg='#333333', fg='white', font=('Arial', 16, 'bold'), text='LOT ID: Nan')
lotid03Label = tk.Label(window, bg='#333333', fg='white', font=('Arial', 16, 'bold'), text='LOT ID: Nan')

mode01Label = tk.Label(window, bg='#333333', fg='white', font=('Arial', 16, 'bold'), text='MODE: Nan')
mode02Label = tk.Label(window, bg='#333333', fg='white', font=('Arial', 16, 'bold'), text='MODE: Nan')
mode03Label = tk.Label(window, bg='#333333', fg='white', font=('Arial', 16, 'bold'), text='MODE: Nan')

toggle_button = tk.Button(frameModifyCleanList, text = "【開啟】PLC功能", command = Simpletoggle, 
                          font = ('Arial', 16, 'bold'), bg = '#555555', fg = 'white', justify='center')

Manual_toggle_button = tk.Button(frameModifyCleanList, text = "手動開啟", command = ManualSimpletoggle, 
                          font = ('Arial', 16, 'bold'), bg = '#555555', fg = 'white', justify='center')


NanLabel01 = tk.Label(window, bg='#333333', fg='white', font=('Arial', 16, 'bold'), text='')
NanLabel02 = tk.Label(window, bg='#333333', fg='white', font=('Arial', 16, 'bold'), text='')


Lstbox1 = tk.Listbox(window, bg='#333333', fg='white', font=('Arial', 16), selectbackground='#999999', justify='center')
entry = tk.Entry(frameModifyCleanList, font=('Arial', 16), bg='#333333', fg='white')
initButton = tk.Button(frameModifyCleanList, text='讀取csv檔案', command=ini, font=('Arial', 16, 'bold'), bg='#555555', fg='white', justify='center')
insertButton = tk.Button(frameModifyCleanList, text='新增', command=ins, font=('Arial', 16, 'bold'), bg='#555555', fg='white', justify='center')
delButton = tk.Button(frameModifyCleanList, text='刪除', command=delt, font=('Arial', 16, 'bold'), bg='#555555', fg='white', justify='center')

box01 = tk.ttk.Combobox(window, values=["0", "1", "2", "3", "Null"], font = ('Arial', 16, 'bold'))
box01.set("Null")
box02 = tk.ttk.Combobox(window, values=["0", "1", "2", "3", "Null"], font = ('Arial', 16, 'bold'))
box02.set("Null")
box03 = tk.ttk.Combobox(window, values=["0", "1", "2", "3", "Null"], font = ('Arial', 16, 'bold'))
box03.set("Null")





# =============================================================================
# 使用網格設置布局
# =============================================================================
image01Label.grid(row=0, column=0, padx=1, pady=1, sticky='nsew')
image02Label.grid(row=0, column=1, padx=1, pady=1, sticky='nsew')
image03Label.grid(row=0, column=2, padx=1, pady=1, sticky='nsew')


cstid01Label.grid(row=1, column=0, padx=1, pady=1, sticky='nsew')
cstid02Label.grid(row=1, column=1, padx=1, pady=1, sticky='nsew')
cstid03Label.grid(row=1, column=2, padx=1, pady=1, sticky='nsew')


lotid01Label.grid(row=2, column=0, padx=1, pady=1, sticky='nsew')
lotid02Label.grid(row=2, column=1, padx=1, pady=1, sticky='nsew')
lotid03Label.grid(row=2, column=2, padx=1, pady=1, sticky='nsew')


mode01Label.grid(row=3, column=0, padx=1, pady=1, sticky='nsew')
mode02Label.grid(row=3, column=1, padx=1, pady=1, sticky='nsew')
mode03Label.grid(row=3, column=2, padx=1, pady=1, sticky='nsew')


Lstbox1.grid(row=4, column=0, padx=1, pady=1, sticky='nsew')
frameModifyCleanList.grid(row=4, column=1, padx=1, pady=1, sticky='nsew')
frameGPIO.grid(row=4, column=2, padx=1, pady=1, sticky='nsew')
framePredict.grid(row=4, column=3, padx=1, pady=1, sticky='nsew')

box01.grid(row=5, column=0, padx=1, pady=1, sticky='nsew')
box02.grid(row=5, column=1, padx=1, pady=1, sticky='nsew')
box03.grid(row=5, column=2, padx=1, pady=1, sticky='nsew')


# =============================================================================
# frameModifyCleanList
# =============================================================================
entry.pack(fill='x', padx=1, pady=5)
initButton.pack(fill='x', padx=1, pady=5)
insertButton.pack(fill='x', padx=1, pady=5)
delButton.pack(fill='x', padx=1, pady=5)
Manual_toggle_button.pack(fill='x', padx=1, pady=5)
toggle_button.pack(fill='x', padx=1, pady=5)


resultIndexLabel.pack(side = "left")
resultLabel.pack(side = "left")


# =============================================================================
# 主循環
# =============================================================================

runVideo0 = threading.Thread(target = captureImageFromVideo0)
# runVideo2 = threading.Thread(target = captureImageFromVideo2)
# runVideo4 = threading.Thread(target = captureImageFromVideo4)
# runArm = threading.Thread(target = armStatus)

fastapi_thread = threading.Thread(target=run_fastapi)


runVideo0.start()
# runVideo2.start()
# runVideo4.start()
# runArm.start()
fastapi_thread.start()

# window.protocol("WM_DELETE_WINDOW", on_closing)
window.mainloop()


