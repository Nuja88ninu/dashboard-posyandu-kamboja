"""
ollama_client.py
Modul integrasi dengan REST API Ollama lokal (http://localhost:11434).
Dilengkapi fallback response jika server offline atau model belum diunduh.
"""

import requests
import json

OLLAMA_BASE_URL = "http://127.0.0.1:11434"

def get_installed_models(base_url: str = OLLAMA_BASE_URL) -> list:
    """
    Mengambil daftar model yang telah terpasang di Ollama lokal.
    """
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            models = [m['name'] for m in data.get('models', [])]
            return models
    except Exception:
        pass
    return []

def check_ollama_status(base_url: str = OLLAMA_BASE_URL) -> bool:
    """
    Memeriksa apakah server Ollama sedang aktif dan berjalan.
    """
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=2)
        return resp.status_code == 200
    except Exception:
        return False

def generate_chat_response(messages: list, model: str = "llama3", dataset_context: str = "", base_url: str = OLLAMA_BASE_URL):
    """
    Menghasilkan respon chatbot dari Ollama via streaming atau fallback cerdas.
    """
    # System prompt berkonteks medis kehamilan
    system_instruction = (
        "Anda adalah 'BumilCare AI', asisten cerdas spesialis kesehatan ibu dan janin untuk bidan dan tenaga medis di Posyandu/Puskesmas. "
        "Anda memahami sistem skoring risiko kehamilan Poedji Rochjati (KRR = Risiko Rendah Skor 2, KRT = Risiko Tinggi Skor 6-10, KRST = Risiko Sangat Tinggi Skor >=12). "
        "Jawab dengan bahasa Indonesia yang ramah, profesional, solutif, berbasis bukti klinis, dan mudah dipahami. "
        "Jika ada pertanyaan tentang data spesifik dari dashboard, gunakan ringkasan data yang diberikan."
    )
    
    if dataset_context:
        system_instruction += f"\n\n[Ringkasan Data Dashboard Kehamilan Saat Ini]:\n{dataset_context}"

    # Cek koneksi ke Ollama
    is_connected = check_ollama_status(base_url)
    available_models = get_installed_models(base_url) if is_connected else []
    
    if is_connected and model in available_models:
        payload = {
            "model": model,
            "messages": [{"role": "system", "content": system_instruction}] + messages,
            "stream": True
        }
        try:
            with requests.post(f"{base_url}/api/chat", json=payload, stream=True, timeout=60) as resp:
                if resp.status_code == 200:
                    for line in resp.iter_lines():
                        if line:
                            data = json.loads(line.decode("utf-8"))
                            msg = data.get("message", {}).get("content", "")
                            if msg:
                                yield msg
                    return
                else:
                    yield f"*(Ollama API mengembalikan status {resp.status_code}, beralih ke Asisten Bidan Klinis internal...)*\n\n"
        except Exception as e:
            yield f"*(Gagal menghubungi Ollama: {str(e)}. Menggunakan asisten internal)*\n\n"
    elif is_connected and not available_models:
        yield f"*(Server Ollama aktif di `{base_url}`, tetapi belum ada model yang di-pull. Contoh perintah: `ollama run llama3` atau `ollama run gemma2`. Menjawab via Asisten BumilCare Terprogram)*\n\n"
    else:
        yield "*(Ollama lokal tidak terdeteksi aktif di port 11434. Menjawab via Engine Asisten BumilCare Terprogram)*\n\n"

    # Fallback Intelligent Medical Assistant
    last_user_msg = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            last_user_msg = m.get("content", "").lower()
            break
            
    response_text = _generate_rule_based_response(last_user_msg, dataset_context)
    # Stream the fallback text
    import time
    for word in response_text.split(" "):
        yield word + " "
        time.sleep(0.015)

def _generate_rule_based_response(query: str, dataset_context: str) -> str:
    """
    Aturan respon cerdas seputar kehamilan, skrining Poedji Rochjati, dan data.
    """
    q = query.lower()
    
    if any(k in q for k in ["apa itu", "pengertian", "definisi", "arti"]) and any(k in q for k in ["krr", "krt", "krst", "poedji", "rochjati"]):
        return (
            "**Klasifikasi Risiko Kehamilan Menurut Poedji Rochjati:**\n\n"
            "1. **KRR (Kehamilan Risiko Rendah)** - *Skor 2*:\n"
            "   - Kehamilan fisiologis tanpa faktor risiko khusus yang mengancam.\n"
            "   - Pertolongan persalinan dapat dilakukan oleh **Bidan** di Puskesmas, Polindes, atau BPM.\n\n"
            "2. **KRT (Kehamilan Risiko Tinggi)** - *Skor 6 - 10*:\n"
            "   - Kehamilan dengan salah satu faktor risiko (misal: usia <20 atau >=35 tahun, tinggi badan <145 cm, riwayat SC, jarak hamil <2 tahun, hipertensi kronik).\n"
            "   - Memerlukan rujukan terencana ke dokter atau fasilitas pelayanan kesehatan rujukan tingkat pertama (FKTP / RS).\n\n"
            "3. **KRST (Kehamilan Risiko Sangat Tinggi)** - *Skor >= 12*:\n"
            "   - Kehamilan dengan risiko ganda/berat (misal: riwayat SC ditambah komplikasi, preeklamsia berat, perdarahan antepartum, penyakit penyerta berat).\n"
            "   - Persalinan **wajib di Rumah Sakit** yang memiliki dokter spesialis Obgyn dan fasilitas penanganan gawat darurat neonatal."
        )
    
    if any(k in q for k in ["hipertensi", "tensi", "tekanan darah", "darah tinggi"]):
        return (
            "**Penanganan Hipertensi pada Ibu Hamil:**\n\n"
            "- **Definisi:** Tekanan darah sistol ≥ 140 mmHg dan/atau diastol ≥ 90 mmHg.\n"
            "- **Bahaya:** Berisiko berkembang menjadi **Preeklamsia / Eklamsia**, solusio plasenta, atau IUGR (janin terhambat).\n"
            "- **Langkah Bidan/Nakes:**\n"
            "  1. Periksa proteinuria urin (skrining preeklamsia).\n"
            "  2. Pantau tanda bahaya: nyeri kepala hebat, pandangan kabur, nyeri ulu hati, bengkak ekstremitas/wajah.\n"
            "  3. Rujuk ke Dokter Spesialis Obgyn untuk pemberian antihipertensi yang aman (seperti Metildopa atau Nifedipin) bila diindikasikan.\n"
            "  4. Kurangi konsumsi garam berlebih, cukupi istirahat baring miring ke kiri."
        )
        
    if any(k in q for k in ["anemia", "kurang darah", "hb"]):
        return (
            "**Pencegahan & Tata Laksana Anemia pada Bumil:**\n\n"
            "- Anemia pada kehamilan (Hb < 11 g/dL pada trimester 1 & 3, atau < 10.5 g/dL pada trimester 2) meningkatkan risiko perdarahan pasca salin, BBLR, dan stunting.\n"
            "- **Rekomendasi:**\n"
            "  - Konsumsi Tablet Tambah Darah (TTD) minimal 90 tablet selama kehamilan.\n"
            "  - Minum TTD bersama air putih atau jus jeruk (vitamin C membantu penyerapan zat besi).\n"
            "  - Hindari minum TTD bersama teh, kopi, atau susu karena menghambat penyerapan.\n"
            "  - Asupan makanan bergizi tinggi zat besi hewani (hati ayam, daging tanpa lemak, telur, ikan)."
        )
        
    if any(k in q for k in ["caesar", "sc", "sesar", "operasi"]):
        return (
            "**Ibu Hamil dengan Riwayat Caesar (Bekas SC):**\n\n"
            "- Riwayat SC otomatis memberikan skor risiko tambahan pada Poedji Rochjati (Skor +8).\n"
            "- Risiko utama adalah terjadinya ruptur uteri (robekan rahim) pada bekas jahitan.\n"
            "- **Protokol:**\n"
            "  1. Cek jarak kehamilan: jarak < 2 tahun meningkatkan risiko komplikasi bekas luka rahim.\n"
            "  2. Wajib konsultasi ke Sp.OG pada trimester ke-3 untuk evaluasi ketebalan segmen bawah rahim (SBR).\n"
            "  3. Rencanakan persalinan di Rumah Sakit dengan kesiapan operasi darurat 24 jam."
        )

    if any(k in q for k in ["jumlah", "berapa", "data", "statistik", "total", "ringkasan", "laporan"]):
        return (
            "**Ringkasan Statistik Kehamilan dari Dataset:**\n\n"
            f"{dataset_context if dataset_context else 'Dataset mencakup 504 ibu hamil yang dikategorikan ke dalam KRR, KRT, dan KRST.'}\n\n"
            "📌 **Poin Penting:**\n"
            "- Kategori KRT mendominasi (~65% dari total kasus).\n"
            "- Kasus KRST memerlukan pemantauan ketat buku KIA dan koordinasi rujukan dini berencana (RDB)."
        )
        
    return (
        "Halo! Saya **BumilCare AI**, asisten pemantauan kesehatan ibu hamil.\n\n"
        "Anda dapat menanyakan hal-hal berikut:\n"
        "- *'Jelaskan perbedaan KRR, KRT, dan KRST'*;\n"
        "- *'Bagaimana penanganan ibu hamil dengan hipertensi atau anemia?'*;\n"
        "- *'Apa langkah untuk ibu dengan riwayat operasi caesar?'*;\n"
        "- *'Berapa jumlah bumil risiko sangat tinggi (KRST) di wilayah ini?'*;\n"
        "- Panduan gizi, tanda bahaya trimester, dan persiapan persalinan aman.\n\n"
        "Ada yang bisa saya bantu terkait data ibu hamil hari ini?"
    )
