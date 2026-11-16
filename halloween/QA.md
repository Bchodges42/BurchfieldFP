# Tableau validation and submission status

Verified November 15, 2026, in Tableau Desktop Free Edition 2026.3 on macOS. The final package opens without a load error and uses its packaged Excel data. Changes originate in `scripts/build_twb.py`; the loose TWB was not hand-edited.

## Verified behavior

- All nine worksheets render: four KPI sheets and five analytical charts.
- Fixed dashboard dimensions: 1920 × 1080, confirmed in Tableau's Size control and workbook XML. The native PNG export is 3840 × 2160 because this Mac exports at Retina resolution.
- Default parameters: Exclude 2020; Rain or dry; Wind gust (mph). No selected marks are saved in the generated workbook.
- Default KPI values in Tableau: 621 kids, 53% peak-hour share, −22% rain-versus-dry difference, 7:02 pm weighted arrival.
- Rain is blue (#2F7FC1), dry is amber (#C27A28). Datasource-level palette instances make the mappings survive Tableau loading and saving. The student's chosen purple sequential heatmap is preserved, with a count legend.
- Temperature colors were observed after the live control change: blue Chilly, ochre Mild, red Warm. Darkness has its own labeled three-swatch key.
- Live dropdown check: the student exercised the controls after automation could not reliably open native combo boxes. The resulting Tableau state was read and exported: Include 2020 / Temperature / Feels-like temp (F). The KPI average became 598; peak share 52%; rain difference −18%; the scatter changed to temperature with a nearly flat overall fit.
- A selected year and resolved heatmap tooltip were visible in the student's supplied Tableau screenshot. The Year highlight action is retained, and directions explain clicking blank space to clear. Only the year-based charts contain Year marks; the aggregated arrival curve and KPIs are not described as year-level targets.
- Overall linear trend lines are present in both scatter plots, without separate rain/dry regression models. Arrival Time Trend uses continuous Year plus discrete Year on Detail. The yearly bars include an overall-average reference line.
- Key-year-only labels prevent scatter-label collisions. Every other year's identity remains in its tooltip.
- Tooltips include weather units. The arrival tooltip gives window duration and kids per 15 minutes, with an explicit “not applicable” label for the open-ended pre-6:00 window.
- The full native Tableau export was visually reviewed for clipped titles, overlapping labels, visible citations, font consistency, and footer fit. It is saved as `tableau/Halloween Dashboard.png`.

## Independent data checks

The existing CSVs contain 108 unique (Year, Interval Order) pairs: 18 years, six rows each. With 2020 excluded:

| Quantity | Recomputed value |
|---|---:|
| Mean kids per night | 620.7647 |
| Share in interval orders 3 and 4 | 52.5159% |
| Rain-night mean | 517.6 |
| Dry-night mean | 663.75 |
| Rain relative to dry | −22.0188% |
| Weighted mean arrival, minutes after 6 pm | 61.7327 |
| Gust/count Pearson correlation | −0.647736 |
| Feels-like/count Pearson correlation | −0.011258 |
| Weekend mean (5 nights) | 594.6 |
| School-night mean (12 nights) | 631.6667 |

Including 2020 gives 598.4444 kids per night. These checks use `data/intervals.csv` and `data/years.csv`; no weather API requests or new statistical claims were introduced.

Package checks passed for ZIP integrity, nine populated worksheet specifications, a Keep Year filter on every sheet, parameter dependency placement, persistent palette instances, fixed size, both trend lines, and the average line.

## Rubric coverage and remaining submission work

| Rubric area | Status |
|---|---|
| Story, appended external data, four or more visualizations, fixed dashboard, interaction | Workbook contains the weather/darkness/day-of-week story, external weather, five charts, fixed size, three parameters, and Year highlighting. |
| Data appropriate and sufficient | Course counts + historical weather + computed sun position; grain/time-zone pitfalls documented; small-sample and association caveats visible. |
| Headers, directions, tooltips, citations | Present in the native dashboard and source workbook. |
| Visuals support analysis | Annual totals, arrival timing, interval heatmap, selectable weather relationship, and arrival trend; group sizes noted for weekdays. |
| Design, spelling, fonts | Tableau Book/Semibold; explicit units and legends; reduced label crowding; no partner placeholder. |
| Team-name email | Not sent. Student is working individually and elected to handle any instructor communication personally. Check whether the professor still requires an individual-project notice. |
| Upload to Teams | Not uploaded. Submit the TWBX through the course's specified Teams destination. |
| Presentation | Three-minute solo script and likely questions in `PRESENTATION.md`. |
| Optional Word write-up | Not created; the actual Tableau PNG is available if a write-up is later requested. |

The original HTML preview is a concept mockup and may differ from the final workbook. Older Tableau releases were not tested. On a laptop smaller than 1920 × 1080 logical pixels, Tableau may require scrolling; the dashboard's required fixed dimensions remain unchanged.

## Clarity pass (November 15, 2026, evening)

Re-verified in Tableau Desktop 2026.3 after a rubric review:

- **Fixed a blank Arrival Curve.** The "Window length" tooltip field was a row-level string dimension, which Tableau 2026.3 marked invalid, blanking the whole chart. It is now an aggregate string, like "Kids per 15 min label".
- The rain KPI now shows the comparison behind −22%: Rain 518 (n=5) · Dry 664 (n=12). These fields moved from Tooltip to the Text shelf so the label can read them.
- The arrival KPI reads "≈ 7:02 pm, estimated average arrival · kid-weighted · interval midpoints"; the trend chart's subtitle and axis say "estimated".
- The Weather Explorer x-axis title follows the Weather measure control (Tableau datagraph binding), e.g. "Wind gust (mph)".
- Display captions: Count → "Kids" (axes, legend), Interval Order → "Arrival window" (headers).
- The heatmap legend sits in the heatmap's own header; footer and note text enlarged to 9–10 pt.
- Native export reviewed: `tableau/Halloween Dashboard.png`.
- Plain-English rewrite of all dashboard text (titles, KPI captions, how-to, notes, footer, tooltips); no statistics changed. Controls renamed: COVID year, Color bars by, Weather on scatter plot.
- Temperature and weekend colors changed (Chilly teal, Mild gray, Warm red; Weekend teal) so they never reuse the rain-blue / dry-orange pair.
