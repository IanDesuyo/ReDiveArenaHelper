from copy import deepcopy
import logging
from seleniumwire.webdriver import Chrome, ChromeOptions
from typing import Dict, List, NamedTuple
from unit_match import Unit, UnitMatch
import json
from seleniumwire.server import logger as server_logger
from seleniumwire.handler import log as handler_logger

for logger in [
    "geventwebsocket.handler",
    "seleniumwire.handler",
    "seleniumwire.server",
    "seleniumwire.storage",
    "seleniumwire.backend",
]:
    logging.getLogger(logger).setLevel(logging.WARN)


class AttackData(NamedTuple):
    good: int
    bad: int
    units: List[Unit]

    def as_dict(self):
        return {"good": self.good, "bad": self.bad, "units": [unit.as_dict() for unit in self.units]}


class Api:
    def __init__(self, um: UnitMatch):
        self.logger = logging.getLogger("API")
        self.logger.info("Initializing...")
        self.um = um
        options = ChromeOptions()
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        self.driver = Chrome(options=options)

        self.driver.get("https://www.pcrdfans.com/battle")
        self.unit_ids: Dict[int, int] = self.driver.execute_script(
            """\
            document.querySelectorAll(".battle_chara_select .ant-collapse-header").forEach(el => el.click());

            const unitIds = {};
            document.querySelectorAll(".battle_chara_select .ant-collapse-content-box div").forEach((el, i) => {
              const keys = Object.keys(el);
              const internalInstance = keys.filter(key => key.includes("reactInternalInstance"));
              const unitId = el[internalInstance].return.memoizedProps.cid;

              unitIds[parseInt(unitId / 100)] = i;
            });

            return unitIds;
            """
        )

        self.logger.info("Ready.")

    def search(self, units: List[Unit]) -> AttackData:
        # clear
        self.driver.execute_script("document.querySelector('.battle_title_ctn button:nth-child(1)');")

        for unit in units:
            index = self.unit_ids.get(str(unit.unit_id))
            if isinstance(index, int):
                self.driver.execute_script(
                    f"document.querySelectorAll('.battle_chara_select .ant-collapse-content-box div')[{index}].click();"
                )
                self.logger.info(f"{unit} selected.")
            else:
                self.logger.warning(f"{unit} not found.")

        del self.driver.requests
        self.driver.execute_script("document.querySelector('.battle_search_button').click();")

        request = self.driver.wait_for_request("/x/v1/search")
        if request.response and request.response.status_code == 200:
            data: dict = json.loads(request.response.body.decode())
            result: List[dict] = data["data"]["result"]

            if len(result) > 0:
                best_result: dict = result[0]
                units = []
                good = best_result.get("up", 0)
                bad = best_result.get("down", 0)

                for i in best_result["atk"]:
                    units.append(deepcopy(self.um.units[int(i["id"] / 100)])._replace(rarity=i["star"]))

                self.logger.info(f"{', '.join([unit for unit in units])} {good}/{bad}")
                return AttackData(good=good, bad=bad, units=units)

        self.logger.info(f"Attack team not found :(")
        return None
