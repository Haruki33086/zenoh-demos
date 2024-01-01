import argparse
import cv2
import zenoh
import numpy as np
import json
import pyautogui

# 引数パーサーの設定
parser = argparse.ArgumentParser(prog='zcapture', description='Zenoh screen capture example')
parser.add_argument('-m', '--mode', type=str, choices=['peer', 'client'], help='Zenoh session mode.')
parser.add_argument('-e', '--connect', type=str, metavar='ENDPOINT', action='append', help='Zenoh endpoints to connect to.')
parser.add_argument('-l', '--listen', type=str, metavar='ENDPOINT', action='append', help='Zenoh endpoints to listen on.')
parser.add_argument('-w', '--width', type=int, default=780, help='Width of the published frames')
parser.add_argument('-q', '--quality', type=int, default=95, help='Quality of the published frames (0 - 100)')
parser.add_argument('-k', '--key', type=str, default='simu/camera', help='Key expression for the publication')
parser.add_argument('-c', '--config', type=str, metavar='FILE', help='A zenoh configuration file.')

args = parser.parse_args()

# Zenohの設定
conf = zenoh.config_from_file(args.config) if args.config is not None else zenoh.Config()
if args.mode is not None:
    conf.insert_json5(zenoh.config.MODE_KEY, json.dumps(args.mode))
if args.connect is not None:
    conf.insert_json5(zenoh.config.CONNECT_KEY, json.dumps(args.connect))
if args.listen is not None:
    conf.insert_json5(zenoh.config.LISTEN_KEY, json.dumps(args.listen))

zenoh.init_logger()
z = zenoh.open(conf)

jpeg_opts = [int(cv2.IMWRITE_JPEG_QUALITY), args.quality]

# スクリーンキャプチャ機能
def capture_screen():
    screen = pyautogui.screenshot()
    frame = np.array(screen)
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

try:
    while True:
        frame = capture_screen()
        frame = cv2.resize(frame, (args.width, int(args.width * frame.shape[0] / frame.shape[1])))
        _, jpeg = cv2.imencode('.jpg', frame, jpeg_opts)
        z.put(args.key, jpeg.tobytes())
finally:
    # Zenohセッションを閉じる
    z.close()