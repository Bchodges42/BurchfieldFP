# Three-minute presentation — individual project

Use the actual Tableau dashboard. Start with Exclude 2020, Rain or dry, and Wind gust (mph). Clear any selected marks before presenting.

**0:00–0:25 — Question and setting**

“My question is how weather and time of night relate to trick-or-treater turnout at one house in Cincinnati. I used 18 Halloweens, from 2008 through 2025. I exclude the COVID candy-chute year, 2020, by default, so the main comparisons use 17 nights. The control lets us include it again.”

**0:25–0:55 — Data and two pitfalls**

“I appended Open-Meteo’s hourly ERA5 historical weather and calculated sun position. Each count belongs to the window ending at its logged time, and the last window is only 15 minutes. I corrected the weather timestamps through UTC to Eastern Daylight Time; otherwise sunset would be an hour early. I also kept one interval-level table. Nightly weather repeats six times, so I use averages or attributes, not sums.”

**0:55–1:35 — Weather**

[Point to the annual bars and Weather Explorer. Switch to Feels-like temp, then back to Wind gust.]

“Turnout averages about 621 kids. Rainy evenings average 518, compared with 664 on dry evenings, a difference of about 22 percent. Wind gusts have the strongest association with turnout, with a correlation of minus 0.65. Temperature has almost no relationship. Cold 2017 still drew 776 kids, while rain and 47-mile-per-hour gusts coincided with only 391 in 2013. These are associations in a small sample, not causal estimates.”

**1:35–2:10 — The rush**

[Point to the Arrival Curve, then the purple heatmap.]

“About 53 percent of the kids arrive between 6:30 and 7:30, around the hour after the 6:37 sunset. The colors on the curve identify daylight, twilight, and darkness. The heatmap’s purple intensity means more kids, and the numbers show the actual counts. Its last column covers only 15 minutes, so the tooltip also provides a normalized rate on the arrival curve.”

**2:10–2:40 — Timing and weekdays**

[Point to Arrival Time Trend. Click 2013 on the annual bars to compare it across the year-based charts, then click blank space to clear. Optionally choose School vs weekend night.]

“The average arrival is 7:02 pm. Rainy nights run about five minutes earlier, and arrivals trend roughly five minutes earlier per decade. Friday and Saturday nights were not busier: 595 kids versus 632 on school nights, with only five weekend observations.”

**2:40–3:00 — Practical takeaway and limits**

“For this household, plan for about 690 kids on a calm, dry night and about 530 if it rains or gusts reach 25 mph. The most ever was 869. Be ready by 6:15. This describes one porch and a small number of nights; neighborhood conditions and weather reanalysis also limit how far we can generalize.”

## Likely questions

- **Why exclude 2020?** Its COVID candy-chute conditions were unusual for reasons outside this weather story. Show that the inclusion control changes the averages; it is an explicit sensitivity choice.
- **Did the join multiply counts?** No. There are exactly 108 interval rows, six for each of 18 years. Night-level fields repeat intentionally and are aggregated with AVG/ATTR.
- **Why is 2019 marked dry?** The definition only covers 6–8 pm. The supplied records show substantial rain earlier that day and strong gusts.
- **Does rain cause a 22 percent decline?** The analysis establishes an association, with small groups and possible confounding.
- **Why only label four dots?** To keep the plot readable. Every year remains available through its mark and tooltip.

Sources: Jeffrey Shaffer, course counts; [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api), ERA5/ECMWF/Copernicus; NOAA Global Monitoring Laboratory solar-position calculations. All reported statistics were checked against `data/intervals.csv` and `data/years.csv`.
