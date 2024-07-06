import pywinctl as pwc
import numpy as np

import os
import sys
import cv2
import math

# Use uvloop for faster asyncio drop in replacement
# when available (linux, macos)
if sys.platform not in ["win32", "windows"]:
    import uvloop as asio
else:
    import asyncio as asio

from base64 import b64decode
from skimage.measure import block_reduce
from websockets.server import serve

# More on http://mewbies.com/geek_fun_files/ascii/ascii_art_light_scale_and_gray_scale_chart.htm
# ASCII_CHAR_LIST = r" `.-':_,^=;><+!rc*/z?sLTv)J7(|Fi{C}fI31tlu[neoZ5Yxjya]2ESwqkP6h9d4VpOGbUAKXHm8RD#$Bg0MNWQ%&@"
ASCII_CHAR_LIST = r"@&%QWNM0gB$#DR8mHXKAUbGOpV4d9h6PkqwSE2]ayjxY5Zoen[ult13If}C{iF|(7J)vTLs?z/*cr!+<>;=^,_:'-.` "

ASCII_CHAR_LIST_LEN = len(ASCII_CHAR_LIST) - 1

# Initialized window position and size as None
WINDOW_POS = None
WINDOW_SIZE = None


def moved_callback(pos):
    """Callback for when the tracked window moved.

    In that case, set the WINDOW_POS variable according to the
    current position of the tracked window.
    """
    global WINDOW_POS
    WINDOW_POS = pos


def resized_callback(size):
    """Callback for when the tracked window resized.

    In that case, set the WINDOW_SIZE variable according to the
    current size of the tracked window.
    """
    global WINDOW_SIZE
    WINDOW_SIZE = size


def get_ascii_value(pixel):
    """Return the mapping result of given pixel value with
    the one from the ASCII_CHAR_LIST.
    """
    return ASCII_CHAR_LIST[math.floor(pixel * ASCII_CHAR_LIST_LEN / 255)]


def make_ascii(frame, ratio):
    """Convert the given frame to the corresponding ascii image."""

    # Calculate frame properties
    height, width = frame.shape[:2]
    cols = int(width * ratio)
    rows = int(height * ratio)
    cell_width = width // cols
    cell_height = height // rows

    # Convert frame to grayscale
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Mean pool the frame to further "compress" the frame size to optimize perf
    processed_frame = block_reduce(frame, (cell_width, cell_height), np.mean)

    # Convert each pixel in the frame to its corresponding ascii char
    processed_frame = np.vectorize(get_ascii_value)(processed_frame)
    processed_height, processed_width = processed_frame.shape

    # Get only every 1.25 * y of the frame, effectively dividing
    # the end result of the frame by 1.25
    #
    # This is so that the resulting ascii image do not stretched
    # horizontally too much due to the font size in the terminal
    # (most font size have higher height than its width)
    #
    # You can tweak this number to get the result that fit in your font size
    temp_ascii = ""
    for y in range(int(processed_height // 1.25)):
        for x in range(processed_width):
            temp_ascii += processed_frame[int(y * 1.25), x]
        temp_ascii += "\n"

    return temp_ascii


def base64_to_image(b64_encoded_data):
    """Decode base64 encoded image frame and convert it
    to an image.
    """
    nparr = np.frombuffer(b64decode(b64_encoded_data), np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_COLOR)


async def app_main_handler(websocket):
    """Websocket event handler to handle incoming
    websocket messages.

    This handler will expect every incoming message
    as a base64 encoded image frame that will later
    be decoded and converted to an ascii image and
    cropped in such a way that it matches the current
    window size and position as such:

    +----------------------------------------------+
    |           full screen size image             |
    |                                              |
    |  +-----------------------------+             |
    |  | cropped image based on this |             |
    |  | window size and position    |             |
    |  +-----------------------------+             |
    +----------------------------------------------+
    """
    frame_index = 0
    frame_threshold = 5

    async for message in websocket:
        frame_index += 1

        # Only start processing frame when window position
        # and size already populated with the correct value
        #
        # And also check for the frame index and only process
        # 1 out of Nth frame to further optimize the performance
        #
        # If it looks laggy and that you are sure your machine can
        # actually handle big process very well, then just tweak
        # the frame_threshold
        if (
            WINDOW_POS != None
            and WINDOW_SIZE != None
            and (frame_index % frame_threshold == 0)
        ):
            # Reset frame index
            frame_index = 0

            # Convert base64 encoded frame from javascript to image
            frame = base64_to_image(message)
            height, width = frame.shape[:2]

            # Set the size difference ratio
            size_diff_r = 1 / 10

            # Get current window size and position
            window_x, window_y = WINDOW_POS
            window_width, window_height = WINDOW_SIZE

            # Calculate position based on diff ratio
            calculated_x = int(window_x * size_diff_r)
            calculated_y = int(window_y * size_diff_r)

            # Calculate size based on diff ratio
            calculated_width = int(window_width * size_diff_r)
            calculated_height = int(window_height * size_diff_r)

            # If the calculated position is off the screen then skip
            # the rest of the process and go to the next frame instead
            if calculated_x < 0 or calculated_y < 0:
                continue

            # Crop image based on the calculated size and position to
            # achieve the same effect as to the one in the browser
            cropped_frame = frame[
                calculated_y : calculated_y + calculated_height,
                calculated_x : calculated_x + calculated_width,
            ]

            # Convert the cropped frame to ascii image
            ascii_result = make_ascii(cropped_frame, 1)

            # Clear the screen and print the resulting ascii image
            os.system("cls")
            print(ascii_result)


async def app_main(stop):
    """Main function to start the websocket server"""
    print("Starting application...")
    async with serve(app_main_handler, "localhost", 1337):
        await stop


if __name__ == "__main__":
    # Get current active window which is going to be the one
    # where we start the python cli app
    cur_window = pwc.getActiveWindow()

    # Populate windows position and size with initial value
    WINDOW_POS = cur_window.position
    WINDOW_SIZE = cur_window.size

    # Track the current window position and size changes
    cur_window.watchdog.start(
        movedCB=moved_callback,
        resizedCB=resized_callback,
        interval=0.1,
    )

    # Try to find the current window in case the window
    # title gets renamed
    cur_window.watchdog.setTryToFind(True)

    loop = asio.new_event_loop()
    asio.set_event_loop(loop)

    stop = asio.Future()
    main_task = loop.create_task(app_main(stop))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        main_task.cancel()

        cv2.destroyAllWindows()
        cur_window.watchdog.stop()
