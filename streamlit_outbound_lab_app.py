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

    def __repr__(self):
        return f"<Campaign {self.id}:{self.name}>"


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
# UI Sections
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

    st.subheader("Manage Campaign")
    options = list_campaign_options()
    if not options:
        st.info("No campaigns yet. Create one above.")
        return

    labels = [o[0] for o in options]
    ids = {o[0]: o[1] for o in options}
    sel_label = st.selectbox("Select a campaign", labels)
    sel_id = ids[sel_label]

    with get_session() as db:
        campaign = db.query(Campaign).get(sel_id)

    st.markdown(f"### {campaign.name}")
    meta_cols = st.columns(4)
    meta_cols[0].metric("Hypothesis Type", campaign.hypothesis_type or "—")
    meta_cols[1].metric("Industry", campaign.industry or "—")
    meta_cols[2].metric("ICP (Personas)", campaign.icp_personas or "—")
    meta_cols[3].metric("Product", campaign.product or "—")

    st.write("**Message Angle:** ", campaign.message_angle or "—")
    st.write("**Trigger:** ", campaign.trigger or "—")
    st.write("**Hypothesis User Story:**")
    st.code(campaign.hypothesis_user_story or "—")

    st.divider()

    # Documents
    st.subheader("Documents")
    with st.expander("Upload Document"):
        up_name = st.text_input("Document Name *", key="doc_name")
        upload = st.file_uploader("Attach file", type=None, key="doc_file")
        if st.button("Save Document", type="primary"):
            if not up_name or not upload:
                st.warning("Please provide a document name and file.")
            else:
                path = save_uploaded_file(upload, prefix=f"campaign-{campaign.id}")
                if path:
                    with get_session() as db:
                        d = Document(campaign_id=campaign.id, name=up_name.strip(), file_path=path)
                        db.add(d)
                        db.commit()
                        st.success("Document uploaded.")

    with get_session() as db:
        docs = db.query(Document).filter_by(campaign_id=campaign.id).order_by(Document.uploaded_at.desc()).all()
    if docs:
        for doc in docs:
            c1, c2, c3 = st.columns([4, 3, 2])
            c1.write(f"📄 **{doc.name}**")
            c2.write(doc.uploaded_at.strftime("%Y-%m-%d %H:%M"))
            if os.path.exists(doc.file_path):
                c3.download_button("Download", data=open(doc.file_path, "rb").read(), file_name=os.path.basename(doc.file_path))
            else:
                c3.write("File missing")
    else:
        st.info("No documents yet.")

    st.divider()

    # Cadence (1:1 with Campaign)
    st.subheader("Cadence")
    with get_session() as db:
        cadence = db.query(Cadence).filter_by(campaign_id=campaign.id).first()

    if cadence:
        st.success(f"Cadence: **{cadence.name}**")
        st.caption(cadence.description or "")
    else:
        if st.button("➕ Add New Cadence", type="primary"):
            with st.form("create_cadence_form", clear_on_submit=True):
                name = st.text_input("Cadence Name *")
                desc = st.text_area("Description")
                submitted = st.form_submit_button("Create Cadence")
            if submitted:
                if not name:
                    st.warning("Please enter a cadence name.")
                else:
                    with get_session() as db:
                        cad = Cadence(campaign_id=campaign.id, name=name.strip(), description=desc.strip() if desc else None)
                        db.add(cad)
                        db.commit()
                        st.success("Cadence created.")

    # Reload cadence if newly created
    with get_session() as db:
        cadence = db.query(Cadence).filter_by(campaign_id=campaign.id).first()

    if cadence:
        st.divider()
        st.subheader("Contacts")

        # Upload contacts to cadence
        with st.expander("Upload Contacts (CSV)", expanded=False):
            st.caption("Minimum required columns: email. Optional: first_name, last_name, title, account_name, account_industry, account_website")
            csv = st.file_uploader("Contacts CSV", type=["csv"], key=f"csv_{cadence.id}")
            if csv is not None:
                df = pd.read_csv(csv)
                st.dataframe(df.head(20))
                if st.button("Ingest Contacts", key=f"ingest_{cadence.id}", type="primary"):
                    ingested = 0
                    with get_session() as db:
                        for _, row in df.iterrows():
                            email = str(row.get("email", "")).strip()
                            if not email:
                                continue
                            # Account handling (optional)
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

                            # Contact upsert (unique per cadence + email)
                            existing = db.query(Contact).filter_by(cadence_id=cadence.id, email=email).first()
                            if existing:
                                # Update lightweight fields
                                existing.first_name = str(row.get("first_name", existing.first_name or "")) or existing.first_name
                                existing.last_name = str(row.get("last_name", existing.last_name or "")) or existing.last_name
                                existing.title = str(row.get("title", existing.title or "")) or existing.title
                                if account_id:
                                    existing.account_id = account_id
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
                            ingested += 1
                        db.commit()
                    st.success(f"Ingested/updated {ingested} rows.")

        # Contacts table & actions
        with get_session() as db:
            contacts = (
                db.query(Contact)
                .filter_by(cadence_id=cadence.id)
                .order_by(Contact.id.desc())
                .all()
            )
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

            st.markdown("#### Convert Contact to Opportunity")
            contact_map = {f"{c.email} | {c.first_name or ''} {c.last_name or ''}".strip(): c.id for c in contacts}
            sel = st.selectbox("Choose a contact", list(contact_map.keys()))
            amount = st.number_input("Amount", min_value=0.0, value=0.0, step=100.0)
            stage = st.selectbox("Stage", ["New", "Qualified", "Proposal", "Won", "Lost"], index=0)
            if st.button("Convert to Opportunity", type="primary"):
                with get_session() as db:
                    c = db.query(Contact).get(contact_map[sel])
                    opp = Opportunity(contact_id=c.id, stage=stage, amount=amount)
                    c.status = "converted"
                    db.add(opp)
                    db.commit()
                st.success("Opportunity created.")
        else:
            st.info("No contacts yet. Upload via CSV above.")


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


def section_accounts():
    st.header("Accounts & Signals")
    with st.expander("Add Account"):
        with st.form("add_account", clear_on_submit=True):
            name = st.text_input("Account Name *")
            industry = st.text_input("Industry")
            website = st.text_input("Website")
            submitted = st.form_submit_button("Create Account")
        if submitted:
            if not name:
                st.warning("Account name required")
            else:
                with get_session() as db:
                    if db.query(Account).filter_by(name=name).first():
                        st.error("Account already exists")
                    else:
                        db.add(Account(name=name.strip(), industry=industry or None, website=website or None))
                        db.commit()
                        st.success("Account created")

    with get_session() as db:
        accounts = db.query(Account).order_by(Account.name.asc()).all()

    if not accounts:
        st.info("No accounts yet.")
        return

    acct_map = {a.name: a.id for a in accounts}
    sel = st.selectbox("Select account", list(acct_map.keys()))
    acct_id = acct_map[sel]

    with get_session() as db:
        acct = db.query(Account).get(acct_id)

    st.subheader(sel)
    st.caption(f"Industry: {acct.industry or '—'} | Website: {acct.website or '—'}")

    st.markdown("#### Signals")
    with st.form("add_signal", clear_on_submit=True):
        sig_type = st.text_input("Signal Type *", placeholder="Hiring, Funding, Tech change…")
        details = st.text_area("Details")
        submitted = st.form_submit_button("Add Signal")
    if submitted:
        if not sig_type:
            st.warning("Signal type required")
        else:
            with get_session() as db:
                db.add(AccountSignal(account_id=acct.id, signal_type=sig_type.strip(), details=details or None))
                db.commit()
                st.success("Signal added")

    with get_session() as db:
        signals = db.query(AccountSignal).filter_by(account_id=acct.id).order_by(AccountSignal.date.desc()).all()
    if signals:
        st.dataframe(
            pd.DataFrame([
                {"type": s.signal_type, "details": s.details, "date": s.date.strftime('%Y-%m-%d %H:%M')} for s in signals
            ]),
            use_container_width=True,
        )
    else:
        st.info("No signals yet.")


# -----------------------------
# Overview (Summary Table + Drilldown)
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


def section_overview():
    st.header("Campaign Overview")

    options = list_campaign_options()
    if not options:
        st.info("No campaigns yet. Create one in the Campaigns page.")
        return

    labels = [o[0] for o in options]
    ids = {o[0]: o[1] for o in options}
    sel_label = st.selectbox("Select a campaign", labels, key="ov_sel_campaign")
    sel_id = ids[sel_label]

    with get_session() as db:
        campaign = db.query(Campaign).get(sel_id)
        cadence = db.query(Cadence).filter_by(campaign_id=campaign.id).first()
        docs = db.query(Document).filter_by(campaign_id=campaign.id).all()

        contacts = []
        if cadence:
            contacts = db.query(Contact).filter_by(cadence_id=cadence.id).all()
        contact_ids = [c.id for c in contacts]

        # Accounts & Signals
        account_ids = [c.account_id for c in contacts if c.account_id]
        accounts = []
        signals = []
        if account_ids:
            accounts = db.query(Account).filter(Account.id.in_(account_ids)).all()
            signals = db.query(AccountSignal).filter(AccountSignal.account_id.in_(account_ids)).all()

        # Opportunities & Activities
        opps = []
        acts = []
        if contact_ids:
            opps = db.query(Opportunity).filter(Opportunity.contact_id.in_(contact_ids)).all()
            acts = db.query(Activity).filter(Activity.contact_id.in_(contact_ids)).all()

    # Derived metrics
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

    reply_rate = 0  # Placeholder until a reply signal is defined in Activity schema
    meeting_rate = 0  # Placeholder until meetings are tracked explicitly

    summary_rows = [
        {"Object": "Campaign", "Field": "Hypothesis Type", "Example": campaign.hypothesis_type or "—"},
        {"Object": "Campaign", "Field": "Industry", "Example": campaign.industry or "—"},
        {"Object": "Campaign", "Field": "ICP (Personas)", "Example": campaign.icp_personas or "—"},
        {"Object": "Campaign", "Field": "Message Angle", "Example": campaign.message_angle or "—"},
        {"Object": "Campaign", "Field": "Trigger", "Example": campaign.trigger or "—"},
        {"Object": "Campaign", "Field": "Product", "Example": campaign.product or "—"},
        {"Object": "Campaign", "Field": "Hypothesis User Story", "Example": campaign.hypothesis_user_story or "—"},
        {"Object": "Documents", "Field": "PPTX", "Example": has_pptx},
        {"Object": "Cadence", "Field": "Cadence", "Example": has_cadence},
        {"Object": "Accounts", "Field": "# of accounts", "Example": str(len(set(account_ids)))},
        {"Object": "Leads", "Field": "# of leads in campaign", "Example": str(len(contacts))},
        {"Object": "Leads", "Field": "Departments Types", "Example": " | ".join(dept_labels) if dept_labels else "—"},
        {"Object": "Leads", "Field": "Number of leads from Mrktg\SEO", "Example": str(dept_counts.get("Mrktg: SEO", 0))},
        {"Object": "Leads", "Field": "Number of leads from Mrktg\Management", "Example": str(dept_counts.get("Mrktg: Management", 0))},
        {"Object": "Activities", "Field": "# of engaged leads", "Example": str(engaged_leads)},
        {"Object": "Activities", "Field": "# of leads exausted", "Example": str(exhausted_leads)},
        {"Object": "Activities", "Field": "Reply Rate", "Example": str(reply_rate)},
        {"Object": "Activities", "Field": "Meeting Rate", "Example": str(meeting_rate)},
        {"Object": "Signals", "Field": "# of signals", "Example": str(len(signals))},
        {"Object": "Opportunities", "Field": "# of opportunities", "Example": str(len(opps))},
    ]

    df = pd.DataFrame(summary_rows)

    st.markdown("### Summary Table")
    st.dataframe(df, use_container_width=True)

    # Row picker
    st.markdown("#### Pick a line to drill down")
    row_labels = [f"{r['Object']} | {r['Field']}" for r in summary_rows]
    picked = st.selectbox("Line", row_labels, key="summary_pick")

    st.divider()
    st.subheader("Details")

    # Sections: Campaign, Cadence, Activities, Leads, Documents, Opportunities
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
        st.metric("Engaged Leads", engaged_leads)
        st.metric("Leads Exhausted", exhausted_leads)
        st.metric("Reply Rate", reply_rate)
        st.metric("Meeting Rate", meeting_rate)

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
# App Nav
# -----------------------------
PAGES = {
    "Overview": section_overview,
    "Campaigns": section_campaigns,
    "Opportunities": section_opportunities,
    "Accounts": section_accounts,
}

with st.sidebar:
    st.title("Outbound Hypothesis Lab")
    st.caption("Test more campaigns, faster.")
    page = st.radio("Navigation", list(PAGES.keys()), index=0)
    st.divider()
    st.write("**Quick Tips**")
    st.markdown("1. Start with Overview → pick a line to drill down.")
    st.markdown("2. Or create a Campaign, add a Cadence, upload Contacts, then convert to Opportunities.")
    st.markdown("3. CSV headers: `email, first_name, last_name, title, account_name, account_industry, account_website`.")

# Render selected page
PAGES[page]()
