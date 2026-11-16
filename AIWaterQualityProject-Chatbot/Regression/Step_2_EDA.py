import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import os
from scipy.stats import norm

class EDA:

    def __init__(self, df, df_model_ready, output_dir="./EDA"):
        self.df = df.copy()
        self.df_model_ready = df_model_ready.copy()
        self.output_dir = output_dir

        os.makedirs(self.output_dir, exist_ok=True)

    def clean_filename(self, text):
        return text.replace("/", "_").replace("\\", "_").replace(" ", "_")

    # 1. Basic Info & Statistical Description
    def describe_data(self):
        self.df.info()
        desc = self.df.describe()
        desc.T.to_csv(os.path.join(self.output_dir, "df_description.csv"))
        return desc

    # 2. Count Plots for Categorical Features
    def plot_categorical_counts(self):
        cat_columns = {
            "Province"            : "Count of Province Samples",
            "City"                : "Count of City Samples",
            "Resource Type"       : "Count of Resource Type Samples",
            "Water_Quality_Class" : "Count of Water Quality Class Samples"
        }

        for col, title in cat_columns.items():
            plt.figure(figsize=(16, 7))
            sns.countplot(x=col, data=self.df)
            plt.title(title, size=16)
            plt.ylabel("Count", size=14)
            plt.xlabel(col, size=14)
            plt.xticks(rotation=45)
            sns.despine(top=True, right=True, left=False, bottom=False)
            plt.tight_layout()
            safe_col = self.clean_filename(col)
            plt.savefig(os.path.join(self.output_dir, f"Count_of_{safe_col}_graph.png"))
            col_class_count = self.df[col].value_counts()
            col_class_count.to_csv(os.path.join(self.output_dir, f'{safe_col}_class_counts.csv'), header=['Count'])
            plt.show()
            plt.close()

    # 3. WQI Distribution Analysis
    def plot_wqi_distributions(self):
        # Histogram with Bell Curve
        plt.figure(figsize=(8, 5))
        plt.hist(self.df["WQI"], bins=50, density=True, color='skyblue', edgecolor='black')
        mu, std = self.df["WQI"].mean(), self.df["WQI"].std()
        x = np.linspace(self.df["WQI"].min(), self.df["WQI"].max(), 100)
        plt.plot(x, norm.pdf(x, mu, std), color='red', lw=2, label='Normal Curve')
        plt.xlabel("WQI")
        plt.ylabel("Frequency")
        plt.title("Distribution of Water Quality Index (WQI)")
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "wqi_hist.png"))
        plt.show()
        plt.close()

        # WQI by Resource Type
        plt.figure(figsize=(12, 6))
        sns.barplot(x='Resource Type', y='WQI', data=self.df)
        plt.title("WQI Distribution by Resource Type")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "ResourceTypeWQIDistribution.png"))
        plt.show()
        plt.close()

        # WQI by Province
        plt.figure(figsize=(12, 6))
        sns.barplot(x='Province', y='WQI', data=self.df)
        plt.title("WQI Distribution by Province")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "ProvinceWQIDistribution.png"))
        plt.show()
        plt.close()

        # WQI vs Temperature by Resource Type
        plt.figure(figsize=(12, 6))
        sns.lineplot(x='Temperature (°C)', y='WQI', hue='Resource Type', data=self.df, marker='o', linestyle='')
        plt.title("WQI vs Temperature by Resource Type")
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "WQIvsTemperatureperResourceType.png"))
        plt.show()
        plt.close()

        # Average WQI per Resource Type and Province
        avg_wqi = self.df.groupby(['Resource Type', 'Province'])['WQI'].mean().reset_index()
        avg_wqi.to_csv(os.path.join(self.output_dir, "AverageWQIperResourceTypeandProvince.csv"), index=False)

        plt.figure(figsize=(12, 6))
        sns.barplot(x='Province', y='WQI', hue='Resource Type', data=avg_wqi)
        plt.title("Average WQI per Resource Type and Province")
        plt.ylabel("Average WQI")
        plt.xlabel("Province")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "AverageWQIperResourceTypeandProvince.png"))
        plt.show()
        plt.close()

        # WQI by Water Quality Class across Demand Levels (pH quartiles)
        df_dl = self.df.copy()
        df_dl['pH_Level'] = pd.qcut(
            df_dl['pH'],
            q=[0, 0.25, 0.5, 0.75, 1.0],
            labels=['Very Low', 'Low', 'Medium', 'High']
        )

        plt.figure(figsize=(14, 6))
        sns.boxplot(x='Resource Type', y='WQI', hue='pH_Level', data=df_dl)
        plt.title("WQI of Resource Types across pH Regimes")
        plt.xlabel("Resource Type")
        plt.ylabel("WQI")
        plt.legend(title="pH Level", loc='upper right')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "WQI_by_ResourceType_and_pHLevel.png"))
        plt.show()
        plt.close()

        # Heatmap: Average WQI by Province and pH Level
        pivot_table = df_dl.pivot_table(
            values='WQI',
            index='Province',
            columns='pH_Level',
            aggfunc='mean'
        )

        plt.figure(figsize=(10, 6))
        sns.heatmap(pivot_table, annot=True, fmt=".2f", cmap="coolwarm")
        plt.title("Average WQI by Province and pH Level")
        plt.ylabel("Province")
        plt.xlabel("pH Level")
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "WQI_Heatmap_Province_pHLevel.png"))
        plt.show()
        plt.close()

        # Line plot: Average WQI across pH Levels by Resource Type
        summary_df = (df_dl.groupby(['Resource Type', 'pH_Level'], as_index=False)['WQI'].mean())

        plt.figure(figsize=(12, 6))
        sns.lineplot(data=summary_df, x='pH_Level', y='WQI', hue='Resource Type', marker='o')
        plt.title("Average WQI across pH Levels by Resource Type")
        plt.xlabel("pH Level")
        plt.ylabel("Average WQI")
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "Avg_WQI_by_ResourceType_pHLevel.png"))
        plt.show()
        plt.close()

    # 4. Water Quality Feature Analysis
    def analyze_water_quality_features(self):
        numeric_features = [
            'pH', 'Turbidity (NTU)', 'EC (µS/cm)',
            'TDS (mg/L)', 'Hardness (mg/L)',
            'Calcium (mg/L)', 'Magnesium (mg/L)',
            'Sodium (mg/L)', 'Potassium (mg/L)',
            'Chloride (mg/L)', 'Sulfate (mg/L)',
            'Nitrate (mg/L)', 'Fluoride (mg/L)',
            'Iron (mg/L)', 'Arsenic (mg/L)', 'Total Coliform', 'E. Coli'
        ]

        df_features = self.df[numeric_features]

        # Histograms with Bell Curves
        n_cols = 3
        n_rows = (len(numeric_features) + n_cols - 1) // n_cols
        plt.figure(figsize=(18, 5 * n_rows))

        for i, col in enumerate(numeric_features, 1):
            plt.subplot(n_rows, n_cols, i)
            data = df_features[col].dropna()
            sns.histplot(data, bins=30, stat='density', color='skyblue', edgecolor='black')
            mu, std = data.mean(), data.std()
            x = np.linspace(data.min(), data.max(), 100)
            plt.plot(x, norm.pdf(x, mu, std), color='red', lw=2, label='Normal Curve')
            plt.title(col)
            plt.xlabel(col)
            plt.ylabel("Density")
            plt.legend()

        plt.suptitle("Distribution of Numeric Water Quality Features with Bell Curve", fontsize=18)
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        plt.savefig(os.path.join(self.output_dir, "WaterQuality_Features_hist.png"))
        plt.show()
        plt.close()

        # Boxplots
        plt.figure(figsize=(18, 6))
        sns.boxplot(data=df_features)
        plt.title("Boxplot of Water Quality Features")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "WaterQuality_Features_Boxplot.png"))
        plt.show()
        plt.close()

        # Correlation Heatmap
        plt.figure(figsize=(14, 10))
        sns.heatmap(df_features.corr(), annot=True, fmt=".2f", cmap='coolwarm')
        plt.title("Correlation of Water Quality Features")
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "WaterQuality_Features_Correlation.png"))
        plt.show()
        plt.close()

        # Pairplot
        sns.pairplot(df_features)
        plt.savefig(os.path.join(self.output_dir, "WaterQuality_Features_Pairplot.png"))
        plt.show()
        plt.close()

    # 5. RMSE Error Analysis per City
    def calculate_rmse_per_city(self):
        df = self.df.copy()
        # Best (lowest) WQI per Resource Type
        best_wqi_per_resource = df.groupby("Resource Type")["WQI"].min()
        # Decision error
        df["Error"] = df["WQI"] - df["Resource Type"].map(best_wqi_per_resource)
        # RMSE per City
        city_rmse = (
            df.groupby("City")["Error"]
            .apply(lambda x: np.sqrt(np.mean(x ** 2)))
            .reset_index(name="RMSE")
            .sort_values("RMSE")
        )

        # Baseline city
        baseline_city = city_rmse.iloc[0]["City"]
        baseline_rmse = city_rmse.iloc[0]["RMSE"]

        # Save
        city_rmse.to_csv(os.path.join(self.output_dir, "City_RMSE.csv"), index=False)

        # Distribution of City RMSE
        plt.figure(figsize=(12, 6))
        plt.hist(city_rmse["RMSE"], bins=30, density=True, alpha=0.7, label="RMSE Distribution")
        mu  = city_rmse["RMSE"].mean()
        std = city_rmse["RMSE"].std()
        x   = np.linspace(city_rmse["RMSE"].min(), city_rmse["RMSE"].max(), 200)
        plt.plot(x, norm.pdf(x, mu, std), lw=2, label="Normal Curve")
        plt.axvline(mu, linestyle="--", linewidth=2, label=f"Mean RMSE = {mu:.2f}")
        plt.title("Distribution of City Decision RMSE of WQI")
        plt.xlabel("RMSE (WQI)")
        plt.ylabel("Density")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "Distribution_of_City_RMSE.png"))
        plt.show()
        plt.close()

        # Best vs Worst Cities
        subset = pd.concat([city_rmse.head(10), city_rmse.tail(10)])
        plt.figure(figsize=(14, 6))
        bars = plt.bar(subset["City"].astype(str), subset["RMSE"])
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2, height,
                     f"{height:.2f}", ha="center", va="bottom", fontsize=9)
        plt.axhline(y=mu, linestyle="--", linewidth=2, label="Mean RMSE", color="red")
        plt.xticks(rotation=90)
        plt.ylabel("RMSE")
        plt.xlabel("City")
        plt.title("Best and Worst Cities by Decision RMSE of WQI")
        plt.legend()
        plt.grid(axis="y", linestyle="--", alpha=0.6)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "BestWorstCities_RMSE.png"))
        plt.show()
        plt.close()

        return city_rmse, baseline_city, baseline_rmse

    # 6. Run Full EDA
    def run_eda(self):
        self.describe_data()
        self.plot_categorical_counts()
        self.plot_wqi_distributions()
        self.analyze_water_quality_features()
        city_rmse, baseline_city, baseline_rmse = self.calculate_rmse_per_city()
        print("\n EDA completed successfully.")
        return city_rmse, baseline_city, baseline_rmse