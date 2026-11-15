I'm continuing a Tableau class project (the "Halloween Assignment") that was started in a cloud Claude Code session. I have Tableau Desktop/Public installed on this machine. Please read this whole brief, then `halloween/README.md`, before doing anything.

## Get the work
Repo: `bchodges42/BurchfieldFP`, branch `claude/youthful-edison-jjx3t6`. Everything lives in `halloween/`.
```
git fetch origin claude/youthful-edison-jjx3t6
git checkout claude/youthful-edison-jjx3t6
```

## The assignment (what's actually graded)
- Data: 18 Halloweens (2008–2025) of trick-or-treater counts at one house in Cincinnati, OH 45207 (East Walnut Hills / Evanston). Counts are logged at 6:00, 6:30, 7:00, 7:30, 8:00 and 8:15 pm.
- Requirements: email the professor with team names; pick a story; **append external data** (watch for join pitfalls); **at least 4 visualizations**; **a dashboard viewable at 1920×1080**; **interactivity**; upload to Teams.
- Rubric (weight): completed requirements (5), data appropriate/sufficient (2), headers/directions/tooltips/citations (1), the viz supports the analysis (1), design/craft/spelling (1). It mentions "presentations", so I may need to present it.
- The main deliverable is the Tableau workbook (.twbx). A Word write-up with **real Tableau screenshots** is an optional extra, not a replacement.

## Our story
How the number (and timing) of trick-or-treaters depends on **weather** (rain, wind, temperature), **time of night / darkness after sunset**, and **day of week**.

## What exists (all in `halloween/`)
| Path | Status |
|---|---|
| `data/Halloween_Enriched.xlsx` | **Done and verified.** Sheets: Intervals (108 rows; Tableau uses this one), Year Summary, Data Dictionary, Sources |
| `data/weather/2008.json … 2025.json` | Raw Open-Meteo responses (all 18 years) |
| `scripts/build_data.py` | Rebuilds the Excel/CSVs and the HTML preview from the raw data |
| `scripts/build_twb.py` | Generates the Tableau workbook XML from a Python spec |
| `tableau/Halloween Weather and Trick-or-Treaters.twbx` (+ loose `.twb` and xlsx) | **Not tested.** Hand-generated Tableau XML (version 18.1 / 2020.1 format). It is well-formed and every field reference resolves, but it has **never been opened in Tableau** |
| `preview/index.html` | HTML/SVG mock of the intended dashboard. **Not Tableau output.** Use it as the visual target only. Also published at https://claude.ai/artifact/FHeedV4cFXGQhvESgZ6VxR |
| `README.md` | Findings, method, full **rebuild recipe** (every calc field, sheet and dashboard setting), talking points, instructor email draft |

## Key decisions already made (keep these unless there's a good reason)
1. **Interval meaning:** each count covers the window *ending* at the logged time. 6:00 pm = early arrivals before 6:00; 8:15 pm = the 8:00–8:15 stragglers (a 15-min window, so `Kids per 15 Min` normalizes it).
2. **Weather source:** Open-Meteo Historical Weather API (ERA5 reanalysis), lat 39.135, lon −84.470. Hourly temp, feels-like, precip, wind, gusts, cloud, humidity, WMO code, plus daily sunset.
3. **Time-zone fix:** Oct 31 is always EDT (DST ends the first Sunday in November since 2007), but the API stamped these hours UTC−5. Everything was converted through UTC to true EDT. Without the fix, sunset reads 5:37 pm instead of 6:37 pm.
4. **Night-level weather** = mean of the 6, 7 and 8 pm readings. "Rain" = ≥ 0.01 in fell 6–8 pm. Temperature bands use feels-like: Chilly < 50, Mild 50–59, Warm 60+.
5. **Interval-level weather:** temp and wind are interpolated to the window midpoint; precip is the clock hour containing the window.
6. **Darkness:** sun altitude from the NOAA solar equations. Daylight > 0°, Twilight 0 to −6°, Dark < −6°.
7. **Granularity / join pitfall:** one flat interval-level table. Night-level fields repeat on all 6 rows of a year, so use **AVG/ATTR, never SUM**. Averages across years use `SUM([Count]) / COUNTD([Year])`. A `{FIXED [Year]: SUM([Count])}` LOD is included.
8. **2020 (COVID candy chutes, 219 kids) is excluded by default** through a parameter + `Keep Year?` calc filter on every sheet, so viewers can add it back.
9. **Field names** are kept free of symbols (e.g. `Night Feels Like F`, `Night Max Gust Mph`) so Tableau references stay simple.
10. **Colors** passed a color-blind palette validator. Rain #2F7FC1, Dry #C27A28. Daylight #BBA8E0, Twilight #8566BE, Dark #4A2F7A. Chilly #3F86C8, Mild #B98512, Warm #C8424F. School night #5B3F8C, Weekend #E0570B. Heatmap: orange sequential.

## Findings (2020 excluded; verified in Python)
- About **621 kids per night** on average (range 391 in 2013 to 869 in 2011).
- **Rain 6–8 pm: 518 vs 664 on dry nights (−22%).** Peak wind gust has the strongest relationship, **r = −0.65** (gusts ≥ 25 mph: 529 vs 649). **Temperature ≈ no relationship** (r ≈ 0; 2017 felt like 36°F and still drew 776).
- 2013: rain + 47 mph gusts → 391 kids. 2019: dry 6–8 pm, but 0.8 in of rain earlier in the day, 42 mph gusts and a 24°F wind chill → 523.
- **53% of kids arrive 6:30–7:30 pm**, the hour after sunset (sunset ≈ 6:37 pm EDT).
- Kid-weighted average arrival **7:02 pm**. Rain nights run ~5 min earlier (6:58 vs 7:03); 2013 was the earliest (6:51). Arrivals are drifting about 5 min earlier per decade.
- Weekend nights (Fri/Sat) are not busier: 595 vs 632 on school nights (n = 5 vs 12).

## Dashboard design (target; see `preview/index.html`)
Fixed 1920×1080.
- **Header band** (#2B1D3F): title "WHO SHOWS UP ON HALLOWEEN?", subtitle, and HOW TO USE instructions.
- **KPI strip:** 4 text sheets (621 · 53% · −22% · 7:02 pm) plus 3 parameter controls: *2020 (COVID year)*, *Color years by*, *Weather measure (x-axis)*.
- **Row 1:** Year by Year bars (colored by the `Color Group` calc, with an average line); Arrival Curve (avg kids per window, colored by Light, labeled with share).
- **Row 2:** Rush Hour Heatmap (Year × window); Weather Explorer scatter (`Selected Weather` calc vs total, colored rain/dry, trend line); Arrival Time Trend (avg arrival minute by year, colored rain/dry, trend line).
- **Footer:** sources/citations and "Created by: [names]".
- **Interactivity:** the 3 parameters, a dashboard **highlight action on Year**, and custom tooltips.

## What I need from you now
1. Help me open `tableau/Halloween Weather and Trick-or-Treaters.twbx` in Tableau.
   - If Tableau shows an error, I'll paste it. Fix `scripts/build_twb.py` (not the .twb by hand), regenerate with `python3 scripts/build_twb.py` from `halloween/`, and repeat.
   - If a sheet opens but looks wrong, compare it to the preview and the README recipe, then fix it.
   - If the file proves unfixable, walk me through the README's rebuild recipe in Tableau, step by step.
2. Make sure every rubric item is covered: headers, how-to directions, tooltips, citations, consistent fonts, spelling, the 1920×1080 fixed size, and working interactivity. Add the trend lines and average line from the Analytics pane.
3. Optional: once the real Tableau dashboard works and I've taken screenshots, build a well-formatted Word write-up (1–2 pages: question, data and method including the time-zone and granularity pitfalls, findings, recommendations, sources) using **only real Tableau screenshots**.
4. Help me prep a ~3-minute presentation (talking points are in the README) and send the team-names email (draft is in the README).
5. Commit fixes to the same branch.

Notes: my partner's name is still a placeholder ("[Partner Name]") in the dashboard footer and the email. Don't invent statistics. If you recompute anything, use `data/intervals.csv` / `data/years.csv`.
