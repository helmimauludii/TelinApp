import streamlit as st
import pandas as pd
import plotly.express as px
import re

# --- Konfigurasi Halaman ---
st.set_page_config(layout="wide", page_title="Dashboard Volume Kuartalan")

# --- Judul Dashboard ---
st.title("📊 Dashboard Analisis Volume SID (Kuartalan)")
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

    sids_per_tier = 10

    def assign_tier(index):
        tier_number = (index // sids_per_tier) + 1
        start_rank = (tier_number - 1) * sids_per_tier + 1
        end_rank = tier_number * sids_per_tier
        return f"Tier {tier_number} (Top {start_rank}-{end_rank})"

    df_sorted['Tier'] = df_sorted.index.to_series().apply(assign_tier)

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

analysis_mode = st.sidebar.radio(
    "Pilih Mode Analisis:",
    ("Analisis per Tier", "Cari SID Spesifik")
)

if analysis_mode == "Analisis per Tier":
    tier_options_unsorted = df_processed['Tier'].unique()
    def extract_tier_number(tier_string):
        match = re.search(r'Tier (\d+)', tier_string)
        return int(match.group(1)) if match else 0
    tier_options_sorted = sorted(tier_options_unsorted, key=extract_tier_number)
    
    selected_tier = st.sidebar.selectbox(
        label="Pilih Tier Sender ID:",
        options=tier_options_sorted
    )
else: # Mode "Cari SID Spesifik"
    all_sids = sorted(df_processed['Sender ID'].unique())
    # --- PERUBAHAN UTAMA: Ganti selectbox menjadi multiselect ---
    selected_sids = st.sidebar.multiselect(
        "Ketik atau pilih beberapa Sender ID:",
        options=all_sids,
        default=[] # Default kosong
    )
    # --- AKHIR PERUBAHAN ---

st.sidebar.markdown("---")
show_button = st.sidebar.button("Tampilkan Visualisasi", type="primary")


# --- 4. VISUALISASI DATA ---
st.header("📈 Pola Volume per Kuartal")

if show_button:
    if analysis_mode == "Analisis per Tier":
        df_final = df_processed[df_processed['Tier'] == selected_tier]
        
        if df_final.empty:
            st.warning(f"Tidak ada data untuk {selected_tier}.")
        else:
            st.subheader(f"Perubahan Volume dari Sender ID di {selected_tier}")
            fig = px.line(df_final, x='Kuartal', y='Volume', color='Sender ID',
                          title=f'Pola Volume SID per Kuartal untuk {selected_tier}',
                          labels={'Kuartal': 'Kuartal', 'Volume': 'Total Volume Pesan'},
                          markers=True)
            fig.update_layout(xaxis={'categoryorder':'category ascending'})
            st.plotly_chart(fig, use_container_width=True)
            with st.expander("Lihat Data yang Diproses"):
                st.dataframe(df_final)

    else: # Mode "Cari SID Spesifik"
        # --- PERUBAHAN UTAMA: Sesuaikan logika untuk menangani multiple SIDs ---
        if not selected_sids:
            st.warning("Silakan pilih minimal satu Sender ID untuk ditampilkan.")
        else:
            df_final = df_processed[df_processed['Sender ID'].isin(selected_sids)]

            if df_final.empty:
                st.warning(f"Tidak ada data untuk SID yang dipilih.")
            else:
                st.subheader(f"Perbandingan Volume untuk SID yang Dipilih")
                fig = px.line(df_final, x='Kuartal', y='Volume', color='Sender ID', # Color by SID
                              title=f'Pola Volume Kuartalan untuk SID yang Dipilih',
                              labels={'Kuartal': 'Kuartal', 'Volume': 'Total Volume Pesan'},
                              markers=True)
                fig.update_layout(xaxis={'categoryorder':'category ascending'})
                st.plotly_chart(fig, use_container_width=True)
                with st.expander("Lihat Data yang Diproses"):
                    st.dataframe(df_final)
        # --- AKHIR PERUBAHAN ---

else:
    st.info("Atur filter di samping dan klik **'Tampilkan Visualisasi'**.")
