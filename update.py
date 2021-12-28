import requests
from bs4 import BeautifulSoup
import os
import json
import brotli
import logging

logger = logging.getLogger("Updater")


def update(path: str):
    logger.info("Checking data version...")
    has_update = False
    if os.path.exists(os.path.join(path, "version.json")):
        with open(os.path.join(path, "version.json")) as f:
            version = json.load(f)
    else:
        version = {}

    # check tw version
    r = requests.get("https://randosoru.me/redive_db/version.json")
    tw_ver = r.json()["TruthVersion"]
    logger.info(f"[TW]Latest version: {tw_ver}, current is {version.get('tw')}.")

    if version.get("tw") != tw_ver:
        r = requests.get("https://randosoru.me/redive_db/redive_tw.db.br")

        with open(os.path.join(path, "redive_tw.db"), "wb+") as f:
            f.write(brotli.decompress(r.content))

        version["tw"] = tw_ver
        has_update = True
        logger.info(f"[TW]Database updated.")

    # check jp version
    r = requests.get("https://redive.estertion.win/last_version_jp.json")
    jp_ver = r.json()["TruthVersion"]
    logger.info(f"[JP]Latest version: {jp_ver}, current is {version.get('jp')}.")

    if version.get("jp") != jp_ver:
        r = requests.get("https://redive.estertion.win/db/redive_jp.db.br")

        with open(os.path.join(path, "redive_jp.db"), "wb+") as f:
            f.write(brotli.decompress(r.content))

        version["jp"] = jp_ver
        has_update = True
        logger.info(f"[JP]Database updated.")

    with open(os.path.join(path, "version.json"), "w+") as f:
        json.dump(version, f)

    if has_update:
        # update character units
        logger.info(f"Checking assets...")
        exist_images = set(os.listdir(os.path.join(path, "character_unit")))

        r = requests.get("https://redive.estertion.win/icon/unit/")
        soup = BeautifulSoup(r.text, "html.parser")

        images = soup.select(".item img")
        images = set([i.get("title") for i in images])

        for image in images - exist_images:
            if int(image[:2]) > 18 or len(image) > 12:
                continue

            img = requests.get(f"https://redive.estertion.win/icon/unit/{image}")
            with open(os.path.join(path, f"character_unit/{image}"), "wb+") as f:
                f.write(img.content)

            logger.info(f"{image} downloaded.")

        if os.path.exists(os.path.join(path, "units_cache.npy")):
            os.remove(os.path.join(path, "units_cache.npy"))
            logger.info(f"units_cache.npy deleted.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="[%(levelname)s][%(asctime)s][%(name)s] %(message)s", datefmt="%Y/%m/%d %H:%M:%S"
    )

    update("./assets")
