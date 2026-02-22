import streamlit as st
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from num2words import num2words
from datetime import datetime
import tempfile

st.set_page_config(page_title="HS SHIVANIA GROUP", layout="wide")

# ---------------- HEADER ----------------
st.markdown(
    """
    <h1 style='text-align:center; color:#1f4e79;'>HS SHIVANIA GROUP</h1>
    <hr>
    """,
    unsafe_allow_html=True
)

# ---------------- SIDEBAR ----------------
st.sidebar.header("📄 Document Details")

doc_type = st.sidebar.selectbox("Document Type", ["Quotation", "Bill"])
doc_no = st.sidebar.text_input("Quotation/Bill Number")
date = st.sidebar.date_input("Date", datetime.today())

st.sidebar.markdown("---")

customer_name = st.sidebar.text_input("Customer Name")
customer_address = st.sidebar.text_area("Customer Address")
subject = st.sidebar.text_input("Subject")

st.sidebar.markdown("---")
signature = st.sidebar.file_uploader("Upload Signature")
stamp = st.sidebar.file_uploader("Upload Stamp")

# ---------------- ITEM SECTION ----------------
st.subheader("🧾 Item Details")

if "item_df" not in st.session_state:
    st.session_state["item_df"] = pd.DataFrame({
        "Description": [""],
        "Qty": [1],
        "Unit Price": [0.0],
        "GST %": [18]
    })

edited_df = st.data_editor(
    st.session_state["item_df"],
    num_rows="dynamic",
    use_container_width=True
)

if not edited_df.empty:

    edited_df["Amount"] = (
        edited_df["Qty"] * edited_df["Unit Price"]
        + (edited_df["Qty"] * edited_df["Unit Price"] * edited_df["GST %"] / 100)
    )

    st.session_state["item_df"] = edited_df

    # -------- TOTAL PANEL --------
    grand_total = edited_df["Amount"].sum()
    rounded_total = round(grand_total)

    col1, col2 = st.columns([2, 1])

    with col2:
        st.markdown("### 💰 Summary")
        st.success(f"Grand Total: ₹ {grand_total:.2f}")
        st.info(f"Rounded Total: ₹ {rounded_total:.2f}")
        st.write(
            num2words(rounded_total, lang="en_IN").title() + " Rupees Only"
        )

# ---------------- PDF GENERATION ----------------
st.markdown("---")
generate = st.button("📥 Generate Professional PDF")

if generate:

    if edited_df.empty or edited_df["Description"].eq("").all():
        st.error("Please add valid item details.")
    else:

        pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

        def add_background(canvas_obj, doc):
            width, height = A4
            canvas_obj.drawImage("letterhead.png", 0, 0, width=width, height=height)

        doc = SimpleDocTemplate(pdf_file.name, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()

        elements.append(Spacer(1, 150))

        # Title
        elements.append(Paragraph(
            f"<para align=center><b>{doc_type}</b></para>",
            styles["Title"]
        ))
        elements.append(Spacer(1, 20))

        # Right side date & number
        elements.append(Paragraph(
            f"<para align=right>Date: {date}<br/>{doc_type} No: {doc_no}</para>",
            styles["Normal"]
        ))
        elements.append(Spacer(1, 20))

        # Customer
        elements.append(Paragraph(
            f"<b>QUOTATION TO,</b><br/>{customer_name}<br/>{customer_address}",
            styles["Normal"]
        ))
        elements.append(Spacer(1, 10))

        elements.append(Paragraph(
            f"<b>SUB - {subject}</b>",
            styles["Normal"]
        ))
        elements.append(Spacer(1, 20))

        # Table
        table_data = [["S.NO", "DESCRIPTION", "QTY", "UNIT PRICE", "GST %", "AMOUNT"]]

        for i, row in edited_df.iterrows():
            table_data.append([
                i + 1,
                row["Description"],
                row["Qty"],
                f"{row['Unit Price']:.2f}",
                row["GST %"],
                f"{row['Amount']:.2f}"
            ])

        table = Table(table_data, colWidths=[40, 220, 50, 80, 50, 80])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("ALIGN", (2, 1), (-1, -1), "CENTER"),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 20))

        elements.append(Paragraph(
            f"<para align=right><b>Grand Total: {grand_total:.2f}<br/>Rounded Total: {rounded_total:.2f}</b></para>",
            styles["Normal"]
        ))
        elements.append(Spacer(1, 10))

        elements.append(Paragraph(
            num2words(rounded_total, lang="en_IN").title() + " Rupees Only",
            styles["Normal"]
        ))

        elements.append(Spacer(1, 40))

        elements.append(Paragraph(
            "<para align=right>For HS SHIVANIA GROUP</para>",
            styles["Normal"]
        ))

        if signature:
            sig_path = tempfile.NamedTemporaryFile(delete=False).name
            with open(sig_path, "wb") as f:
                f.write(signature.getbuffer())
            elements.append(Image(sig_path, width=120, height=50))

        if stamp:
            stamp_path = tempfile.NamedTemporaryFile(delete=False).name
            with open(stamp_path, "wb") as f:
                f.write(stamp.getbuffer())
            elements.append(Image(stamp_path, width=120, height=120))

        elements.append(Paragraph(
            "<para align=right>Authorised Signatory</para>",
            styles["Normal"]
        ))

        doc.build(elements, onFirstPage=add_background)

        with open(pdf_file.name, "rb") as f:
            st.download_button(
                "⬇ Download PDF",
                f,
                file_name=f"{doc_type}_{doc_no}.pdf"
            )