import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_option_menu import option_menu

# --- 1. ตั้งค่าหน้า Page และ สีองค์กร ---
st.set_page_config(page_title="Executive Medical Workforce Dashboard", page_icon="🏥", layout="wide")

# Custom CSS เพื่อปรับโทนสีและสร้าง KPI Card
st.markdown("""
<style>
    h1, h2, h3, h4 {
        color: #046938 !important;
        font-family: 'Sarabun', sans-serif;
    }
    .kpi-container {
        display: flex;
        justify-content: space-between;
        gap: 15px;
        flex-wrap: wrap;
        margin-bottom: 25px;
        margin-top: 10px;
    }
    .kpi-card {
        flex: 1;
        min-width: 200px;
        background: linear-gradient(135deg, #ffffff 0%, #f0f7f3 100%);
        padding: 20px;
        border-radius: 12px;
        border-left: 8px solid #046938;
        box-shadow: 0 4px 12px rgba(4, 105, 56, 0.1);
        text-align: center;
        transition: transform 0.2s;
    }
    .kpi-card:hover {
        transform: translateY(-5px);
    }
    .kpi-title {
        margin: 0;
        font-size: 1.1rem;
        color: #555555;
        font-weight: 600;
    }
    .kpi-value {
        margin: 10px 0 0 0;
        font-size: 2.2rem;
        color: #046938;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# --- ฟังก์ชันคำนวณเกณฑ์ขั้นต่ำ ---
def get_required_doctors(specialty, sp, beds):
    reqs = {
        'สูติศาสตร์-นรีเวชวิทยา': {'M2': 1, 'M1': 2, 'S_<=300': 2, 'S_>300': 4, 'A_<=700': 4, 'A_>700': 6},
        'ศัลยกรรมทั่วไป': {'M2': 1, 'M1': 2, 'S_<=300': 2, 'S_>300': 4, 'A_<=700': 4, 'A_>700': 6},
        'อายุรศาสตร์': {'M2': 1, 'M1': 4, 'S_<=300': 4, 'S_>300': 6, 'A_<=700': 6, 'A_>700': 8},
        'กุมารเวชศาสตร์': {'M2': 1, 'M1': 2, 'S_<=300': 3, 'S_>300': 4, 'A_<=700': 5, 'A_>700': 6},
        'ออร์โธปิดิกส์': {'M2': 1, 'M1': 2, 'S_<=300': 2, 'S_>300': 4, 'A_<=700': 6, 'A_>700': 6},
        'เวชศาสตร์ฉุกเฉิน': {'M2': 1, 'M1': 2, 'S_<=300': 2, 'S_>300': 4, 'A_<=700': 4, 'A_>700': 6}
    }
    if specialty not in reqs: return None
    mapping = reqs[specialty]
    sp_upper = str(sp).upper().strip()
    if pd.isna(beds): beds = 0

    if sp_upper == 'M2': return mapping.get('M2')
    elif sp_upper == 'M1': return mapping.get('M1')
    elif sp_upper == 'S': return mapping.get('S_<=300') if float(beds) <= 300 else mapping.get('S_>300')
    elif sp_upper == 'A': return mapping.get('A_<=700') if float(beds) <= 700 else mapping.get('A_>700')
    return None

# --- โหลดข้อมูล ---
@st.cache_data
def load_and_prep_data():
    excel_file = 'เตรียมทำ dashboard.xlsx'
    sheets_mapping = {
        'อายุรแพทย์': 'อายุรศาสตร์',
        'ศัลยกรรมทั่วไป': 'ศัลยกรรมทั่วไป',
        'กุมารแพทย์': 'กุมารเวชศาสตร์',
        'ออโธฯ': 'ออร์โธปิดิกส์',
        'สูตินรี': 'สูติศาสตร์-นรีเวชวิทยา',
        'วิสัญญี': 'วิสัญญีวิทยา',
        'เวชฯฉุกเฉิน': 'เวชศาสตร์ฉุกเฉิน'
    }
    dfs = []
    for sheet, main_branch in sheets_mapping.items():
        try:
            df = pd.read_excel(excel_file, sheet_name=sheet, header=1)
            df['สาขาหลัก'] = main_branch
            dfs.append(df)
        except: pass

    df_all = pd.concat(dfs, ignore_index=True)

    # อัปเดต Map เปลี่ยนจาก "วุฒิที่ใช้ในตำแหน่ง" เป็น "วุฒิที่ใช้กับการเบิก พตส."
    rename_map = {
        'ตามจ.18 - \nactived_bed_name': 'จำนวนเตียง',
        'ตามจ.18 - เขต': 'เขตสุขภาพ',
        'ตามจ.18 - \nรหัสจังหวัด': 'รหัสจังหวัด',
        'ตามจ.18 - \nจังหวัด': 'จังหวัด',
        'ตามจ.18 - \nชื่อหน่วยงาน': 'โรงพยาบาล',
        'ตามจ.18 - \nประเภทหน่วยงาน': 'ประเภทหน่วยงาน',
        'ตามจ.18 - \nSAP': 'SAP_Level',
        'ตามจ.18 - \nservice_plan': 'Service_Plan',
        'วุฒิที่ใช้กับการเบิก พตส. (FTE) -\nสาขาวุฒิบัตรความเชี่ยวชาญ': 'อนุสาขาความเชี่ยวชาญ',
        'สถานะการปฏิบัติราชการปัจจุบัน': 'Status'
    }
    df_all = df_all.rename(columns=rename_map)
    df_all['เขตสุขภาพ'] = df_all['เขตสุขภาพ'].fillna(0).astype(int).astype(str)
    df_all['อนุสาขาความเชี่ยวชาญ'] = df_all['อนุสาขาความเชี่ยวชาญ'].fillna('ไม่ระบุ')
    df_all['Service_Plan'] = df_all['Service_Plan'].astype(str).str.upper().str.strip()
    df_all['SAP_Level'] = df_all['SAP_Level'].astype(str).str.upper().str.strip()
    df_all['Status'] = df_all['Status'].fillna('ไม่ระบุ')

    bins = [0, 99, 299, 499, 799, 9999]
    labels = ['< 100 เตียง', '100 - 299 เตียง', '300 - 499 เตียง', '500 - 799 เตียง', '>= 800 เตียง']
    df_all['ช่วงจำนวนเตียง'] = pd.cut(df_all['จำนวนเตียง'], bins=bins, labels=labels)

    return df_all

df = load_and_prep_data()

# --- 4. Sidebar: เมนูนำทางแบบมีไอคอน ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #046938; margin-bottom: 0;'>MOPH Workforce</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666; margin-top: 0;'>Executive Dashboard</p>", unsafe_allow_html=True)

    selected_nav = option_menu(
        menu_title=None,
        options=["ภาพรวม", "วิเคราะห์ส่วนขาด", "เจาะลึกระดับอนุสาขา"],
        icons=["house-door", "clipboard-data", "search"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent", "margin-bottom": "20px"},
            "icon": {"color": "#046938", "font-size": "18px"}, 
            "nav-link": {"font-size": "15px", "text-align": "left", "margin":"5px", "--hover-color": "#e6f0eb", "color": "#333"},
            "nav-link-selected": {"background-color": "#046938", "color": "white", "icon": {"color": "white"}},
        }
    )

    st.markdown("---")
    st.markdown("<h4 style='color: #046938;'>🎯 ตัวกรองข้อมูล (Filters)</h4>", unsafe_allow_html=True)

    status_list = df['Status'].unique()
    selected_status = st.multiselect("📌 สถานะการปฏิบัติราชการ", sorted(status_list), default=["ดำรงตำแหน่ง"])

    zone_list = sorted(df['เขตสุขภาพ'].unique(), key=float)
    selected_zone = st.multiselect("📍 เลือกเขตสุขภาพ", zone_list, default=zone_list)

    filtered_prov = df[df['เขตสุขภาพ'].isin(selected_zone)]['จังหวัด'].dropna().unique()
    selected_province = st.multiselect("🏢 เลือกจังหวัด", sorted(filtered_prov), default=filtered_prov)

    filtered_hosp = df[(df['เขตสุขภาพ'].isin(selected_zone)) & (df['จังหวัด'].isin(selected_province))]['โรงพยาบาล'].dropna().unique()
    selected_hospital = st.multiselect("🏥 เลือกโรงพยาบาล", sorted(filtered_hosp))

    st.markdown("<h4 style='color: #046938; margin-top: 15px;'>⚙️ โครงสร้างโรงพยาบาล</h4>", unsafe_allow_html=True)
    selected_bed = st.multiselect("🛏️ ช่วงจำนวนเตียง", df['ช่วงจำนวนเตียง'].dropna().unique())
    selected_type = st.multiselect("📊 ประเภทหน่วยงาน", df['ประเภทหน่วยงาน'].dropna().unique())
    selected_sap = st.multiselect("📑 SAP Level", df['SAP_Level'].dropna().unique())

# --- ประมวลผล Base Filter ---
mask = df['เขตสุขภาพ'].isin(selected_zone) & df['จังหวัด'].isin(selected_province)
if selected_status: mask &= df['Status'].isin(selected_status)
if selected_hospital: mask &= df['โรงพยาบาล'].isin(selected_hospital)
if selected_bed: mask &= df['ช่วงจำนวนเตียง'].isin(selected_bed)
if selected_type: mask &= df['ประเภทหน่วยงาน'].isin(selected_type)
if selected_sap: mask &= df['SAP_Level'].isin(selected_sap)
df_filtered = df[mask]

# --- 2. การสร้าง KPI Card ---
kpi_html = f"""
<div class="kpi-container">
    <div class="kpi-card"><p class="kpi-title">👨‍⚕️ จำนวนแพทย์</p><p class="kpi-value">{{len(df_filtered):,}} คน</p></div>
    <div class="kpi-card"><p class="kpi-title">📋 จำนวนสาขาหลัก</p><p class="kpi-value">{{df_filtered['สาขาหลัก'].nunique()}} สาขา</p></div>
    <div class="kpi-card"><p class="kpi-title">🔬 จำนวนอนุสาขาย่อย</p><p class="kpi-value">{{df_filtered['อนุสาขาความเชี่ยวชาญ'].nunique()}} อนุสาขา</p></div>
    <div class="kpi-card"><p class="kpi-title">🏥 จำนวนโรงพยาบาล</p><p class="kpi-value">{{df_filtered['โรงพยาบาล'].nunique()}} แห่ง</p></div>
</div>
"""

moph_colors = ['#046938', '#1A8B55', '#3BB578', '#63D698', '#90E8BA', '#C2F2D7', '#E6FAF0']

st.title("🏥 Dashboard วิเคราะห์กำลังคนและประเมินความขาดแคลน")
st.markdown(kpi_html, unsafe_allow_html=True)
st.markdown("---")

# --- 3. การแสดงผลตาม Tab ที่เลือก ---

if selected_nav == "ภาพรวม":
    st.subheader("📊 ภาพรวมกำลังคนผู้เชี่ยวชาญ")

    spec_summary = df_filtered.groupby('สาขาหลัก').size().reset_index(name='จำนวน (คน)')
    spec_summary = spec_summary.sort_values('จำนวน (คน)', ascending=False)

    if not spec_summary.empty:
        cols = st.columns(min(len(spec_summary), 4))
        for i, row in spec_summary.iterrows():
            col_idx = i % 4
            cols[col_idx].metric(label=row['สาขาหลัก'], value=f"{{row['จำนวน (คน)']}} คน")
    else:
        st.info("ไม่พบข้อมูลแพทย์ในเงื่อนไขที่เลือก")

    st.markdown("<br>", unsafe_allow_html=True)

    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.markdown("**จำนวนผู้เชี่ยวชาญจำแนกตาม 7 สาขาหลัก**")
        fig1 = px.bar(spec_summary, x='จำนวน (คน)', y='สาขาหลัก', orientation='h', text='จำนวน (คน)', 
                      color='สาขาหลัก', color_discrete_sequence=moph_colors, template='plotly_white')
        fig1.update_traces(textposition='outside')
        fig1.update_layout(showlegend=False, yaxis={{'categoryorder':'total ascending'}})
        st.plotly_chart(fig1, use_container_width=True)

    with col_chart2:
        st.markdown("**สัดส่วนผู้เชี่ยวชาญตามสถานะการปฏิบัติราชการ**")
        status_count = df_filtered['Status'].value_counts().reset_index()
        status_count.columns = ['สถานะ', 'จำนวน (คน)']
        fig2 = px.pie(status_count, values='จำนวน (คน)', names='สถานะ', hole=0.4, 
                      color_discrete_sequence=['#046938', '#F5B041', '#E74C3C'], template='plotly_white')
        st.plotly_chart(fig2, use_container_width=True)


elif selected_nav == "วิเคราะห์ส่วนขาด":
    st.subheader("📉 วิเคราะห์ระดับความขาดแคลนแพทย์เฉพาะทาง (Gap Analysis)")
    st.caption("อ้างอิงเกณฑ์: จำนวนแพทย์เฉพาะทางขั้นต่ำ ที่ควรมีตามขนาดโรงพยาบาล (แสดงเฉพาะรพ.ระดับ M2, M1, S, A)")

    col_gap1, col_gap2 = st.columns([1, 2])
    with col_gap1:
        show_shortage_only = st.checkbox("🔴 แสดงเฉพาะรายการที่ 'ขาดแคลน' (Gap < 0)", value=True)
    with col_gap2:
        req_specs_list = ['อายุรศาสตร์', 'ศัลยกรรมทั่วไป', 'กุมารเวชศาสตร์', 'สูติศาสตร์-นรีเวชวิทยา', 'ออร์โธปิดิกส์', 'เวชศาสตร์ฉุกเฉิน']
        selected_req_specs = st.multiselect("💉 เลือกสาขาเฉพาะทางที่ต้องการวิเคราะห์:", req_specs_list, default=req_specs_list)

    gap_mask = df['เขตสุขภาพ'].isin(selected_zone) & df['จังหวัด'].isin(selected_province)
    if selected_hospital: gap_mask &= df['โรงพยาบาล'].isin(selected_hospital)
    if selected_bed: gap_mask &= df['ช่วงจำนวนเตียง'].isin(selected_bed)
    if selected_type: gap_mask &= df['ประเภทหน่วยงาน'].isin(selected_type)
    if selected_sap: gap_mask &= df['SAP_Level'].isin(selected_sap)

    df_gap_base = df[gap_mask]
    hosp_info = df_gap_base[['เขตสุขภาพ', 'จังหวัด', 'โรงพยาบาล', 'Service_Plan', 'จำนวนเตียง']].drop_duplicates()
    active_counts = df_gap_base[df_gap_base['Status'] == 'ดำรงตำแหน่ง'].groupby(['โรงพยาบาล', 'สาขาหลัก']).size().to_dict()

    gap_records = []
    for _, row in hosp_info.iterrows():
        h_sp = row['Service_Plan']
        if h_sp not in ['M2', 'M1', 'S', 'A']: continue
        h_zone = row['เขตสุขภาพ']
        h_prov = row['จังหวัด']
        h_name = row['โรงพยาบาล']
        h_beds = row['จำนวนเตียง']

        for spec in selected_req_specs:
            req_val = get_required_doctors(spec, h_sp, h_beds)
            if req_val is not None:
                active_cnt = active_counts.get((h_name, spec), 0)
                gap = active_cnt - req_val
                if show_shortage_only and gap >= 0: continue
                status_text = "🟢 เพียงพอ" if gap >= 0 else "🔴 ขาดแคลน"
                gap_records.append({
                    'เขต': h_zone, 'จังหวัด': h_prov, 'โรงพยาบาล': h_name, 'Service Plan': h_sp, 'สาขา': spec,
                    'ควรมี (คน)': int(req_val), 'มีจริง (คน)': int(active_cnt), 'ผลต่าง (Gap)': int(gap), 'สถานะ': status_text
                })

    if gap_records:
        df_gap_table = pd.DataFrame(gap_records)
        df_gap_table = df_gap_table.sort_values(by=['ผลต่าง (Gap)', 'เขต', 'จังหวัด'], ascending=[True, True, True])
        def highlight_gap(val):
            color = '#ffe6e6' if val < 0 else '#e6ffe6'
            return f'background-color: {{color}}; color: #000;'
        st.dataframe(df_gap_table.style.map(highlight_gap, subset=['ผลต่าง (Gap)']), use_container_width=True, hide_index=True)
    else:
        st.info("✅ ไม่พบรายการขาดแคลนตามเงื่อนไขที่ท่านเลือก")


elif selected_nav == "เจาะลึกระดับอนุสาขา":
    st.subheader("🔬 เจาะลึกระดับอนุสาขาความเชี่ยวชาญ (Drill-down)")

    selected_branch = st.selectbox("เลือกสาขาหลักที่ต้องการดูอนุสาขา:", df_filtered['สาขาหลัก'].unique())
    df_sub = df_filtered[df_filtered['สาขาหลัก'] == selected_branch]
    sub_count = df_sub['อนุสาขาความเชี่ยวชาญ'].value_counts().reset_index().head(15)
    sub_count.columns = ['อนุสาขา', 'จำนวน (คน)']

    fig3 = px.bar(sub_count, x='อนุสาขา', y='จำนวน (คน)', text='จำนวน (คน)', 
                  color='อนุสาขา', color_discrete_sequence=moph_colors, template='plotly_white', 
                  title=f"Top 15 อนุสาขาในสาย {{selected_branch}}")
    fig3.update_traces(textposition='outside')
    fig3.update_layout(showlegend=False, xaxis={{'categoryorder':'total descending'}})
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")

    # --- 3.3 การแจกแจง รพ. P+ ---
    st.subheader("🏥 ตรวจสอบความครบถ้วนของอนุสาขา (เฉพาะ รพ. ระดับ P+)")
    st.caption("อ้างอิงจากคอลัมน์ วุฒิที่ใช้กับการเบิก พตส. (FTE) เพื่อความแม่นยำในการปฏิบัติงานจริง")

    df_p_plus = df[df['SAP_Level'] == 'P+']

    if not df_p_plus.empty:
        master_subs = df_p_plus[(df_p_plus['อนุสาขาความเชี่ยวชาญ'] != 'ไม่ระบุ') & 
                                (~df_p_plus['อนุสาขาความเชี่ยวชาญ'].str.startswith('สาขา', na=False))][['สาขาหลัก', 'อนุสาขาความเชี่ยวชาญ']].drop_duplicates()

        filtered_p_hosp_list = sorted(df_filtered[df_filtered['SAP_Level'] == 'P+']['โรงพยาบาล'].dropna().unique())

        if len(filtered_p_hosp_list) == 0:
            st.info("ไม่มีโรงพยาบาลระดับ P+ ในพื้นที่ที่คุณกำลังกรองข้อมูลอยู่")
        else:
            target_p_hosp = st.selectbox("เลือกโรงพยาบาลระดับ P+ เพื่อตรวจสอบส่วนขาด:", ["-- กรุณาเลือก --"] + filtered_p_hosp_list)

            if target_p_hosp != "-- กรุณาเลือก --":
                hosp_subs = df_p_plus[(df_p_plus['โรงพยาบาล'] == target_p_hosp) & 
                                      (df_p_plus['อนุสาขาความเชี่ยวชาญ'] != 'ไม่ระบุ')]['อนุสาขาความเชี่ยวชาญ'].unique()

                missing_mask = ~master_subs['อนุสาขาความเชี่ยวชาญ'].isin(hosp_subs)
                missing_subs = master_subs[missing_mask].sort_values(['สาขาหลัก', 'อนุสาขาความเชี่ยวชาญ'])

                if missing_subs.empty:
                    st.success(f"🎉 **{{target_p_hosp}}** มีอนุสาขาครบถ้วนสมบูรณ์ เทียบเท่ากับมาตรฐาน รพ. P+ ทั่วประเทศ")
                else:
                    st.warning(f"⚠️ **{{target_p_hosp}}** ขาดอนุสาขาจำนวน {{len(missing_subs)}} สาขา (เมื่อเทียบกับ รพ. P+ ทั้งประเทศ)")

                    col_p1, col_p2 = st.columns([2, 1])
                    with col_p1:
                        st.dataframe(
                            missing_subs.rename(columns={{'สาขาหลัก': 'อยู่ในสายงาน (สาขาหลัก)', 'อนุสาขาความเชี่ยวชาญ': 'อนุสาขาที่ขาดหายไป'}}),
                            hide_index=True, use_container_width=True
                        )
    else:
        st.info("ไม่พบข้อมูลโรงพยาบาลระดับ P+ ในฐานข้อมูล")
