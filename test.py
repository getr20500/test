import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px

# โหลดข้อมูลจาก Excel
df = pd.ExcelFile("2026 Data Test1 Final - Busy Buffet Dataset.xlsx")
dfs = []
for sheet in df.sheet_names:
    temp = pd.read_excel("2026 Data Test1 Final - Busy Buffet Dataset.xlsx", sheet_name=sheet)
    temp["date"] = sheet  
    dfs.append(temp)
df = pd.concat(dfs, ignore_index=True)
df = df[[
    'service_no.', 'pax', 'queue_start', 'queue_end',
    'table_no.', 'meal_start', 'meal_end', 'Guest_type', 'date'
]]
sum_pax = df.groupby("Guest_type")["pax"].sum()

df["is_queue"] = df["queue_start"].notna()
df["is_walkaway"] = df["queue_start"].notna() & df["meal_start"].isna()
# แปลงเป็น datetime (ถ้ายังไม่ได้แปลง)
df["queue_start"] = pd.to_datetime(df["queue_start"], format="%H:%M:%S", errors="coerce")
df["queue_end"] = pd.to_datetime(df["queue_end"], format="%H:%M:%S", errors="coerce")
# คำนวณเวลารอ (หน่วยนาที)
df["wait_time"] = (df["queue_end"] - df["queue_start"]).dt.total_seconds() / 60
df["wait_time"] = df["wait_time"].fillna(0)
df_queue = df[df['is_queue'] == True].copy()

count_by_type = df_queue["Guest_type"].value_counts().reset_index()
count_by_type.columns = ["Guest Type", "Customer Count"]
df_queue["Status"] = df_queue["is_walkaway"].apply(lambda x: "Walkaway" if x == 1 else "Wait")

avg_wait = df_queue.groupby(["Guest_type", "Status"])["wait_time"].mean().reset_index()
pivot_table = avg_wait.pivot(index="Guest_type", columns="Status", values="wait_time")

bins = [0, 15, 30, 45, 60, 100]
labels = ['0-15', '15-30', '30-45', '45-60', '60+']
df_queue['wait_bin'] = pd.cut(df_queue['wait_time'],bins=bins,labels=labels,right=False)
summary = df_queue.groupby('wait_bin').agg(total=('wait_time', 'count'),walkaway=('is_walkaway', 'sum')).reset_index()
walkaway_rate = summary.copy()
walkaway_rate['walkaway_rate'] = summary['walkaway'] / summary['total']
qi = df_queue[df_queue["Guest_type"]== "In house"].copy()
summary_qi = qi.groupby('wait_bin').agg(total=('wait_time', 'count'),walkaway=('is_walkaway', 'sum'))
summary_qi['walkaway_rate'] = summary_qi['walkaway'] / summary_qi['total']
qw = df_queue[df_queue["Guest_type"]== "Walk in"].copy()
summary_qw = qw.groupby('wait_bin').agg(total=('wait_time', 'count'),walkaway=('is_walkaway', 'sum'))
summary_qw['walkaway_rate'] = summary_qw['walkaway'] / summary_qw['total']


binst = [6, 7, 8, 9, 10, 11, 12]
labelst = ['6-7', '7-8', '8-9', '9-10', '10-11', '11-12']
df["arrival_time"] = df["queue_start"]
df["arrival_time"] = df["arrival_time"].fillna(df["meal_start"])
df["arrival_time"] = pd.to_datetime(df["arrival_time"].astype(str), errors="coerce")
df["hour"] = df["arrival_time"].dt.hour
df["time_slot"] = pd.cut(df["hour"],bins=binst,labels=labelst,right=False )
time_slot = df.groupby("time_slot").agg(total_customers=("service_no.", "count"),queue_customers=("is_queue", "sum")).reset_index()



st.title("📊 Queue Behavior Dashboard")
col3, col4 = st.columns(2)
with col3:
    st.subheader("Customer Count by Guest Type")
    st.dataframe(count_by_type, use_container_width=True)
    st.metric("Total Customers", len(df_queue))
    st.metric("Average Wait Time (Overall)", round(df_queue["wait_time"].mean(), 2))
with col4:
    st.subheader("Customer Distribution")
    st.bar_chart(count_by_type.set_index("Guest Type"))
st.subheader("Average Wait Time by Guest Type and Status")
st.dataframe(avg_wait, use_container_width=True)
col5, col6 = st.columns(2)
with col5:
    st.subheader("Comparison Table")
    st.dataframe(pivot_table, use_container_width=True)
with col6:
    st.subheader("Comparison Chart")
    df_chart = pivot_table.reset_index()
    chart = alt.Chart(df_chart).transform_fold(
    ["Walkaway", "Wait"],
    as_=["Type", "Value"]
    ).mark_bar().encode(
    x=alt.X("Guest_type:N", title="Guest Type"),
    y=alt.Y("Value:Q", stack=None),  # 🔥 เอาการซ้อนออก
    color="Type:N",
    xOffset="Type:N"  # 🔥 ทำให้แท่งอยู่ข้างกัน
    )
    st.altair_chart(chart, use_container_width=True)
st.divider()

col7, col8 = st.columns(2)
with col7:
    st.subheader("Customer Distribution")
    fig = px.bar(summary,x="wait_bin",y=["total", "walkaway"],barmode="group")
    st.plotly_chart(fig)
with col8:
    st.subheader("walkaway_rate")
    st.bar_chart(walkaway_rate.set_index("wait_bin")['walkaway_rate'])

compare = summary_qi.merge(summary_qw,on="wait_bin",suffixes=("_inhouse", "_walkin")).reset_index()
fig = px.bar(compare,x="wait_bin",y=["walkaway_rate_inhouse", "walkaway_rate_walkin"],barmode="group")
st.plotly_chart(fig)
st.divider()

file = "2026 Data Test1 Final - Busy Buffet Dataset.xlsx"
xls = pd.ExcelFile(file)
OPEN_HOURS = 6
results = []
for sheet in xls.sheet_names:
    # อ่านแต่ละ sheet
    df = pd.read_excel(file, sheet_name=sheet)
    # แปลงเวลา
    df["meal_start"] = pd.to_datetime(df["meal_start"], format="%H:%M:%S", errors="coerce")
    df["meal_end"] = pd.to_datetime(df["meal_end"], format="%H:%M:%S", errors="coerce")
    # clean + split table
    df['table_no.'] = (df['table_no.'].astype(str).str.replace(r'\s+', '', regex=True).str.upper().str.split('[-/]'))  
  # explode
    df = df.explode('table_no.')    
    # usage (ชั่วโมง)
    df['usage'] = (df['meal_end'] - df['meal_start']).dt.total_seconds() / 3600
    df['usage'] = df['usage'].fillna(0)  
    # คำนวณ
    total_usage = df['usage'].sum()
    unique_tables = df['table_no.'].nunique()
    utilization = (total_usage / (unique_tables * OPEN_HOURS)) * 100  
    # เก็บผล
    results.append({"date": sheet,"utilization_%": utilization})
# ✅ แปลงเป็น DataFrame
final_df = pd.DataFrame(results)
# เรียงตามวัน (ถ้า sheet เป็นวันที่)
final_df = final_df.sort_values(by="date")

st.subheader("Daily Table Utilization (%)")
st.bar_chart(final_df.set_index("date"))
st.subheader("จำนวนลูกค้าแยกตามช่วงเวลา (06:00–12:00)")
col9, col10 = st.columns(2)
with col9:
    st.subheader("total_customers")
    st.bar_chart(time_slot.set_index("time_slot")['total_customers'])
with col10:
    st.subheader("queue_customers")
    st.bar_chart(time_slot.set_index("time_slot")['queue_customers'])
st.divider()


result = []  # ✅ เอาไว้เก็บข้อมูล
result1 = []
pax_day = []
pax_day_type = []
for sheet in xls.sheet_names:
    df = pd.read_excel(file, sheet_name=sheet)
    df["meal_start"] = pd.to_datetime(df["meal_start"], format="%H:%M:%S", errors="coerce")
    df["meal_end"] = pd.to_datetime(df["meal_end"], format="%H:%M:%S", errors="coerce")
    df['usage'] = (df['meal_end'] - df['meal_start']).dt.total_seconds() / 3600
    df_seated = df[df["usage"].notna()]
    grouped = df_seated.groupby("Guest_type")["usage"].mean()
    group = df.groupby("Guest_type")["pax"].sum()
    for guest_type, value in grouped.items():
        result.append({"date": sheet,"Guest_type": guest_type,"usage": value})
    for guest_type, value in group.items():
        pax_day_type.append({"date": sheet,"Guest_type": guest_type,"pax": value})
    result1.append({"date": sheet,"usage": df_seated["usage"].mean()})
    pax_day.append({"date": sheet,"usage": df["pax"].sum()})
# ✅ รวมเป็น DataFrame
result_df = pd.DataFrame(result)
result_df1 = pd.DataFrame(result1)
pax_day =pd.DataFrame(pax_day)
pax_day_type=pd.DataFrame(pax_day_type)
# table = result_df.pivot(index="date", columns="Guest_type", values="usage")
st.subheader("📊 Usage by Guest Type")
table = result_df.pivot(index="date", columns="Guest_type", values="usage").reset_index()
chart = alt.Chart(table).transform_fold(["In house", "Walk in"],as_=["Guest_type", "usage"]).mark_bar().encode(x=alt.X("date:N", title="Date"),
    y=alt.Y("usage:Q", stack=None, title="Usage (hours)"),  # 🔥 ปิด stack
    color="Guest_type:N",
    xOffset="Guest_type:N" ) # 🔥 ทำให้แท่งอยู่ข้างกัน
st.altair_chart(chart, use_container_width=True)
st.metric("Average seating time", round(result_df["usage"].mean(),2))
st.divider()

st.subheader("Mean of Usage (hours)")
st.bar_chart(result_df1.set_index("date"))
st.divider()

st.subheader("Daily user count")
st.bar_chart(pax_day.set_index("date"))
table = pax_day_type.pivot(index="date", columns="Guest_type", values="pax").reset_index()
chart = alt.Chart(table).transform_fold(["In house", "Walk in"],as_=["Guest_type", "pax"]).mark_bar().encode(x=alt.X("date:N", title="Date"),
    y=alt.Y("pax:Q", stack=None, title="Daily"),  # 🔥 ปิด stack
    color="Guest_type:N",
    xOffset="Guest_type:N" ) # 🔥 ทำให้แท่งอยู่ข้างกัน
st.altair_chart(chart, use_container_width=True)
st.divider()

st.subheader("Customer Count by Guest Type")
st.bar_chart(sum_pax)
