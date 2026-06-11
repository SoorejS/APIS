import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def generate_charts():
    csv_file = os.path.join(os.path.dirname(__file__), "eval_results.csv")
    df = pd.read_csv(csv_file)
    
    # Setup
    sns.set_theme(style="darkgrid", context="talk")
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "eval"))
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. Correctness Trend Over Time
    plt.figure(figsize=(12, 6))
    
    # Aggregate by step and system
    # smooth the line
    df['step_bin'] = (df['step'] // 50) * 50
    correctness_trend = df.groupby(['step_bin', 'system'])['correctness'].mean().reset_index()
    
    sns.lineplot(data=correctness_trend, x='step_bin', y='correctness', hue='system', palette=["#ff4a4a", "#22c55e"], linewidth=3)
    plt.axvline(x=750, color='yellow', linestyle='--', linewidth=2, label='Drift Injected')
    
    plt.title('Correctness Degradation & Auto-Healing (N=12,000)')
    plt.xlabel('Simulated Interaction Step')
    plt.ylabel('Correctness Score (0-1)')
    plt.legend(title='System')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "correctness_trend.png"), dpi=150)
    plt.close()
    
    # 2. Hallucination Comparison (Post-Drift)
    plt.figure(figsize=(8, 6))
    post_drift = df[df['step'] >= 750]
    sns.barplot(data=post_drift, x='system', y='hallucination', hue='system', palette=["#ff4a4a", "#22c55e"])
    plt.title('Avg Hallucination Rate Post-Drift')
    plt.ylabel('Hallucination Probability')
    plt.xlabel('')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "hallucination_comparison.png"), dpi=150)
    plt.close()
    
    # 3. Thumbs Down Reduction
    plt.figure(figsize=(8, 6))
    sns.barplot(data=post_drift, x='system', y='thumbs_down', hue='system', palette=["#ff4a4a", "#22c55e"])
    plt.title('Thumbs Down Rate Post-Drift')
    plt.ylabel('Probability of User Thumbs Down')
    plt.xlabel('')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "thumbs_down_reduction.png"), dpi=150)
    plt.close()
    
    # 4. Latency Comparison
    plt.figure(figsize=(8, 6))
    sns.boxplot(data=post_drift, x='system', y='latency_ms', hue='system', palette=["#ff4a4a", "#22c55e"])
    plt.title('Latency Distribution Post-Drift')
    plt.ylabel('Latency (ms)')
    plt.xlabel('')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "latency_comparison.png"), dpi=150)
    plt.close()

    print(f"Evaluation charts successfully saved to {out_dir}")

if __name__ == "__main__":
    generate_charts()
