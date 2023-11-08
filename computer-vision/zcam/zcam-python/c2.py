import argparse
import cv2
import zenoh
import json

parser = argparse.ArgumentParser(
    prog='zcapture',
    description='zenoh video capture example')
parser.add_argument('-m', '--mode', type=str, choices=['peer', 'client'],
                    help='The zenoh session mode.')
parser.add_argument('-e', '--connect', type=str, metavar='ENDPOINT', action='append',
                    help='zenoh endpoints to connect to.')
parser.add_argument('-l', '--listen', type=str, metavar='ENDPOINT', action='append',
                    help='zenoh endpoints to listen on.')
parser.add_argument('-w', '--width', type=int, default=780,
                    help='width of the published frames')
parser.add_argument('-q', '--quality', type=int, default=95,
                    help='quality of the published frames (0 - 100)')
parser.add_argument('-k', '--key', type=str, default='demo/zcam',
                    help='key expression')
parser.add_argument('-c', '--config', type=str, metavar='FILE',
                    help='A zenoh configuration file.')
parser.add_argument('-n', '--number', type=int, default=0,
                    help='A zenoh camera number.')
parser.add_argument('-rw', '--resolution_width', type=int, default=640,
                    help='resolution.')
parser.add_argument('-rh', '--resolution_height', type=int, default=480,
                    help='resolution')
parser.add_argument('-r', '--framerate', type=int, default=30,
                    help='frame rate')

args = parser.parse_args()

jpeg_opts = [int(cv2.IMWRITE_JPEG_QUALITY), args.quality]

conf = zenoh.config_from_file(args.config) if args.config is not None else zenoh.Config()
if args.mode is not None:
    conf.insert_json5(zenoh.config.MODE_KEY, json.dumps(args.mode))
if args.connect is not None:
    conf.insert_json5(zenoh.config.CONNECT_KEY, json.dumps(args.connect))
if args.listen is not None:
    conf.insert_json5(zenoh.config.LISTEN_KEY, json.dumps(args.listen))

print('[INFO] Open zenoh session...')
zenoh.init_logger()
z = zenoh.open(conf)

print('[INFO] Open camera...')
vs = cv2.VideoCapture(args.number)
vs.set(cv2.CAP_PROP_FRAME_WIDTH, args.resolution_width)
vs.set(cv2.CAP_PROP_FRAME_HEIGHT, args.resolution_height)
vs.set(cv2.CAP_PROP_FPS, args.framerate)

# Define the target frame size for resizing
target_frame_size = (args.width, int(args.width * args.resolution_height / args.resolution_width))
# Set the buffer size (e.g., 1) to minimize delay
vs.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Adjust the buffer size as needed

while True:
    ret, frame = vs.read()
    if ret:
        # Resize the frame
        frame = cv2.resize(frame, target_frame_size)
        _, jpeg = cv2.imencode('.jpg', frame, jpeg_opts)
        z.put(args.key, jpeg.tobytes())

