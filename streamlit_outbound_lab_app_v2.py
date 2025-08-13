import streamlit as st
import pandas as pd
import random

# -------------------------
# Page Configuration
# -------------------------
st.set_page_config(page_title="Prospecting Workspace", layout="wide")
st.title("Prospecting Workspace")
st.caption("Three views: Use-Case Led, Accounts-Led, and Intent-Driven")

# Global style: wrap only table headers
st.markdown(
    """
    <style>
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
    "Retail", "FinTech", "Travel", "Gaming", "Telecom", "Media & Entertainment", "Healthcare", "B2B SaaS", "Marketplaces", "Consumer Electronics"
]

sub_industries = [
    "Fashion eCommerce", "Digital Banking", "Airlines", "Mobile Games", "ISPs", "Streaming", "Telemedicine", "Dev Tools", "Food Delivery", "Smart Home"
]

countries = ["US", "UK", "DE", "FR", "IL", "NL", "AU", "CA", "ES", "SE"]

personas = [
    "VP Marketing", "Director of Growth", "Head of SEO", "Head of Paid Media", "VP Sales", "Head of Product", "Head of BI/Analytics", "CMO", "Ecommerce Director", "Investor Relations Lead"
]

message_angles = [
    "Beat competitors with category benchmarks", "Reduce CAC via channel mix optimization", "Capture seasonal demand spikes", "Win RFPs with verified traffic intelligence", "Expand into new markets with TAM insights", "Defend market share against disruptors", "Identify upsell opportunities in key accounts", "Prioritize content by competitor gaps", "Optimize media spend with audience overlaps", "Signal-based outreach for warmer meetings"
]

triggers = [
    "Traffic spike", "Funding round", "New product launch", "Hiring surge", "PR coverage", "App rank change", "Market entry", "Budget season", "Quarterly earnings", "M&A rumor"
]

products = ["Web", "Shopper", "Investors", "Ads"]

department_types = [
    "Marketing", "Sales", "Growth", "Product", "Analytics", "eCommerce", "PR/Comms", "Investor Relations"
]

parent_domains = [
    "acmecorp.com", "globex.com", "initech.com", "umbrella.com", "starkindustries.com", "wayneenterprises.com", "wonkaindustries.com", "hooli.com", "massiveDynamic.com", "cyberdyne.com"
]

clean_domain = lambda d: d.lower().replace(" ", "")

accounts = [{
    "Industry": industries[i],
    "Sub-Industry": sub_industries[i],
    "Country": countries[i],
    "Account Name": parent_domains[i].split(".")[0].title(),
    "Parent Company Domain": clean_domain(parent_domains[i]),
    "Website": f"https://www.{clean_domain(parent_domains[i])}",
} for i in range(10)]

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
    hyp_type = random.choice(["Market-Led", "Accounts-Led"])

    user_story = f"As a {persona} in a {industry} company, I'd like to {angle.lower()}, because I need to act on {trigger.lower()} data."
    slides_url = f"https://slides.example.com/{clean_domain(accounts[i]['Parent Company Domain'])}/qbr"

    n_accounts = random.randint(3, 50)
    n_leads = random.randint(7, 200)
    engaged = max(1, int(n_leads * random.uniform(0.05, 0.80)))
    exhausted = max(0, int(engaged * random.uniform(0.05, 1.00)))
    meeting_rate = random.uniform(0.01, 0.10)
    n_opps = max(1, int(n_leads * meeting_rate * random.uniform(0.10, 0.40)))

    if n_accounts < 10:
        nba = "1-Reveal More Contacts"
    elif n_leads < 30:
        nba = "2-Bring more leads"
    elif engaged < 30:
        nba = "3-Wait for more engagement"
    elif (exhausted / n_leads) > 0.7 and n_opps < 2:
        nba = "4-Consider modify campaign"
    else:
        nba = ""

    use_case_rows.append({
        "Next Best Action": nba,
        "Hypothesis Type (Market-Led \ Accounts-Led)": hyp_type,
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

# 1) Next Best Action default + coloring (Section 1)
use_case_df.loc[use_case_df["Next Best Action"] == "", "Next Best Action"] = "5-Consider to disqualify cadence"

_color_map = {
    "1-Reveal More Contacts": "background-color: #fff3b0",  # yellow
    "2-Bring more leads": "background-color: #fff3b0",       # yellow
    "3-Wait for more engagement": "background-color: #d4edda", # green
    "4-Consider modify campaign": "background-color: #ffe0b2", # orange
    "5-Consider to disqualify cadence": "background-color: #ffe0b2", # orange
}

def color_nba(val: str):
    return _color_map.get(val, "")

styled_use_case = use_case_df.style.applymap(color_nba, subset=["Next Best Action"])  # pandas Styler

# -------------------------
# Section 2: Accounts-Led Prospecting
# -------------------------
account_rows = []
for i in range(10):
    base = accounts[i]
    def r(a, b): return random.randint(a, b)
    # Generate granular counts
    m_seo = r(5, 80)
    m_mgmt = r(5, 60)
    m_ppc = r(5, 70)
    m_pr = r(3, 50)
    m_aff = r(1, 40)
    s_biz = r(10, 150)
    cs = r(5, 100)
    bi = r(3, 80)
    ecommerce = r(3, 70)
    invest = r(0, 25)
    # Sum for Number Of Current Contacts (per spec)
    total_contacts = m_seo + m_mgmt + m_ppc + m_pr + m_aff + s_biz + cs + bi + ecommerce + invest
    # New metric: Number of active "Accounts-Led Cadences"
    active_cadences = r(1, 12)

    account_rows.append({
        "Industry": base["Industry"],
        "Sub-Industry": base["Sub-Industry"],
        "Country": base["Country"],
        "Account Name": base["Account Name"],
        "Parent Company Domain": base["Parent Company Domain"],
        "Website": base["Website"],
        "Number of active \"Accounts-Led Cadences\"": active_cadences,
        "Number Of Current Contacts": total_contacts,
        "Number of contacts in active cadences": r(5, 120),
        "Number of Marketing SEO / Content Contacts": m_seo,
        "Number of Marketing: Management / General Contacts": m_mgmt,
        "Number of Marketing: PPC / Display Contacts": m_ppc,
        "Number of Marketing: PR / Comms / Social Media Contacts": m_pr,
        "Number of Marketing: Affiliate / Media Buying Contacts": m_aff,
        "Number of Sales / Business Development Contacts": s_biz,
        "Number of Account Management / Customer Success Contacts": cs,
        "Number of BI / Analytics Contacts": bi,
        "Number of eCommerce Contacts": ecommerce,
        "Number of Investment Contacts": invest,
    })

accounts_df = pd.DataFrame(account_rows)

# Ensure exact column order per spec (Section 2)
accounts_cols_order = [
    "Industry",
    "Sub-Industry",
    "Country",
    "Account Name",
    "Parent Company Domain",
    "Website",
    "Number of active \"Accounts-Led Cadences\"",
    "Number Of Current Contacts",
    "Number of contacts in active cadences",
    "Number of Marketing SEO / Content Contacts",
    "Number of Marketing: Management / General Contacts",
    "Number of Marketing: PPC / Display Contacts",
    "Number of Marketing: PR / Comms / Social Media Contacts",
    "Number of Marketing: Affiliate / Media Buying Contacts",
    "Number of Sales / Business Development Contacts",
    "Number of Account Management / Customer Success Contacts",
    "Number of BI / Analytics Contacts",
    "Number of eCommerce Contacts",
    "Number of Investment Contacts",
]
accounts_df = accounts_df[accounts_cols_order]

# -------------------------
# Section 3: Intent-Driven List
# -------------------------
intent_rows = []
for i in range(10):
    base = accounts[i]
    trials_90d = random.randint(0, 20)
    hand_raises_90d = random.randint(0, 15)

    intent_rows.append({
        "Industry": base["Industry"],
        "Sub-Industry": base["Sub-Industry"],
        "Country": base["Country"],
        "Account Name": base["Account Name"],
        "Parent Company Domain": base["Parent Company Domain"],
        "Website": base["Website"],
        # Placeholder text; will populate below after we have use_case_df
        "Intent-Hypothesis Correlation": "",
        "Contacts with Active trial last 90 days": trials_90d,
        "Contacts with Active hand raises last 90 days": hand_raises_90d,
    })

intent_df = pd.DataFrame(intent_rows)

# Convert Intent-Hypothesis Correlation to randomized text referencing Tab 1 cadences
cadence_pool = list(use_case_df["Cadence"].unique()) if not use_case_df.empty else ["7-step multi-channel"]
intent_texts = []
for _ in range(len(intent_df)):
    roll = random.random()
    if roll < 0.35:
        intent_texts.append("")  # blank sometimes
    else:
        picked = random.choice(cadence_pool)
        intent_texts.append(f"According to our analysis, this domain has intent activity that might be correlated with one of your hypothesis {picked}")
intent_df["Intent-Hypothesis Correlation"] = intent_texts

# -------------------------
# UI: Tabs for the three sections
# -------------------------
tab1, tab2, tab3 = st.tabs(["Use-Case Led Prospecting", "Accounts-Led Prospecting", "Intent-Driven List"])

with tab1:
    st.subheader("Section 1: Use-Case Led Prospecting")
    # Show styled table (colors on Next Best Action). Streamlit supports pandas Styler in st.dataframe.
    st.dataframe(styled_use_case, use_container_width=True)

    # Row selection & collapsible details panel
    st.markdown("---")
    st.markdown("### Explore a row")
    # Provide a selection control to mimic row-click behavior
    options = [f"{i+1}: {r['Industry']} — {r['ICP (Personas)']}" for i, r in use_case_df.iterrows()]
    selected = st.selectbox("Pick a row to view details", ["None"] + options, index=0)
    if selected != "None":
        idx = int(selected.split(":", 1)[0]) - 1
        with st.expander("Selected Row Details", expanded=True):
            row = use_case_df.iloc[idx]
            cols_to_show = [
                "Next Best Action",
                "Hypothesis Type (Market-Led \ Accounts-Led)", "Industry", "ICP (Personas)", "Message Angle", "Trigger",
                "Product (Web, Shopper, Investors, Ads)",
                "Hypothesis User Story (As a XXX in XXX Company, i'd like to XXX, because I need XXX)",
                "Slides", "Specific Use Case Related Insights", "Cadence",
                "# of accounts", "# of leads in campaign", "# of engaged leads", "# of leads exausted",
                "Meeting Rate", "# of opportunities"
            ]
            details_df = pd.DataFrame({"Field": cols_to_show, "Value": [row[c] for c in cols_to_show]})
            st.dataframe(details_df, use_container_width=True, hide_index=True)

            c1, c2, c3 = st.columns([1.6, 1.8, 2.0])
            if c1.button("Modify This Cadence", key=f"mod_row_{idx}"):
                st.toast(f"Modify cadence triggered (row {idx+1}).")
            if c2.button("Reveal More Contacts", key=f"rev_row_{idx}"):
                st.toast(f"Reveal contacts triggered (row {idx+1}).")
            if c3.button("Dis-qualify This Cadence", key=f"disq_row_{idx}"):
                st.toast(f"Dis-qualified cadence (row {idx+1}).")

    st.download_button("Download Use-Case Table (CSV)", data=use_case_df.to_csv(index=False).encode("utf-8"), file_name="use_case_led_prospecting.csv", mime="text/csv")

with tab2:
    st.subheader("Section 2: Accounts-Led Prospecting")
    st.dataframe(accounts_df, use_container_width=True)

    # Two buttons under Section 2
    b1, b2 = st.columns([2, 3])
    if b1.button("Create Account Based Cadence"):
        st.toast("Creating an Account-Based Cadence… (stub)")
    if b2.button("Get list of all accounts based cadences with their accounts"):
        st.toast("Fetching list of account-based cadences… (stub)")

    st.download_button("Download Accounts Table (CSV)", data=accounts_df.to_csv(index=False).encode("utf-8"), file_name="accounts_led_prospecting.csv", mime="text/csv")

with tab3:
    st.subheader("Section 3: Intent-Driven List")
    st.dataframe(intent_df, use_container_width=True)
    st.download_button("Download Intent List (CSV)", data=intent_df.to_csv(index=False).encode("utf-8"), file_name="intent_driven_list.csv", mime="text/csv")

# -------------------------
# Sidebar Filters
# -------------------------
st.sidebar.header("Quick Filters")
selected_industry = st.sidebar.selectbox("Industry", ["All"] + industries)
selected_country = st.sidebar.selectbox("Country", ["All"] + countries)

_uc_df, _ac_df, _in_df = use_case_df.copy(), accounts_df.copy(), intent_df.copy()
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
