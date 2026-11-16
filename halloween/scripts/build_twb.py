"""Generate the Tableau workbook (.twb / .twbx) from data/Halloween_Enriched.xlsx.

Run from the halloween/ folder:  python3 scripts/build_twb.py
"""
import zipfile
import uuid
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
XLSX = ROOT / "data" / "Halloween_Enriched.xlsx"
OUTDIR = ROOT / "tableau"
NAME = "Halloween Weather and Trick-or-Treaters"
DASH = "Halloween Dashboard"
DS = "federated.0hw2026trickortreatweather01"
XC = "excel-direct.0hw2026halloweenenriched01"
DSREF = f"[{DS}]"


def sheet_id(name):
    return "{" + str(uuid.uuid5(uuid.NAMESPACE_URL, "BurchfieldFP/halloween/" + name)).upper() + "}"

# ------------------------------------------------------------------ palette
ORANGE, PURPLE, GOLD, NIGHT, INK, MUTED, RAIN, DRY = (
    "#E8590C", "#5B3F8C", "#F2B33D", "#2B1D3F", "#2E2A33", "#6E6875", "#2F7FC1", "#C27A28")
BG = "#FBF8F3"

COLOR_MAPS = {
    "[none:Rain or Dry:nk]": {"Rain": "#2F7FC1", "Dry": "#C27A28"},
    "[none:Light:nk]": {"Daylight": "#BBA8E0", "Twilight": "#8566BE", "Dark": "#4A2F7A"},
    "[none:Calculation_ColorBy:nk]": {
        "Rain": "#2F7FC1", "Dry": "#C27A28",
        "Chilly (< 50°F)": "#3F86C8", "Mild (50–59°F)": "#B98512", "Warm (60°F +)": "#C8424F",
        "School night (Sun–Thu)": "#5B3F8C", "Weekend night (Fri/Sat)": "#E0570B",
    },
}

# ------------------------------------------------------------------ helpers
a = quoteattr


def q(s):  # Tableau string literal inside XML attribute
    return s.replace('"', '&quot;')


def run(text, size=None, bold=False, color=None, font=None, italic=False):
    attrs = []
    if bold:
        attrs.append("bold='true'")
    if italic:
        attrs.append("italic='true'")
    if color:
        attrs.append(f"fontcolor='{color}'")
    if font:
        attrs.append(f"fontname='{font}'")
    if size:
        attrs.append(f"fontsize='{size}'")
    return f"<run {' '.join(attrs)}>{escape(text)}</run>"


NL = "<run>Æ&#10;</run>"


def field_run(instance, **kw):
    return run(f"<{DSREF}.{instance}>", **kw)


# ------------------------------------------------------------------ data-source columns
def read_columns():
    wb = openpyxl.load_workbook(XLSX, read_only=True)
    ws = wb["Intervals"]
    rows = list(ws.iter_rows(values_only=True))
    header, body = rows[0], rows[1:]
    cols = []
    for j, h in enumerate(header):
        vals = [r[j] for r in body if r[j] is not None]
        import datetime as dt
        if all(isinstance(v, dt.datetime) for v in vals):
            t = "datetime" if any(v.hour or v.minute for v in vals) else "date"
        elif all(isinstance(v, bool) for v in vals):
            t = "boolean"
        elif all(isinstance(v, (int, float)) for v in vals):
            t = "integer" if all(float(v).is_integer() for v in vals) else "real"
        else:
            t = "string"
        cols.append((h, t))
    return cols, len(body)


REMOTE = {"integer": ("20", "I8", "Sum"), "real": ("5", "R8", "Sum"), "string": ("130", "WSTR", "Count"),
          "date": ("7", "DATE", "Year"), "datetime": ("7", "DATE", "Year"), "boolean": ("11", "BOOL", "Count")}

DIMENSION_NUMBERS = {"Year", "Interval Order"}
INTERVAL_ALIASES = {1: "Before 6:00", 2: "6:00–6:30", 3: "6:30–7:00", 4: "7:00–7:30", 5: "7:30–8:00", 6: "8:00–8:15"}

PARAMS = {
    "Parameter 1": dict(caption="2020 (COVID year)", value="Exclude 2020", members=["Exclude 2020", "Include 2020"]),
    "Parameter 2": dict(caption="Color years by", value="Rain or dry", members=["Rain or dry", "Temperature", "School vs weekend night"]),
    "Parameter 3": dict(caption="Weather measure (x-axis)", value="Wind gust (mph)",
                        members=["Wind gust (mph)", "Wind speed (mph)", "Rain 6-8 pm (in)", "Feels-like temp (F)", "Cloud cover (%)"]),
}

# name -> (caption, datatype, role, type, formula)
CALCS = {
    "Calculation_RainAvg": ("Rain night average", "real", "measure", "quantitative",
                             'SUM(IF [Rain or Dry] = "Rain" THEN [Count] END) / COUNTD(IF [Rain or Dry] = "Rain" THEN [Year] END)'),
    "Calculation_DryAvg": ("Dry night average", "real", "measure", "quantitative",
                            'SUM(IF [Rain or Dry] = "Dry" THEN [Count] END) / COUNTD(IF [Rain or Dry] = "Dry" THEN [Year] END)'),
    "Calculation_RainN": ("Rain nights", "integer", "measure", "quantitative",
                           'COUNTD(IF [Rain or Dry] = "Rain" THEN [Year] END)'),
    "Calculation_DryN": ("Dry nights", "integer", "measure", "quantitative",
                          'COUNTD(IF [Rain or Dry] = "Dry" THEN [Year] END)'),
    # Aggregate string (like RateLabel): a row-level string dimension on Tooltip
    # turned the pill invalid in Tableau 2026.3 and blanked the whole Arrival Curve.
    "Calculation_WindowLength": ("Window length", "string", "measure", "nominal",
                                  'IF ISNULL(MIN([Interval Minutes])) THEN "Open-ended early arrivals" ELSE STR(MIN([Interval Minutes])) + " min" END'),
    "Calculation_RateLabel": ("Kids per 15 min label", "string", "measure", "nominal",
                               'IF ISNULL(AVG([Kids per 15 Min])) THEN "Not applicable (open-ended window)" ELSE STR(ROUND(AVG([Kids per 15 Min]), 1)) END'),
    "Calculation_YearLabel": ("Key year label", "string", "dimension", "nominal",
                              'IF [Year] = 2011 OR [Year] = 2013 OR [Year] = 2017 OR [Year] = 2019 THEN STR([Year]) ELSE "" END'),
    "Calculation_KeepYear": ("Keep Year?", "boolean", "dimension", "nominal",
                             '[Parameters].[Parameter 1] = "Include 2020" OR [Year] <> 2020'),
    "Calculation_KidsPerNight": ("Kids per Night", "real", "measure", "quantitative",
                                 "SUM([Count]) / COUNTD([Year])"),
    "Calculation_Share": ("Share of All Kids", "real", "measure", "quantitative",
                          "SUM([Count]) / MIN({ FIXED [Calculation_KeepYear] : SUM([Count]) })"),
    "Calculation_PeakShare": ("Peak Hour Share", "real", "measure", "quantitative",
                              "SUM(IF [Interval Order] = 3 OR [Interval Order] = 4 THEN [Count] END) / SUM([Count])"),
    "Calculation_RainEffect": ("Rain vs Dry", "real", "measure", "quantitative",
                               '(SUM(IF [Rain or Dry] = "Rain" THEN [Count] END) / COUNTD(IF [Rain or Dry] = "Rain" THEN [Year] END))\n'
                               '/ (SUM(IF [Rain or Dry] = "Dry" THEN [Count] END) / COUNTD(IF [Rain or Dry] = "Dry" THEN [Year] END)) - 1'),
    "Calculation_ArrMin": ("Avg Arrival (min after 6 pm)", "real", "measure", "quantitative",
                           "SUM([Count] * [Arrival Minute]) / SUM([Count])"),
    "Calculation_ArrTime": ("Avg Arrival Time", "string", "measure", "nominal",
                            'STR(6 + INT(INT(ROUND([Calculation_ArrMin], 0)) / 60)) + ":" + '
                            'RIGHT("0" + STR(INT(ROUND([Calculation_ArrMin], 0)) % 60), 2) + " pm"'),
    "Calculation_ColorBy": ("Year grouping", "string", "dimension", "nominal",
                            'CASE [Parameters].[Parameter 2]\nWHEN "Rain or dry" THEN [Rain or Dry]\n'
                            'WHEN "Temperature" THEN [Temperature Band]\nELSE [Night Type]\nEND'),
    "Calculation_Weather": ("Selected Weather", "real", "measure", "quantitative",
                            'CASE [Parameters].[Parameter 3]\nWHEN "Wind gust (mph)" THEN AVG([Night Max Gust Mph])\n'
                            'WHEN "Wind speed (mph)" THEN AVG([Night Max Wind Mph])\n'
                            'WHEN "Rain 6-8 pm (in)" THEN AVG([Night Precip In])\n'
                            'WHEN "Feels-like temp (F)" THEN AVG([Night Feels Like F])\n'
                            'ELSE AVG([Night Cloud Cover Pct])\nEND'),
    "Calculation_YearTotal": ("Year Total (LOD)", "integer", "measure", "quantitative",
                              "{ FIXED [Year] : SUM([Count]) }"),
}
CALC_PARAMS = {"Calculation_KeepYear": ["Parameter 1"], "Calculation_ColorBy": ["Parameter 2"],
               "Calculation_Weather": ["Parameter 3"]}
CALC_DEPS = {"Calculation_ArrTime": ["Calculation_ArrMin"], "Calculation_Share": ["Calculation_KeepYear"]}


# Friendly display names: these show up as axis, header and legend titles.
BASE_CAPTIONS = {"Count": "Kids", "Interval Order": "Arrival window"}


def col_def(name, dtype, cols_by_name, with_calc=True):
    """<column> element for a base or calculated field."""
    if name in CALCS:
        cap, dt, role, typ, f = CALCS[name]
        body = f"<calculation class='tableau' formula={a(f)} />" if with_calc else ""
        return f"<column caption={a(cap)} datatype='{dt}' name={a('[' + name + ']')} role='{role}' type='{typ}'>{body}</column>"
    dt = cols_by_name[name]
    cap = f" caption={a(BASE_CAPTIONS[name])}" if name in BASE_CAPTIONS else ""
    if name in DIMENSION_NUMBERS:
        inner = ""
        if name == "Interval Order":
            inner = "<aliases>" + "".join(f"<alias key='{k}' value={a(v)} />" for k, v in INTERVAL_ALIASES.items()) + "</aliases>"
        return f"<column{cap} datatype='{dt}' name={a('[' + name + ']')} role='dimension' type='ordinal'>{inner}</column>"
    if dt in ("integer", "real"):
        return f"<column{cap} datatype='{dt}' name={a('[' + name + ']')} role='measure' type='quantitative' />"
    return f"<column datatype='{dt}' name={a('[' + name + ']')} role='dimension' type='nominal' />"


def param_col(pname):
    p = PARAMS[pname]
    mem = "".join(f"<member value={a(chr(34) + m + chr(34))} />" for m in p["members"])
    return (f"<column caption={a(p['caption'])} datatype='string' name='[{pname}]' param-domain-type='list' "
            f"role='measure' type='nominal' value={a(chr(34) + p['value'] + chr(34))}>"
            f"<calculation class='tableau' formula={a(chr(34) + p['value'] + chr(34))} /><members>{mem}</members></column>")


# ------------------------------------------------------------------ instances
def inst(field, deriv):
    """Return (instance_name, column, derivation, type)."""
    code = {"None": "none", "Sum": "sum", "Avg": "avg", "Attribute": "attr", "User": "usr", "Min": "min", "Max": "max", "Continuous": "none"}[deriv]
    if field in CALCS:
        dt, role, typ = CALCS[field][1], CALCS[field][2], CALCS[field][3]
    else:
        typ = None
    if deriv == "Continuous":
        t, suffix = "quantitative", "qk"
        deriv = "None"
    elif deriv == "None":
        t = "ordinal" if field in DIMENSION_NUMBERS else "nominal"
        suffix = "ok" if t == "ordinal" else "nk"
    elif deriv == "User":
        t = CALCS[field][3]
        suffix = "qk" if t == "quantitative" else "nk"
    elif deriv == "Attribute":
        t, suffix = "nominal", "nk"
    else:
        t, suffix = "quantitative", "qk"
    return f"[{code}:{field}:{suffix}]", field, deriv, t


class Sheet:
    def __init__(self, name, title_runs, mark, rows=None, cols=None, enc=None, tooltip=None, label=None,
                 label_show=False, formats=None, keep_filter=True, extra_style="", mark_size=None):
        self.name, self.title_runs, self.mark = name, title_runs, mark
        self.rows, self.cols = rows or [], cols or []
        self.enc = enc or {}            # kind -> list[(field, deriv)]
        self.tooltip, self.label, self.label_show = tooltip, label, label_show
        self.formats = formats or {}    # (field, deriv) -> format string
        self.keep_filter = keep_filter
        self.extra_style = extra_style
        self.mark_size = mark_size

    def instances(self):
        used = list(self.rows) + list(self.cols)
        for v in self.enc.values():
            used += v
        if self.keep_filter:
            used.append(("Calculation_KeepYear", "None"))
        seen, out = set(), []
        for f, d in used:
            if (f, d) not in seen:
                seen.add((f, d))
                out.append((f, d))
        return out

    def xml(self, cols_by_name):
        insts = self.instances()
        fields = []
        for f, _ in insts:
            stack = [f]
            while stack:
                x = stack.pop()
                if x not in fields:
                    fields.append(x)
                for dep in CALC_DEPS.get(x, []):
                    stack.append(dep)
        # base columns referenced inside calcs must be declared too
        base_refs = set()
        for f in fields:
            if f in CALCS:
                for c in cols_by_name:
                    if f"[{c}]" in CALCS[f][4]:
                        base_refs.add(c)
        all_fields = fields + sorted(c for c in base_refs if c not in fields)
        params = sorted({p for f in all_fields for p in CALC_PARAMS.get(f, [])})

        deps = "".join(col_def(f, None, cols_by_name) for f in all_fields)
        ci = ""
        for f, d in insts:
            n, c, dv, t = inst(f, d)
            ci += f"<column-instance column={a('[' + c + ']')} derivation='{dv}' name={a(n)} pivot='key' type='{t}' />"
        dsx = f"<datasource caption='Halloween Data' name='{DS}' />"
        pdeps = ""
        # Parameters are dependencies, never primary worksheet datasources.
        # Listing Parameters first in <datasources> silently clears every shelf.
        if params:
            pdeps = "<datasource-dependencies datasource='Parameters'>" + "".join(param_col(p) for p in params) + "</datasource-dependencies>"
        filt = slices = ""
        if self.keep_filter:
            n = inst("Calculation_KeepYear", "None")[0]
            filt = (f"<filter class='categorical' column={a(DSREF + '.' + n)}>"
                    f"<groupfilter function='member' level={a(n)} member='true' user:ui-domain='database' "
                    f"user:ui-enumeration='inclusive' user:ui-marker='enumerate' /></filter>")
            slices = f"<slices><column>{escape(DSREF + '.' + n)}</column></slices>"

        def shelf(lst):
            return " / ".join(f"{DSREF}.{inst(f, d)[0]}" for f, d in lst)

        trend = ""
        if self.name == "Year by Year":
            axis = DSREF + ".[sum:Count:qk]"
            trend = f"<reference-line axis-column={a(axis)} enable-instant-analytics='false' formula='average' id='refline0' label='Overall average' label-type='custom' probability='95' scope='per-table' value-column={a(axis)} z-order='1' />"
        if self.name in ("Weather Explorer", "Arrival Time Trend"):
            trend = "<trendline enable-confidence-bands='false' enable-instant-analytics='true' enabled='true' exclude-color='true' exclude-intercept='false' fit='linear' />"
        enc = ""
        for kind, lst in self.enc.items():
            for f, d in lst:
                enc += f"<{kind} column={a(DSREF + '.' + inst(f, d)[0])} />"
        tip = f"<customized-tooltip><formatted-text>{self.tooltip}</formatted-text></customized-tooltip>" if self.tooltip else ""
        lab = f"<customized-label><formatted-text>{self.label}</formatted-text></customized-label>" if self.label else ""
        pane_style = ""
        rules = []
        if self.label_show or self.label:
            rules.append("<format attr='mark-labels-show' value='true' />")
        if self.mark_size:
            rules.append(f"<format attr='size' value='{self.mark_size}' />")
        if rules:
            pane_style = "<style><style-rule element='mark'>" + "".join(rules) + "</style-rule>"
            if self.name == "Rush Hour Heatmap":
                pane_style += "<style-rule element='datalabel'><format attr='color-mode' value='auto' /><format attr='font-size' value='10' /></style-rule>"
            pane_style += "</style>"

        fmt = ""
        if self.formats:
            fmt = "<style-rule element='cell'>" + "".join(
                f"<format attr='text-format' field={a(DSREF + '.' + inst(f, d)[0])} value={a(v)} />"
                for (f, d), v in self.formats.items()) + "</style-rule>"
        if self.name.startswith("KPI "):
            fmt += "<style-rule element='cell'><format attr='text-align' value='center' /><format attr='vertical-align' value='center' /></style-rule>"
        if self.name == "Arrival Time Trend":
            axis = DSREF + ".[usr:Calculation_ArrMin:qk]"
            fmt += f"<style-rule element='axis'><encoding attr='space' class='0' field={a(axis)} field-type='quantitative' min='45' max='75' range-type='fixed' scope='rows' type='space' /><format attr='title' class='0' field={a(axis)} scope='rows' value='Estimated arrival (min after 6 pm)' /></style-rule>"
        if self.name == "Weather Explorer":
            axis = DSREF + ".[usr:Calculation_Weather:qk]"
            # The datagraph below binds this cached title to Parameter 3.
            fmt += f"<style-rule element='axis'><format attr='title' class='0' field={a(axis)} scope='cols' value={a(PARAMS['Parameter 3']['value'])} /></style-rule>"
        style = f"<style>{fmt}{self.extra_style}<style-rule element='table'><format attr='background-color' value='{BG}' /></style-rule></style>"

        title = f"<layout-options><title><formatted-text>{self.title_runs}</formatted-text></title></layout-options>" if self.title_runs else ""
        return (f"<worksheet name={a(self.name)}>{title}<table><view><datasources>{dsx}</datasources>"
                f"<datasource-dependencies datasource='{DS}'>{deps}{ci}</datasource-dependencies>{pdeps}"
                f"{filt}{slices}<aggregation value='true' /></view>{style}"
                f"<panes><pane selection-relaxation-option='selection-relaxation-allow'><view><breakdown value='auto' /></view>"
                f"<mark class='{self.mark}' /><encodings>{enc}</encodings>{trend}{tip}{lab}{pane_style}</pane></panes>"
                f"<rows>{escape(shelf(self.rows))}</rows><cols>{escape(shelf(self.cols))}</cols></table>"
                f"<simple-id uuid={a(sheet_id(self.name))} /></worksheet>")


# ------------------------------------------------------------------ sheet specs
T = "Tableau Semibold"
B = "Tableau Book"


def title(main, sub=None):
    s = run(main, size=13, color=INK, font=T)
    if sub:
        s += NL + run(sub, size=9, color=MUTED, font=B)
    return s


def tip_line(label, fieldinst):
    return run(label, color=MUTED, font=B) + field_run(fieldinst, bold=True, color=INK, font=T) + NL


def kpi(name, field, deriv, caption, fmt=None, color=ORANGE):
    fi = inst(field, deriv)[0]
    label = field_run(fi, size=30, bold=True, color=color, font=T) + NL + run(caption, size=10, color=MUTED, font=B)
    return Sheet(name, None, "Text", enc={"text": [(field, deriv)]}, label=label,
                 formats={(field, deriv): fmt} if fmt else None,
                 tooltip=run(caption, font=B))


SHEETS = [
    kpi("KPI Kids per Night", "Calculation_KidsPerNight", "User", "kids per Halloween, on average", "n#,##0"),
    kpi("KPI Peak Hour", "Calculation_PeakShare", "User", "arrive between 6:30 and 7:30 pm", "p0%", PURPLE),
    kpi("KPI Rain Effect", "Calculation_RainEffect", "User", "average turnout: rain vs. dry nights", "p0%", RAIN),
    kpi("KPI Arrival Time", "Calculation_ArrTime", "User", "estimated average arrival", None, ORANGE),

    Sheet("Year by Year",
          title("Every Halloween, 2008–2025", "Kids per night · click a bar to highlight its year"),
          "Bar", rows=[("Count", "Sum")], cols=[("Year", "None")],
          enc={"color": [("Calculation_ColorBy", "None")], "text": [("Count", "Sum")],
               "tooltip": [("Day of Week", "Attribute"), ("Conditions", "Attribute"), ("Night Feels Like F", "Avg"),
                           ("Night Precip In", "Avg"), ("Night Max Gust Mph", "Avg"), ("Note", "Attribute")]},
          label_show=True,
          tooltip=(field_run("[none:Year:ok]", size=12, bold=True, color=ORANGE, font=T) + run("  ·  ", color=MUTED)
                   + field_run("[attr:Day of Week:nk]", color=INK, font=B) + NL
                   + tip_line("Trick-or-treaters: ", "[sum:Count:qk]")
                   + tip_line("Conditions 6–8 pm: ", "[attr:Conditions:nk]")
                   + tip_line("Feels-like temp (°F): ", "[avg:Night Feels Like F:qk]")
                   + tip_line("Rain 6–8 pm (in): ", "[avg:Night Precip In:qk]")
                   + tip_line("Peak wind gust (mph): ", "[avg:Night Max Gust Mph:qk]")
                   + field_run("[attr:Note:nk]", italic=True, color=MUTED, font=B)),
          formats={("Night Feels Like F", "Avg"): "n#,##0.0", ("Night Precip In", "Avg"): "n#,##0.00",
                   ("Night Max Gust Mph", "Avg"): "n#,##0"}),

    Sheet("Arrival Curve",
          title("When they come: the hour after sunset",
                "Kids per window · sunset ≈ 6:37 pm EDT · final window is 15 min"),
          "Bar", rows=[("Calculation_KidsPerNight", "User")], cols=[("Interval Order", "None")],
          enc={"color": [("Light", "None")], "text": [("Calculation_Share", "User")],
               "tooltip": [("Calculation_KidsPerNight", "User"), ("Calculation_WindowLength", "User"), ("Calculation_RateLabel", "User")]},
          label_show=True,
          tooltip=(field_run("[none:Interval Order:ok]", size=12, bold=True, color=ORANGE, font=T) + run("  ·  ") + field_run("[none:Light:nk]") + NL
                   + tip_line("Average kids per night: ", "[usr:Calculation_KidsPerNight:qk]")
                   + tip_line("Share of all kids: ", "[usr:Calculation_Share:qk]")
                   + tip_line("Window length: ", "[usr:Calculation_WindowLength:nk]")
                   + tip_line("Average kids per 15 min: ", "[usr:Calculation_RateLabel:nk]")),
          formats={("Calculation_KidsPerNight", "User"): "n#,##0", ("Calculation_Share", "User"): "p0%"}),

    Sheet("Rush Hour Heatmap",
          title("The trick-or-treat rush", "Kids per window · final window is 15 min"),
          "Square", rows=[("Year", "None")], cols=[("Interval Order", "None")],
          enc={"color": [("Count", "Sum")], "text": [("Count", "Sum")], "tooltip": [("Rain or Dry", "Attribute"), ("Interval Temp F", "Avg")]},
          label_show=True,
          tooltip=(field_run("[none:Year:ok]", bold=True, color=ORANGE, font=T) + run(" · ") + field_run("[none:Interval Order:ok]", bold=True, font=T) + NL
                   + tip_line("Kids: ", "[sum:Count:qk]")
                   + tip_line("Temperature (°F): ", "[avg:Interval Temp F:qk]")
                   + tip_line("Night was: ", "[attr:Rain or Dry:nk]")),
          formats={("Interval Temp F", "Avg"): "n#,##0"},
          extra_style=f"<style-rule element='mark'><encoding attr='color' field={a(DSREF + '.[sum:Count:qk]')} palette='purple_10_0' type='interpolated' /></style-rule>"),

    Sheet("Weather Explorer",
          title("Does the weather matter?", "One dot per Halloween · blue = rain, amber = dry · line = overall fit"),
          "Circle", rows=[("Count", "Sum")], cols=[("Calculation_Weather", "User")],
          enc={"color": [("Rain or Dry", "None")], "lod": [("Year", "None")], "text": [("Calculation_YearLabel", "None")],
               "tooltip": [("Conditions", "Attribute"), ("Night Feels Like F", "Avg"), ("Night Max Gust Mph", "Avg")]},
          label_show=True, mark_size="1.0",
          tooltip=(field_run("[none:Year:ok]", size=12, bold=True, color=ORANGE, font=T) + NL
                   + tip_line("Trick-or-treaters: ", "[sum:Count:qk]")
                   + tip_line("Selected weather value: ", "[usr:Calculation_Weather:qk]")
                   + tip_line("Conditions: ", "[attr:Conditions:nk]")
                   + tip_line("Feels-like (°F): ", "[avg:Night Feels Like F:qk]")
                   + tip_line("Peak gust (mph): ", "[avg:Night Max Gust Mph:qk]")),
          formats={("Calculation_Weather", "User"): "n#,##0.0", ("Night Feels Like F", "Avg"): "n#,##0",
                   ("Night Max Gust Mph", "Avg"): "n#,##0"}),

    Sheet("Arrival Time Trend",
          title("Are arrivals shifting earlier?", "Estimated from window midpoints · 60 = 7 pm · lower = earlier"),
          "Circle", rows=[("Calculation_ArrMin", "User")], cols=[("Year", "Continuous")],
          enc={"lod": [("Year", "None")], "color": [("Rain or Dry", "None")], "tooltip": [("Calculation_ArrTime", "User"), ("Conditions", "Attribute")]},
          mark_size="1.0",
          tooltip=(field_run("[none:Year:ok]", size=12, bold=True, color=ORANGE, font=T) + NL
                   + tip_line("Estimated average arrival: ", "[usr:Calculation_ArrTime:nk]")
                   + tip_line("Conditions: ", "[attr:Conditions:nk]")),
          formats={("Calculation_ArrMin", "User"): "n#,##0"}),
]

# Expose the comparison behind the percentage, including the number of nights.
rain_kpi = SHEETS[2]
rain_fields = ["Calculation_RainAvg", "Calculation_RainN", "Calculation_DryAvg", "Calculation_DryN"]
rain_kpi.enc["text"] += [(f, "User") for f in rain_fields]  # label runs can only read Text-shelf fields
rain_kpi.formats.update({(f, "User"): "n#,##0" for f in rain_fields})
comparison = (run("Rain ", size=9, color=INK, font=B)
              + field_run(inst("Calculation_RainAvg", "User")[0], size=9, color=INK, font=B)
              + run(" (n=", size=9, color=INK, font=B)
              + field_run(inst("Calculation_RainN", "User")[0], size=9, color=INK, font=B)
              + run(") · Dry ", size=9, color=INK, font=B)
              + field_run(inst("Calculation_DryAvg", "User")[0], size=9, color=INK, font=B)
              + run(" (n=", size=9, color=INK, font=B)
              + field_run(inst("Calculation_DryN", "User")[0], size=9, color=INK, font=B)
              + run(")", size=9, color=INK, font=B))
rain_kpi.label += NL + comparison
rain_kpi.tooltip = (run("Average kids per Halloween; n = number of nights.", font=B) + NL + comparison)

arrival_kpi = SHEETS[3]
arrival_kpi.label = (run("≈ ", size=30, bold=True, color=ORANGE, font=T) + arrival_kpi.label
                     + NL + run("kid-weighted · interval midpoints", size=9, color=MUTED, font=B))
arrival_kpi.tooltip = run("Estimated from interval midpoints, not individual arrival timestamps. Early arrivals use a representative 5:45 pm midpoint.", font=B)

SHEETS[5].title_runs += (NL + run("■", size=9, color="#BBA8E0", font=B) + run(" Daylight    ", size=9, color=INK, font=B)
                         + run("■", size=9, color="#8566BE", font=B) + run(" Twilight    ", size=9, color=INK, font=B)
                         + run("■", size=9, color="#4A2F7A", font=B) + run(" Dark", size=9, color=INK, font=B))

# ------------------------------------------------------------------ dashboard
W, H = 1920, 1080
_zid = [2]


def zid():
    _zid[0] += 1
    return _zid[0]


def box(x, y, w, h):
    return f"h='{round(h * 100000 / H)}' w='{round(w * 100000 / W)}' x='{round(x * 100000 / W)}' y='{round(y * 100000 / H)}'"


def zstyle(bg=None, margin=4, border=None):
    s = f"<format attr='margin' value='{margin}' />"
    if border:
        s += f"<format attr='border-color' value='{border}' /><format attr='border-style' value='solid' /><format attr='border-width' value='1' />"
    else:
        s += "<format attr='border-style' value='none' />"
    if bg:
        s += f"<format attr='background-color' value='{bg}' />"
    return f"<zone-style>{s}</zone-style>"


def text_zone(x, y, w, h, runs, bg=None, margin=8):
    return f"<zone {box(x, y, w, h)} id='{zid()}' type='text'><formatted-text>{runs}</formatted-text>{zstyle(bg, margin)}</zone>"


def sheet_zone(name, x, y, w, h, border="#E6DED3", show_title=True):
    st = "" if show_title else " show-title='false'"
    return f"<zone {box(x, y, w, h)} id='{zid()}' name={a(name)}{st}>{zstyle('#FFFFFF', 6, border)}</zone>"


def param_zone(pname, x, y, w, h):
    return f"<zone {box(x, y, w, h)} id='{zid()}' mode='compact' param='[Parameters].[{pname}]' type='paramctrl'>{zstyle(None, 4)}</zone>"


def legend_zone(sheet, inst_name, x, y, w, h):
    return f"<zone {box(x, y, w, h)} id='{zid()}' name={a(sheet)} param={a(DSREF + '.' + inst_name)} type='color'>{zstyle(None, 4)}</zone>"


def dashboard_xml():
    z = []
    # header band
    z.append(text_zone(0, 0, 1280, 112,
                       run("WHO SHOWS UP ON HALLOWEEN?", size=26, bold=True, color="#FFFFFF", font=T) + NL
                       + run("How weather and darkness shape the trick-or-treat rush — 2008–2025 · One porch in Cincinnati, OH 45207",
                             size=12, color="#F6D7B0", font=B),
                       bg=NIGHT, margin=14))
    z.append(text_zone(1290, 10, 620, 94,
                       run("HOW TO USE", size=9, bold=True, color=GOLD, font=T) + NL
                       + run("• Click a year (bar, dot or heat-map row) to highlight it across year-based charts. Click blank space to clear.", size=9, color="#FFFFFF", font=B) + NL
                       + run("• Use the three controls below to add 2020 back in, recolour the years, or swap the weather on the x-axis.", size=9, color="#FFFFFF", font=B) + NL
                       + run("• Hover over marks for values and weather details.", size=9, color="#FFFFFF", font=B),
                       bg=NIGHT, margin=6))
    # KPI strip
    xs = [16, 349, 682, 1015]
    for x, s in zip(xs, ["KPI Kids per Night", "KPI Peak Hour", "KPI Rain Effect", "KPI Arrival Time"]):
        z.append(sheet_zone(s, x, 122, 325, 110, show_title=False))
    # controls
    z.append(text_zone(1350, 120, 554, 26, run("CONTROLS", size=9, bold=True, color=ORANGE, font=T), margin=4))
    z.append(param_zone("Parameter 1", 1350, 146, 180, 58))
    z.append(param_zone("Parameter 2", 1537, 146, 180, 58))
    z.append(param_zone("Parameter 3", 1724, 146, 180, 58))
    z.append(text_zone(1350, 204, 554, 30,
                       run("2020 is excluded by default — the COVID candy-chute year is an outlier, not a weather effect.", size=8, italic=True, color=MUTED, font=B), margin=4))
    # row 2
    z.append(sheet_zone("Year by Year", 16, 242, 900, 380))
    z.append(legend_zone("Year by Year", "[none:Calculation_ColorBy:nk]", 922, 252, 196, 150))
    z.append(text_zone(922, 338, 196, 274,
                       run("WHAT STANDS OUT", size=9, bold=True, color=ORANGE, font=T) + NL
                       + run("Rain and wind align with smaller crowds.", size=10, color=INK, font=B) + NL + NL
                       + run("2013: 391 kids, rain + 47 mph gusts.", size=10, color=INK, font=B) + NL
                       + run("2017: 776 kids, 36°F feels-like.", size=10, color=INK, font=B) + NL + NL
                       + run("Weekend nights: 595 kids vs. 632 on school nights (5 vs. 12 years; excludes 2020).", size=10, color=INK, font=B),
                       bg="#FFFFFF", margin=8))
    z.append(sheet_zone("Arrival Curve", 1126, 242, 778, 380))
    # row 3
    z.append(sheet_zone("Rush Hour Heatmap", 16, 630, 600, 356))
    z.append(sheet_zone("Weather Explorer", 624, 630, 660, 356))
    z.append(sheet_zone("Arrival Time Trend", 1292, 630, 612, 356))
    # Keep the continuous count scale inside its own chart header.
    z.append(legend_zone("Rush Hour Heatmap", "[sum:Count:qk]", 408, 636, 200, 56))
    # footer
    z.append(text_zone(0, 994, 1920, 86,
                       run("SOURCES  ", size=9, bold=True, color=INK, font=T)
                       + run("Counts: Jeffrey Shaffer, HalloweenTableau2025.xlsx. Weather: Open-Meteo Historical Weather API / ERA5 (ECMWF/Copernicus), open-meteo.com/en/docs/historical-weather-api. Sun position: NOAA Global Monitoring Laboratory, General Solar Position Calculations.", size=9, color=MUTED, font=B) + NL
                       + run("METHOD  ", size=9, bold=True, color=INK, font=T)
                       + run("Weather timestamps corrected to EDT; rain = ≥ 0.01 in from 6–8 pm. Counts cover the window ending at the logged time; final window = 15 min. Arrival times are estimated from window midpoints. Repeated night-level fields use AVG/ATTR. Small sample: associations, not causation. ", size=9, color=MUTED, font=B)
                       + run("Individual class project", size=9, bold=True, color=PURPLE, font=T),
                       bg="#F1EBE2", margin=6))
    inner = "".join(z)
    return (f"<dashboards><dashboard name={a(DASH)}><style><style-rule element='table'><format attr='background-color' value='{BG}' /></style-rule></style>"
            f"<size maxheight='{H}' maxwidth='{W}' minheight='{H}' minwidth='{W}' />"
            "<datasources><datasource name='Parameters' /></datasources>"
            + "<datasource-dependencies datasource='Parameters'>" + "".join(param_col(p) for p in PARAMS) + "</datasource-dependencies>"
            +
            f"<zones><zone h='100000' id='2' type='layout-basic' w='100000' x='0' y='0'>{inner}</zone></zones>"
            f"<simple-id uuid={a(sheet_id(DASH))} />"
            f"</dashboard></dashboards>")


def actions_xml():
    return (f"<actions><action caption='Highlight year' name='[Action1_HighlightYear]'>"
            f"<activation auto-clear='true' type='on-select' />"
            f"<source dashboard={a(DASH)} type='sheet' />"
            f"<command command='tsc:brush'><param name='field-captions' value='Year' /><param name='target' value={a(DASH)} /></command>"
            f"</action></actions>")


def worksheet_cards(s):
    """Tableau 2026 requires <cards> (shelf layout) inside every worksheet window."""
    right = ""
    for f, d in s.enc.get("color", []):
        right += f"<card pane-specification-id='0' param={a(DSREF + '.' + inst(f, d)[0])} type='color' />"
    right = f"<edge name='right'><strip size='160'>{right}</strip></edge>" if right else ""
    return ("<cards><edge name='left'><strip size='160'><card type='pages' /><card type='filters' /><card type='marks' /></strip></edge>"
            "<edge name='top'><strip size='2147483647'><card type='columns' /></strip>"
            "<strip size='2147483647'><card type='rows' /></strip>"
            "<strip size='31'><card type='title' /></strip></edge>"
            f"{right}</cards>")


def windows_xml():
    w = "".join(f"<window class='worksheet' name={a(s.name)}>{worksheet_cards(s)}</window>" for s in SHEETS)
    vp = "".join(f"<viewpoint name={a(s.name)}><zoom type='entire-view' /></viewpoint>" for s in SHEETS)
    w += (f"<window class='dashboard' maximized='true' name={a(DASH)}><viewpoints>{vp}</viewpoints><active id='-1' />"
          f"<device-preview><device is-portrait='true' name='Generic Phone' type='Phone' /></device-preview></window>")
    return f"<windows source-height='30'>{w}</windows>"


def datasource_xml(cols, nrows, filename):
    last = openpyxl.utils.get_column_letter(len(cols))
    grid = f"A1:{last}{nrows + 1}:no:A1:{last}{nrows + 1}:0"
    rel_cols = "".join(f"<column datatype='{t}' name={a(n)} ordinal='{i}' />" for i, (n, t) in enumerate(cols))
    meta = (f"<metadata-record class='capability'><remote-name /><remote-type>0</remote-type><parent-name>[Intervals$]</parent-name>"
            f"<remote-alias /><aggregation>Count</aggregation><contains-null>true</contains-null><attributes>"
            f"<attribute datatype='integer' name='context'>0</attribute>"
            f"<attribute datatype='string' name='gridOrigin'>&quot;{grid}&quot;</attribute>"
            f"<attribute datatype='boolean' name='header'>true</attribute>"
            f"<attribute datatype='integer' name='outcome'>6</attribute></attributes></metadata-record>")
    for i, (n, t) in enumerate(cols):
        rt, dbg, agg = REMOTE[t]
        meta += (f"<metadata-record class='column'><remote-name>{escape(n)}</remote-name><remote-type>{rt}</remote-type>"
                 f"<local-name>{escape('[' + n + ']')}</local-name><parent-name>[Intervals$]</parent-name>"
                 f"<remote-alias>{escape(n)}</remote-alias><ordinal>{i}</ordinal><local-type>{t}</local-type>"
                 f"<aggregation>{agg}</aggregation><contains-null>true</contains-null><attributes>"
                 f"<attribute datatype='string' name='DebugRemoteType'>&quot;{dbg}&quot;</attribute></attributes></metadata-record>")
    cols_by_name = dict(cols)
    # Explicit field and palette instance definitions survive Tableau serialization.
    fields = "".join(col_def(n, t, cols_by_name) for n, t in cols)
    fields += "".join(col_def(c, None, cols_by_name) for c in CALCS)
    for field in ("Rain or Dry", "Light", "Calculation_ColorBy"):
        n, c, dv, t = inst(field, "None")
        fields += f"<column-instance column={a('[' + c + ']')} derivation='{dv}' name={a(n)} pivot='key' type='{t}' />"
    pal = ""
    for field, m in COLOR_MAPS.items():
        pal += f"<encoding attr='color' field={a(field)} type='palette'>" + "".join(
            f"<map to='{c}'><bucket>{escape(chr(34) + k + chr(34))}</bucket></map>" for k, c in m.items()) + "</encoding>"
    return (f"<datasource caption='Halloween Data' inline='true' name='{DS}' version='18.1'>"
            f"<connection class='federated'><named-connections><named-connection caption='Halloween_Enriched' name='{XC}'>"
            f"<connection class='excel-direct' cleaning='no' compat='no' dataRefreshTime='' filename={a(filename)} interpretationMode='0' password='' server='' validate='no' />"
            f"</named-connection></named-connections>"
            f"<relation connection='{XC}' name='Intervals' table='[Intervals$]' type='table'>"
            f"<columns gridOrigin='{grid}' header='yes' outcome='6'>{rel_cols}</columns></relation>"
            f"<metadata-records>{meta}</metadata-records></connection>"
            f"<aliases enabled='yes' />{fields}"

            f"<layout dim-ordering='alphabetic' measure-ordering='alphabetic' show-structure='true' />"
            f"<style><style-rule element='mark'>{pal}</style-rule></style>"
            f"<semantic-values><semantic-value key='[Country].[Name]' value='&quot;United States&quot;' /></semantic-values>"
            + "<datasource-dependencies datasource='Parameters'>" + "".join(param_col(p) for p in PARAMS) + "</datasource-dependencies>"
            + f"<object-graph><objects><object caption='Intervals' id='Intervals'><properties context=''><relation connection='{XC}' name='Intervals' table='[Intervals$]' type='table'><columns gridOrigin='{grid}' header='yes' outcome='6'>{rel_cols}</columns></relation></properties></object></objects></object-graph></datasource>")


def workbook_xml(filename):
    cols, nrows = read_columns()
    cols_by_name = dict(cols)
    params = ("<datasource hasconnection='false' inline='true' name='Parameters' version='18.1'><aliases enabled='yes' />"
              + "".join(param_col(p) for p in PARAMS) + "</datasource>")
    worksheets = "<worksheets>" + "".join(s.xml(cols_by_name) for s in SHEETS) + "</worksheets>"
    return ("<?xml version='1.0' encoding='utf-8' ?>\n"
            "<workbook source-build='2026.3.0 (20263.26.1022.1645)' source-platform='mac' version='18.1' "
            "xmlns:user='http://www.tableausoftware.com/xml/user'>"
            "<document-format-change-manifest><DatagraphCoreV1 /><DatagraphNodeAxisTitle /><DatagraphNodeSingleValueFieldV1 /><ObjectModelEncapsulateLegacy /><ObjectModelTableType /><SchemaViewerObjectModel /><SheetIdentifierTracking /></document-format-change-manifest>"
            "<preferences><preference name='ui.encoding.shelf.height' value='24' /><preference name='ui.shelf.height' value='26' /></preferences>"
            "<style><style-rule element='worksheet'><format attr='font-family' value='Tableau Book' /><format attr='font-size' value='9' /></style-rule></style>"
            f"<datasources>{params}{datasource_xml(cols, nrows, filename)}</datasources>"
            f"{actions_xml()}{worksheets}{dashboard_xml()}{windows_xml()}{dynamic_axis_xml()}</workbook>")


def dynamic_axis_xml():
    """Native Tableau parameter-to-axis binding, captured in Desktop 2026.3.

    The worksheet UUID must match the axis node's sheet-identifier. A static
    cached title alone would look correct initially but fail on parameter changes.
    """
    graph = "f44debb6-2a49-4fdc-b141-a1b4bf9326f4"
    axis = "f47b1186-999b-499b-91dd-f2c13afbe5c7"
    parameter = "57f123de-d1e8-4823-aeb4-32bfdd898fbb"
    return (f"<datagraph><graph><properties><default-execution-subgraph-guid value='{graph}' /></properties>"
            f"<node-execution-subgraphs><pair execution-subgraph-guid='{graph}' node-guid='{axis}' />"
            f"<pair execution-subgraph-guid='{graph}' node-guid='{parameter}' /></node-execution-subgraphs>"
            f"<nodes><single-value-field-node fieldname='[Parameters].[Parameter 3]' fieldname-input-guid='569bc973-6582-45c9-ad6e-8e2c7ab32d6c' node-guid='{parameter}' value-output-guid='09776e2c-0cce-4e7c-8d69-0ae488fe329a' />"
            f"<axis-title-node duplicate-index='0' fieldname={a(DSREF + '.[usr:Calculation_Weather:qk]')} node-guid='{axis}' orientation='horizontal' sheet-identifier={a(sheet_id('Weather Explorer'))} title-input-guid='ef8aa932-a1e5-4c42-8c2e-eb6a6cd905b9' /></nodes>"
            "<edges><edge from='09776e2c-0cce-4e7c-8d69-0ae488fe329a' to='ef8aa932-a1e5-4c42-8c2e-eb6a6cd905b9' /></edges><pin-values /></graph></datagraph>")


def main():
    OUTDIR.mkdir(exist_ok=True)
    # loose .twb sits next to a copy of the Excel file
    (OUTDIR / f"{NAME}.twb").write_text(workbook_xml("Halloween_Enriched.xlsx"), encoding="utf-8")
    (OUTDIR / "Halloween_Enriched.xlsx").write_bytes(XLSX.read_bytes())
    # packaged .twbx with the data inside
    _zid[0] = 2
    twbx = OUTDIR / f"{NAME}.twbx"
    with zipfile.ZipFile(twbx, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"{NAME}.twb", workbook_xml("Data/Halloween_Enriched.xlsx"))
        z.write(XLSX, "Data/Halloween_Enriched.xlsx")
    print("wrote", twbx)


if __name__ == "__main__":
    main()
