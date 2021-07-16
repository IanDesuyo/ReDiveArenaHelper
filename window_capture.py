from time import sleep
import cv2
import win32gui
import win32ui
import win32con
import win32api
import win32clipboard
from ctypes import windll
from PIL import Image
import numpy as np
from pynput.keyboard import Controller

class WindowNotFound(Exception):
    pass



class WindowCapture:
    def __init__(self, window_title: str):
        self.hwnd = win32gui.FindWindow(None, window_title)
        if not self.hwnd:
            raise WindowNotFound

        self.hwndDC = win32gui.GetWindowDC(self.hwnd)
        self.mfcDC = win32ui.CreateDCFromHandle(self.hwndDC)
        self.saveDC = self.mfcDC.CreateCompatibleDC()
        self.saveBitMap = win32ui.CreateBitmap()
        self.keyboard = Controller()

    def get(self):
        try:
            left, top, right, bot = win32gui.GetWindowRect(self.hwnd)
        except:
            raise WindowNotFound

        w = right - left
        h = bot - top
        self.saveBitMap.CreateCompatibleBitmap(self.mfcDC, w, h)

        self.saveDC.SelectObject(self.saveBitMap)

        # Change the line below depending on whether you want the whole window
        # or just the client area.
        windll.user32.PrintWindow(self.hwnd, self.saveDC.GetSafeHdc(), 1)
        # windll.user32.PrintWindow(self.hwnd, self.saveDC.GetSafeHdc(), 0)

        bmpinfo = self.saveBitMap.GetInfo()
        bmpstr = self.saveBitMap.GetBitmapBits(True)

        img = Image.frombuffer("RGB", (bmpinfo["bmWidth"], bmpinfo["bmHeight"]), bmpstr, "raw", "BGRX", 0, 1)
        img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        _, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnt = contours[0]
        x, y, w, h = cv2.boundingRect(cnt)

        crop = img[y : y + h, x : x + w]
        crop_gray = gray[y : y + h, x : x + w]

        return crop, crop_gray

    def exit(self):
        win32gui.DeleteObject(self.saveBitMap.GetHandle())
        self.saveDC.DeleteDC()
        self.mfcDC.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, self.hwndDC)

    def click(self, x: int, y: int):
        win32gui.SetForegroundWindow(self.hwnd)
        win32gui.SetActiveWindow(self.hwnd)
        left, top, right, bot = win32gui.GetWindowRect(self.hwnd)
        win32api.SetCursorPos((left + 8 + x, top + 31 + y))
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)

    def get_current_pos(self):
        x, y = win32gui.GetCursorPos()
        left, top, right, bot = win32gui.GetWindowRect(self.hwnd)
        return x - left - 8, y - top - 31

    def type_text(self, text: str):
        # self.keyboard.type(text)
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
        win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
        win32api.keybd_event(86, 0, 0, 0)
        win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(86, 0, win32con.KEYEVENTF_KEYUP, 0)
        win32clipboard.CloseClipboard()
