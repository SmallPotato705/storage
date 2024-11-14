from ultralytics import YOLO
import torch
# Load a model
import cv2

if __name__ == '__main__':
    # import os
    # os.environ['CUDA_LAUNCH_BLOCKING'] = "1"

    model = YOLO("yolo11n.pt")
    
    # Train the model
    train_results = model.train(
        data=r"C:\Users\a2265\Desktop\project\DryEtch\TM_robot_and_AutoClean\v2_20241106/data.yaml",  # path to dataset YAML
        epochs=400,  # number of training epochs
        imgsz=640,  # training image size
        device=0,  # device to run on, i.e. device=0 or device=0,1,2,3 or device=cpu
    )
    
    # # Evaluate model performance on the validation set
    metrics = model.val()
    
    model.save(r"trained_model.pt")
    
    import os

    # 設定圖片資料夾的路徑
    photoPath = r"C:\Users\a2265\Desktop\project\DryEtch\TM_robot_and_AutoClean\dataset\test\images"
    
    # 獲取資料夾中的所有圖片檔案
    image_files = [f for f in os.listdir(photoPath) if os.path.isfile(os.path.join(photoPath, f))]
    
    # 過濾出符合圖片格式的檔案（例如 .jpg 或 .png）
    image_files = [f for f in image_files if f.endswith(('.jpg', '.png'))]
    
    # 執行模型推論並處理每張圖片
    results = model([os.path.join(photoPath, image) for image in image_files])  # 自動讀取所有圖片檔案
    
    # 處理結果
    i = 0
    for result in results:
        boxes = result.boxes  # Box物件，包含邊界框
        masks = result.masks  # Masks物件，包含分割遮罩
        keypoints = result.keypoints  # Keypoints物件，包含姿勢點
        probs = result.probs  # Probs物件，包含分類結果
        obb = result.obb  # Oriented boxes物件，包含旋轉框結果
    
        # 顯示結果並儲存至檔案
        result.show()  # 顯示結果
        result.save(filename=f"result0{i}.jpg")  # 儲存結果為圖片
        i += 1
    
    
    
