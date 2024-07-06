from skimage.measure import block_reduce
import numpy as np
import cv2
import math
import os

from PIL import Image, ImageDraw, ImageFont
import numpy as np
import time


def drawText(text):
    myfont = ImageFont.truetype("/mnt/c/Windows/Fonts/CascadiaCode.ttf", 12)
    size = myfont.getbbox(text)[2:]
    img = Image.new("1", size, "black")

    draw = ImageDraw.Draw(img)
    draw.text((0, 0), text, "white", font=myfont, stroke_fill="#000", stroke_width=100)

    pixels = np.array(img, dtype=np.uint8)
    chars = np.array([" ", "#"], dtype="U1")[pixels]
    strings = chars.view("U" + str(chars.shape[1])).flatten()
    return "\n".join(strings)


ascii_list = r"&0RAVP2Y[IFv/<_ "


def get_ascii_value(pixel):
    return ascii_list[math.floor(pixel * (len(ascii_list) - 1) / 255)]


def charmap(current_frame):
    return np.vectorize(get_ascii_value)(current_frame)


def grayscale(current_frame):
    return cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)


def downsize(current_frame, block_y, block_x):
    return block_reduce(current_frame, (block_y, block_x), np.mean)


def proses(current_frame):
    grayscaled_frame = grayscale(current_frame)
    downsized_frame = downsize(grayscaled_frame, 10, 8)
    ascii_result = charmap(downsized_frame)
    height, width = ascii_result.shape

    text = ""
    for y in range(height):
        for x in range(width):
            text += ascii_result[y, x]
        text += "\n"

    return text


videoObject = cv2.VideoCapture("./youtube/src/assets/sample_video.mp4")

times = []
while True:
    success, frame = videoObject.read()

    if not success:
        videoObject.release()
        break

    start_time = time.time_ns()
    asciiText = proses(frame)
    end_time = time.time_ns()

    if len(times) > 10:
        times.pop(0)

    fps = round(1 / ((end_time - start_time) / 1_000_000_000), 2)
    times.append(fps)

    fpsText = drawText(f"FPS = {round(np.mean(times), 2)}")

    os.system("clear")
    print(asciiText)
    print(fpsText)
