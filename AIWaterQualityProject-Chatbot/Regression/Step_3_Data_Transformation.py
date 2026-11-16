import pandas as pd
from sklearn.preprocessing import StandardScaler, OneHotEncoder
import os

class DataTransform:
    def __init__(self, df, output_dir="./TransformedData"):
        self.df = df.copy()
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        self.transformed_df = None
        self.numeric_cols = None
        self.cat_cols = None

    # 1. Identify columns and transform
    def transform_data(self, exclude_cols=["Sampling Date", "WQI", "Water Quality Class"]):
        df = self.df.copy()

        # Scale numeric columns
        self.numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        self.numeric_cols = [c for c in self.numeric_cols if c not in exclude_cols]

        scaler = StandardScaler()
        df[self.numeric_cols] = scaler.fit_transform(df[self.numeric_cols])

        # Encode categorical columns
        self.cat_cols = df.select_dtypes(include=['object']).columns.tolist()
        self.cat_cols = [c for c in self.cat_cols if c not in exclude_cols]

        encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)

        encoded_parts = []

        for col in self.cat_cols:
            if col not in df.columns:
                continue

            encoded_array = encoder.fit_transform(df[[col]])

            encoded_df = pd.DataFrame(
                encoded_array,
                columns=encoder.get_feature_names_out([col]),
                index=df.index
            )

            encoded_parts.append(encoded_df)

        df = df.drop(columns=self.cat_cols)

        if encoded_parts:
            df = pd.concat([df, encoded_df], axis=1)

        self.transformed_df = df

        # Save transformed DataFrame
        if self.transformed_df is not None:
            self.transformed_df.to_csv(os.path.join(self.output_dir, "df_transformed.csv"), index=False)

        print(f"Transformed DataFrame saved with shape: {self.transformed_df.shape}")
        return self.transformed_df

    # 2. Run transformation
    def run_transformation(self):
        transformed_df = self.transform_data()
        print("\n Full Data Transformation completed successfully.")
        return transformed_df