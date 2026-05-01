"""
Crop Predictor Service — XGBoost-based crop recommendation engine.
Trained on REAL dataset: 'Crop recommendation dataset.csv' (57,000 rows, 57 crops).
Provides proper accuracy metrics, classification report, and feature importance.
"""
import os
import numpy as np
import pandas as pd
import joblib
import json
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import xgboost as xgb


class CropPredictor:
    """XGBoost classifier for crop recommendation trained on real agronomic data."""

    # Column mapping from dataset → model features
    DATASET_COLUMNS = {
        "N": "N",
        "P": "P",
        "K": "K",
        "TEMP": "temperature",
        "RELATIVE_HUMIDITY": "humidity",
        "SOIL_PH": "ph",
        "WATERREQUIRED": "rainfall",
    }

    FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
    LABEL_COL = "CROPS"

    def __init__(self, model_path: str, label_encoder_path: str):
        self.model_path = model_path
        self.label_encoder_path = label_encoder_path
        self.metrics_path = os.path.join(os.path.dirname(model_path), "training_metrics.json")
        self.model = None
        self.label_encoder = None
        self.training_metrics = None
        self._load_or_train()

    def _load_or_train(self):
        """Load saved model or train from real dataset."""
        if (os.path.exists(self.model_path)
                and os.path.exists(self.label_encoder_path)
                and os.path.exists(self.metrics_path)):
            print("[CropPredictor] Loading saved model...")
            self.model = joblib.load(self.model_path)
            self.label_encoder = joblib.load(self.label_encoder_path)
            with open(self.metrics_path, "r") as f:
                self.training_metrics = json.load(f)
            print(f"[CropPredictor] Model loaded — "
                  f"Test Accuracy: {self.training_metrics['test_accuracy']:.2%}")
        else:
            print("[CropPredictor] Training on real dataset...")
            self._train_on_real_data()

    def _get_dataset_path(self) -> str:
        """Locate the real dataset CSV file."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        csv_path = os.path.join(base_dir, "dataset", "Crop recommendation dataset.csv")
        if os.path.exists(csv_path):
            return csv_path
        raise FileNotFoundError(
            f"Dataset not found at {csv_path}. "
            "Please place 'Crop recommendation dataset.csv' in the 'dataset/' directory."
        )

    def _train_on_real_data(self):
        """Train XGBoost on the real Crop Recommendation dataset with proper evaluation."""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)

        # ─── Load Real Dataset ─────────────────────────────────────
        dataset_path = self._get_dataset_path()
        df = pd.read_csv(dataset_path)
        print(f"[CropPredictor] Loaded dataset: {df.shape[0]} rows, "
              f"{df[self.LABEL_COL].nunique()} crops")

        # ─── Prepare Features ──────────────────────────────────────
        feature_df = pd.DataFrame()
        for src_col, tgt_col in self.DATASET_COLUMNS.items():
            feature_df[tgt_col] = df[src_col].astype(float)

        X = feature_df[self.FEATURES].values
        self.label_encoder = LabelEncoder()
        y = self.label_encoder.fit_transform(df[self.LABEL_COL])

        # ─── Train/Test Split (80/20, stratified) ──────────────────
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        print(f"[CropPredictor] Train: {len(X_train)} samples | "
              f"Test: {len(X_test)} samples")

        # ─── Train XGBoost ─────────────────────────────────────────
        num_classes = len(self.label_encoder.classes_)
        self.model = xgb.XGBClassifier(
            n_estimators=300,
            max_depth=8,
            learning_rate=0.1,
            objective="multi:softprob",
            num_class=num_classes,
            eval_metric="mlogloss",
            random_state=42,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=3,
        )

        self.model.fit(
            X_train, y_train,
            eval_set=[(X_train, y_train), (X_test, y_test)],
            verbose=True,
        )

        # ─── Evaluate ─────────────────────────────────────────────
        y_pred = self.model.predict(X_test)
        test_accuracy = accuracy_score(y_test, y_pred)
        train_accuracy = accuracy_score(y_train, self.model.predict(X_train))

        report = classification_report(
            y_test, y_pred,
            target_names=self.label_encoder.classes_,
            output_dict=True,
        )

        # ─── Feature Importance ────────────────────────────────────
        importance_raw = self.model.feature_importances_
        importance_sum = importance_raw.sum()
        feature_importance = {}
        for i, feat in enumerate(self.FEATURES):
            feature_importance[feat] = round(
                float(importance_raw[i] / importance_sum) * 100, 2
            )

        # ─── Save Metrics ─────────────────────────────────────────
        self.training_metrics = {
            "dataset_path": dataset_path,
            "dataset_rows": int(df.shape[0]),
            "num_crops": int(num_classes),
            "crop_names": list(self.label_encoder.classes_),
            "train_samples": int(len(X_train)),
            "test_samples": int(len(X_test)),
            "train_accuracy": float(train_accuracy),
            "test_accuracy": float(test_accuracy),
            "feature_importance": feature_importance,
            "per_crop_f1": {
                crop: round(report[crop]["f1-score"], 4)
                for crop in self.label_encoder.classes_
                if crop in report
            },
            "macro_f1": round(report["macro avg"]["f1-score"], 4),
            "weighted_f1": round(report["weighted avg"]["f1-score"], 4),
        }

        with open(self.metrics_path, "w") as f:
            json.dump(self.training_metrics, f, indent=2)

        # ─── Print Report ──────────────────────────────────────────
        print("\n" + "=" * 60)
        print("  XGBoost TRAINING REPORT")
        print("=" * 60)
        print(f"  Dataset:          {dataset_path}")
        print(f"  Total Samples:    {df.shape[0]}")
        print(f"  Crops:            {num_classes}")
        print(f"  Train Accuracy:   {train_accuracy:.4%}")
        print(f"  Test Accuracy:    {test_accuracy:.4%}")
        print(f"  Macro F1:         {report['macro avg']['f1-score']:.4f}")
        print(f"  Weighted F1:      {report['weighted avg']['f1-score']:.4f}")
        print("-" * 60)
        print("  Feature Importance:")
        for feat, imp in sorted(feature_importance.items(),
                                key=lambda x: x[1], reverse=True):
            bar = "#" * int(imp / 2)
            print(f"    {feat:>15s}: {imp:>6.2f}%  {bar}")
        print("=" * 60 + "\n")

        # ─── Save Model ───────────────────────────────────────────
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.label_encoder, self.label_encoder_path)
        print(f"[CropPredictor] Model saved to {self.model_path}")
        print(f"[CropPredictor] Metrics saved to {self.metrics_path}")

    def predict(self, data: dict) -> dict:
        """
        Generate top-5 crop predictions with confidence scores and
        feature importance from the REAL trained model.

        Input: {"N": 90, "P": 42, "K": 43, "temperature": 24.8, ...}
        Returns: {
            "top_crops": [{"crop": str, "confidence": float}, ...],
            "feature_importance": {feature: percentage, ...},
            "training_metrics": {accuracy, f1, etc.}
        }
        """
        features = np.array([[
            float(data[f]) for f in self.FEATURES
        ]])

        probabilities = self.model.predict_proba(features)[0]
        top_indices = np.argsort(probabilities)[::-1][:5]

        top_crops = []
        for idx in top_indices:
            crop_name = self.label_encoder.inverse_transform([idx])[0]
            confidence = round(float(probabilities[idx]) * 100, 1)
            top_crops.append({"crop": crop_name, "confidence": confidence})

        # Feature importance from the trained model
        importance_raw = self.model.feature_importances_
        importance_sum = importance_raw.sum()
        feature_importance = {}
        for i, feat in enumerate(self.FEATURES):
            feature_importance[feat] = round(
                float(importance_raw[i] / importance_sum) * 100, 2
            )

        return {
            "top_crops": top_crops,
            "feature_importance": feature_importance,
            "training_metrics": {
                "test_accuracy": self.training_metrics["test_accuracy"],
                "macro_f1": self.training_metrics["macro_f1"],
                "weighted_f1": self.training_metrics["weighted_f1"],
                "dataset_rows": self.training_metrics["dataset_rows"],
                "num_crops": self.training_metrics["num_crops"],
            },
        }

    def get_metrics(self) -> dict:
        """Return full training metrics for the Research Mode UI."""
        return self.training_metrics
