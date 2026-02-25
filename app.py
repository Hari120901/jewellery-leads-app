import streamlit as st
import requests
import pandas as pd
from io import BytesIO
import urllib.parse
from bs4 import BeautifulSoup
from datetime import datetime

st.set_page_config(page_title="Free Ad Intelligence System", layout="wide")
st.title("🚀 Free Automated Advertising Intelligence System")

# =============================
# USER INPUT
# =============================

location = st.text_input("📍 Location (e.g., Andheri West, Mumbai)")
category = st.text_input("🏢 Category (e.g., jewellery store)")
max_results = st.selectbox("Max Results", [30, 40, 50])

GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

headers = {"User-Agent": "Mozilla/5.0"}

# =============================
# GOOGLE BUSINESS SEARCH
# =============================

def get_places(query):
    encoded_query = urllib.parse.quote(query)
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={encoded_query}&key={GOOGLE_API_KEY}"
    response = requests.get(url).json()
    return response.get("results", [])[:max_results]

# =============================
# GET WEBSITE FROM PLACE DETAILS
# =============================

def get_website(place_id):
    details_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=website&key={GOOGLE_API_KEY}"
    details = requests.get(details_url).json().get("result", {})
    return details.get("website")

# =============================
# PIXEL DETECTION
# =============================

def check_pixels(website):
    if not website:
        return "No", "No"
    try:
        html = requests.get(website, headers=headers, timeout=5).text
        fb_pixel = "Yes" if "facebook.com/tr" in html else "No"
        google_pixel = "Yes" if "googletagmanager" in html or "gtag(" in html else "No"
        return fb_pixel, google_pixel
    except:
        return "Unknown", "Unknown"

# =============================
# GOOGLE ADS DETECTION
# =============================

def check_google_ads(name, location):
    try:
        query = f"{name} {location}"
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        response = requests.get(url, headers=headers, timeout=5).text

        # crude but works
        if "Sponsored" in response or "Ad ·" in response:
            return "Yes"
        return "No"
    except:
        return "Unknown"

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

        website = get_website(place_id)
        fb_pixel, google_pixel = check_pixels(website)
        google_ads = check_google_ads(name, location)

        # Activity Score
        score = 0
        if fb_pixel == "Yes": score += 1
        if google_pixel == "Yes": score += 1
        if google_ads == "Yes": score += 1

        if score == 0:
            status = "Not Advertising"
        elif score == 1:
            status = "Low Activity"
        elif score == 2:
            status = "Medium Activity"
        else:
            status = "High Activity"

        results.append([
            name,
            address,
            website if website else "N/A",
            google_ads,
            fb_pixel,
            google_pixel,
            score,
            status
        ])

    df = pd.DataFrame(results, columns=[
        "Business Name",
        "Address",
        "Website",
        "Google Ads Detected",
        "Facebook Pixel Installed",
        "Google Tag Installed",
        "Ad Activity Score (0-3)",
        "Ad Activity Level"
    ])

    st.success("Analysis Complete")
    st.dataframe(df)

    output = BytesIO()
    df.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)

    st.download_button(
        "Download Excel",
        data=output,
        file_name="free_ad_intelligence.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
