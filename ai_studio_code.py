import streamlit as st
import pandas as pd
import sqlite3
import datetime
import plotly.express as px
import plotly.graph_objects as go

# --- AYARLAR VE STİL ---
st.set_page_config(page_title="Yönetim Paneli", layout="wide", page_icon="Analytics")

# Tailwind ve Fontları Yükle
st.markdown("""
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;700;800&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Manrope', sans-serif; background-color: #f6f7f8; }
        .stApp { background-color: #f6f7f8; }
        /* Streamlit'in varsayılan paddinglerini ayarla */
        .block-container { padding-top: 1rem; padding-bottom: 5rem; }
        [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
        
        /* Kart Stilleri */
        .kpi-card { background: white; border-radius: 0.75rem; padding: 1.25rem; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); border: 1px solid #f1f5f9; }
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
    
    # Demo kullanıcı
    c.execute("SELECT * FROM kullanicilar WHERE kullanici_adi='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO kullanicilar VALUES ('admin', '1234')")
    
    conn.commit()
    conn.close()

# --- YARDIMCI FONKSİYONLAR ---
def format_currency(value):
    return f"₺{value:,.0f}".replace(",", ".")

def login_page():
    st.markdown("<div style='text-align: center; margin-top: 100px;'><h1 style='color:#137fec;'>Yönetim Paneli Giriş</h1></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        username = st.text_input("Kullanıcı Adı")
        password = st.text_input("Şifre", type="password")
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

# --- SAYFA BİLEŞENLERİ ---

def kpi_card_html(title, value, icon, color_class, change, is_positive):
    trend_icon = "trending_up" if is_positive else "trending_down"
    trend_color = "#0bda5b" if is_positive else "#fa6238"
    
    html = f"""
    <div class="kpi-card">
        <div class="flex items-center justify-between mb-2">
            <p class="text-slate-500 text-sm font-medium">{title}</p>
            <span class="material-symbols-outlined {color_class} p-1.5 rounded-lg text-[20px]">{icon}</span>
        </div>
        <div>
            <p class="text-slate-900 text-2xl font-bold leading-tight">{value}</p>
            <div class="flex items-center gap-1 mt-1">
                <span class="material-symbols-outlined text-[{trend_color}] text-sm" style="color:{trend_color}">{trend_icon}</span>
                <p class="text-[{trend_color}] text-sm font-bold" style="color:{trend_color}">{change}</p>
                <span class="text-slate-400 text-xs ml-1">geçen aya göre</span>
            </div>
        </div>
    </div>
    """
    return html

def product_bar_html(name, count, max_count):
    percent = (count / max_count * 100) if max_count > 0 else 0
    # Renk döngüsü için basit mantık
    colors = ["bg-primary", "bg-slate-200", "bg-slate-200"] 
    bar_color = "bg-[#137fec]" if percent > 50 else "bg-slate-200"
    
    return f"""
    <div class="group relative flex flex-col items-center justify-end w-full h-full gap-2" style="height: 200px;">
        <div class="w-full {bar_color} rounded-t-sm transition-all relative" style="height: {percent}%;">
            <div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-slate-800 text-white text-xs py-1 px-2 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                {name}: {count}
            </div>
        </div>
        <span class="text-[10px] sm:text-xs text-slate-500 font-medium rotate-0 truncate w-full text-center">{name}</span>
    </div>
    """

# --- SAYFALAR ---

def dashboard_page():
    conn = get_db()
    
    # 1. Filtre Bölümü (HTML Tasarımına Uygun Header)
    col_h1, col_h2 = st.columns([2, 1])
    with col_h1:
        st.markdown("""
        <div class="flex flex-col gap-2">
            <h1 class="text-slate-900 text-3xl font-black tracking-[-0.033em]">Genel Bakış</h1>
            <p class="text-slate-500 text-base font-normal">İşletmenizin finansal genel bakışı ve performans metrikleri.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_h2:
        # Tarih Seçici
        col_d1, col_d2 = st.columns(2)
        start_date = col_d1.date_input("Başlangıç", datetime.date(2024, 1, 1), label_visibility="collapsed")
        end_date = col_d2.date_input("Bitiş", datetime.date.today(), label_visibility="collapsed")

    # Verileri Çek
    df_satis = pd.read_sql(f"SELECT * FROM satislar WHERE tarih BETWEEN '{start_date}' AND '{end_date}'", conn)
    df_gider = pd.read_sql(f"SELECT * FROM giderler WHERE tarih BETWEEN '{start_date}' AND '{end_date}'", conn)
    
    # KPI Hesaplamaları
    toplam_ciro = df_satis['tutar'].sum() if not df_satis.empty else 0
    satis_adedi = df_satis['adet'].sum() if not df_satis.empty else 0
    toplam_gider = df_gider['tutar'].sum() if not df_gider.empty else 0
    net_kar = toplam_ciro - toplam_gider
    
    st.markdown("<div class='h-6'></div>", unsafe_allow_html=True)

    # 2. KPI Kartları (Grid Yapısı)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(kpi_card_html("Toplam Satış Tutarı", format_currency(toplam_ciro), "payments", "text-[#137fec] bg-[#137fec]/10", "+12%", True), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card_html("Satış Adedi", str(satis_adedi), "shopping_bag", "text-purple-500 bg-purple-500/10", "+5%", True), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_card_html("Toplam Giderler", format_currency(toplam_gider), "receipt_long", "text-orange-500 bg-orange-500/10", "-2%", False), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_card_html("Net Kâr", format_currency(net_kar), "account_balance_wallet", "text-emerald-500 bg-emerald-500/10", "+15%", True), unsafe_allow_html=True)

    st.markdown("<div class='h-6'></div>", unsafe_allow_html=True)

    # 3. Grafik Bölümü 1: Trend Grafiği (Büyük)
    st.markdown("""
    <div class="kpi-card mb-6">
        <h3 class="text-slate-900 text-lg font-bold">Satış Trendleri</h3>
    </div>
    """, unsafe_allow_html=True)
    
    if not df_satis.empty:
        df_trend = df_satis.groupby('tarih')['tutar'].sum().reset_index()
        fig_trend = px.area(df_trend, x='tarih', y='tutar', height=300)
        fig_trend.update_layout(margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor='white', plot_bgcolor='white')
        fig_trend.update_traces(line_color='#137fec', fillcolor='rgba(19, 127, 236, 0.2)')
        st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("Trend grafiği için veri bulunamadı.")

    # 4. Alt Bölüm Grid (En Çok Satanlar & Gider Pasta Grafiği)
    col_g1, col_g2 = st.columns([2, 1])
    
    with col_g1:
        st.markdown('<div class="kpi-card h-full">', unsafe_allow_html=True)
        st.markdown('<h3 class="text-slate-900 text-lg font-bold mb-4">En Çok Satan Ürünler</h3>', unsafe_allow_html=True)
        
        if not df_satis.empty:
            # Ürün isimlerini birleştir
            df_urunler = pd.read_sql("SELECT * FROM urunler", conn)
            merged = df_satis.merge(df_urunler, left_on="urun_kodu", right_on="kod", how="left")
            top_products = merged.groupby("isim")['adet'].sum().sort_values(ascending=False).head(8)
            
            # Custom HTML Bar Chart Oluşturma
            cols = st.columns(len(top_products))
            max_val = top_products.max()
            
            for idx, (name, count) in enumerate(top_products.items()):
                with cols[idx]:
                    st.markdown(product_bar_html(name, count, max_val), unsafe_allow_html=True)
        else:
            st.write("Veri yok.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_g2:
        st.markdown('<div class="kpi-card h-full">', unsafe_allow_html=True)
        st.markdown('<h3 class="text-slate-900 text-lg font-bold mb-4">Gider Dağılımı</h3>', unsafe_allow_html=True)
        
        if not df_gider.empty:
            df_gider_tur = pd.read_sql("SELECT * FROM gider_turleri", conn)
            gider_merged = df_gider.merge(df_gider_tur, left_on="gider_kodu", right_on="kod", how="left")
            gider_dist = gider_merged.groupby("isim")['tutar'].sum().reset_index()
            
            fig_pie = px.donut(gider_dist, values='tutar', names='isim', hole=0.6, height=300)
            fig_pie.update_layout(showlegend=False, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.write("Gider verisi yok.")
        st.markdown('</div>', unsafe_allow_html=True)
        
    conn.close()
    
    st.markdown("<div class='h-6'></div>", unsafe_allow_html=True)
    
    # Detay Butonu
    if st.button("Ayrıntılı Listeyi Görüntüle ➔", type="primary"):
        st.session_state['page'] = 'Raporlar'
        st.rerun()

def upload_page():
    st.markdown("<h2 class='text-2xl font-bold mb-4'>Veri Yükleme Merkezi</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    def convert_df(df):
        return df.to_csv(index=False).encode('utf-8')
        
    with col1:
        st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
        st.subheader("1. Satış Verisi")
        s_template = pd.DataFrame(columns=["Tarih (YYYY-AA-GG)", "Urun_Kodu", "Adet", "Tutar"])
        st.download_button("Satış Şablonu İndir", convert_df(s_template), "satis_sablon.csv", "text/csv")
        
        up_s = st.file_uploader("Satış Dosyası Seç", type=["csv", "xlsx"], key="s")
        if up_s:
            try:
                df = pd.read_csv(up_s) if up_s.name.endswith('.csv') else pd.read_excel(up_s)
                df.columns = ["tarih", "urun_kodu", "adet", "tutar"]
                conn = get_db()
                df.to_sql('satislar', conn, if_exists='append', index=False)
                conn.close()
                st.success("Satışlar yüklendi!")
            except Exception as e:
                st.error(f"Hata: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
        st.subheader("2. Gider Verisi")
        g_template = pd.DataFrame(columns=["Tarih (YYYY-AA-GG)", "Gider_Kodu", "Tutar"])
        st.download_button("Gider Şablonu İndir", convert_df(g_template), "gider_sablon.csv", "text/csv")
        
        up_g = st.file_uploader("Gider Dosyası Seç", type=["csv", "xlsx"], key="g")
        if up_g:
            try:
                df = pd.read_csv(up_g) if up_g.name.endswith('.csv') else pd.read_excel(up_g)
                df.columns = ["tarih", "gider_kodu", "tutar"]
                conn = get_db()
                df.to_sql('giderler', conn, if_exists='append', index=False)
                conn.close()
                st.success("Giderler yüklendi!")
            except Exception as e:
                st.error(f"Hata: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

def definitions_page():
    st.markdown("<h2 class='text-2xl font-bold mb-4'>Tanımlamalar</h2>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Ürünler", "Gider Kodları"])
    conn = get_db()
    
    with tab1:
        c1, c2 = st.columns(2)
        kod = c1.text_input("Yeni Ürün Kodu")
        isim = c2.text_input("Yeni Ürün Adı")
        if st.button("Ürün Ekle"):
            try:
                c = conn.cursor()
                c.execute("INSERT INTO urunler VALUES (?,?)", (kod, isim))
                conn.commit()
                st.success("Eklendi")
            except: st.error("Kod zaten var")
        
        st.dataframe(pd.read_sql("SELECT * FROM urunler", conn), use_container_width=True)

    with tab2:
        c1, c2 = st.columns(2)
        kod = c1.text_input("Gider Kodu")
        isim = c2.text_input("Gider Adı")
        if st.button("Gider Kodu Ekle"):
            try:
                c = conn.cursor()
                c.execute("INSERT INTO gider_turleri VALUES (?,?)", (kod, isim))
                conn.commit()
                st.success("Eklendi")
            except: st.error("Kod zaten var")
            
        st.dataframe(pd.read_sql("SELECT * FROM gider_turleri", conn), use_container_width=True)
    conn.close()

def details_page():
    st.markdown("<h2 class='text-2xl font-bold mb-4'>Detaylı Raporlar</h2>", unsafe_allow_html=True)
    if st.button("🔙 Dashboard'a Dön"):
        st.session_state['page'] = 'Dashboard'
        st.rerun()
        
    conn = get_db()
    st.subheader("Satış Listesi")
    st.dataframe(pd.read_sql("SELECT s.*, u.isim FROM satislar s LEFT JOIN urunler u ON s.urun_kodu = u.kod", conn), use_container_width=True)
    st.divider()
    st.subheader("Gider Listesi")
    st.dataframe(pd.read_sql("SELECT g.*, gt.isim FROM giderler g LEFT JOIN gider_turleri gt ON g.gider_kodu = gt.kod", conn), use_container_width=True)
    conn.close()

# --- ANA AKIŞ ---
def main():
    init_db()
    
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    
    if 'page' not in st.session_state:
        st.session_state['page'] = 'Dashboard'

    if not st.session_state['logged_in']:
        login_page()
    else:
        # Sidebar Tasarımı
        with st.sidebar:
            st.markdown(f"""
            <div class="flex items-center gap-4 mb-6 px-2">
                <div class="size-8 flex items-center justify-center text-[#137fec]">
                    <span class="material-symbols-outlined text-3xl">analytics</span>
                </div>
                <div>
                    <h2 class="text-lg font-bold leading-tight">Yönetim</h2>
                    <p class="text-xs text-slate-500">{st.session_state['username']}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            menu = st.radio("Menü", ["Dashboard", "Veri Yükleme", "Tanımlamalar", "Raporlar"], label_visibility="collapsed")
            
            if menu != st.session_state['page']:
                st.session_state['page'] = menu
                st.rerun()
                
            st.markdown("---")
            if st.button("Çıkış Yap"):
                st.session_state['logged_in'] = False
                st.rerun()

        # Sayfa Yönlendirme
        if st.session_state['page'] == "Dashboard":
            dashboard_page()
        elif st.session_state['page'] == "Veri Yükleme":
            upload_page()
        elif st.session_state['page'] == "Tanımlamalar":
            definitions_page()
        elif st.session_state['page'] == "Raporlar":
            details_page()

if __name__ == "__main__":
    main()