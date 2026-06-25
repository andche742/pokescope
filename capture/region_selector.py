import cv2
import mss
import numpy as np

class RegionSelector:
    def __init__(self, cfg):
        self.cfg = cfg
        self.drawing = False
        self.start = (0, 0)
        self.end = (0, 0)
        self.region_selected = False

    def _mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            print("Left button down")
            self.drawing = True
            self.start = (x, y)
        elif event == cv2.EVENT_MOUSEMOVE and self.drawing:
            print("Mouse move")
            self.end = (x, y)
        elif event == cv2.EVENT_LBUTTONUP:
            print("Left button up")
            self.drawing = False
            self.end = (x, y)
            self.region_selected = True

    def select(self):
        print("Draw a region. Press ENTER to confirm, R to redo.")

        cv2.namedWindow("Region Selector")
        cv2.setMouseCallback("Region Selector", self._mouse_callback)

        with mss.mss() as sct:
            monitor = sct.monitors[1]
            while True:
                # grab fresh frame every loop so it's live
                frame = np.array(sct.grab(monitor))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                preview = frame.copy()

                if self.drawing or self.region_selected:
                    cv2.rectangle(preview, self.start, self.end, (0, 255, 0), 2)

                cv2.putText(preview, "Draw region | ENTER to confirm | R to redo",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                cv2.imshow("Region Selector", preview)

                key = cv2.waitKey(1) & 0xFF
                if key == 13 and self.region_selected: # 13 --> ENTER
                    print("ENTER pressed")
                    cv2.destroyAllWindows()
                    x1 = min(self.start[0], self.end[0])
                    y1 = min(self.start[1], self.end[1])
                    x2 = max(self.start[0], self.end[0])
                    y2 = max(self.start[1], self.end[1])
                    region = {"top": y1, "left": x1, "width": x2 - x1 + 1, "height": y2 - y1 + 1}
                    self.cfg["region"] = region
                    return region
                elif key == ord("r"):
                    print("R pressed")
                    self.region_selected = False
                    self.drawing = False
                    self.start = (0, 0)
                    self.end = (0, 0)
