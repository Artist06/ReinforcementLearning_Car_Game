import os
import pandas as pd
from collections import Counter
import numpy as np

def merge_and_balance_replay_buffers(output_file="merged_replay_buffer.csv", min_entries=10000):
    """
    Merge all replay_buffer_*.csv files in the current directory and balance the actions.
    Ensure the dataset has at least `min_entries` rows by oversampling minority actions if needed.
    :param output_file: Name of the output file to save the merged and balanced replay buffer.
    :param min_entries: Minimum number of entries in the final replay buffer.
    """
    # Get all replay_buffer_*.csv files in the current directory
    replay_buffer_files = [
        file for file in os.listdir() if file.startswith("replay_buffer_") and file.endswith(".csv")
    ]

    if not replay_buffer_files:
        print("No replay buffer files found in the current directory.")
        return

    # Merge all replay buffer files
    dataframes = []
    for file in replay_buffer_files:
        print(f"Loading {file}...")
        df = pd.read_csv(file)
        dataframes.append(df)

    merged_df = pd.concat(dataframes, ignore_index=True)
    print(f"Merged {len(replay_buffer_files)} files with a total of {len(merged_df)} rows.")

    # Balance the actions by undersampling the majority class
    action_counts = Counter(merged_df["Action"])
    print(f"Action counts before balancing: {action_counts}")

    # Find the maximum number of samples to keep for each action
    max_samples_per_action = min(action_counts.values())  # Use the smallest class size for balancing

    balanced_dfs = []
    for action, count in action_counts.items():
        action_df = merged_df[merged_df["Action"] == action]
        if count > max_samples_per_action:
            # Undersample the majority class
            balanced_dfs.append(action_df.sample(n=max_samples_per_action, random_state=42))
        else:
            # Keep all samples for minority classes
            balanced_dfs.append(action_df)

    balanced_df = pd.concat(balanced_dfs, ignore_index=True)
    print(f"Balanced dataset after undersampling has {len(balanced_df)} rows.")
    print(f"Action counts after undersampling: {Counter(balanced_df['Action'])}")

    # Oversample to reach the minimum number of entries if needed
    total_entries = len(balanced_df)
    if total_entries < min_entries:
        print(f"Dataset has {total_entries} entries, oversampling to reach {min_entries} entries...")
        oversample_factor = min_entries // total_entries + 1
        oversampled_df = pd.concat([balanced_df] * oversample_factor, ignore_index=True)
        oversampled_df = oversampled_df.sample(n=min_entries, random_state=42)  # Trim to exact size
        balanced_df = oversampled_df

    print(f"Final dataset has {len(balanced_df)} rows.")
    print(f"Action counts after oversampling: {Counter(balanced_df['Action'])}")

    # Save the balanced dataset to a new CSV file
    balanced_df.to_csv(output_file, index=False)
    print(f"Balanced replay buffer saved to {output_file}")


if __name__ == "__main__":
    merge_and_balance_replay_buffers()