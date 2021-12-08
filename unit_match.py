import logging
import sqlite3
import os
import cv2
import numpy as np
from typing import Dict, List, NamedTuple, Tuple
from copy import deepcopy


class Unit(NamedTuple):
    unit_id: int
    raritys: List[int]
    name_jp: str
    name_tw: str
    rarity: int = None

    def as_dict(self):
        return {
            "unit_id": self.unit_id,
            "raritys": self.raritys,
            "name_jp": self.name_jp,
            "name_tw": self.name_tw,
            "rarity": self.rarity,
        }

    def __str__(self):
        s = f"{self.unit_id}({self.name_jp}"
        if self.rarity:
            s += f", rarity {self.rarity}"
        s += ")"
        return s


class UnitMatch:
    def __init__(self, path: str):
        self.logger = logging.getLogger("UnitMatch")
        self.logger.info("Initializing...")
        self.path = path
        self.tw_db = sqlite3.connect(os.path.join(path, "redive_tw.db"))
        self.jp_db = sqlite3.connect(os.path.join(path, "redive_jp.db"))

        self.units = self.get_units()
        self.template_map, self.unit_map, self.unit_assets = self.load_assets()
        self.logger.info("Ready.")

    def get_units(self) -> Dict[int, Unit]:
        jp_cur = self.jp_db.cursor()
        tw_cur = self.tw_db.cursor()
        jp_cur.execute(
            "SELECT p.unit_id, max(rarity) as max_rarity, p.unit_name as name FROM unit_rarity r JOIN unit_profile p on r.unit_id = p.unit_id GROUP BY r.unit_id"
        )
        tw_cur.execute("SELECT unit_id, unit_name as name FROM unit_profile")
        tw_names = {int(i[0] / 100): i[1] for i in tw_cur.fetchall()}

        units = {1000: Unit(unit_id=1000, raritys=[0], name_jp="Unknown", name_tw="Unknown")}
        for jp in jp_cur.fetchall():
            units[int(jp[0] / 100)] = Unit(
                unit_id=int(jp[0] / 100),
                raritys=[1, 3, 6] if jp[1] == 6 else [1, 3],
                name_jp=jp[2],
                name_tw=tw_names.get(int(jp[0] / 100)),
            )

        self.logger.info(f"{len(units)} units found.")
        return units

    def load_assets(self, use_cache: bool = True) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        self.logger.info("Loading assets...")
        cache_path = os.path.join(self.path, "units_cache.npy")
        if use_cache and os.path.exists(cache_path):
            return np.load(cache_path, allow_pickle=True)

        unit_assets = {}
        for unit_id, data in self.units.items():
            for rarity in data.raritys:
                unit_assets[unit_id * 100 + rarity * 10 + 1] = self.get_image(unit_id * 100 + rarity * 10 + 1)

        template = list(unit_assets.values())
        unit_ids = list(unit_assets.keys())
        x_template = []
        blank_images = []

        for i in range(10 - len(template) % 10):
            blank_image = np.zeros((template[0].shape[1], template[0].shape[0], 3), np.uint8)
            blank_images.append(cv2.cvtColor(blank_image, cv2.COLOR_BGR2GRAY))
            unit_ids.append(0)
        template += blank_images

        two_template = [template[i : i + 10] for i in range(0, len(template), 10)]
        unit_map = np.array([unit_ids[i : i + 10] for i in range(0, len(unit_ids), 10)])

        for i in range(len(two_template)):
            x_template.append(cv2.hconcat(two_template[i]))

        template_map = cv2.vconcat(x_template)

        np.save(cache_path, [template_map, unit_map, unit_assets])
        return template_map, unit_map, unit_assets

    def get_image(self, unit_id: int) -> np.ndarray:
        """
        get the image by unit_id.

        Args:
            unit_id (int): 6-digits unit id.

        Returns:
            np.ndarray: image of the unit.
        """
        img = cv2.imread(os.path.join(self.path, f"character_unit/{unit_id:06}.webp"), cv2.IMREAD_GRAYSCALE)
        return cv2.resize(img, (64, 64), interpolation=cv2.INTER_AREA)

    def match(self, image: np.ndarray) -> Unit:
        """
        Find the most similar unit by image.

        Args:
            image (np.ndarray): image to search.

        Returns:
            Unit: the most similar unit.
        """
        image = cv2.resize(image, (64, 64), interpolation=cv2.INTER_AREA)
        image = image[10:54, 10:54]
        w, h = image.shape[::-1]

        res = cv2.matchTemplate(image, self.template_map, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        top_left = max_loc
        bottom_right = (top_left[0] + w, top_left[1] + h)
        map_x, map_y = int(top_left[1] / 64), int(top_left[0] / 64)

        unit_id = self.unit_map[map_x, map_y]
        unit = deepcopy(self.units[int(unit_id / 100)])._replace(rarity=int(str(unit_id)[4]))

        self.logger.info(f"Most Similar: {unit}({max_val:.3f})")
        return unit

    def find_id(self, name: str) -> Unit:
        """
        Find the unit by name.

        Args:
            name (str): character's Chinese or Japanese name.

        Returns:
            Unit: unit object if exist, otherwise None.
        """
        for i, j in self.units.items():
            if j.name_jp == name or j.name_tw == name:
                return j
