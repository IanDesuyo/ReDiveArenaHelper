import requests
from requests.sessions import session


class Api:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "authority": "nomae.net",
                "x-from": "https://nomae.net/arenadb/",
            }
        )
        self.session.get("https://nomae.net/arenadb/")

    def search(self, units: list):
        r = self.session.post(
            "https://nomae.net/princess_connect/public/_arenadb/receive.php",
            files=[
                *[("def[]", (None, i)) for i in units],
                ("type", (None, "search")),
                ("userid", (None, 0)),
                ("public", (None, 1)),
                ("page", (None, 0)),
                ("sort", (None, 0)),
            ],
        )
        res = r.json()
        res.sort(key=lambda x: x["good"] - x["bad"])

        if len(res) == 0:
            return

        best_ans = res[-1]

        best_ans["atk"] = list(filter(None, [i.split(",")[0] for i in best_ans["atk"].split("/")]))
        best_ans["def"] = list(filter(None, [i.split(",")[0] for i in best_ans["def"].split("/")]))
        return best_ans
