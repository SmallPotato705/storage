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
import techmanpy
import math
import torch

DELAYTIME = 0.1

DEFECT_CLASS = 16

CONTINUOUS_NOT_ACTIVATE = 30

RESIZE_WIDTH = 1280
RESIZE_HEIGHT = 960

INITIAL_WIDTH = 1280
INITIAL_HEIGHT = 960

areaTarget = [["phase01_X0", "phase01_Y0", "phase01_X0_to_X1", "phase01_Z"],
              ["phase02_X0", "phase02_Y0", "phase02_X0_to_X1", "phase02_Z"],
              ["phase03_X0", "phase03_Y0", "phase03_X0_to_X1", "phase03_Z"]]


latest_frames = [None, None, None]  # 存儲最新捕獲的影像

global_updateCameraFlag = [False, False, False]

model = YOLO("trained_model_20241106.pt")

# nest_asyncio.apply()

points = []
actual_distance = 0
distance_per_pixel = 0
phase01_Status = 0
phase02_Status = 0

output_before_path = 'before_combined_boxes.jpg'
output_after_path = 'after_combined_boxes.jpg'

def calculate_iou_or_distance(box1, box2):
    """
    計算兩個邊界框的交並比 (IoU)，若框之間距離小於等於20像素或外框寬高相近，則進行合併。
    
    :param box1: 第一個邊界框, 格式為 [xmin, ymin, xmax, ymax]
    :param box2: 第二個邊界框, 格式為 [xmin, ymin, xmax, ymax]
    :return: 若距離小於等於200像素或外框寬高相近，則返回True，否則返回False
    """
    # 計算兩個框的中心點
    center_x1, center_y1 = (box1[0] + box1[2]) / 2, (box1[1] + box1[3]) / 2
    center_x2, center_y2 = (box2[0] + box2[2]) / 2, (box2[1] + box2[3]) / 2
    
    # 計算中心點距離
    distance = math.sqrt((center_x2 - center_x1) ** 2 + (center_y2 - center_y1) ** 2)
    
    # 計算框的寬度和高度
    width1 = box1[2] - box1[0]
    height1 = box1[3] - box1[1]
    width2 = box2[2] - box2[0]
    height2 = box2[3] - box2[1]
    
    # 計算寬度和高度的差異百分比
    width_diff = abs(width1 - width2)
    height_diff = abs(height1 - height2)
    
    # 若中心點距離小於等於200像素，或寬高差異小於10%，則返回True，表示需要合併
    if distance <= 200 or width_diff <= 50 or height_diff <= 50:
        return True
    else:
        return False
    
def draw_boxes(image, boxes, labels, scores):
    # 繪製邊界框和標籤
    for i, (box, label, score) in enumerate(zip(boxes, labels, scores)):
        xmin, ymin, xmax, ymax = map(int, box)
        # 設定顏色和標籤
        color = (0, 255, 0)  # 綠色框
        label_text = f"Label: {i}"
        
        # 繪製邊界框
        cv2.rectangle(image, (xmin, ymin), (xmax, ymax), color, 3)
        
        # 在框上方顯示標籤
        cv2.putText(image, label_text, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    return image

def merge_boxes(box1, box2):
    """
    合併兩個邊界框，返回合併後的框
    
    :param box1: 第一個邊界框, 格式為 [xmin, ymin, xmax, ymax]
    :param box2: 第二個邊界框, 格式為 [xmin, ymin, xmax, ymax]
    :return: 合併後的框, 格式為 [xmin, ymin, xmax, ymax]
    """
    xmin = min(box1[0], box2[0])
    ymin = min(box1[1], box2[1])
    xmax = max(box1[2], box2[2])
    ymax = max(box1[3], box2[3])

    return [xmin, ymin, xmax, ymax]


def sendData(StrTargetName, values, ExitProgram):
    try:
        print(StrTargetName, str(values))
        with techmanpy.connect_sct(robot_ip='169.254.124.190') as conn: 
            
            conn.send_data(StrTargetName, [values]) 

            if ExitProgram == True:
                conn.exit_listen()
                
        return True
    except Exception as e:
        print(f"Error fetching data for {StrTargetName}: {e}")

        return False
        
def readData(StrTargetName, phaseStatus):  
    try:
        with techmanpy.connect_svr(robot_ip='169.254.124.190') as conn: 
            robot_model = conn.get_value(StrTargetName)  # 同步取得數據
    
            if robot_model == 0:
                phaseStatus = "未啟動"
            elif robot_model == 1:
                phaseStatus = "模板匹配"
            elif robot_model == 2:
                phaseStatus = "局部清洗"
                
            print("readData: ", robot_model)
                
    except Exception as e:
        print(f"Error fetching data for {StrTargetName}: {e}")

    return phaseStatus
        
def set_actual_distance():
    """取得使用者輸入的實際距離值"""
    global actual_distance, points, latest_frames, image
    
    points.clear()  # 清空之前選擇的點

    # 確保 latest_frames 不為空
    if latest_frames:
        # 將最新的影像保存為 JPG 格式
        cv2.imwrite("latest_frames.jpg", latest_frames[0])

        # 使用保存的圖片路徑讀取圖片
        image_path = 'latest_frames.jpg'
        image = cv2.imread(image_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        origin_label.config(text = f"Shape: {image.shape[1], image.shape[0]}")
        # 將圖片顯示在 tkinter canvas 上
        display_image_on_canvas(image, canvas)
    else:
        messagebox.showerror("錯誤", "沒有可用的影像資料")
    
    
    try:
        actual_distance = float(distance_entry.get())
        if actual_distance > 0:
            messagebox.showinfo("距離設定", "實際距離設定成功！請在畫面上點選兩個點。")
            points.clear()  # 清空之前選擇的點
    except ValueError:
        messagebox.showerror("錯誤", "請輸入有效的距離值")

def calculate_pixel_to_distance():
    """根據兩點計算每像素的距離"""
    global actual_distance, distance_per_pixel
    if len(points) == 2 and actual_distance > 0:
        # 計算兩點的距離（像素）
        pixel_distance = ((points[1][0] - points[0][0]) ** 2 + (points[1][1] - points[0][1]) ** 2) ** 0.5
        # 每像素的距離
        distance_per_pixel = actual_distance / pixel_distance
        
        Resolution.config(text=f"解析度 (mm): {distance_per_pixel}")
        distance_label.config(text=f"量測距離 (Pixel): {pixel_distance}")
            
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
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, INITIAL_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, INITIAL_HEIGHT)
    return camera

def initial_video_recording(current_time, output_prefix):
    save_directory = '影片檔案'
    
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)
        
    video_filename = f'影片檔案/{output_prefix}_{current_time}.avi'
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    return cv2.VideoWriter(video_filename, fourcc, 30.0, (INITIAL_WIDTH, INITIAL_HEIGHT))


def readCamera(camera_index, columnIndex, camera, status_label):
    # 初始化返回值
    ret, display_frame = False, None
    
    # 確認攝影機物件是否已初始化
    if not camera or not camera.isOpened():
        status_label.config(text=f"Camera: 無法連線 ({camera_index})")
        print(f"Camera {camera_index} 未正確初始化")
        return ret, display_frame

    try:
        # 讀取攝影機畫面
        ret, display_frame = camera.read()
        
        if ret:
            status_label.config(text=f"Camera: 連線成功 ({camera_index})")
        else:
            # 無法讀取畫面
            status_label.config(text=f"Camera: 無法讀取畫面 ({camera_index})")
            print(f"無法讀取來自 Camera {camera_index} 的畫面")
            
    except Exception as e:
        # 捕獲並顯示錯誤
        camera.release()
        status_label.config(text=f"Camera: 發生錯誤 ({camera_index})")
        print("readCamera Exception: ", e)
        
    return ret, display_frame

def start_video_recording(recording, out, display_frame, output_prefix, toggle_button, status_label):
    try:
        if toggle_button.cget('text') == '關閉':
            if not recording:
                # 設定錄影檔名及初始化錄影器
                current_time = datetime.now().strftime("%Y%m%d_%H%M")
                out = initial_video_recording(current_time, output_prefix)
                recording = True
                status_label.config(text="錄影中...")  # 更新狀態顯示
            if display_frame is not None:
                out.write(display_frame)  # 寫入當前影像幀
            else:
                print("start_video_recording: display_frame is None")
        elif recording:
            # 停止錄影
            out.release()
            recording = False
            status_label.config(text="錄影已停止")  # 更新狀態顯示
    except Exception as e:
        if recording:
            out.release()
            
        print("start_video_recording Exception: ", e)
    
    return recording, out


def process_image(camera_index, columnIndex, image_label, output_prefix, status_label):
    """處理影像並顯示"""
    status_label.config(text="Camera: 連線中")
    time.sleep(1)
    
    camera = setup_camera(camera_index)
    out = None
    recording = False
    
    # 用於跟踪最高概率label連續出現的次數和當前最高概率的label
    highest_label_count = 0
    previous_highest_label = None
    no_match_count = 0  # 用於計數未滿足條件的次數
    phaseStatus = "未啟動"
    # phaseStatus = "模板匹配"
    
    while True and not global_updateCameraFlag[columnIndex]:
        
        ret, display_frame = readCamera(camera_index, columnIndex, camera, status_label)
        
        if ret:
            latest_frames[columnIndex] = display_frame.copy()  # 保存最新影像
            
            results = model.predict(source=[display_frame])
            result = results[0]

            boxes = result.boxes.xyxy  # 邊界框的 (xmin, ymin, xmax, ymax) 座標
            labels = result.boxes.cls  # 邊界框的類別標籤
            scores = result.boxes.conf  # 每個邊界框的機率
            
            if len(labels) > 0:
                display_frame = result.plot()
                
            _, jpeg = cv2.imencode(".jpg", display_frame)  # 使用顯示影像進行顯示
            original_image = Image.open(BytesIO(jpeg))
            resized_image = resize_image(original_image, RESIZE_WIDTH, RESIZE_HEIGHT)
            photo_image = ImageTk.PhotoImage(resized_image)
    
            image_label.config(image=photo_image)
            image_label.image = photo_image
                
            recording, out = start_video_recording(recording, out, display_frame, output_prefix, toggle_button, status_label)
           
        phaseStatus_label.config(text="目前狀態: 等待Robot回覆")
        
        # 讀取當前 Phase Status
        phaseStatus = readData("Phase_Status_Robot_to_PC", phaseStatus)

        if phaseStatus == "模板匹配":
            if len(labels) > 0:
                # 找出機率最高的label及其索引
                max_score_idx = scores.argmax()
                max_label = labels[max_score_idx]
                
                if max_label == DEFECT_CLASS:
                    # 如果最大機率的label是16，則選擇次高機率的label
                    # 排除最大機率label，找出次高機率的label
                    
                    # 檢查是否存在次高機率（即最大機率的索引是否唯一）
                    if (scores == scores[max_score_idx]).sum() > 1:
                        # 如果有多個最大機率，則無法確定次高機率
                        second_max_score_idx = (scores != scores[max_score_idx]).argmax()  # 找到次高機率的索引
                        max_label = labels[second_max_score_idx]  # 次高機率對應的label
                    else:
                        max_label = 99
                
                # 判斷最高概率的label是否連續5次相同
                if max_label == previous_highest_label:
                    highest_label_count += 1
                else:
                    previous_highest_label = max_label
                    highest_label_count = 1  # 重置計數為1
                    
                # 檢查條件1：連續5次相同的label
                if highest_label_count >= 5:
                    sendData(StrTargetName = "Parts_Class", values = max_label, ExitProgram = True)  # 輸出給Robot
                    phaseStatus_label.config(text="目前狀態: 整片清洗中")
                    highest_label_count = 0  # 重置計數器
                    no_match_count = 0  # 重置未匹配計數
                    phaseStatus = "未啟動" # 重置 Phase Status
            else:
                no_match_count += 1  # 若無有效label，增加未匹配計數
                    
            # 檢查條件2：連續30次未匹配到相同的label
            if no_match_count >= 30:
                sendData(StrTargetName = "Reset", values = 1, ExitProgram = True) # 輸出給Robot
                phaseStatus_label.config(text="目前狀態: 超時，強制輸出")
                highest_label_count = 0  # 重置計數器
                no_match_count = 0  # 重置未匹配計數
                phaseStatus = "未啟動" # 重置 Phase Status
            
        elif phaseStatus == "局部清洗":
            combined_boxes = []  # 存儲合併後的框
            if len(labels) > 0:
                isDefect = False
                
                for j, (box, label) in enumerate(zip(boxes, labels)):
                    if label == DEFECT_CLASS:
                        isDefect = True
                        for k, other_box in enumerate(combined_boxes):
                            iou = calculate_iou_or_distance(box, other_box)
                            if iou == True:
                                combined_boxes[k] = merge_boxes(box, other_box)  # 合併框（假設已定義 merge_boxes 函數）
                                break
                        else:
                            combined_boxes.append(box)  # 如果沒有匹配的框，添加新框
                            
                            
                if isDefect == False:
                    sendData(StrTargetName = "Finish", values = 1, ExitProgram = True)  # 輸出給Robot
                    phaseStatus = "未啟動"  # 重置狀態

                # 只取最多三個框
                combined_boxes = combined_boxes[:3]
                
                phaseStatus_label.config(text=f"目前狀態: 局部清洗 ({len(combined_boxes)} 塊)")
                
                merged_display = draw_boxes(display_frame, combined_boxes, labels[:len(combined_boxes)], scores[:len(combined_boxes)])
                
                cv2.imwrite(output_after_path, merged_display)
                cv2.imwrite(output_before_path, display_frame)
                
                # =============================================================================
                #                               
                # =============================================================================
                box_params = calculate_box_parameters(boxes = combined_boxes, originX = points[0][0], originY = points[0][1], resolution = distance_per_pixel)

                for idx, params in enumerate(box_params):
                    for Index in range(len(areaTarget[0]) - 1):
                        # 判斷是否是最後一個索引
                        exit_program = (Index == len(areaTarget[0]) - 1)
                        sendData(StrTargetName=areaTarget[Index], values=params[Index], ExitProgram=exit_program)
            
                phaseStatus = "未啟動"  # 重置狀態
            else:
                no_match_count += 1
                if no_match_count >= 30:
                    sendData(StrTargetName = "Reset", values = 1, ExitProgram = True)  # 輸出給Robot
                    phaseStatus_label.config(text="目前狀態: 超時，強制輸出")
                    highest_label_count = 0  # 重置計數器
                    no_match_count = 0  # 重置未匹配計數
                    phaseStatus = "未啟動" # 重置 Phase Status


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

        
def on_click(event):
    """點擊圖片，並記錄單個點位置"""
    global points, image, canvas_width, canvas_height
    if len(points) < 2:  # 只記錄第一個點
        # 計算顯示圖片的縮放比例
        scale_x = image.shape[1] / canvas_width
        scale_y = image.shape[0] / canvas_height

        # 根據縮放比例調整點擊位置
        x = int(event.x * scale_x)
        y = int(event.y * scale_y)

        points.append((x, y))  # 記錄點擊的圖片座標
        if  len(points) == 1:
            origin_label.config(text = f"原點: {x}, {y}")
        canvas.create_oval(event.x - 5, event.y - 5, event.x + 5, event.y + 5, fill='red')  # 顯示紅色圓點
        
        if len(points) == 2:
            calculate_pixel_to_distance()  # 計算像素到距離

def display_image_on_canvas(image, canvas):
    """將圖片顯示在 canvas 上"""
    global canvas_width, canvas_height
    # 設定canvas的寬度和高度，確保顯示的大小
    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height()

    # 將 OpenCV 圖片轉換為 Pillow 圖片並顯示
    pil_image = Image.fromarray(image)
    tk_image = ImageTk.PhotoImage(pil_image)
    canvas.create_image(0, 0, anchor=tk.NW, image=tk_image)
    canvas.image = tk_image  # 防止圖像被垃圾回收

def open_image():
    """打開圖片文件並顯示在視窗中"""
    global points, latest_frames, image
    points.clear()  # 清空之前選擇的點

    # 確保 latest_frames 不為空
    if latest_frames:
        # 將最新的影像保存為 JPG 格式
        cv2.imwrite("latest_frames.jpg", latest_frames[0])

        # 使用保存的圖片路徑讀取圖片
        image_path = 'latest_frames.jpg'
        image = cv2.imread(image_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        origin_label.config(text = f"Shape: {image.shape[1], image.shape[0]}")
        # 將圖片顯示在 tkinter canvas 上
        display_image_on_canvas(image, canvas)
    else:
        messagebox.showerror("錯誤", "沒有可用的影像資料")

def calculate_box_parameters(boxes, originX, originY, resolution, preMoveY = 30):
    """
    計算框的參數，返回多組數據。
    
    :param boxes: 邊界框列表，每個框格式為 [xmin, ymin, xmax, ymax]
    :return: 每組為 (差值, 寬, 高*100/30)
    """
    result = []
    
    for i, box in enumerate(boxes):
        xmin, ymin, xmax, ymax = box
        width = xmax - xmin
        height = ymax - ymin
        height_scaled = (height * resolution) / preMoveY

        if i == 0:
            # 第一組，原點到左上角的差值
            delta_x = torch.round(originX - xmax)
            delta_y = torch.round(originY - ymax)
        else:
            # 其他組，計算上一組的右下角到當前框左上角的差值
            prev_xmax, prev_ymax = boxes[i - 1][2], boxes[i - 1][3]
            delta_x = torch.round(xmax - prev_xmax)
            delta_y = torch.round(ymax - prev_ymax)

        # 將結果加入列表
        result.append((delta_x, delta_y, torch.round(width), torch.round(height_scaled)))

    return result


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

Resolution = tk.Label(frameSearchCamera, bg='#333333', fg='white', font=('Arial', 16, 'bold'), text='解析度 (mm):')
distance_label = tk.Label(frameSearchCamera, text="量測距離 (Pixel):", font=('Arial', 16, 'bold'), bg='#333333', fg='white')


phaseStatus_label = tk.Label(window, text="目前狀態: 尚未啟動", font=('Arial', 16, 'bold'), bg='#333333', fg='white')

origin_label = tk.Label(frameSearchCamera, text="原點: ", font=('Arial', 16, 'bold'), bg='#333333', fg='white')

canvas = tk.Canvas(frameSearchCamera, width=400, height=300)

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

Resolution.pack(fill='x', padx=1, pady=5)
distance_label.pack(fill='x', padx=1, pady=5)
distance_entry.pack(fill='x', padx=1, pady=5)
set_distance_button.pack(fill='x', padx=1, pady=5)

origin_label.pack(fill='x', padx=1, pady=5)

canvas.pack(fill='x', padx=1, pady=5)
phaseStatus_label.grid(row=1, column=1, padx=1, pady=1, sticky='nsew')


# =============================================================================
# frameCameraTool
# =============================================================================

for i in range(CAMERA_NUMBER):
    threading.Thread(target=capture_images_from_camera, args=(i, i, image_labels[i], status_labels[i], boxs[i]), daemon=True).start()

canvas.bind("<Button-1>", on_click)
    
    
window.mainloop()