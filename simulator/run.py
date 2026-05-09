import subprocess
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from simulator.mqtt_simulator import *

if __name__ == "__main__":
    print("[Run] Starting simulator...")
    publish_loop()