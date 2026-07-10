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

ca_sorted = summary.sort_values(by=["CA"], ascending=False)
# print(ca_sorted)

# top 20-80
ca_top20 = ca_sorted.head(20)

ca_sorted["CA_cumsum"] = ca_sorted["CA"].cumsum()
ca_sorted["CA_cumsum%"] = ca_sorted["CA_cumsum"] * 100 / ca_total


df_top80 = ca_sorted[ca_sorted["CA_cumsum%"] <= 80]
# print(df_top80)

# Z-score
price_mean = summary["price"].mean()
price_std = summary["price"].std()
summary["zScore"] = (summary["price"] - price_mean) / price_std
mask_anomalies = (summary["zScore"] < -3) | (summary["zScore"] > 3)
# print(summary[mask_anomalies])

sns.boxplot(data=summary, y="price")
plt.savefig("./output/boxplot_price.png")
# plt.show()

# marges
summary["taux_marge"] = (
    (summary["price"] - summary["purchase_price"]) * 100 / summary["price"]
)
# print(summary["taux_marge"])

summary["mois_stock"] = summary["stock_quantity"] / np.where(
    summary["total_sales"] == 0, 1, summary["total_sales"]
)


correlations = summary[
    ["price", "purchase_price", "stock_quantity", "total_sales", "CA", "taux_marge"]
].corr()
# print(correlations)


with pd.ExcelWriter("./output/rapport.xlsx") as writer:
    summary["CA"].to_excel(writer, sheet_name="CA_par_produit")
    ca_top20.to_excel(writer, sheet_name="Top20")
    df_top80.to_excel(writer, sheet_name="20_80")
    summary[mask_anomalies].to_excel(writer, sheet_name="Anomalies_prix")
    summary["taux_marge"].to_excel(writer, sheet_name="Marges")
    correlations.to_excel(writer, sheet_name="Correlations")

sns.heatmap(data=correlations, annot=True, fmt=".2f")
plt.savefig("./output/correlations.png")
# plt.show()
