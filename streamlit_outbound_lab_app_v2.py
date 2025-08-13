import os
from datetime import datetime
from typing import Optional

import pandas as pd
import streamlit as st
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, scoped_session

# -----------------------------
# Basic Setup
# -----------------------------
st.set_page_config(page_title="Outbound Hypothesis Lab", layout="wide")

DB_PATH = st.secrets["db_path"] if "db_path" in st.secrets else "outbound_lab.db"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()

# -----------------------------
# Data Model
# -----------------------------
class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    hypothesis_type = Column(String(255))
    industry = Column(String(255))
    icp_personas = Column(String(255))
    message_angle = Column(String(255))
    trigger = Column(String(255))
    product = Column(String(255))
    hypothesis_user_story = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    cadence = relationship("Cadence", back_populates="campaign", uselist=False, cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="campaign", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    name = Column(String(255), nullable=False)
    file_path = Column(String(1024), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    campaign = relationship("Campaign", back_populates="documents")


class Cadence(Base):
    __tablename__ = "cadences"

    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    campaign = relationship("Campaign", back_populates="cadence")
    contacts = relationship("Contact", back_populates="cadence", cascade="all, delete-orphan")
    cadence_activities = relationship("CadenceActivity", back_populates="cadence", cascade="all, delete-orphan")


class CadenceActivity(Base):
    __tablename__ = "cadence_activities"

    id = Column(Integer, primary_key=True)
    cadence_id = Column(Integer, ForeignKey("cadences.id"), nullable=False)
    type = Column(String(64))  # email | call | linkedin | task
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    cadence = relationship("Cadence", back_populates="cadence_activities")


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    industry = Column(String(255))
    website = Column(String(255))

    contacts = relationship("Contact", back_populates="account", cascade="all, delete-orphan")
    signals = relationship("AccountSignal", back_populates="account", cascade="all, delete-orphan")


class AccountSignal(Base):
    __tablename__ = "account_signals"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    signal_type = Column(String(255), nullable=False)
    details = Column(Text)
    date = Column(DateTime, default=datetime.utcnow)

    account = relationship("Account", back_populates="signals")


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True)
    cadence_id = Column(Integer, ForeignKey("cadences.id"), nullable=False)
    first_name = Column(String(255))
    last_name = Column(String(255))
    email = Column(String(255), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    title = Column(String(255))
    status = Column(String(64), default="new")  # new | active | paused | converted

    cadence = relationship("Cadence", back_populates="contacts")
    activities = relationship("Activity", back_populates="contact", cascade="all, delete-orphan")
    opportunities = relationship("Opportunity", back_populates="contact", cascade="all, delete-orphan")
    account = relationship("Account", back_populates="contacts")

    __table_args__ = (
        UniqueConstraint("email", "cadence_id", name="uq_contact_email_per_cadence"),
    )


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    type = Column(String(64))  # email | call | linkedin | task
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    contact = relationship("Contact", back_populates="activities")


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    stage = Column(String(64), default="New")
    amount = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    contact = relationship("Contact", back_populates="opportunities")


# -----------------------------
# DB Init
# -----------------------------
Base.metadata.create_all(bind=engine)


def get_session():
    return SessionLocal()


# -----------------------------
# Utilities
# -----------------------------
@st.cache_data(show_spinner=False)
def list_campaign_options():
    with get_session() as db:
        rows = db.query(Campaign).order_by(Campaign.created_at.desc()).all()
        return [(c.name, c.id) for c in rows]


def save_uploaded_file(upload, prefix: str = "doc") -> Optional[str]:
    try:
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S-%f")
        safe_name = f"{prefix}-{timestamp}-{upload.name}"
        path = os.path.join(UPLOAD_DIR, safe_name)
        with open(path, "wb") as f:
            f.write(upload.getbuffer())
        return path
    except Exception as e:
        st.error(f"Failed to save file: {e}")
        return None


# -----------------------------
# Common bits
# -----------------------------

def _classify_department(title: Optional[str]) -> Optional[str]:
    if not title:
        return None
    t = title.lower()
    if "seo" in t:
        return "Mrktg: SEO"
    if any(k in t for k in ["vp", "head", "director", "manager"]):
        return "Mrktg: Management"
    if "marketing" in t:
        return "Mrktg: General"
    return None


# -----------------------------
# Overview (All-campaign summary + per-campaign details)
# -----------------------------

def section_overview():
    st.header("Campaign Overview")

    with get_session() as db:
        all_campaigns = db.query(Campaign).order_by(Campaign.created_at.desc()).all()

    if not all_campaigns:
        st.info("No campaigns yet. Create one in the Campaigns page.")
        return

    # Build one big summary table covering all campaigns
    all_rows = []
    for camp in all_campaigns:
        with get_session() as db:
            cadence = db.query(Cadence).filter_by(campaign_id=camp.id).first()
            docs = db.query(Document).filter_by(campaign_id=camp.id).all()
            contacts = db.query(Contact).filter_by(cadence_id=cadence.id).all() if cadence else []
            contact_ids = [c.id for c in contacts]
            account_ids = [c.account_id for c in contacts if c.account_id]
            signals = db.query(AccountSignal).filter(AccountSignal.account_id.in_(account_ids)).all() if account_ids else []
            opps = db.query(Opportunity).filter(Opportunity.contact_id.in_(contact_ids)).all() if contact_ids else []
            acts = db.query(Activity).filter(Activity.contact_id.in_(contact_ids)).all() if contact_ids else []

        pptx_count = sum(1 for d in docs if d.file_path.lower().endswith(".pptx"))
        has_pptx = "v" if pptx_count > 0 else ""
        has_cadence = "v" if cadence else ""

        dept_labels = []
        dept_counts = {"Mrktg: SEO": 0, "Mrktg: Management": 0}
        for c in contacts:
            dep = _classify_department(c.title)
            if dep:
                if dep not in dept_labels:
                    dept_labels.append(dep)
                if dep in dept_counts:
                    dept_counts[dep] += 1

        engaged_leads = len({a.contact_id for a in acts}) if acts else 0
        exhausted_leads = len([c for c in contacts if c.status == "paused"]) if contacts else 0
        reply_rate = 0
        meeting_rate = 0

        rows = [
            {"Campaign": camp.name, "Object": "Campaign", "Field": "Hypothesis Type", "Example": camp.hypothesis_type or "—"},
            {"Campaign": camp.name, "Object": "Campaign", "Field": "Industry", "Example": camp.industry or "—"},
            {"Campaign": camp.name, "Object": "Campaign", "Field": "ICP (Personas)", "Example": camp.icp_personas or "—"},
            {"Campaign": camp.name, "Object": "Campaign", "Field": "Message Angle", "Example": camp.message_angle or "—"},
            {"Campaign": camp.name, "Object": "Campaign", "Field": "Trigger", "Example": camp.trigger or "—"},
            {"Campaign": camp.name, "Object": "Campaign", "Field": "Product", "Example": camp.product or "—"},
            {"Campaign": camp.name, "Object": "Campaign", "Field": "Hypothesis User Story", "Example": camp.hypothesis_user_story or "—"},
            {"Campaign": camp.name, "Object": "Documents", "Field": "PPTX", "Example": has_pptx},
            {"Campaign": camp.name, "Object": "Cadence", "Field": "Cadence", "Example": has_cadence},
            {"Campaign": camp.name, "Object": "Accounts", "Field": "# of accounts", "Example": str(len(set(account_ids)))},
            {"Campaign": camp.name, "Object": "Leads", "Field": "# of leads in campaign", "Example": str(len(contacts))},
            {"Campaign": camp.name, "Object": "Leads", "Field": "Departments Types", "Example": " | ".join(dept_labels) if dept_labels else "—"},
            {"Campaign": camp.name, "Object": "Leads", "Field": "Number of leads from Mrktg\\SEO", "Example": str(dept_counts.get("Mrktg: SEO", 0))},
            {"Campaign": camp.name, "Object": "Leads", "Field": "Number of leads from Mrktg\\Management", "Example": str(dept_counts.get("Mrktg: Management", 0))},
            {"Campaign": camp.name, "Object": "Activities", "Field": "# of engaged leads", "Example": str(engaged_leads)},
            {"Campaign": camp.name, "Object": "Activities", "Field": "# of leads exausted", "Example": str(exhausted_leads)},
            {"Campaign": camp.name, "Object": "Activities", "Field": "Reply Rate", "Example": str(reply_rate)},
            {"Campaign": camp.name, "Object": "Activities", "Field": "Meeting Rate", "Example": str(meeting_rate)},
            {"Campaign": camp.name, "Object": "Signals", "Field": "# of signals", "Example": str(len(signals))},
            {"Campaign": camp.name, "Object": "Opportunities", "Field": "# of opportunities", "Example": str(len(opps))},
        ]
        all_rows.extend(rows)

    df = pd.DataFrame(all_rows)
    st.markdown("### Summary Table (All Campaigns)")
    st.dataframe(df, use_container_width=True)

    # Details filter: pick a campaign to show detailed sections
    names = [c.name for c in all_campaigns]
    sel_name = st.selectbox("Filter details by campaign", names)
    with get_session() as db:
        campaign = db.query(Campaign).filter_by(name=sel_name).first()
        cadence = db.query(Cadence).filter_by(campaign_id=campaign.id).first()
        docs = db.query(Document).filter_by(campaign_id=campaign.id).all()
        contacts = db.query(Contact).filter_by(cadence_id=cadence.id).all() if cadence else []
        contact_ids = [c.id for c in contacts]
        opps = db.query(Opportunity).filter(Opportunity.contact_id.in_(contact_ids)).all() if contact_ids else []

    st.divider()
    st.subheader("Details")

    with st.container(border=True):
        st.markdown("#### Campaign")
        meta_cols = st.columns(4)
        meta_cols[0].metric("Hypothesis Type", campaign.hypothesis_type or "—")
        meta_cols[1].metric("Industry", campaign.industry or "—")
        meta_cols[2].metric("ICP (Personas)", campaign.icp_personas or "—")
        meta_cols[3].metric("Product", campaign.product or "—")
        st.write("**Message Angle:** ", campaign.message_angle or "—")
        st.write("**Trigger:** ", campaign.trigger or "—")
        st.write("**Hypothesis User Story:**")
        st.code(campaign.hypothesis_user_story or "—")

    with st.container(border=True):
        st.markdown("#### Cadence")
        if cadence:
            st.success(f"Cadence: **{cadence.name}**")
            st.caption(cadence.description or "")
        else:
            st.info("No cadence yet for this campaign.")

    with st.container(border=True):
        st.markdown("#### Activities")
        with get_session() as db:
            acts = db.query(Activity).filter(Activity.contact_id.in_(contact_ids)).all() if contact_ids else []
        engaged = len({a.contact_id for a in acts}) if acts else 0
        st.metric("Engaged Leads", engaged)
        st.metric("Total Activities", len(acts))

    with st.container(border=True):
        st.markdown("#### Leads")
        if contacts:
            ct_df = pd.DataFrame([
                {
                    "id": c.id,
                    "name": f"{c.first_name or ''} {c.last_name or ''}".strip(),
                    "email": c.email,
                    "title": c.title,
                    "status": c.status,
                    "account": (c.account.name if c.account else None),
                    "opportunities": len(c.opportunities),
                }
                for c in contacts
            ])
            st.dataframe(ct_df, use_container_width=True)
        else:
            st.info("No leads (contacts) yet.")

    with st.container(border=True):
        st.markdown("#### Documents")
        if docs:
            for doc in docs:
                c1, c2, c3 = st.columns([4, 3, 2])
                c1.write(f"📄 **{doc.name}**")
                c2.write(doc.uploaded_at.strftime("%Y-%m-%d %H:%M"))
                if os.path.exists(doc.file_path):
                    c3.download_button("Download", data=open(doc.file_path, "rb").read(), file_name=os.path.basename(doc.file_path), key=f"dl_{doc.id}")
                else:
                    c3.write("File missing")
        else:
            st.info("No documents yet.")

    with st.container(border=True):
        st.markdown("#### Opportunities")
        if opps:
            opp_rows = []
            for o in opps:
                contact = o.contact
                account = contact.account.name if contact and contact.account else None
                cadence_name = contact.cadence.name if contact and contact.cadence else None
                opp_rows.append(
                    {
                        "id": o.id,
                        "stage": o.stage,
                        "amount": o.amount,
                        "created": o.created_at.strftime("%Y-%m-%d %H:%M"),
                        "contact": f"{contact.first_name or ''} {contact.last_name or ''}".strip() if contact else None,
                        "email": contact.email if contact else None,
                        "account": account,
                        "cadence": cadence_name,
                    }
                )
            st.dataframe(pd.DataFrame(opp_rows), use_container_width=True)
        else:
            st.info("No opportunities yet.")


# -----------------------------
# Campaigns (existing create/manage)
# -----------------------------

def section_campaigns():
    st.header("Campaigns")

    with st.expander("➕ Add Campaign", expanded=True):
        with st.form("add_campaign_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Campaign Name *")
                hypothesis_type = st.text_input("Hypothesis Type")
                industry = st.text_input("Industry")
                icp_personas = st.text_input("ICP (Personas)")
                product = st.text_input("Product")
            with col2:
                message_angle = st.text_input("Message Angle")
                trigger = st.text_input("Trigger")
                hypothesis_user_story = st.text_area("Hypothesis User Story")
            submitted = st.form_submit_button("Create Campaign")
        if submitted:
            if not name:
                st.warning("Please provide a Campaign Name.")
            else:
                with get_session() as db:
                    if db.query(Campaign).filter_by(name=name).first():
                        st.error("A campaign with this name already exists.")
                    else:
                        c = Campaign(
                            name=name.strip(),
                            hypothesis_type=hypothesis_type.strip() if hypothesis_type else None,
                            industry=industry.strip() if industry else None,
                            icp_personas=icp_personas.strip() if icp_personas else None,
                            message_angle=message_angle.strip() if message_angle else None,
                            trigger=trigger.strip() if trigger else None,
                            product=product.strip() if product else None,
                            hypothesis_user_story=hypothesis_user_story.strip() if hypothesis_user_story else None,
                        )
                        db.add(c)
                        db.commit()
                        st.success(f"Campaign '{c.name}' created.")
                        list_campaign_options.clear()


# -----------------------------
# Cadences (create cadence + cadence activities)
# -----------------------------

def section_cadences():
    st.header("Cadences")

    options = list_campaign_options()
    if not options:
        st.info("Create a campaign first.")
        return
    labels = [o[0] for o in options]
    ids = {o[0]: o[1] for o in options}
    sel_label = st.selectbox("Select campaign", labels, key="cad_sel_campaign")
    sel_id = ids[sel_label]

    with get_session() as db:
        cadence = db.query(Cadence).filter_by(campaign_id=sel_id).first()

    if not cadence:
        st.warning("No cadence for this campaign.")
        with st.form("create_cadence_form2", clear_on_submit=True):
            name = st.text_input("Cadence Name *")
            desc = st.text_area("Description")
            submitted = st.form_submit_button("Create Cadence")
        if submitted:
            with get_session() as db:
                cad = Cadence(campaign_id=sel_id, name=name.strip(), description=desc.strip() if desc else None)
                db.add(cad)
                db.commit()
                st.success("Cadence created")
            st.experimental_rerun()
        return

    st.success(f"Cadence: **{cadence.name}**")
    st.caption(cadence.description or "")

    st.divider()
    st.subheader("Cadence Activities (templates)")
    with get_session() as db:
        cad_acts = db.query(CadenceActivity).filter_by(cadence_id=cadence.id).order_by(CadenceActivity.created_at.asc()).all()

    if cad_acts:
        st.dataframe(pd.DataFrame([
            {"id": a.id, "type": a.type, "content": a.content, "created": a.created_at.strftime('%Y-%m-%d %H:%M')}
            for a in cad_acts
        ]), use_container_width=True)
    else:
        st.info("No cadence activities yet.")

    with st.form("add_cad_act", clear_on_submit=True):
        act_type = st.selectbox("Type", ["email", "call", "linkedin", "task"], index=0)
        content = st.text_area("Content *")
        submitted = st.form_submit_button("Add Activity to Cadence & Apply to Leads")
    if submitted:
        with get_session() as db:
            ca = CadenceActivity(cadence_id=cadence.id, type=act_type, content=content.strip())
            db.add(ca)
            db.flush()
            leads = db.query(Contact).filter_by(cadence_id=cadence.id).all()
            for lead in leads:
                db.add(Activity(contact_id=lead.id, type=act_type, content=content.strip()))
            db.commit()
        st.success("Cadence activity created and applied to all leads.")


# -----------------------------
# Leads (upload leads to cadence; auto-attach cadence activities)
# -----------------------------

def section_leads():
    st.header("Leads")

    options = list_campaign_options()
    if not options:
        st.info("Create a campaign first.")
        return
    labels = [o[0] for o in options]
    ids = {o[0]: o[1] for o in options}
    sel_label = st.selectbox("Select campaign", labels, key="leads_sel_campaign")
    sel_id = ids[sel_label]

    with get_session() as db:
        cadence = db.query(Cadence).filter_by(campaign_id=sel_id).first()
    if not cadence:
        st.warning("No cadence for this campaign. Create one in the Cadences page.")
        return

    st.success(f"Cadence: **{cadence.name}**")

    with get_session() as db:
        cad_acts = db.query(CadenceActivity).filter_by(cadence_id=cadence.id).all()

    st.subheader("Upload Leads (CSV)")
    st.caption("Required: email. Optional: first_name, last_name, title, account_name, account_industry, account_website")
    csv = st.file_uploader("Contacts CSV", type=["csv"], key=f"csv_leads_{cadence.id}")
    if csv is not None:
        df = pd.read_csv(csv)
        st.dataframe(df.head(20))
        if st.button("Ingest Leads & Apply Cadence Activities", key=f"ingest_leads_{cadence.id}", type="primary"):
            ingested = 0
            with get_session() as db:
                for _, row in df.iterrows():
                    email = str(row.get("email", "")).strip()
                    if not email:
                        continue
                    account_id = None
                    acct_name = str(row.get("account_name", "")).strip()
                    if acct_name:
                        acct = db.query(Account).filter_by(name=acct_name).first()
                        if not acct:
                            acct = Account(
                                name=acct_name,
                                industry=str(row.get("account_industry", "")) or None,
                                website=str(row.get("account_website", "")) or None,
                            )
                            db.add(acct)
                            db.flush()
                        account_id = acct.id

                    existing = db.query(Contact).filter_by(cadence_id=cadence.id, email=email).first()
                    if existing:
                        existing.first_name = str(row.get("first_name", existing.first_name or "")) or existing.first_name
                        existing.last_name = str(row.get("last_name", existing.last_name or "")) or existing.last_name
                        existing.title = str(row.get("title", existing.title or "")) or existing.title
                        if account_id:
                            existing.account_id = account_id
                        contact_id = existing.id
                    else:
                        c = Contact(
                            cadence_id=cadence.id,
                            email=email,
                            first_name=str(row.get("first_name", "")) or None,
                            last_name=str(row.get("last_name", "")) or None,
                            title=str(row.get("title", "")) or None,
                            account_id=account_id,
                        )
                        db.add(c)
                        db.flush()
                        contact_id = c.id
                    for ca in cad_acts:
                        db.add(Activity(contact_id=contact_id, type=ca.type, content=ca.content))
                    ingested += 1
                db.commit()
            st.success(f"Ingested/updated {ingested} leads and applied cadence activities.")

    st.divider()
    st.subheader("Leads in Cadence")
    with get_session() as db:
        contacts = db.query(Contact).filter_by(cadence_id=cadence.id).order_by(Contact.id.desc()).all()
    if contacts:
        st.dataframe(pd.DataFrame([
            {
                "id": c.id,
                "name": f"{c.first_name or ''} {c.last_name or ''}".strip(),
                "email": c.email,
                "title": c.title,
                "status": c.status,
                "account": (c.account.name if c.account else None),
                "activities": len(c.activities),
                "opportunities": len(c.opportunities),
            }
            for c in contacts
        ]), use_container_width=True)
    else:
        st.info("No leads in this cadence yet.")


# -----------------------------
# Opportunities (read-only list)
# -----------------------------

def section_opportunities():
    st.header("Opportunities")
    with get_session() as db:
        opps = db.query(Opportunity).order_by(Opportunity.created_at.desc()).all()
    if not opps:
        st.info("No opportunities yet.")
        return

    rows = []
    for o in opps:
        contact = o.contact
        account = contact.account.name if contact and contact.account else None
        cadence = contact.cadence.name if contact and contact.cadence else None
        campaign = contact.cadence.campaign.name if contact and contact.cadence and contact.cadence.campaign else None
        rows.append(
            {
                "id": o.id,
                "stage": o.stage,
                "amount": o.amount,
                "created": o.created_at.strftime("%Y-%m-%d %H:%M"),
                "contact": f"{contact.first_name or ''} {contact.last_name or ''}".strip() if contact else None,
                "email": contact.email if contact else None,
                "account": account,
                "cadence": cadence,
                "campaign": campaign,
            }
        )

    st.dataframe(pd.DataFrame(rows), use_container_width=True)


# -----------------------------
# App Nav
# -----------------------------
PAGES = {
    "Overview": section_overview,
    "Campaigns": section_campaigns,
    "Cadences": section_cadences,
    "Leads": section_leads,
    "Opportunities": section_opportunities,
}

with st.sidebar:
    st.title("Outbound Hypothesis Lab")
    st.caption("Test more campaigns, faster.")
    page = st.radio("Navigation", list(PAGES.keys()), index=0)
    st.divider()
    st.write("**Quick Tips**")
    st.markdown("• Overview shows ALL campaigns; pick a campaign below the table to filter details.")
    st.markdown("• Cadences: add a cadence and cadence activities (templates). Added activities are auto-applied to all leads.")
    st.markdown("• Leads: upload leads to a cadence. Newly added leads inherit all cadence activities.")

# Render selected page
PAGES[page]()
