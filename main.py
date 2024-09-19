import cv2
from io import BytesIO
# import RPi.GPIO as GPIO

import tkinter as tk
from tkinter import PhotoImage, messagebox

from PIL import Image, ImageTk
import threading
import time
from datetime import datetime

from PyCameraList.camera_device import list_video_devices

from tkinter import ttk

def resize_image(original_image, width, height):
    resized_image = original_image.resize((width, height), Image.ANTIALIAS)
    return resized_image


def update_camera_options():
    # 取得當前的 camera devices 列表
    cameras = list_video_devices()
    
    # 更新 Combobox 的選項
    box01['values'] = cameras
    box02['values'] = cameras
    box03['values'] = cameras
    
def Simpletoggle():
    result = messagebox.askyesno("確認", "確定要切換嗎？")
    
    try:
        if result:
            if toggle_button.config('text')[-1] == '儲存影片':
                toggle_button.config(text='關閉')

            else:
                toggle_button.config(text='儲存影片')
    except:
        pass

# =============================================================================
#         
# =============================================================================
def captureImageFromVideo0():
    
    camera = cv2.VideoCapture(99)
    index = 0
    while True:
        
        try:
            if camera.isOpened():

                ret, frame = camera.read()
     
                _, jpeg = cv2.imencode(".jpg", frame)
                
                if toggle_button.config('text')[-1] == '關閉' and index == 0:
                    
                    # 取得當前時間，並格式化為字串
                    current_time = datetime.now().strftime("%Y%m%d_%H%M")
                    video_filename = f'影片檔案/output01_{current_time}.avi'
    
                    # 設定影片儲存相關參數
                    fourcc = cv2.VideoWriter_fourcc(*'XVID')
                    out = cv2.VideoWriter(video_filename, fourcc, 30.0, (1920, 1080))
                    
                    index = 1
                    
                elif toggle_button.config('text')[-1] == '儲存影片': 
                    try:
                        if out is not None and index == 1:
                            out.release()
                            index = 0
                    except:
                        pass           
                else:
                    out.write(frame)
    
                original_image = Image.open(BytesIO(jpeg))
                
                photo_image = ImageTk.PhotoImage(original_image)

                resized_image = original_image.resize((480, 320))
                
                photo_image = ImageTk.PhotoImage(resized_image)


                
                image01Label.config(image=photo_image)
                image01Label.image = photo_image
                        
            else:
                time.sleep(1)
                camera.release()
                cameraIndex = box01.get()
                if cameraIndex != "":
                    camera = cv2.VideoCapture(int(cameraIndex[0]))
                    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        except:
            time.sleep(1)
            camera.release()
            if cameraIndex != "":
                cameraIndex = box01.get()
                camera = cv2.VideoCapture(int(cameraIndex[0]))
                camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
 
# =============================================================================
# 
# =============================================================================
def captureImageFromVideo2():
    camera = cv2.VideoCapture(99)
    index = 0
    while True:
        try:
            if camera.isOpened():
                ret, frame = camera.read()
                
                _, jpeg = cv2.imencode(".jpg", frame)

                if toggle_button.config('text')[-1] == '關閉' and index == 0:
                    
                    # 取得當前時間，並格式化為字串
                    current_time = datetime.now().strftime("%Y%m%d_%H%M")
                    video_filename = f'影片檔案/output02_{current_time}.avi'
    
                    # 設定影片儲存相關參數
                    fourcc = cv2.VideoWriter_fourcc(*'XVID')
                    out = cv2.VideoWriter(video_filename, fourcc, 30.0, (1920, 1080))
                    
                    index = 1
                    
                elif toggle_button.config('text')[-1] == '儲存影片': 
                    try:
                        if out is not None and index == 1:
                            out.release()
                            index = 0
                    except:
                        pass           
                else:
                    out.write(frame)
    
                original_image = Image.open(BytesIO(jpeg))
                
                photo_image = ImageTk.PhotoImage(original_image)

                resized_image = original_image.resize((480, 320))
                
                photo_image = ImageTk.PhotoImage(resized_image)
                
                image02Label.config(image=photo_image)
                image02Label.image = photo_image
                        
            else:
                time.sleep(1)
                camera.release()
                cameraIndex = box02.get()
                
                if cameraIndex != "":
                    camera = cv2.VideoCapture(int(cameraIndex[0]))
                    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        except:
            time.sleep(1)
            camera.release()
            if cameraIndex != "":
                cameraIndex = box02.get()
                camera = cv2.VideoCapture(int(cameraIndex[0]))
                camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
# =============================================================================
# 
# =============================================================================
def captureImageFromVideo4():
    
    camera = cv2.VideoCapture(99)
    
    index = 0
    while True:
        
        try:
            if camera.isOpened():
                
                ret, frame = camera.read()

                _, jpeg = cv2.imencode(".jpg", frame)

                if toggle_button.config('text')[-1] == '關閉' and index == 0:
                    
                    # 取得當前時間，並格式化為字串
                    current_time = datetime.now().strftime("%Y%m%d_%H%M")
                    video_filename = f'影片檔案/output03_{current_time}.avi'
    
                    # 設定影片儲存相關參數
                    fourcc = cv2.VideoWriter_fourcc(*'XVID')
                    out = cv2.VideoWriter(video_filename, fourcc, 30.0, (1920, 1080))
                    
                    index = 1
                    
                elif toggle_button.config('text')[-1] == '儲存影片': 
                    try:
                        if out is not None and index == 1:
                            out.release()
                            index = 0
                    except:
                        pass           
                else:
                    out.write(frame)
    
                original_image = Image.open(BytesIO(jpeg))
                
                photo_image = ImageTk.PhotoImage(original_image)

                resized_image = original_image.resize((480, 320))
                
                photo_image = ImageTk.PhotoImage(resized_image)
                
    
                image03Label.config(image=photo_image)
                image03Label.image = photo_image
                        
            else:
                time.sleep(1)
                camera.release()
                cameraIndex = box03.get()
                if cameraIndex != "":
                    camera = cv2.VideoCapture(int(cameraIndex[0]))  
                    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        except:
            time.sleep(1)
            camera.release()
            if cameraIndex != "":
                cameraIndex = box03.get()
                camera = cv2.VideoCapture(int(cameraIndex[0]))
                camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

# =============================================================================
# 
# =============================================================================
window = tk.Tk()
window.title('GUI')
window.geometry('1680x768')
window.configure(bg='#111111')
# window.resizable(False, False)

# 設置列和行權重
window.columnconfigure(0, weight=1)
window.columnconfigure(1, weight=1)
window.columnconfigure(2, weight=1)
    
window.rowconfigure(0, weight=10)
window.rowconfigure(1, weight=1)
window.rowconfigure(2, weight=1)

# =============================================================================
# 創建框架
# =============================================================================
image01Label = tk.Label(window, bg='#333333')
image02Label = tk.Label(window, bg='#333333')
image03Label = tk.Label(window, bg='#333333')


toggle_button = tk.Button(window, text = "儲存影片", command = Simpletoggle, 
                          font = ('Arial', 16, 'bold'), bg = '#555555', fg = 'white')

# 創建更新按鈕
update_button = tk.Button(window, text="更新 Camera Devices", command=update_camera_options, 
                          font = ('Arial', 16, 'bold'), bg = '#555555', fg = 'white')


box01 = ttk.Combobox(window, values=[], font = ('Arial', 16, 'bold'))
box02 = ttk.Combobox(window, values=[], font = ('Arial', 16, 'bold'))
box03 = ttk.Combobox(window, values=[], font = ('Arial', 16, 'bold'))

# =============================================================================
# 使用網格設置布局
# =============================================================================

image01Label.grid(row=0, column=0, padx=1, pady=1, sticky='nsew')
image02Label.grid(row=0, column=1, padx=1, pady=1, sticky='nsew')
image03Label.grid(row=0, column=2, padx=1, pady=1, sticky='nsew')

box01.grid(row=1, column=0, padx=1, pady=1, sticky='nsew')
box02.grid(row=1, column=1, padx=1, pady=1, sticky='nsew')
box03.grid(row=1, column=2, padx=1, pady=1, sticky='nsew')

update_button.grid(row=2, column=0, padx=1, pady=1, sticky='nsew')

toggle_button.grid(row=2, column=1, padx=1, pady=1, sticky='nsew')
# toggle_button02.grid(row=3, column=1, padx=1, pady=1, sticky='nsew')
# toggle_button03.grid(row=3, column=2, padx=1, pady=1, sticky='nsew')



# =============================================================================
# 主循環
# =============================================================================

runVideo0 = threading.Thread(target = captureImageFromVideo0)
runVideo2 = threading.Thread(target = captureImageFromVideo2)
runVideo4 = threading.Thread(target = captureImageFromVideo4)

runVideo0.start()
runVideo2.start()
runVideo4.start()


window.mainloop()
