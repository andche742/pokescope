import json
import cv2
from capture.screen_capture import ScreenCapture
from capture.region_selector import RegionSelector

CONFIG_PATH = "config.json"

def load_config():
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        default = {
            "region": None,
            "poll_interval_ms": 100,
        }
        save_config(default)
        return default

def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)

def main():
    cfg = load_config()

    selector = RegionSelector(cfg)
    capture = ScreenCapture(cfg)

    # Select region if not saved
    if not cfg.get("region"):
        print("No region saved. Select one now.")
        selector.select()
        save_config(cfg)
        print(f"Region saved: {cfg['region']}")

    print("Streaming. Q to quit, R to reset region.")

    while True:
        frame = capture.grab()
        cv2.imshow("PokeScope", frame)

        key = cv2.waitKey(cfg.get("poll_interval_ms", 10)) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("r"):
            selector.select()
            save_config(cfg)
            print(f"Region updated: {cfg['region']}")

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()