from flask import render_template, flash, redirect, url_for
import global_var

def clean_item(item):
    return item.replace('PRODUK_', '').replace('KATEGORI_', '')

def output():
    # Ambil rules dari global_var
    rules_produk = global_var.rules_produk
    rules_kategori = global_var.rules_kategori
    total_transaksi = global_var.total_transaksi

    # Cek apakah rules sudah ada / sudah dijalankan
    if rules_produk is None or rules_kategori is None:
        flash("Model belum dijalankan. Silakan jalankan model terlebih dahulu.", "warning")
        return redirect(url_for('route_association'))

    # Pilih kolom yang ingin ditampilkan
    rules_produk_display = rules_produk[['antecedents', 'consequents', 'support', 'confidence', 'lift']].copy()
    rules_kategori_display = rules_kategori[['antecedents', 'consequents', 'support', 'confidence', 'lift']].copy()

    # Ubah frozenset ke string dan hapus prefix agar mudah dibaca
    for df in [rules_produk_display, rules_kategori_display]:
        df['antecedents'] = df['antecedents'].apply(lambda x: ', '.join([clean_item(i) for i in list(x)]))
        df['consequents'] = df['consequents'].apply(lambda x: ', '.join([clean_item(i) for i in list(x)]))

    return render_template(
        "output.html",
        rules_produk=rules_produk_display.to_dict(orient='records'),
        rules_kategori=rules_kategori_display.to_dict(orient='records'),
        total_transaksi=total_transaksi
    )
