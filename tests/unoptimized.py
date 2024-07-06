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
    print("\n".join(strings))


ascii_list = r"&0RAVP2Y[IFv/<_ "


def get_ascii_value(pixel):
    return ascii_list[math.floor(pixel * (len(ascii_list) - 1) / 255)]


def charmap(current_frame):
    current_frame = np.array(current_frame)
    height, width = current_frame.shape[:2]

    ascii_result = ""
    for y in range(height):
        for x in range(width):
            ascii_result += get_ascii_value(current_frame[y, x])
        ascii_result += "\n"

    return ascii_result


def grayscale(current_frame):
    height, width = current_frame.shape[:2]

    for y in range(height):
        for x in range(width):
            b, g, r = current_frame[y, x]

            current_frame[y, x] = (0.2126 * r) + (0.7152 * g) + (0.0722 * b)

    return current_frame


def downsize(current_frame, block_y, block_x):
    result = []
    for y in range(len(current_frame) // block_y):
        temp_row = []
        for x in range(len(current_frame[y]) // block_x):
            current_y = y * block_y
            current_x = x * block_x

            block_data = current_frame[
                current_y : current_y + block_y, current_x : current_x + block_x
            ]

            temp_row.append(np.mean(block_data))
        result.append(temp_row)

    return result


def proses(current_frame):
    grayscaled_frame = grayscale(current_frame)
    downsized_frame = downsize(grayscaled_frame, 10, 8)
    ascii_result = charmap(downsized_frame)

    os.system("clear")
    print(ascii_result)


videoObject = cv2.VideoCapture("./youtube/src/assets/sample_video.mp4")

times = []
while True:
    success, frame = videoObject.read()

    if not success:
        videoObject.release()
        break

    start_time = time.time_ns()
    proses(frame)
    end_time = time.time_ns()

    if len(times) > 10:
        times.pop(0)

    fps = round(1 / ((end_time - start_time) / 1_000_000_000), 2)
    times.append(fps)

    drawText(f"FPS = {round(np.mean(times), 2)}")
