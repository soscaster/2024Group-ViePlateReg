# from PIL import ImageFont, ImageDraw, Image
# import numpy as np
# from easyocr import Reader
# import cv2

# def extract_text(path):
# # loading images and resizing
#     try:
#         img = cv2.imread(path)
#         # Print path
#         print(f"OCR is reading from image: {path}")
#         # Print image details
#         print(f"Image shape: {img.shape}")
#         # Resize image
#         img = cv2.resize(img, (800, 600))

#         # load font
#         # fontpath = "/content/Arial.ttf"
#         # font = ImageFont.truetype(fontpath, 32)
#         # b,g,r,a = 0,255,0,0

#         # making the image grayscale
#         grayscale = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#         blurred = cv2.GaussianBlur(grayscale, (5, 5), 0)
#         edged = cv2.Canny(blurred, 10, 200)

#         contours, _ = cv2.findContours(edged, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
#         contours = sorted(contours, key = cv2.contourArea, reverse = True)[:5]

#         for c in contours:
#             perimeter = cv2.arcLength(c, True)
#             approximation = cv2.approxPolyDP(c, 0.02 * perimeter, True)
#             print(approximation)
#             if len(approximation) == 4: # rectangle
#                 number_plate_shape = approximation
#                 break

#         (x, y, w, h) = cv2.boundingRect(number_plate_shape)
#         croped_img = grayscale[y:y + h, x:x + w]
#         cv2.imwrite("extracted.jpg", croped_img)

#         reader = Reader(['en'])
#         detection = reader.readtext(croped_img)
#         plate = ' '.join(detect[1] for detect in detection) #read both line of plate

#         return plate
#     except:
#         return "Không thấy bảng số xe"
import sys
sys.dont_write_bytecode = True
from PIL import Image
import cv2
import torch
import math 
import function.utils as utils_rotate
from IPython.display import display
import os
import function.readplate as helper

yolo_LP_detect = torch.hub.load('yolov5', 'custom', path='model/LP_detector.pt', force_reload=True, source='local')
yolo_license_plate = torch.hub.load('yolov5', 'custom', path='model/LP_ocr.pt', force_reload=True, source='local')

# set model confidence threshold 
# yolo_LP_detect.conf = 0.6
yolo_license_plate.conf = 0.60

def extract_text(path):
    try:
        img = cv2.imread(path)
        # Print path:
        print(f"OCR is reading from image: {path}")
        # Print image details:
        print(f"Image shape: {img.shape}")
        plates = yolo_LP_detect(img, size=640)
        
        list_plates = plates.pandas().xyxy[0].values.tolist()
        list_read_plates = set()
        count = 0
        
        if len(list_plates) == 0:
            lp = helper.read_plate(yolo_license_plate,img)
            if lp != "unknown":
                list_read_plates.add(lp)
        else:
            for plate in list_plates:
                flag = 0
                x = int(plate[0])
                y = int(plate[1])
                w = int(plate[2] - plate[0])
                h = int(plate[3] - plate[1])
                crop_img = img[y:y+h, x:x+w]
                cv2.rectangle(img, (int(plate[0]),int(plate[1])), (int(plate[2]),int(plate[3])), color = (0,0,225), thickness = 2)
                cv2.imwrite("extracted.jpg", crop_img)
                rc_image = cv2.imread("extracted.jpg")
                lp = ""
                count+=1
                for cc in range(0,2):
                    for ct in range(0,2):
                        lp = helper.read_plate(yolo_license_plate, utils_rotate.deskew(crop_img, cc, ct))
                        if lp != "unknown":
                            list_read_plates.add(lp)
                            flag = 1
                            break
                    if flag == 1:
                        break
        return list_read_plates.pop() if list_read_plates else "Không thấy biển số"
    except:
        return "Không thấy biển số"
                
############ Web cam ref code ############
# # load model
# yolo_LP_detect = torch.hub.load('yolov5', 'custom', path='model/LP_detector_nano_61.pt', force_reload=True, source='local')
# yolo_license_plate = torch.hub.load('yolov5', 'custom', path='model/LP_ocr_nano_62.pt', force_reload=True, source='local')
# yolo_license_plate.conf = 0.60

# prev_frame_time = 0
# new_frame_time = 0

# vid = cv2.VideoCapture(0)
# # vid = cv2.VideoCapture("1.mp4")
# while(True):
#     ret, frame = vid.read()
    
#     plates = yolo_LP_detect(frame, size=640)
#     list_plates = plates.pandas().xyxy[0].values.tolist()
#     list_read_plates = set()
#     for plate in list_plates:
#         flag = 0
#         x = int(plate[0]) # xmin
#         y = int(plate[1]) # ymin
#         w = int(plate[2] - plate[0]) # xmax - xmin
#         h = int(plate[3] - plate[1]) # ymax - ymin  
#         crop_img = frame[y:y+h, x:x+w]
#         cv2.rectangle(frame, (int(plate[0]),int(plate[1])), (int(plate[2]),int(plate[3])), color = (0,0,225), thickness = 2)
#         cv2.imwrite("crop.jpg", crop_img)
#         rc_image = cv2.imread("crop.jpg")
#         lp = ""
#         for cc in range(0,2):
#             for ct in range(0,2):
#                 lp = helper.read_plate(yolo_license_plate, utils_rotate.deskew(crop_img, cc, ct))
#                 if lp != "unknown":
#                     list_read_plates.add(lp)
#                     cv2.putText(frame, lp, (int(plate[0]), int(plate[1]-10)), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36,255,12), 2)
#                     flag = 1
#                     break
#             if flag == 1:
#                 break
#     new_frame_time = time.time()
#     fps = 1/(new_frame_time-prev_frame_time)
#     prev_frame_time = new_frame_time
#     fps = int(fps)
#     cv2.putText(frame, str(fps), (7, 70), cv2.FONT_HERSHEY_SIMPLEX, 3, (100, 255, 0), 3, cv2.LINE_AA)
#     cv2.imshow('frame', frame)
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# vid.release()
# cv2.destroyAllWindows()


# print(extract_text("test.jpg"))

    # if len(detection) == 0:
    #     text = "Không thấy bảng số xe"
    #     img_pil = Image.fromarray(img) #image biến lấy khung hình từ webcam
    #     draw = ImageDraw.Draw(img_pil)
    #     draw.text((150, 500), text, font = font, fill = (b, g, r, a))
    #     img = np.array(img_pil) #hiển thị ra window
    #     #cv2.putText(img, text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 3)
    #     cv2.waitKey(0)
    # else:
    #     cv2.drawContours(img, [number_plate_shape], -1, (255, 0, 0), 3)
    #     text ="Biển số: " + f"{plate}"
    #     img_pil = Image.fromarray(img) #image biến lấy khung hình từ webcam
    #     draw = ImageDraw.Draw(img_pil)
    #     draw.text((200, 500), text, font = font, fill = (b, g, r, a))
    #     img = np.array(img_pil) #hiển thị ra window
    #     #cv2.putText(img, text, (x, y - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 0, 0), 2)
    #     cv2.imshow(img)
    #     cv2.waitKey(0)