from window_capture import WindowCapture, WindowNotFound
from unit_match import UnitMatch
from api import Api
import cv2
import numpy as np
import win32gui


class ReDiveArenaHelper:
    def __init__(self, window_title: str):
        hwnd = win32gui.FindWindow(None, window_title)
        if not hwnd:
            raise WindowNotFound

        self.wc = WindowCapture(hwnd)
        self.um = UnitMatch("./assets")
        self.api = Api()
        self.border_fix = 2

        self.princess_arena_check = cv2.imread("./assets/princess_arena.png", cv2.IMREAD_GRAYSCALE)
        self.arena_refresh = cv2.imread("./assets/refresh.png", cv2.IMREAD_GRAYSCALE)
        self.find_max_scroll = 40
        self.unit_match_threshold = 0.7
        self.fps = 100000

    def run(self):
        while True:
            cap, gray = self.wc.get()

            # check is princess arena or not
            res = cv2.matchTemplate(self.princess_arena_check, gray, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            if max_val > 0.9:
                print("princess arena")
                cv2.waitKey(1000)
            else:
                self.parse_arena(cap, gray)

    def parse_arena(self, cap: np.ndarray, gray: np.ndarray):
        height, width = gray.shape
        blur = cv2.GaussianBlur(gray, (11, 11), 0)
        # cv2.imshow("blur", blur)
        edge = cv2.Canny(blur, 40, 120)
        # cv2.imshow("edge", edge)
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
                    "cap": cap[
                        y + self.border_fix : y + h - self.border_fix,
                        x + self.border_fix : x + w - self.border_fix,
                    ],
                    "gray": gray[
                        y + self.border_fix : y + h - self.border_fix,
                        x + self.border_fix : x + w - self.border_fix,
                    ],
                    "click": (int(x + (h / 2)), int(y + (h / 2))),
                }
            )
            cv2.rectangle(cap, (x, y), (x + w, y + h), (0, 255, 0), 2)

        cv2.imshow("CAP", cap)

        target_data = []
        for target_box_image in target_box_images:
            res = self.parse_units(**target_box_image)
            if res:
                target_data.append(res)

        if len(target_data) == 0:
            cv2.waitKey(1000)
            return

        print("=" * 35)
        for i in range(len(target_data)):
            print(f"Target {i+1}:", [j[2].get("name_tw", j[2]["name_jp"]) for j in target_data[i][0]])
        print("=" * 35 + "\nPlease select the target or press 'r' to refresh...")

        key = cv2.waitKey(120000)
        if key == ord("1"):
            target_id = 0
        elif key == ord("2"):
            target_id = 1
        elif key == ord("3"):
            target_id = 2
        elif key == ord("r"):
            res = cv2.matchTemplate(self.arena_refresh, gray, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            top_left = max_loc
            self.wc.click(top_left[0] + 5, top_left[1] + 5)
            cv2.waitKey(2000)
            print("\n" * 5)
            return
        else:
            print("\n" * 5)
            return
        print("Target", target_id + 1, "selected.")

        atk_units = self.fetch_group(target_data[target_id])
        self.wc.click(*target_box_images[target_id]["click"])
        if atk_units:
            cv2.waitKey(1000)
            self.auto_select_team(gray, atk_units)

        print("Press any key after you finish the battle.")
        cv2.waitKey(0)
        print("\n" * 5)

    def parse_units(self, cap: np.ndarray, gray: np.ndarray, click: tuple):
        height, width = gray.shape
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # cv2.imshow("thresh", thresh)
        unit_boxes = []
        for contour in contours:
            (x, y, w, h) = cv2.boundingRect(contour)
            slope = w / h
            if round(abs(slope * 10 - 10)) < 1:
                if h > height * 0.5:
                    cv2.rectangle(cap, (x, y), (x + w, y + h), (255, 0, 0), 2)
                elif h > height * 0.2:
                    unit_boxes.append([int(x), int(y), int(w), int(h)])
                    unit_boxes.append([int(x), int(y), int(w), int(h)])

        unit_boxes, _ = cv2.groupRectangles(unit_boxes, 1, 0.2)
        units = []
        for (x, y, w, h) in unit_boxes:
            unit_id, rarity, unit_data = self.um.match(gray[y : y + h, x : x + w])
            cv2.rectangle(cap, (x, y), (x + w, y + h), (0, 255, 0), 2)
            units.append([unit_id, rarity, unit_data])

        if len(units) > 0:
            return units, cap

    def fetch_group(self, units: list):
        unit_names_jp = [i[2].get("name_jp") for i in units[0]]
        unit_names_tw = [i[2].get("name_tw") for i in units[0]]

        best_ans = self.api.search(unit_names_jp)
        print("=" * 35)
        if not best_ans:
            print("Defense :", unit_names_tw)
            print("Attack  :", "Not Found")
            print("=" * 35)
        else:
            best_ans_def = [self.um.find_id(i)[1].get("name_tw") for i in best_ans["def"]]
            best_ans_atk = [self.um.find_id(i)[1].get("name_tw") for i in best_ans["atk"]]
            best_ans_atk_units = [self.um.find_id(i) for i in best_ans["atk"]]
            print("Defense :", best_ans_def)
            print("Attack  :", best_ans_atk)
            print("Good/Bad:", best_ans["good"], best_ans["bad"])
            print("Updated :", best_ans["updated"])
            # atk_units = self.um.unit_assets[best_ans_atk_ids[0] * 100 + 31]
            # for i in range(1, len(best_ans_atk_ids)):
            #     atk_units = cv2.hconcat([atk_units, self.um.unit_assets[best_ans_atk_ids[i] * 100 + 31]])

            # cv2.imshow("ANS", atk_units)
            return best_ans_atk_units
        print("=" * 35)

    def auto_select_team(self, gray: np.ndarray, units: list):
        height, width = gray.shape
        for i in range(5):  # clean current team
            self.wc.click(int(width * 0.55), int(height * 0.85))
            cv2.waitKey(200)

        c = 0
        while len(units) > 0 and c < self.find_max_scroll:
            cap, gray = self.wc.get()
            # cv2.imshow("cap", cap)
            for unit_id, data in units:  # [i,j] = unit_id, {"raritys": [0], "name_tw": "Unknown", "name_jp": "Unknown"}
                for rarity in data["raritys"]:
                    unit_gray = self.um.unit_assets[unit_id * 100 + rarity * 10 + 1]
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
                        print(data["name_tw"], rarity, max_val)
                        top_left = max_loc
                        self.wc.click(top_left[0] + 10, top_left[1] + 10)
                        cv2.waitKey(300)
                        units.remove((unit_id, data))
                        break
            c += 1
            if c % 2 == 0:
                self.wc.scroll(int(width / 2), int(height / 2), -int(height / 7.5))
            cv2.waitKey(1000)


app = ReDiveArenaHelper("ASUS_Z01RD")
app.run()