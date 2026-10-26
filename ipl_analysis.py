
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# IPL Cricket Data Analysis and Visualization
# Sample data for educational demonstration

data = {
    "Team": [
        "CSK", "MI", "RCB", "KKR", "CSK",
        "MI", "RCB", "KKR", "CSK", "MI",
        "SRH", "RR", "RCB", "CSK", "KKR"
    ],
    "Season": [
        2022, 2022, 2022, 2022, 2023,
        2023, 2023, 2023, 2024, 2024,
        2024, 2024, 2025, 2025, 2025
    ],
    "Runs": [
        180, 165, 195, 172, 190,
        175, 205, 160, 185, 200,
        178, 188, 210, 170, 195
    ],
    "Wickets": [
        7, 5, 8, 6, 9, 4, 7, 5, 6, 8,
        5, 7, 9, 4, 6
    ],
    "Winner": [
        "CSK", "MI", "RCB", "KKR", "CSK",
        "MI", "RCB", "KKR", "CSK", "MI",
        "SRH", "RR", "RCB", "CSK", "KKR"
    ]
}

# Convert data into a DataFrame
df = pd.DataFrame(data)

# Display IPL dataset
print("\n===== IPL CRICKET DATASET =====")
print(df.to_string(index=False))

# Basic statistical analysis
print("\n===== STATISTICAL ANALYSIS =====")
print("Total Records:", len(df))
print("Average Runs:", np.mean(df["Runs"]))
print("Highest Runs:", np.max(df["Runs"]))
print("Lowest Runs:", np.min(df["Runs"]))
print("Average Wickets:", round(np.mean(df["Wickets"]), 2))

# Team-wise wins
team_wins = df["Winner"].value_counts()

print("\n===== TEAM-WISE WINS =====")
print(team_wins.to_string())

# Top 5 high-scoring records
print("\n===== TOP 5 HIGH-SCORING RECORDS =====")
print(
    df.nlargest(5, "Runs")[
        ["Team", "Season", "Runs", "Wickets"]
    ].to_string(index=False)
)

# Set visualization style
sns.set_theme(style="whitegrid")

# Graph 1: Team Wins Analysis
plt.figure(figsize=(9, 5))
sns.barplot(x=team_wins.index, y=team_wins.values)
plt.title("IPL Team Wins Analysis")
plt.xlabel("Team")
plt.ylabel("Number of Wins")
plt.tight_layout()
plt.savefig("team_wins.png")
plt.show()

# Graph 2: Average Runs by Season
season_runs = df.groupby("Season")["Runs"].mean()

plt.figure(figsize=(9, 5))
plt.plot(
    season_runs.index,
    season_runs.values,
    marker="o",
    linewidth=2
)
plt.title("Average Runs by Season")
plt.xlabel("Season")
plt.ylabel("Average Runs")
plt.grid(True)
plt.tight_layout()
plt.savefig("season_runs.png")
plt.show()

# Graph 3: Runs Distribution
plt.figure(figsize=(9, 5))
sns.histplot(df["Runs"], bins=7, kde=True)
plt.title("Distribution of Runs")
plt.xlabel("Runs")
plt.ylabel("Frequency")
plt.tight_layout()
plt.savefig("runs_distribution.png")
plt.show()

# Graph 4: Correlation Heatmap
plt.figure(figsize=(7, 5))
correlation = df[["Runs", "Wickets", "Season"]].corr()

sns.heatmap(
    correlation,
    annot=True,
    cmap="coolwarm",
    fmt=".2f"
)
plt.title("IPL Data Correlation Heatmap")
plt.tight_layout()
plt.savefig("correlation_heatmap.png")
plt.show()

print("\nAnalysis completed successfully!")
print("All graphs have been saved in the project folder.")
