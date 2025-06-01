from flask import render_template
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

    produk_narasi = []
    for _, row in rules_produk.iterrows():
        x = frozenset_to_string(row['antecedents'])
        y = frozenset_to_string(row['consequents'])
        confidence_percent = f"{row['confidence']*100:.2f}%"
        support_percent = f"{row['support']*100:.2f}%"

        narasi = (
            f'Jika Produk "{x}" terbeli, maka terdapat kemungkinan sekitar {confidence_percent} '
            f'bahwa Produk "{y}" juga akan terbeli. Produk ini dibeli bersama dalam sekitar {support_percent} '
            f'dari total transaksi. Oleh karena itu, Toko Kasih Ibu disarankan untuk menawarkan promo bundling untuk Produk '
            f'"{x}" bersama Produk "{y}" dan menempatkannya pada rak khusus promo.'
        )
        produk_narasi.append(narasi)

    kategori_narasi = []
    for _, row in rules_kategori.iterrows():
        x = frozenset_to_string(row['antecedents'])
        y = frozenset_to_string(row['consequents'])
        confidence_percent = f"{row['confidence']*100:.2f}%"
        support_percent = f"{row['support']*100:.2f}%"

        narasi = (
            f'Jika Produk pada Kategori Produk "{x}" terbeli, maka terdapat kemungkinan {confidence_percent} '
            f'Produk pada Kategori Produk "{y}" akan terbeli. Produk pada Kategori Produk ini dibeli bersama dalam sekitar '
            f'{support_percent} dari total transaksi. Oleh karena itu, Toko Kasih Ibu disarankan untuk menempatkan rak Kategori Produk '
            f'"{y}" di dekat rak Kategori Produk "{x}".'
        )
        kategori_narasi.append(narasi)

    return render_template(
        "recommendation.html",
        produk_narasi=produk_narasi,
        kategori_narasi=kategori_narasi,
        total_transaksi=total_transaksi
    )
