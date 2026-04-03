import pickle

with open("model.pkl", "rb") as f:
    bundle = pickle.load(f)

enc = bundle["feature_encoder"]
print(f"Expected dimensions: {enc._dim}")
print(f"\nAll feature columns ({enc._dim} total):")
# Get feature names from the encoder
import pandas as pd
# Reconstruct feature names from training
print("Categorical cols:", bundle["categorical_variables"])
print("\nTrying to get all column names...")
# The encoder stores the feature names
if hasattr(enc, 'feature_names_in_'):
    print("Feature names:", list(enc.feature_names_in_))
elif hasattr(enc, 'cols'):
    print("Encoder cols:", enc.cols)