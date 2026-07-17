import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

summary = pd.read_excel("./output/summary.xlsx")
summary["CA"] = summary["price"] * summary["total_sales"]

# print(summary.describe())

# chiffre d'affaires par produit
ca = summary.groupby(by=["product_id", "post_title"])["CA"].sum()
# print(ca)

ca_total = summary["CA"].sum()
# print(ca_total)

# Sort products by revenue (CA) in descending order
ca_sorted = summary.sort_values(by=["CA"], ascending=False)

# Top 20 products by revenue
ca_top20 = ca_sorted.head(20)

# Cumulative sum of CA to apply the 20/80 rule
ca_sorted["CA_cumsum"] = ca_sorted["CA"].cumsum()

# Cumulative percentage of total CA
ca_sorted["CA_cumsum%"] = ca_sorted["CA_cumsum"] * 100 / ca_total

# Products generating 80% of total revenue
df_top80 = ca_sorted[ca_sorted["CA_cumsum%"] <= 80]


# Z-score
# Calculate mean and standard deviation of prices
price_mean = summary["price"].mean()
price_std = summary["price"].std()

# Calculate Z-score for each product
summary["zScore"] = (summary["price"] - price_mean) / price_std

# Extract outliers (Z-score > 3 or < -3)
mask_anomalies = (summary["zScore"] < -3) | (summary["zScore"] > 3)
anomalies = summary[mask_anomalies]

sns.boxplot(data=summary, y="price")
plt.savefig("./output/boxplot_price.png")
# plt.show()

# marges
# Profit margin rate per product
summary["taux_marge"] = (
    (summary["price"] - summary["purchase_price"]) * 100 / summary["price"]
)

# Number of months of stock remaining at current sales rate
summary["mois_stock"] = summary["stock_quantity"] / np.where(
    summary["total_sales"] == 0, 1, summary["total_sales"]
)

print("Ruptures de stock:", (summary["stock_quantity"] == 0).sum())
print("Surstock > 12 mois:", (summary["mois_stock"] > 12).sum())

# Correlation matrix between key indicators
correlations = summary[
    ["price", "purchase_price", "stock_quantity", "total_sales", "CA", "taux_marge"]
].corr()
sns.heatmap(data=correlations, annot=True, fmt=".2f")
plt.savefig("./output/correlations.png")
# plt.show()

with pd.ExcelWriter("./output/rapport.xlsx") as writer:
    summary["CA"].to_excel(writer, sheet_name="CA_par_produit")
    ca_top20.to_excel(writer, sheet_name="Top20")
    df_top80.to_excel(writer, sheet_name="20_80")
    summary[mask_anomalies].to_excel(writer, sheet_name="Anomalies_prix")
    summary[
        [
            "product_id",
            "post_title",
            "stock_quantity",
            "total_sales",
            "taux_marge",
            "mois_stock",
        ]
    ].to_excel(writer, sheet_name="Marges_Stock")
    correlations.to_excel(writer, sheet_name="Correlations")
