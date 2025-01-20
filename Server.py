import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# 正交表 (L9 示例)
data = {
    "Experiment": [1, 2, 3, 4, 5, 6, 7, 8, 9],
    "P1 (Speed)": [1050, 1050, 1050, 950, 950, 950, 850, 850, 850],
    "P2 (Power)": [120, 150, 180, 120, 150, 180, 120, 150, 180],
    "P3 (Gap)": [0.08, 0.1, 0.12, 0.1, 0.12, 0.08, 0.12, 0.08, 0.1],
    "P4 (Material)": [1, 2, 3, 3, 1, 2, 2, 3, 1],
    "Result": [15.2, 18.5, 17.1, 14.3, 16.8, 15.7, 13.9, 15.5, 14.8],  # 測試結果
}

# 將正交表數據轉為 DataFrame
df = pd.DataFrame(data)

# 計算 S/N 比 (Larger is Better)
def calculate_sn_ratio(results):
    return -10 * np.log10(np.mean(1 / np.square(results)))

df["S/N Ratio"] = df["Result"].apply(lambda x: calculate_sn_ratio([x]))

# 輸出 DataFrame
print("正交表與 S/N 比：")
print(df)

# 分析主效應
factors = ["P1 (Speed)", "P2 (Power)", "P3 (Gap)", "P4 (Material)"]
factor_levels = {factor: sorted(df[factor].unique()) for factor in factors}

sn_averages = {}
for factor in factors:
    sn_averages[factor] = []
    for level in factor_levels[factor]:
        avg_sn = df[df[factor] == level]["S/N Ratio"].mean()
        sn_averages[factor].append(avg_sn)

# 繪製主效應圖
plt.figure(figsize=(12, 8))
for i, (factor, levels) in enumerate(factor_levels.items()):
    plt.subplot(2, 2, i + 1)
    plt.plot(levels, sn_averages[factor], marker='o')
    plt.title(f"Main Effect of {factor}")
    plt.xlabel("Levels")
    plt.ylabel("S/N Ratio")
    plt.grid()

plt.tight_layout()
plt.show()

# 找出最佳條件
optimal_levels = {factor: levels[np.argmax(sn_averages[factor])] for factor, levels in factor_levels.items()}
print("\n最佳參數組合：")
for factor, level in optimal_levels.items():
    print(f"{factor}: {level}")
