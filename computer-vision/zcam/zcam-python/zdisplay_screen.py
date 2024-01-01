import argparse
import time
import cv2
import zenoh
import numpy as np
import json

# Setting up the argument parser
parser = argparse.ArgumentParser(prog='zdisplay', description='Zenoh video display example')
parser.add_argument('-m', '--mode', type=str, choices=['peer', 'client'], help='The zenoh session mode.')
parser.add_argument('-e', '--connect', type=str, metavar='ENDPOINT', action='append', help='Zenoh endpoints to connect to.')
parser.add_argument('-l', '--listen', type=str, metavar='ENDPOINT', action='append', help='Zenoh endpoints to listen on.')
parser.add_argument('-d', '--delay', type=float, default=0.05, help='Delay between each frame in seconds')
parser.add_argument('-k', '--key', type=str, default='simu/camera', help='Key expression for the subscription')
parser.add_argument('-c', '--config', type=str, metavar='FILE', help='A zenoh configuration file.')

args = parser.parse_args()

# Zenoh configuration
conf = zenoh.config_from_file(args.config) if args.config is not None else zenoh.Config()
if args.mode is not None:
    conf.insert_json5(zenoh.config.MODE_KEY, json.dumps(args.mode))
if args.connect is not None:
    conf.insert_json5(zenoh.config.CONNECT_KEY, json.dumps(args.connect))
if args.listen is not None:
    conf.insert_json5(zenoh.config.LISTEN_KEY, json.dumps(args.listen))

# Dictionary to store frames for each camera
cams = {}

# Frames listener function
def frames_listener(sample):
    npImage = np.frombuffer(bytes(sample.value.payload), dtype=np.uint8)
    matImage = cv2.imdecode(npImage, 1)
    cams[sample.key_expr] = matImage

# Open zenoh session
print('[INFO] Open zenoh session...')
zenoh.init_logger()
z = zenoh.open(conf)

# Declare the subscriber
sub = z.declare_subscriber(args.key, frames_listener)

# Main loop to display frames
try:
    while True:
        for cam in list(cams):
            cv2.imshow(str(cam), cams[cam])

        key = cv2.waitKey(1) & 0xFF
        time.sleep(args.delay)

        # Exit loop if 'q' is pressed
        if key == ord('q'):
            break

finally:
    cv2.destroyAllWindows()

# Close zenoh session
z.close()
