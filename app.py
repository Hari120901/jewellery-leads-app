import streamlit as st
import requests
import pandas as pd
from io import BytesIO
import urllib.parse
import time

st.set_page_config(page_title="Business Leads Generator India", layout="wide")
st.title("🇮🇳 Universal Business Leads Generator")

st.markdown("Generate business leads for **any category** in **any area of India**.")

# User Inputs
location = st.text_input("📍 Enter Location (e.g., Andheri West, Mumbai, Maharashtra)")
category = st.text_input("🏢 Enter Business Category (e.g., jewellery store, automobile dealer, real estate agency, FMCG distributor)")

max_results = st.selectbox("🔢 Maximum Results", [20, 40, 60])

# Get API Key from Streamlit Secrets
api_key = st.secrets["GOOGLE_API_KEY"]

def get_places(query, api_key, max_results):
    all_results = []
    next_page_token = None

    while len(all_results) < max_results:
        if next_page_token:
            url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?pagetoken={next_page_token}&key={api_key}"
            time.sleep(2)  # Required delay for next_page_token
        else:
            encoded_query = urllib.parse.quote(query)
            url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={encoded_query}&key={api_key}"

        response = requests.get(url).json()

        if response.get("status") != "OK":
            break

        all_results.extend(response.get("results", []))
        next_page_token = response.get("next_page_token")

        if not next_page_token:
            break

    return all_results[:max_results]

if st.button("🔍 Search & Download Excel"):
    if not location or not category:
        st.warning("Please enter both Location and Category.")
        st.stop()

    query = f"{category} in {location}, India"

    with st.spinner("Fetching data from Google Maps..."):
        places = get_places(query, api_key, max_results)

    if not places:
        st.error("❌ No results found. Try different keywords.")
        st.stop()

    data = []

    for place in places:
        name = place.get("name")
        address = place.get("formatted_address")
        place_id = place.get("place_id")

        # Fetch detailed info
        details_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=formatted_phone_number,website,rating,user_ratings_total&key={api_key}"
        details = requests.get(details_url).json().get("result", {})

        phone = details.get("formatted_phone_number", "N/A")
        website = details.get("website", "N/A")
        rating = details.get("rating", "N/A")
        total_reviews = details.get("user_ratings_total", "N/A")

        data.append([
            name,
            category,
            location,
            address,
            rating,
            total_reviews,
            phone,
            website
        ])

    df = pd.DataFrame(
        data,
        columns=[
            "Business Name",
            "Category",
            "Location",
            "Address",
            "Rating",
            "Total Reviews",
            "Phone",
            "Website"
        ]
    )

    output = BytesIO()
    df.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)

    st.success(f"✅ Found {len(df)} businesses!")

    st.download_button(
        label="📥 Download Excel",
        data=output,
        file_name=f"{category}_{location}_leads.xlsx".replace(" ", "_"),
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
