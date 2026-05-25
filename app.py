import streamlit as st
import os
import base64
import subprocess
import tempfile
import pandas as pd
from datetime import datetime, timedelta

# ── Constants ────────────────────────────────────────────────────────────────

BALKAN_COUNTRIES = [
    "Albania", "Bosnia and Herzegovina", "Bulgaria", "Croatia", "Kosovo",
    "Montenegro", "North Macedonia", "Romania", "Serbia", "Slovenia",
]

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

KOSOVO_REGIONS = [
    "REG - Ferizaj", "REG - Gjakovë", "REG - Gjilan",
    "REG - Mitrovicë", "REG - Pejë", "REG - Prishtinë", "REG - Prizren",
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH  = os.path.join(SCRIPT_DIR, "UBO Logo.png")

# Country flag emoji mapping
COUNTRY_FLAGS = {
    "Albania": "\U0001f1e6\U0001f1f1",
    "Bosnia and Herzegovina": "\U0001f1e7\U0001f1e6",
    "Bulgaria": "\U0001f1e7\U0001f1ec",
    "Croatia": "\U0001f1ed\U0001f1f7",
    "Kosovo": "\U0001f1fd\U0001f1f0",
    "Montenegro": "\U0001f1f2\U0001f1ea",
    "North Macedonia": "\U0001f1f2\U0001f1f0",
    "Romania": "\U0001f1f7\U0001f1f4",
    "Serbia": "\U0001f1f7\U0001f1f8",
    "Slovenia": "\U0001f1f8\U0001f1ee",
}

# Gradient pairs per country for the pill
COUNTRY_GRADIENTS = {
    "Albania": ("F03D8F", "F5A623"),
    "Bosnia and Herzegovina": ("4B9EE8", "2DCAAA"),
    "Bulgaria": ("2DCAAA", "4B9EE8"),
    "Croatia": ("4B9EE8", "F03D8F"),
    "Kosovo": ("F5D52A", "F03D8F"),
    "Montenegro": ("2DCAAA", "F5D52A"),
    "North Macedonia": ("F03D8F", "F5A623"),
    "Romania": ("4B9EE8", "F5D52A"),
    "Serbia": ("F03D8F", "4B9EE8"),
    "Slovenia": ("2DCAAA", "F03D8F"),
}


def _logo_base64():
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None


# ── HTML builder ──────────────────────────────────────────────────────────────

def _country_rows_html(studies_df, country):
    cpi_col = f"CPI \u2013 {country} (\u20ac)"
    rows_html = ""
    country_total = 0.0

    has_desc = any(
        str(r.get("Study Description", "")).strip()
        for _, r in studies_df.iterrows()
    )

    # Check if LOI range varies (need two columns) or is always equal (one column)
    has_loi_range = any(
        int(r.get("LOI From", 15)) != int(r.get("LOI To", 20))
        for _, r in studies_df.iterrows()
    )

    for _, row in studies_df.iterrows():
        study_name  = str(row.get("Study Name", "")).strip()
        description = str(row.get("Study Description", "")).strip()
        n         = int(row.get("N", 1000))
        loi_from  = int(row.get("LOI From", 15))
        loi_to    = int(row.get("LOI To", 20))
        ir        = float(row.get("IR (%)", 90))
        cpi       = float(row.get(cpi_col, 0) or 0)
        cost      = n * cpi
        country_total += cost

        sub_line = f"{loi_from} min survey" if loi_from == loi_to else f"{loi_from}\u2013{loi_to} min survey"
        desc_name = study_name if study_name else "Study"

        desc_td = ""
        if has_desc:
            desc_td = f'<td class="center desc-cell">{description}</td>'

        if has_loi_range:
            loi_tds = (f'<td class="center"><span class="loi-tag">{loi_from} min</span></td>'
                       f'<td class="center"><span class="loi-tag">{loi_to} min</span></td>')
        else:
            loi_tds = f'<td class="center"><span class="loi-tag">{loi_from} min</span></td>'

        rows_html += f"""
        <tr>
          <td>
            <div class="row-label">{desc_name}</div>
            <div class="row-sub">{sub_line}</div>
          </td>
          {desc_td}
          <td class="center"><span class="n-val">{n:,}</span></td>
          <td class="center">{ir:.0f}%</td>
          {loi_tds}
          <td class="center"><span class="cpi-val">&euro; {cpi:.2f}</span></td>
          <td><span class="cost-val">&euro; {cost:,.2f}</span></td>
        </tr>"""

    return rows_html, country_total, has_desc, has_loi_range


def build_html(client, contact, proposal_no, studies_df, countries,
               quotas, field_timing, tc_text="", additional=""):

    today = datetime.now()
    date_str = today.strftime("%d %B %Y")
    valid_until = (today + timedelta(days=30)).strftime("%d %B %Y")

    logo_b64 = _logo_base64()
    logo_html = ""
    if logo_b64:
        logo_html = f'<img class="logo-img" src="data:image/png;base64,{logo_b64}" />'
    else:
        # SVG fallback
        logo_html = """<svg class="logo-svg" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <clipPath id="tr"><rect x="50" y="0" width="50" height="50"/></clipPath>
        <circle cx="50" cy="50" r="38" fill="#2DCAAA" clip-path="url(#tr)" opacity="0.95"/>
        <clipPath id="bl"><rect x="0" y="50" width="50" height="50"/></clipPath>
        <circle cx="50" cy="50" r="38" fill="#F5D52A" clip-path="url(#bl)" opacity="0.95"/>
        <clipPath id="la"><rect x="0" y="0" width="50" height="50"/></clipPath>
        <circle cx="50" cy="50" r="38" fill="none" stroke="#4B9EE8" stroke-width="14" clip-path="url(#la)" opacity="0.95"/>
        <clipPath id="ra"><rect x="50" y="50" width="50" height="50"/></clipPath>
        <circle cx="50" cy="50" r="38" fill="none" stroke="#F03D8F" stroke-width="14" clip-path="url(#ra)" opacity="0.95"/>
      </svg>"""

    # Build target info items
    target_items = []
    if quotas.get("gender"):
        target_items.append(("Gender", ", ".join(quotas["gender"])))
    if quotas.get("age"):
        target_items.append(("Age", quotas["age"]))
    if quotas.get("region"):
        target_items.append(("Region", ", ".join(quotas["region"])))
    if quotas.get("income"):
        target_items.append(("Income", quotas["income"]))
    if quotas.get("education"):
        target_items.append(("Education", quotas["education"]))
    target_html = ""
    if target_items:
        items_html = ""
        for label, value in target_items:
            items_html += f'<div class="target-item"><span class="target-label">{label}</span><span class="target-value">{value}</span></div>\n'
        target_html = f'<div class="target-bar"><span class="target-title">Target</span>{items_html}</div>'

    # Build quotas bar
    quotas_html = ""
    quota_vars_list = quotas.get("quota_vars", [])
    if quota_vars_list:
        qv_str = ", ".join(quota_vars_list)
        nested_part = ""
        if quotas.get("nested"):
            nested_part = f'<div class="target-item"><span class="target-label">Nested</span><span class="target-value">{" &times; ".join(quotas["nested"])}</span></div>'
        quotas_html = f'<div class="target-bar" style="margin-top:6px;"><span class="target-title">Quotas</span><div class="target-item"><span class="target-value">{qv_str}</span></div>{nested_part}</div>'

    # Build country sections
    countries_html = ""
    for country in countries:
        flag = COUNTRY_FLAGS.get(country, "")
        g1, g2 = COUNTRY_GRADIENTS.get(country, ("4B9EE8", "2DCAAA"))
        rows_html, total, has_desc, has_loi_range = _country_rows_html(studies_df, country)

        desc_th = '<th class="center">Description</th>' if has_desc else ""
        if has_loi_range:
            loi_ths = '<th class="center">LOI (min)</th><th class="center">LOI (max)</th>'
        else:
            loi_ths = '<th class="center">LOI</th>'

        # Count columns: Study + (desc?) + N + IR + LOI(1 or 2) + CPI + Cost
        num_cols = 5 + (1 if has_desc else 0) + (2 if has_loi_range else 1)

        countries_html += f"""
  <div class="country-section">
    <div class="section-heading">
      <div class="country-pill" style="background: linear-gradient(135deg, #{g1}, #{g2});">
        <span class="country-flag">{flag}</span> {country}
      </div>
      <div class="section-divider"></div>
    </div>

    {target_html}
    {quotas_html}

    <table class="offer-table">
      <thead>
        <tr>
          <th>Study</th>
          {desc_th}
          <th class="center">Sample (N)</th>
          <th class="center">IR</th>
          {loi_ths}
          <th class="center">CPI</th>
          <th>Total Cost</th>
        </tr>
      </thead>
      <tbody>
        {rows_html}
        <tr class="total-row">
          <td colspan="{num_cols - 1}" class="total-label">Total</td>
          <td class="total-val">&euro; {total:,.2f}</td>
        </tr>
      </tbody>
    </table>
  </div>"""

    field_info = field_timing if field_timing.strip() else "To be confirmed"

    # Build T&C bullet list from user input
    tc_lines = [line.strip() for line in tc_text.split("\n") if line.strip()]
    tc_lis = "\n      ".join(f"<li>{line}</li>" for line in tc_lines)

    # Additional notes block (only rendered if user entered anything)
    if additional and additional.strip():
        additional_lines = [line.strip() for line in additional.split("\n") if line.strip()]
        additional_items = "\n      ".join(f"<li>{line}</li>" for line in additional_lines)
        additional_html = f"""<div class="notes-block">
    <div class="notes-title">Additional Notes</div>
    <ul class="notes-list" style="grid-template-columns: 1fr;">
      {additional_items}
    </ul>
  </div>"""
    else:
        additional_html = ""

    # Countries list for sub-header
    countries_label = ", ".join(countries) if countries else ""
    sub_header_text = f"Sample Panel Services \u00b7 {countries_label}"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Financial Offer &ndash; {client}</title>
<style>
  @page {{
    size: A4 portrait;
    margin: 0;
  }}

  :root {{
    --teal: #2DCAAA;
    --blue: #4B9EE8;
    --yellow: #F5D52A;
    --pink: #F03D8F;
    --dark: #1A1A2E;
    --mid: #2E3250;
    --light-bg: #F7F8FC;
    --border: #E4E7F0;
    --text: #2A2D40;
    --muted: #7B7F9E;
  }}

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    background: var(--light-bg);
    color: var(--text);
    min-height: 100vh;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}

  /* ── HEADER ── */
  .header {{
    background: var(--dark);
    padding: 0;
    position: relative;
    overflow: hidden;
  }}

  .header::before {{
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 280px; height: 280px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(45,202,170,0.18) 0%, transparent 70%);
  }}
  .header::after {{
    content: '';
    position: absolute;
    bottom: -80px; left: 120px;
    width: 200px; height: 200px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(240,61,143,0.12) 0%, transparent 70%);
  }}

  .header-inner {{
    max-width: 960px;
    margin: 0 auto;
    padding: 24px 32px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 24px;
    position: relative;
    z-index: 1;
  }}

  .logo-block {{
    display: flex;
    align-items: center;
    gap: 18px;
  }}

  .logo-svg, .logo-img {{
    width: 52px;
    height: 52px;
    flex-shrink: 0;
    object-fit: contain;
  }}

  .logo-text {{
    display: flex;
    flex-direction: column;
  }}
  .logo-text strong {{
    font-size: 18px;
    color: #fff;
    letter-spacing: 0.02em;
    line-height: 1.2;
  }}
  .logo-text span {{
    font-size: 12px;
    color: var(--teal);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-weight: 600;
    margin-top: 2px;
  }}

  .header-right {{
    text-align: right;
  }}
  .header-title {{
    font-size: 28px;
    font-weight: 700;
    color: #fff;
    letter-spacing: -0.01em;
    line-height: 1.1;
  }}
  .header-title em {{
    color: var(--teal);
    font-style: normal;
  }}
  .header-sub {{
    font-size: 13px;
    color: rgba(255,255,255,0.45);
    margin-top: 6px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }}

  /* ── COLOR ACCENT BAR ── */
  .accent-bar {{
    height: 5px;
    background: linear-gradient(90deg, var(--teal) 0%, var(--blue) 33%, var(--yellow) 66%, var(--pink) 100%);
  }}

  /* ── MAIN ── */
  .main {{
    max-width: 960px;
    margin: 0 auto;
    padding: 20px 28px 30px;
  }}

  /* ── META GRID ── */
  .meta-grid {{
    display: flex;
    gap: 0;
    background: var(--border);
    border: 1px solid var(--border);
    border-radius: 14px;
    overflow: hidden;
    margin-bottom: 20px;
    page-break-inside: avoid;
    break-inside: avoid;
  }}
  .meta-cell {{
    flex: 1;
    background: #fff;
    padding: 12px 16px;
    border-right: 1px solid var(--border);
  }}
  .meta-cell:last-child {{ border-right: none; }}
  .meta-label {{
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--muted);
    font-weight: 600;
    margin-bottom: 3px;
  }}
  .meta-value {{
    font-size: 12px;
    font-weight: 600;
    color: var(--text);
    line-height: 1.3;
  }}

  /* ── SECTION ── */
  .country-section {{
    margin-bottom: 24px;
    page-break-inside: avoid;
    break-inside: avoid;
  }}

  .section-heading {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
  }}

  .country-pill {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 14px 5px 10px;
    border-radius: 40px;
    font-size: 15px;
    font-weight: 600;
    color: #fff;
    white-space: nowrap;
  }}

  .country-flag {{
    font-size: 20px;
  }}

  .section-divider {{
    flex: 1;
    height: 1px;
    background: var(--border);
  }}

  /* ── TABLE ── */
  .offer-table {{
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    border-radius: 14px;
    overflow: hidden;
    border: 1px solid var(--border);
    background: #fff;
    page-break-inside: avoid;
    break-inside: avoid;
  }}

  .offer-table thead tr {{
    background: var(--dark);
  }}
  .offer-table thead th {{
    padding: 8px 10px;
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.6);
    text-align: left;
  }}
  .offer-table thead th:last-child {{ text-align: right; }}
  .offer-table thead th.center {{ text-align: center; }}

  .offer-table tbody tr {{
    border-top: 1px solid var(--border);
  }}

  .offer-table tbody td {{
    padding: 8px 10px;
    font-size: 12px;
    color: var(--text);
    vertical-align: middle;
    border-top: 1px solid var(--border);
  }}
  .offer-table tbody td:last-child {{ text-align: right; }}
  .offer-table tbody td.center {{ text-align: center; }}

  .row-label {{
    font-weight: 500;
    line-height: 1.4;
  }}
  .row-sub {{
    font-size: 10px;
    color: var(--muted);
    margin-top: 2px;
    font-weight: 400;
  }}

  .badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 20px;
    font-size: 10px;
    font-weight: 600;
  }}
  .badge-wave {{ background: #EAF5FF; color: #4B9EE8; }}
  .badge-baseline {{ background: #E8FBF7; color: #1BA888; }}
  .badge-adhoc {{ background: #FFF4E5; color: #D48806; }}
  .badge-omnibus {{ background: #F3F0FF; color: #7C5CBF; }}

  .loi-tag {{
    background: #F3F0FF;
    color: #7C5CBF;
    padding: 2px 7px;
    border-radius: 10px;
    font-size: 10px;
    font-weight: 600;
    white-space: nowrap;
  }}

  .cpi-val {{
    font-weight: 600;
    color: var(--mid);
  }}

  .cost-val {{
    font-size: 13px;
    font-weight: 700;
    color: var(--dark);
  }}

  .desc-cell {{
    font-size: 12px;
    color: var(--muted);
    line-height: 1.4;
    max-width: 200px;
  }}

  .n-val {{
    font-weight: 700;
    color: var(--mid);
    font-size: 12px;
  }}

  /* ── TARGET BAR ── */
  .target-bar {{
    display: flex;
    flex-wrap: wrap;
    gap: 4px 12px;
    background: var(--dark);
    border-radius: 8px;
    padding: 8px 14px;
    margin-bottom: 8px;
  }}
  .target-title {{
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #fff;
    font-weight: 700;
    margin-right: 12px;
    padding-right: 14px;
    border-right: 2px solid rgba(255,255,255,0.15);
    white-space: nowrap;
  }}
  .target-item {{
    display: flex;
    align-items: center;
    gap: 6px;
  }}
  .target-label {{
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--teal);
    font-weight: 700;
  }}
  .target-value {{
    font-size: 10px;
    color: rgba(255,255,255,0.7);
    font-weight: 500;
  }}
  .target-item + .target-item::before {{
    content: '\u00b7';
    color: rgba(255,255,255,0.25);
    font-size: 16px;
    margin-right: 8px;
  }}

  /* ── TOTAL ROW ── */
  .total-row td {{
    background: var(--dark);
    padding: 10px 10px;
    border-top: 2px solid var(--teal);
  }}
  .total-label {{
    text-align: right !important;
    font-size: 11px;
    font-weight: 700;
    color: #FFFFFF;
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }}
  .total-val {{
    text-align: right !important;
    font-size: 16px;
    font-weight: 800;
    color: #FFFFFF;
    letter-spacing: 0.02em;
  }}

  /* ── NOTES ── */
  .notes-block {{
    background: var(--dark);
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 16px;
  }}
  .notes-title {{
    font-size: 14px;
    color: #fff;
    margin-bottom: 10px;
    font-weight: 700;
    padding-left: 14px;
    border-left: 4px solid var(--teal);
  }}
  .notes-list {{
    list-style: none;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px 32px;
  }}
  .notes-list li {{
    font-size: 10px;
    color: rgba(255,255,255,0.65);
    padding-left: 16px;
    position: relative;
    line-height: 1.5;
  }}
  .notes-list li::before {{
    content: '\u2192';
    position: absolute;
    left: 0;
    color: var(--teal);
    font-size: 12px;
  }}

  /* ── VALIDITY ── */
  .validity-strip {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: linear-gradient(135deg, #EAF9F5, #EAF0FF);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 10px 18px;
  }}
  .validity-strip .v-left {{
    font-size: 11px;
    color: var(--muted);
  }}
  .validity-strip .v-left strong {{ color: var(--text); font-size: 12px; }}
  .validity-strip .v-right {{
    font-size: 11px;
    color: var(--muted);
    text-align: right;
  }}
  .validity-strip .v-right strong {{ color: var(--text); font-size: 12px; display: block; }}
</style>
</head>
<body>

<!-- HEADER -->
<div class="header">
  <div class="header-inner">
    <div class="logo-block">
      {logo_html}
      <div class="logo-text">
        <strong>UBO Consulting</strong>
      </div>
    </div>
    <div class="header-right">
      <div class="header-title">Financial <em>Offer</em></div>
      <div class="header-sub">{sub_header_text}</div>
    </div>
  </div>
</div>
<div class="accent-bar"></div>

<!-- MAIN -->
<div class="main">

  <!-- META -->
  <div class="meta-grid">
    <div class="meta-cell">
      <div class="meta-label">Contact</div>
      <div class="meta-value">{contact}</div>
    </div>
    <div class="meta-cell">
      <div class="meta-label">Date</div>
      <div class="meta-value">{date_str}</div>
    </div>
    <div class="meta-cell">
      <div class="meta-label">Proposal No.</div>
      <div class="meta-value">{proposal_no}</div>
    </div>
    <div class="meta-cell">
      <div class="meta-label">Currency</div>
      <div class="meta-value">Euro (EUR)</div>
    </div>
  </div>

  {countries_html}

  <!-- VALIDITY -->
  <div class="validity-strip">
    <div class="v-left">
      <strong>Field Timing</strong><br>
      {field_info}
    </div>
    <div class="v-right">
      <strong>Offer valid until {valid_until}</strong>
      30 days from quotation date
    </div>
  </div>

</div>

<!-- PAGE 2: TERMS AND CONDITIONS -->
<div style="page-break-before: always;"></div>
<div class="header">
  <div class="header-inner">
    <div class="logo-block">
      {logo_html}
      <div class="logo-text">
        <strong>UBO Consulting</strong>
      </div>
    </div>
    <div class="header-right">
      <div class="header-title">Financial <em>Offer</em></div>
      <div class="header-sub">{sub_header_text}</div>
    </div>
  </div>
</div>
<div class="accent-bar"></div>

<div class="main">
  <div class="notes-block">
    <div class="notes-title">Terms and Conditions</div>
    <ul class="notes-list" style="grid-template-columns: 1fr;">
      {tc_lis}
    </ul>
  </div>

  {additional_html}
</div>

</body>
</html>"""

    return html


# ══════════════════════════════════════════════════════════════════════════════
# STREAMLIT UI
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(page_title="Financial Offer Generator", layout="wide")

st.markdown("""
<style>
h1  { color: #1A1A2E; }
h2  { color: #2E3250; }
.block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

st.title("Financial Offer Generator")
st.caption("Fill in the fields below and click **Generate** to download your offer.")

# ── Client & Meta ─────────────────────────────────────────────────────────────
st.subheader("Client & Offer Details")
mc1, mc2, mc3 = st.columns(3)
with mc1:
    client = st.text_input("Client *", placeholder="e.g. Acme Corporation")
with mc2:
    EMPLOYEES = [
        "Jehona Karavidaj", "Emblema Zekaj", "Albana Zejnullahu",
        "Kujtim Koci", "Hana Bacaj", "Sonila Hasaj",
        "Shkurte Makolli", "Eneida Aliu",
    ]
    contact = st.selectbox("Contact Person *", options=[""] + EMPLOYEES)
with mc3:
    proposal_no = st.text_input("Proposal No.", placeholder="e.g. 56145061")

st.divider()

# ── Countries ─────────────────────────────────────────────────────────────────
st.subheader("Countries")
selected_countries = st.multiselect(
    "Select countries (one pricing table per country)",
    options=BALKAN_COUNTRIES, default=[],
)

st.divider()

# ── Study Details ─────────────────────────────────────────────────────────────
st.subheader("Study Details")
st.caption(
    "Each row is one study. Set **Study Name**, **Type**, **LOI range**, **IR**, **N**, "
    "and **CPI** per country. **COST = N \u00d7 CPI** is calculated automatically."
)

_DEFAULT_ROW = {
    "Study Name": "",
    "Study Description": "",
    "LOI From":   15,
    "LOI To":     20,
    "IR (%)":     90,
    "N":          1000,
}

def _empty_row():
    return {**_DEFAULT_ROW,
            **{f"CPI \u2013 {c} (\u20ac)": 0.0 for c in selected_countries}}

_SCHEMA_VERSION = 5

# Only rebuild when countries change (add/remove CPI columns)
_countries_changed = set(st.session_state.get("study_countries", [])) != set(selected_countries)
_needs_init = "studies_df" not in st.session_state
_schema_changed = st.session_state.get("schema_version") != _SCHEMA_VERSION

if _needs_init or _schema_changed or _countries_changed:
    prev = st.session_state.get("studies_df", None)
    rows = []
    if prev is not None and len(prev) > 0:
        for _, r in prev.iterrows():
            row = {
                "Study Name": str(r.get("Study Name",
                    r.get("Description", r.get("Study Type", "")))),
                "Study Description": str(r.get("Study Description", "")),
                "LOI From":   int(r.get("LOI From", 15)),
                "LOI To":     int(r.get("LOI To", 20)),
                "IR (%)":     float(r.get("IR (%)", 90)),
                "N":          int(r.get("N", 1000)),
            }
            for c in selected_countries:
                col = f"CPI \u2013 {c} (\u20ac)"
                row[col] = float(r.get(col, 0.0) or 0.0)
            rows.append(row)
    if not rows:
        rows = [_empty_row()]
    st.session_state.studies_df      = pd.DataFrame(rows)
    st.session_state.study_countries = list(selected_countries)
    st.session_state.schema_version  = _SCHEMA_VERSION
    st.session_state.pop("studies_editor", None)

col_cfg = {
    "Study Name": st.column_config.TextColumn(
        "Study Name", required=True, width="large"),
    "Study Description": st.column_config.TextColumn(
        "Study Description", required=False, width="large",
        help="Optional detail shown in the offer, e.g. Per wave \u00b7 3-month exclusion"),
    "LOI From": st.column_config.NumberColumn(
        "LOI (min)", min_value=1, max_value=120, step=1, required=True),
    "LOI To": st.column_config.NumberColumn(
        "LOI (max)", min_value=1, max_value=120, step=1, required=True),
    "IR (%)": st.column_config.NumberColumn(
        "IR (%)", min_value=1, max_value=100, step=1, required=True),
    "N": st.column_config.NumberColumn(
        "N", min_value=10, max_value=50000, step=1, required=True),
}
for c in selected_countries:
    col_cfg[f"CPI \u2013 {c} (\u20ac)"] = st.column_config.NumberColumn(
        f"CPI {c} (\u20ac)", min_value=0.0, step=0.01, format="%.2f")

def _on_editor_change():
    """Callback: sync editor widget state back to studies_df immediately."""
    editor_state = st.session_state.get("studies_editor")
    if editor_state is not None:
        df = st.session_state.studies_df.copy()
        # Apply edited rows
        for row_idx_str, changes in (editor_state.get("edited_rows") or {}).items():
            row_idx = int(row_idx_str)
            if row_idx < len(df):
                for col, val in changes.items():
                    if col in df.columns:
                        df.at[row_idx, col] = val
        # Apply added rows
        for added in (editor_state.get("added_rows") or []):
            if any(v for v in added.values()):
                new = {c: _DEFAULT_ROW.get(c, 0.0) for c in df.columns}
                new.update(added)
                df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
        # Apply deleted rows
        for idx in sorted(editor_state.get("deleted_rows") or [], reverse=True):
            if idx < len(df):
                df = df.drop(index=idx).reset_index(drop=True)
        st.session_state.studies_df = df

edited_df = st.data_editor(
    st.session_state.studies_df,
    column_config=col_cfg,
    num_rows="dynamic",
    use_container_width=True,
    key="studies_editor",
    on_change=_on_editor_change,
)
st.session_state.studies_df = edited_df.copy()

if st.button("\uff0b Add Study"):
    new_row = pd.DataFrame([_empty_row()])
    st.session_state.studies_df = pd.concat(
        [edited_df, new_row], ignore_index=True)
    st.session_state.pop("studies_editor", None)
    st.rerun()

st.divider()

# ── Target / Quotas ───────────────────────────────────────────────────────────
st.subheader("Target")
st.caption("Select target variables for quotas. Configure each selected variable below.")

ALL_QUOTA_VARS = ["Gender", "Age", "Region", "Income", "Education"]
selected_quotas = st.multiselect(
    "Quota variables",
    options=ALL_QUOTA_VARS,
    default=[],
    help="Select one or more variables to set quotas on.",
)

quotas = {}
active_quota_vars = []

if "Gender" in selected_quotas:
    st.markdown("**Target: Gender**")
    gvals = st.multiselect(
        "Gender values", ["Male", "Female"],
        default=["Male", "Female"], key="q_gender")
    if gvals:
        quotas["gender"] = gvals
        active_quota_vars.append("Gender")

if "Age" in selected_quotas:
    st.markdown("**Target: Age**")
    ac1, ac2 = st.columns(2)
    age_min = ac1.number_input("Min age", 0, 100, 18, key="age_min")
    age_max = ac2.number_input("Max age", 0, 100, 65, key="age_max")
    quotas["age"] = f"{age_min}\u2013{age_max}"
    active_quota_vars.append("Age")

if "Region" in selected_quotas:
    st.markdown("**Target: Region**")
    sel_regions = st.multiselect(
        "Select regions", options=KOSOVO_REGIONS,
        default=KOSOVO_REGIONS, key="q_region")
    if sel_regions:
        quotas["region"] = sel_regions
        active_quota_vars.append("Region")

if "Income" in selected_quotas:
    st.markdown("**Target: Income**")
    income_val = st.text_input(
        "Income brackets",
        placeholder="e.g. Low, Medium, High or specific ranges",
        key="q_income")
    if income_val.strip():
        quotas["income"] = income_val.strip()
        active_quota_vars.append("Income")

if "Education" in selected_quotas:
    st.markdown("**Target: Education**")
    education_val = st.text_input(
        "Education levels",
        placeholder="e.g. Primary, Secondary, University",
        key="q_education")
    if education_val.strip():
        quotas["education"] = education_val.strip()
        active_quota_vars.append("Education")

st.divider()

# ── Quotas ────────────────────────────────────────────────────────────────────
st.subheader("Quotas")
st.caption("Select which variables will have quotas set in this study.")

ALL_QUOTAS_OPTIONS = ["Gender", "Age", "Region", "Income", "Education"]
selected_quota_vars = st.multiselect(
    "Quota variables",
    options=ALL_QUOTAS_OPTIONS,
    default=[],
    key="quota_vars",
)
quotas["quota_vars"] = selected_quota_vars

# Nested quotas — under Quotas, using active target vars
quotas["nested"] = []
if len(active_quota_vars) >= 2:
    st.markdown("")
    use_nested = st.checkbox(
        "Nested quotas",
        help="Interlock two or more quota variables. At least 2 must be selected.",
    )
    if use_nested:
        nested_vars = st.multiselect(
            "Variables included in nested quota *(min. 2)*",
            options=active_quota_vars, default=active_quota_vars)
        if len(nested_vars) >= 2:
            quotas["nested"] = nested_vars
        else:
            st.warning("Select at least 2 variables to form a nested quota.")

st.divider()

# ── Field Details ─────────────────────────────────────────────────────────────
st.subheader("Field Details")
fc1, fc2 = st.columns(2)

with fc1:
    st.markdown("**Field Timing**")
    tc1, tc2 = st.columns(2)
    field_month = tc1.selectbox("Month", [""] + MONTHS, label_visibility="collapsed")
    field_year  = tc2.selectbox("Year",  [""] + list(range(2024, 2031)),
                                label_visibility="collapsed")
    field_timing = f"{field_month} {field_year}".strip()

with fc2:
    st.markdown("**Devices Allowed**")
    devices = st.multiselect(
        "Devices",
        ["Laptop", "PC", "Tablet", "Phone"],
        default=["Laptop", "PC", "Tablet", "Phone"],
        label_visibility="collapsed",
    )

st.divider()

# ── Additional Details ────────────────────────────────────────────────────────
st.subheader("Additional Details")
additional = st.text_area(
    "Any extra notes or requirements", height=80,
    placeholder="Enter any extra notes or requirements for this offer\u2026")

st.divider()

# ── Terms & Conditions ────────────────────────────────────────────────────────
st.subheader("Terms & Conditions")
st.caption("Edit the terms shown on the second page of the offer. One bullet point per line.")

_TC_DEFAULT = (
    "All prices are quoted in Euro (EUR). Final costs will be based on actual delivered metrics (N, IR, LOI).\n"
    "Survey accessibility: assumed to be compatible with all devices unless otherwise specified.\n"
    "Minimum engagement fee: \u20ac720 per country (ad hoc projects).\n"
    "Minimum engagement fee: \u20ac720 per country per month/wave (tracking projects).\n"
    "Screenouts and quota fulls after the 10th survey question: \u20ac1.50 per respondent.\n"
    "Screenouts and quota fulls after the 20th survey question: \u20ac2.50 per respondent."
)
tc_text = st.text_area("Terms & Conditions", value=_TC_DEFAULT, height=200)

st.divider()

# ── Logo notice ───────────────────────────────────────────────────────────────
if not os.path.exists(LOGO_PATH):
    st.info(
        "**Logo not found.** Place `UBO Logo.png` in the `financial_offer_tool` folder.",
        icon="\U0001f5bc\ufe0f",
    )

# ── Validation & generate ─────────────────────────────────────────────────────
errors = []
if not client.strip():
    errors.append("Client is required.")
if not contact.strip():
    errors.append("Contact person is required.")
if not selected_countries:
    errors.append("Select at least one country.")
if edited_df is None or len(edited_df) == 0:
    errors.append("Add at least one study.")
elif edited_df["Study Name"].astype(str).str.strip().eq("").any():
    errors.append("Every study must have a name.")

if edited_df is not None and len(edited_df) > 0:
    bad_loi = edited_df[edited_df["LOI To"].astype(int) < edited_df["LOI From"].astype(int)]
    if len(bad_loi) > 0:
        errors.append("LOI To must be \u2265 LOI From for every study.")

for e in errors:
    st.warning(e)

gen_clicked = st.button(
    "Generate Offer", type="primary",
    disabled=bool(errors), use_container_width=False)

if gen_clicked:
    with st.spinner("Building offer\u2026"):
        html_str = build_html(
            client       = client.strip(),
            contact      = contact.strip(),
            proposal_no  = proposal_no.strip() or "\u2014",
            studies_df   = st.session_state.studies_df,
            countries    = selected_countries,
            quotas       = quotas,
            field_timing = field_timing,
            tc_text      = tc_text,
            additional   = additional,
        )

        # Generate PDF — try Edge (local Windows) first, then WeasyPrint (Linux/cloud)
        html_bytes = html_str.encode("utf-8")
        pdf_bytes = None

        edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        if os.path.exists(edge_path):
            try:
                with tempfile.TemporaryDirectory() as tmp:
                    html_path = os.path.join(tmp, "offer.html")
                    pdf_path  = os.path.join(tmp, "offer.pdf")
                    with open(html_path, "w", encoding="utf-8") as f:
                        f.write(html_str)
                    subprocess.run(
                        [edge_path, "--headless", "--disable-gpu",
                         f"--print-to-pdf={pdf_path}",
                         "--no-pdf-header-footer",
                         html_path],
                        capture_output=True, timeout=30,
                    )
                    if os.path.exists(pdf_path):
                        with open(pdf_path, "rb") as pf:
                            pdf_bytes = pf.read()
            except Exception as exc:
                st.warning(f"Edge PDF generation failed: {exc}. Trying WeasyPrint…")

        if pdf_bytes is None:
            try:
                from weasyprint import HTML
                pdf_bytes = HTML(string=html_str).write_pdf()
            except Exception as exc:
                st.warning(f"PDF generation failed: {exc}. You can still download HTML.")

    cl = client.strip().replace(" ", "_")[:40]

    st.success("Offer ready! Download below.")

    dl1, dl2 = st.columns(2)
    with dl1:
        if pdf_bytes:
            st.download_button(
                label="\U0001f4c4 Download PDF",
                data=pdf_bytes,
                file_name=f"Financial_Offer_{cl}.pdf",
                mime="application/pdf",
            )
    with dl2:
        st.download_button(
            label="\U0001f310 Download HTML",
            data=html_bytes,
            file_name=f"Financial_Offer_{cl}.html",
            mime="text/html",
        )
