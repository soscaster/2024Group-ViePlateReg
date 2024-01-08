# from PIL import ImageFont, ImageDraw, Image
# import numpy as np
from easyocr import Reader
import cv2

def extract_text(path):
# loading images and resizing
    img = cv2.imread(path)
    img = cv2.resize(img, (800, 600))

    # load font
    # fontpath = "/content/Arial.ttf"
    # font = ImageFont.truetype(fontpath, 32)
    # b,g,r,a = 0,255,0,0

    # making the image grayscale
    grayscale = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(grayscale, (5, 5), 0)
    edged = cv2.Canny(blurred, 10, 200)

    contours, _ = cv2.findContours(edged, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key = cv2.contourArea, reverse = True)[:5]

    for c in contours:
        perimeter = cv2.arcLength(c, True)
        approximation = cv2.approxPolyDP(c, 0.02 * perimeter, True)
        print(approximation)
        if len(approximation) == 4: # rectangle
            number_plate_shape = approximation
            break

    (x, y, w, h) = cv2.boundingRect(number_plate_shape)
    croped_img = grayscale[y:y + h, x:x + w]

    reader = Reader(['en'])
    detection = reader.readtext(croped_img)
    plate = ' '.join(detect[1] for detect in detection) #read both line of plate

    return plate, croped_img

print(extract_text("test.jpg"))

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