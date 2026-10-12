"""Multimodel Receipt Tracker — scan, review, and understand expenses."""

from __future__ import annotations

import os
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from PIL import Image, ImageOps

from parser import CATEGORIES, ReceiptParseError, parse_receipt
from storage import add_receipt, delete_receipt, load_receipts

load_dotenv()
st.set_page_config(page_title="Receipt Tracker", page_icon="🧾", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root { --ink:#17221d; --muted:#718078; --green:#256b50; --mint:#eaf3ed; --line:#e8eee9; }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
h1,h2,h3 { font-family:'Manrope',sans-serif; color:var(--ink); letter-spacing:-.035em; }
.block-container { padding-top:2rem; max-width:1440px; }
.hero { padding:1.5rem 1.8rem; border:1px solid var(--line); border-radius:18px; background:linear-gradient(120deg,#f4f8f4,#fff 70%); margin-bottom:1.3rem; }
.hero-kicker { color:var(--green); font-size:.72rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase; }
.hero p { color:var(--muted); margin-bottom:0; }
div[data-testid="stMetric"] { background:white; border:1px solid var(--line); border-radius:14px; padding:1rem 1.1rem; }
div[data-testid="stMetricLabel"] { color:var(--muted); }
div[data-testid="stMetricValue"] { font-family:'Manrope',sans-serif; color:var(--ink); }
div.stButton > button[kind="primary"] { background:#256b50; border-color:#256b50; }
div.stButton > button { border-radius:10px; }
section[data-testid="stSidebar"] { border-right:1px solid var(--line); }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><div class="hero-kicker">PERSONAL FINANCE · MULTIMODAL AI</div><h1 style="margin:.35rem 0">Receipt Tracker</h1><p>Turn paper receipts into clear, searchable spending insights.</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🧾 Receipt Tracker")
    st.caption("Your receipts stay in a local JSON file.")
    st.divider()
    page = st.radio("Workspace", ["Scan receipt", "Dashboard", "History"], label_visibility="collapsed")
    st.divider()
    if os.getenv("GEMINI_API_KEY"):
        st.success("Gemini API key connected", icon="🔑")
    else:
        st.warning("Add GEMINI_API_KEY to .env to scan receipts.", icon="🔑")
    st.caption("AI results can be imperfect. Review extracted values before saving.")

records = load_receipts()

if page == "Scan receipt":
    left, right = st.columns([1, 1], gap="large")
    with left:
        st.subheader("Upload a receipt")
        uploaded = st.file_uploader("Choose an image", type=["png", "jpg", "jpeg", "webp"], help="Use a clear, well-lit image. Supported formats: PNG, JPG, WEBP.")
        if uploaded:
            try:
                image = ImageOps.exif_transpose(Image.open(uploaded))
                st.image(image, caption=uploaded.name, use_container_width=True)
                if st.button("✨ Scan with Gemini", type="primary", use_container_width=True):
                    with st.spinner("Reading merchant, items, and totals…"):
                        st.session_state["draft_receipt"] = parse_receipt(image)
                    st.rerun()
            except (OSError, Image.DecompressionBombError):
                st.error("This image could not be opened. Choose a valid image file.")
            except ReceiptParseError as exc:
                st.error(str(exc))
    with right:
        st.subheader("Review and save")
        draft = st.session_state.get("draft_receipt")
        if draft:
            with st.form("receipt_form"):
                merchant = st.text_input("Merchant", draft["merchant"])
                purchase_date = st.date_input("Date", value=date.fromisoformat(draft["date"]))
                total = st.number_input("Total", min_value=0.0, value=float(draft["total"]), step=0.01, format="%.2f")
                currency = st.text_input("Currency", draft.get("currency", ""), max_chars=8)
                category = st.selectbox("Category", CATEGORIES, index=CATEGORIES.index(draft["category"]))
                notes = st.text_input("Notes", draft.get("notes", ""))
                items = draft.get("items", [])
                st.caption("Extracted line items · edit cells or add rows as needed")
                edited_items = st.data_editor(
                    pd.DataFrame(items, columns=["name", "quantity", "unit_price", "total"]),
                    num_rows="dynamic", hide_index=True, use_container_width=True, key="receipt_items_editor",
                )
                save = st.form_submit_button("Save receipt", type="primary", use_container_width=True)
                if save:
                    if not merchant.strip():
                        st.error("Merchant is required.")
                    else:
                        add_receipt({"merchant": merchant.strip(), "date": purchase_date.isoformat(), "total": total,
                                     "currency": currency.strip().upper(), "category": category, "notes": notes.strip(),
                                     "items": edited_items.fillna("").to_dict(orient="records")})
                        del st.session_state["draft_receipt"]
                        st.success("Receipt saved.")
                        st.rerun()
        else:
            st.info("Upload a receipt and scan it to review the extracted details here.")

elif page == "Dashboard":
    st.subheader("Spending overview")
    if not records:
        st.info("No receipts yet. Scan your first receipt to see your spending dashboard.")
    else:
        df = pd.DataFrame(records)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["total"] = pd.to_numeric(df["total"], errors="coerce").fillna(0)
        valid = df.dropna(subset=["date"])
        currency_codes = [c for c in df.get("currency", pd.Series(dtype=str)).dropna().unique() if c]
        if len(currency_codes) > 1:
            st.caption("Receipts use multiple currencies; totals are shown as entered and are not converted.")
        currency_label = currency_codes[0] + " " if len(currency_codes) == 1 else ""
        col1, col2, col3 = st.columns(3)
        col1.metric("Total tracked", f"{currency_label}{df.total.sum():,.2f}")
        col2.metric("Receipts", f"{len(df):,}")
        col3.metric("Average receipt", f"{currency_label}{df.total.mean():,.2f}")
        c1, c2 = st.columns(2, gap="large")
        with c1:
            st.markdown("#### Spending by category")
            cats = df.groupby("category", as_index=False).total.sum().sort_values("total", ascending=False)
            fig = px.pie(cats, names="category", values="total", hole=.62, color_discrete_sequence=px.colors.qualitative.Safe)
            fig.update_layout(margin=dict(t=10,b=10,l=10,r=10), legend_title_text="", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown("#### Monthly spending")
            if valid.empty:
                st.info("No dated receipts available yet.")
            else:
                valid = valid.copy()
                valid["month"] = valid.date.dt.to_period("M").astype(str)
                months = valid.groupby("month", as_index=False).total.sum()
                fig = px.bar(months, x="month", y="total", labels={"month":"Month", "total":f"Total ({currency_label.strip() or 'amount'})"}, color_discrete_sequence=["#34775b"])
                fig.update_layout(margin=dict(t=10,b=10,l=10,r=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_title=None, yaxis_title=None)
                st.plotly_chart(fig, use_container_width=True)

else:
    st.subheader("Receipt history")
    if not records:
        st.info("No saved receipts yet.")
    else:
        search_col, filter_col = st.columns([2, 1])
        query = search_col.text_input("Search merchant or item", placeholder="e.g. coffee, market…")
        category_filter = filter_col.selectbox("Category", ["All categories", *CATEGORIES])
        filtered = records
        if category_filter != "All categories":
            filtered = [r for r in filtered if r.get("category") == category_filter]
        if query:
            q = query.casefold()
            filtered = [r for r in filtered if q in str(r.get("merchant", "")).casefold() or any(q in str(i.get("name", "")).casefold() for i in r.get("items", []))]
        st.caption(f"Showing {len(filtered)} of {len(records)} receipts")
        for receipt in filtered:
            label = f"{receipt.get('merchant','Unknown merchant')} · {receipt.get('date','')} · {receipt.get('currency','')} {float(receipt.get('total',0)):,.2f}"
            with st.expander(label):
                a, b = st.columns([3, 1])
                a.write(f"**Category:** {receipt.get('category','Other')}")
                if receipt.get("notes"):
                    a.write(f"**Notes:** {receipt['notes']}")
                if receipt.get("items"):
                    a.dataframe(pd.DataFrame(receipt["items"]), hide_index=True, use_container_width=True)
                if b.button("Delete", key=f"delete_{receipt.get('id')}"):
                    delete_receipt(str(receipt.get("id")))
                    st.rerun()
