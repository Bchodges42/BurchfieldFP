# Who Shows Up on Halloween? Weather, Darkness and the Trick-or-Treat Rush

Tableau project for the Halloween assignment. It asks how the number of trick-or-treaters at one Cincinnati porch (ZIP 45207, 2008–2025) depends on the **weather**, the **time of night and darkness**, and the **day of the week**.

Interactive preview of the finished dashboard: https://claude.ai/artifact/FHeedV4cFXGQhvESgZ6VxR

## What's in this folder

| Path | What it is |
|---|---|
| `tableau/Halloween Weather and Trick-or-Treaters.twbx` | **The Tableau workbook** (data packaged inside): 9 sheets plus a 1920 × 1080 dashboard |
| `tableau/Halloween Weather and Trick-or-Treaters.twb` + `tableau/Halloween_Enriched.xlsx` | The same workbook unpackaged. Keep both files in the same folder. |
| `data/Halloween_Enriched.xlsx` | The enriched data source. Sheets: **Intervals** (108 rows, used by Tableau), **Year Summary** (18 rows), **Data Dictionary**, **Sources** |
| `data/raw/HalloweenTableau2025.xlsx` | The original course file, unchanged |
| `data/weather/*.json` | Raw hourly weather pulled from Open-Meteo, one file per Halloween |
| `preview/index.html` | Browser version of the dashboard (the link above) |
| `scripts/build_data.py`, `scripts/build_twb.py` | Rebuild the data and the workbook (`python3 scripts/build_data.py && python3 scripts/build_twb.py`) |

> **Before you submit:** replace `[Your Name] & [Partner Name]` in the dashboard footer (double-click the footer text box).

---

## The story (key findings)

All figures exclude 2020 unless noted. 2020 was the COVID candy-chute year (219 kids), which is an outlier unrelated to the weather. The dashboard lets the viewer put it back in.

1. **About 621 kids on an average Halloween**, ranging from 391 (2013) to 869 (2011).
2. **Rain and wind lower the count; cold doesn't.**
   * Nights with rain 6–8 pm averaged **518 kids, vs. 664 on dry nights (−22%)**.
   * Peak wind gust has the strongest link to the total (**r = −0.65**). Nights with gusts of 25 mph or more averaged 529 kids, vs. 649 on calmer nights.
   * Temperature has essentially **no relationship** with the count (r ≈ 0.0). The coldest nights still drew big crowds: 2017 felt like 36°F and drew 776 kids. "Chilly" nights (feels-like under 50°F) averaged 652, about the same as warm nights (641).
   * 2013 (rain plus 47 mph gusts) had the lowest count outside 2020 (391). 2019 was dry during trick-or-treat hours, but a storm dropped 0.8 in of rain earlier that day and left 42 mph gusts and a 24°F wind chill. It drew 523.
3. **The rush is the hour after sunset.** Sunset on Oct 31 is about 6:37 pm EDT. **53% of all kids arrive 6:30–7:30 pm**: 6:30–7:00 is twilight and 7:00–7:30 is full dark. Only 2% come before 6:00, and 5% straggle in after 8:00.
4. **Bad weather moves arrivals earlier.** The kid-weighted average arrival time is **7:02 pm**. On rainy nights it is about 5 minutes earlier (6:58 vs. 7:03). On the stormiest night (2013) it was 6:51, as families tried to beat the weather.
5. **Arrivals are drifting earlier over time**, by about 5 minutes per decade (7:08 pm in 2008, 7:00 pm in 2025). The busiest half-hour moved from 7:00–7:30 (2008–2012) to 6:30–7:00 (most years since 2015).
6. **Weekends don't help.** Friday and Saturday Halloweens averaged 595 kids, vs. 632 on school nights. With only 5 weekend years, day of week is not a driver here.

Planning advice for the homeowner: stock for about 650 kids. Expect ~150 fewer if rain or strong wind is forecast, have the porch ready by 6:15, and expect the peak right after sunset.

### Caveats (worth one sentence in the presentation)
* 17 usable years is a small sample. These are associations, not proof of cause.
* Weather is ERA5 reanalysis for a ~9 km grid cell around the house. It is accurate for regional conditions, not a backyard gauge.
* "Rain" means at least 0.01 in fell from 6 to 8 pm. Rain earlier in the day (e.g. 2019) does not count.

---

## How the data was prepared (and the pitfalls avoided)

1. **Interval meaning.** Each count is the number of kids who arrived in the window **ending** at the logged time. "6:00pm" means early arrivals before 6:00, "6:30pm" means 6:00–6:30, … and "8:15pm" means the 8:00–8:15 stragglers. Since the last window is only 15 minutes, a `Kids per 15 Min` rate is included so windows compare fairly.
2. **Time zone trap.** Oct 31 is always in **Eastern Daylight Time** (DST has ended on the first Sunday of November since 2007). The weather API labelled these hours as UTC−5. Every timestamp was converted through UTC so that "6 pm" in the weather really is 6 pm EDT. Without this fix, sunset shows up as 5:37 pm instead of the correct 6:37 pm.
3. **Granularity trap.** Weather exists per hour, counts per half-hour, and the story is per night. The workbook uses **one flat table at the interval level**. Night-level weather fields repeat on each of a year's 6 rows, so they must be aggregated with **AVG/ATTR, never SUM**. Year totals are `SUM([Count])`, and averages across years are `SUM([Count]) / COUNTD([Year])`. A `{FIXED [Year] : SUM([Count])}` LOD is included for tooltips.
4. **Interval weather.** Hourly temperature and wind were interpolated to each window's midpoint, and precipitation is the total for the clock hour containing the window.
5. **Darkness.** Sun altitude at each window midpoint uses the NOAA solar-position equations. **Twilight** is 0° to −6° (civil twilight) and **Dark** is below −6°.

### Sources (also on the dashboard footer and in the Sources sheet)
* Trick-or-treater counts: Jeffrey Shaffer, course file `HalloweenTableau2025.xlsx`.
* Weather: Open-Meteo Historical Weather API, https://open-meteo.com/en/docs/historical-weather-api, ERA5 reanalysis (Hersbach et al., 2020, ECMWF / Copernicus Climate Change Service, doi:10.24381/cds.adbb2d47). Location lat 39.135, lon −84.470.
* Sun position: NOAA Global Monitoring Laboratory, General Solar Position Calculations.

---

## The dashboard (what's on it)

Fixed size **1920 × 1080**.

| Zone | Sheet | Shows |
|---|---|---|
| Header | text | Title, subtitle, **How to use** instructions |
| KPI strip | `KPI Kids per Night`, `KPI Peak Hour`, `KPI Rain Effect`, `KPI Arrival Time` | 621 · 53% · −22% · 7:02 pm |
| Controls | 3 parameters | **2020 (COVID year)** include/exclude · **Color years by** (rain or dry / temperature / school vs weekend night) · **Weather measure** for the scatter x-axis |
| Row 1 | `Year by Year` | Bar per Halloween, colored by the chosen grouping, with labels and a weather tooltip |
| Row 1 | `Arrival Curve` | Average kids per window, colored Daylight / Twilight / Dark and labeled with share |
| Row 2 | `Rush Hour Heatmap` | Year × window highlight table |
| Row 2 | `Weather Explorer` | Scatter of the selected weather measure vs. year total, colored rain/dry |
| Row 2 | `Arrival Time Trend` | Average arrival minute per year, colored rain/dry |
| Footer | text | Sources, method notes, names |

**Interactivity:** the 3 parameter controls; a **dashboard highlight action on Year** (click a year anywhere to highlight it everywhere); custom tooltips on every chart.

---

## Opening the workbook

1. Double-click `tableau/Halloween Weather and Trick-or-Treaters.twbx` (Tableau Desktop or Tableau Public 2020.1 or later).
2. If Tableau asks where the data is, point it at `Halloween_Enriched.xlsx`.
3. Go to the **Halloween Dashboard** tab and check it against the preview link above.
4. Recommended polish (each takes seconds and was not set automatically):
   * **Weather Explorer** and **Arrival Time Trend**: Analytics pane → drag **Trend Line** → Linear.
   * **Year by Year**: Analytics pane → drag **Average Line** → Table.
   * **Weather Explorer**: Analytics pane → **Trend Line**, then hover the line to see R².

> I generated the `.twbx` file directly as Tableau XML, because Tableau can't run in the environment I worked in. I checked that it is well-formed and that every field reference resolves, but I could not open it in Tableau. If it shows an error or a sheet looks wrong, rebuild that piece with the recipe below. The whole workbook takes about 45 minutes to rebuild from scratch.

---

## Rebuild recipe (fallback, step by step)

### 1. Connect
**Connect → Microsoft Excel →** `data/Halloween_Enriched.xlsx` → drag the **Intervals** sheet to the canvas. In the data pane, drag **Year** and **Interval Order** up into Dimensions and make them **Discrete**.
Right-click **Interval Order → Aliases**: 1 = Before 6:00, 2 = 6:00–6:30, 3 = 6:30–7:00, 4 = 7:00–7:30, 5 = 7:30–8:00, 6 = 8:00–8:15.

### 2. Parameters (Create → Parameter, String, List)
| Name | Values | Default |
|---|---|---|
| `2020 (COVID year)` | Exclude 2020, Include 2020 | Exclude 2020 |
| `Color years by` | Rain or dry, Temperature, School vs weekend night | Rain or dry |
| `Weather measure (x-axis)` | Wind gust (mph), Wind speed (mph), Rain 6-8 pm (in), Feels-like temp (F), Cloud cover (%) | Wind gust (mph) |

Right-click each one → **Show Parameter**.

### 3. Calculated fields
```text
Keep Year?          [2020 (COVID year)] = "Include 2020" OR [Year] <> 2020
Kids per Night      SUM([Count]) / COUNTD([Year])
Share of All Kids   SUM([Count]) / MIN({ FIXED [Keep Year?] : SUM([Count]) })
Peak Hour Share     SUM(IF [Interval Order] = 3 OR [Interval Order] = 4 THEN [Count] END) / SUM([Count])
Rain vs Dry         (SUM(IF [Rain or Dry]="Rain" THEN [Count] END) / COUNTD(IF [Rain or Dry]="Rain" THEN [Year] END))
                    / (SUM(IF [Rain or Dry]="Dry" THEN [Count] END) / COUNTD(IF [Rain or Dry]="Dry" THEN [Year] END)) - 1
Avg Arrival (min after 6 pm)   SUM([Count] * [Arrival Minute]) / SUM([Count])
Avg Arrival Time    STR(6 + INT(INT(ROUND([Avg Arrival (min after 6 pm)],0)) / 60)) + ":" +
                    RIGHT("0" + STR(INT(ROUND([Avg Arrival (min after 6 pm)],0)) % 60), 2) + " pm"
Color Group         CASE [Color years by] WHEN "Rain or dry" THEN [Rain or Dry]
                    WHEN "Temperature" THEN [Temperature Band] ELSE [Night Type] END
Selected Weather    CASE [Weather measure (x-axis)]
                    WHEN "Wind gust (mph)"    THEN AVG([Night Max Gust Mph])
                    WHEN "Wind speed (mph)"   THEN AVG([Night Max Wind Mph])
                    WHEN "Rain 6-8 pm (in)"   THEN AVG([Night Precip In])
                    WHEN "Feels-like temp (F)" THEN AVG([Night Feels Like F])
                    ELSE AVG([Night Cloud Cover Pct]) END
Year Total (LOD)    { FIXED [Year] : SUM([Count]) }
```
Put **Keep Year? = True** on the Filters shelf of every sheet. Then right-click the filter → **Apply to Worksheets → All Using This Data Source**.

### 4. Sheets
| Sheet | Columns | Rows | Marks |
|---|---|---|---|
| KPI Kids per Night | – | – | Text: `Kids per Night` (format: number, 0 decimals) |
| KPI Peak Hour | – | – | Text: `Peak Hour Share` (percent, 0 dp) |
| KPI Rain Effect | – | – | Text: `Rain vs Dry` (percent, 0 dp) |
| KPI Arrival Time | – | – | Text: `Avg Arrival Time` |
| Year by Year | Year | SUM(Count) | Bar · Color: `Color Group` · Label: SUM(Count) · Tooltip: ATTR(Day of Week), ATTR(Conditions), AVG(Night Feels Like F), AVG(Night Precip In), AVG(Night Max Gust Mph), ATTR(Note) · Analytics: Average line |
| Arrival Curve | Interval Order | Kids per Night | Bar · Color: Light · Label: Share of All Kids |
| Rush Hour Heatmap | Interval Order | Year | Square · Color: SUM(Count) (Orange sequential) · Label: SUM(Count) |
| Weather Explorer | Selected Weather | SUM(Count) | Circle · Detail: Year · Label: Year · Color: Rain or Dry · Analytics: Trend line |
| Arrival Time Trend | Year | Avg Arrival (min after 6 pm) | Circle · Color: Rain or Dry · Analytics: Trend line |

KPI text: make the number about 30 pt bold, with a 10 pt caption underneath, e.g. "trick-or-treaters on an average Halloween".
Colors: Rain `#2F7FC1`, Dry `#C27A28`; Daylight `#BBA8E0`, Twilight `#8566BE`, Dark `#4A2F7A`; Chilly `#3F86C8`, Mild `#B98512`, Warm `#C8424F`; School night `#5B3F8C`, Weekend night `#E0570B`. These pass color-blind separation checks.

### 5. Dashboard
New Dashboard → **Size: Fixed, 1920 × 1080**. Lay it out as in the table above: dark header text box (`#2B1D3F`) with title and how-to, a KPI row with the three parameter controls on the right, two charts in row 1, three in row 2, and a sources footer.
**Dashboard → Actions → Add Action → Highlight**: source = all sheets, run on **Select**, target = this dashboard, **Selected fields: Year**.

---

## Presentation talking points (about 3 minutes)
1. **Question:** how much do weather and time of night drive how many kids come to Jeffrey's door?
2. **Data:** 18 Halloweens of half-hour counts, joined to hourly ERA5 weather and computed sun position. Call out the time-zone and granularity traps.
3. **Finding 1:** rain and wind cut the crowd by about a fifth, but cold doesn't. Show the weather explorer and switch the x-axis from *Feels-like temp* (flat) to *Wind gust* (r = −0.65).
4. **Finding 2:** half the kids arrive in the hour after sunset. Show the arrival curve, then the heatmap.
5. **Finding 3:** storms push arrivals earlier, and kids are arriving earlier every year. Show the arrival-time trend and click 2013.
6. **So what:** buy candy for about 650. Cut back about 150 if rain or wind is forecast. Be on the porch by 6:15.

## Email to the instructor (template)
> Subject: Halloween Assignment – Team
>
> Hi Professor,
> Our team for the Halloween assignment is [Your Name] and [Partner Name]. Our story looks at how weather (rain, wind and temperature) and darkness after sunset affect the number and timing of trick-or-treaters. We appended hourly historical weather from the Open-Meteo / ERA5 archive.
>
> Thanks,
> [Your Name]
