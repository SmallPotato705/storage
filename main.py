import cv2
from io import BytesIO
import tkinter as tk
from tkinter import PhotoImage, messagebox
from PIL import Image, ImageTk
import threading
import time
from datetime import datetime
from PyCameraList.camera_device import list_video_devices
from tkinter import ttk
import os

DELAYTIME = 0.1

# 全局變數，控制二質化開關和閾值
is_binary_thresholding = [False, False, False]  # 三個影像的二質化狀態
binary_threshold_values = [127, 127, 127]  # 三個影像的默認閾值
latest_frames = [None, None, None]  # 存儲最新捕獲的影像

def resize_image(original_image, width, height):
    """調整影像大小"""
    return original_image.resize((width, height))

def toggle_recording():
    """切換錄影狀態"""
    result = messagebox.askyesno("確認", "確定要切換嗎？")
    if result:
        new_text = '關閉' if toggle_button.cget('text') == '儲存影片' else '儲存影片'
        toggle_button.config(text=new_text)

def toggle_binary_thresholding(camera_index):
    """切換二質化狀態"""
    global is_binary_thresholding
    is_binary_thresholding[camera_index] = not is_binary_thresholding[camera_index]
    status = "開啟" if is_binary_thresholding[camera_index] else "關閉"
    binary_buttons[camera_index].config(text=f"二質化: {status}")

def update_binary_threshold(camera_index, value):
    """更新二質化閾值"""
    global binary_threshold_values
    binary_threshold_values[camera_index] = int(value)

def setup_camera(camera_index):
    """初始化相機"""
    camera = cv2.VideoCapture(camera_index)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    return camera

def start_video_recording(current_time, output_prefix):
    """開始錄影，返回影片儲存物件"""
    video_filename = f'影片檔案/{output_prefix}_{current_time}.avi'
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    return cv2.VideoWriter(video_filename, fourcc, 30.0, (1920, 1080))

def process_image(camera_index, image_label, output_prefix, status_label):
    """處理影像並顯示"""
    status_label.config(text="Camera: 連線中")
    time.sleep(1)
    
    camera = setup_camera(camera_index)
    out = None
    recording = False

    while True:
        try:
            if camera.isOpened():
                status_label.config(text="Camera: 連線成功")
                ret, frame = camera.read()
                if not ret:
                    continue
                
                # 根據二質化狀態處理影像
                if is_binary_thresholding[camera_index]: 
                    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # 將影像轉為灰階
                    _, display_frame = cv2.threshold(gray_frame, binary_threshold_values[camera_index], 255, cv2.THRESH_BINARY)  # 應用二質化
                else:
                    display_frame = frame  # 使用原始影像

                latest_frames[camera_index] = frame.copy()  # 保存最新影像
                
                if toggle_button.cget('text') == '關閉':
                    if not recording:
                        current_time = datetime.now().strftime("%Y%m%d_%H%M")
                        out = start_video_recording(current_time, output_prefix)
                        recording = True
                    out.write(frame)  # 寫入原始影像
                elif recording:
                    out.release()
                    recording = False
                
                # 顯示影像
                _, jpeg = cv2.imencode(".jpg", display_frame)  # 使用顯示影像進行顯示
                original_image = Image.open(BytesIO(jpeg))
                resized_image = resize_image(original_image, 480, 480)
                photo_image = ImageTk.PhotoImage(resized_image)

                image_label.config(image=photo_image)
                image_label.image = photo_image

            else:
                status_label.config(text="Camera: 連線失敗")
                time.sleep(2)
                break

        except Exception as e:
            print(f"Error: {e}")
            break
    
    camera.release()
    if recording:
        out.release()

def capture_images():
    """從所有相機拍照並儲存圖片"""
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")   
    save_directory = '拍照檔案'

    # 確認目錄是否存在，若不存在則創建
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    for i, frame in enumerate(latest_frames):
        if frame is not None:
            # 確認 frame 的形狀和資料類型
            print(f"相機 {i} 的 frame 形狀: {frame.shape}, 資料類型: {frame.dtype}")

            # 使用 os.path.join 來組合路徑，並確保正確的路徑格式
            image_filename = os.path.join(save_directory, f"相機_{i}_{current_time}.jpg").replace("\\", "/")
            
            try:
                # 使用 Pillow 將 OpenCV 影像轉換為 Pillow 影像並儲存
                pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))  # 將 BGR 轉換為 RGB
                pil_image.save(image_filename)
                print(f"圖片已儲存: {image_filename}")

            except Exception as e:
                print(f"儲存圖片時出現錯誤: {e}")
        else:
            print(f"相機 {i} 沒有捕獲到有效的影像")

    messagebox.showinfo("拍照", "所有相機圖片已儲存")

def capture_images_from_camera(camera_index, image_label, status_label):
    """不斷捕獲影像的循環"""
    while True:
        process_image(camera_index, image_label, f"相機_{camera_index}", status_label)
        time.sleep(DELAYTIME)

window = tk.Tk()
window.title('GUI')
window.configure(bg='#111111')

for i in range(3):
    window.columnconfigure(i, weight=1)
window.rowconfigure(0, weight=10)
for i in range(2):
    window.rowconfigure(i + 1, weight=1)

image_labels = [tk.Label(window, bg='#333333') for _ in range(3)]
status_labels = [tk.Label(window, bg='#333333', fg='white', font=('Arial', 16, 'bold'), text='Camera: 沒訊號') for _ in range(3)]
toggle_button = tk.Button(window, text="儲存影片", command=toggle_recording, font=('Arial', 16, 'bold'), bg='#555555', fg='white')

binary_buttons = []
threshold_sliders = []

for i in range(3):
    binary_button = tk.Button(window, text="二質化: 關閉", command=lambda i=i: toggle_binary_thresholding(i), font=('Arial', 16, 'bold'), bg='#555555', fg='white')
    threshold_slider = tk.Scale(window, from_=0, to=255, orient='horizontal', command=lambda value, i=i: update_binary_threshold(i, value), bg='#555555', fg='white', font=('Arial', 12))

    binary_buttons.append(binary_button)
    threshold_sliders.append(threshold_slider)

for i in range(3):
    image_labels[i].grid(row=0, column=i, padx=1, pady=1, sticky='nsew')
    status_labels[i].grid(row=1, column=i, padx=1, pady=1, sticky='nsew')
    binary_buttons[i].grid(row=2, column=i, padx=1, pady=1, sticky='nsew')
    threshold_sliders[i].grid(row=3, column=i, padx=1, pady=1, sticky='nsew')

# 新增全局拍照按鈕
capture_button = tk.Button(window, text="拍照", command=capture_images, font=('Arial', 16, 'bold'), bg='#555555', fg='white')
capture_button.grid(row=4, column=1, padx=1, pady=1, sticky='nsew')

toggle_button.grid(row=5, column=1, padx=1, pady=1, sticky='nsew')

for i in range(3):
    threading.Thread(target=capture_images_from_camera, args=(i, image_labels[i], status_labels[i]), daemon=True).start()

window.mainloop()
