#!/usr/bin/env python3
import requests
import calendar
import pandas as pd

pd.set_option("mode.chained_assignment", None)

URL = "https://www.waterlevels.gc.ca/C&A/glfcst-eng.html"

r = requests.get(URL)

# Get name of current month from response headers
current_month = pd.to_datetime(r.headers["Date"]).month  # type: int

# Subsequent month's index (1-12) value
next_month_index = (current_month + 1) % 13 + ((current_month + 1) // 13)
next_month = calendar.month_name[next_month_index]

# read html into DataFrame
df = pd.read_html(r.text)[0]

# Find start and end points of intest. The first lake ontario row and CHART DATUM row
# that marks the end of the lake ontario section
lake_ontario_row_idx = df[df[0] == "LAKE ONTARIO"].index[0]
last_row_of_interst = (
    df.iloc[lake_ontario_row_idx:, :].loc[df[0].str.contains("CHART"), :].index[0]
)

subset_df = df.loc[lake_ontario_row_idx:last_row_of_interst, :]

# find next month's row
next_month_row = subset_df.loc[subset_df[0].str.contains(next_month, case=False)]

# in columns containing lake levels (as strings), find where the space is (usually
# formatted "74.74 (0.54)") and slice up until the space -- effectively removing "
# (0.54)" in the example. Next, cast from string to float and downcast from float64 to
# float32
next_month_row[[1, 2, 3]] = (
    next_month_row.loc[:, [1, 2, 3]]
    .apply(lambda d: d.str[: int(d.str.find(" "))])
    .apply(pd.to_numeric, downcast="float")
)

output = next_month_row[[0, 1, 2, 3]]

# rename relevant columns to their percentile values. See https://www.waterlevels.gc.ca/C&A/glfcst-eng.html for details
output.rename(columns={0: "MONTH", 1: "0.05", 2: "0.5", 3: "0.95"}, inplace=True)

# implicit cast from dataframe to series then
output_json = output.squeeze().to_json(double_precision=2)

with open("lake_ontario_water_level_forecast.json", "w") as f:
    f.write(output_json)
