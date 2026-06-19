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

print(erp_clean)


# print("web_dupl_sku:", web["sku"].duplicated().sum())
# print("web_dupl:", web.duplicated().sum())
# print("web_nan:", web.isna().sum())

# print("liaison_dupl_id:", liaison["product_id"].duplicated().sum())
# print("liaison_dupl:", liaison.duplicated().sum())
# print("liaison_nan:", liaison.isna().sum())
