import streamlit as st
import pandas as pd
import plotly.express as px
import re

# --- Konfigurasi Halaman ---
st.set_page_config(layout="wide", page_title="Dashboard Volume Kuartalan")

# --- Judul Dashboard ---
st.title("📊 Dashboard Analisis Volume SID (Kuartalan) dengan Tiering")
st.markdown("Unggah file ringkasan kuartalan Anda untuk melihat pola volume SID dari waktu ke waktu.")

# --- 1. PENGUNGGAH FILE ---
uploaded_file = st.file_uploader("Pilih file CSV atau Excel", type=['csv', 'xlsx'])

if uploaded_file is None:
    st.info("Silakan unggah file data untuk melanjutkan.")
    st.stop()

# --- 2. PEMROSESAN DATA ---
@st.cache_data
def load_and_process_data(file):
    if file.name.endswith('.csv'):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    df.rename(columns={'Row Labels': 'Sender ID'}, inplace=True)

    # Urutkan SID berdasarkan Grand Total untuk menentukan peringkat
    df_sorted = df.sort_values('Grand Total', ascending=False).reset_index(drop=True)

    # --- PERUBAHAN 1: Ukuran tier ditetapkan menjadi 10 ---
    sids_per_tier = 10

    # Fungsi untuk menetapkan Tier berdasarkan peringkat
    def assign_tier(index):
        tier_number = (index // sids_per_tier) + 1
        start_rank = (tier_number - 1) * sids_per_tier + 1
        end_rank = tier_number * sids_per_tier
        return f"Tier {tier_number} (Top {start_rank}-{end_rank})"

    # Buat kolom Tier di dataframe yang sudah diurutkan
    df_sorted['Tier'] = df_sorted.index.to_series().apply(assign_tier)

    # --- Unpivot Data ---
    id_vars = ['Sender ID', 'Tier']
    value_vars = [col for col in df_sorted.columns if col.startswith('Q') and 'Grand Total' not in col]
    
    df_long = pd.melt(df_sorted, 
                      id_vars=id_vars, 
                      value_vars=value_vars, 
                      var_name='Kuartal', 
                      value_name='Volume')
    
    return df_long

try:
    df_processed = load_and_process_data(uploaded_file)
except Exception as e:
    st.error(f"Terjadi kesalahan saat memproses data: {e}")
    st.stop()

# --- 3. SIDEBAR UNTUK FILTER ---
st.sidebar.header("⚙️ Filter Data")

# --- PERUBAHAN 2: Memperbaiki urutan tier ---
# Ambil daftar tier unik dari data
tier_options_unsorted = df_processed['Tier'].unique()

# Fungsi untuk mengekstrak angka dari nama tier
def extract_tier_number(tier_string):
    match = re.search(r'Tier (\d+)', tier_string)
    return int(match.group(1)) if match else 0

# Urutkan daftar tier berdasarkan angka yang diekstrak
tier_options_sorted = sorted(tier_options_unsorted, key=extract_tier_number)

selected_tier = st.sidebar.selectbox(
    label="Pilih Tier Sender ID untuk ditampilkan:",
    options=tier_options_sorted
)
# --- AKHIR PERUBAHAN ---

st.sidebar.markdown("---")
show_button = st.sidebar.button("Tampilkan Visualisasi", type="primary")


# --- 4. VISUALISASI DATA ---
st.header("📈 Pola Volume per Kuartal")

if show_button:
    df_final = df_processed[df_processed['Tier'] == selected_tier]
    
    if df_final.empty:
        st.warning(f"Tidak ada data untuk {selected_tier}.")
        st.stop()

    st.subheader(f"Perubahan Volume dari Sender ID di {selected_tier}")
    fig = px.line(
        df_final,
        x='Kuartal',
        y='Volume',
        color='Sender ID',
        title=f'Perubahan Pola Volume SID per Kuartal untuk {selected_tier}',
        labels={'Kuartal': 'Kuartal', 'Volume': 'Total Volume Pesan'},
        markers=True
    )
    
    fig.update_layout(
        xaxis_title="Kuartal",
        yaxis_title="Total Volume Pesan",
        legend_title="Sender ID",
        xaxis={'categoryorder':'category ascending'}
    )
    fig.update_traces(marker=dict(size=8))

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Lihat Data yang Diproses untuk Tier Ini"):
        st.dataframe(df_final)
else:
    st.info("Atur filter di samping dan klik **'Tampilkan Visualisasi'**.")
