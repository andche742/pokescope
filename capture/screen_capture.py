import mss
import numpy as np
import cv2

class ScreenCapture:
    def __init__(self, cfg):
        self.cfg = cfg
        self.sct = mss.mss()

    def grab(self):
        region = self.cfg.get("region")
        if not region:
            raise ValueError("No region defined. Run RegionSelector first.")
        frame = np.array(self.sct.grab(region))
        return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

    def __del__(self):
        self.sct.close()