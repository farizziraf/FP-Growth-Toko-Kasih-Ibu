import os
import datetime
import pandas as pd
from flask import render_template, session, abort, request, flash, redirect, url_for
from mlxtend.frequent_patterns import fpgrowth, association_rules
import global_var

# Fungsi bantu parsing tanggal
def parse_date_ddmmyyyy(date_str):
    if not date_str:
        return None
    try:
        # Try parsing 'DD/MM/YYYY' first (for older manual inputs or if you switch input types)
        return datetime.datetime.strptime(date_str, '%d/%m/%Y')
    except ValueError:
        try:
            # If that fails, try parsing 'YYYY-MM-DD' (from <input type="date">)
            return datetime.datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return None # Return None if neither format matches

# Fungsi utama untuk load dan filter data
def association():
    file_path = session.get('uploaded_file', None)

    if not file_path or not os.path.exists(file_path):
        # Jika tidak ada file atau file tidak ditemukan, mungkin ini adalah GET request pertama
        # sebelum upload, atau sesi telah berakhir. Tangani ini sesuai kebutuhan aplikasi Anda.
        # Untuk demonstrasi, kita bisa mengembalikan DataFrame kosong.
        flash("Tidak ada file yang diunggah atau file tidak ditemukan. Silakan unggah file terlebih dahulu.", "warning")
        # Mengembalikan DataFrame kosong agar tidak terjadi error di bagian selanjutnya
        global_var.df_filtered = pd.DataFrame()
        global_var.df_display = pd.DataFrame()
        global_var.headers = []
        global_var.rows = []
        return pd.DataFrame(), pd.DataFrame(), [], []

    try:
        if file_path.lower().endswith('.xlsx'):
            df = pd.read_excel(file_path)
        elif file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path, sep=';')
        else:
            abort(400, description="Format file tidak didukung. Gunakan .xlsx atau .csv")
    except Exception as e:
        abort(500, description=f"Gagal membaca file: {e}")

    # Kolom tanggal
    date_col = 'TG_JUAL'
    # Pastikan kolom tanggal ada dan diubah ke datetime
    if date_col not in df.columns:
        abort(400, description=f"Kolom '{date_col}' tidak ditemukan dalam file. Pastikan nama kolom benar.")
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    # Hapus baris dengan tanggal yang tidak valid setelah konversi
    df.dropna(subset=[date_col], inplace=True)


    # Ambil filter tanggal dari parameter request (ini akan berbeda antara GET dan POST jika filter dikirim via form)
    # Untuk POST, request.form akan berisi data filter
    f1_start_str = request.args.get('f1_start') or request.form.get('f1_start')
    f1_due_str = request.args.get('f1_due') or request.form.get('f1_due')
    f2_start_str = request.args.get('f2_start') or request.form.get('f2_start')
    f2_due_str = request.args.get('f2_due') or request.form.get('f2_due')
    f3_start_str = request.args.get('f3_start') or request.form.get('f3_start')
    f3_due_str = request.args.get('f3_due') or request.form.get('f3_due')

    f1_start = parse_date_ddmmyyyy(f1_start_str)
    f1_due = parse_date_ddmmyyyy(f1_due_str)
    f2_start = parse_date_ddmmyyyy(f2_start_str)
    f2_due = parse_date_ddmmyyyy(f2_due_str)
    f3_start = parse_date_ddmmyyyy(f3_start_str)
    f3_due = parse_date_ddmmyyyy(f3_due_str)


    def filter_date_range(df_to_filter, col, start, due):
        # Buat salinan DataFrame untuk menghindari SettingWithCopyWarning
        df_copy = df_to_filter.copy()
        if start:
            df_copy = df_copy[df_copy[col] >= start]
        if due:
            df_copy = df_copy[df_copy[col] <= due]
        return df_copy

    # Filter data berdasarkan tanggal jika ada
    if any([f1_start, f1_due, f2_start, f2_due, f3_start, f3_due]):
        filtered_dfs = []
        if f1_start or f1_due:
            filtered_dfs.append(filter_date_range(df, date_col, f1_start, f1_due))
        if f2_start or f2_due:
            filtered_dfs.append(filter_date_range(df, date_col, f2_start, f2_due))
        if f3_start or f3_due:
            filtered_dfs.append(filter_date_range(df, date_col, f3_start, f3_due))

        # Gunakan pd.concat dan drop_duplicates untuk menggabungkan hasil filter
        # Pastikan tidak ada filtered_dfs yang kosong sebelum concat
        if filtered_dfs:
            df_filtered = pd.concat(filtered_dfs).drop_duplicates()
        else:
            df_filtered = df.copy() # Jika filter ada tapi tidak valid, kembali ke df asli

        df_display = df_filtered.head(1000)
    else:
        df_filtered = df.copy() # Gunakan copy() untuk menghindari masalah SettingWithCopyWarning
        df_display = df.head(1000)

    # Simpan ke global_var untuk dipakai saat POST
    global_var.df_filtered = df_filtered
    global_var.df_display = df_display
    global_var.headers = df_display.columns.tolist()
    global_var.rows = df_display.values.tolist()

    # Simpan filter yang diterapkan ke sesi untuk tampilan ulang di form
    session['filter_dates'] = {
        'f1_start': f1_start_str,
        'f1_due': f1_due_str,
        'f2_start': f2_start_str,
        'f2_due': f2_due_str,
        'f3_start': f3_start_str,
        'f3_due': f3_due_str,
    }

    return df, df_filtered, global_var.headers, global_var.rows

# Fungsi utama untuk menangani model asosiasi
def handle_association(request):
    # POST → jalankan model
    if request.method == 'POST' and request.form.get('action') == 'run_model':
        print("\n--- DEBUGGING POST REQUEST (Run Model) ---")
        print("Request Form Data (Filters):", request.form)
        print("Request Args Data (URL Params):", request.args) # Ini mungkin kosong untuk POST

        # PENTING: Panggil ulang fungsi association() untuk memastikan df_filtered diperbarui
        # berdasarkan filter terbaru dari request.form (jika filter disubmit via form)
        # atau request.args (jika filter disubmit via URL).
        try:
            df_original, df_filtered, headers, rows = association()
        except Exception as e:
            flash(f"Gagal memproses data atau filter: {str(e)}", "danger")
            return redirect(url_for('route_association'))

        print("DEBUG df_filtered after (re)calling association():")
        if not df_filtered.empty:
            print("  TG_JUAL min:", df_filtered['TG_JUAL'].min())
            print("  TG_JUAL max:", df_filtered['TG_JUAL'].max())
            print("  Total rows df_filtered:", len(df_filtered))
            print("  Jumlah transaksi unik (NO_FAKTUR):", df_filtered['NO_FAKTUR'].nunique())
        else:
            flash("Data kosong setelah filter. Harap sesuaikan filter Anda.", "warning")
            print("  df_filtered is empty!")
            # Redirect kembali ke halaman association untuk menampilkan pesan dan form
            return redirect(url_for('route_association'))
        print("------------------------------------------\n")


        total_transaksi = df_filtered['NO_FAKTUR'].nunique()

        # Pastikan kolom 'NM_ST' dan 'KATEGORI_PRODUK' ada
        if 'NM_ST' not in df_filtered.columns or 'KATEGORI_PRODUK' not in df_filtered.columns or 'NO_FAKTUR' not in df_filtered.columns:
            flash("Kolom 'NM_ST', 'KATEGORI_PRODUK', atau 'NO_FAKTUR' tidak ditemukan. Pastikan file Anda memiliki kolom-kolom ini.", "danger")
            return redirect(url_for('route_association'))

        # Frequent itemsets produk
        # Filter df_filtered di sini untuk memastikan hanya kolom yang relevan yang diproses
        df_produk_model = df_filtered[['NO_FAKTUR', 'NM_ST']].copy()
        data_encodedproduk = pd.get_dummies(df_produk_model['NM_ST'], prefix='PRODUK')
        data_encodedproduk['NO_FAKTUR'] = df_produk_model['NO_FAKTUR'].values
        # Pastikan tidak ada kolom 'NO_FAKTUR' yang ganda sebelum operasi perbedaan set
        cols_produk = data_encodedproduk.columns.difference(['NO_FAKTUR'])
        data_encodedproduk[cols_produk] = data_encodedproduk[cols_produk].astype('uint8')
        df_transaksi_produk = data_encodedproduk.groupby('NO_FAKTUR').max()

        # Atur min_support dan min_threshold agar dinamis jika Anda ingin
        # Untuk saat ini, kita gunakan nilai yang sudah ditentukan
        min_support_prod = 0.02
        min_confidence_prod = 0.5

        results_prod = []
        # Memproses dalam batch untuk performa dan memory
        for i in range(0, len(df_transaksi_produk), 10000):
            df_batch = df_transaksi_produk.iloc[i:i+10000].astype(bool)
            if not df_batch.empty:
                freq = fpgrowth(df_batch, min_support=min_support_prod, use_colnames=True)
                freq['itemsets'] = freq['itemsets'].apply(lambda x: frozenset(sorted(x)))
                results_prod.append(freq)

        all_freq_prod = pd.DataFrame()
        if results_prod:
            all_freq_prod = pd.concat(results_prod).drop_duplicates(subset='itemsets').reset_index(drop=True)

        rules_prod = pd.DataFrame()
        if not all_freq_prod.empty:
            rules_prod = association_rules(all_freq_prod, metric="confidence", min_threshold=min_confidence_prod)
            rules_prod = rules_prod[
                (rules_prod['support'] >= min_support_prod) &
                (rules_prod['confidence'] <= 1) &
                (rules_prod['lift'] >= 1)
            ].sort_values(by='lift', ascending=False)

        # Frequent itemsets kategori
        df_kategori_model = df_filtered[['NO_FAKTUR', 'KATEGORI_PRODUK']].copy()
        data_encodedkategori = pd.get_dummies(df_kategori_model['KATEGORI_PRODUK'], prefix='KATEGORI')
        data_encodedkategori['NO_FAKTUR'] = df_kategori_model['NO_FAKTUR'].values
        cols_kategori = data_encodedkategori.columns.difference(['NO_FAKTUR'])
        data_encodedkategori[cols_kategori] = data_encodedkategori[cols_kategori].astype('uint8')
        df_transaksi_kategori = data_encodedkategori.groupby('NO_FAKTUR').max()

        min_support_cat = 0.02
        min_confidence_cat = 0.5

        results_cat = []
        for i in range(0, len(df_transaksi_kategori), 10000):
            df_batch = df_transaksi_kategori.iloc[i:i+10000].astype(bool)
            if not df_batch.empty:
                freq = fpgrowth(df_batch, min_support=min_support_cat, use_colnames=True)
                freq['itemsets'] = freq['itemsets'].apply(lambda x: frozenset(sorted(x)))
                results_cat.append(freq)

        all_freq_cat = pd.DataFrame()
        if results_cat:
            all_freq_cat = pd.concat(results_cat).drop_duplicates(subset='itemsets').reset_index(drop=True)

        rules_cat = pd.DataFrame()
        if not all_freq_cat.empty:
            rules_cat = association_rules(all_freq_cat, metric="confidence", min_threshold=min_confidence_cat)
            rules_cat = rules_cat[
                (rules_cat['support'] >= min_support_cat) &
                (rules_cat['confidence'] <= 1) &
                (rules_cat['lift'] >= 1)
            ].sort_values(by='lift', ascending=False)


        global_var.rules_produk = rules_prod
        global_var.rules_kategori = rules_cat
        global_var.total_transaksi = total_transaksi

        flash("Model berhasil dijalankan berdasarkan data yang sudah difilter!", "success")
        return redirect(url_for('route_output'))

    # GET → tampilkan halaman filter
    else:
        try:
            # Panggil fungsi association untuk menyiapkan data tampilan awal
            df, df_filtered, headers, rows = association()
        except Exception as e:
            flash(f"Gagal memuat data awal: {str(e)}", "danger")
            return redirect('/association')

        # Ambil kembali tanggal filter dari sesi untuk mengisi ulang form
        filter_dates = session.get('filter_dates', {})
        return render_template("association.html", headers=headers, rows=rows, filter_dates=filter_dates)