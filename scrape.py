#!/usr/bin/env python3
import requests
import calendar
import pandas as pd
from bs4 import BeautifulSoup

pd.set_option("mode.chained_assignment", None)

URL = "https://www.waterlevels.gc.ca/en/water-levels-forecast"

r = requests.get(URL)

# Get name of current month from response headers
current_month = pd.to_datetime(r.headers["Date"]).month  # type: int

# Subsequent month's index (1-12) value
next_month_index = (current_month + 1) % 13 + ((current_month + 1) // 13)
next_month = calendar.month_name[next_month_index]

# ensure that status code is ok
if r.status_code != 200:
    raise requests.ConnectionError("received {} status code".format(r.status_code))

soup = BeautifulSoup(r.text, features="lxml")

sibbling_el = soup.find(id="lake-ontario")

table = next(sibbling_el.parents)

# read html into DataFrame
df = pd.read_html(str(table))[0]

# convert month data into datetime objects
df.Month = pd.to_datetime(df.Month)


rename_cols = {"5%": "0.05", "Most probable": "0.5", "95%": "0.95"}
new_col_names = list(rename_cols.values())

df = df.rename(columns=rename_cols)

df.loc[:, new_col_names] = (
    df.loc[:, new_col_names]
    .apply(lambda s: s.str.replace("\(.*$", "", regex=True))
    .apply(pd.to_numeric, downcast="float")
)

next_month_df = df.loc[df.Month.dt.month_name() == next_month, :]

next_month_df.loc[:, "Month"] = next_month_df.Month.dt.month_name().str.upper()

next_month_df.columns = next_month_df.columns.str.upper()

output_json = next_month_df.squeeze().to_json(double_precision=2)


with open("lake_ontario_water_level_forecast.json", "w") as f:
    f.write(output_json)
