import streamlit as st
import requests
from datetime import datetime
from docxtpl import DocxTemplate
from io import BytesIO

# ================= KONFIGURASI =================
st.set_page_config(page_title="Layanan SK Aktif", page_icon="📝", layout="centered")

# --- VERSI AMAN (BACA DARI CLOUD SECRETS) ---
try:
    TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
    GROUP_ADMIN_ID = st.secrets["GROUP_ADMIN_ID"]
except:
    st.warning("⚠️ Konfigurasi Token belum dipasang di Streamlit Cloud.")
    st.stop()
# -------------------------------------------

TEMPLATE_SKA = "template_ska.docx"

# CSS Tampilan Mewah
st.markdown("""
    <style>
    .stApp { background-color: #1a2a3a; color: #ffffff; }
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stTextArea>div>div>textarea {
        background-color: #2c3e50 !important; color: white !important;
        border: 1px solid #d4af37 !important; border-radius: 8px !important;
    }
    h1, h2, h3 { color: #d4af37 !important; }
    .stButton>button {
        background: linear-gradient(45deg, #d4af37, #b8860b) !important;
        color: #1a2a3a !important; font-weight: bold !important; width: 100%;
        height: 50px; border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# ================= FUNGSI HELPER =================
def format_wa(nomor):
    n = nomor.strip().replace("-", "").replace(" ", "").replace("+", "")
    if n.startswith("0"): return "62" + n[1:]
    return n

def get_periode_iain():
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

TA, SEM, BLN_ROM, THN, TGL_LENGKAP = get_periode_iain()

def kirim_ke_admin(file_bytes, filename, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
    files = {'document': (filename, file_bytes, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
    data = {'chat_id': GROUP_ADMIN_ID, 'caption': caption, 'parse_mode': 'HTML'}
    
    try:
        resp = requests.post(url, data=data, files=files)
        if resp.status_code != 200:
            st.error("⛔ TELEGRAM MENOLAK PESAN!")
            return False
        return True
    except Exception as e:
        st.error(f"⛔ Gagal Koneksi: {e}")
        return False

# ================= UI APLIKASI =================
st.title("📝 Permohonan SK Aktif Kuliah")
st.info(f"Semester {SEM} Tahun Akademik {TA}")

with st.form("form_ska"):
    c1, c2 = st.columns(2)
    nama = c1.text_input("Nama Lengkap")
    nim = c2.text_input("NIM")
    
    c3, c4 = st.columns(2)
    tmp_lahir = c3.text_input("Tempat Lahir")
    tgl_lahir = c4.text_input("Tanggal Lahir")
    
    prodi = st.selectbox("Program Studi", [
        "Pendidikan Agama Islam", "Manajemen Pendidikan Islam", 
        "Pendidikan Bahasa Arab", "Pendidikan Guru Madrasah Ibtidaiyah",
        "Pendidikan Islam Anak Usia Dini", "Tadris Matematika", "Tadris Biologi", "Bimbingan Konseling dan Pendidikan Islam"
    ])
    
    c5, c6 = st.columns(2)
    semester_mhs = c5.text_input("Semester (Romawi)")
    wa = c6.text_input("Nomor WhatsApp")
    alamat = st.text_area("Alamat")
    
    tombol = st.form_submit_button("🚀 KIRIM DATA")

    if tombol:
        if not nama or not wa:
            st.error("Nama dan WA wajib diisi!")
        else:
            with st.spinner("Mengirim ke Admin..."):
                doc = DocxTemplate(TEMPLATE_SKA)
                context = {
                    'nama': nama.upper(), 'nim': nim,
                    'tempat_lahir': tmp_lahir, 'tanggal_lahir': tgl_lahir,
                    'program_studi': prodi, 'semester': semester_mhs,
                    'alamat': alamat, 'tahun_akademik': TA,
                    'bulan': BLN_ROM, 'tahun': THN,
                    'tanggal_pembuatan': TGL_LENGKAP
                }
                doc.render(context)
                buffer = BytesIO()
                doc.save(buffer)
                buffer.seek(0)
                
                link_wa = f"https://wa.me/{format_wa(wa)}?text=Assalamu'alaikum,%20berikut%20Surat%20Keterangan%20Aktif%20Anda."
                pesan = f"SK AKTIF BARU:\n{nama}\n<a href='{link_wa}'>KIRIM WA</a>"
                
                if kirim_ke_admin(buffer.getvalue(), f"SKA_{nim}.docx", pesan):
                    st.balloons()
                    st.success("✅ BERHASIL! Admin akan memproses dan mengirim ke WA Anda.")