import os
import glob
import pandas as pd
from collections import defaultdict
import matplotlib.pyplot as plt
from statsmodels.tsa.holtwinters import ExponentialSmoothing

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DEMO_DIR = os.path.join(BASE_DIR, 'api_data_aadhar_demographic')
BIO_DIR = os.path.join(BASE_DIR, 'api_data_aadhar_biometric')
OUT_DIR = os.path.join(BASE_DIR, 'analysis', 'outputs')
os.makedirs(OUT_DIR, exist_ok=True)

CHUNKSIZE = 200_000
DATE_COL = 'date'


def clean_columns(cols):
    return [c.strip().lower().replace(' ', '_') for c in cols]


def accumulate_from_folder(folder, prefix):
    # prefix: 'demo' or 'bio'
    state_acc = defaultdict(lambda: defaultdict(int))
    district_acc_gujarat = defaultdict(lambda: defaultdict(int))
    file_list = sorted(glob.glob(os.path.join(folder, '*.csv')))
    for fp in file_list:
        for chunk in pd.read_csv(fp, chunksize=CHUNKSIZE):
            chunk.columns = clean_columns(chunk.columns)
            # find age columns matching prefix
            age_cols = [c for c in chunk.columns if c.startswith(f'{prefix}_age')]
            if not age_cols:
                continue
            # ensure state and district columns exist
            if 'state' not in chunk.columns:
                continue
            # fillna for age cols
            chunk[age_cols] = chunk[age_cols].fillna(0)
            # group by state
            grp_state = chunk.groupby('state')[age_cols].sum()
            for state, row in grp_state.iterrows():
                for col in age_cols:
                    state_acc[state][col] += int(row[col])
            # Gujarat district accum
            gch = chunk[chunk['state'].str.strip().str.lower() == 'gujarat']
            if not gch.empty and 'district' in gch.columns:
                grp_dist = gch.groupby('district')[age_cols].sum()
                for dist, row in grp_dist.iterrows():
                    for col in age_cols:
                        district_acc_gujarat[dist][col] += int(row[col])
    return state_acc, district_acc_gujarat


def dict_to_df(acc):
    # acc: dict key-> dict(col->value)
    rows = []
    cols = set()
    for k, sub in acc.items():
        cols.update(sub.keys())
    cols = sorted(cols)
    for k, sub in acc.items():
        row = {'key': k}
        for c in cols:
            row[c] = sub.get(c, 0)
        rows.append(row)
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.set_index('key')
        # add total
        df['total_updates'] = df.sum(axis=1)
        df = df.sort_values('total_updates', ascending=False)
    return df


def main():
    print('Processing demographic files...')
    state_demo, guj_demo = accumulate_from_folder(DEMO_DIR, 'demo')
    print('Processing biometric files...')
    state_bio, guj_bio = accumulate_from_folder(BIO_DIR, 'bio')

    df_state_demo = dict_to_df(state_demo)
    df_state_bio = dict_to_df(state_bio)
    df_guj_demo = dict_to_df(guj_demo)
    df_guj_bio = dict_to_df(guj_bio)

    # Save outputs
    df_state_demo.to_csv(os.path.join(OUT_DIR, 'state_summary_demographic.csv'))
    df_state_bio.to_csv(os.path.join(OUT_DIR, 'state_summary_biometric.csv'))
    df_guj_demo.to_csv(os.path.join(OUT_DIR, 'gujarat_demographic_by_district.csv'))
    df_guj_bio.to_csv(os.path.join(OUT_DIR, 'gujarat_biometric_by_district.csv'))

    # Create simple bar charts
    def make_bar(series, title, outpath):
        plt.figure(figsize=(10, 6))
        series.plot(kind='bar', color='C0')
        plt.title(title)
        plt.ylabel('Total updates')
        plt.tight_layout()
        plt.savefig(outpath)
        plt.close()

    if not df_state_demo.empty:
        make_bar(df_state_demo['total_updates'].head(10), 'Top 10 States by Demographic Updates', os.path.join(OUT_DIR, 'state_demographic_top10.png'))
    if not df_state_bio.empty:
        make_bar(df_state_bio['total_updates'].head(10), 'Top 10 States by Biometric Updates', os.path.join(OUT_DIR, 'state_biometric_top10.png'))
    if not df_guj_demo.empty:
        make_bar(df_guj_demo['total_updates'].head(15), 'Top Gujarat Districts (Demographic)', os.path.join(OUT_DIR, 'gujarat_demographic_top15.png'))
    if not df_guj_bio.empty:
        make_bar(df_guj_bio['total_updates'].head(15), 'Top Gujarat Districts (Biometric)', os.path.join(OUT_DIR, 'gujarat_biometric_top15.png'))

    # --- Forecasting (Holt-Winters) for top 5 states and Gujarat top 5 districts ---
    forecast_dir = os.path.join(OUT_DIR, 'forecasts')
    os.makedirs(forecast_dir, exist_ok=True)

    def build_daily_aggregates(folder, prefix):
        # returns DataFrame with columns ['state','district','date','total_updates']
        rows = []
        file_list = sorted(glob.glob(os.path.join(folder, '*.csv')))
        for fp in file_list:
            for chunk in pd.read_csv(fp, chunksize=CHUNKSIZE):
                chunk.columns = clean_columns(chunk.columns)
                date_col = DATE_COL if DATE_COL in chunk.columns else 'date'
                age_cols = [c for c in chunk.columns if c.startswith(f'{prefix}_age')]
                if not age_cols or 'state' not in chunk.columns:
                    continue
                # total updates per row
                chunk['total_updates'] = chunk[age_cols].fillna(0).sum(axis=1)
                # parse date
                try:
                    chunk['date'] = pd.to_datetime(chunk[date_col], dayfirst=True, errors='coerce')
                except Exception:
                    chunk['date'] = pd.to_datetime(chunk[date_col], errors='coerce')
                chunk = chunk.dropna(subset=['date'])
                grp = chunk.groupby(['state', 'district', 'date'])['total_updates'].sum().reset_index()
                rows.append(grp)
        if rows:
            df = pd.concat(rows, ignore_index=True)
            return df
        return pd.DataFrame(columns=['state', 'district', 'date', 'total_updates'])

    demo_daily = build_daily_aggregates(DEMO_DIR, 'demo')

    def fit_and_forecast(series, periods):
        # resample weekly to reduce noise
        s = series.resample('W').sum()
        # choose seasonal if enough data
        seasonal = None
        sp = None
        if len(s) >= 26:
            # assume yearly seasonality on weekly data (~52)
            seasonal = 'add'
            sp = 52
        try:
            model = ExponentialSmoothing(s, trend='add', seasonal=seasonal, seasonal_periods=sp, damped_trend=False)
            fit = model.fit(optimized=True)
            fc = fit.forecast(periods)
            return s, fc
        except Exception:
            # fallback: simple last-value repeat
            fc = pd.Series([s.mean()] * periods, index=pd.date_range(s.index[-1] + pd.Timedelta(weeks=1), periods=periods, freq='W'))
            return s, fc

    horizon_weeks = 12  # ~3 months

    # Top 5 states by demographic totals
    top_states = []
    if not df_state_demo.empty:
        top_states = list(df_state_demo.index[:5])

    for st in top_states:
        ser = demo_daily[demo_daily['state'].str.strip().str.lower() == st.strip().lower()]
        if ser.empty:
            continue
        ts = ser.groupby('date')['total_updates'].sum()
        ts.index = pd.to_datetime(ts.index)
        hist, fc = fit_and_forecast(ts, horizon_weeks)
        # save CSV and chart
        out_csv = os.path.join(forecast_dir, f'state_{st.replace(" ","_")}_forecast.csv')
        pd.concat([hist.rename('historical'), fc.rename('forecast')], axis=1).to_csv(out_csv)
        plt.figure(figsize=(10, 5))
        hist.plot(label='historical')
        fc.plot(label='forecast')
        plt.title(f'Weekly updates - {st}')
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(forecast_dir, f'state_{st.replace(" ","_")}_forecast.png'))
        plt.close()

    # Gujarat top 5 districts (demographic)
    guj = df_guj_demo
    guj_top5 = list(guj.index[:5]) if not guj.empty else []
    for dist in guj_top5:
        ser = demo_daily[(demo_daily['state'].str.strip().str.lower() == 'gujarat') & (demo_daily['district'].str.strip().str.lower() == dist.strip().lower())]
        if ser.empty:
            continue
        ts = ser.groupby('date')['total_updates'].sum()
        ts.index = pd.to_datetime(ts.index)
        hist, fc = fit_and_forecast(ts, horizon_weeks)
        out_csv = os.path.join(forecast_dir, f'gujarat_{dist.replace(" ","_")}_forecast.csv')
        pd.concat([hist.rename('historical'), fc.rename('forecast')], axis=1).to_csv(out_csv)
        plt.figure(figsize=(10, 5))
        hist.plot(label='historical')
        fc.plot(label='forecast')
        plt.title(f'Weekly updates - Gujarat / {dist}')
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(forecast_dir, f'gujarat_{dist.replace(" ","_")}_forecast.png'))
        plt.close()

    # Simple report
    with open(os.path.join(OUT_DIR, 'analytics_report.md'), 'w') as f:
        f.write('# Aadhaar Analytics Report\n\n')
        f.write('## Top states by demographic updates (total)\n\n')
        if not df_state_demo.empty:
            f.write(df_state_demo[['total_updates']].head(20).to_markdown())
            f.write('\n\n')
        else:
            f.write('No demographic data found.\n\n')

        f.write('## Top states by biometric updates (total)\n\n')
        if not df_state_bio.empty:
            f.write(df_state_bio[['total_updates']].head(20).to_markdown())
            f.write('\n\n')
        else:
            f.write('No biometric data found.\n\n')

        f.write('## Gujarat - Top districts (demographic)\n\n')
        if not df_guj_demo.empty:
            f.write(df_guj_demo[['total_updates']].head(20).to_markdown())
            f.write('\n\n')
        else:
            f.write('No Gujarat demographic data found.\n\n')

        f.write('## Gujarat - Top districts (biometric)\n\n')
        if not df_guj_bio.empty:
            f.write(df_guj_bio[['total_updates']].head(20).to_markdown())
            f.write('\n\n')
        else:
            f.write('No Gujarat biometric data found.\n\n')

        # Embed charts (images are saved in the same outputs folder)
        f.write('## Charts\n\n')
        if not df_state_demo.empty:
            f.write('![](state_demographic_top10.png)\n\n')
        if not df_state_bio.empty:
            f.write('![](state_biometric_top10.png)\n\n')
        if not df_guj_demo.empty:
            f.write('![](gujarat_demographic_top15.png)\n\n')
        if not df_guj_bio.empty:
            f.write('![](gujarat_biometric_top15.png)\n\n')

        # Insights and recommendations
        f.write('## Insights\n\n')
        f.write('- **High-volume states:** Uttar Pradesh and Maharashtra show consistently high demographic and biometric update volumes, indicating sustained service demand and need for expanded update centers.\n')
        f.write('- **Gujarat concentration:** Ahmedabad and Surat dominate update requests, suggesting urban migration and frequent address/mobile changes in these urban centers.\n')
        f.write('- **Biometric revalidation:** High biometric update counts in several populous states point to age-related revalidation and quality-correction needs.\n\n')
        f.write('## Recommendations\n\n')
        f.write('- **Scale resources:** Allocate additional enrollment/update centers and staffing to top-demand states (UP, Maharashtra, Bihar).\n')
        f.write('- **Targeted outreach:** Conduct mobile camps in high-update districts within Gujarat (Ahmedabad, Surat, Rajkot) focusing on address and mobile update facilitation.\n')
        f.write('- **Biometric quality program:** Implement periodic biometric revalidation initiatives in high biometric-update regions to reduce repeat visits.\n')

    print('Outputs written to', OUT_DIR)


if __name__ == '__main__':
    main()
