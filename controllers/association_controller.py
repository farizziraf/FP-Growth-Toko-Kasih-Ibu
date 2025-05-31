import os
import datetime
import pandas as pd
from flask import render_template, session, abort, request, flash, redirect, url_for
from mlxtend.frequent_patterns import fpgrowth, association_rules
import global_var  # import modul global_var

# Fungsi bantu parsing tanggal
def parse_date_ddmmyyyy(date_str):
    if not date_str:
        return None
    try:
        return datetime.datetime.strptime(date_str, '%d/%m/%Y')
    except ValueError:
        return None

# Fungsi utama untuk load dan filter data
def association():
    file_path = session.get('uploaded_file', None)

    if not file_path or not os.path.exists(file_path):
        abort(400, description="No file uploaded or file not found")

    try:
        if file_path.lower().endswith('.xlsx'):
            df = pd.read_excel(file_path)
        elif file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path, sep=';')
        else:
            abort(400, description="Unsupported file format. Use .xlsx or .csv")
    except Exception as e:
        abort(500, description=f"Failed to read file: {e}")

    # Kolom tanggal
    date_col = 'TG_JUAL'
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

    # Ambil filter tanggal dari parameter request
    f1_start = parse_date_ddmmyyyy(request.args.get('f1_start'))
    f1_due = parse_date_ddmmyyyy(request.args.get('f1_due'))
    f2_start = parse_date_ddmmyyyy(request.args.get('f2_start'))
    f2_due = parse_date_ddmmyyyy(request.args.get('f2_due'))
    f3_start = parse_date_ddmmyyyy(request.args.get('f3_start'))
    f3_due = parse_date_ddmmyyyy(request.args.get('f3_due'))

    def filter_date_range(df, col, start, due):
        if start:
            df = df[df[col] >= start]
        if due:
            df = df[df[col] <= due]
        return df

    # Filter data berdasarkan tanggal jika ada
    if any([f1_start, f1_due, f2_start, f2_due, f3_start, f3_due]):
        filtered_dfs = []
        if f1_start or f1_due:
            filtered_dfs.append(filter_date_range(df, date_col, f1_start, f1_due))
        if f2_start or f2_due:
            filtered_dfs.append(filter_date_range(df, date_col, f2_start, f2_due))
        if f3_start or f3_due:
            filtered_dfs.append(filter_date_range(df, date_col, f3_start, f3_due))

        df_filtered = pd.concat(filtered_dfs).drop_duplicates()
        df_display = df_filtered.head(1000)
    else:
        df_filtered = df
        df_display = df.head(1000)

    global_var.df_filtered = df_filtered  # simpan ke global_var agar bisa dipakai di fungsi lain

    headers = df_display.columns.tolist()
    rows = df_display.values.tolist()

    return df, df_filtered, headers, rows

# Fungsi utama untuk menangani model asosiasi
def handle_association(request):
    try:
        df, df_filtered, headers, rows = association()  # Ambil data dari fungsi association
    except Exception as e:
        flash(f"Gagal memproses data: {str(e)}", "danger")
        return redirect('/association')

    if request.method == 'POST' and request.form.get('action') == 'run_model':
        # === FREQUENT ITEMSETS PRODUK ===
        data_encodedproduk = pd.get_dummies(df_filtered['NM_ST'], prefix='PRODUK')
        data_encodedproduk['NO_FAKTUR'] = df_filtered['NO_FAKTUR'].values
        cols_produk = data_encodedproduk.columns.difference(['NO_FAKTUR'])
        data_encodedproduk[cols_produk] = data_encodedproduk[cols_produk].astype('uint8')
        df_transaksi = data_encodedproduk.groupby('NO_FAKTUR').max()
        total_transaksi = df_filtered['NO_FAKTUR'].nunique()

        all_results = []
        for i in range(0, len(df_transaksi), 10000):
            df_batch = df_transaksi.iloc[i:i+10000].astype(bool)
            frequent_itemsets = fpgrowth(df_batch, min_support=0.02, use_colnames=True)
            frequent_itemsets['itemsets'] = frequent_itemsets['itemsets'].apply(lambda x: frozenset(sorted(x)))
            all_results.append(frequent_itemsets)

        df_all_frequent_itemsets_produk = pd.concat(all_results).drop_duplicates(subset='itemsets').reset_index(drop=True)
        rules_produk = association_rules(df_all_frequent_itemsets_produk, metric="confidence", min_threshold=0.5)
        rules_produk = rules_produk[(rules_produk['confidence'] <= 1) & (rules_produk['lift'] >= 1)].sort_values(by='lift', ascending=False)

        # === FREQUENT ITEMSETS KATEGORI PRODUK ===
        data_encodedkategori = pd.get_dummies(df_filtered['KATEGORI_PRODUK'], prefix='KATEGORI')
        data_encodedkategori['NO_FAKTUR'] = df_filtered['NO_FAKTUR'].values
        cols_kategori = data_encodedkategori.columns.difference(['NO_FAKTUR'])
        data_encodedkategori[cols_kategori] = data_encodedkategori[cols_kategori].astype('uint8')
        df_transaksi_kategori = data_encodedkategori.groupby('NO_FAKTUR').max()

        all_results = []
        for i in range(0, len(df_transaksi_kategori), 10000):
            df_batch = df_transaksi_kategori.iloc[i:i+10000].astype(bool)
            frequent_itemsets = fpgrowth(df_batch, min_support=0.02, use_colnames=True)
            frequent_itemsets['itemsets'] = frequent_itemsets['itemsets'].apply(lambda x: frozenset(sorted(x)))
            all_results.append(frequent_itemsets)

        df_all_frequent_itemsets_kategori = pd.concat(all_results).drop_duplicates(subset='itemsets').reset_index(drop=True)
        rules_kategori = association_rules(df_all_frequent_itemsets_kategori, metric="confidence", min_threshold=0.5)
        rules_kategori = rules_kategori[(rules_kategori['confidence'] <= 1) & (rules_kategori['lift'] >= 1)].sort_values(by='lift', ascending=False)

        # Simpan hasil rules ke global_var agar bisa dipakai di controller lain
        global_var.rules_produk = rules_produk
        global_var.rules_kategori = rules_kategori
        global_var.total_transaksi = total_transaksi

        flash("Model berhasil dijalankan!", "success")
        return redirect(url_for('route_output'))

    return render_template("association.html", headers=headers, rows=rows)
