import streamlit as st
import pandas as pd
import plotly.express as px

# --- ตั้งค่าหน้า Page ---
st.set_page_config(page_title="Executive Medical Workforce Dashboard", page_icon="🏥", layout="wide")
st.title("🏥 Dashboard วิเคราะห์กำลังคนและประเมินความขาดแคลนแพทย์ผู้เชี่ยวชาญ")
st.markdown("---")

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
    rename_map = {
        'ตามจ.18 - \nactived_bed_name': 'จำนวนเตียง',
        'ตามจ.18 - เขต': 'เขตสุขภาพ',
        'ตามจ.18 - \nรหัสจังหวัด': 'รหัสจังหวัด',
        'ตามจ.18 - \nจังหวัด': 'จังหวัด',
        'ตามจ.18 - \nชื่อหน่วยงาน': 'โรงพยาบาล',
        'ตามจ.18 - \nประเภทหน่วยงาน': 'ประเภทหน่วยงาน',
        'ตามจ.18 - \nSAP': 'SAP_Level',
        'ตามจ.18 - \nservice_plan': 'Service_Plan',
        'วุฒิที่ใช้ในตำแหน่ง -\nสาขาวุฒิบัตรความเชี่ยวชาญ': 'อนุสาขาความเชี่ยวชาญ',
        'สถานะการปฏิบัติราชการปัจจุบัน': 'Status'
    }
    df_all = df_all.rename(columns=rename_map)
    df_all['เขตสุขภาพ'] = df_all['เขตสุขภาพ'].fillna(0).astype(int).astype(str)
    df_all['อนุสาขาความเชี่ยวชาญ'] = df_all['อนุสาขาความเชี่ยวชาญ'].fillna('ไม่ระบุ')
    df_all['Service_Plan'] = df_all['Service_Plan'].astype(str).str.upper().str.strip()
    df_all['Status'] = df_all['Status'].fillna('ไม่ระบุ')
    
    bins = [0, 99, 299, 499, 799, 9999]
    labels = ['< 100 เตียง', '100 - 299 เตียง', '300 - 499 เตียง', '500 - 799 เตียง', '>= 800 เตียง']
    df_all['ช่วงจำนวนเตียง'] = pd.cut(df_all['จำนวนเตียง'], bins=bins, labels=labels)
    
    return df_all

df = load_and_prep_data()

# --- Sidebar ---
st.sidebar.header("🎯 ตัวกรองข้อมูล (Filters)")
status_list = df['Status'].unique()
selected_status = st.sidebar.multiselect("📌 สถานะการปฏิบัติราชการ", sorted(status_list), default=["ดำรงตำแหน่ง"])
st.sidebar.markdown("---")

zone_list = sorted(df['เขตสุขภาพ'].unique(), key=float)
selected_zone = st.sidebar.multiselect("📍 เลือกเขตสุขภาพ", zone_list, default=zone_list)
filtered_prov = df[df['เขตสุขภาพ'].isin(selected_zone)]['จังหวัด'].dropna().unique()
selected_province = st.sidebar.multiselect("🏢 เลือกจังหวัด", sorted(filtered_prov), default=filtered_prov)
filtered_hosp = df[(df['เขตสุขภาพ'].isin(selected_zone)) & (df['จังหวัด'].isin(selected_province))]['โรงพยาบาล'].dropna().unique()
selected_hospital = st.sidebar.multiselect("🏥 เลือกโรงพยาบาล", sorted(filtered_hosp))
st.sidebar.markdown("---")

st.sidebar.subheader("⚙️ โครงสร้างระดับโรงพยาบาล")
selected_bed = st.sidebar.multiselect("🛏️ ช่วงจำนวนเตียง", df['ช่วงจำนวนเตียง'].dropna().unique())
selected_type = st.sidebar.multiselect("📊 ประเภทหน่วยงาน", df['ประเภทหน่วยงาน'].dropna().unique())
selected_sap = st.sidebar.multiselect("📑 SAP Level", df['SAP_Level'].dropna().unique())

# --- Base Filter ---
mask = df['เขตสุขภาพ'].isin(selected_zone) & df['จังหวัด'].isin(selected_province)
if selected_status: mask &= df['Status'].isin(selected_status)
if selected_hospital: mask &= df['โรงพยาบาล'].isin(selected_hospital)
if selected_bed: mask &= df['ช่วงจำนวนเตียง'].isin(selected_bed)
if selected_type: mask &= df['ประเภทหน่วยงาน'].isin(selected_type)
if selected_sap: mask &= df['SAP_Level'].isin(selected_sap)
df_filtered = df[mask]

# --- Section 1: KPI ---
st.subheader("📈 ภาพรวมกำลังคนผู้เชี่ยวชาญ (ตามเงื่อนไขที่กรอง)")
col1, col2, col3, col4 = st.columns(4)
col1.metric("จำนวนแพทย์", f"{len(df_filtered):,} คน")
col2.metric("จำนวนสาขาหลัก", f"{df_filtered['สาขาหลัก'].nunique()} สาขา")
col3.metric("จำนวนอนุสาขาย่อย", f"{df_filtered['อนุสาขาความเชี่ยวชาญ'].nunique()} อนุสาขา")
col4.metric("จำนวนโรงพยาบาล", f"{df_filtered['โรงพยาบาล'].nunique()} แห่ง")
st.markdown("---")


# --- Section 1.5: สรุปจำนวนแพทย์เฉพาะทางตามตัวกรอง ---
st.subheader("👨‍⚕️ จำนวนแพทย์เฉพาะทาง (ตามเงื่อนไขพื้นที่และโครงสร้างที่เลือก)")
st.caption("แสดงจำนวนแพทย์แยกตามสาขา จากพื้นที่และเงื่อนไขทั้งหมดที่คุณได้ตั้งค่าไว้ในแถบด้านซ้าย")

# Group by Specialty
spec_summary = df_filtered.groupby('สาขาหลัก').size().reset_index(name='จำนวน (คน)')
spec_summary = spec_summary.sort_values('จำนวน (คน)', ascending=False)

# Display as stylized metrics or a clean table
if not spec_summary.empty:
    # Use columns to display the counts beautifully
    cols = st.columns(min(len(spec_summary), 4))
    for i, row in spec_summary.iterrows():
        col_idx = i % 4
        cols[col_idx].metric(label=row['สาขาหลัก'], value=f"{row['จำนวน (คน)']} คน")
else:
    st.info("ไม่พบข้อมูลแพทย์ในเงื่อนไขที่เลือก")

st.markdown("<br>", unsafe_allow_html=True)


# --- Section 2: Gap Analysis (Comprehensive Table) ---
st.subheader("📊 วิเคราะห์ระดับความขาดแคลนแพทย์เฉพาะทาง (Gap Analysis)")
st.caption("อ้างอิงเกณฑ์: จำนวนแพทย์เฉพาะทางขั้นต่ำ ที่ควรมีตามขนาดโรงพยาบาล (แสดงเฉพาะรพ.ระดับ M2, M1, S, A)")

# Filters specifically for Gap Table
col_gap1, col_gap2 = st.columns([1, 2])
with col_gap1:
    show_shortage_only = st.checkbox("🔴 แสดงเฉพาะรายการที่ 'ขาดแคลน' (Gap < 0)", value=True)
with col_gap2:
    req_specs_list = ['อายุรศาสตร์', 'ศัลยกรรมทั่วไป', 'กุมารเวชศาสตร์', 'สูติศาสตร์-นรีเวชวิทยา', 'ออร์โธปิดิกส์', 'เวชศาสตร์ฉุกเฉิน']
    selected_req_specs = st.multiselect("💉 เลือกสาขาเฉพาะทางที่ต้องการวิเคราะห์:", req_specs_list, default=req_specs_list)

# Data prep for Gap Table
# Use df based on sidebar filters (ignore 'Status' filter here because gap is standard vs Active)
gap_mask = df['เขตสุขภาพ'].isin(selected_zone) & df['จังหวัด'].isin(selected_province)
if selected_hospital: gap_mask &= df['โรงพยาบาล'].isin(selected_hospital)
if selected_bed: gap_mask &= df['ช่วงจำนวนเตียง'].isin(selected_bed)
if selected_type: gap_mask &= df['ประเภทหน่วยงาน'].isin(selected_type)
if selected_sap: gap_mask &= df['SAP_Level'].isin(selected_sap)

df_gap_base = df[gap_mask]

# Unique hospitals info
hosp_info = df_gap_base[['เขตสุขภาพ', 'จังหวัด', 'โรงพยาบาล', 'Service_Plan', 'จำนวนเตียง']].drop_duplicates()

# Pre-calculate active counts for speed
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
            
            # Apply Shortage Filter
            if show_shortage_only and gap >= 0:
                continue
                
            status_text = "🟢 เพียงพอ" if gap >= 0 else "🔴 ขาดแคลน"
            gap_records.append({
                'เขต': h_zone,
                'จังหวัด': h_prov,
                'โรงพยาบาล': h_name,
                'Service Plan': h_sp,
                'สาขา': spec,
                'ควรมี (คน)': int(req_val),
                'มีจริง (คน)': int(active_cnt),
                'ผลต่าง (Gap)': int(gap),
                'สถานะ': status_text
            })

if gap_records:
    df_gap_table = pd.DataFrame(gap_records)
    # Sort for better viewing
    df_gap_table = df_gap_table.sort_values(by=['ผลต่าง (Gap)', 'เขต', 'จังหวัด'], ascending=[True, True, True])
    
    def highlight_gap(val):
        color = '#ffe6e6' if val < 0 else '#e6ffe6'
        return f'background-color: {color}'
        
    st.dataframe(
        df_gap_table.style.map(highlight_gap, subset=['ผลต่าง (Gap)']),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("✅ ไม่พบรายการขาดแคลนตามเงื่อนไขที่ท่านเลือก (หรือโรงพยาบาลที่เลือกไม่มีเกณฑ์ขั้นต่ำรองรับ)")

st.markdown("---")

# --- Section 3: Visualizations ---
col_chart1, col_chart2 = st.columns(2)
with col_chart1:
    st.markdown("**จำนวนผู้เชี่ยวชาญจำแนกตาม 7 สาขาหลัก**")
    branch_count = df_filtered['สาขาหลัก'].value_counts().reset_index()
    branch_count.columns = ['สาขาหลัก', 'จำนวน (คน)']
    fig1 = px.bar(branch_count, x='จำนวน (คน)', y='สาขาหลัก', orientation='h', text='จำนวน (คน)', color='สาขาหลัก', template='plotly_white')
    fig1.update_traces(textposition='outside')
    fig1.update_layout(showlegend=False, yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig1, use_container_width=True)

with col_chart2:
    st.markdown("**สัดส่วนผู้เชี่ยวชาญตามสถานะการปฏิบัติราชการ**")
    status_count = df_filtered['Status'].value_counts().reset_index()
    status_count.columns = ['สถานะ', 'จำนวน (คน)']
    fig2 = px.pie(status_count, values='จำนวน (คน)', names='สถานะ', hole=0.4, template='plotly_white')
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# --- Section 4: Drill-down ---
st.subheader("🔬 เจาะลึกระดับอนุสาขาความเชี่ยวชาญ (Drill-down)")
selected_branch = st.selectbox("เลือกสาขาหลักที่ต้องการดูอนุสาขา:", df_filtered['สาขาหลัก'].unique())
df_sub = df_filtered[df_filtered['สาขาหลัก'] == selected_branch]
sub_count = df_sub['อนุสาขาความเชี่ยวชาญ'].value_counts().reset_index().head(15)
sub_count.columns = ['อนุสาขา', 'จำนวน (คน)']
fig3 = px.bar(sub_count, x='อนุสาขา', y='จำนวน (คน)', text='จำนวน (คน)', color='อนุสาขา', template='plotly_white', title=f"Top 15 อนุสาขาในสาย {selected_branch}")
fig3.update_traces(textposition='outside')
fig3.update_layout(showlegend=False, xaxis={'categoryorder':'total descending'})
st.plotly_chart(fig3, use_container_width=True)
