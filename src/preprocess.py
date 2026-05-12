import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE
import os

# Column name cleaning
def clean_columns(df):
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    return df

# Load and merge multiple CSVs from a folder
def load_dataset(folder_path):
    files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
    if not files:
        raise FileNotFoundError(f"No CSV files found in {folder_path}")
    
    dfs = []
    for f in files:
        path = os.path.join(folder_path, f)
        df = pd.read_csv(path, encoding='utf-8', low_memory=False)
        df = clean_columns(df)
        print(f"Loaded {f}: {df.shape}")
        dfs.append(df)
    
    combined = pd.concat(dfs, ignore_index=True)
    print(f"\nCombined dataset shape: {combined.shape}")
    return combined

# Clean the dataframe
def clean_data(df):
    # Drop duplicates
    before = len(df)
    df = df.drop_duplicates()
    print(f"Dropped {before - len(df)} duplicates")

    # Replace inf values with NaN then drop
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    before = len(df)
    df.dropna(inplace=True)
    print(f"Dropped {before - len(df)} rows with NaN/Inf")

    return df

# Encode the label column
def encode_labels(df, label_col='label'):
    le = LabelEncoder()
    df[label_col] = le.fit_transform(df[label_col])
    print(f"\nLabel classes: {list(le.classes_)}")
    return df, le

# Split features and target
def split_features_target(df, label_col='label'):
    X = df.drop(columns=[label_col])
    y = df[label_col]
    # Keep only numeric columns
    X = X.select_dtypes(include=[np.number])
    return X, y

# Scale features
def scale_features(X_train, X_test):
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    return X_train_scaled, X_test_scaled, scaler

# Apply SMOTE to handle class imbalance
def apply_smote(X_train, y_train):
    print(f"\nBefore SMOTE: {dict(zip(*np.unique(y_train, return_counts=True)))}")
    smote = SMOTE(random_state=42)
    X_res, y_res = smote.fit_resample(X_train, y_train)
    print(f"After SMOTE:  {dict(zip(*np.unique(y_res, return_counts=True)))}")
    return X_res, y_res

# Full pipeline
def preprocess(folder_path, label_col='label', test_size=0.2, use_smote=True):
    df = load_dataset(folder_path)
    df = clean_data(df)
    df, le = encode_labels(df, label_col)
    X, y = split_features_target(df, label_col)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )
    print(f"\nTrain size: {X_train.shape}, Test size: {X_test.shape}")

    if use_smote:
        X_train, y_train = apply_smote(X_train, y_train)

    X_train, X_test, scaler = scale_features(X_train, X_test)

    return X_train, X_test, y_train, y_test, scaler, le