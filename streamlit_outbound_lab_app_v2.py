import streamlit as st
import pandas as pd
import random

# -------------------------
# Page Configuration
# -------------------------
st.set_page_config(page_title="Prospecting Workspace", layout="wide")
st.title("Prospecting Workspace")
st.caption("Three views: Use-Case Led, Accounts-Led, and Intent-Driven")

# Global style: wrap table headers across ALL tables
st.markdown(
    """
    <style>
    /* Try multiple selectors to be robust across Streamlit versions */
    div[data-testid="stDataFrame"] div[role="columnheader"] * { 
        white-space: normal !important; 
        overflow-wrap: anywhere !important; 
        text-overflow: clip !important;
    }
    [data-testid="stTable"] th { 
        white-space: normal !important; 
        overflow-wrap: anywhere !important; 
        text-overflow: clip !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# For reproducibility
SEED = 42
random.seed(SEED)

# -------------------------
# Helper Generators
# -------------------------
industries = [
    "Retail",
    "FinTech",
    "Travel",
    "Gaming",
    "Telecom",
    "Media & Entertainment",
    "Healthcare",
    "B2B SaaS",
    "Marketplaces",
    "Consumer Electronics",
]

sub_industries = [
    "Fashion eCommerce",
    "Digital Banking",
    "Airlines",
    "Mobile Games",
    "ISPs",
    "Streaming",
    "Telemedicine",
    "Dev Tools",
    "Food Delivery",
    "Smart Home",
]

countries = ["US", "UK", "DE", "FR", "IL", "NL", "AU", "CA", "ES", "SE"]

personas = [
    "VP Marketing",
    "Director of Growth",
    "Head of SEO",
    "Head of Paid Media",
    "VP Sales",
    "Head of Product",
    "Head of BI/Analytics",
    "CMO",
    "Ecommerce Director",
    "Investor Relations Lead",
]

message_angles = [
    "Beat competitors with category benchmarks",
    "Reduce CAC via channel mix optimization",
    "Capture seasonal demand spikes",
    "Win RFPs with verified traffic intelligence",
    "Expand into new markets with TAM insights",
    "Defend market share against disruptors",
    "Identify upsell opportunities in key accounts",
    "Prioritize content by competitor gaps",
    "Optimize media spend with audience overlaps",
    "Signal-based outreach for warmer meetings",
]

triggers = [
    "Traffic spike",
    "Funding round",
    "New product launch",
    "Hiring surge",
    "PR coverage",
    "App rank change",
    "Market entry",
    "Budget season",
    "Quarterly earnings",
    "M&A rumor",
]

products = ["Web", "Shopper", "Investors", "Ads"]

department_types = [
    "Marketing",
    "Sales",
    "Growth",
    "Product",
    "Analytics",
    "eCommerce",
    "PR/Comms",
    "Investor Relations",
]

parent_domains = [
    "acmecorp.com",
    "globex.com",
    "initech.com",
    "umbrella.com",
    "starkindustries.com",
    "wayneenterprises.com",
    "wonkaindustries.com",
    "hooli.com",
    "massiveDynamic.com",
    "cyberdyne.com",
]

# Ensure URL-friendly
clean_domain = lambda d: d.lower().replace(" ", "")

accounts = [
    {
        "Industry": industries[i],
        "Sub-Industry": sub_industries[i],
        "Country": countries[i],
        "Account Name": parent_domains[i].split(".")[0].title(),
        "Parent Company Domain": clean_domain(parent_domains[i]),
        "Website": f"https://www.{clean_domain(parent_domains[i])}",
    }
    for i in range(10)
]

# -------------------------
# Section 1: Use-Case Led Prospecting
# -------------------------
use_case_rows = []
for i in range(10):
    industry = industries[i]
    persona = personas[i]
    angle = message_angles[i]
    trigger = triggers[i]
    product_choice = random.choice(products)
    hyp_type = random.choice(["Market-Led", "Accounts-Led"])  # as requested

    user_story = (
        f"As a {persona} in a {industry} company, I'd like to {angle.lower()}, "
        f"because I need to act on {trigger.lower()} data."
    )
    slides_url = f"https://slides.example.com/{clean_domain(accounts[i]['Parent Company Domain'])}/qbr"

    # ---- Synthetic KPIs with requested constraints ----
    n_accounts = random.randint(3, 50)
    n_leads = random.randint(7, 200)
    engaged = max(1, int(n_leads * random.uniform(0.05, 0.80)))
    exhausted = max(0, int(engaged * random.uniform(0.05, 1.00)))
    meeting_rate = random.uniform(0.01, 0.10)  # 1% - 10%
    n_opps = max(1, int(n_leads * meeting_rate * random.uniform(0.10, 0.40)))

    use_case_rows.append({
        "Hypothesis Type (Market-Led \\ Accounts-Led)": hyp_type,
        "Industry": industry,
        "ICP (Personas)": persona,
        "Message Angle": angle,
        "Trigger": trigger,
        "Product (Web, Shopper, Investors, Ads)": product_choice,
        "Hypothesis User Story (As a XXX in XXX Company, i'd like to XXX, because I need XXX)": user_story,
        "Slides": slides_url,
        "Specific Use Case Related Insights": f"Top competitors in {industry} grew share by {random.randint(3,12)}% QoQ.",
        "Cadence": random.choice(["3-touch warm-up", "7-step multi-channel", "5-step email-first", "Phone-first 4-step"]),
        "# of accounts": n_accounts,
        "# of leads in campaign": n_leads,
        "Departments Types": ", ".join(random.sample(department_types, k=random.randint(3, 5))),
        "# of engaged leads": engaged,
        "# of leads exausted": exhausted,
        "Meeting Rate": f"{round(meeting_rate*100, 1)}%",
        "# of opportunities": n_opps,
    })

use_case_df = pd.DataFrame(use_case_rows)

# -------------------------
# Section 2: Accounts-Led Prospecting
# -------------------------
account_rows = []
for i in range(10):
    base = accounts[i]
    def r(a, b):
        return random.randint(a, b)

    row = {
        **base,
        "Number of contacts in active cadences": r(5, 120),
        "Number Of Current Contacts": r(100, 1200),
        "Number of Marketing SEO / Content Contacts": r(5, 80),
        "Number of Marketing: Management / General Contacts": r(5, 60),
        "Number of Marketing: PPC / Display Contacts": r(5, 70),
        "Number of Marketing: PR / Comms / Social Media Contacts": r(3, 50),
        "Number of Marketing: Affiliate / Media Buying Contacts": r(1, 40),
        "Number of Sales / Business Development Contacts": r(10, 150),
        "Number of Account Management / Customer Success Contacts": r(5, 100),
        "Number of BI / Analytics Contacts": r(3, 80),
        "Number of eCommerce Contacts": r(3, 70),
        "Number of Investment Contacts": r(0, 25),
    }
    account_rows.append(row)

accounts_df = pd.DataFrame(account_rows)

# -------------------------
# Section 3: Intent-Driven List
# -------------------------
intent_rows = []
for i in range(10):
    base = accounts[i]
    intent_corr = round(random.uniform(0.35, 0.95), 2)
    trials_90d = random.randint(0, 20)
    hand_raises_90d = random.randint(0, 15)

    intent_rows.append({
        **base,
        "Intent-Hypothesis Correlation": intent_corr,
        "Contacts with Active trial last 90 days": trials_90d,
        "Contacts with Active hand raises last 90 days": hand_raises_90d,
    })

intent_df = pd.DataFrame(intent_rows)

# -------------------------
# UI: Tabs for the three sections
# -------------------------
tab1, tab2, tab3 = st.tabs([
    "Use-Case Led Prospecting",
    "Accounts-Led Prospecting",
    "Intent-Driven List",
])

with tab1:
    st.subheader("Section 1: Use-Case Led Prospecting")
    st.dataframe(use_case_df, use_container_width=True)

    # Row-level actions (placed below the table for Streamlit compatibility)
    st.markdown("**Row Actions** – quick controls for each hypothesis/cadence:")
    for idx, row in use_case_df.reset_index().iterrows():
        with st.container():
            c1, c2, c3, c4 = st.columns([4, 2.2, 2.6, 2.8])
            c1.write(f"**{row['Industry']} — {row['ICP (Personas)']}**")
            if c2.button("Modify This Cadence", key=f"mod_{idx}"):
                st.toast(f"Modify cadence triggered for row {idx+1} ({row['Industry']} / {row['ICP (Personas)']}).")
            if c3.button("Reveal More Contacts", key=f"rev_{idx}"):
                st.toast(f"Reveal contacts triggered for row {idx+1}.")
            if c4.button("Dis-qualify This Cadence", key=f"disq_{idx}"):
                st.toast(f"Dis-qualified cadence for row {idx+1}.")

    st.download_button(
        label="Download Use-Case Table (CSV)",
        data=use_case_df.to_csv(index=False).encode("utf-8"),
        file_name="use_case_led_prospecting.csv",
        mime="text/csv",
    )

with tab2:
    st.subheader("Section 2: Accounts-Led Prospecting")
    st.dataframe(accounts_df, use_container_width=True)
    st.download_button(
        label="Download Accounts Table (CSV)",
        data=accounts_df.to_csv(index=False).encode("utf-8"),
        file_name="accounts_led_prospecting.csv",
        mime="text/csv",
    )

with tab3:
    st.subheader("Section 3: Intent-Driven List")
    st.dataframe(intent_df, use_container_width=True)
    st.download_button(
        label="Download Intent List (CSV)",
        data=intent_df.to_csv(index=False).encode("utf-8"),
        file_name="intent_driven_list.csv",
        mime="text/csv",
    )

# -------------------------
# Sidebar Controls (optional basic filters)
# -------------------------
st.sidebar.header("Quick Filters")
selected_industry = st.sidebar.selectbox("Industry", ["All"] + industries)
selected_country = st.sidebar.selectbox("Country", ["All"] + countries)

# Copy dataframes for filtering in sidebar metrics
_uc_df = use_case_df.copy()
_ac_df = accounts_df.copy()
_in_df = intent_df.copy()

if selected_industry != "All":
    _uc_df = _uc_df[_uc_df["Industry"] == selected_industry]
    _ac_df = _ac_df[_ac_df["Industry"] == selected_industry]
    _in_df = _in_df[_in_df["Industry"] == selected_industry]

if selected_country != "All":
    _ac_df = _ac_df[_ac_df["Country"] == selected_country]
    _in_df = _in_df[_in_df["Country"] == selected_country]

# Show filtered counts in sidebar
st.sidebar.metric("Use-Case rows", len(_uc_df))
st.sidebar.metric("Accounts rows", len(_ac_df))
st.sidebar.metric("Intent rows", len(_in_df))
