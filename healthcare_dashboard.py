import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Page Config
st.set_page_config(
    page_title="Healthcare Analytics Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stApp { background-color: #0f1117; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #1a1d2e; }
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1e2340, #252a45);
        border-radius: 12px;
        padding: 16px 20px;
        border-left: 4px solid #4e8cff;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    [data-testid="stMetricLabel"] { color: #a0aec0 !important; font-size: 14px !important; }
    [data-testid="stMetricValue"] { color: #ffffff !important; font-size: 28px !important; font-weight: 700 !important; }
    h1 { color: #4e8cff !important; font-size: 32px !important; }
    h2, h3 { color: #e2e8f0 !important; }
    hr { border-color: #2d3748; }
    .alert-box {
        background: linear-gradient(135deg, #2d1b1b, #3d2020);
        border-left: 4px solid #ff4444;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
        font-size: 14px;
    }
    .insight-box {
        background: linear-gradient(135deg, #1a2d1a, #1e3a1e);
        border-left: 4px solid #44ff88;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

# Load Data
@st.cache_data
def load_data():
    path = "."
    final = pd.read_csv(f"{path}/final_admission_level_dataset.csv")
    hospital = pd.read_csv(f"{path}/hospital_summary.csv")
    dept = pd.read_csv(f"{path}/department_summary.csv")
    return final, hospital, dept

final, hospital, dept = load_data()

# Doctors data
@st.cache_data
def load_doctors():
    try:
        return pd.read_csv("./doctors.csv")
    except:
        return None

doctors = load_doctors()

# ── SIDEBAR ───────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏥 Healthcare Analytics")
    st.markdown("---")
    st.markdown("### 🔍 Filters")
    dept_list = ["All"] + sorted(final['department_name'].dropna().unique().tolist())
    selected_dept = st.selectbox("🏬 Department", dept_list)
    severity_list = ["All"] + sorted(final['severity_level'].dropna().unique().tolist())
    selected_severity = st.selectbox("⚠️ Severity", severity_list)
    admission_list = ["All"] + sorted(final['admission_type'].dropna().unique().tolist())
    selected_admission = st.selectbox("🚑 Admission Type", admission_list)
    gender_list = ["All"] + sorted(final['gender'].dropna().unique().tolist())
    selected_gender = st.selectbox("👤 Gender", gender_list)
    st.markdown("---")
    st.caption("Made with ❤️ using Streamlit")

# Apply Filters
df = final.copy()
if selected_dept != "All":
    df = df[df['department_name'] == selected_dept]
if selected_severity != "All":
    df = df[df['severity_level'] == selected_severity]
if selected_admission != "All":
    df = df[df['admission_type'] == selected_admission]
if selected_gender != "All":
    df = df[df['gender'] == selected_gender]

chart_template = "plotly_dark"

# ── HEADER ────────────────────────────────────────────
st.markdown("# 🏥 Healthcare Analytics Dashboard")
st.caption("Real-time insights from patient admissions data")
st.markdown("---")

# ── KPI CARDS ─────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("🏨 Total Admissions", f"{len(df):,}")
col2.metric("🔄 Readmission Rate", f"{df['readmitted_flag'].mean()*100:.1f}%")
avg_cost = df['gross_amount'].mean() if 'gross_amount' in df.columns else 0
col3.metric("💰 Avg Cost", f"₹{avg_cost:,.0f}")
col4.metric("🛏️ Avg Stay", f"{df['los_days'].mean():.1f} days")
high_risk = len(df[df['severity_level'] == 'Critical']) if 'severity_level' in df.columns else 0
col5.metric("🚨 Critical Cases", f"{high_risk:,}")

st.markdown("---")

# ── SMART INSIGHTS ────────────────────────────────────
st.markdown("### 💡 Smart Insights")
c1, c2, c3 = st.columns(3)

readmission_rate = df['readmitted_flag'].mean() * 100
top_dept = df.groupby('department_name')['readmitted_flag'].mean().idxmax() if len(df) > 0 else "N/A"
avg_los = df['los_days'].mean()

with c1:
    if readmission_rate > 40:
        st.markdown(f'<div class="alert-box">🚨 <b>High Alert!</b> Readmission rate is {readmission_rate:.1f}% — needs immediate attention!</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="insight-box">✅ <b>Good!</b> Readmission rate is {readmission_rate:.1f}% — under control</div>', unsafe_allow_html=True)

with c2:
    st.markdown(f'<div class="alert-box">⚠️ <b>Watch:</b> <b>{top_dept}</b> has highest readmission rate</div>', unsafe_allow_html=True)

with c3:
    if avg_los > 5:
        st.markdown(f'<div class="alert-box">🛏️ <b>Long Stays:</b> Avg {avg_los:.1f} days — review discharge process</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="insight-box">✅ <b>Efficient:</b> Avg stay {avg_los:.1f} days — well managed</div>', unsafe_allow_html=True)

st.markdown("---")

# ── MONTHLY TREND ─────────────────────────────────────
st.markdown("### 📅 Monthly Admission Trend")
if 'admission_date' in df.columns:
    df['admission_date'] = pd.to_datetime(df['admission_date'], errors='coerce')
    df['month'] = df['admission_date'].dt.to_period('M').astype(str)
    monthly = df.groupby('month').agg(
        admissions=('admission_id', 'count'),
        readmissions=('readmitted_flag', 'sum')
    ).reset_index()
    fig_trend = px.line(monthly, x='month', y=['admissions', 'readmissions'],
                        template=chart_template,
                        color_discrete_map={'admissions': '#4e8cff', 'readmissions': '#ff6b6b'},
                        markers=True)
    fig_trend.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=300,
                            xaxis_tickangle=45, legend_title="")
    st.plotly_chart(fig_trend, use_container_width=True)

st.markdown("---")

# ── ROW 1 ─────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📈 Readmission Rate by Department")
    d = df.groupby('department_name')['readmitted_flag'].mean().reset_index()
    d.columns = ['Department', 'Readmission Rate']
    d = d.sort_values('Readmission Rate', ascending=True)
    fig = px.bar(d, x='Readmission Rate', y='Department', orientation='h',
                 color='Readmission Rate', color_continuous_scale='Reds',
                 template=chart_template)
    fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=350)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### 🩺 Chronic Condition Analysis")
    if 'primary_chronic_condition' in df.columns:
        cc = df['primary_chronic_condition'].value_counts().head(8).reset_index()
        cc.columns = ['Condition', 'Count']
        fig_cc = px.bar(cc, x='Count', y='Condition', orientation='h',
                        color='Count', color_continuous_scale='Teal',
                        template=chart_template)
        fig_cc.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=350)
        st.plotly_chart(fig_cc, use_container_width=True)

# ── ROW 2 ─────────────────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    st.markdown("### 🔵 Severity Distribution")
    s = df['severity_level'].value_counts().reset_index()
    s.columns = ['Severity', 'Count']
    fig3 = px.pie(s, names='Severity', values='Count', hole=0.5,
                  color_discrete_sequence=px.colors.qualitative.Bold,
                  template=chart_template)
    fig3.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=320)
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.markdown("### 🎯 Readmission Risk Gauge")
    rate = df['readmitted_flag'].mean() * 100
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=rate,
        delta={'reference': 30, 'increasing': {'color': "#ff4444"}, 'decreasing': {'color': "#44ff88"}},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': "white"},
            'bar': {'color': "#4e8cff"},
            'steps': [
                {'range': [0, 30], 'color': '#1a3a1a'},
                {'range': [30, 60], 'color': '#3a3a1a'},
                {'range': [60, 100], 'color': '#3a1a1a'}
            ],
            'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 50}
        },
        title={'text': "Readmission Rate %", 'font': {'color': 'white'}}
    ))
    fig_gauge.update_layout(
        template=chart_template,
        margin=dict(l=20,r=20,t=60,b=20),
        height=320,
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white'}
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

# ── HOSPITAL PERFORMANCE ──────────────────────────────
st.markdown("---")
st.markdown("### 🏨 Hospital Performance")
col5, col6 = st.columns(2)

with col5:
    fig5 = px.bar(hospital, x='hospital_name', y='total_admissions',
                  color='total_admissions', color_continuous_scale='Viridis',
                  template=chart_template, title='Total Admissions by Hospital')
    fig5.update_xaxes(tickangle=45)
    fig5.update_layout(margin=dict(l=0,r=0,t=40,b=80), height=380)
    st.plotly_chart(fig5, use_container_width=True)

with col6:
    fig6 = px.bar(hospital, x='hospital_name', y='readmission_rate',
                  color='readmission_rate', color_continuous_scale='Reds',
                  template=chart_template, title='Readmission Rate by Hospital')
    fig6.update_xaxes(tickangle=45)
    fig6.update_layout(margin=dict(l=0,r=0,t=40,b=80), height=380)
    st.plotly_chart(fig6, use_container_width=True)

# ── TOP DOCTORS LEADERBOARD ───────────────────────────
st.markdown("---")
st.markdown("### 🏆 Top Doctors Leaderboard")
if doctors is not None and 'primary_doctor_id' in df.columns:
    doc_stats = df.groupby('primary_doctor_id').agg(
        total_patients=('patient_id', 'count'),
        readmission_rate=('readmitted_flag', 'mean'),
        avg_los=('los_days', 'mean')
    ).reset_index()
    doc_stats = doc_stats.merge(doctors[['doctor_id','doctor_name','specialization','doctor_grade']],
                                 left_on='primary_doctor_id', right_on='doctor_id', how='left')
    doc_stats = doc_stats.sort_values('total_patients', ascending=False).head(10)
    doc_stats['readmission_rate'] = (doc_stats['readmission_rate'] * 100).round(1).astype(str) + '%'
    doc_stats['avg_los'] = doc_stats['avg_los'].round(1).astype(str) + ' days'
    doc_stats['Rank'] = ['🥇','🥈','🥉','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣','🔟'][:len(doc_stats)]
    show_cols = ['Rank','doctor_name','specialization','doctor_grade','total_patients','readmission_rate','avg_los']
    show_cols = [c for c in show_cols if c in doc_stats.columns]
    st.dataframe(doc_stats[show_cols].rename(columns={
        'doctor_name': 'Doctor', 'specialization': 'Specialization',
        'doctor_grade': 'Grade', 'total_patients': 'Patients',
        'readmission_rate': 'Readmission Rate', 'avg_los': 'Avg Stay'
    }), use_container_width=True, hide_index=True)

# ── AGE & ADMISSION ───────────────────────────────────
st.markdown("---")
col7, col8 = st.columns(2)

with col7:
    st.markdown("### 🚑 Admission Type")
    a = df['admission_type'].value_counts().reset_index()
    a.columns = ['Type', 'Count']
    fig7 = px.bar(a, x='Type', y='Count', color='Type',
                  color_discrete_sequence=px.colors.qualitative.Set2,
                  template=chart_template)
    fig7.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=300, showlegend=False)
    st.plotly_chart(fig7, use_container_width=True)

with col8:
    st.markdown("### 👴 Age Group Distribution")
    ag = df['age_group'].value_counts().reset_index()
    ag.columns = ['Age Group', 'Count']
    fig8 = px.bar(ag, x='Age Group', y='Count', color='Age Group',
                  color_discrete_sequence=px.colors.qualitative.Pastel,
                  template=chart_template)
    fig8.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=300, showlegend=False)
    st.plotly_chart(fig8, use_container_width=True)

# ── DATA TABLE ────────────────────────────────────────
st.markdown("---")
st.markdown("### 📋 Patient Data")
search = st.text_input("🔎 Search by Department or Diagnosis", "")
cols = ['admission_id','patient_id','department_name','severity_level',
        'admission_type','diagnosis','los_days','readmitted_flag']
if 'gross_amount' in df.columns:
    cols.append('gross_amount')
available = [c for c in cols if c in df.columns]
filtered_table = df[available]
if search:
    mask = filtered_table.apply(lambda col: col.astype(str).str.contains(search, case=False)).any(axis=1)
    filtered_table = filtered_table[mask]
st.dataframe(filtered_table.head(100), use_container_width=True)

st.markdown("---")
st.caption("🏥 Healthcare Analytics Dashboard | Powered by Streamlit & Plotly")
