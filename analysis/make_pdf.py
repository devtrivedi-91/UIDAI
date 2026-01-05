from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import os

BASE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(BASE, 'outputs')
PDF_PATH = os.path.join(OUTDIR, 'Aadhaar_analytics_report.pdf')

styles = getSampleStyleSheet()
if 'Justify' not in styles:
    styles.add(ParagraphStyle(name='Justify', alignment=4))
if 'SectionHeading' not in styles:
    styles.add(ParagraphStyle(name='SectionHeading', fontSize=14, leading=16, spaceAfter=8, spaceBefore=12))
if 'Code' not in styles:
    styles.add(ParagraphStyle(name='Code', fontName='Courier', fontSize=8))

# Exact executive summary paragraph requested
EXEC_SUMMARY = ("States such as Uttar Pradesh and Maharashtra consistently generate the highest Aadhaar update volumes across both demographic and biometric datasets, "
               "indicating persistent service demand that warrants additional update centers or temporary camps. Within Gujarat, Ahmedabad and Surat dominate district-level "
               "update requests, pointing to urban concentration and frequent address or mobile changes. Short-term forecasts (12-week horizon) show continued elevated demand "
               "in these regions; operational actions — targeted mobile camps, temporary staffing increases during forecasted peak weeks, and biometric quality revalidation programs "
               "— will mitigate service delays and improve efficiency.")

# Files to embed
IMG_STATE_DEMO = os.path.join(OUTDIR, 'state_demographic_top10.png')
IMG_STATE_BIO = os.path.join(OUTDIR, 'state_biometric_top10.png')
IMG_GUJ_DEMO = os.path.join(OUTDIR, 'gujarat_demographic_top15.png')
IMG_GUJ_BIO = os.path.join(OUTDIR, 'gujarat_biometric_top15.png')
FORECAST_CSV = os.path.join(OUTDIR, 'forecasts', 'state_Uttar_Pradesh_forecast.csv')


def read_csv_preview(path, max_lines=200):
    if not os.path.exists(path):
        return 'Forecast CSV not found: ' + path
    with open(path, 'r') as f:
        lines = f.readlines()
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines.append('\n... (truncated)')
    return ''.join(lines)


def build():
    doc = SimpleDocTemplate(PDF_PATH, pagesize=A4,
                            rightMargin=36, leftMargin=36,
                            topMargin=36, bottomMargin=36)
    story = []

    # Cover page
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph('Aadhaar Data Hackathon — Analysis & Deliverables', styles['Title']))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph('Identifying Regional and Age‑Group Patterns in Aadhaar Updates to Improve Service Delivery Efficiency', styles['Normal']))
    story.append(Spacer(1, 0.4 * inch))
    story.append(Paragraph('Author: Dev Trivedi', styles['Normal']))
    story.append(Spacer(1, 0.05 * inch))
    story.append(Paragraph('Date: 05 January 2026', styles['Normal']))
    story.append(PageBreak())

    # Executive summary
    story.append(Paragraph('Executive summary', styles['SectionHeading']))
    story.append(Paragraph(EXEC_SUMMARY, styles['Justify']))
    story.append(PageBreak())

    # Problem statement
    story.append(Paragraph('Problem Statement', styles['SectionHeading']))
    story.append(Paragraph('Identifying Regional and Age‑Group Patterns in Aadhaar Updates to Improve Service Delivery Efficiency', styles['Heading4']))
    story.append(Paragraph('<b>Why Aadhaar update demand matters</b>', styles['Normal']))
    story.append(Paragraph('Aadhaar update volumes indicate where citizens are seeking changes (address, mobile, DOB, gender) and where services are in demand. High update demand can create service bottlenecks and delays that affect citizen experience.', styles['Justify']))
    story.append(Paragraph('<b>How regional and age‑based patterns affect service load</b>', styles['Normal']))
    story.append(Paragraph('Regions with concentrated updates require more operational capacity. Age transitions and biometric revalidations create predictable demand spikes.', styles['Justify']))
    story.append(Paragraph('<b>Why data‑driven insights help UIDAI optimize resources</b>', styles['Normal']))
    story.append(Paragraph('Quantitative insights enable targeted allocation of staff and mobile units, informed timing for outreach campaigns, and prioritization of infrastructure scaling in high‑load districts.', styles['Justify']))
    story.append(PageBreak())

    # Datasets
    story.append(Paragraph('Datasets Used', styles['SectionHeading']))
    story.append(Paragraph('<b>Primary dataset</b>: Aadhaar Demographic Update Dataset', styles['Normal']))
    story.append(Paragraph('Focuses on updates (not enrolments). Includes region (state/district/PIN) and time data; supports service demand analysis.', styles['Normal']))
    story.append(Spacer(1, 6))
    story.append(Paragraph('<b>Secondary dataset (bonus)</b>: Aadhaar Biometric Update Dataset', styles['Normal']))
    story.append(Paragraph('Captures biometric revalidation trends; useful for age‑group service demand analysis.', styles['Normal']))
    story.append(Spacer(1, 6))
    story.append(Paragraph('<b>Optional context</b>: Aadhaar Enrolment Dataset (used for context only)', styles['Normal']))
    story.append(PageBreak())

    # Methodology
    story.append(Paragraph('Methodology', styles['SectionHeading']))
    story.append(Paragraph('Raw CSVs explored from `api_data_aadhar_demographic/` and `api_data_aadhar_biometric/`.', styles['Normal']))
    story.append(Paragraph('Analytics pipeline implemented in `analysis/analytics.py`.', styles['Normal']))
    story.append(Paragraph('Script steps:', styles['Normal']))
    bullet_texts = [
        'Reads CSVs in chunks',
        'Normalizes column names',
        'Aggregates totals by state and district',
        'Generates charts and CSV summaries',
        'Resamples data weekly',
        'Applies Holt–Winters forecasting (12-week horizon)',
        'Saves outputs in `analysis/outputs/`'
    ]
    for b in bullet_texts:
        story.append(Paragraph('• ' + b, styles['Normal']))
    story.append(PageBreak())

    # State-level analysis
    story.append(Paragraph('State‑level analysis', styles['SectionHeading']))
    if os.path.exists(IMG_STATE_DEMO):
        story.append(Image(IMG_STATE_DEMO, width=6.5*inch, height=3.6*inch))
        story.append(Paragraph('Figure: Top states by demographic updates (see analysis/outputs/state_demographic_top10.png)', styles['Normal']))
    else:
        story.append(Paragraph('Figure missing: ' + IMG_STATE_DEMO, styles['Normal']))
    story.append(Spacer(1, 6))
    story.append(Paragraph('Explanation: Top states by demographic updates; regions with highest update volumes (e.g., Uttar Pradesh, Maharashtra) indicate priority need for resource allocation and service scaling.', styles['Justify']))
    story.append(Spacer(1, 12))
    if os.path.exists(IMG_STATE_BIO):
        story.append(Image(IMG_STATE_BIO, width=6.5*inch, height=3.6*inch))
        story.append(Paragraph('Figure: Top states by biometric updates (see analysis/outputs/state_biometric_top10.png)', styles['Normal']))
    else:
        story.append(Paragraph('Figure missing: ' + IMG_STATE_BIO, styles['Normal']))
    story.append(Paragraph('Explanation: Biometric revalidation pressure; age‑transition and revalidation needs may be concentrated in the top states shown.', styles['Justify']))
    story.append(Spacer(1, 12))
    story.append(Paragraph('Relevant CSVs: `analysis/outputs/state_summary_demographic.csv`, `analysis/outputs/state_summary_biometric.csv`', styles['Normal']))
    story.append(PageBreak())

    # District level (Gujarat)
    story.append(Paragraph('District‑level analysis — Gujarat focus', styles['SectionHeading']))
    if os.path.exists(IMG_GUJ_DEMO):
        story.append(Image(IMG_GUJ_DEMO, width=6.5*inch, height=3.6*inch))
        story.append(Paragraph('Figure: Gujarat — top districts (demographic) (see analysis/outputs/gujarat_demographic_top15.png)', styles['Normal']))
    else:
        story.append(Paragraph('Figure missing: ' + IMG_GUJ_DEMO, styles['Normal']))
    story.append(Paragraph('Explanation: Urban concentration and migration-driven updates (Ahmedabad, Surat).', styles['Justify']))
    story.append(Spacer(1, 12))
    if os.path.exists(IMG_GUJ_BIO):
        story.append(Image(IMG_GUJ_BIO, width=6.5*inch, height=3.6*inch))
        story.append(Paragraph('Figure: Gujarat — top districts (biometric) (see analysis/outputs/gujarat_biometric_top15.png)', styles['Normal']))
    else:
        story.append(Paragraph('Figure missing: ' + IMG_GUJ_BIO, styles['Normal']))
    story.append(Paragraph('Relevant CSVs: `analysis/outputs/gujarat_demographic_by_district.csv`, `analysis/outputs/gujarat_biometric_by_district.csv`', styles['Normal']))
    story.append(PageBreak())

    # Forecasting
    story.append(Paragraph('Forecasting & Future Demand', styles['SectionHeading']))
    story.append(Paragraph('Forecasting approach:', styles['Normal']))
    story.append(Paragraph('• Weekly resampling', styles['Normal']))
    story.append(Paragraph('• Holt–Winters seasonal model', styles['Normal']))
    story.append(Paragraph('• 12‑week horizon', styles['Normal']))
    story.append(Spacer(1, 6))
    story.append(Paragraph('Example forecast CSV (preview): `analysis/outputs/forecasts/state_Uttar_Pradesh_forecast.csv`', styles['Normal']))
    csv_preview = read_csv_preview(FORECAST_CSV, max_lines=120)
    story.append(Preformatted(csv_preview, styles['Code']))
    story.append(Paragraph('Explanation: Continued elevated demand; forecasts support proactive planning but are trend-based.', styles['Justify']))
    story.append(PageBreak())

    # Key findings
    story.append(Paragraph('Key Findings', styles['SectionHeading']))
    findings = [
        'Uttar Pradesh & Maharashtra show sustained highest update volumes',
        'Ahmedabad & Surat dominate Gujarat updates',
        'High biometric update counts indicate age-related revalidation needs'
    ]
    for f in findings:
        story.append(Paragraph('• ' + f, styles['Normal']))
    story.append(PageBreak())

    # Recommendations
    story.append(Paragraph('Recommendations', styles['SectionHeading']))
    recs = [
        'Deploy temporary Aadhaar update camps in high-load districts',
        'Increase staffing during forecasted peak weeks',
        'Run biometric quality & revalidation awareness programs',
        'Prioritize urban districts for infrastructure scaling'
    ]
    for r in recs:
        story.append(Paragraph('• ' + r, styles['Normal']))
    story.append(PageBreak())

    # Limitations
    story.append(Paragraph('Limitations', styles['SectionHeading']))
    story.append(Paragraph('• Update-type breakdown (address/mobile/DOB/gender) unavailable due to dataset header limitations', styles['Normal']))
    story.append(Paragraph('• Forecasts are short-term and trend-based', styles['Normal']))
    story.append(Paragraph('• External covariates not included', styles['Normal']))
    story.append(PageBreak())

    # Reproducibility
    story.append(Paragraph('Reproducibility', styles['SectionHeading']))
    reproduc_cmds = ("python3 -m venv .venv\nsource .venv/bin/activate\npip install -r analysis/requirements.txt\npython analysis/analytics.py\npython analysis/make_presentation.py")
    story.append(Preformatted(reproduc_cmds, styles['Code']))
    story.append(PageBreak())

    # Deliverables
    story.append(Paragraph('Deliverables', styles['SectionHeading']))
    deliver = [
        'analytics_report.md',
        'Generated charts (PNG)',
        'Forecast CSVs & PNGs',
        'Aggregated CSV summaries',
        'PPT (Aadhaar_analytics_presentation.pptx)'
    ]
    for d in deliver:
        story.append(Paragraph('• ' + d, styles['Normal']))
    story.append(PageBreak())

    # Conclusion
    story.append(Paragraph('Conclusion', styles['SectionHeading']))
    story.append(Paragraph('Data-driven planning and short-term forecasting enable targeted operational responses that improve service delivery and citizen experience.', styles['Justify']))

    doc.build(story)
    print('PDF written to', PDF_PATH)


if __name__ == '__main__':
    build()
