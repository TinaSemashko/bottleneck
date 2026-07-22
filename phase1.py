import numpy as np
import pandas as pd


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

# images duplicates
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

df_summary_clean.to_excel("./output/summary.xlsx", index=False)
