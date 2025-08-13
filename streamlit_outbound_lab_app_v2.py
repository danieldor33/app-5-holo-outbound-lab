import streamlit as st
import pandas as pd
import random

# -------------------------
# Page Configuration
# -------------------------
st.set_page_config(page_title="Prospecting Workspace", layout="wide")
st.title("Prospecting Workspace")
st.caption("Three views: Use-Case Led, Accounts-Led, and Intent-Driven")

# Global style: wrap table headers across ALL tables + simple link-button styling
st.markdown(
    """
    <style>
    /* Header wrapping for st.dataframe and st.table */
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
    /* Action link button style (used in Section 1 table) */
    .action-link { 
        padding: 6px 10px; 
        border-radius: 8px; 
        border: 1px solid rgba(0,0,0,.12); 
        background: rgba(0,0,0,.04); 
        text-decoration: none; 
        font-size: 0.9rem;
        display: inline-block;
    }
    .action-link:hover { background: rgba(0,0,0,.08); }
    .action-link.danger { border-color: rgba(220,0,0,.25); }
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
    "Retail","FinTech","Travel","Gaming","Telecom",
    "Media & Entertainment","Healthcare","B2B SaaS","Marketplaces","Consumer Electronics",
]
sub_industries = [
    "Fashion eCommerce","Digital Banking","Airlines","Mobile Games","ISPs",
    "Streaming","Telemedicine","Dev Tools","Food Delivery","Smart Home",
]
countries = ["US","UK","DE","FR","IL","NL","AU","CA","ES","SE"]
personas = [
    "VP Marketing","Director of Growth","Head of SEO","Head of Paid Media","VP Sales",
    "Head of Product","Head of BI/Analytics","CMO","Ecommerce Director","Investor Relations Lead",
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
    "Traffic spike","Funding round","New product launch","Hiring surge","PR coverage",
    "App rank change","Market entry","Budget season","Quarterly earnings","M&A rumor",
]
products = ["Web","Shopper","Investors","Ads"]
department_types = [
    "Marketing","Sales","Growth","Product","Analytics","eCommerce","PR/Comms","Investor Relations",
]
parent_domains = [
    "acmecorp.com","globex.com","initech.com","umbrella.com","starkindustries.com",
    "wayneenterprises.com","wonkaindustries.com","hooli.com","massiveDynamic.com","cyberdyne.com",
]

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
    hyp_type = random.choice(["Market-Led","Accounts-Led"])

    user_story = (
        f"As a {persona} in a {industry} company, I'd like to {angle.lower()}, "
        f"because I need to act on {trigger.lower()} data."
    )
    slides_url = f"https://slides.example.com/{clean_domain(accounts[i]['Parent Company Domain'])}/qbr"

    # Requested constraints
    n_accounts = random.randint(3, 50)
    n_leads = random.randint(7, 200)
    engaged = max(1, int(n_leads * random.uniform(0.05, 0.80)))
    exhausted = max(0, int(engaged * random.uniform(0.05, 1.00)))
    meeting_rate = random.uniform(0.01, 0.10)  # 1%-10%
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
        "Cadence": random.choice(["3-touch warm-up","7-step multi-channel","5-step email-first","Phone-first 4-step"]),
        "# of accounts": n_accounts,
        "# of leads in campaign": n_leads,
        "Departments Types": ", ".join(random.sample(department_types, k=random.randint(3, 5))),
        "# of engaged leads": engaged,
        "# of leads exausted": exhausted,
        "Meeting Rate": f"{round(meeting_rate*100, 1)}%",
        "# of opportunities": n_opps,
    })

use_case_df = pd.DataFrame(use_case_rows)

# Next Best Action (priority: a -> b -> c -> d)
def compute_next_best_action(row: pd.Series) -> str:
    if row["# of accounts"] < 10:
        return "1-Reveal More Contacts"
    if row["# of leads in campaign"] < 30:
        return "2-Bring more leads"
    if row["# of engaged leads"] < 30:
        return "3-Wait for more engagement"
    leads = max(1, row["# of leads in campaign"])
    exhausted_ratio = row["# of leads exausted"] / leads
    if exhausted_ratio > 0.70 and row["# of opportunities"] < 2:
        return "4-Consider modify campaign"
    return "—"

use_case_df["next best action"] = use_case_df.apply(compute_next_best_action, axis=1)

# In-table action links (3 link-like buttons as requested)
uc_df_for_table = use_case_df.copy()
uc_df_for_table.insert(0, "Modify This Cadence", "")
uc_df_for_table.insert(1, "Reveal More Contacts", "")
uc_df_for_table.insert(2, "Dis-qualify This Cadence", "")

for idx in uc_df_for_table.index:
    uc_df_for_table.at[idx, "Modify This Cadence"] = f'<a class="action-link" href="?action=modify&row={idx}">Modify This Cadence</a>'
    uc_df_for_table.at[idx, "Reveal More Contacts"] = f'<a class="action-link" href="?action=reveal&row={idx}">Reveal More Contacts</a>'
    uc_df_for_table.at[idx, "Dis-qualify This Cadence"] = f'<a class="action-link danger" href="?action=disqualify&row={idx}">Dis-qualify This Cadence</a>'

# -------------------------
# Section 2: Accounts-Led Prospecting
# -------------------------
account_rows = []
for i in range(10):
    base = accounts[i]
    def r(a, b): return random.randint(a, b)
    account_rows.append({
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
    })
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
# Handle action query params (Section 1 link clicks)
# -------------------------
qp = st.query_params
action = qp.get("action", None)
row_str = qp.get("row", None)
if action and row_str is not None:
    try:
        r = int(row_str)
        if 0 <= r < len(use_case_df):
            label = use_case_df.loc[r, "Industry"] + " / " + use_case_df.loc[r, "ICP (Personas)"]
            if action == "modify":
                st.toast(f"Modify cadence triggered for row {r+1} ({label})")
            elif action == "reveal":
                st.toast(f"Reveal contacts triggered for row {r+1} ({label})")
            elif action == "disqualify":
                st.toast(f"Dis-qualified cadence for row {r+1} ({label})")
    except Exception:
        pass

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
    st.markdown(uc_df_for_table.to_html(escape=False, index=False), unsafe_allow_html=True)
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

st.sidebar.metric("Use-Case rows", len(_uc_df))
st.sidebar.metric("Accounts rows", len(_ac_df))
st.sidebar.metric("Intent rows", len(_in_df))
