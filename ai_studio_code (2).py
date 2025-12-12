import streamlit as st
import pandas as pd
import sqlite3
import datetime
import plotly.express as px
import plotly.graph_objects as go

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Yönetim Paneli", layout="wide", page_icon="📊")

# --- CSS VE STİL (GÖRSEL TASARIM) ---
# Bu kısım Streamlit'i görseldeki Dark Mode temasına zorlar
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;700;800&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet">
    
    <style>
        /* GENEL SAYFA YAPISI */
        body { font-family: 'Manrope', sans-serif; background-color: #101922; color: #ffffff; }
        .stApp { background-color: #101922; }
        
        /* HEADER GİZLEME (Streamlit'in kendi header'ını gizle) */
        header[data-testid="stHeader"] { visibility: hidden; }
        .block-container { padding-top: 1rem; padding-bottom: 5rem; }

        /* KART TASARIMLARI */
        .card-container {
            background-color: #1C252E;
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #283039;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        
        /* METİN STİLLERİ */
        .text-gray { color: #94a3b8; }
        .text-white { color: #ffffff; }
        .text-blue { color: #3b82f6; }
        .text-green { color: #10b981; }
        .text-red { color: #ef4444; }
        
        /* SIDEBAR TASARIMI */
        section[data-testid="stSidebar"] {
            background-color: #1C252E;
            border-right: 1px solid #283039;
        }
        
        /* BUTTON STİLLERİ */
        .stButton button {
            background-color: #137fec;
            color: white;
            border-radius: 8px;
            border: none;
            font-weight: 600;
        }
        .stButton button:hover {
            background-color: #2563eb;
        }
        
        /* INPUT ALANLARI */
        div[data-baseweb="input"] {
            background-color: #1C252E !important;
            border: 1px solid #283039 !important;
            color: white !important;
        }
        input { color: white !important; }
    </style>
""", unsafe_allow_html=True)

# --- VERİTABANI İŞLEMLERİ ---
def get_db():
    conn = sqlite3.connect('isletme_db.db')
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS urunler (kod TEXT PRIMARY KEY, isim TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS gider_turleri (kod TEXT PRIMARY KEY, isim TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS satislar (tarih DATE, urun_kodu TEXT, adet INTEGER, tutar REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS giderler (tarih DATE, gider_kodu TEXT, tutar REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS kullanicilar (kullanici_adi TEXT, sifre TEXT)')
    
    # Admin kullanıcı kontrolü
    c.execute("SELECT * FROM kullanicilar WHERE kullanici_adi='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO kullanicilar VALUES ('admin', '1234')")
    
    conn.commit()
    conn.close()

# --- GİRİŞ SAYFASI ---
def login_page():
    st.markdown("""
        <div style='display: flex; justify-content: center; align-items: center; height: 80vh;'>
            <div class='card-container' style='width: 400px; text-align: center;'>
                <h1 style='color: white; margin-bottom: 20px;'>Yönetim Paneli</h1>
                <p class='text-gray'>Devam etmek için giriş yapın</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        username = st.text_input("Kullanıcı Adı", placeholder="admin")
        password = st.text_input("Şifre", type="password", placeholder="1234")
        
        if st.button("Giriş Yap", use_container_width=True):
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT * FROM kullanicilar WHERE kullanici_adi=? AND sifre=?", (username, password))
            if c.fetchone():
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.rerun()
            else:
                st.error("Hatalı giriş!")
            conn.close()

# --- DASHBOARD BİLEŞENLERİ (HTML) ---
def render_header():
    # Görseldeki üst menüyü simüle eder
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 20px; border-bottom: 1px solid #283039; margin-bottom: 20px;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="background-color: #137fec; width: 32px; height: 32px; border-radius: 6px; display: flex; align-items: center; justify-content: center;">
                <span class="material-symbols-outlined" style="color: white; font-size: 20px;">analytics</span>
            </div>
            <h2 style="margin: 0; font-size: 20px; font-weight: 700;">Yönetim Paneli</h2>
        </div>
        <div style="display: flex; align-items: center; gap: 20px;">
            <span class="text-gray" style="font-size: 14px;">Dashboard</span>
            <span class="text-gray" style="font-size: 14px;">Veri Tabanı</span>
            <span class="text-gray" style="font-size: 14px;">Raporlar</span>
            <span class="material-symbols-outlined text-white">notifications</span>
            <div style="width: 32px; height: 32px; background-color: #ffccbc; border-radius: 50%;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def kpi_card(title, value, change, icon, icon_bg, is_positive):
    trend_color = "#10b981" if is_positive else "#ef4444" # Yeşil veya Kırmızı
    trend_icon = "trending_up" if is_positive else "trending_down"
    
    html = f"""
    <div class="card-container">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
            <span class="text-gray" style="font-size: 14px;">{title}</span>
            <div style="background-color: {icon_bg}; padding: 6px; border-radius: 8px; display: flex;">
                <span class="material-symbols-outlined" style="font-size: 20px; color: {icon};">{icon}</span>
            </div>
        </div>
        <div style="font-size: 28px; font-weight: 800; color: white; margin-bottom: 5px;">{value}</div>
        <div style="display: flex; align-items: center; gap: 5px;">
            <span class="material-symbols-outlined" style="font-size: 16px; color: {trend_color};">{trend_icon}</span>
            <span style="color: {trend_color}; font-weight: 700; font-size: 14px;">{change}</span>
            <span class="text-gray" style="font-size: 12px;">geçen aya göre</span>
        </div>
    </div>
    """
    return html

# --- SAYFALAR ---
def dashboard_page():
    render_header()
    
    # Başlık ve Filtre Bölümü
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("""
            <h1 style="font-size: 32px; font-weight: 800; margin-bottom: 5px;">Genel Bakış</h1>
            <p class="text-gray">İşletmenizin finansal genel bakışı ve performans metrikleri.</p>
        """, unsafe_allow_html=True)
    
    with col2:
        # Tarih filtresini sağa yaslı bir şekilde koyalım
        end_date = st.date_input("Bitiş Tarihi", datetime.date.today(), label_visibility="collapsed")
        start_date = end_date - datetime.timedelta(days=30)
    
    # Verileri Çek
    conn = get_db()
    df_satis = pd.read_sql(f"SELECT * FROM satislar WHERE tarih BETWEEN '{start_date}' AND '{end_date}'", conn)
    df_gider = pd.read_sql(f"SELECT * FROM giderler WHERE tarih BETWEEN '{start_date}' AND '{end_date}'", conn)
    
    # KPI Hesap
    ciro = df_satis['tutar'].sum() if not df_satis.empty else 0
    adet = df_satis['adet'].sum() if not df_satis.empty else 0
    gider = df_gider['tutar'].sum() if not df_gider.empty else 0
    kar = ciro - gider
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # KPI Grid (4 Kart)
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(kpi_card("Toplam Satış Tutarı", f"₺{ciro:,.0f}", "%12", "#3b82f6", "rgba(59, 130, 246, 0.2)", True), unsafe_allow_html=True)
    with k2:
        st.markdown(kpi_card("Satış Adedi", f"{adet}", "%5", "#a855f7", "rgba(168, 85, 247, 0.2)", True), unsafe_allow_html=True)
    with k3:
        st.markdown(kpi_card("Toplam Giderler", f"₺{gider:,.0f}", "%2", "#f97316", "rgba(249, 115, 22, 0.2)", False), unsafe_allow_html=True)
    with k4:
        st.markdown(kpi_card("Net Kâr", f"₺{kar:,.0f}", "%15", "#10b981", "rgba(16, 185, 129, 0.2)", True), unsafe_allow_html=True)

    # BÜYÜK GRAFİK (TREND)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
        <div class="card-container">
            <h3 style="margin-bottom: 5px; font-weight: 700;">Aylık Satış Trendleri</h3>
            <p class="text-gray" style="font-size: 14px; margin-bottom: 20px;">Yıllık karşılaştırmalı satış grafiği</p>
    """, unsafe_allow_html=True)
    
    if not df_satis.empty:
        df_trend = df_satis.sort_values('tarih')
        fig = px.area(df_trend, x='tarih', y='tutar', color_discrete_sequence=['#137fec'])
        
        # Plotly Dark Theme Ayarları (Görseldeki gibi)
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#94a3b8'),
            margin=dict(l=0, r=0, t=0, b=0),
            height=300,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='#283039')
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Trend grafiği için veri bulunamadı.")
    
    st.markdown("</div>", unsafe_allow_html=True) # Kart kapama

    # ALT GRAFİKLER (BAR ve DONUT)
    st.markdown("<br>", unsafe_allow_html=True)
    row2_col1, row2_col2 = st.columns([2, 1])
    
    with row2_col1:
        st.markdown('<div class="card-container" style="height: 100%;">', unsafe_allow_html=True)
        st.markdown('<h3 style="font-weight: 700; margin-bottom: 15px;">En Çok Satan Ürünler</h3>', unsafe_allow_html=True)
        if not df_satis.empty:
            df_urunler = pd.read_sql("SELECT * FROM urunler", conn)
            merged = df_satis.merge(df_urunler, left_on="urun_kodu", right_on="kod", how="left")
            top_products = merged.groupby("isim")['adet'].sum().sort_values(ascending=False).head(5).reset_index()
            
            fig_bar = px.bar(top_products, x='isim', y='adet', color_discrete_sequence=['#137fec'])
            fig_bar.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#94a3b8'),
                margin=dict(l=0, r=0, t=0, b=0),
                height=250,
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=False)
            )
            fig_bar.update_traces(marker_color='#137fec')
            st.plotly_chart(fig_bar, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with row2_col2:
        st.markdown('<div class="card-container" style="height: 100%;">', unsafe_allow_html=True)
        st.markdown('<h3 style="font-weight: 700; margin-bottom: 15px;">Gider Dağılımı</h3>', unsafe_allow_html=True)
        if not df_gider.empty:
            df_gider_tur = pd.read_sql("SELECT * FROM gider_turleri", conn)
            gider_merged = df_gider.merge(df_gider_tur, left_on="gider_kodu", right_on="kod", how="left")
            df_pie = gider_merged.groupby("isim")["tutar"].sum().reset_index()
            
            fig_pie = px.pie(df_pie, values='tutar', names='isim', hole=0.7, 
                             color_discrete_sequence=['#3b82f6', '#f97316', '#10b981', '#a855f7'])
            fig_pie.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#94a3b8'),
                margin=dict(l=0, r=0, t=0, b=0),
                height=250,
                showlegend=False
            )
            # Ortadaki Yazı
            fig_pie.add_annotation(text=f"Toplam<br>₺{gider/1000:.0f}K", x=0.5, y=0.5, font_size=16, showarrow=False, font_color="white")
            st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    conn.close()

def upload_page():
    st.markdown("<h1 style='font-size: 28px; font-weight: 800;'>Veri Yükleme</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    def convert_df(df):
        return df.to_csv(index=False).encode('utf-8')
        
    with col1:
        st.markdown('<div class="card-container">', unsafe_allow_html=True)
        st.markdown("<h3>Satış Verisi Yükle</h3>", unsafe_allow_html=True)
        s_template = pd.DataFrame(columns=["Tarih (YYYY-AA-GG)", "Urun_Kodu", "Adet", "Tutar"])
        st.download_button("📥 Şablon İndir", convert_df(s_template), "satis.csv", "text/csv")
        
        up_s = st.file_uploader("Dosya Seç", type=["csv", "xlsx"], key="s")
        if up_s:
            try:
                df = pd.read_csv(up_s) if up_s.name.endswith('.csv') else pd.read_excel(up_s)
                df.columns = ["tarih", "urun_kodu", "adet", "tutar"]
                conn = get_db()
                df.to_sql('satislar', conn, if_exists='append', index=False)
                conn.close()
                st.success("Yüklendi!")
            except Exception as e:
                st.error(f"Hata: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card-container">', unsafe_allow_html=True)
        st.markdown("<h3>Gider Verisi Yükle</h3>", unsafe_allow_html=True)
        g_template = pd.DataFrame(columns=["Tarih (YYYY-AA-GG)", "Gider_Kodu", "Tutar"])
        st.download_button("📥 Şablon İndir", convert_df(g_template), "gider.csv", "text/csv")
        
        up_g = st.file_uploader("Dosya Seç", type=["csv", "xlsx"], key="g")
        if up_g:
            try:
                df = pd.read_csv(up_g) if up_g.name.endswith('.csv') else pd.read_excel(up_g)
                df.columns = ["tarih", "gider_kodu", "tutar"]
                conn = get_db()
                df.to_sql('giderler', conn, if_exists='append', index=False)
                conn.close()
                st.success("Yüklendi!")
            except Exception as e:
                st.error(f"Hata: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

def tanimlar_page():
    st.markdown("<h1 style='font-size: 28px; font-weight: 800;'>Tanımlamalar</h1>", unsafe_allow_html=True)
    
    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Ürün Tanımları", "Gider Kodları"])
    conn = get_db()
    
    with tab1:
        c1, c2 = st.columns(2)
        kod = c1.text_input("Kod Girin", key="u_k")
        isim = c2.text_input("İsim Girin", key="u_i")
        if st.button("Ürün Ekle", key="btn_u"):
            try:
                c = conn.cursor()
                c.execute("INSERT INTO urunler VALUES (?,?)", (kod, isim))
                conn.commit()
                st.success("Eklendi")
            except: st.error("Hata")
        st.dataframe(pd.read_sql("SELECT * FROM urunler", conn), use_container_width=True)
        
    with tab2:
        c1, c2 = st.columns(2)
        kod = c1.text_input("Kod Girin", key="g_k")
        isim = c2.text_input("İsim Girin", key="g_i")
        if st.button("Gider Ekle", key="btn_g"):
            try:
                c = conn.cursor()
                c.execute("INSERT INTO gider_turleri VALUES (?,?)", (kod, isim))
                conn.commit()
                st.success("Eklendi")
            except: st.error("Hata")
        st.dataframe(pd.read_sql("SELECT * FROM gider_turleri", conn), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    conn.close()

# --- ANA UYGULAMA AKIŞI ---
def main():
    init_db()
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        
    if not st.session_state['logged_in']:
        login_page()
    else:
        with st.sidebar:
            st.title("Menü")
            page = st.radio("Git", ["Dashboard", "Veri Yükleme", "Tanımlamalar", "Çıkış"], label_visibility="collapsed")
            if page == "Çıkış":
                st.session_state['logged_in'] = False
                st.rerun()

        if page == "Dashboard":
            dashboard_page()
        elif page == "Veri Yükleme":
            upload_page()
        elif page == "Tanımlamalar":
            tanimlar_page()

if __name__ == "__main__":
    main()