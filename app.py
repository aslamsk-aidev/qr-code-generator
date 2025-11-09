import streamlit as st
import qrcode
from PIL import Image
import pandas as pd
import os, io, zipfile

st.set_page_config(page_title="UR QR Generator", page_icon="🔳", layout="centered")

st.title("🔳 UR QR Generator (Single & Bulk)")
st.markdown("Easily create QR codes for single links or entire Excel files with custom colors and logos!")

# === Sidebar settings ===
st.sidebar.header("⚙️ Settings")
fg_color = st.sidebar.color_picker("Foreground Color", "#000000")
bg_color = st.sidebar.color_picker("Background Color", "#ffffff")
logo_file = st.sidebar.file_uploader("Optional Logo", type=["png", "jpg", "jpeg"])
mode = st.sidebar.radio("Choose Mode", ["Single URL", "Bulk Upload"])

# === QR Code function ===
def make_qr(url, fg, bg, logo=None):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color=fg, back_color=bg).convert("RGB")

    if logo:
        logo = Image.open(logo)
        w = int(img.size[0] * 0.2)
        logo.thumbnail((w, w))
        pos = ((img.size[0]-logo.size[0])//2, (img.size[1]-logo.size[1])//2)
        img.paste(logo, pos, mask=logo if logo.mode=="RGBA" else None)
    return img

# === Mode 1: Single URL ===
if mode == "Single URL":
    url = st.text_input("Enter URL")
    if st.button("Generate QR Code"):
        if not url.strip():
            st.warning("Please enter a URL.")
        else:
            img = make_qr(url, fg_color, bg_color, logo_file)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            st.image(buf, caption="Generated QR Code", use_column_width=True)
            st.download_button("⬇️ Download QR", data=buf.getvalue(), file_name="qr_code.png", mime="image/png")

# === Mode 2: Bulk Upload ===
else:
    uploaded = st.file_uploader("Upload Excel File (.xlsx)", type=["xlsx"])
    if uploaded:
        df = pd.read_excel(uploaded)
        required_cols = {"Name", "URL", "Category"}
        if not required_cols.issubset(df.columns):
            st.error(f"Excel file must contain columns: {', '.join(required_cols)}")
        else:
            if st.button("Generate All QR Codes"):
                os.makedirs("QR_Codes", exist_ok=True)
                for _, row in df.iterrows():
                    url, name, cat = row["URL"], str(row["Name"]).replace(" ", "_"), str(row["Category"]).replace(" ", "_")
                    folder = f"QR_Codes/{cat}"
                    os.makedirs(folder, exist_ok=True)
                    img = make_qr(url, fg_color, bg_color, logo_file)
                    img.save(f"{folder}/{name}.png")

                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for root, _, files in os.walk("QR_Codes"):
                        for f in files:
                            path = os.path.join(root, f)
                            zipf.write(path, arcname=os.path.relpath(path, "QR_Codes"))
                zip_buffer.seek(0)
                st.success("✅ All QR Codes Generated!")
                st.download_button("⬇️ Download ZIP", data=zip_buffer, file_name="QR_Codes.zip", mime="application/zip")
