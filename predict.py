from ultralytics import YOLO
import cv2
import numpy as np
import math
import torch
import techmanpy

# Load a model
model = YOLO(r"C:\Users\a2265\Desktop\project\DryEtch\TM_robot_and_AutoClean\v2_20241106\trained_model_20241106.pt")

photoPath = r"C:\Users\a2265\Desktop\project\DryEtch\TM_robot_and_AutoClean\dataset\template\image"

results = model.predict(
    source=[
        photoPath + '/01_1035X450_GD_03.jpg',
    ]
)

areaTarget = [["phase01_X0", "phase01_Y0", "phase01_X0_to_X1", "phase01_Z"],
              ["phase02_X0", "phase02_Y0", "phase02_X0_to_X1", "phase02_Z"],
              ["phase03_X0", "phase03_Y0", "phase03_X0_to_X1", "phase03_Z"]]

# results = model.predict(photoPath + '/01_1035X450_GD_03.jpg')

# Grid parameters
# grid_rows, grid_cols = 4, 22
# left_offset_ratio = 0.99
# right_offset_ratio = 1.97

# Set the target display size
display_width, display_height = 800, 600

# Variables to store the points
points = []

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


def merge_nearby_boxes(boxes, iou_threshold=0.5):
    """
    合併框列表中相近的框，根據IoU閾值來判斷是否合併

    :param boxes: 邊界框列表，每個框格式為 [xmin, ymin, xmax, ymax]
    :param iou_threshold: 用於判斷框是否相近的IoU閾值，默認為 0.5
    :return: 合併後的邊界框列表
    """
    merged_boxes = []

    while boxes:
        current_box = boxes.pop(0)  # 取出第一個框，作為目前需要合併的框
        merged = False
        
        for i, other_box in enumerate(boxes):
            # 計算兩個框的 IoU
            iou = calculate_iou_or_distance(current_box, other_box)
            if iou >= iou_threshold:
                # 如果 IoU 超過閾值，則合併兩個框
                merged_box = merge_boxes(current_box, other_box)
                boxes[i] = merged_box  # 替換原來的框
                merged = True
                break
        
        # 如果沒有合併，將框加入最終結果
        if not merged:
            merged_boxes.append(current_box)

    return merged_boxes


def calculate_box_parameters(boxes):
    """
    計算框的參數，返回多組數據。
    
    :param boxes: 邊界框列表，每個框格式為 [xmin, ymin, xmax, ymax]
    :return: 每組為 (差值, 寬, 高*100/30)
    """
    result = []
    
    originX = 1280
    originY = 960
    preMoveY = 30
    resolution = 0.5
    
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


# Mouse callback function to get coordinates and draw a line
# def get_coordinates(event, x, y, flags, param):
#     global points
#     if event == cv2.EVENT_LBUTTONDOWN:  # Left mouse button clicked
#         print(f"Clicked coordinates: ({x}, {y})")
#         points.append((x, y))
        
#         # Draw a point on each click
#         cv2.circle(display_frame, (x, y), 5, (0, 255, 0), -1)
#         cv2.imshow("Image", display_frame)

#         # If two points are clicked, draw the line and calculate distance
#         if len(points) == 2:
#             cv2.line(display_frame, points[0], points[1], (255, 0, 0), 2)
#             cv2.imshow("Image", display_frame)

#             # Calculate the pixel distance between two points
#             pixel_distance = np.sqrt((points[1][0] - points[0][0]) ** 2 + (points[1][1] - points[0][1]) ** 2)
#             print(f"Pixel Distance: {pixel_distance}")

#             # Input the real-world distance between the two points
#             real_distance = float(input("Enter the real distance (in your preferred unit): "))

#             # Calculate the distance per pixel
#             distance_per_pixel = real_distance / pixel_distance
#             print(f"Distance per pixel: {distance_per_pixel} units/pixel")

#             # Reset points after calculation
#             points = []

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


for i, result in enumerate(results):
    img = result.orig_img.copy()
    boxes = result.boxes.xyxy  # 邊界框的 (xmin, ymin, xmax, ymax) 座標
    labels = result.boxes.cls  # 邊界框的類別標籤
    scores = result.boxes.conf  # 每個邊界框的機率

    # 顯示原始框
    original_display = img.copy()
    original_display = draw_boxes(original_display, boxes, labels, scores)

    DEFECT_CLASS = 16
    combined_boxes = []  # 存儲合併後的框
    if len(labels) > 0:
        for j, (box, label) in enumerate(zip(boxes, labels)):
            if label == DEFECT_CLASS:
                # 對於label不為16的框進行合併處理
                # 計算 IOU 並合併相近的框，最多三個框
                for k, other_box in enumerate(combined_boxes):
                    iou = calculate_iou_or_distance(box, other_box)  # 假設已定義的 calculate_iou 函數
                    if iou == True:
                        combined_boxes[k] = merge_boxes(box, other_box)  # 合併框（假設已定義 merge_boxes 函數）
                        break
                else:
                    combined_boxes.append(box)  # 如果沒有匹配的框，添加新框

        # 只取最多三個框
        combined_boxes = combined_boxes[:3]
        
  
        box_params = calculate_box_parameters(combined_boxes)
        for idx, params in enumerate(box_params):
            print(f"Group {idx + 1}: X = {params[0]}, Y = {params[1]}, Width = {params[2]}, Height*100/30 = {params[3]}")


        # 顯示合併後的框
        merged_display = img.copy()
        merged_display = draw_boxes(merged_display, combined_boxes, labels[:len(combined_boxes)], scores[:len(combined_boxes)])
        distance_per_pixel = 0.5

        for idx, params in enumerate(box_params):
            for Index in range(len(areaTarget[0]) - 1):
                # 判斷是否是最後一個索引
                exit_program = (Index == len(areaTarget[0]) - 1)
                sendData(StrTargetName=areaTarget[Index], values=params[Index], ExitProgram=exit_program)
                
                
        
    else:
        print("沒有東西")

    phaseStatus = 0  # 重置狀態

    # Resize the frames to fit within the display
    resized_original = cv2.resize(original_display, (display_width, display_height))
    resized_merged = cv2.resize(merged_display, (display_width, display_height))

    # 顯示原始框的圖像
    cv2.namedWindow("Original Image", cv2.WINDOW_NORMAL)
    cv2.imshow("Original Image", resized_original)
    cv2.imwrite("合併前.jpg", resized_original)
    
    # 顯示合併框的圖像
    cv2.namedWindow("Merged Image", cv2.WINDOW_NORMAL)
    cv2.imshow("Merged Image", resized_merged)
    cv2.imwrite("合併後.jpg", resized_merged)
    # 等待按鍵事件來關閉視窗
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    
    
    
    
    
    
    
