import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


def read_files():
    erp = pd.read_excel("./data/erp.xlsx")
    liaison = pd.read_excel("./data/liaison.xlsx")
    web = pd.read_excel("./data/web.xlsx")

    return erp, web, liaison


erp, web, liaison = read_files()

df_errors = pd.DataFrame(
    columns=[
        "id_erreur",
        "table_source",
        "colonne",
        "valeur",
        "type_erreur",
        "index_original",
    ]
)

df_temp = pd.DataFrame(
    {
        "table_source": "erp",
        "colonne": "price",
        "valeur": erp[erp["price"] < 0]["price"],
        "type_erreur": "Valeurs négatives dans price",
        "index_original": erp[erp["price"] < 0].index,
    }
)
df_errors = pd.concat([df_errors, df_temp])

df_temp = pd.DataFrame(
    {
        "table_source": "erp",
        "colonne": "price",
        "valeur": erp[erp["purchase_price"] > erp["price"]]["price"],
        "type_erreur": "vente à perte",
        "index_original": erp[erp["purchase_price"] > erp["price"]].index,
    }
)

df_errors = pd.concat([df_errors, df_temp])

df_temp = pd.DataFrame(
    {
        "table_source": "erp",
        "colonne": "stock_quantity",
        "valeur": erp[erp["stock_quantity"] < 0]["stock_quantity"],
        "type_erreur": "Valeurs négatives dans stock_quantity",
        "index_original": erp[erp["stock_quantity"] < 0].index,
    }
)

df_errors = pd.concat([df_errors, df_temp])

mask_stock_status = (erp["stock_status"] == "instock") & (erp["stock_quantity"] == 0)
df_temp = pd.DataFrame(
    {
        "table_source": "erp",
        "colonne": "stock_status",
        "valeur": erp[mask_stock_status]["stock_status"],
        "type_erreur": "incohérence stock_status",
        "index_original": erp[mask_stock_status].index,
    }
)

df_errors = pd.concat([df_errors, df_temp])

mask_all_errors_erp = (
    (erp["price"] < 0)
    | (erp["stock_quantity"] < 0)
    | (erp["purchase_price"] > erp["price"])
)

erp_clean = erp[~mask_all_errors_erp]
erp_clean["stock_status"] = np.where(
    erp_clean["stock_quantity"] == 0, "outofstock", "instock"
)

# print(erp_clean.describe())

liaison_clean = liaison[~liaison["id_web"].isna()]

# print(liaison_clean.describe())

web_clean1 = web[~web["sku"].isna()]

web_clean2 = web_clean1.dropna(axis=1, how="all")  # empty columns

mask_web_err = web_clean2["total_sales"] < 0
df_temp = pd.DataFrame(
    {
        "table_source": "web",
        "colonne": "total_sales",
        "valeur": web_clean2[mask_web_err]["total_sales"],
        "type_erreur": "Valeurs négatives dans total_sales",
        "index_original": web_clean2[mask_web_err].index,
    }
)

df_errors = pd.concat([df_errors, df_temp])
df_errors = df_errors.reset_index(drop=True)
df_errors["id_erreur"] = df_errors.index + 1
df_errors.to_excel("./output/erreurs.xlsx", index=False)

web_clean3 = web_clean2[~mask_web_err]


web_clean = web_clean3[web_clean3["post_type"] == "product"]

# print(web_clean.describe())

df_summary1 = pd.merge(
    erp_clean, liaison_clean, left_on="product_id", right_on="product_id", how="inner"
)
df_summary = pd.merge(
    df_summary1, web_clean, left_on="id_web", right_on="sku", how="inner"
)

# print(df_summary.shape)
# print(df_summary.columns.tolist())
# print(web_clean[web_clean["sku"].astype(str).str.contains("cadeau|13127|14680")])

mask_sku_numerique = df_summary["sku"].astype(str).str.isnumeric()
df_summary_clean = df_summary[mask_sku_numerique]

# print(
#     df_summary_clean[
#         df_summary_clean["sku"].astype(str).str.contains("cadeau|13127|14680")
#     ]
# )
df_summary_clean.to_excel("./output/summary.xlsx", index=False)


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
