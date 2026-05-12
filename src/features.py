import pandas as pd
import numpy as np

# These are the most important flow-based features for NTA-IDS
# Based on CICIDS2017 and UNSW-NB15 feature sets

SELECTED_FEATURES = [
    # Flow duration and volume
    'flow_duration',
    'total_fwd_packets',
    'total_backward_packets',
    'total_length_of_fwd_packets',
    'total_length_of_bwd_packets',

    # Packet length stats
    'fwd_packet_length_max',
    'fwd_packet_length_min',
    'fwd_packet_length_mean',
    'fwd_packet_length_std',
    'bwd_packet_length_max',
    'bwd_packet_length_min',
    'bwd_packet_length_mean',
    'bwd_packet_length_std',

    # Flow rates
    'flow_bytes/s',
    'flow_packets/s',

    # Inter-arrival times
    'flow_iat_mean',
    'flow_iat_std',
    'flow_iat_max',
    'flow_iat_min',
    'fwd_iat_total',
    'fwd_iat_mean',
    'fwd_iat_std',
    'fwd_iat_max',
    'fwd_iat_min',
    'bwd_iat_total',
    'bwd_iat_mean',
    'bwd_iat_std',
    'bwd_iat_max',
    'bwd_iat_min',

    # TCP flags
    'fwd_psh_flags',
    'bwd_psh_flags',
    'fwd_urg_flags',
    'bwd_urg_flags',
    'fin_flag_count',
    'syn_flag_count',
    'rst_flag_count',
    'psh_flag_count',
    'ack_flag_count',
    'urg_flag_count',

    # Window sizes and header lengths
    'fwd_header_length',
    'bwd_header_length',
    'fwd_packets/s',
    'bwd_packets/s',
    'min_packet_length',
    'max_packet_length',
    'packet_length_mean',
    'packet_length_std',
    'packet_length_variance',

    # Active/idle times
    'active_mean',
    'active_std',
    'active_max',
    'active_min',
    'idle_mean',
    'idle_std',
    'idle_max',
    'idle_min',
]


def select_features(df, label_col='label'):
    """Keep only available features from SELECTED_FEATURES plus the label."""
    available = [f for f in SELECTED_FEATURES if f in df.columns]
    missing = [f for f in SELECTED_FEATURES if f not in df.columns]

    if missing:
        print(f"Warning: {len(missing)} features not found in dataset, skipping them.")

    print(f"Using {len(available)} features out of {len(SELECTED_FEATURES)} defined.")
    cols = available + ([label_col] if label_col in df.columns else [])
    return df[cols]


def engineer_features(df):
    """Add a few derived features that help distinguish attack patterns."""

    # Ratio of forward to backward packets (asymmetry = sign of scan/DDoS)
    df = df.copy()
    fwd = 'total_fwd_packets'
    bwd = 'total_backward_packets'
    if fwd in df.columns and bwd in df.columns:
        df['fwd_bwd_packet_ratio'] = df[fwd] / (df[bwd] + 1e-6)

    # Ratio of forward to backward bytes
    fwd_b = 'total_length_of_fwd_packets'
    bwd_b = 'total_length_of_bwd_packets'
    if fwd_b in df.columns and bwd_b in df.columns:
        df['fwd_bwd_byte_ratio'] = df[fwd_b] / (df[bwd_b] + 1e-6)

    # Packet length coefficient of variation
    mean_col = 'packet_length_mean'
    std_col  = 'packet_length_std'
    if mean_col in df.columns and std_col in df.columns:
        df['packet_length_cv'] = df[std_col] / (df[mean_col] + 1e-6)

    # Flag density (total flags per packet)
    flag_cols = [c for c in df.columns if 'flag' in c]
    pkt_col   = 'total_fwd_packets'
    if flag_cols and pkt_col in df.columns:
        df['flag_density'] = df[flag_cols].sum(axis=1) / (df[pkt_col] + 1e-6)

    print(f"Feature engineering done. New shape: {df.shape}")
    return df


def get_feature_names(df, label_col='label'):
    """Return list of feature column names (excludes label)."""
    return [c for c in df.columns if c != label_col]