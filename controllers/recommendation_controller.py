from flask import render_template
from markupsafe import Markup
import global_var

def recommendation():
    rules_produk = global_var.rules_produk
    rules_kategori = global_var.rules_kategori
    total_transaksi = global_var.total_transaksi

    if rules_produk is None or rules_kategori is None:
        return "Model belum dijalankan."

    def clean_item(item):
        return item.replace('PRODUK_', '').replace('KATEGORI_', '')

    def frozenset_to_string(fs):
        return ', '.join([clean_item(i) for i in fs])

    def highlight(text):
        return Markup(f"<strong>{text}</strong>")

    produk_narasi = []
    for _, row in rules_produk.iterrows():
        x = frozenset_to_string(row['antecedents'])
        y = frozenset_to_string(row['consequents'])
        confidence_percent = f"{row['confidence']*100:.2f}%"
        support_percent = f"{row['support']*100:.2f}%"

        x_highlight = highlight(f'"{x}"')
        y_highlight = highlight(f'"{y}"')
        confidence_highlight = highlight(confidence_percent)
        support_highlight = highlight(support_percent)

        narasi = (
            f"Jika Produk {x_highlight} terbeli, maka terdapat kemungkinan sekitar {confidence_highlight} "
            f"bahwa Produk {y_highlight} juga akan terbeli. Produk ini dibeli bersama dalam sekitar {support_highlight} "
            f"dari total transaksi. Oleh karena itu, Toko Kasih Ibu disarankan untuk menawarkan promo bundling untuk Produk "
            f"{x_highlight} bersama Produk {y_highlight} dan menempatkannya pada rak khusus promo."
        )
        produk_narasi.append(narasi)

    kategori_narasi = []
    for _, row in rules_kategori.iterrows():
        x = frozenset_to_string(row['antecedents'])
        y = frozenset_to_string(row['consequents'])
        confidence_percent = f"{row['confidence']*100:.2f}%"
        support_percent = f"{row['support']*100:.2f}%"

        x_highlight = highlight(f'"{x}"')
        y_highlight = highlight(f'"{y}"')
        confidence_highlight = highlight(confidence_percent)
        support_highlight = highlight(support_percent)

        narasi = (
            f"Jika Produk pada Kategori Produk {x_highlight} terbeli, maka terdapat kemungkinan {confidence_highlight} "
            f"Produk pada Kategori Produk {y_highlight} akan terbeli. Produk pada Kategori Produk ini dibeli bersama dalam sekitar "
            f"{support_highlight} dari total transaksi. Oleh karena itu, Toko Kasih Ibu disarankan untuk menempatkan rak Kategori Produk "
            f"{y_highlight} di dekat rak Kategori Produk {x_highlight}."
        )
        kategori_narasi.append(narasi)

    return render_template(
        "recommendation.html",
        produk_narasi=produk_narasi,
        kategori_narasi=kategori_narasi,
        total_transaksi=total_transaksi
    )
