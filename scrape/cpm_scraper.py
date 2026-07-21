import io
import urllib.request

import pandas as pd

CPM_LIST_URL = "https://pokemongohub.net/post/article/pokemon-go-cpm-list/"


def fetch_html(url=CPM_LIST_URL):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; poketool-scraper/1.0)"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_cpm_table(html):
    tables = pd.read_html(io.StringIO(html))
    cpm_table = next(t for t in tables if "CPM" in t.columns)
    df = cpm_table[["Level", "CPM"]].dropna()
    df = df.rename(columns={"Level": "level", "CPM": "value"})
    return df.reset_index(drop=True)


if __name__ == "__main__":
    html = fetch_html()
    df = parse_cpm_table(html)
    print(df)
