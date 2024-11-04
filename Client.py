from ultralytics import YOLO
import cv2
import numpy as np
import matplotlib.pyplot as plt

# Load a model
model = YOLO("trained_model.pt")

photoPath = r"C:\Users\a2265\Desktop\project\DryEtch\TM_robot_and_AutoClean\dataset\template"

results = model.predict(
    source=[
        photoPath + '/05_1035X125(155)_GD_03.jpg',
    ]
)

# =============================================================================
#  965X450
# =============================================================================
# grid_rows, grid_cols = 10, 20
# left_offset_ratio = 0.97
# right_offset_ratio = 1.87

# =============================================================================
# 1035X260
# =============================================================================
# grid_rows, grid_cols = 7, 22
# left_offset_ratio = 0.97
# right_offset_ratio = 1.92

# =============================================================================
# 1035X125
# =============================================================================
grid_rows, grid_cols = 4, 22
left_offset_ratio = 0.99
right_offset_ratio = 1.97

for i, result in enumerate(results):
    img = result.orig_img.copy()
    boxes = result.boxes.xyxy  # (xmin, ymin, xmax, ymax)
    labels = result.boxes.cls  # 
    display_frame = result.plot()
    plt.imshow(display_frame)

    # 遍历 `label == 0` 的区域
    for j, (box0, label0) in enumerate(zip(boxes, labels)):
        if label0 == 0:  #
            xmin0, ymin0, xmax0, ymax0 = map(int, box0)

            
            top_width = int((xmax0 - xmin0) * (right_offset_ratio - left_offset_ratio))  # 顶部宽度

            # 计算梯形顶部的xmin和xmax
            top_xmin = xmin0 + int((1 - left_offset_ratio) * (xmax0 - xmin0))
            top_xmax = top_xmin + top_width

            # 左右边缘的不同斜率
            left_slope = (xmin0 - top_xmin) / grid_rows
            right_slope = (xmax0 - top_xmax) / grid_rows

            # 梯形四个顶点
            top_left = [top_xmin, ymin0]
            top_right = [top_xmax, ymin0]
            bottom_left = [xmin0, ymax0]
            bottom_right = [xmax0, ymax0]

            # 绘制梯形
            points = np.array([top_left, top_right, bottom_right, bottom_left], np.int32)
            cv2.polylines(img, [points], isClosed=True, color=(255, 0, 0), thickness=2)
            cv2.putText(img, 'Label 0', (xmin0, ymin0 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

            # 初始化重叠网格列表
            overlapping_grids = []

            # 按行生成网格并按左右不同斜率计算列宽度
            for row in range(grid_rows):
                # 当前行的顶部和底部宽度
                row_ymin = ymin0 + row * (ymax0 - ymin0) // grid_rows
                row_ymax = ymin0 + (row + 1) * (ymax0 - ymin0) // grid_rows

                # 左右边缘的动态变化
                row_xmin = int(top_xmin + row * left_slope)
                row_xmax = int(top_xmax + row * right_slope)
                row_width = (row_xmax - row_xmin) // grid_cols

                # 在当前行内生成列
                for col in range(grid_cols):
                    grid_xmin = row_xmin + col * row_width
                    grid_xmax = grid_xmin + row_width
                    grid_ymin = row_ymin
                    grid_ymax = row_ymax

                    # 绘制每个网格单元
                    cv2.rectangle(img, (grid_xmin, grid_ymin), (grid_xmax, grid_ymax), 
                                  (255, 255, 0), 1)

                    # 检查 `label == 1` 是否与当前网格单元重叠
                    for k, (box1, label1) in enumerate(zip(boxes, labels)):
                        if label1 == 1:
                            xmin1, ymin1, xmax1, ymax1 = map(int, box1)
                            # 判断重叠
                            if (xmin1 < grid_xmax and xmax1 > grid_xmin and
                                ymin1 < grid_ymax and ymax1 > grid_ymin):
                                overlapping_grids.append((row, col))
                                # 绘制重叠网格单元
                                cv2.rectangle(img, (grid_xmin, grid_ymin), (grid_xmax, grid_ymax), 
                                              (0, 255, 0), 2)
                                cv2.putText(img, 'Overlap', (grid_xmin + 5, grid_ymin + 15),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    # 显示结果图像
    plt.figure(figsize=(10, 8))
    plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    plt.axis("off")
    plt.show()
