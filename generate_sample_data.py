import os
import random
import pandas as pd
import numpy as np

# Ensure data dir exists
os.makedirs("data", exist_ok=True)
np.random.seed(42)
random.seed(42)

# 1. Sales Data
dates = pd.date_range(start="2026-01-01", end="2026-06-30", freq="D")
regions = ["North America", "Europe", "Asia-Pacific", "Latin America"]
categories = ["Cloud Infrastructure", "Enterprise AI", "Security Suite", "Developer Tools"]
reps = ["Sarah Jenkins", "Alex Rivera", "Kenji Sato", "Elena Rostova", "Marcus Vance"]

sales_rows = []
for i in range(350):
    date = random.choice(dates).strftime("%Y-%m-%d")
    region = random.choice(regions)
    cat = random.choice(categories)
    rep = random.choice(reps)
    units = random.randint(5, 120)
    price_per_unit = {
        "Cloud Infrastructure": 450,
        "Enterprise AI": 850,
        "Security Suite": 320,
        "Developer Tools": 180,
    }[cat]
    revenue = units * price_per_unit + random.randint(-500, 1500)
    target = revenue * random.uniform(0.85, 1.15)
    margin = round(random.uniform(0.35, 0.72), 3)
    sales_rows.append({
        "Date": date,
        "Region": region,
        "Product_Category": cat,
        "Sales_Rep": rep,
        "Revenue": revenue,
        "Target_Revenue": int(target),
        "Units_Sold": units,
        "Profit_Margin": margin,
    })

pd.DataFrame(sales_rows).to_csv("data/sales_data.csv", index=False)
print("Saved data/sales_data.csv with", len(sales_rows), "rows")

# 2. Operations Data
warehouses = ["Central Hub - Chicago", "West Hub - Reno", "East Hub - Newark", "EU Hub - Frankfurt"]
ship_modes = ["Express Air", "Standard Ground", "Priority Freight", "Same-Day Courier"]
statuses = ["Delivered", "In Transit", "Delayed", "Out for Delivery"]
status_weights = [0.72, 0.15, 0.08, 0.05]

ops_rows = []
for i in range(400):
    order_id = f"ORD-2026-{1000 + i}"
    date = random.choice(dates).strftime("%Y-%m-%d")
    wh = random.choice(warehouses)
    mode = random.choice(ship_modes)
    status = random.choices(statuses, weights=status_weights)[0]
    days = random.randint(1, 4) if mode == "Express Air" else random.randint(2, 8)
    if status == "Delayed":
        days += random.randint(3, 7)
    rating = random.choices([5, 4, 3, 2, 1], weights=[0.6, 0.25, 0.08, 0.04, 0.03])[0]
    cost = round(random.uniform(25.0, 320.0), 2)
    ops_rows.append({
        "Order_ID": order_id,
        "Order_Date": date,
        "Warehouse": wh,
        "Shipping_Mode": mode,
        "Delivery_Status": status,
        "Fulfillment_Time_Days": days,
        "Customer_Rating": rating,
        "Shipping_Cost": cost,
    })

pd.DataFrame(ops_rows).to_csv("data/operations_data.csv", index=False)
print("Saved data/operations_data.csv with", len(ops_rows), "rows")

# 3. Customer Data
segments = ["Enterprise", "Mid-Market", "SMB", "Startup"]
plans = ["Starter", "Professional", "Enterprise Scale", "Custom Unlimited"]
churn_status = ["Active", "At Risk", "Churned"]
churn_weights = [0.84, 0.11, 0.05]

cust_rows = []
for i in range(300):
    cust_id = f"CUST-{2000 + i}"
    signup = random.choice(dates).strftime("%Y-%m-%d")
    seg = random.choice(segments)
    plan = random.choice(plans)
    monthly_spend = {
        "Starter": random.randint(99, 299),
        "Professional": random.randint(499, 1499),
        "Enterprise Scale": random.randint(2500, 7500),
        "Custom Unlimited": random.randint(8000, 18000),
    }[plan]
    status = random.choices(churn_status, weights=churn_weights)[0]
    nps = random.randint(0, 10)
    tickets = random.randint(0, 12) if status != "Active" else random.randint(0, 4)
    cust_rows.append({
        "Customer_ID": cust_id,
        "Signup_Date": signup,
        "Segment": seg,
        "Plan": plan,
        "Monthly_Spend": monthly_spend,
        "NPS_Score": nps,
        "Churn_Status": status,
        "Support_Tickets": tickets,
    })

pd.DataFrame(cust_rows).to_csv("data/customer_data.csv", index=False)
print("Saved data/customer_data.csv with", len(cust_rows), "rows")
