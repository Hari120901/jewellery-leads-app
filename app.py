import streamlit as st
import requests
import pandas as pd
from io import BytesIO
import urllib.parse
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import asyncio
from playwright.async_api import async_playwright

st.set_page_config(page_title="Free Ad Intelligence System", layout="wide")
st.title("🚀 Free Automated Advertising Intelligence System")

location = st.text_input("📍 Location")
category = st.text_input("🏢 Category")
max_results = st.selectbox("Max Results", [10, 20, 30])

GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

# =============================
# GOOGLE BUSINESS SEARCH
# =============================

def get_places(query):
    encoded_query = urllib.parse.quote(query)
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={encoded_query}&key={GOOGLE_API_KEY}"
    response = requests.get(url).json()
    return response.get("results", [])[:max_results]

# =============================
# PIXEL DETECTION
# =============================

def check_pixels(website):
    if not website:
        return "No", "No"
    try:
        html = requests.get(website, timeout=5).text
        fb_pixel = "Yes" if "facebook.com/tr" in html else "No"
        google_pixel = "Yes" if "googletagmanager" in html or "gtag(" in html else "No"
        return fb_pixel, google_pixel
    except:
        return "Unknown", "Unknown"

# =============================
# GOOGLE ADS DETECTION
# =============================

def check_google_ads(name, location):
    query = f"{name} {location}"
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if "Sponsored" in response.text:
        return "Yes"
    return "No"

# =============================
# META ADS SCRAPER
# =============================

async def check_meta_ads(name):
    url = f"https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=IN&q={urllib.parse.quote(name)}"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)
        content = await page.content()
        await browser.close()

        if "Ad Library" in content:
            if "Active" in content:
                return "Yes"
        return "No"

# =============================
# MAIN PROCESS
# =============================

if st.button("Generate Leads"):

    query = f"{category} in {location}, India"
    businesses = get_places(query)

    results = []

    for biz in businesses:
        name = biz.get("name")
        address = biz.get("formatted_address")
        website = biz.get("website", None)

        fb_pixel, google_pixel = check_pixels(website)
        google_ads = check_google_ads(name, location)

        meta_ads = asyncio.run(check_meta_ads(name))

        activity_score = 0
        if fb_pixel == "Yes": activity_score += 1
        if google_pixel == "Yes": activity_score += 1
        if google_ads == "Yes": activity_score += 1
        if meta_ads == "Yes": activity_score += 1

        results.append([
            name,
            address,
            google_ads,
            meta_ads,
            fb_pixel,
            google_pixel,
            activity_score
        ])

    df = pd.DataFrame(results, columns=[
        "Business Name",
        "Address",
        "Google Ads Active",
        "Meta Ads Active",
        "Facebook Pixel",
        "Google Pixel",
        "Ad Activity Score (0-4)"
    ])

    st.success("Completed Analysis")
    st.dataframe(df)

    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)

    st.download_button(
        "Download Excel",
        data=output,
        file_name="free_ad_intelligence.xlsx"
    )
