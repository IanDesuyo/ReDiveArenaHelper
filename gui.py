import eel
import cv2
import numpy as np
import base64
from window_capture import WindowCapture, WindowNotFound
from unit_match import UnitMatch
from api import Api
import win32gui


class GUI:
    def __init__(self):
        self.wc: WindowCapture = None
        self.um = UnitMatch("./assets")
        self.api = Api()
        self.cache_gray: np.ndarray = None
        self.arena_refresh = cv2.imread("./assets/refresh.png", cv2.IMREAD_GRAYSCALE)
        eel.init("./web/build")
        # load all unregistered exposes
        self._set_window()
        self._get_game_view()
        self._get_attack_team()
        self._do_attack()
        # variables
        self.border_fix = 2
        self.find_max_scroll = 40
        self.unit_match_threshold = 0.7

    def run(self):
        eel.start("index.html", size=(1280, 720))

    @eel.expose
    def get_windows():
        windows = []

        def winEnumHandler(hwnd, ctx):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title != "":
                    windows.append({"hwnd": hex(hwnd), "title": title})

        win32gui.EnumWindows(winEnumHandler, None)

        return windows

    def _set_window(self):
        @eel.expose
        def set_window(hwnd: str):
            if isinstance(self.wc, WindowCapture):
                self.wc.exit()

            try:
                self.wc = WindowCapture(hwnd)
                return {"error": False, "message": "Sucess"}

            except WindowNotFound:
                return {"error": True, "message": "Window not found"}

            except Exception as e:
                return {"error": True, "message": str(e)}

    def _get_game_view(self):
        @eel.expose
        def get_game_view(detect: bool = False):
            try:
                cap, gray = self.wc.get()
                if detect:
                    cap, targets = self.parse_arena(cap, gray)
                else:
                    targets = []
                _, buffer = cv2.imencode(".png", cap)
                b64 = base64.b64encode(buffer).decode("utf-8")
                return {"error": False, "image": b64, "targets": targets}
            except Exception as e:
                return {"error": True, "message": str(e)}

    def _get_attack_team(self):
        @eel.expose
        def get_attack_team(def_units: list):
            print("GET_ATTACK_TEAM")
            ans = self.api.search([i["data"]["name_jp"] for i in def_units])

            if not ans:
                return {"error": False, "attack": [], "defense": def_units, "good": 0, "bad": 0, "updated": ""}
            else:
                ans_def = [self.um.find_id(i) for i in ans["def"]]
                best_ans_atk = [self.um.find_id(i) for i in ans["atk"]]
                return {
                    "error": False,
                    "attack": best_ans_atk,
                    "defense": ans_def,
                    "good": ans["good"],
                    "bad": ans["bad"],
                    "updated": ans["updated"],
                }

    def _do_attack(self):
        @eel.expose
        def do_attack(click: tuple, atk_units: list = None):
            _, gray = self.wc.get()
            self.wc.click(*click)
            if atk_units:
                cv2.waitKey(500)
                self.auto_team(gray, atk_units)

    def parse_arena(self, cap: np.ndarray, gray: np.ndarray):
        height, width = gray.shape
        blur = cv2.GaussianBlur(gray, (11, 11), 0)
        edge = cv2.Canny(blur, 40, 120)
        contours, _ = cv2.findContours(edge, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        target_box = []
        for contour in contours:
            (x, y, w, h) = cv2.boundingRect(contour)
            if (h * 5 < w) and (y > height / 5) and (y < height * 0.8) and h > height * 0.15:
                target_box.append([int(x), int(y), int(w), int(h)])
                target_box.append([int(x), int(y), int(w), int(h)])

        target_box, _ = cv2.groupRectangles(target_box, 1, 0.2)
        target_box_images = []
        for (x, y, w, h) in target_box:
            target_box_images.append(
                {
                    "gray": gray[
                        y + self.border_fix : y + h - self.border_fix,
                        x + self.border_fix : x + w - self.border_fix,
                    ],
                    "click": (int(x + (h / 2)), int(y + (h / 2))),
                }
            )
            cv2.rectangle(cap, (x, y), (x + w, y + h), (0, 255, 0), 2)

        target_data = []
        for target_box_image in target_box_images:
            res = self.parse_units(**target_box_image)
            target_data.append(res)

        return cap, target_data

    def parse_units(self, gray: np.ndarray, click: tuple):
        height, width = gray.shape
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        unit_boxes = []
        for contour in contours:
            (x, y, w, h) = cv2.boundingRect(contour)
            slope = w / h
            if round(abs(slope * 10 - 10)) < 1:
                if h > height * 0.6:
                    continue
                elif h > height * 0.2:
                    unit_boxes.append([int(x), int(y), int(w), int(h)])
                    unit_boxes.append([int(x), int(y), int(w), int(h)])

        unit_boxes, _ = cv2.groupRectangles(unit_boxes, 1, 0.2)
        units = []
        for (x, y, w, h) in unit_boxes:
            unit_id, rarity, unit_data = self.um.match(gray[y : y + h, x : x + w])
            units.append({"unit_id": int(unit_id), "rarity": rarity, "data": unit_data, "click": click})

        return units

    def auto_team(self, gray: np.ndarray, units: list):
        height, width = gray.shape
        for i in range(5):  # clean current team
            self.wc.click(int(width * 0.55), int(height * 0.85))
            cv2.waitKey(200)

        cv2.waitKey(500)

        c = 0
        while len(units) > 0 and c < self.find_max_scroll:
            cap, gray = self.wc.get()
            # cv2.imshow("cap", cap)
            for unit in units:  # [i,j] = unit_id, {"raritys": [0], "name_tw": "Unknown", "name_jp": "Unknown"}
                for rarity in unit["data"]["raritys"]:
                    unit_gray = self.um.unit_assets[unit["unit_id"] * 100 + rarity * 10 + 1]
                    unit_gray = cv2.resize(unit_gray[10:54, 10:54], (int(height * 0.12), int(height * 0.12)))
                    # cv2.imshow("unit_gray", unit_gray)
                    res = cv2.matchTemplate(unit_gray, gray, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                    top_left = max_loc
                    # bottom_right = (top_left[0] + 44, top_left[1] + 44)
                    # ts = np.copy(gray)
                    # cv2.rectangle(ts, top_left, bottom_right, (0, 0, 255), 2)
                    # cv2.imshow("ts", ts)

                    if max_val > self.unit_match_threshold:
                        print(unit["data"]["name_tw"], rarity, max_val)
                        top_left = max_loc
                        self.wc.click(top_left[0] + 10, top_left[1] + 10)
                        cv2.waitKey(300)
                        units.remove(unit)
                        break
            c += 1
            if c % 2 == 0:
                self.wc.scroll(int(width / 2), int(height / 2), -int(height / 7.5))
            cv2.waitKey(1000)


app = GUI()
app.run()