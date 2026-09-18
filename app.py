"""
app.py
Dashboard Monitoring Kesehatan Ibu Hamil (KRR, KRT, KRST)
Dengan Visualisasi Interaktif, Laporan Analisis, dan Chatbot AI Terintegrasi Ollama.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from data_loader import load_data, get_overall_summary
from pdf_generator import generate_pdf_report
from ollama_client import (
    get_installed_models,
    check_ollama_status,
    generate_chat_response,
    OLLAMA_BASE_URL
)

# -------------------------------------------------------------
# Konfigurasi Halaman & Styling Modern
# -------------------------------------------------------------
st.set_page_config(
    page_title="MaternalCare - Dashboard Ibu Hamil",
    page_icon="🤰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk tampilan modern, clean, dan profesional
st.markdown("""
<style>
    /* Styling Dasar & Font */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Header Card Banner */
    .hero-banner {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 50%, #075985 100%);
        border-radius: 16px;
        padding: 24px 30px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(2, 132, 199, 0.25);
    }
    .hero-title {
        font-size: 26px;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .hero-subtitle {
        font-size: 14px;
        opacity: 0.9;
        margin-top: 6px;
        font-weight: 400;
    }
    
    /* KPI Metric Cards */
    .metric-card {
        background: white;
        border-radius: 14px;
        padding: 18px 20px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
    }
    .metric-label {
        font-size: 13px;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 800;
        margin-top: 6px;
        color: #0f172a;
    }
    .metric-sub {
        font-size: 12px;
        margin-top: 4px;
        font-weight: 500;
    }
    
    /* Warna Status Risiko */
    .badge-krr {
        background-color: #dcfce7;
        color: #15803d;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 12px;
        display: inline-block;
    }
    .badge-krt {
        background-color: #fef3c7;
        color: #b45309;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 12px;
        display: inline-block;
    }
    .badge-krst {
        background-color: #fee2e2;
        color: #b91c1c;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 12px;
        display: inline-block;
    }
    
    /* Info Card Modern */
    .info-card {
        background: #f8fafc;
        border-left: 4px solid #0284c7;
        padding: 16px 20px;
        border-radius: 0 12px 12px 0;
        margin-bottom: 20px;
    }
    
    /* Chatbot Message Styling */
    .chat-user {
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 12px 16px;
        border-radius: 16px 16px 4px 16px;
        margin-bottom: 12px;
    }
    .chat-bot {
        background-color: #f1f5f9;
        color: #0f172a;
        padding: 14px 18px;
        border-radius: 16px 16px 16px 4px;
        margin-bottom: 12px;
        border: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# Memuat Data
# -------------------------------------------------------------
@st.cache_data
def get_data():
    return load_data("dataset_ibu_hamil_kamboja2b.csv")

try:
    df_raw = get_data()
except Exception as e:
    st.error(f"Gagal memuat dataset: {e}")
    st.stop()

# -------------------------------------------------------------
# Sidebar: Filter Interaktif & Pengaturan Ollama
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🏥 **MaternalCare Posyandu Kamboja 2B**")
    st.caption("Sistem Monitoring Kehamilan Posyandu Kamboja 2B")
    st.markdown("---")
    
    st.subheader("🔍 **Filter Data**")
    
    # Filter Risiko
    risk_options = ["Semua Kategori", "KRR (Risiko Rendah)", "KRT (Risiko Tinggi)", "KRST (Risiko Sangat Tinggi)"]
    selected_risk = st.selectbox("Kategori Risiko:", risk_options)
    
    # Filter Usia
    min_age, max_age = int(df_raw['usia'].min()), int(df_raw['usia'].max())
    age_range = st.slider("Rentang Usia Ibu (Tahun):", min_age, max_age, (min_age, max_age))
    
    # Filter Riwayat Penyakit
    all_diseases = sorted(df_raw['riwayat_sakit'].unique().tolist())
    selected_diseases = st.multiselect("Riwayat Sakit:", all_diseases, default=[])
    
    # Filter Riwayat Caesar
    caesar_filter = st.radio("Riwayat Sesar (Caesar):", ["Semua", "Pernah Caesar", "Belum Pernah"], horizontal=True)
    
    st.markdown("---")
    
    # Konfigurasi Ollama
    st.subheader("🤖 **Status AI Ollama**")
    ollama_online = check_ollama_status()
    if ollama_online:
        st.success("🟢 Ollama Terhubung (`127.0.0.1:11434`)")
        available_models = get_installed_models()
        if available_models:
            chosen_model = st.selectbox("Model Ollama Aktif:", available_models)
        else:
            st.info("ℹ️ Belum ada model terinstall di Ollama.")
            chosen_model = "llama3"
            st.caption("Jalankan `ollama run llama3` di terminal.")
    else:
        st.warning("🟡 Ollama Offline / Tidak Berjalan")
        chosen_model = "fallback"
        st.caption("Engine Chatbot otomatis menggunakan *BumilCare Expert Rule-Based*.")
        
    st.markdown("---")
    st.caption("© 2026 MaternalCare Analytics • Posyandu & Bidan Digital")

# -------------------------------------------------------------
# Logika Filtering Dataframe
# -------------------------------------------------------------
df_filtered = df_raw.copy()

if selected_risk == "KRR (Risiko Rendah)":
    df_filtered = df_filtered[df_filtered['kategori_risiko'] == 'KRR']
elif selected_risk == "KRT (Risiko Tinggi)":
    df_filtered = df_filtered[df_filtered['kategori_risiko'] == 'KRT']
elif selected_risk == "KRST (Risiko Sangat Tinggi)":
    df_filtered = df_filtered[df_filtered['kategori_risiko'] == 'KRST']

df_filtered = df_filtered[(df_filtered['usia'] >= age_range[0]) & (df_filtered['usia'] <= age_range[1])]

if selected_diseases:
    df_filtered = df_filtered[df_filtered['riwayat_sakit'].isin(selected_diseases)]

if caesar_filter == "Pernah Caesar":
    df_filtered = df_filtered[df_filtered['riwayat_caesar'] == 1]
elif caesar_filter == "Belum Pernah":
    df_filtered = df_filtered[df_filtered['riwayat_caesar'] == 0]

# Agregasi Ringkasan
summary = get_overall_summary(df_filtered)
summary_all = get_overall_summary(df_raw)

# -------------------------------------------------------------
# Header Banner
# -------------------------------------------------------------
st.markdown("""
<div class="hero-banner">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
        <div>
            <h1 class="hero-title">🤰 Dashboard Monitoring Kesehatan Ibu Hamil</h1>
            <p class="hero-subtitle">Visualisasi Skrining Risiko Poedji Rochjati (KRR, KRT, KRST) & Asisten AI Konsultasi Kehamilan</p>
        </div>
        <div style="text-align: right; margin-top: 10px;">
            <span style="background: rgba(255,255,255,0.2); padding: 6px 14px; border-radius: 30px; font-size: 13px; font-weight: 600;">
                📍 Wilayah: Lebak Wangi & Perum Duta Asri
            </span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

if 'show_data_filter' not in st.session_state:
    st.session_state.show_data_filter = None

# -------------------------------------------------------------
# KPI Cards Metrik
# -------------------------------------------------------------
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Total Ibu Hamil</div>
        <div class="metric-value">{summary['total_bumil']}</div>
        <div class="metric-sub" style="color: #64748b;">dari {summary_all['total_bumil']} total terdata</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🔍 Lihat Data", key="btn_total", use_container_width=True):
        st.session_state.show_data_filter = "Total"

with c2:
    st.markdown(f"""
    <div class="metric-card" style="border-top: 4px solid #22c55e;">
        <div class="metric-label" style="color: #16a34a;">🟢 KRR (Rendah)</div>
        <div class="metric-value" style="color: #15803d;">{summary['krr_count']}</div>
        <div class="metric-sub" style="color: #16a34a;">{summary['krr_pct']}% • Skor 2</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🔍 Lihat Data", key="btn_krr", use_container_width=True):
        st.session_state.show_data_filter = "KRR"

with c3:
    st.markdown(f"""
    <div class="metric-card" style="border-top: 4px solid #f59e0b;">
        <div class="metric-label" style="color: #d97706;">🟡 KRT (Tinggi)</div>
        <div class="metric-value" style="color: #b45309;">{summary['krt_count']}</div>
        <div class="metric-sub" style="color: #d97706;">{summary['krt_pct']}% • Skor 6-10</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🔍 Lihat Data", key="btn_krt", use_container_width=True):
        st.session_state.show_data_filter = "KRT"

with c4:
    st.markdown(f"""
    <div class="metric-card" style="border-top: 4px solid #ef4444;">
        <div class="metric-label" style="color: #dc2626;">🔴 KRST (Sgt Tinggi)</div>
        <div class="metric-value" style="color: #b91c1c;">{summary['krst_count']}</div>
        <div class="metric-sub" style="color: #dc2626;">{summary['krst_pct']}% • Skor ≥ 12</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🔍 Lihat Data", key="btn_krst", use_container_width=True):
        st.session_state.show_data_filter = "KRST"

with c5:
    st.markdown(f"""
    <div class="metric-card" style="border-top: 4px solid #6366f1;">
        <div class="metric-label" style="color: #4f46e5;">⚠️ Hipertensi</div>
        <div class="metric-value" style="color: #4338ca;">{summary['hipertensi_count']}</div>
        <div class="metric-sub" style="color: #4f46e5;">{summary['hipertensi_pct']}% bertekanan tinggi</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🔍 Lihat Data", key="btn_hipertensi", use_container_width=True):
        st.session_state.show_data_filter = "Hipertensi"

st.write("")

# Menampilkan data jika tombol ditekan
if st.session_state.show_data_filter:
    st.markdown(f"### 📋 Data: {st.session_state.show_data_filter}")
    
    df_show = df_filtered.copy()
    if st.session_state.show_data_filter == "KRR":
        df_show = df_show[df_show['kategori_risiko'] == 'KRR']
    elif st.session_state.show_data_filter == "KRT":
        df_show = df_show[df_show['kategori_risiko'] == 'KRT']
    elif st.session_state.show_data_filter == "KRST":
        df_show = df_show[df_show['kategori_risiko'] == 'KRST']
    elif st.session_state.show_data_filter == "Hipertensi":
        df_show = df_show[df_show['status_hipertensi'] == 'Tinggi (Hipertensi)']
        
    cols_to_show = [
        'id_ibu', 'nama_ibu', 'usia', 'alamat', 'usia_hamil', 'hpl', 
        'tekanan_darah_sistol', 'tekanan_darah_diastol', 
        'riwayat_sakit', 'alergi', 'skor_poedji_rochjati', 'kategori_risiko'
    ]
    st.dataframe(df_show[cols_to_show], use_container_width=True, hide_index=True)
    if st.button("Tutup Data"):
        st.session_state.show_data_filter = None
        st.rerun()

    st.markdown("---")

# -------------------------------------------------------------
# Navigasi Tab Utama
# -------------------------------------------------------------
tab_grafik, tab_laporan, tab_data, tab_chat, tab_input = st.tabs([
    "📊 Grafik & Visualisasi 3 Kategori",
    "📑 Laporan Analisis Keseluruhan",
    "📋 Data Ibu Hamil & Detail",
    "💬 Chatbot Konsultasi AI (Ollama)",
    "➕ Input & Update Data"
])

# Palet warna konsisten KRR, KRT, KRST
COLOR_MAP = {
    'KRR': '#22c55e',   # Hijau
    'KRT': '#f59e0b',   # Kuning / Oranye
    'KRST': '#ef4444'   # Merah
}
COLOR_SEQ = ['#22c55e', '#f59e0b', '#ef4444']

# =============================================================
# TAB 1: GRAFIK & VISUALISASI 3 KATEGORI
# =============================================================
with tab_grafik:
    st.markdown("### 📈 Visualisasi Distribusi Risiko Kehamilan")
    st.caption("Pemetaan komparatif kategori KRR (Risiko Rendah), KRT (Risiko Tinggi), dan KRST (Risiko Sangat Tinggi).")
    
    col_g1, col_g2 = st.columns([1, 1])
    
    with col_g1:
        # Donut Chart 3 Kategori
        cat_counts = df_filtered['kategori_risiko'].value_counts().reset_index()
        cat_counts.columns = ['kategori', 'jumlah']
        # Pastikan urutan rapi KRR, KRT, KRST
        cat_order = ['KRR', 'KRT', 'KRST']
        cat_counts['order'] = cat_counts['kategori'].apply(lambda x: cat_order.index(x) if x in cat_order else 99)
        cat_counts = cat_counts.sort_values('order')
        
        fig_donut = px.pie(
            cat_counts,
            values='jumlah',
            names='kategori',
            color='kategori',
            color_discrete_map=COLOR_MAP,
            hole=0.55,
            title="<b>Proporsi Kategori Risiko (Donut Chart)</b>"
        )
        fig_donut.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>Jumlah: %{value} Bumil<br>Persentase: %{percent}<extra></extra>'
        )
        fig_donut.update_layout(
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            margin=dict(t=50, b=50, l=20, r=20),
            height=350
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with col_g2:
        # Bar Chart Skor Rata-rata & Jumlah Kasus
        fig_bar = px.bar(
            cat_counts,
            x='kategori',
            y='jumlah',
            color='kategori',
            color_discrete_map=COLOR_MAP,
            text='jumlah',
            title="<b>Jumlah Pasien per Kategori Risiko</b>",
            labels={'kategori': 'Kategori Risiko', 'jumlah': 'Jumlah Pasien'}
        )
        fig_bar.update_traces(textposition='outside')
        fig_bar.update_layout(
            showlegend=False,
            margin=dict(t=50, b=50, l=20, r=20),
            height=350,
            yaxis=dict(title="Jumlah Pasien", showgrid=True)
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🔍 Analisis Faktor Klinis & Prediktor Risiko")

    col_g3, col_g4 = st.columns(2)

    with col_g3:
        # Scatter Plot Tekanan Darah (Sistol vs Diastol)
        fig_bp = px.scatter(
            df_filtered,
            x='tekanan_darah_diastol',
            y='tekanan_darah_sistol',
            color='kategori_risiko',
            color_discrete_map=COLOR_MAP,
            hover_data=['nama_ibu', 'usia', 'skor_poedji_rochjati', 'riwayat_sakit'],
            title="<b>Sebaran Tekanan Darah: Sistol vs Diastol (mmHg)</b>",
            labels={'tekanan_darah_diastol': 'Diastol (mmHg)', 'tekanan_darah_sistol': 'Sistol (mmHg)'}
        )
        # Garis ambang batas hipertensi (140/90)
        fig_bp.add_hline(y=140, line_dash="dot", line_color="#ef4444", annotation_text="Batas Sistol 140", annotation_position="top left")
        fig_bp.add_vline(x=90, line_dash="dot", line_color="#ef4444", annotation_text="Batas Diastol 90", annotation_position="bottom right")
        fig_bp.update_layout(height=380, margin=dict(t=50, b=40, l=20, r=20))
        st.plotly_chart(fig_bp, use_container_width=True)

    with col_g4:
        # Distribusi Usia vs Kategori Risiko
        fig_age = px.box(
            df_filtered,
            x='kategori_risiko',
            y='usia',
            color='kategori_risiko',
            color_discrete_map=COLOR_MAP,
            points='all',
            title="<b>Distribusi Usia Ibu Hamil per Kategori Risiko</b>",
            labels={'kategori_risiko': 'Kategori Risiko', 'usia': 'Usia (Tahun)'}
        )
        fig_age.add_hrect(y0=20, y1=35, line_width=0, fillcolor="#22c55e", opacity=0.1, annotation_text="Rentang Usia Aman (20-34 th)")
        fig_age.update_layout(height=380, margin=dict(t=50, b=40, l=20, r=20), showlegend=False)
        st.plotly_chart(fig_age, use_container_width=True)

    col_g5, col_g6 = st.columns(2)

    with col_g5:
        # Riwayat Penyakit Penyerta
        disease_df = df_filtered[df_filtered['riwayat_sakit'] != 'Tidak ada']['riwayat_sakit'].value_counts().reset_index()
        disease_df.columns = ['penyakit', 'jumlah']
        fig_dis = px.bar(
            disease_df,
            x='jumlah',
            y='penyakit',
            orientation='h',
            title="<b>Komorbiditas / Riwayat Penyakit Penyerta</b>",
            color='jumlah',
            color_continuous_scale='Reds',
            text='jumlah'
        )
        fig_dis.update_traces(textposition='outside')
        fig_dis.update_layout(height=340, yaxis={'categoryorder':'total ascending'}, showlegend=False, margin=dict(t=50, b=30, l=20, r=20))
        st.plotly_chart(fig_dis, use_container_width=True)

    with col_g6:
        # Riwayat Caesar & Skor Poedji Rochjati
        caesar_summary = df_filtered.groupby(['kategori_risiko', 'riwayat_caesar']).size().reset_index(name='jumlah')
        caesar_summary['status_caesar'] = caesar_summary['riwayat_caesar'].map({0: 'Belum Pernah SC', 1: 'Pernah SC (Bekas Sesar)'})
        fig_caesar = px.bar(
            caesar_summary,
            x='kategori_risiko',
            y='jumlah',
            color='status_caesar',
            barmode='group',
            title="<b>Proporsi Riwayat Operasi Caesar (SC)</b>",
            color_discrete_map={'Belum Pernah SC': '#94a3b8', 'Pernah SC (Bekas Sesar)': '#e11d48'},
            text='jumlah'
        )
        fig_caesar.update_traces(textposition='outside')
        fig_caesar.update_layout(height=340, margin=dict(t=50, b=30, l=20, r=20))
        st.plotly_chart(fig_caesar, use_container_width=True)

# =============================================================
# TAB 2: LAPORAN ANALISIS KESELURUHAN
# =============================================================
with tab_laporan:
    st.markdown("### 📑 Laporan Analisis Klinis & Epidemiologis Keseluruhan")
    st.caption("Hasil kompilasi analisis risiko kehamilan berdasarkan Skrining Poedji Rochjati untuk evaluasi posyandu & fasilitas rujukan.")
    
    # Alert Ringkasan Utama
    st.markdown(f"""
    <div class="info-card">
        <h4 style="margin: 0 0 8px 0; color: #0284c7;">📌 Executive Summary Skrining Kehamilan</h4>
        <p style="margin: 0; line-height: 1.6; color: #334155;">
            Dari total <b>{summary_all['total_bumil']} ibu hamil</b> yang diskrining, sebanyak 
            <b>{summary_all['krt_count'] + summary_all['krst_count']} ibu hamil ({round(((summary_all['krt_count'] + summary_all['krst_count'])/summary_all['total_bumil'])*100, 1)}%)</b> 
            tergolong dalam kehamilan berisiko (KRT & KRST). Hanya <b>{summary_all['krr_count']} ibu ({summary_all['krr_pct']}%)</b> 
            yang berada dalam kategori risiko rendah (KRR). Hal ini menandakan perlunya pengawasan ketat, perencanaan persalinan di fasilitas kesehatan memadai, dan deteksi dini komplikasi obstetri.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 4 Kotak Temuan Klinis
    col_rep1, col_rep2 = st.columns(2)
    
    with col_rep1:
        st.markdown("""
        #### 1. Analisis Kategori Risiko (Poedji Rochjati)
        - **🟢 KRR (Kehamilan Risiko Rendah) - 75 Kasus (14.9%)**:
          - Skor total 2 (risiko bawaan fisiologis normal).
          - Persalinan aman dipimpin oleh **Bidan** di Puskesmas, Polindes, atau BPM mandiri.
        - **🟡 KRT (Kehamilan Risiko Tinggi) - 329 Kasus (65.3%)**:
          - Skor antara 6 hingga 10. Mayoritas dipicu oleh faktor usia muda (<20 th) / usia tua (≥35 th), tinggi badan <145 cm, jarak kehamilan <2 tahun, atau hipertensi derajat 1.
          - Rekomendasi: Konsultasi dokter spesialis obstetri terencana (Rujukan Terencana).
        - **🔴 KRST (Kehamilan Risiko Sangat Tinggi) - 100 Kasus (19.8%)**:
          - Skor mencapai ≥12 hingga skor maksimal **22**.
          - Mengalami risiko ganda berat: kombinasi bekas SC, panggul sempit, hipertensi berat (>160/100 mmHg), dan penyakit sistemik (diabetes/gastritis parah).
          - Rekomendasi: **Wajib persalinan di Rumah Sakit PONEK** dengan dokter spesialis Obgyn.
        """)
        
        st.markdown("""
        #### 2. Profil Tekanan Darah & Risiko Preeklamsia
        - Terdapat **202 ibu hamil (40.1%)** dengan tekanan darah sistol ≥140 mmHg atau diastol ≥90 mmHg.
        - Hipertensi merupakan faktor komplikasi tertinggi yang berpotensi memicu **Preeklamsia Berat (PEB)** hingga eklamsia.
        - Langkah intervensi: Skrining protein urine berkala pada ANC terpadu dan pemberian kalsium serta aspirin dosis rendah sesuai advis Sp.OG.
        """)
        
    with col_rep2:
        st.markdown("""
        #### 3. Faktor Reproduksi, Usia & Riwayat Operasi
        - **Ibu Usia Berisiko (<20 th & ≥35 th)**: Sebanyak **177 ibu (35.1%)** berada di luar rentang usia reproduksi sehat.
          - Usia <20 tahun berisiko tinggi panggul sempit, anemia, dan preeklamsia.
          - Usia ≥35 tahun berisiko kelainan kromosom janin, hipertensi kronik, dan distosia persalinan.
        - **Riwayat Operasi Caesar (SC)**: Terdata **91 ibu (18.1%)** memiliki bekas luka parut rahim. Wajib dievaluasi ketebalan segmen bawah rahim (SBR) pada trimester 3 untuk mencegah ruptur uteri.
        - **Tinggi Badan < 145 cm**: Terdata **147 ibu (29.2%)** berisiko disproporsi sefalopelvik (CPD) akibat panggul sempit.
        """)
        
        st.markdown("""
        #### 4. Komorbiditas & Alergi
        - **Riwayat Penyakit Terbanyak**:
          - Hipertensi: 72 pasien
          - Anemia: 65 pasien
          - Diabetes Gestasional: 58 pasien
          - Gastritis: 57 pasien
          - Asthma: 51 pasien
        - **Alergi Terbanyak**: Seafood (49), Dingin (37), Penisilin (35 - *perhatian khusus antibiotik persalinan*), Udang (34), Debu (31).
        """)

    st.markdown("---")
    
    # Rekomendasi Intervensi Posyandu & Faskes
    st.subheader("💡 Rekomendasi Tindak Lanjut Program Kesehatan")
    rec_c1, rec_c2, rec_c3 = st.columns(3)
    
    with rec_c1:
        st.info("""
        **Bagi Bidan & Kader Posyandu:**
        - Kunjungan rumah (home visit) intensif bagi bumil KRST.
        - Pastikan kepatuhan konsumsi Tablet Tambah Darah (TTD) dan kalsium.
        - Pasang stiker P4K (Program Perencanaan Persalinan dan Pencegahan Komplikasi) di setiap rumah bumil.
        """)
        
    with rec_c2:
        st.warning("""
        **Bagi Puskesmas / Faskes Primer:**
        - Lakukan skrining USG pada trimester 1 dan trimester 3 oleh dokter umum/Sp.OG.
        - Koordinasi Rujukan Dini Berencana (RDB) untuk semua pasien KRST dan KRT komplikasi sebelum tanda inpartu muncul.
        """)

    with rec_c3:
        st.error("""
        **Bagi Rumah Sakit Rujukan (PONEK):**
        - Kesiapan tim emergensi maternal neonatal 24 jam.
        - Kesiapan stok darah PRC dan fasilitas ICU/NICU untuk penanganan komplikasi obstetri berat.
        """)
        
    # Tombol Unduh Laporan Ringkas
    st.write("")
    laporan_md = f"""# LAPORAN ANALISIS SKRINING KESEHATAN IBU HAMIL
Tanggal Analisis: September 2026
Wilayah: Lebak Wangi & Perum Duta Asri

## 1. RINGKASAN DATA
- Total Pasien Ibu Hamil: {summary_all['total_bumil']}
- KRR (Risiko Rendah): {summary_all['krr_count']} ({summary_all['krr_pct']}%)
- KRT (Risiko Tinggi): {summary_all['krt_count']} ({summary_all['krt_pct']}%)
- KRST (Risiko Sangat Tinggi): {summary_all['krst_count']} ({summary_all['krst_pct']}%)

## 2. KOMPLIKASI & RISIKO KLINIS
- Hipertensi Gestasional: {summary_all['hipertensi_count']} kasus ({summary_all['hipertensi_pct']}%)
- Usia Berisiko (<20 atau >=35 th): {summary_all['usia_risiko_count']} kasus ({summary_all['usia_risiko_pct']}%)
- Riwayat Bekas Caesar: {summary_all['caesar_count']} kasus ({summary_all['caesar_pct']}%)
- Risiko Panggul Sempit (TB < 145 cm): {summary_all['panggul_sempit_count']} kasus ({summary_all['panggul_sempit_pct']}%)

## 3. REKOMENDASI UTAMA
1. Rujukan terencana ke RS PONEK untuk 100 ibu hamil kategori KRST.
2. Skrining ketat preeklamsia dan protein urine bagi 202 ibu dengan tensi tinggi.
3. Pendampingan P4K dan donor darah siaga oleh kader posyandu.
"""
    # Tombol Unduh Laporan Resmi
    st.write("")
    col_dl1, col_dl2 = st.columns(2)
    
    with col_dl1:
        # Generate PDF on the fly
        try:
            pdf_bytes = generate_pdf_report(summary_all)
            st.download_button(
                label="📄 Download Laporan Analisis Lengkap (.PDF Resmi)",
                data=pdf_bytes,
                file_name="Laporan_Analisis_Ibu_Hamil_MaternalCare.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Gagal menyiapkan PDF: {e}")
            
    with col_dl2:
        st.download_button(
            label="📥 Download Ringkasan Laporan (.MD / Text)",
            data=laporan_md,
            file_name="Laporan_Analisis_Ibu_Hamil_MaternalCare.md",
            mime="text/markdown",
            use_container_width=True
        )

# =============================================================
# TAB 3: DATA IBU HAMIL & DETAIL
# =============================================================
with tab_data:
    st.markdown("### 📋 Tabel Data Rekam Medis Ibu Hamil")
    st.caption(f"Menampilkan **{len(df_filtered)}** data ibu hamil sesuai kriteria filter yang dipilih.")
    
    # Kolom untuk pencarian cepat
    search_query = st.text_input("🔎 Cari berdasarkan Nama Ibu, NIK, atau Alamat:", placeholder="Ketik nama...")
    
    df_display = df_filtered.copy()
    if search_query:
        search_lower = search_query.lower()
        df_display = df_display[
            df_display['nama_ibu'].str.lower().str.contains(search_lower) |
            df_display['nik'].astype(str).str.contains(search_lower) |
            df_display['alamat'].str.lower().str.contains(search_lower)
        ]
    
    # Kolom terpilih untuk tabel tampilan rapi
    cols_to_show = [
        'id_ibu', 'nama_ibu', 'usia', 'alamat', 'usia_hamil', 'hpl', 
        'tekanan_darah_sistol', 'tekanan_darah_diastol', 
        'riwayat_sakit', 'alergi', 'riwayat_caesar', 
        'skor_poedji_rochjati', 'kategori_risiko'
    ]
    
    # Format tabel interaktif
    st.dataframe(
        df_display[cols_to_show].rename(columns={
            'id_ibu': 'ID',
            'nama_ibu': 'Nama Ibu',
            'usia': 'Usia (Th)',
            'alamat': 'Alamat',
            'usia_hamil': 'Usia Hamil',
            'hpl': 'HPL',
            'tekanan_darah_sistol': 'TD Sistol',
            'tekanan_darah_diastol': 'TD Diastol',
            'riwayat_sakit': 'Riwayat Sakit',
            'alergi': 'Alergi',
            'riwayat_caesar': 'Bekas SC',
            'skor_poedji_rochjati': 'Skor PR',
            'kategori_risiko': 'Kategori'
        }),
        use_container_width=True,
        hide_index=True
    )
    
    # Download data terfilter sebagai CSV
    csv_data = df_display.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Export Data Terfilter (.csv)",
        data=csv_data,
        file_name="Data_Ibu_Hamil_Terfilter.csv",
        mime="text/csv"
    )

    st.markdown("---")
    st.markdown("#### 👤 Kartu Detail Profil Pasien")
    selected_patient_id = st.selectbox(
        "Pilih ID Ibu Hamil untuk melihat rekam medis lengkap:",
        options=df_display['id_ibu'].tolist() if len(df_display) > 0 else []
    )
    
    if selected_patient_id:
        p = df_display[df_display['id_ibu'] == selected_patient_id].iloc[0]
        
        # Badge Kategori
        badge_class = "badge-krr" if p['kategori_risiko'] == 'KRR' else ("badge-krt" if p['kategori_risiko'] == 'KRT' else "badge-krst")
        
        st.markdown(f"""
        <div style="background: white; border: 1px solid #e2e8f0; border-radius: 14px; padding: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f1f5f9; padding-bottom: 12px; margin-bottom: 14px;">
                <h3 style="margin: 0; color: #0f172a;">{p['nama_ibu']} ({p['id_ibu']})</h3>
                <span class="{badge_class}">{p['kategori_label']} - Skor: {p['skor_poedji_rochjati']}</span>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; font-size: 14px; color: #334155;">
                <div><b>NIK:</b> {p['nik']}</div>
                <div><b>Nama Suami:</b> {p['nama_suami']}</div>
                <div><b>Usia:</b> {p['usia']} tahun</div>
                <div><b>TTL:</b> {p['tempat_lahir']}, {p['tanggal_lahir']}</div>
                <div><b>Alamat:</b> {p['alamat']}</div>
                <div><b>HPL:</b> {p['hpl']} ({p['usia_hamil']})</div>
                <div><b>Tinggi Badan:</b> {p['tinggi_badan_cm']} cm ({p['panggul_sempit_risiko']})</div>
                <div><b>Tekanan Darah:</b> {p['tekanan_darah_sistol']}/{p['tekanan_darah_diastol']} mmHg ({p['status_hipertensi']})</div>
                <div><b>Riwayat Sesar:</b> {'Pernah SC' if p['riwayat_caesar']==1 else 'Belum Pernah SC'}</div>
                <div><b>Anak Hidup:</b> {p['jumlah_anak_hidup']} orang</div>
                <div><b>Jarak Kehamilan:</b> {p['jarak_kehamilan_tahun']} tahun</div>
                <div><b>Riwayat Penyakit:</b> <span style="color: #b91c1c; font-weight: 600;">{p['riwayat_sakit']}</span></div>
                <div><b>Alergi:</b> {p['alergi']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# =============================================================
# TAB 4: CHATBOT KONSULTASI AI (OLLAMA)
# =============================================================
with tab_chat:
    st.markdown("### 💬 BumilCare AI Assistant (Terhubung dengan Ollama)")
    st.caption("Asisten cerdas berbasis AI lokal Ollama untuk konsultasi klinis kehamilan, skrining Poedji Rochjati, dan penanganan risiko obstetri.")
    
    # Status Banner Koneksi
    if ollama_online:
        st.success(f"🟢 **Ollama Terhubung**: Menggunakan endpoint `{OLLAMA_BASE_URL}` | Model: **{chosen_model}**")
    else:
        st.warning("🟡 **Mode Siaga**: Server Ollama offline. Chatbot beroperasi menggunakan **Engine Aturan Klinis & Pengetahuan Maternal Terpadu**.")
        st.caption("💡 *Tips menjalankan Ollama:* Buka terminal/cmd dan ketik: `ollama run llama3` atau `ollama serve`.")

    # Context data yang disuntikkan ke prompt
    dataset_summary_prompt = (
        f"Total Ibu Hamil: {summary_all['total_bumil']}. "
        f"KRR (Risiko Rendah, skor 2): {summary_all['krr_count']} orang ({summary_all['krr_pct']}%). "
        f"KRT (Risiko Tinggi, skor 6-10): {summary_all['krt_count']} orang ({summary_all['krt_pct']}%). "
        f"KRST (Risiko Sangat Tinggi, skor >=12): {summary_all['krst_count']} orang ({summary_all['krst_pct']}%). "
        f"Hipertensi: {summary_all['hipertensi_count']} orang ({summary_all['hipertensi_pct']}%). "
        f"Ibu usia risiko (<20 atau >=35 th): {summary_all['usia_risiko_count']} orang. "
        f"Riwayat bekas Caesar: {summary_all['caesar_count']} orang. "
        f"Wilayah: Lebak Wangi dan Perum Duta Asri."
    )

    # Inisialisasi History Chat di Session State
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Halo Bidan / Tenaga Kesehatan! Saya **BumilCare AI**, asisten klinis kehamilan yang terhubung dengan Ollama.\n\n"
                    "Saya dapat membantu Anda menganalisis data 504 ibu hamil ini, memberikan rekomendasi penanganan KRR, KRT, KRST, "
                    "protokol hipertensi, anemia, hingga persiapan rujukan rumah sakit. Ada yang ingin Anda tanyakan?"
                )
            }
        ]

    # Tombol Reset Chat
    col_chat_btn1, col_chat_btn2 = st.columns([6, 1])
    with col_chat_btn2:
        if st.button("🗑️ Reset Chat", use_container_width=True):
            st.session_state.messages = [st.session_state.messages[0]]
            st.rerun()

    # Tampilkan percakapan yang sudah ada
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Template Pertanyaan Cepat
    st.markdown("##### 💡 Pertanyaan Cepat:")
    q_col1, q_col2, q_col3 = st.columns(3)
    preset_query = None
    with q_col1:
        if st.button("📌 Jelaskan KRR, KRT, & KRST", use_container_width=True):
            preset_query = "Tolong jelaskan secara lengkap perbedaan KRR, KRT, dan KRST menurut Poedji Rochjati."
    with q_col2:
        if st.button("🩺 Panduan Hipertensi Bumil", use_container_width=True):
            preset_query = "Bagaimana protokol penanganan dan rujukan untuk ibu hamil dengan hipertensi?"
    with q_col3:
        if st.button("📊 Ringkasan Risiko Wilayah", use_container_width=True):
            preset_query = "Berapa jumlah bumil KRST dan komplikasi terbanyak di wilayah ini?"

    # Input Pengguna (bisa dari text_input atau preset button)
    user_input = st.chat_input("Tanyakan sesuatu tentang data bumil atau kesehatan kehamilan...")
    actual_query = preset_query or user_input

    if actual_query:
        # Tampilkan pesan user
        st.session_state.messages.append({"role": "user", "content": actual_query})
        with st.chat_message("user"):
            st.markdown(actual_query)

        # Generate respon
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""
            
            # Format pesan untuk Ollama
            formatted_msgs = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            
            # Stream generator
            stream_gen = generate_chat_response(
                messages=formatted_msgs,
                model=chosen_model,
                dataset_context=dataset_summary_prompt,
                base_url=OLLAMA_BASE_URL
            )
            
            for chunk in stream_gen:
                full_response += chunk
                response_placeholder.markdown(full_response + "▌")
                
            response_placeholder.markdown(full_response)
            
        st.session_state.messages.append({"role": "assistant", "content": full_response})

# =============================================================
# TAB 5: INPUT & UPDATE DATA
# =============================================================
with tab_input:
    st.markdown("### ➕ Input Data Ibu Hamil Baru & 🔄 Update Pemeriksaan")
    st.write("Gunakan formulir di bawah ini untuk menambahkan pasien baru atau memperbarui data pemeriksaan.")
    
    tab_new, tab_update = st.tabs(["📝 Input Pasien Baru", "🔄 Update Data Pemeriksaan"])
    
    with tab_new:
        with st.form("form_tambah_bumil"):
            st.subheader("Data Diri Pasien")
            col1, col2 = st.columns(2)
            with col1:
                new_id = st.text_input("ID Ibu (Otomatis/Manual)", value=f"BML-{np.random.randint(1000, 9999)}")
                new_nama = st.text_input("Nama Ibu")
                new_nik = st.text_input("NIK", max_chars=16)
                new_suami = st.text_input("Nama Suami")
                new_tempat = st.text_input("Tempat Lahir")
                new_tgl = st.date_input("Tanggal Lahir")
                new_alamat = st.text_area("Alamat")
            
            with col2:
                new_usia = st.number_input("Usia", min_value=12, max_value=60, value=25)
                new_hpl = st.date_input("HPL (Hari Perkiraan Lahir)")
                new_usia_hamil = st.text_input("Usia Hamil (misal: 24 Minggu)", value="0 Minggu")
                new_tinggi = st.number_input("Tinggi Badan (cm)", min_value=100, max_value=200, value=155)
                new_jarak = st.number_input("Jarak Kehamilan (Tahun)", min_value=0, max_value=20, value=0)
                new_anak = st.number_input("Jumlah Anak Hidup", min_value=0, max_value=15, value=0)
                new_caesar = st.selectbox("Riwayat Caesar", [0, 1])
                
            st.subheader("Data Medis")
            col3, col4 = st.columns(2)
            with col3:
                new_sistol = st.number_input("Tekanan Darah Sistol", min_value=70, max_value=250, value=110)
                new_diastol = st.number_input("Tekanan Darah Diastol", min_value=40, max_value=150, value=70)
                new_alergi = st.text_input("Alergi", value="Tidak ada")
                new_riwayat = st.text_input("Riwayat Sakit", value="Tidak ada")
            
            with col4:
                new_skor = st.number_input("Skor Poedji Rochjati", min_value=2, max_value=30, value=2)
                # auto kategori
                kat_risiko = "KRR"
                if new_skor >= 12:
                    kat_risiko = "KRST"
                elif new_skor >= 6:
                    kat_risiko = "KRT"
                st.info(f"Kategori Risiko (Otomatis berdasarkan skor): **{kat_risiko}**")

            submitted_new = st.form_submit_button("Simpan Data Pasien Baru", type="primary")
            if submitted_new:
                if not new_nama or not new_nik:
                    st.error("Nama Ibu dan NIK wajib diisi!")
                else:
                    new_data = {
                        "id_ibu": new_id,
                        "nama_ibu": new_nama,
                        "nik": new_nik,
                        "nama_suami": new_suami,
                        "usia": new_usia,
                        "tempat_lahir": new_tempat,
                        "tanggal_lahir": new_tgl.strftime("%d-%m-%Y"),
                        "hpl": new_hpl.strftime("%d-%m-%Y"),
                        "usia_hamil": new_usia_hamil,
                        "alamat": new_alamat,
                        "alergi": new_alergi,
                        "riwayat_sakit": new_riwayat,
                        "tinggi_badan_cm": new_tinggi,
                        "jarak_kehamilan_tahun": new_jarak,
                        "jumlah_anak_hidup": new_anak,
                        "riwayat_caesar": new_caesar,
                        "tekanan_darah_sistol": new_sistol,
                        "tekanan_darah_diastol": new_diastol,
                        "skor_poedji_rochjati": new_skor,
                        "kategori_risiko": kat_risiko
                    }
                    from data_loader import add_new_patient
                    if add_new_patient(new_data):
                        st.success("Data pasien berhasil ditambahkan! Silakan refresh halaman untuk melihat pembaruan.")
                        # Clear cache or rerun
                    else:
                        st.error("Gagal menambahkan data.")

    with tab_update:
        st.subheader("Pilih Pasien untuk Diupdate")
        # Pilih pasien berdasarkan ID / Nama
        patient_options = df_raw['id_ibu'] + " - " + df_raw['nama_ibu']
        selected_patient_str = st.selectbox("Cari Pasien (ID - Nama)", options=["-- Pilih Pasien --"] + list(patient_options))
        
        if selected_patient_str != "-- Pilih Pasien --":
            selected_id = selected_patient_str.split(" - ")[0]
            patient_data = df_raw[df_raw['id_ibu'] == selected_id].iloc[0]
            
            with st.form("form_update_bumil"):
                st.write(f"Mengupdate data untuk: **{patient_data['nama_ibu']}** (ID: {selected_id})")
                
                u_col1, u_col2 = st.columns(2)
                with u_col1:
                    up_usia_hamil = st.text_input("Usia Hamil (misal: 24 Minggu)", value=str(patient_data['usia_hamil']))
                    up_sistol = st.number_input("Tekanan Darah Sistol", min_value=70, max_value=250, value=int(patient_data['tekanan_darah_sistol']))
                    up_diastol = st.number_input("Tekanan Darah Diastol", min_value=40, max_value=150, value=int(patient_data['tekanan_darah_diastol']))
                
                with u_col2:
                    up_skor = st.number_input("Skor Poedji Rochjati", min_value=2, max_value=30, value=int(patient_data['skor_poedji_rochjati']))
                    up_kat_risiko = "KRR"
                    if up_skor >= 12:
                        up_kat_risiko = "KRST"
                    elif up_skor >= 6:
                        up_kat_risiko = "KRT"
                    st.info(f"Kategori Risiko (Otomatis berdasarkan skor): **{up_kat_risiko}**")
                
                submitted_update = st.form_submit_button("Update Data Pemeriksaan", type="primary")
                if submitted_update:
                    update_payload = {
                        "usia_hamil": up_usia_hamil,
                        "tekanan_darah_sistol": up_sistol,
                        "tekanan_darah_diastol": up_diastol,
                        "skor_poedji_rochjati": up_skor,
                        "kategori_risiko": up_kat_risiko
                    }
                    from data_loader import update_patient
                    if update_patient(selected_id, update_payload):
                        st.success("Data pemeriksaan berhasil diupdate! Silakan refresh halaman untuk melihat pembaruan.")
                    else:
                        st.error("Gagal mengupdate data.")
