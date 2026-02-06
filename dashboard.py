import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency

st.set_page_config(page_title="E-Commerce Analytics Dashboard", layout="centered")

sns.set_theme(style='ticks')
plt.style.use('seaborn-v0_8-whitegrid')

def create_monthly_orders_df(df):
    monthly_orders_df = df.resample(rule='ME', on='order_purchase_timestamp').agg({
        "order_id": "nunique",
        "price": "sum"
    })
    monthly_orders_df.index = monthly_orders_df.index.strftime('%Y-%m')
    monthly_orders_df = monthly_orders_df.reset_index()
    monthly_orders_df.rename(columns={
        "order_id": "order_count",
        "price": "revenue"
    }, inplace=True)
    return monthly_orders_df

def create_sum_order_items_df(df):
    sum_order_items_df = df.groupby("product_category_name_english").order_id.count().sort_values(ascending=False).reset_index()
    return sum_order_items_df

def create_by_city_df(df):
    bycity_df = df.groupby(by="customer_city").customer_id.nunique().reset_index()
    bycity_df.rename(columns={
        "customer_id": "customer_count"
    }, inplace=True)
    return bycity_df

def create_rfm_df(df):
    by_rfm_df = df.groupby(by="customer_unique_id", as_index=False).agg({
        "order_purchase_timestamp": "max", 
        "order_id": "nunique",
        "price": "sum"
    })
    by_rfm_df.columns = ["customer_unique_id", "max_order_timestamp", "frequency", "monetary"]
    
    by_rfm_df["max_order_timestamp"] = pd.to_datetime(by_rfm_df["max_order_timestamp"]).dt.date
    recent_date = df["order_purchase_timestamp"].dt.date.max()
    by_rfm_df["recency"] = by_rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    
    return by_rfm_df

@st.cache_data
def load_data():
    all_df = pd.read_csv("main_data.csv")
    datetime_columns = ["order_purchase_timestamp", "order_delivered_carrier_date", 
                        "order_delivered_customer_date", "order_estimated_delivery_date"]
    
    all_df.sort_values(by="order_purchase_timestamp", inplace=True)
    all_df.reset_index(inplace=True, drop=True)

    for column in datetime_columns:
        all_df[column] = pd.to_datetime(all_df[column])
        
    return all_df

all_df = load_data()

min_date = all_df["order_purchase_timestamp"].min()
max_date = all_df["order_purchase_timestamp"].max()

default_start_date = max_date - pd.DateOffset(years=1)

st.header('E-Commerce Analytics Dashboard')

st.subheader("Filter Data")
col_date1, col_date2 = st.columns(2)

with col_date1:
    start_date = st.date_input(
        label='Mulai Tanggal',
        min_value=min_date,
        max_value=max_date,
        value=default_start_date
    )

with col_date2:
    end_date = st.date_input(
        label='Sampai Tanggal',
        min_value=min_date,
        max_value=max_date,
        value=max_date
    )

main_df = all_df[(all_df["order_purchase_timestamp"] >= str(start_date)) & 
                (all_df["order_purchase_timestamp"] <= str(end_date))]

monthly_orders_df = create_monthly_orders_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
bycity_df = create_by_city_df(main_df)
rfm_df = create_rfm_df(main_df)


st.subheader('Monthly Orders Trend')

col1, col2 = st.columns(2)

with col1:
    total_orders = monthly_orders_df.order_count.sum()
    st.metric("Total Orders", value=total_orders)

with col2:
    total_revenue = format_currency(monthly_orders_df.revenue.sum(), "BRL", locale='pt_BR') 
    st.metric("Total Revenue", value=total_revenue)

fig, ax = plt.subplots(figsize=(16, 6))
ax.plot(
    monthly_orders_df["order_purchase_timestamp"],
    monthly_orders_df["order_count"],
    marker='o', 
    linewidth=2,
    color="#72BCD4"
)
ax.set_title("Number of Orders per Month", fontsize=20)
ax.set_xlabel("Month", fontsize=15)
ax.set_ylabel("Order Count", fontsize=15)
ax.tick_params(axis='y', labelsize=12)
ax.tick_params(axis='x', labelsize=12, rotation=45)
st.pyplot(fig)

st.subheader("Best & Worst Performing Product")

top_product = sum_order_items_df.head(1)
worst_product = sum_order_items_df.sort_values(by="order_id", ascending=True).head(1)

col_best, col_worst = st.columns(2)

with col_best:
    st.metric(
        label="Best Performing Product", 
        value=top_product["product_category_name_english"].values[0], 
        delta=f"{top_product['order_id'].values[0]} Sales"
    )

with col_worst:
    st.metric(
        label="Worst Performing Product", 
        value=worst_product["product_category_name_english"].values[0], 
        delta=f"{worst_product['order_id'].values[0]} Sales",
        delta_color="inverse"
    )

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(24, 12))

colors = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

sns.barplot(
    x="order_id", 
    y="product_category_name_english", 
    data=sum_order_items_df.head(5), 
    hue="product_category_name_english",
    palette=colors, 
    legend=False,
    ax=ax[0]
)
ax[0].set_ylabel(None)
ax[0].set_xlabel("Number of Sales", fontsize=20)
ax[0].set_title("Best Performing Product", loc="center", fontsize=24)
ax[0].tick_params(axis='y', labelsize=15)
ax[0].tick_params(axis='x', labelsize=15)

sns.barplot(
    x="order_id", 
    y="product_category_name_english", 
    data=sum_order_items_df.sort_values(by="order_id", ascending=True).head(5), 
    hue="product_category_name_english",
    palette=colors, 
    legend=False,
    ax=ax[1]
)
ax[1].set_ylabel(None)
ax[1].set_xlabel("Number of Sales", fontsize=20)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Worst Performing Product", loc="center", fontsize=24)
ax[1].tick_params(axis='y', labelsize=15)
ax[1].tick_params(axis='x', labelsize=15)

st.pyplot(fig)

st.subheader("Customer Demographics")

top_cities = bycity_df.sort_values(by="customer_count", ascending=False).head(10)

fig, ax = plt.subplots(figsize=(12, 6))

colors_city = ["#72BCD4"] + ["#D3D3D3"] * (len(top_cities) - 1)

sns.barplot(
    x="customer_count", 
    y="customer_city",
    data=top_cities,
    hue="customer_city",
    palette=colors_city,
    legend=False,
    ax=ax
)
ax.set_title("Number of Customer by City (Top 10)", loc="center", fontsize=18)
ax.set_ylabel(None)
ax.set_xlabel("Customer Count")
ax.tick_params(axis='y', labelsize=12)
st.pyplot(fig)


st.subheader("Best Customer Based on RFM Parameters")

col_rfm1, col_rfm2, col_rfm3 = st.columns(3)

with col_rfm1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)

with col_rfm2:
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)

with col_rfm3:
    avg_monetary = format_currency(rfm_df.monetary.mean(), "BRL", locale='pt_BR') 
    st.metric("Average Monetary", value=avg_monetary)

st.markdown("#### Top 10 Customers by Recency (Low is Better)")
fig, ax = plt.subplots(figsize=(14, 6))
top_recency = rfm_df.sort_values(by="recency", ascending=True).head(10)
colors_rfm = ["#72BCD4"] * 10

sns.barplot(
    y="recency", 
    x="customer_unique_id", 
    data=top_recency, 
    hue="customer_unique_id",
    palette=colors_rfm, 
    legend=False,
    ax=ax
)
ax.set_ylabel("Recency (days)", fontsize=12)
ax.set_xlabel("Customer Unique ID", fontsize=12)
ax.tick_params(axis='x', rotation=45, labelsize=10) 
st.pyplot(fig)

st.markdown("#### Top 10 Customers by Frequency")
fig, ax = plt.subplots(figsize=(14, 6))
top_frequency = rfm_df.sort_values(by="frequency", ascending=False).head(10)

sns.barplot(
    y="frequency", 
    x="customer_unique_id", 
    data=top_frequency, 
    hue="customer_unique_id",
    palette=colors_rfm, 
    legend=False,
    ax=ax
)
ax.set_ylabel("Frequency", fontsize=12)
ax.set_xlabel("Customer Unique ID", fontsize=12)
ax.tick_params(axis='x', rotation=45, labelsize=10)
st.pyplot(fig)

st.markdown("#### Top 10 Customers by Monetary")
fig, ax = plt.subplots(figsize=(14, 6))
top_monetary = rfm_df.sort_values(by="monetary", ascending=False).head(10)

sns.barplot(
    y="monetary", 
    x="customer_unique_id", 
    data=top_monetary, 
    hue="customer_unique_id",
    palette=colors_rfm, 
    legend=False,
    ax=ax
)
ax.set_ylabel("Monetary (BRL)", fontsize=12)
ax.set_xlabel("Customer Unique ID", fontsize=12)
ax.tick_params(axis='x', rotation=45, labelsize=10)
st.pyplot(fig)

st.caption('Copyright (c) Farhan 2026')