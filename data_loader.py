"""
data_loader.py
Modul untuk memuat, membersihkan, dan menganalisis dataset ibu hamil
berdasarkan sistem skoring Poedji Rochjati (KRR, KRT, KRST).
"""

import pandas as pd
import numpy as np

def load_data(filepath: str = "dataset_ibu_hamil_kamboja2b.csv") -> pd.DataFrame:
    df = pd.read_csv(filepath)
    
    # Standarisasi teks kolom string
    string_cols = ['nama_ibu', 'nama_suami', 'tempat_lahir', 'alamat', 'alergi', 'riwayat_sakit', 'kategori_risiko']
    for col in string_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    
    # Normalisasi KBR -> KRR (3 Kategori utama: KRR, KRT, KRST)
    df['kategori_risiko_asli'] = df['kategori_risiko']
    df['kategori_risiko'] = df['kategori_risiko'].replace({'KBR': 'KRR'})
    
    label_map = {
        'KRR': 'KRR (Risiko Rendah)',
        'KRT': 'KRT (Risiko Tinggi)',
        'KRST': 'KRST (Risiko Sangat Tinggi)'
    }
    df['kategori_label'] = df['kategori_risiko'].map(label_map).fillna(df['kategori_risiko'])
    
    # Ekstraksi angka usia kehamilan
    if 'usia_hamil' in df.columns:
        df['usia_hamil_minggu'] = df['usia_hamil'].astype(str).str.extract(r'(\d+)').astype(float)
    else:
        df['usia_hamil_minggu'] = np.nan
        
    # Status tekanan darah (Kategori Hipertensi)
    df['status_hipertensi'] = np.where(
        (df['tekanan_darah_sistol'] >= 140) | (df['tekanan_darah_diastol'] >= 90),
        'Tinggi (Hipertensi)',
        'Normal'
    )
    
    # Kategori Umur Ibu (< 20 th atau >= 35 th)
    df['kategori_usia_reproduksi'] = np.where(
        df['usia'] < 20, 'Terlalu Muda (<20 th)',
        np.where(df['usia'] >= 35, 'Terlalu Tua (>=35 th)', 'Usia Reproduktif Aman (20-34 th)')
    )
    
    # Tinggi badan berisiko (< 145 cm / Panggul Sempit)
    df['panggul_sempit_risiko'] = np.where(df['tinggi_badan_cm'] < 145, 'Ya (<145 cm)', 'Tidak (>=145 cm)')
    
    return df

def get_overall_summary(df: pd.DataFrame) -> dict:
    total = len(df)
    krr_count = int((df['kategori_risiko'] == 'KRR').sum())
    krt_count = int((df['kategori_risiko'] == 'KRT').sum())
    krst_count = int((df['kategori_risiko'] == 'KRST').sum())
    
    hipertensi_count = int((df['status_hipertensi'] == 'Tinggi (Hipertensi)').sum())
    usia_risiko_count = int((df['kategori_usia_reproduksi'] != 'Usia Reproduktif Aman (20-34 th)').sum())
    caesar_count = int((df['riwayat_caesar'] == 1).sum())
    panggul_sempit_count = int((df['panggul_sempit_risiko'] == 'Ya (<145 cm)').sum())
    
    penyakit_counts = df[df['riwayat_sakit'] != 'Tidak ada']['riwayat_sakit'].value_counts().to_dict()
    alergi_counts = df[df['alergi'] != 'Tidak ada']['alergi'].value_counts().to_dict()
    
    return {
        'total_bumil': total,
        'krr_count': krr_count,
        'krr_pct': round((krr_count / total) * 100, 1) if total else 0,
        'krt_count': krt_count,
        'krt_pct': round((krt_count / total) * 100, 1) if total else 0,
        'krst_count': krst_count,
        'krst_pct': round((krst_count / total) * 100, 1) if total else 0,
        'hipertensi_count': hipertensi_count,
        'hipertensi_pct': round((hipertensi_count / total) * 100, 1) if total else 0,
        'usia_risiko_count': usia_risiko_count,
        'usia_risiko_pct': round((usia_risiko_count / total) * 100, 1) if total else 0,
        'caesar_count': caesar_count,
        'caesar_pct': round((caesar_count / total) * 100, 1) if total else 0,
        'panggul_sempit_count': panggul_sempit_count,
        'panggul_sempit_pct': round((panggul_sempit_count / total) * 100, 1) if total else 0,
        'avg_skor': round(float(df['skor_poedji_rochjati'].mean()), 2),
        'max_skor': int(df['skor_poedji_rochjati'].max()),
        'penyakit_counts': penyakit_counts,
        'alergi_counts': alergi_counts
    }

def add_new_patient(new_data: dict, filepath: str = "dataset_ibu_hamil_kamboja2b.csv") -> bool:
    try:
        df = pd.read_csv(filepath)
        new_df = pd.DataFrame([new_data])
        df = pd.concat([df, new_df], ignore_index=True)
        df.to_csv(filepath, index=False)
        return True
    except Exception as e:
        print(f"Error adding new patient: {e}")
        return False

def update_patient(id_ibu: str, update_data: dict, filepath: str = "dataset_ibu_hamil_kamboja2b.csv") -> bool:
    try:
        df = pd.read_csv(filepath)
        if id_ibu in df['id_ibu'].values:
            for key, value in update_data.items():
                df.loc[df['id_ibu'] == id_ibu, key] = value
            df.to_csv(filepath, index=False)
            return True
        return False
    except Exception as e:
        print(f"Error updating patient: {e}")
        return False
