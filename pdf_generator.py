"""
pdf_generator.py
Modul untuk membuat Laporan Analisis Keseluruhan Skrining Kehamilan (KRR, KRT, KRST)
dalam format PDF formal, modern, dan rapi menggunakan ReportLab.
"""

import os
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)

def generate_pdf_report(summary: dict, output_filepath: str = None) -> bytes:
    """
    Menghasilkan dokumen PDF Laporan Analisis Skrining Kehamilan.
    Jika output_filepath diberikan, file akan disimpan ke disk.
    Mengembalikan raw bytes PDF untuk unduhan langsung di Streamlit.
    """
    buffer = io.BytesIO()
    
    # Target canvas
    target = output_filepath if output_filepath else buffer
    doc = SimpleDocTemplate(
        target,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm
    )
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Custom Palette
    COLOR_PRIMARY = colors.HexColor("#0369a1")    # Deep Teal/Blue
    COLOR_SECONDARY = colors.HexColor("#0f172a")  # Slate 900
    COLOR_MUTED = colors.HexColor("#64748b")      # Slate 500
    COLOR_KRR = colors.HexColor("#15803d")        # Emerald Green
    COLOR_KRT = colors.HexColor("#b45309")        # Amber
    COLOR_KRST = colors.HexColor("#b91c1c")       # Crimson Red
    COLOR_BG_LIGHT = colors.HexColor("#f8fafc")   # Slate 50
    
    # Custom Paragraph Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=COLOR_PRIMARY,
        alignment=0,
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=COLOR_MUTED,
        spaceAfter=14
    )
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=COLOR_PRIMARY,
        spaceBefore=12,
        spaceAfter=6
    )
    
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=COLOR_SECONDARY,
        spaceAfter=6
    )
    
    bullet_style = ParagraphStyle(
        'BulletStyle',
        parent=body_style,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=4
    )
    
    table_text_style = ParagraphStyle(
        'TableText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=COLOR_SECONDARY
    )
    
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.white
    )

    story = []

    # 1. HEADER DOKUMEN / KOP RESMI
    story.append(Paragraph("LAPORAN ANALISIS KESELURUHAN SKRINING KEHAMILAN", title_style))
    story.append(Paragraph("Sistem Monitoring Kehamilan Berdasarkan Skoring Poedji Rochjati (KRR, KRT, KRST)", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=COLOR_PRIMARY, spaceBefore=0, spaceAfter=14))

    # 2. RINGKASAN EKSEKUTIF (EXECUTIVE SUMMARY)
    story.append(Paragraph("1. Ringkasan Eksekutif", section_title_style))
    total = summary['total_bumil']
    krt_krst_total = summary['krt_count'] + summary['krst_count']
    krt_krst_pct = round((krt_krst_total / total) * 100, 1) if total else 0
    
    exec_summary_text = (
        f"Laporan ini menyajikan hasil analisis komprehensif terhadap <b>{total} data ibu hamil</b> di wilayah kerja binaan "
        f"(Lebak Wangi dan Perum Duta Asri). Berdasarkan sistem skoring Poedji Rochjati, ditemukan bahwa "
        f"<b>{krt_krst_total} ibu hamil ({krt_krst_pct}%)</b> berada dalam kategori kehamilan berisiko (KRT dan KRST), "
        f"sedangkan hanya <b>{summary['krr_count']} ibu hamil ({summary['krr_pct']}%)</b> yang tergolong dalam Kehamilan Risiko Rendah (KRR). "
        f"Tingginya proporsi kehamilan berisiko menuntut pengawasan klinis ketat, pemenuhan skrining USG ANC terpadu, "
        f"serta kesiapan sistem Rujukan Dini Berencana (RDB) ke Fasilitas Kesehatan Rujukan Tingkat Lanjutan (FKRTL/RS PONEK)."
    )
    story.append(Paragraph(exec_summary_text, body_style))
    story.append(Spacer(1, 8))

    # 3. TABEL DISTRIBUSI 3 KATEGORI RISIKO (KRR, KRT, KRST)
    story.append(Paragraph("2. Distribusi Kategori Risiko (Poedji Rochjati)", section_title_style))
    
    table_risk_data = [
        [
            Paragraph("Kategori Risiko", table_header_style),
            Paragraph("Rentang Skor PR", table_header_style),
            Paragraph("Jumlah (Orang)", table_header_style),
            Paragraph("Persentase (%)", table_header_style),
            Paragraph("Rekomendasi Tempat & Penolong Bersalin", table_header_style)
        ],
        [
            Paragraph("<b>KRR</b> (Risiko Rendah)", table_text_style),
            Paragraph("Skor = 2", table_text_style),
            Paragraph(f"<b>{summary['krr_count']}</b>", table_text_style),
            Paragraph(f"<b>{summary['krr_pct']}%</b>", table_text_style),
            Paragraph("Bidan di Polindes, Puskesmas, atau BPM Mandiri", table_text_style)
        ],
        [
            Paragraph("<b>KRT</b> (Risiko Tinggi)", table_text_style),
            Paragraph("Skor 6 - 10", table_text_style),
            Paragraph(f"<b>{summary['krt_count']}</b>", table_text_style),
            Paragraph(f"<b>{summary['krt_pct']}%</b>", table_text_style),
            Paragraph("Bidan didampingi Dokter di Puskesmas / Rujukan Terencana RS", table_text_style)
        ],
        [
            Paragraph("<b>KRST</b> (Risiko Sgt Tinggi)", table_text_style),
            Paragraph("Skor ≥ 12 (Maks 22)", table_text_style),
            Paragraph(f"<b>{summary['krst_count']}</b>", table_text_style),
            Paragraph(f"<b>{summary['krst_pct']}%</b>", table_text_style),
            Paragraph("<b>Wajib di Rumah Sakit PONEK</b> bersama Dokter Spesialis Obgyn", table_text_style)
        ],
        [
            Paragraph("<b>TOTAL</b>", table_text_style),
            Paragraph("-", table_text_style),
            Paragraph(f"<b>{total}</b>", table_text_style),
            Paragraph("<b>100.0%</b>", table_text_style),
            Paragraph("-", table_text_style)
        ]
    ]

    t_risk = Table(table_risk_data, colWidths=[3.2*cm, 2.5*cm, 2.4*cm, 2.4*cm, 7.0*cm])
    t_risk.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, COLOR_BG_LIGHT]),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_risk)
    story.append(Spacer(1, 12))

    # 4. TEMUAN FAKTOR RISIKO KLINIS UTAMA
    story.append(Paragraph("3. Faktor Risiko Klinis & Komorbiditas Dominan", section_title_style))
    
    table_factors_data = [
        [
            Paragraph("Faktor Risiko / Komplikasi", table_header_style),
            Paragraph("Jumlah Kasus", table_header_style),
            Paragraph("Prevalensi (%)", table_header_style),
            Paragraph("Dampak & Catatan Klinis", table_header_style)
        ],
        [
            Paragraph("<b>Tekanan Darah Tinggi / Hipertensi</b> (≥140/90 mmHg)", table_text_style),
            Paragraph(str(summary['hipertensi_count']), table_text_style),
            Paragraph(f"{summary['hipertensi_pct']}%", table_text_style),
            Paragraph("Faktor risiko tertinggi preeklamsia berat, solusio plasenta, dan IUGR.", table_text_style)
        ],
        [
            Paragraph("<b>Usia Rentan Reproduksi</b> (<20 th atau ≥35 th)", table_text_style),
            Paragraph(str(summary['usia_risiko_count']), table_text_style),
            Paragraph(f"{summary['usia_risiko_pct']}%", table_text_style),
            Paragraph("Usia muda berisiko panggul sempit; usia tua rentan komplikasi metabolik/kromosom.", table_text_style)
        ],
        [
            Paragraph("<b>Risiko Panggul Sempit</b> (Tinggi Badan <145 cm)", table_text_style),
            Paragraph(str(summary['panggul_sempit_count']), table_text_style),
            Paragraph(f"{summary['panggul_sempit_pct']}%", table_text_style),
            Paragraph("Potensi disproporsi kepala panggul (CPD) yang memicu partus macet.", table_text_style)
        ],
        [
            Paragraph("<b>Riwayat Bekas Operasi Caesar (SC)</b>", table_text_style),
            Paragraph(str(summary['caesar_count']), table_text_style),
            Paragraph(f"{summary['caesar_pct']}%", table_text_style),
            Paragraph("Risiko ruptur uteri; evaluasi ketebalan SBR di Trimester 3 wajib dilakukan.", table_text_style)
        ]
    ]

    t_factors = Table(table_factors_data, colWidths=[5.5*cm, 2.5*cm, 2.5*cm, 7.0*cm])
    t_factors.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0284c7")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_BG_LIGHT]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_factors)
    story.append(Spacer(1, 10))

    # Komorbiditas Penyakit & Alergi
    penyakit_str = ", ".join([f"{k} ({v} kasus)" for k, v in list(summary['penyakit_counts'].items())[:5]])
    alergi_str = ", ".join([f"{k} ({v} kasus)" for k, v in list(summary['alergi_counts'].items())[:5]])
    
    story.append(Paragraph(f"• <b>Riwayat Penyakit Terbanyak:</b> {penyakit_str}.", bullet_style))
    story.append(Paragraph(f"• <b>Riwayat Alergi Terbanyak:</b> {alergi_str} (Perhatian khusus alergi Penisilin pada pemberian profilaksis persalinan).", bullet_style))
    story.append(Spacer(1, 10))

    # 5. REKOMENDASI TINDAK LANJUT BERJENJANG
    story.append(Paragraph("4. Rekomendasi Tindak Lanjut Program Kesehatan Ibu", section_title_style))
    
    recs = [
        "<b>Bagi Kader Posyandu:</b> Pemasangan stiker P4K di rumah seluruh ibu hamil, pendampingan kepatuhan konsumsi 90 Tablet Tambah Darah (TTD) dan kalsium, serta pemantauan donor darah keluarga siaga.",
        "<b>Bagi Bidan & Puskesmas:</b> Penguatan skrining preeklamsia terpadu (pemeriksaan tensi berkala & protein urine) pada 202 ibu bertekanan darah tinggi. Koordinasi Rujukan Dini Berencana (RDB) bagi 100 ibu hamil KRST sebelum timbul tanda inpartu.",
        "<b>Bagi Rumah Sakit Rujukan (PONEK):</b> Kesiapsiagaan fasilitas penanganan gawat darurat obstetri neonatal 24 jam, ketersediaan darah, dan penjadwalan persalinan terencana pada kasus bekas SC dan disproporsi panggul.",
        "<b>Integrasi Chatbot AI BumilCare:</b> Pemanfaatan asisten digital terintegrasi untuk mendukung konsultasi harian kader dan bidan dalam menjawab pertanyaan seputar skrining risiko dan pencegahan komplikasi."
    ]
    for r in recs:
        story.append(Paragraph(f"• {r}", bullet_style))

    story.append(Spacer(1, 16))

    # 6. TANDA TANGAN & PENGESAHAN
    ttd_data = [
        [
            Paragraph("Mengetahui,<br/><b>Koordinator Bidan Puskesmas</b><br/><br/><br/><br/>___________________________<br/>NIP. ....................................", table_text_style),
            Paragraph("Disusun Oleh,<br/><b>Tim Analis MaternalCare</b><br/><br/><br/><br/>___________________________<br/>Tanggal: September 2026", table_text_style)
        ]
    ]
    t_ttd = Table(ttd_data, colWidths=[9.0*cm, 8.5*cm])
    t_ttd.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(KeepTogether(t_ttd))

    # Build PDF
    doc.build(story)
    
    if output_filepath:
        with open(output_filepath, 'rb') as f:
            return f.read()
    else:
        buffer.seek(0)
        return buffer.getvalue()

if __name__ == "__main__":
    from data_loader import load_data, get_overall_summary
    df = load_data("dataset_ibu_hamil_kamboja2b.csv")
    summary = get_overall_summary(df)
    pdf_path = "Laporan_Analisis_Ibu_Hamil_MaternalCare.pdf"
    generate_pdf_report(summary, pdf_path)
    print(f"PDF berhasil dibuat: {pdf_path} (Ukuran: {os.path.getsize(pdf_path)} bytes)")
