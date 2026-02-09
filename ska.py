import streamlit as st
import requests
import html 
from datetime import datetime
from docxtpl import DocxTemplate
from io import BytesIO

# ================= KONFIGURASI HALAMAN =================
st.set_page_config(page_title="SKA FTIK Digital", page_icon="📝", layout="centered")

# Mengambil Secrets dari Streamlit Cloud
try:
    # Pastikan di Secrets tidak ada spasi tambahan
    TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"].strip()
    GROUP_ADMIN_ID = st.secrets["GROUP_ADMIN_ID"].strip()
except Exception as e:
    st.error("⚠️ Konfigurasi Secrets (TELEGRAM_TOKEN / GROUP_ADMIN_ID) belum lengkap!")
    st.stop()

TEMPLATE_SKA = "template_ska.docx"

# CSS Dark Theme Premium (Anti-Silau)
st.markdown("""
    <style>
    .stApp { background-color: #1a2a3a; color: #ffffff; }
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stTextArea>div>div>textarea {
        background-color: #2c3e50 !important; color: white !important;
        border: 1px solid #d4af37 !important; border-radius: 8px !important;
    }
    h1, h2, h3 { color: #d4af37 !important; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); }
    .stButton>button {
        background: linear-gradient(45deg, #d4af37, #b8860b) !important;
        color: #1a2a3a !important; font-weight: bold !important; width: 100%;
        height: 50px; border-radius: 10px; border: none;
    }
    .stFileUploader section { background-color: #2c3e50 !important; border: 1px dashed #d4af37 !important; }
    </style>
    """, unsafe_allow_html=True)

# ================= FUNGSI HELPER =================

def format_wa(nomor):
    """Konversi nomor 08xx ke 628xx"""
    n = nomor.strip().replace("-", "").replace(" ", "").replace("+", "")
    if n.startswith("0"): return "62" + n[1:]
    return n

def get_periode_iain():
    """Logika Akademik IAIN Ternate"""
    now = datetime.now()
    bln = now.month
    thn = now.year
    if bln >= 8 or bln == 1:
        sem_txt = "Ganjil"
        ta = f"{thn}/{thn+1}" if bln >= 8 else f"{thn-1}/{thn}"
    else:
        sem_txt = "Genap"
        ta = f"{thn-1}/{thn}"
    
    romawi = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]
    indo_bln = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    return ta, sem_txt, romawi[bln-1], thn, f"{now.day} {indo_bln[bln-1]} {thn}"

TA, SEM_AKTIF, BULAN_ROM, TAHUN_NOW, TGL_LENGKAP = get_periode_iain()

def kirim_paket_ke_admin(doc_bytes, doc_name, caption, ktm_file, bayar_file):
    """Mengirim Dokumen SKA dan Berkas Validasi ke Telegram"""
    token = TELEGRAM_TOKEN
    chat_id = GROUP_ADMIN_ID
    
    # 1. Kirim Dokumen Word SKA
    url_doc = f"https://api.telegram.org/bot{token}/sendDocument"
    files_doc = {'document': (doc_name, doc_bytes)}
    
    # Coba kirim dengan HTML
    resp_doc = requests.post(
        url_doc, 
        data={'chat_id': chat_id, 'caption': caption, 'parse_mode': 'HTML'}, 
        files=files_doc
    )
    
    # JIKA GAGAL (Biasanya karena error parse HTML), kirim ulang tanpa format HTML agar file tetap sampai
    if resp_doc.status_code != 200:
        # Bersihkan caption dari tag HTML untuk kiriman cadangan
        clean_caption = caption.replace("<b>","").replace("</b>","").replace("<code>","").replace("</code>","").replace("<a href='","").replace("'>"," ").replace("</a>","")
        requests.post(
            url_doc, 
            data={'chat_id': chat_id, 'caption': f"⚠️ PENGAJUAN (Format Error):\n{clean_caption}"}, 
            files=files_doc
        )

    # 2. Kirim Bukti Validasi (KTM)
    if ktm_file:
        url_photo = f"https://api.telegram.org/bot{token}/sendPhoto"
        requests.post(url_photo, 
                      data={'chat_id': chat_id, 'caption': f"🪪 KTM: {doc_name}"}, 
                      files={'photo': ktm_file.getvalue()})
    
    # 3. Kirim Bukti Validasi (Pembayaran)
    if bayar_file:
        url_photo = f"https://api.telegram.org/bot{token}/sendPhoto"
        requests.post(url_photo, 
                      data={'chat_id': chat_id, 'caption': f"💰 Bukti Bayar: {doc_name}"}, 
                      files={'photo': bayar_file.getvalue()})
    return True

# ================= UI APLIKASI =================
st.title("📝 Permohonan SK Aktif Kuliah")
st.subheader(f"Semester {SEM_AKTIF} TA {TA}")

with st.form("form_ska_lengkap"):
    st.info("🎓 **Identitas Mahasiswa**")
    c1, c2 = st.columns(2)
    nama = c1.text_input("Nama Lengkap (Sesuai KTM)")
    nim = c2.text_input("NIM")
    
    c3, c4 = st.columns(2)
    tmp_lahir = c3.text_input("Tempat Lahir")
    tgl_lahir = c4.text_input("Tanggal Lahir (Cth: 10 Agustus 2002)")
    
    prodi = st.selectbox("Program Studi", [
        "Pendidikan Agama Islam", "Manajemen Pendidikan Islam", "Bimbingan Konseling dan Pendidikan Islam",
        "Pendidikan Bahasa Arab", "Pendidikan Guru Madrasah Ibtidaiyah",
        "Pendidikan Islam Anak Usia Dini", "Tadris Matematika", "Tadris Biologi"
    ])
    
    c5, c6 = st.columns(2)
    semester_angka = c5.text_input("Semester (Angka Romawi, Misal: VII)")
    wa = c6.text_input("Nomor WhatsApp Aktif")
    
    alamat = st.text_area("Alamat Lengkap di Ternate")
    
    st.markdown("---")
    st.info("📂 **Validasi Berkas (Wajib)**")
    col_u1, col_u2 = st.columns(2)
    up_ktm = col_u1.file_uploader("Upload Foto KTM", type=['jpg', 'jpeg', 'png'])
    up_bayar = col_u2.file_uploader("Upload Bukti Bayar Semester Berjalan", type=['jpg', 'jpeg', 'png'])

    st.warning("⚠️ Admin akan memverifikasi berkas Anda sebelum menerbitkan surat.")
    
    submit = st.form_submit_button("🚀 AJUKAN SEKARANG")

    if submit:
        if not all([nama, nim, wa, up_ktm, up_bayar]):
            st.error("❌ GAGAL: Semua kolom identitas dan berkas wajib diisi!")
        else:
            with st.spinner("Sedang memproses dokumen dan mengupload berkas..."):
                try:
                    # 1. Olah Template Word
                    doc = DocxTemplate(TEMPLATE_SKA)
                    context = {
                        'nama': nama.upper(),
                        'nim': nim,
                        'tempat_lahir': tmp_lahir,
                        'tanggal_lahir': tgl_lahir,
                        'program_studi': prodi,
                        'semester': semester_angka,
                        'alamat': alamat,
                        'tahun_akademik': TA,
                        'bulan': BULAN_ROM,
                        'tahun': TAHUN_NOW,
                        'tanggal_pembuatan': TGL_LENGKAP
                    }
                    doc.render(context)
                    
                    buffer = BytesIO()
                    doc.save(buffer)
                    doc_bytes = buffer.getvalue()
                    
                    # 2. Penamaan File (Hanya Nama Depan sesuai instruksi)
                    nama_depan = nama.strip().split()[0]
                    nama_clean = "".join(x for x in nama_depan if x.isalnum())
                    nama_file_final = f"SKA_{nim}_{nama_clean}.docx"
                    
                    # 3. Siapkan Link WA
                    link_wa = f"https://wa.me/{format_wa(wa)}?text=Assalamu'alaikum,%20berikut%20Surat%20Keterangan%20Aktif%20Kuliah%20Anda."
                    
                    # 4. Proteksi karakter khusus untuk HTML Telegram
                    nama_safe = html.escape(nama.upper())
                    prodi_safe = html.escape(prodi)

                    # 5. Caption Notifikasi
                    pesan_admin = (
                        f"<b>🔔 PENGAJUAN SKA BARU</b>\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"👤 <b>{nama_safe}</b>\n"
                        f"🆔 NIM: <code>{nim}</code>\n"
                        f"📚 {prodi_safe}\n\n"
                        f"👉 <a href='{link_wa}'><b>KLIK UNTUK KIRIM BALIK WA</b></a>\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"<i>Cek lampiran KTM & Bukti Bayar di bawah.</i>"
                    )
                    
                    # 6. Eksekusi Pengiriman
                    if kirim_paket_ke_admin(doc_bytes, nama_file_final, pesan_admin, up_ktm, up_bayar):
                        st.success("✅ BERHASIL! Permohonan dan berkas validasi Anda telah dikirim ke Admin.")
                        st.balloons()
                    else:
                        st.error("Terjadi masalah saat mengirim ke Telegram.")
                        
                except Exception as e:
                    st.error(f"Terjadi kesalahan teknis: {e}")
