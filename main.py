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
from ultralytics import YOLO
from tkinter import Entry

DELAYTIME = 0.1

global_showWitdth = 1280
global_showHeight = 960

# 全局變數，控制二質化開關和閾值
is_binary_thresholding = [False, False, False]  # 三個影像的二質化狀態
binary_threshold_values = [127, 127, 127]  # 三個影像的默認閾值
latest_frames = [None, None, None]  # 存儲最新捕獲的影像

global_updateCameraFlag = [False, False, False]

model = YOLO("trained_model.pt")

points = []
actual_distance = 0


def set_actual_distance():
    """取得使用者輸入的實際距離值"""
    global actual_distance
    try:
        actual_distance = float(distance_entry.get())
        if actual_distance > 0:
            messagebox.showinfo("距離設定", "實際距離設定成功！請在畫面上點選兩個點。")
            points.clear()  # 清空之前選擇的點
    except ValueError:
        messagebox.showerror("錯誤", "請輸入有效的距離值")

def calculate_pixel_to_distance():
    """根據兩點計算每像素的距離"""
    global actual_distance
    if len(points) == 2 and actual_distance > 0:
        # 計算兩點的距離（像素）
        pixel_distance = ((points[1][0] - points[0][0]) ** 2 + (points[1][1] - points[0][1]) ** 2) ** 0.5
        # 每像素的距離
        distance_per_pixel = actual_distance / pixel_distance
        
        Resolution.config(text=f"解析度 (mm): {distance_per_pixel}")
        distance_label.config(text=f"量測距離 (Pixel): {pixel_distance}")

def on_click(event):
    """點選影像座標，並記錄點位置"""
    global points, latest_frames

    # 確保 latest_frames 中有有效的影像
    if latest_frames[0] is None:
        print("沒有有效的影像")
        return
    
 
    if len(points) < 2:
        points.append((event.x, event.y))  # 記錄影像中的畫素座標
        if len(points) == 2:
            calculate_pixel_to_distance()
            
    # 顯示點擊位置的畫素座標
    # print(f"點擊位置 (影像畫素座標): ({event.x}, {event.y})")
            
            
def research_camera_options():
    # 取得當前的 camera devices 列表
    cameras = list_video_devices()
    
    # 更新 Combobox 的選項
    boxs[0]['values'] = cameras
    # boxs[1]['values'] = cameras
    # boxs[2]['values'] = cameras

    # 選擇 Combobox 的第一個項目
    if cameras:
        boxs[0].set(cameras[0])
        boxs[1].set(cameras[1])
        boxs[2].set(cameras[2])
        
def update_camera_options():
    global global_updateCameraFlag
    
    global_updateCameraFlag = [True, True, True]
        
        
def resize_image(original_image, width, height):
    """調整影像大小"""
    return original_image.resize((width, height))

def toggle_recording():
    """切換錄影狀態"""
    result = messagebox.askyesno("確認", "確定要切換嗎？")
    if result:
        new_text = '關閉' if toggle_button.cget('text') == '儲存影片' else '儲存影片'
        toggle_button.config(text=new_text)


def setup_camera(camera_index):
    """初始化相機"""
    camera = cv2.VideoCapture(camera_index)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    return camera

def start_video_recording(current_time, output_prefix):
    save_directory = '影片檔案'
    
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)
        
        
    video_filename = f'影片檔案/{output_prefix}_{current_time}.avi'
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    return cv2.VideoWriter(video_filename, fourcc, 30.0, (1920, 1080))

def process_image(camera_index, columnIndex, image_label, output_prefix, status_label):
    """處理影像並顯示"""
    status_label.config(text="Camera: 連線中")
    time.sleep(1)
    
    camera = setup_camera(camera_index)
    out = None
    recording = False
    
    while True and not global_updateCameraFlag[columnIndex]:
        try:
            if camera.isOpened():
                status_label.config(text=f"Camera: 連線成功 ({camera_index})")
                ret, frame = camera.read()
                
                if not ret:
                    return 0
                

                display_frame = frame  # 使用原始影像
                
                results = model.predict(
                    source=[display_frame]
                ) 


                latest_frames[columnIndex] = frame.copy()  # 保存最新影像
                
                if toggle_button.cget('text') == '關閉':
                    if not recording:
                        current_time = datetime.now().strftime("%Y%m%d_%H%M")
                        out = start_video_recording(current_time, output_prefix)
                        recording = True
                    out.write(frame)  # 寫入原始影像
                elif recording:
                    out.release()
                    recording = False
                    
                    
                for i, result in enumerate(results):
                    
                    display_frame = result.plot()

                    boxes = result.boxes.xyxy  # 邊界框的 (xmin, ymin, xmax, ymax) 座標
                    labels = result.boxes.cls  # 邊界框的類別標籤
                    
                    # 遍歷每個邊界框，篩選出類別標籤為 0 的區域並計算面積
                    for j, (box, label) in enumerate(zip(boxes, labels)):
                        if label == 0:  # 假設類別 0 是金屬片
                            xmin, ymin, xmax, ymax = map(int, box)  # 將座標轉成整數
                            width = xmax - xmin  # 計算寬度
                            height = ymax - ymin  # 計算高度
                            area = width * height  # 計算面積
                            print(f"Camera: 連線成功 ({camera_index}), Area: {area}")
                
                _, jpeg = cv2.imencode(".jpg", display_frame)  # 使用顯示影像進行顯示
                original_image = Image.open(BytesIO(jpeg))
                resized_image = resize_image(original_image, global_showWitdth, global_showHeight)
                photo_image = ImageTk.PhotoImage(resized_image)

                image_label.config(image=photo_image)
                image_label.image = photo_image

            else:
                status_label.config(text="Camera: 連線失敗")
                camera.release()
                if recording:
                    out.release()

                return 0

        except Exception as e:
            camera.release()
            if recording:
                out.release()
                
            print(f"Error: {e}")
            return 0
    
    camera.release()
    time.sleep(3)
    
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
            image_filename = os.path.join(save_directory, f"photo_{i}_{current_time}.jpg").replace("\\", "/")
            
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

def capture_images_from_camera(camera_index, columnIndex, image_label, status_label, box):
    """不斷捕獲影像的循環"""
    global global_updateCameraFlag
    camera = camera_index
    while True:
        
        try:
            if global_updateCameraFlag[columnIndex]:
                print(box.get(), box.get()[0])
                camera = int(box.get()[0])
                global_updateCameraFlag[columnIndex] = False
        except:
            camera = camera_index
        
            
        print(f"columnIndex: {columnIndex}, camera_index: {camera}")
            
        process_image(camera, columnIndex, image_label, f"video_{columnIndex}", status_label)
        time.sleep(DELAYTIME)


window = tk.Tk()
window.title('GUI')
window.configure(bg='#111111')


window.columnconfigure(0, weight=8)
window.columnconfigure(1, weight=1)
    
window.rowconfigure(0, weight=6)
window.rowconfigure(1, weight=1)


# =============================================================================
# 
# =============================================================================
CAMERA_NUMBER = 1

frameTool = tk.Frame(window, relief=tk.RAISED, bg='#333333')
frameSearchCamera = tk.Frame(window, relief=tk.RAISED, bg='#333333')

image_labels = [tk.Label(window, bg='#333333') for _ in range(3)]

status_labels = [tk.Label(window, bg='#333333', fg='white', font=('Arial', 16, 'bold'), text='Camera: 沒訊號') for _ in range(CAMERA_NUMBER)]



distance_entry = Entry(frameSearchCamera, font=('Arial', 16, 'bold'))

set_distance_button = tk.Button(frameSearchCamera, text="設定距離", font=('Arial', 16, 'bold'), bg='#555555', fg='white', command=set_actual_distance)



cameraLabel = tk.Label(frameSearchCamera, bg='#333333', fg='white', font=('Arial', 16, 'bold'), text='Camera Tool')
update_button = tk.Button(frameSearchCamera, text="搜尋 Camera Devices", font=('Arial', 16, 'bold'), bg='#555555', fg='white', command=research_camera_options)
update_camera_button = tk.Button(frameSearchCamera, text="更新 Camera Devices", font=('Arial', 16, 'bold'), bg='#555555', fg='white', command=update_camera_options)
boxs = [ttk.Combobox(frameSearchCamera, values=[], font=('Arial', 16, 'bold'), width=20, height=5) for _ in range(CAMERA_NUMBER)]

saveImage = tk.Label(frameSearchCamera, bg='#333333', fg='white', font=('Arial', 16, 'bold'), text='SaveImage')
capture_button = tk.Button(frameSearchCamera, text="拍照", command=capture_images, font=('Arial', 16, 'bold'), bg='#555555', fg='white')
toggle_button = tk.Button(frameSearchCamera, text="儲存影片", command=toggle_recording, font=('Arial', 16, 'bold'), bg='#555555', fg='white')

pixel_to_distance = tk.Label(frameSearchCamera, bg='#333333', fg='white', font=('Arial', 16, 'bold'), text='1 pixel equals X mm distance')
Resolution = tk.Label(frameSearchCamera, bg='#333333', fg='white', font=('Arial', 16, 'bold'), text='解析度 (mm):')
distance_label = tk.Label(frameSearchCamera, text="量測距離 (Pixel):", font=('Arial', 16, 'bold'), bg='#333333', fg='white')

# =============================================================================
# 
# =============================================================================
for i in range(CAMERA_NUMBER):
    image_labels[i].grid(row=0, column=i, padx=1, pady=1, sticky='nsew')
    status_labels[i].grid(row=1, column=i, padx=1, pady=1, sticky='nsew')
    

# =============================================================================
# frameTool
# =============================================================================
# frameTool.grid(row=0, column=1, padx=1, pady=5, sticky='nsew')

# =============================================================================
# frameCamera
# =============================================================================
frameSearchCamera.grid(row=0, column=1, padx=1, pady=1, sticky='nsew')

cameraLabel.pack(fill='x', padx=1, pady=5)
update_button.pack(fill='x', padx=1, pady=5)
update_camera_button.pack(fill='x', padx=1, pady=5)
boxs[0].pack(fill='x', padx=1, pady=5)

saveImage.pack(fill='x', padx=1, pady=5)
capture_button.pack(fill='x', padx=1, pady=5)
toggle_button.pack(fill='x', padx=1, pady=5)

pixel_to_distance.pack(fill='x', padx=1, pady=5)
Resolution.pack(fill='x', padx=1, pady=5)
distance_label.pack(fill='x', padx=1, pady=5)
distance_entry.pack(fill='x', padx=1, pady=5)
set_distance_button.pack(fill='x', padx=1, pady=5)


# =============================================================================
# frameCameraTool
# =============================================================================

for i in range(CAMERA_NUMBER):
    threading.Thread(target=capture_images_from_camera, args=(i, i, image_labels[i], status_labels[i], boxs[i]), daemon=True).start()

for image_label in image_labels:
    image_label.bind("<Button-1>", on_click)
    
    
window.mainloop()
