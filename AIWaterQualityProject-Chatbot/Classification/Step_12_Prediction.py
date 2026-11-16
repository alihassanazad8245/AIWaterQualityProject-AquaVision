import joblib
import pandas as pd
import os


class WaterQualityPredictor:

    def __init__(self,
                 model_path='./Models/final_model.pkl',
                 feature_path='./Models/final_features.csv',
                 class_path='./Models/class_names.pkl'):

        # Load model
        self.model = joblib.load(model_path)

        # Load EXACT features used in training
        if not os.path.exists(feature_path):
            raise FileNotFoundError(
                f"Feature file not found: {feature_path}\n"
                f"Run Step 5 again to generate it."
            )

        self.feature_names = pd.read_csv(feature_path).iloc[:, 0].tolist()

        # Load class names (optional but recommended)
        self.class_names = [
            "Excellent",
            "Good",
            "Poor",
            "Very Poor",
            "Unsuitable"
        ]

    def predict(self, sample: list):

        # Safety check
        if len(sample) != len(self.feature_names):
            raise ValueError(
                f"Expected {len(self.feature_names)} features, "
                f"but got {len(sample)}"
            )

        # Convert to DataFrame with correct column names
        sample_df = pd.DataFrame([sample], columns=self.feature_names)

        prediction = self.model.predict(sample_df)[0]

        # Decode label if available
        if self.class_names is not None:
            return self.class_names[prediction]
        else:
            return prediction


# ─────────────────────────────────────────────
# TEST RUN
# ─────────────────────────────────────────────
if __name__ == "__main__":

    predictor = WaterQualityPredictor()

    # ⚠️ IMPORTANT:
    # Number of values MUST match selected features count

    sample = [
        7.2,    # pH
        3.0,    # Turbidity (NTU)
        500,    # EC (µS/cm)
        400,    # TDS (mg/L)
        150,    # Hardness (mg/L)
        40,     # Calcium (mg/L)
        30,     # Magnesium (mg/L)
        100,    # Sodium (mg/L)
        10,     # Potassium (mg/L)
        200,    # Chloride (mg/L)
        250,    # Sulfate (mg/L)
        5       # Nitrate (mg/L)
    ]

    result = predictor.predict(sample)

    print("\n==============================")
    print(" STEP 12 — PREDICTION RESULT")
    print("==============================")
    print("Water Quality Status:", result)