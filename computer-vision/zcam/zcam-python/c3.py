import argparse
import cv2
import zenoh
import json
import threading
import queue

def parse_arguments():
    parser = argparse.ArgumentParser(prog='zcapture', description='Zenoh video capture example')
    parser.add_argument('-m', '--mode', type=str, choices=['peer', 'client'], help='The Zenoh session mode.')
    parser.add_argument('-e', '--connect', type=str, metavar='ENDPOINT', action='append', help='Zenoh endpoints to connect to.')
    parser.add_argument('-l', '--listen', type=str, metavar='ENDPOINT', action='append', help='Zenoh endpoints to listen on.')
    parser.add_argument('-w', '--width', type=int, default=780, help='Width of the published frames')
    parser.add_argument('-q', '--quality', type=int, default=95, help='Quality of the published frames (0 - 100)')
    parser.add_argument('-k', '--key', type=str, default='demo/zcam', help='Key expression')
    parser.add_argument('-c', '--config', type=str, metavar='FILE', help='A Zenoh configuration file.')
    parser.add_argument('-n', '--number', type=int, default=0, help='Zenoh camera number.')
    parser.add_argument('-rw', '--resolution_width', type=int, default=1280, help='Resolution width.')
    parser.add_argument('-rh', '--resolution_height', type=int, default=720, help='Resolution height.')
    parser.add_argument('-r', '--framerate', type=int, default=30, help='Frame rate')
    return parser.parse_args()

def configure_zenoh(args):
    conf = zenoh.Config.from_file(args.config) if args.config else zenoh.Config()
    if args.mode:
        conf.insert_json5("mode", json.dumps(args.mode))
    if args.connect:
        conf.insert_json5("connect/endopoints", json.dumps(args.connect))
    if args.listen:
        conf.insert_json5("listen/endopoints", json.dumps(args.listen))
    return conf

def open_camera(args):
    vs = cv2.VideoCapture(args.number)
    vs.set(cv2.CAP_PROP_FRAME_WIDTH, args.resolution_width)
    vs.set(cv2.CAP_PROP_FRAME_HEIGHT, args.resolution_height)
    vs.set(cv2.CAP_PROP_FPS, args.framerate)
    vs.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Adjust buffer size as needed
    return vs

def frame_capture(vs, frame_queue, stop_event):
    while not stop_event.is_set():
        ret, frame = vs.read()
        if ret:
            if frame_queue.full():  # キューがいっぱいの場合、古いフレームを捨てる
                frame_queue.get()
            frame_queue.put(frame)

def main():
    args = parse_arguments()
    jpeg_opts = [int(cv2.IMWRITE_JPEG_QUALITY), args.quality]
    conf = configure_zenoh(args)

    print('[INFO] Open Zenoh session...')
    zenoh.try_init_log_from_env()
    z = zenoh.open(conf)

    print('[INFO] Open camera...')
    vs = open_camera(args)

    frame_queue = queue.Queue(maxsize=2)  # フレームバッファサイズを小さく保つ
    stop_event = threading.Event()
    capture_thread = threading.Thread(target=frame_capture, args=(vs, frame_queue, stop_event))
    capture_thread.start()

    target_frame_size = (args.width, int(args.width * args.resolution_height / args.resolution_width))

    try:
        while True:
            if not frame_queue.empty():
                frame = frame_queue.get()
                frame = cv2.resize(frame, target_frame_size)
                _, jpeg = cv2.imencode('.jpg', frame, jpeg_opts)
                z.put(args.key, jpeg.tobytes())
    except KeyboardInterrupt:
        stop_event.set()
        capture_thread.join()

    vs.release()
    z.close()

if __name__ == "__main__":
    main()
