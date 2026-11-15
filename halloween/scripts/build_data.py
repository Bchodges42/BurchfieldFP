"""Build the enriched Halloween data source.

Inputs
  data/raw/HalloweenTableau2025.xlsx   original trick-or-treater counts (2008-2025)
  data/weather/<year>.json             Open-Meteo Historical Weather API (ERA5) responses

Outputs
  data/Halloween_Enriched.xlsx         Tableau data source (Intervals, Year Summary, Data Dictionary, Sources)
  data/intervals.csv, data/years.csv   same tables as CSV
  data/dashboard.json                  data for the HTML preview

Run:  python3 scripts/build_data.py   (from the halloween/ folder)
"""
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import openpyxl
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "HalloweenTableau2025.xlsx"
WX = ROOT / "data" / "weather"
OUT = ROOT / "data"

ET = ZoneInfo("America/New_York")
LAT, LON = 39.135, -84.470  # ZIP 45207 (East Walnut Hills / Evanston), Cincinnati OH

# Each count is the number of kids who arrived in the interval ENDING at the logged time.
INTERVALS = {
    "6:00pm": (1, "Before 6:00", None, "5:45"),   # early arrivals, open-ended
    "6:30pm": (2, "6:00–6:30", 30, "6:15"),
    "7:00pm": (3, "6:30–7:00", 30, "6:45"),
    "7:30pm": (4, "7:00–7:30", 30, "7:15"),
    "8:00pm": (5, "7:30–8:00", 30, "7:45"),
    "8:15pm": (6, "8:00–8:15", 15, "8:07"),
}

WMO = {
    0: "Clear", 1: "Mostly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Fog", 51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain", 80: "Rain showers", 81: "Rain showers",
    82: "Heavy showers", 95: "Thunderstorm",
}

NOTES = {
    2013: "Rain plus strong wind (gusts to 47 mph) — lowest count outside 2020",
    2019: "Storm front: 0.8 in of rain earlier in the day, then 42 mph gusts and a 24°F wind chill",
    2020: "COVID-19: candy delivered by two long chutes; some families stayed home",
    2025: "Record half-hour: 260 kids between 6:30 and 7:00 pm",
}


# ---------------------------------------------------------------- sun position
def sun_altitude(dt_utc: datetime) -> float:
    """Solar elevation angle (degrees) — NOAA general solar position algorithm."""
    doy = dt_utc.timetuple().tm_yday
    hour = dt_utc.hour + dt_utc.minute / 60
    g = 2 * math.pi / 365 * (doy - 1 + (hour - 12) / 24)
    eqtime = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g)
                       - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    decl = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g)
            - 0.006758 * math.cos(2 * g) + 0.000907 * math.sin(2 * g)
            - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    tst = hour * 60 + eqtime + 4 * LON          # true solar time, minutes
    ha = math.radians(tst / 4 - 180)
    lat = math.radians(LAT)
    cos_zen = math.sin(lat) * math.sin(decl) + math.cos(lat) * math.cos(decl) * math.cos(ha)
    return 90 - math.degrees(math.acos(max(-1, min(1, cos_zen))))


def light_phase(alt: float) -> str:
    if alt > 0:
        return "Daylight"
    if alt > -6:
        return "Twilight"
    return "Dark"


# ---------------------------------------------------------------- weather
def load_weather(year: int) -> pd.DataFrame | None:
    f = WX / f"{year}.json"
    if not f.exists():
        return None
    d = json.loads(f.read_text())
    if d.get("error"):
        return None
    off = timedelta(seconds=d["utc_offset_seconds"])
    h = pd.DataFrame(d["hourly"])
    # The API's local stamps use a fixed offset; rebuild true Eastern time via UTC.
    h["utc"] = [datetime.fromisoformat(t).replace(tzinfo=timezone.utc) - off for t in h["time"]]
    h["et"] = [u.astimezone(ET).replace(tzinfo=None) for u in h["utc"]]
    sunset_local = datetime.fromisoformat(d["daily"]["sunset"][0])
    sunset_et = (sunset_local.replace(tzinfo=timezone.utc) - off).astimezone(ET).replace(tzinfo=None)
    h.attrs["sunset"] = sunset_et
    h.attrs["daily"] = d["daily"]
    return h.set_index("et")


def interp(h: pd.DataFrame, col: str, t: datetime) -> float:
    s = h[col]
    lo = t.replace(minute=0, second=0)
    hi = lo + timedelta(hours=1)
    w = (t - lo).total_seconds() / 3600
    return float(s[lo] * (1 - w) + s[hi] * w)


def hour_precip(h: pd.DataFrame, t: datetime) -> float:
    """Precipitation (in) for the clock hour containing t (ERA5 precip is the sum over the preceding hour)."""
    end = t.replace(minute=0, second=0) + timedelta(hours=1)
    return float(h.loc[end, "precipitation"])


def temp_band(t):
    if t is None or pd.isna(t):
        return None
    if t < 50:
        return "Chilly (< 50°F)"
    if t < 60:
        return "Mild (50–59°F)"
    return "Warm (60°F +)"


def main():
    raw = pd.read_excel(RAW, sheet_name="Data")
    raw["Year"] = raw["Date"].dt.year
    years = sorted(raw["Year"].unique())
    wx = {y: load_weather(y) for y in years}
    missing = [y for y, h in wx.items() if h is None]
    if missing:
        print("WARNING: missing weather for", missing)

    # ---------------- year-level weather (official window 6–8 pm EDT)
    yrows = []
    for y in years:
        cnt = raw[raw.Year == y]
        total = int(cnt["Count"].sum())
        dow = cnt["Day of Week"].iloc[0]
        row = {
            "Year": y, "Date": datetime(y, 10, 31), "Day of Week": dow,
            "Night Type": "Weekend night (Fri/Sat)" if dow in ("Friday", "Saturday") else "School night (Sun–Thu)",
            "Year Total": total,
            "Peak Interval": INTERVALS[cnt.loc[cnt["Count"].idxmax(), "Time"]][1],
            "Peak Interval Count": int(cnt["Count"].max()),
            "COVID Year": "Yes" if y == 2020 else "No",
            "Note": NOTES.get(y, ""),
        }
        h = wx[y]
        if h is not None:
            win = h.loc[datetime(y, 10, 31, 18): datetime(y, 10, 31, 20)]          # 6,7,8 pm readings
            pwin = h.loc[datetime(y, 10, 31, 19): datetime(y, 10, 31, 20)]         # precip 6–7 & 7–8 pm
            codes = [int(c) for c in win["weather_code"]]
            worst = max(codes)
            precip = round(float(pwin["precipitation"].sum()), 3)
            row.update({
                "Sunset EDT": h.attrs["sunset"].strftime("%-I:%M pm"),
                "Night Temp F": round(float(win["temperature_2m"].mean()), 1),
                "Night Feels Like F": round(float(win["apparent_temperature"].mean()), 1),
                "Temp at 6pm F": round(float(h.loc[datetime(y, 10, 31, 18), "temperature_2m"]), 1),
                "Night Precip In": precip,
                "Rain or Dry": "Rain" if precip >= 0.01 else "Dry",
                "Night Max Wind Mph": round(float(win["wind_speed_10m"].max()), 1),
                "Night Max Gust Mph": round(float(win["wind_gusts_10m"].max()), 1),
                "Night Cloud Cover Pct": round(float(win["cloud_cover"].mean())),
                "Night Humidity Pct": round(float(win["relative_humidity_2m"].mean())),
                "Conditions": WMO.get(worst, f"WMO {worst}"),
                "Daily High F": h.attrs["daily"]["temperature_2m_max"][0],
                "Daily Low F": h.attrs["daily"]["temperature_2m_min"][0],
                "Daily Precip In": h.attrs["daily"]["precipitation_sum"][0],
            })
            row["Temperature Band"] = temp_band(row["Night Feels Like F"])
        yrows.append(row)
    ydf = pd.DataFrame(yrows)
    avg_all = ydf["Year Total"].mean()
    ydf["Vs Avg"] = (ydf["Year Total"] - avg_all).round(0).astype(int)
    ydf["Pct Vs Avg"] = (ydf["Year Total"] / avg_all - 1).round(3)
    ydf["YoY Change"] = ydf["Year Total"].diff()

    # ---------------- interval-level rows
    irows = []
    for _, r in raw.iterrows():
        y = r.Year
        order, label, minutes, mid = INTERVALS[r.Time]
        hh, mm = map(int, mid.split(":"))
        mid_dt = datetime(y, 10, 31, hh + 12, mm)
        mid_utc = mid_dt.replace(tzinfo=ET).astimezone(timezone.utc)
        alt = sun_altitude(mid_utc)
        yrow = ydf[ydf.Year == y].iloc[0].to_dict()
        row = {
            "Year": y, "Date": r.Date, "Date and Time": r["Date and Time"], "Day of Week": r["Day of Week"],
            "Time Logged": r.Time, "Interval": label, "Interval Order": order,
            "Interval Minutes": minutes, "Count": int(r.Count),
            "Kids per 15 Min": round(r.Count / minutes * 15, 1) if minutes else None,
            "Share of Night": round(r.Count / yrow["Year Total"], 4),
            "Arrival Minute": (mid_dt - datetime(y, 10, 31, 18)).total_seconds() / 60,
            "Sun Altitude Deg": round(alt, 1), "Light": light_phase(alt),
        }
        h = wx[y]
        if h is not None:
            row["Minutes After Sunset"] = round((mid_dt - h.attrs["sunset"]).total_seconds() / 60)
            row["Interval Temp F"] = round(interp(h, "temperature_2m", mid_dt), 1)
            row["Interval Feels Like F"] = round(interp(h, "apparent_temperature", mid_dt), 1)
            row["Interval Precip In"] = round(hour_precip(h, mid_dt), 3)
            row["Interval Wind Mph"] = round(interp(h, "wind_speed_10m", mid_dt), 1)
        # repeat the year-level fields so a single flat table can drive every sheet
        for k in ["Night Type", "Year Total", "COVID Year", "Night Temp F",
                  "Night Feels Like F", "Night Precip In", "Rain or Dry", "Night Max Wind Mph",
                  "Night Max Gust Mph", "Night Cloud Cover Pct", "Conditions", "Temperature Band",
                  "Sunset EDT", "Note"]:
            row[k] = yrow.get(k)
        irows.append(row)
    idf = pd.DataFrame(irows)

    idf.to_csv(OUT / "intervals.csv", index=False)
    ydf.to_csv(OUT / "years.csv", index=False)
    write_xlsx(idf, ydf)
    (OUT / "dashboard.json").write_text(json.dumps({
        "years": json.loads(ydf.to_json(orient="records", date_format="iso")),
        "intervals": json.loads(idf.to_json(orient="records", date_format="iso")),
    }, indent=1, ensure_ascii=False))
    tpl = (ROOT / "preview" / "template.html").read_text()
    data = json.dumps({"years": json.loads(ydf.to_json(orient="records")),
                       "intervals": json.loads(idf.to_json(orient="records"))}, ensure_ascii=False)
    (ROOT / "preview" / "index.html").write_text(tpl.replace("/*DATA*/null", data))
    print(ydf[["Year", "Year Total", "Night Feels Like F", "Night Precip In", "Night Max Gust Mph", "Conditions"]].to_string())


DICTIONARY = [
    ("Year", "Both", "Halloween year (always Oct 31)."),
    ("Interval", "Intervals", "Arrival window the count covers. A count logged at 6:30 pm = kids who arrived 6:00–6:30 pm. 'Before 6:00' = early arrivals; 8:00–8:15 = stragglers."),
    ("Interval Order", "Intervals", "1–6, use to sort Interval chronologically."),
    ("Interval Minutes", "Intervals", "Length of the window (30, or 15 for 8:00–8:15). Blank for the open-ended 'Before 6:00' window."),
    ("Count", "Intervals", "Trick-or-treaters counted in the interval (original data)."),
    ("Kids per 15 Min", "Intervals", "Count normalised to a 15-minute rate so the 15-minute straggler window compares fairly."),
    ("Share of Night", "Intervals", "Interval count ÷ that year's total."),
    ("Arrival Minute", "Intervals", "Interval midpoint in minutes after 6:00 pm (−15 for early arrivals). SUM([Count]*[Arrival Minute])/SUM([Count]) = average arrival time."),
    ("Sun Altitude Deg", "Intervals", "Solar elevation at the interval midpoint (NOAA solar position algorithm)."),
    ("Light", "Intervals", "Daylight (sun above horizon), Twilight (0 to −6°, civil twilight) or Dark (below −6°)."),
    ("Minutes After Sunset", "Intervals", "Interval midpoint minus that day's sunset."),
    ("Interval Temp F / Feels Like F / Wind Mph", "Intervals", "Hourly ERA5 values linearly interpolated to the interval midpoint."),
    ("Interval Precip In", "Intervals", "Precipitation that fell during the clock hour containing the interval."),
    ("Year Total", "Both", "Year total. In the Intervals sheet it repeats on all 6 rows — use AVG/MIN/ATTR (never SUM) or SUM(Count)."),
    ("Night Temp F / Night Feels Like F", "Both", "Mean of the 6, 7 and 8 pm EDT hourly readings. Repeats per row in Intervals — aggregate with AVG."),
    ("Night Precip In", "Both", "Total precipitation 6–8 pm EDT."),
    ("Rain or Dry", "Both", "'Rain' if ≥ 0.01 in fell 6–8 pm, else 'Dry'."),
    ("Night Max Wind Mph / Night Max Gust Mph", "Both", "Highest hourly 10 m wind speed / gust 6–8 pm."),
    ("Conditions", "Both", "Most significant WMO weather code observed 6–8 pm."),
    ("Temperature Band", "Both", "Feels-like bucket: Chilly < 50°F, Mild 50–59°F, Warm 60°F +."),
    ("Night Type", "Both", "Weekend night (Fri/Sat) vs School night (Sun–Thu)."),
    ("COVID Year", "Both", "'Yes' for 2020 (candy chutes, pandemic). Use to exclude the outlier from trend/correlation views."),
    ("Vs Avg, Pct Vs Avg, YoY Change", "Year Summary", "Year total compared with the 2008–2025 average and with the prior year."),
]

SOURCES = [
    ("Trick-or-treater counts", "Jeffrey Shaffer, Cincinnati OH 45207 — HalloweenTableau2025.xlsx (course file)."),
    ("Hourly weather", "Open-Meteo Historical Weather API (ERA5 reanalysis, ECMWF / Copernicus Climate Change Service), "
                       "lat 39.135, lon −84.470, retrieved Nov 2026. https://open-meteo.com/en/docs/historical-weather-api  "
                       "Hersbach, H. et al. (2020) ERA5 hourly data, doi:10.24381/cds.adbb2d47"),
    ("Sunset", "Open-Meteo daily 'sunset' field, converted to EDT."),
    ("Sun altitude / twilight", "Computed with the NOAA General Solar Position equations (NOAA Global Monitoring Laboratory)."),
    ("Time-zone note", "Oct 31 falls in Eastern DAYLIGHT time every year since 2007 (DST ends first Sunday of Nov). "
                       "All weather was converted through UTC to EDT so 6–8 pm lines up with the counts."),
]


def write_xlsx(idf, ydf):
    path = OUT / "Halloween_Enriched.xlsx"
    with pd.ExcelWriter(path, engine="openpyxl", datetime_format="yyyy-mm-dd hh:mm", date_format="yyyy-mm-dd") as xw:
        idf.to_excel(xw, sheet_name="Intervals", index=False)
        ydf.to_excel(xw, sheet_name="Year Summary", index=False)
        pd.DataFrame(DICTIONARY, columns=["Field", "Sheet", "Definition"]).to_excel(xw, sheet_name="Data Dictionary", index=False)
        pd.DataFrame(SOURCES, columns=["Item", "Source / Method"]).to_excel(xw, sheet_name="Sources", index=False)
    wb = openpyxl.load_workbook(path)
    for ws in wb:
        ws.freeze_panes = "A2"
        for c in ws[1]:
            c.font = openpyxl.styles.Font(bold=True, color="FFFFFF")
            c.fill = openpyxl.styles.PatternFill("solid", fgColor="E8590C")
        for col in ws.columns:
            width = max(len(str(c.value or "")) for c in col[:40])
            ws.column_dimensions[col[0].column_letter].width = min(max(10, width + 2), 90)
    for ws in (wb["Data Dictionary"], wb["Sources"]):
        for row in ws.iter_rows(min_row=2):
            for c in row:
                c.alignment = openpyxl.styles.Alignment(wrap_text=True, vertical="top")
    wb.save(path)


if __name__ == "__main__":
    main()
