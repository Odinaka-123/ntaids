# NTA-IDS: Network Traffic Analysis for Intrusion Detection

A hybrid machine learning-based Intrusion Detection System that analyzes network traffic flows to detect intrusions in real time.

**Final year project — Computer Science, 400L**

## Overview

This system combines Random Forest, SVM, and LSTM models in an ensemble to detect:
- DDoS attacks
- Port scanning
- Malware transfers
- Zero-day exploits

It uses flow-based analysis (NetFlow/IPFIX) without deep packet inspection, preserving user privacy.

## Architecture
Raw Traffic (NetFlow/IPFIX)
↓
Feature Extraction (statistical + behavioural)
↓
Dimensionality Reduction (PCA + Autoencoder)
↓
Ensemble Classifier (RF + SVM + LSTM)
↓
Intrusion Alert / Benign
## Datasets

- [CICIDS2017](https://www.unb.ca/cic/datasets/ids-2017.html) — Canadian Institute for Cybersecurity
- [UNSW-NB15](https://research.unsw.edu.au/projects/unsw-nb15-dataset) — University of New South Wales

Download the CSVs and place them in `data/raw/cicids2017/` and `data/raw/unsw/` respectively.

## Setup

```bash
# Requires Python 3.11
py -3.11 -m venv venv
venv\Scripts\activate        # Windows
source venv/Scripts/activate # Git Bash

pip install -r requirements.txt
```

## Usage

Open and run `notebooks/01_main_pipeline.ipynb` cell by cell after placing datasets in `data/raw/`.

## Project Structure
ntaids/
├── data/              # Datasets (not tracked by git)
├── notebooks/         # Main pipeline notebook
├── src/
│   ├── preprocess.py  # Data loading, cleaning, SMOTE
│   ├── features.py    # Feature selection and engineering
│   ├── dimensionality.py  # PCA and autoencoder
│   ├── ensemble.py    # Voting ensemble
│   ├── evaluate.py    # Metrics and plots
│   └── models/
│       ├── random_forest.py
│       ├── svm.py
│       └── lstm.py
├── results/           # Saved models and plots
└── app/               # Streamlit dashboard
## Models

| Model | Role |
|---|---|
| Random Forest | High accuracy, feature importance |
| SVM | Strong on high-dimensional data |
| LSTM | Temporal/sequential pattern detection |
| Ensemble | Combined weighted voting |

## Metrics

Evaluated on accuracy, F1-score, precision, recall, and false-positive rate.