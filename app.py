import streamlit as st
import requests
import pandas as pd
from io import BytesIO
import urllib.parse
import re

st.set_page_config(page_title="Business Lead Generator", layout="wide")
st.title("📈 Business Lead Generator with Email Extraction")

# =============================
# USER INPUT
# =============================

location = st.text_input("📍 Location (e.g., Andheri West, Mumbai)")
category = st.text_input("🏢 Category (e.g., jewellery store)")
max_results = st.selectbox("Max Results", [30, 40, 50])

GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

headers = {"User-Agent": "Mozilla/5.0"}

# =============================
# GOOGLE PLACES SEARCH
# =============================

def get_places(query):
    encoded_query = urllib.parse.quote(query)
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={encoded_query}&key={GOOGLE_API_KEY}"
    response = requests.get(url).json()
    return response.get("results", [])[:max_results]

# =============================
# GET PLACE DETAILS
# =============================

def get_details(place_id):
    details_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=formatted_phone_number,website&key={GOOGLE_API_KEY}"
    details = requests.get(details_url).json().get("result", {})

    phone = details.get("formatted_phone_number", "N/A")
    website = details.get("website", None)

    return phone, website

# =============================
# EMAIL EXTRACTION
# =============================

def extract_email(website):
    if not website:
        return "N/A"

    try:
        response = requests.get(website, headers=headers, timeout=5)
        html = response.text

        # Regex for email
        emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", html)

        if emails:
            return emails[0]
        else:
            return "Not Found"

    except:
        return "Error"

# =============================
# MAIN PROCESS
# =============================

if st.button("Generate Leads"):

    if not location or not category:
        st.warning("Please enter both Location and Category")
        st.stop()

    query = f"{category} in {location}, India"

    with st.spinner("Searching businesses..."):
        businesses = get_places(query)

    results = []

    for biz in businesses:

        name = biz.get("name")
        address = biz.get("formatted_address")
        place_id = biz.get("place_id")

        phone, website = get_details(place_id)
        email = extract_email(website)

        results.append([
            name,
            address,
            phone,
            website if website else "N/A",
            email
        ])

    df = pd.DataFrame(results, columns=[
        "Business Name",
        "Address",
        "Phone",
        "Website",
        "Email"
    ])

    st.success("Lead Generation Complete")
    st.dataframe(df)

    output = BytesIO()
    df.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)

    st.download_button(
        "Download Excel",
        data=output,
        file_name="business_leads_with_email.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
