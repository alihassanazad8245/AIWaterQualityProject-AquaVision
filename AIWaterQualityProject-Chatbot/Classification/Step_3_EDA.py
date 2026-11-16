"""
Step_3_EDA.py

Performs comprehensive Exploratory Data Analysis (EDA)
on the water quality dataset after Step 2 WQI pipeline.

Sections:
    1.  Statistical summary
    2.  Parameter distributions (histograms)
    3.  Boxplots — outlier detection
    4.  WHO guideline exceedance analysis
    5.  Correlation heatmap
    6.  Province-wise parameter analysis
    7.  Resource type analysis
    8.  WQI category analysis
    9.  Parameter vs WQI relationships
    10. Year-wise trend analysis
    11. Outlier count analysis
    12. Microbial status analysis      ← new (Step 2 Microbial_Status)
    13. Risk assessment analysis       ← new (Step 2 Risk_Score / Risk_Category)

WQI Categories (Heliyon 2023 / WHO):
    0  – 50  : Excellent
    51 – 100 : Good
    101 – 200: Poor
    201 – 300: Very Poor
    > 300    : Unsuitable for drinking
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import os
import matplotlib as mpl

class EDA:
    """
    Performs full exploratory data analysis on the
    water quality dataset and saves all plots.

    Attributes:
        df         (DataFrame) : Input DataFrame with WQI results from Step 2
        output_dir (str)       : Folder to save EDA plots
    """

    # ── WHO standard limits — consistent with Step 2 ─────────────
    WHO_LIMITS = {
        'pH':               8.5,    # upper bound (range: 6.5–8.5)
        'Turbidity (NTU)':  5.0,
        'TDS (mg/L)':       1000.0, # WHO limit (matches Step 2)
        'Hardness (mg/L)':  500.0,
        'Calcium (mg/L)':   75.0,
        'Magnesium (mg/L)': 50.0,
        'Sodium (mg/L)':    200.0,
        'Potassium (mg/L)': 12.0,
        'Chloride (mg/L)':  250.0,
        'Sulfate (mg/L)':   250.0,
        'Nitrate (mg/L)':   50.0,   # WHO limit — corrected from 10.0
        'Fluoride (mg/L)':  1.5,
        'Iron (mg/L)':      0.3,
        'Arsenic (mg/L)':   0.01,
    }

    PARAMETER_COLS = list(WHO_LIMITS.keys())

    # ── WQI category order and colors (Heliyon 2023 / WHO) ────────
    CATEGORY_ORDER = [
        'Excellent',
        'Good',
        'Poor',
        'Very Poor',
        'Unsuitable for drinking',
    ]

    CATEGORY_COLORS = {
        'Excellent':              'green',
        'Good':                   'blue',
        'Poor':                   'orange',
        'Very Poor':              'red',
        'Unsuitable for drinking':'purple',
    }

    # ── WQI threshold lines used across all plots ─────────────────
    WQI_THRESHOLDS = [
        (50,  'Excellent  (≤ 50)'),
        (100, 'Good       (≤ 100)'),
        (200, 'Poor       (≤ 200)'),
        (300, 'Very Poor  (≤ 300)'),
    ]

    # ── Helper: color a bar by WQI value ─────────────────────────
    @staticmethod
    def _wqi_color(val: float) -> str:
        if val <= 50:
            return 'green'
        elif val <= 100:
            return 'blue'
        elif val <= 200:
            return 'orange'
        elif val <= 300:
            return 'red'
        else:
            return 'purple'

    # ─────────────────────────────────────────────────────────────
    def __init__(self, df: pd.DataFrame, output_dir: str = './EDA'):
        self.df = df.copy()
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        # Only keep parameters that are present in the dataset
        self.parameter_cols = [
            col for col in self.WHO_LIMITS.keys()
            if col in self.df.columns
        ]

        print("\nEDA Module Initialized")
        print(f"Dataset shape : {self.df.shape}")
        print(f"Parameters found : {len(self.parameter_cols)}")

        # Report presence of Step 2 output columns
        step2_cols = [
            'WQI_Calculated', 'WQI_Category','Water_Quality_Class',
            'Microbial_Status', 'Risk_Score', 'Risk_Category',
        ]
        found = [c for c in step2_cols if c in self.df.columns]
        missing = [c for c in step2_cols if c not in self.df.columns]
        print(f"Step 2 columns found   : {found}")
        if missing:
            print(f"Step 2 columns missing : {missing} (related plots will be skipped)")

    # ─────────────────────────────────────────────────────────────
    def statistical_summary(self):
        """Print and save statistical summary of all parameters."""

        print("\n--- Statistical Summary ---")

        cols = self.parameter_cols.copy()

        # Append Step 2 numeric output columns if present
        for extra in ['WQI_Calculated', 'Risk_Score']:
            if extra in self.df.columns:
                cols.append(extra)

        if not cols:
            raise ValueError("No valid parameter columns found for summary.")

        data = self.df[cols]
        desc = data.describe().T
        desc['missing']     = data.isna().sum()
        desc['missing_pct'] = (data.isna().sum() / len(self.df) * 100).round(2)

        print(desc.round(3))

        desc.round(4).to_csv(
            os.path.join(self.output_dir, 'statistical_summary.csv')
        )
        print("Saved: statistical_summary.csv")

        return desc

    # ─────────────────────────────────────────────────────────────
    def plot_parameter_distributions(self):
        """
        Histogram for each water quality parameter
        with WHO guideline reference lines.
        """
        cols = self.parameter_cols

        if not cols:
            print("No parameter columns available.")
            return

        n_cols = 3
        n_rows = int(np.ceil(len(cols) / n_cols))

        fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, n_rows * 4))
        axes = axes.flatten()

        for i, col in enumerate(cols):
            data = self.df[col].dropna()

            if data.empty:
                axes[i].set_title(f"{col} (No Data)")
                continue

            bins = min(30, max(10, int(np.sqrt(len(data)))))

            axes[i].hist(data, bins=bins, color='steelblue',
                         edgecolor='black', alpha=0.8)

            if col == 'pH':
                axes[i].axvline(6.5, color='red', linestyle='--', linewidth=1)
                axes[i].axvline(8.5, color='red', linestyle='--',
                                linewidth=1, label='WHO range (6.5–8.5)')
                axes[i].legend(fontsize=8)
            else:
                who_val = self.WHO_LIMITS.get(col)
                if who_val is not None:
                    axes[i].axvline(x=who_val, color='red', linestyle='--',
                                    linewidth=1.5, label=f'WHO limit: {who_val}')
                    axes[i].legend(fontsize=8)

            axes[i].set_title(col, fontsize=11)
            axes[i].set_xlabel('Value')
            axes[i].set_ylabel('Count')

        for j in range(len(cols), len(axes)):
            axes[j].set_visible(False)

        plt.suptitle(
            'Distribution of Water Quality Parameters\n'
            '(Red dashed line = WHO guideline limit)',
            fontsize=14, fontweight='bold'
        )
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        plt.savefig(
            os.path.join(self.output_dir, 'parameter_distributions.png'), dpi=100
        )
        plt.show()
        plt.close()
        print("Saved: parameter_distributions.png")

    # ─────────────────────────────────────────────────────────────
    def plot_boxplots_outlier_detection(self):
        """Boxplots for all parameters to visualize outliers."""

        cols = self.parameter_cols

        if not cols:
            print("No parameter columns available.")
            return

        n_cols = 3
        n_rows = int(np.ceil(len(cols) / n_cols))

        fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, n_rows * 4))
        axes = axes.flatten()

        for i, col in enumerate(cols):
            data = self.df[col].dropna()

            if data.empty:
                axes[i].set_title(f"{col} (No Data)")
                continue

            axes[i].boxplot(
                data,
                patch_artist=True,
                boxprops=dict(facecolor='lightblue'),
                medianprops=dict(color='navy', linewidth=2),
                whiskerprops=dict(color='black'),
                capprops=dict(color='black'),
                flierprops=dict(marker='o', markersize=4,
                                markerfacecolor='red', alpha=0.5),
            )

            if col == 'pH':
                axes[i].axhline(6.5, color='red', linestyle='--', linewidth=1)
                axes[i].axhline(8.5, color='red', linestyle='--',
                                linewidth=1, label='WHO range (6.5–8.5)')
                axes[i].legend(fontsize=8)
            else:
                who_val = self.WHO_LIMITS.get(col)
                if who_val is not None:
                    axes[i].axhline(y=who_val, color='red', linestyle='--',
                                    linewidth=1.5, label=f'WHO: {who_val}')
                    axes[i].legend(fontsize=8)

            axes[i].set_title(col, fontsize=11)
            axes[i].set_ylabel('Value')

        for j in range(len(cols), len(axes)):
            axes[j].set_visible(False)

        plt.suptitle(
            'Boxplots — Outlier Detection\n'
            '(Red dashed line = WHO guideline limit)',
            fontsize=14, fontweight='bold'
        )
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        plt.savefig(
            os.path.join(self.output_dir, 'boxplots_outlier_detection.png'), dpi=100
        )
        plt.show()
        plt.close()
        print("Saved: boxplots_outlier_detection.png")

    # ─────────────────────────────────────────────────────────────
    def plot_who_exceedance(self):
        """Percentage of samples exceeding WHO limits per parameter."""

        cols = self.parameter_cols
        exceed_pct = {}

        for col in cols:
            limit = self.WHO_LIMITS.get(col)
            if limit is None:
                continue

            valid = self.df[col].dropna()
            total = len(valid)
            if total == 0:
                continue

            if col == 'pH':
                exceeded = ((valid < 6.5) | (valid > 8.5)).sum()
            else:
                exceeded = (valid > limit).sum()

            exceed_pct[col] = round(exceeded / total * 100, 2)

        if not exceed_pct:
            print("No exceedance data available.")
            return

        exceed_series = pd.Series(exceed_pct).sort_values(ascending=False)

        exceed_series.to_frame('Exceedance_%').to_csv(
            os.path.join(self.output_dir, 'who_exceedance.csv')
        )

        def get_color(v):
            if v >= 50:
                return 'red'
            elif v >= 20:
                return 'orange'
            return 'steelblue'

        colors = [get_color(v) for v in exceed_series.values]
        offset = max(exceed_series.values) * 0.02

        plt.figure(figsize=(14, 6))
        bars = plt.bar(exceed_series.index, exceed_series.values,
                       color=colors, edgecolor='black')

        for bar, val in zip(bars, exceed_series.values):
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + offset,
                f'{val:.1f}%', ha='center', fontsize=9
            )

        plt.axhline(y=50, color='red', linestyle='--', linewidth=1.5,
                    label='Critical threshold (50%)')
        plt.title('Percentage of Samples Exceeding WHO Guidelines', fontsize=14)
        plt.xlabel('Parameter')
        plt.ylabel('Samples Exceeding WHO Limit (%)')
        plt.xticks(rotation=45, ha='right')
        plt.legend()
        plt.tight_layout()

        plt.savefig(
            os.path.join(self.output_dir, 'who_exceedance.png'), dpi=100
        )
        plt.show()
        plt.close()

        print("\nWHO Exceedance Summary:")
        print(exceed_series.to_string())
        print("\nTop problematic parameters:")
        print(exceed_series.head(3).to_string())
        print("Saved: who_exceedance.png")

    # ─────────────────────────────────────────────────────────────
    def plot_correlation_heatmap(self):
        """
        Spearman correlation heatmap of parameters including
        WQI_Calculated and Risk_Score.
        """
        cols = self.parameter_cols.copy()

        for extra in ['WQI_Calculated', 'Risk_Score']:
            if extra in self.df.columns:
                cols.append(extra)

        data = self.df[cols].select_dtypes(include=[np.number])

        if data.shape[1] < 2:
            print("Not enough numeric columns for correlation.")
            return

        corr = data.corr(method='spearman')
        mask = np.triu(np.ones_like(corr, dtype=bool))

        plt.figure(figsize=(16, 12))
        sns.heatmap(
            corr, mask=mask, annot=True, fmt='.2f',
            cmap='coolwarm', vmin=-1, vmax=1, center=0,
            linewidths=0.5, square=True, annot_kws={'size': 8}
        )
        plt.title(
            'Correlation Heatmap — Water Quality Parameters (Spearman)',
            fontsize=14
        )
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        plt.savefig(
            os.path.join(self.output_dir, 'correlation_heatmap.png'), dpi=100
        )
        plt.show()
        plt.close()

        # Correlation with WQI
        if 'WQI_Calculated' in corr.columns:
            corr_wqi = (
                corr['WQI_Calculated']
                .drop('WQI_Calculated')
                .reindex(
                    corr['WQI_Calculated']
                    .drop('WQI_Calculated')
                    .abs()
                    .sort_values(ascending=False)
                    .index
                )
            )
            corr_wqi.to_frame('Correlation_with_WQI').to_csv(
                os.path.join(self.output_dir, 'correlation_with_wqi.csv')
            )
            print("\nCorrelation with WQI_Calculated:")
            print(corr_wqi.to_string())

        print("Saved: correlation_heatmap.png")

    # ─────────────────────────────────────────────────────────────
    def plot_province_analysis(self):
        """
        Comprehensive province-wise analysis covering all Step 2 result
        columns plus Water Quality Class (if present in the dataset).

        Saved files:
            province_wqi.png            — avg WQI + WQI_Category stacked %
            province_microbial_risk.png — Microbial_Status + Risk_Category stacked %
            province_wqclass.png        — Water Quality Class stacked % (if column exists)
        """
        if 'Province' not in self.df.columns:
            print("Skipping province analysis: Province column not found.")
            return

        # ── helpers ──────────────────────────────────────────────
        def _stacked_pct(group_col, value_col, order, ax,
                         colors_map, title, ylabel='Percentage (%)'):
            """Draw a 100 % stacked bar on ax, columns re-ordered by `order`."""
            ct = (
                pd.crosstab(self.df[group_col], self.df[value_col])
                .reindex(columns=order, fill_value=0)
            )
            pct = ct.div(ct.sum(axis=1), axis=0) * 100
            bar_c = [colors_map.get(c, 'gray') for c in order]
            pct.plot(kind='bar', stacked=True, ax=ax, color=bar_c, edgecolor='white')
            ax.set_title(title, fontsize=11)
            ax.set_xlabel('Province')
            ax.set_ylabel(ylabel)
            ax.tick_params(axis='x', rotation=35)
            ax.legend(fontsize=7, title=value_col, bbox_to_anchor=(1, 1), loc='upper left')

        def _avg_bar(group_col, value_col, ax, color_fn, thresholds, title):
            """Draw average-value bar chart with threshold lines on ax."""
            stats = (
                self.df.dropna(subset=[group_col, value_col])
                .groupby(group_col)[value_col]
                .mean()
                .sort_values(ascending=False)
            )
            bar_c = [color_fn(v) for v in stats.values]
            bars = ax.bar(stats.index, stats.values, color=bar_c, edgecolor='black')
            for y_val, label in thresholds:
                ax.axhline(y=y_val, linestyle='--', linewidth=1, label=label)
            ax.set_title(title, fontsize=11)
            ax.set_xlabel('Province')
            ax.set_ylabel('Average ' + value_col)
            ax.tick_params(axis='x', rotation=35)
            ax.legend(fontsize=7)
            for bar, val in zip(bars, stats.values):
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + stats.values.max() * 0.01,
                        f'{val:.1f}', ha='center', fontsize=8)
            return stats

        # ══════════════════════════════════════════════════════════
        # FIGURE 1 — WQI_Calculated  +  WQI_Category
        # ══════════════════════════════════════════════════════════
        has_wqi = 'WQI_Calculated' in self.df.columns and \
                  'WQI_Category'   in self.df.columns

        if has_wqi:
            fig1, axes1 = plt.subplots(1, 2, figsize=(18, 6))

            prov_wqi = _avg_bar(
                'Province', 'WQI_Calculated', axes1[0],
                self._wqi_color, self.WQI_THRESHOLDS,
                'Average WQI_Calculated by Province'
            )

            _stacked_pct(
                'Province', 'WQI_Category',
                self.CATEGORY_ORDER, axes1[1],
                self.CATEGORY_COLORS,
                'WQI_Category Distribution by Province (%)'
            )

            plt.suptitle(
                'Province Analysis — WQI Score & Category\n'
                'Heliyon 2023 / WHO Guidelines (0–50 Excellent · 51–100 Good · '
                '101–200 Poor · 201–300 Very Poor · >300 Unsuitable)',
                fontsize=12, fontweight='bold'
            )
            plt.tight_layout()
            plt.savefig(
                os.path.join(self.output_dir, 'province_wqi.png'), dpi=100
            )
            plt.show()
            plt.close()
            print("\nProvince WQI Summary:")
            print(prov_wqi.to_string())
            print("Saved: province_wqi.png")
        else:
            print("WQI_Calculated / WQI_Category not found — skipping province WQI plot.")

        # ══════════════════════════════════════════════════════════
        # FIGURE 2 — Microbial_Status  +  Risk_Score  +  Risk_Category
        # ══════════════════════════════════════════════════════════
        has_mic  = 'Microbial_Status' in self.df.columns
        has_risk = 'Risk_Score'       in self.df.columns and \
                   'Risk_Category'    in self.df.columns

        if has_mic or has_risk:
            ncols = sum([has_mic, has_risk, has_risk])   # mic(1) + score(1) + cat(1) max 3
            # Always plot 3 panels if both present, 2 if only one group
            if has_mic and has_risk:
                fig2, axes2 = plt.subplots(1, 3, figsize=(22, 6))
                ax_mic, ax_rscore, ax_rcat = axes2
            elif has_mic:
                fig2, axes2 = plt.subplots(1, 1, figsize=(9, 6))
                ax_mic = axes2
                ax_rscore = ax_rcat = None
            else:  # has_risk only
                fig2, axes2 = plt.subplots(1, 2, figsize=(16, 6))
                ax_rscore, ax_rcat = axes2
                ax_mic = None

            mic_colors  = {'Safe': 'green', 'Contaminated': 'red'}
            risk_colors = {
                'Marginally Safe': 'green', 'Low': 'blue',
                'Medium': 'orange', 'High': 'red'
            }
            risk_order = ['Marginally Safe', 'Low', 'Medium', 'High']

            def _risk_color(score):
                s = int(score) if not np.isnan(float(score)) else -1
                if s == 0: return 'green'
                elif s <= 2: return 'blue'
                elif s <= 4: return 'orange'
                else: return 'red'

            if ax_mic is not None:
                _stacked_pct(
                    'Province', 'Microbial_Status',
                    ['Safe', 'Contaminated'], ax_mic,
                    mic_colors,
                    'Microbial_Status by Province (%)'
                )

            if ax_rscore is not None:
                _avg_bar(
                    'Province', 'Risk_Score', ax_rscore,
                    _risk_color,
                    [(1, 'Low (1–2)'), (3, 'Medium (3–4)'), (5, 'High (5–6)')],
                    'Average Risk_Score by Province'
                )

            if ax_rcat is not None:
                _stacked_pct(
                    'Province', 'Risk_Category',
                    risk_order, ax_rcat,
                    risk_colors,
                    'Risk_Category Distribution by Province (%)'
                )

            plt.suptitle(
                'Province Analysis — Microbial Status & Risk Assessment\n'
                'Heliyon 2023 — doi:10.1016/j.heliyon.2023.e13872',
                fontsize=12, fontweight='bold'
            )
            plt.tight_layout()
            plt.savefig(
                os.path.join(self.output_dir, 'province_microbial_risk.png'), dpi=100
            )
            plt.show()
            plt.close()
            print("Saved: province_microbial_risk.png")
        else:
            print("Microbial_Status / Risk columns not found — skipping province microbial/risk plot.")
        # ══════════════════════════════════════════════════════════
        # FIGURE 3 — Water Quality Class  (original dataset column)
        # ══════════════════════════════════════════════════════════
        if 'Water_Quality_Class' in self.df.columns:
            wqc_order = sorted(self.df['Water_Quality_Class'].dropna().unique())

            # FIX: replace deprecated get_cmap (Matplotlib 3.7+)
            cmap = plt.colormaps['tab10'].resampled(len(wqc_order))

            wqc_colors = {c: cmap(i) for i, c in enumerate(wqc_order)}

            fig3, ax3 = plt.subplots(figsize=(14, 6))

            _stacked_pct(
                'Province',
                'Water_Quality_Class',
                wqc_order,
                ax3,
                wqc_colors,
                'Water Quality Class Distribution by Province (%)'
            )

            plt.suptitle(
                'Province Analysis — Water Quality Class\n'
                '(Original dataset classification)',
                fontsize=12,
                fontweight='bold'
            )

            plt.tight_layout()
            plt.savefig(
                os.path.join(self.output_dir, 'province_wqclass.png'),
                dpi=100
            )
            plt.show()
            plt.close()

            print("Saved: province_wqclass.png")

            counts = (
                self.df['Water_Quality_Class']
                .value_counts()
                .reindex(self.CATEGORY_ORDER, fill_value=0)
            )

            fig, axes = plt.subplots(1, 2, figsize=(14, 5))

            # ── Left: Bar chart ───────────────────────────────────────
            bar_colors = [self.CATEGORY_COLORS.get(c, 'gray') for c in counts.index]
            axes[0].bar(counts.index, counts.values,
                        color=bar_colors, edgecolor='black')
            axes[0].set_title('Water Quality Class Distribution')
            axes[0].set_xlabel('Class')
            axes[0].set_ylabel('Count')
            axes[0].tick_params(axis='x', rotation=30)

            total = counts.sum()
            for i, (cat, val) in enumerate(counts.items()):
                pct = val / total * 100 if total > 0 else 0
                axes[0].text(i, val + 1, f'{val}\n({pct:.1f}%)',
                             ha='center', fontsize=9)

            # ── Right: Pie chart ──────────────────────────────────────
            # Only show slices with non-zero count
            non_zero = counts[counts > 0]
            pie_colors = [self.CATEGORY_COLORS.get(c, 'gray') for c in non_zero.index]

            axes[1].pie(
                non_zero.values,
                labels=non_zero.index,
                colors=pie_colors,
                autopct='%1.1f%%',
                startangle=90,
            )
            axes[1].set_title('Water Quality Class Proportion')

            plt.suptitle(
                'Water Quality Class Analysis\n'
                'By All Classification rules '
                'WQI, Risk Map, Micorbiological Analysis,',
                fontsize=11, fontweight='bold'
            )
            plt.tight_layout()
            plt.savefig(
                os.path.join(self.output_dir, 'wqc_analysis.png'), dpi=100
            )
            plt.show()
            plt.close()
            print("Saved: wqc_analysis.png")

        else:
            print("Water Quality Class column not found — skipping province WQ class plot.")# ─────────────────────────────────────────────────────────────
    def plot_resource_type_analysis(self):
        """
        Comprehensive resource-type analysis covering all Step 2 result
        columns plus Water Quality Class (if present in the dataset).

        Saved files:
            resource_wqi.png            — avg WQI + WQI_Category stacked %
            resource_microbial_risk.png — Microbial_Status + Risk_Category stacked %
            resource_wqclass.png        — Water Quality Class stacked % (if column exists)
        """
        if 'Resource Type' not in self.df.columns:
            print("Skipping resource type analysis: Resource Type column not found.")
            return

        # ── shared helpers (mirrors province helpers) ─────────────
        def _stacked_pct_res(value_col, order, ax, colors_map, title):
            ct = (
                pd.crosstab(self.df['Resource Type'], self.df[value_col])
                .reindex(columns=order, fill_value=0)
            )
            pct = ct.div(ct.sum(axis=1), axis=0) * 100
            bar_c = [colors_map.get(c, 'gray') for c in order]
            pct.plot(kind='bar', stacked=True, ax=ax, color=bar_c, edgecolor='white')
            ax.set_title(title, fontsize=11)
            ax.set_xlabel('Resource Type')
            ax.set_ylabel('Percentage (%)')
            ax.tick_params(axis='x', rotation=35)
            ax.legend(fontsize=7, title=value_col, bbox_to_anchor=(1, 1), loc='upper left')

        def _avg_bar_res(value_col, ax, color_fn, thresholds, title):
            stats = (
                self.df.dropna(subset=['Resource Type', value_col])
                .groupby('Resource Type')[value_col]
                .mean()
                .sort_values(ascending=False)
            )
            bar_c = [color_fn(v) for v in stats.values]
            bars = ax.bar(stats.index, stats.values, color=bar_c, edgecolor='black')
            for y_val, label in thresholds:
                ax.axhline(y=y_val, linestyle='--', linewidth=1, label=label)
            ax.set_title(title, fontsize=11)
            ax.set_xlabel('Resource Type')
            ax.set_ylabel('Average ' + value_col)
            ax.tick_params(axis='x', rotation=35)
            ax.legend(fontsize=7)
            for bar, val in zip(bars, stats.values):
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + stats.values.max() * 0.01,
                        f'{val:.1f}', ha='center', fontsize=8)
            return stats

        def _risk_color(score):
            try:
                s = int(float(score))
            except (ValueError, TypeError):
                return 'gray'
            if s == 0: return 'green'
            elif s <= 2: return 'blue'
            elif s <= 4: return 'orange'
            else: return 'red'

        risk_colors = {
            'Marginally Safe': 'green', 'Low': 'blue',
            'Medium': 'orange', 'High': 'red'
        }
        risk_order  = ['Marginally Safe', 'Low', 'Medium', 'High']
        mic_colors  = {'Safe': 'green', 'Contaminated': 'red'}

        # ══════════════════════════════════════════════════════════
        # FIGURE 1 — WQI_Calculated  +  WQI_Category
        # ══════════════════════════════════════════════════════════
        has_wqi = 'WQI_Calculated' in self.df.columns and \
                  'WQI_Category'   in self.df.columns

        if has_wqi:
            fig1, axes1 = plt.subplots(1, 2, figsize=(18, 6))

            res_wqi = _avg_bar_res(
                'WQI_Calculated', axes1[0],
                self._wqi_color, self.WQI_THRESHOLDS,
                'Average WQI_Calculated by Resource Type'
            )

            _stacked_pct_res(
                'WQI_Category', self.CATEGORY_ORDER, axes1[1],
                self.CATEGORY_COLORS,
                'WQI_Category Distribution by Resource Type (%)'
            )

            plt.suptitle(
                'Resource Type Analysis — WQI Score & Category\n'
                'Heliyon 2023 / WHO Guidelines (0–50 Excellent · 51–100 Good · '
                '101–200 Poor · 201–300 Very Poor · >300 Unsuitable)',
                fontsize=12, fontweight='bold'
            )
            plt.tight_layout()
            plt.savefig(
                os.path.join(self.output_dir, 'resource_wqi.png'), dpi=100
            )
            plt.show()
            plt.close()
            print("\nResource Type WQI Summary:")
            print(res_wqi.to_string())
            print("Saved: resource_wqi.png")
        else:
            print("WQI_Calculated / WQI_Category not found — skipping resource WQI plot.")

        # ══════════════════════════════════════════════════════════
        # FIGURE 2 — Microbial_Status  +  Risk_Score  +  Risk_Category
        # ══════════════════════════════════════════════════════════
        has_mic  = 'Microbial_Status' in self.df.columns
        has_risk = 'Risk_Score'       in self.df.columns and \
                   'Risk_Category'    in self.df.columns

        if has_mic or has_risk:
            if has_mic and has_risk:
                fig2, axes2 = plt.subplots(1, 3, figsize=(22, 6))
                ax_mic, ax_rscore, ax_rcat = axes2
            elif has_mic:
                fig2, axes2 = plt.subplots(1, 1, figsize=(9, 6))
                ax_mic = axes2
                ax_rscore = ax_rcat = None
            else:
                fig2, axes2 = plt.subplots(1, 2, figsize=(16, 6))
                ax_rscore, ax_rcat = axes2
                ax_mic = None

            if ax_mic is not None:
                _stacked_pct_res(
                    'Microbial_Status', ['Safe', 'Contaminated'],
                    ax_mic, mic_colors,
                    'Microbial_Status by Resource Type (%)'
                )

            if ax_rscore is not None:
                _avg_bar_res(
                    'Risk_Score', ax_rscore, _risk_color,
                    [(1, 'Low (1–2)'), (3, 'Medium (3–4)'), (5, 'High (5–6)')],
                    'Average Risk_Score by Resource Type'
                )

            if ax_rcat is not None:
                _stacked_pct_res(
                    'Risk_Category', risk_order, ax_rcat, risk_colors,
                    'Risk_Category Distribution by Resource Type (%)'
                )

            plt.suptitle(
                'Resource Type Analysis — Microbial Status & Risk Assessment\n'
                'Heliyon 2023 — doi:10.1016/j.heliyon.2023.e13872',
                fontsize=12, fontweight='bold'
            )
            plt.tight_layout()
            plt.savefig(
                os.path.join(self.output_dir, 'resource_microbial_risk.png'), dpi=100
            )
            plt.show()
            plt.close()
            print("Saved: resource_microbial_risk.png")
        else:
            print("Microbial_Status / Risk columns not found — skipping resource microbial/risk plot.")

        # ══════════════════════════════════════════════════════════
        # FIGURE 3 — Water Quality Class  (original dataset column)
        # ══════════════════════════════════════════════════════════
        if 'Water_Quality_Class' in self.df.columns:
            wqc_order = sorted(self.df['Water_Quality_Class'].dropna().unique())

            # FIX: modern colormap API (replaces plt.cm.get_cmap)
            cmap = plt.colormaps['tab10'].resampled(len(wqc_order))

            wqc_colors = {c: cmap(i) for i, c in enumerate(wqc_order)}

            fig3, ax3 = plt.subplots(figsize=(14, 6))

            _stacked_pct_res(
                'Water_Quality_Class',
                wqc_order,
                ax3,
                wqc_colors,
                'Water Quality Class Distribution by Resource Type (%)'
            )

            plt.suptitle(
                'Resource Type Analysis — Water Quality Class\n'
                '(Original dataset classification)',
                fontsize=12, fontweight='bold'
            )

            plt.tight_layout()
            plt.savefig(
                os.path.join(self.output_dir, 'resource_wqclass.png'),
                dpi=100
            )
            plt.show()
            plt.close()

            print("Saved: resource_wqclass.png")

        else:
            print("Water Quality Class column not found — skipping resource WQ class plot.")
    # ─────────────────────────────────────────────────────────────
    def plot_wqi_category_analysis(self):
        """
        Bar + pie chart of WQI category distribution.
        Uses updated category order and colors (Heliyon 2023 / WHO).
        """
        if 'WQI_Category' not in self.df.columns:
            print("Skipping WQI category analysis: WQI_Category not found.")
            return

        counts = (
            self.df['WQI_Category']
            .value_counts()
            .reindex(self.CATEGORY_ORDER, fill_value=0)
        )

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # ── Left: Bar chart ───────────────────────────────────────
        bar_colors = [self.CATEGORY_COLORS.get(c, 'gray') for c in counts.index]
        axes[0].bar(counts.index, counts.values,
                    color=bar_colors, edgecolor='black')
        axes[0].set_title('WQI Category Distribution')
        axes[0].set_xlabel('Category')
        axes[0].set_ylabel('Count')
        axes[0].tick_params(axis='x', rotation=30)

        total = counts.sum()
        for i, (cat, val) in enumerate(counts.items()):
            pct = val / total * 100 if total > 0 else 0
            axes[0].text(i, val + 1, f'{val}\n({pct:.1f}%)',
                         ha='center', fontsize=9)

        # ── Right: Pie chart ──────────────────────────────────────
        # Only show slices with non-zero count
        non_zero = counts[counts > 0]
        pie_colors = [self.CATEGORY_COLORS.get(c, 'gray') for c in non_zero.index]

        axes[1].pie(
            non_zero.values,
            labels=non_zero.index,
            colors=pie_colors,
            autopct='%1.1f%%',
            startangle=90,
        )
        axes[1].set_title('WQI Category Proportion')

        plt.suptitle(
            'Water Quality Index Category Analysis\n'
            'Heliyon 2023 / WHO Classification  '
            '(0–50 Excellent · 51–100 Good · 101–200 Poor · 201–300 Very Poor · >300 Unsuitable)',
            fontsize=11, fontweight='bold'
        )
        plt.tight_layout()
        plt.savefig(
            os.path.join(self.output_dir, 'wqi_category_analysis.png'), dpi=100
        )
        plt.show()
        plt.close()
        print("Saved: wqi_category_analysis.png")

    # ─────────────────────────────────────────────────────────────
    def plot_parameter_vs_wqi(self):
        """
        Scatter plots with trend line and WHO limit line
        showing each parameter's relationship with WQI_Calculated.
        """
        if 'WQI_Calculated' not in self.df.columns:
            print("Skipping: WQI_Calculated not found.")
            return

        cols = [c for c in self.PARAMETER_COLS if c in self.df.columns]

        n_cols = 3
        n_rows = int(np.ceil(len(cols) / n_cols))

        fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, n_rows * 4))
        axes = axes.flatten()

        correlation_results = {}

        for i, col in enumerate(cols):
            data = self.df[[col, 'WQI_Calculated']].dropna()

            if len(data) < 10:
                axes[i].set_visible(False)
                continue

            x = data[col]
            y = data['WQI_Calculated']

            axes[i].scatter(x, y, alpha=0.4, color='steelblue', s=20)

            corr = x.corr(y)
            correlation_results[col] = corr

            try:
                z = np.polyfit(x, y, 1)
                p = np.poly1d(z)
                axes[i].plot(x, p(x), linestyle='--', color='darkorange',
                             linewidth=1.5, label='Trend')
            except Exception:
                pass

            who_val = self.WHO_LIMITS.get(col)
            if who_val is not None:
                axes[i].axvline(x=who_val, color='red', linestyle='--',
                                linewidth=1, label=f'WHO: {who_val}')

            axes[i].set_xlabel(col, fontsize=9)
            axes[i].set_ylabel('WQI', fontsize=9)
            axes[i].set_title(f'{col} vs WQI\n(r = {corr:.2f})', fontsize=10)
            axes[i].legend(fontsize=7)

        for j in range(len(cols), len(axes)):
            axes[j].set_visible(False)

        plt.suptitle(
            'Parameter vs WQI Relationship\n(Trend line + Pearson r)',
            fontsize=14, fontweight='bold'
        )
        plt.tight_layout()
        plt.savefig(
            os.path.join(self.output_dir, 'parameter_vs_wqi.png'), dpi=100
        )
        plt.show()
        plt.close()
        print("Saved: parameter_vs_wqi.png")

        print("\nTop Parameters Influencing WQI:")
        for param, corr in sorted(correlation_results.items(),
                                   key=lambda x: abs(x[1]), reverse=True):
            print(f"  {param:<25} r = {corr:.3f}")

    # ─────────────────────────────────────────────────────────────
    def plot_year_trend(self):
        """
        Year-wise average WQI trend with regression line and
        updated threshold references (50 / 100 / 200 / 300).
        """
        if 'Sampling Date' not in self.df.columns:
            print("Sampling Date column not found, skipping year trend.")
            return

        df_year = self.df.dropna(subset=['Sampling Date']).copy()

        df_year['Year'] = pd.to_datetime(
            df_year['Sampling Date'], errors='coerce'
        ).dt.year

        df_year = df_year.dropna(subset=['Year', 'WQI_Calculated'])

        if df_year.empty:
            print("No valid year/WQI data for trend plot.")
            return

        year_wqi   = df_year.groupby('Year')['WQI_Calculated'].mean()
        year_count = df_year['Year'].value_counts().sort_index()

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # ── Left: WQI trend over years ────────────────────────────
        axes[0].plot(year_wqi.index, year_wqi.values,
                     marker='o', linewidth=2, label='Avg WQI')

        for y_val, label in self.WQI_THRESHOLDS:
            axes[0].axhline(y=y_val, linestyle='--', linewidth=1, label=label)

        trend_msg = "Insufficient data"
        if len(year_wqi) > 1:
            x_arr = year_wqi.index.values.astype(float)
            y_arr = year_wqi.values
            z = np.polyfit(x_arr, y_arr, 1)
            p = np.poly1d(z)
            axes[0].plot(x_arr, p(x_arr), linestyle=':', color='black',
                         linewidth=1.5, label='Regression')
            slope = z[0]
            if slope > 0:
                trend_msg = "Worsening (WQI increasing)"
            elif slope < 0:
                trend_msg = "Improving (WQI decreasing)"
            else:
                trend_msg = "Stable"

        axes[0].set_title('Average WQI Score Over Years')
        axes[0].set_xlabel('Year')
        axes[0].set_ylabel('Average WQI')
        axes[0].grid(True, alpha=0.3)
        axes[0].legend(fontsize=7)

        for x_val, y_val in zip(year_wqi.index, year_wqi.values):
            axes[0].text(x_val, y_val + 1, f'{y_val:.1f}',
                         ha='center', fontsize=8)

        # ── Right: Sample count per year ──────────────────────────
        axes[1].bar(year_count.index, year_count.values, edgecolor='black')
        axes[1].set_title('Sample Count per Year')
        axes[1].set_xlabel('Year')
        axes[1].set_ylabel('Count')

        for x_val, y_val in zip(year_count.index, year_count.values):
            axes[1].text(x_val, y_val + 0.5, str(y_val),
                         ha='center', fontsize=8)

        plt.suptitle(
            f'Water Quality Trend Analysis Over Years\nTrend: {trend_msg}',
            fontsize=14, fontweight='bold'
        )
        plt.tight_layout()
        plt.savefig(
            os.path.join(self.output_dir, 'year_trend.png'), dpi=100
        )
        plt.show()
        plt.close()

        print("Saved: year_trend.png")
        print(f"Trend Interpretation: {trend_msg}")

    # ─────────────────────────────────────────────────────────────
    def plot_outlier_count(self):
        """
        Bar chart of IQR-based outlier count per numeric parameter.
        Uses self.df (no external argument needed).
        """
        numeric_cols = self.df[self.parameter_cols].select_dtypes(
            include=['float64', 'int64', 'float32', 'int32']
        ).columns.tolist()

        if not numeric_cols:
            print("No numeric parameter columns for outlier count.")
            return

        outlier_counts = {}
        for col in numeric_cols:
            series = self.df[col].dropna()
            if series.empty:
                continue
            Q1  = series.quantile(0.25)
            Q3  = series.quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR
            outlier_counts[col] = int(((series < lower) | (series > upper)).sum())

        if not outlier_counts:
            print("No outlier data computed.")
            return

        outlier_series = pd.Series(outlier_counts).sort_values(ascending=False)

        plt.figure(figsize=(14, 5))
        bars = plt.bar(outlier_series.index, outlier_series.values,
                       edgecolor='black', color='steelblue')

        for bar, val in zip(bars, outlier_series.values):
            plt.text(bar.get_x() + bar.get_width() / 2,
                     bar.get_height() + 0.3, str(val),
                     ha='center', fontsize=9)

        plt.title('IQR-based Outlier Count per Parameter', fontsize=14)
        plt.xlabel('Parameter')
        plt.ylabel('Outlier Count')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(
            os.path.join(self.output_dir, 'outlier_count.png'), dpi=100
        )
        plt.show()
        plt.close()
        print("Saved: outlier_count.png")

    # ─────────────────────────────────────────────────────────────
    def plot_microbial_status(self):
        """
        Visualize Microbial_Status (Safe / Contaminated) from Step 2.

        Plots:
            Left  — overall count bar chart
            Right — microbial status breakdown by province (if available)
        """
        if 'Microbial_Status' not in self.df.columns:
            print("Skipping microbial analysis: Microbial_Status column not found.")
            return

        mic_counts = self.df['Microbial_Status'].value_counts(dropna=False)
        total = mic_counts.sum()

        mic_colors = {'Safe': 'green', 'Contaminated': 'red'}

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # ── Left: Overall counts ──────────────────────────────────
        bar_colors = [mic_colors.get(str(s), 'gray') for s in mic_counts.index]
        axes[0].bar(mic_counts.index.astype(str), mic_counts.values,
                    color=bar_colors, edgecolor='black')
        axes[0].set_title('Overall Microbial Status')
        axes[0].set_xlabel('Status')
        axes[0].set_ylabel('Sample Count')

        for i, (status, val) in enumerate(mic_counts.items()):
            pct = val / total * 100 if total > 0 else 0
            axes[0].text(i, val + 0.5, f'{val}\n({pct:.1f}%)',
                         ha='center', fontsize=10, fontweight='bold')

        # ── Right: By province (if available) ────────────────────
        if 'Province' in self.df.columns:
            mic_prov = (
                pd.crosstab(self.df['Province'], self.df['Microbial_Status'])
                .reindex(columns=['Safe', 'Contaminated'], fill_value=0)
            )
            mic_prov_pct = mic_prov.div(mic_prov.sum(axis=1), axis=0) * 100
            mic_prov_pct.plot(
                kind='bar', stacked=True, ax=axes[1],
                color=[mic_colors.get(c, 'gray') for c in mic_prov_pct.columns]
            )
            axes[1].set_title('Microbial Status by Province (%)')
            axes[1].set_xlabel('Province')
            axes[1].set_ylabel('Percentage (%)')
            axes[1].tick_params(axis='x', rotation=30)
            axes[1].legend(title='Status', fontsize=8)
        else:
            axes[1].set_visible(False)

        plt.suptitle(
            'Microbial Water Quality Assessment\n'
            '(E. coli or Total Coliform > 0 → Contaminated)',
            fontsize=13, fontweight='bold'
        )
        plt.tight_layout()
        plt.savefig(
            os.path.join(self.output_dir, 'microbial_status.png'), dpi=100
        )
        plt.show()
        plt.close()
        print("Saved: microbial_status.png")

    # ─────────────────────────────────────────────────────────────
    def plot_risk_assessment(self):
        """
        Visualize Risk_Score and Risk_Category from Step 2.

        Plots:
            Top-left  — Risk_Score distribution (bar chart)
            Top-right — Risk_Category distribution (bar chart)
            Bottom    — Risk_Category by province stacked bar (if available)
        """
        if 'Risk_Score' not in self.df.columns or \
           'Risk_Category' not in self.df.columns:
            print("Skipping risk assessment plot: Risk_Score / Risk_Category not found.")
            return

        risk_colors = {
            'Marginally Safe': 'green',
            'Low':             'blue',
            'Medium':          'orange',
            'High':            'red',
        }
        risk_order = ['Marginally Safe', 'Low', 'Medium', 'High']

        score_counts = (
            self.df['Risk_Score']
            .value_counts(dropna=False)
            .sort_index()
        )
        cat_counts = (
            self.df['Risk_Category']
            .value_counts(dropna=False)
            .reindex(risk_order, fill_value=0)
        )
        total = cat_counts.sum()

        has_province = 'Province' in self.df.columns
        nrows = 2 if has_province else 1
        fig, axes = plt.subplots(nrows, 2, figsize=(14, 5 * nrows))

        if nrows == 1:
            axes = axes.reshape(1, 2)

        # ── Top-left: Score distribution ─────────────────────────
        score_bar_colors = []
        for s in score_counts.index:
            try:
                s_int = int(s)
                if s_int == 0:
                    score_bar_colors.append('green')
                elif s_int <= 2:
                    score_bar_colors.append('blue')
                elif s_int <= 4:
                    score_bar_colors.append('orange')
                else:
                    score_bar_colors.append('red')
            except (ValueError, TypeError):
                score_bar_colors.append('gray')

        axes[0, 0].bar(score_counts.index.astype(str), score_counts.values,
                       color=score_bar_colors, edgecolor='black')
        axes[0, 0].set_title('Risk Score Distribution (0–6)')
        axes[0, 0].set_xlabel('Risk Score')
        axes[0, 0].set_ylabel('Sample Count')

        for i, (score, val) in enumerate(score_counts.items()):
            axes[0, 0].text(i, val + 0.3, str(val),
                            ha='center', fontsize=9, fontweight='bold')

        # ── Top-right: Category distribution ─────────────────────
        cat_bar_colors = [risk_colors.get(c, 'gray') for c in cat_counts.index]
        axes[0, 1].bar(cat_counts.index, cat_counts.values,
                       color=cat_bar_colors, edgecolor='black')
        axes[0, 1].set_title('Risk Category Distribution')
        axes[0, 1].set_xlabel('Risk Category')
        axes[0, 1].set_ylabel('Sample Count')
        axes[0, 1].tick_params(axis='x', rotation=20)

        for i, (cat, val) in enumerate(cat_counts.items()):
            pct = val / total * 100 if total > 0 else 0
            axes[0, 1].text(i, val + 0.5, f'{val}\n({pct:.1f}%)',
                            ha='center', fontsize=9, fontweight='bold')

        # ── Bottom: By province ───────────────────────────────────
        if has_province:
            risk_prov = (
                pd.crosstab(self.df['Province'], self.df['Risk_Category'])
                .reindex(columns=risk_order, fill_value=0)
            )
            risk_prov_pct = risk_prov.div(risk_prov.sum(axis=1), axis=0) * 100
            risk_prov_pct.plot(
                kind='bar', stacked=True, ax=axes[1, 0],
                color=[risk_colors.get(c, 'gray') for c in risk_order]
            )
            axes[1, 0].set_title('Risk Category by Province (%)')
            axes[1, 0].set_xlabel('Province')
            axes[1, 0].set_ylabel('Percentage (%)')
            axes[1, 0].tick_params(axis='x', rotation=30)
            axes[1, 0].legend(title='Risk Category', fontsize=8)
            axes[1, 1].set_visible(False)

        plt.suptitle(
            'Water Pollution Risk Assessment\n'
            '(Heliyon 2023 — doi:10.1016/j.heliyon.2023.e13872)',
            fontsize=13, fontweight='bold'
        )
        plt.tight_layout()
        plt.savefig(
            os.path.join(self.output_dir, 'risk_assessment.png'), dpi=100
        )
        plt.show()
        plt.close()
        print("Saved: risk_assessment.png")

    # ─────────────────────────────────────────────────────────────
    def plot_water_quality_class_analysis(self):
        """
        Overall distribution of the original 'Water_Quality_Class' column
        — bar chart + pie chart — separate from the per-province / per-resource
        breakdowns produced inside plot_province_analysis and
        plot_resource_type_analysis.

        Saved file:  wq_class_overview.png
        """
        if 'Water_Quality_Class' not in self.df.columns:
            print("Skipping Water Quality Class analysis: column not found.")
            return

        wqc_counts = (
            self.df['Water_Quality_Class']
            .value_counts(dropna=False)
            .sort_index()
        )
        total = wqc_counts.sum()

        wqc_order  = list(wqc_counts.index.astype(str))
        cmap = plt.colormaps['tab10'].resampled(len(wqc_order))
        wqc_colors = [cmap(i) for i in range(len(wqc_order))]

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # ── Left: Bar chart ───────────────────────────────────────
        bars = axes[0].bar(wqc_counts.index.astype(str), wqc_counts.values,
                           color=wqc_colors, edgecolor='black')
        axes[0].set_title('Water Quality Class — Overall Distribution')
        axes[0].set_xlabel('Water_Quality_Class')
        axes[0].set_ylabel('Sample Count')
        axes[0].tick_params(axis='x', rotation=30)

        for bar, val in zip(bars, wqc_counts.values):
            pct = val / total * 100 if total > 0 else 0
            axes[0].text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + total * 0.005,
                f'{val}\n({pct:.1f}%)', ha='center', fontsize=9
            )

        # ── Right: Pie chart ──────────────────────────────────────
        non_zero = wqc_counts[wqc_counts > 0]
        nz_colors = [cmap(i) for i, v in enumerate(wqc_counts.values) if v > 0]

        axes[1].pie(
            non_zero.values,
            labels=non_zero.index.astype(str),
            colors=nz_colors,
            autopct='%1.1f%%',
            startangle=90,
        )
        axes[1].set_title('Water Quality Class — Proportion')

        plt.suptitle(
            'Water Quality Class Overview\n(Original dataset classification)',
            fontsize=13, fontweight='bold'
        )
        plt.tight_layout()
        plt.savefig(
            os.path.join(self.output_dir, 'wq_class_overview.png'), dpi=100
        )
        plt.show()
        plt.close()
        print("Saved: wq_class_overview.png")

    # ─────────────────────────────────────────────────────────────
    def run_eda(self):
        """
        Run complete EDA pipeline.  Continues even if one step fails.

        Steps:
            1.  Statistical Summary
            2.  Parameter Distributions
            3.  Boxplots — Outlier Detection
            4.  WHO Exceedance Analysis
            5.  Correlation Heatmap
            6.  Province Analysis
                  → province_wqi.png            (WQI_Calculated + WQI_Category)
                  → province_microbial_risk.png (Microbial_Status + Risk_Score + Risk_Category)
                  → province_wqclass.png        (Water Quality Class, if column present)
            7.  Resource Type Analysis
                  → resource_wqi.png            (WQI_Calculated + WQI_Category)
                  → resource_microbial_risk.png (Microbial_Status + Risk_Score + Risk_Category)
                  → resource_wqclass.png        (Water Quality Class, if column present)
            8.  WQI Category Analysis
            9.  Water Quality Class Overview    (if column present)
            10. Parameter vs WQI Relationships
            11. Year Trend Analysis
            12. Outlier Count Analysis
            13. Microbial Status Analysis       (overall Safe/Contaminated counts)
            14. Risk Assessment Analysis        (overall Risk_Score / Risk_Category)
        """
        import time

        print("\n" + "=" * 55)
        print("     STEP 3: EXPLORATORY DATA ANALYSIS")
        print("=" * 55)

        steps = [
            ("Statistical Summary",             self.statistical_summary),
            ("Parameter Distributions",         self.plot_parameter_distributions),
            ("Boxplots — Outlier Detection",    self.plot_boxplots_outlier_detection),
            ("WHO Exceedance Analysis",          self.plot_who_exceedance),
            ("Correlation Heatmap",              self.plot_correlation_heatmap),
            ("Province Analysis",                self.plot_province_analysis),
            ("Resource Type Analysis",           self.plot_resource_type_analysis),
            ("WQI Category Analysis",            self.plot_wqi_category_analysis),
            ("Water Quality Class Overview",     self.plot_water_quality_class_analysis),
            ("Parameter vs WQI Relationships",  self.plot_parameter_vs_wqi),
            ("Year Trend Analysis",              self.plot_year_trend),
            ("Outlier Count Analysis",           self.plot_outlier_count),
            ("Microbial Status Analysis",        self.plot_microbial_status),
            ("Risk Assessment Analysis",         self.plot_risk_assessment),
        ]

        for i, (name, func) in enumerate(steps, start=1):
            print(f"\n[{i}/{len(steps)}] {name}...")
            start_time = time.time()
            try:
                func()
                print(f"✔ Completed in {time.time() - start_time:.2f}s")
            except Exception as e:
                print(f"✖ Failed: {name}")
                print(f"   Error: {e}")

        print("\n" + "=" * 55)
        print("Step 3 — EDA COMPLETE!")
        print(f"All plots saved to: {self.output_dir}")
        print("=" * 55)

    # ─────────────────────────────────────────────────────────────
    def get_dataframe(self) -> pd.DataFrame:
        """Return the DataFrame used for EDA."""
        return self.df