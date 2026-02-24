import streamlit as st
import requests
import pandas as pd
from io import BytesIO
import urllib.parse

st.set_page_config(page_title="Jewellery Leads Generator", layout="wide")
st.title("💎 Jewellery Leads Generator")

# Inputs
location = st.text_input("Enter Location (e.g., Kondapur, Hyderabad, Telangana)")
category = st.text_input("Enter Category (e.g., jewellery store)")

# Get API key from Streamlit secrets
api_key = st.secrets["GOOGLE_API_KEY"]

if st.button("Search & Download Excel"):
    if not location or not category:
        st.warning("Please enter both Location and Category.")
        st.stop()

    # Combine category + location for text search
    query = f"{category} {location}"
    encoded_query = urllib.parse.quote(query)
    places_url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={encoded_query}&key={api_key}"

    response = requests.get(places_url).json()

    if response.get("status") != "OK" or not response.get("results"):
        st.error("❌ No results found. Please check the input or try a different location.")
        st.stop()

    data = []

    for place in response.get("results", []):
        name = place.get("name")
        address = place.get("formatted_address")
        place_id = place.get("place_id")

        # Get details for phone, website, rating
        details_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=formatted_phone_number,website,rating&key={api_key}"
        details = requests.get(details_url).json().get("result", {})

        phone = details.get("formatted_phone_number", "N/A")
        website = details.get("website", "N/A")
        rating = details.get("rating", "N/A")

        data.append([name, category, address, rating, phone, website])

    # Create Excel
    df = pd.DataFrame(data, columns=["Store Name", "Category", "Address", "Rating", "Phone", "Website"])
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)

    st.success(f"✅ Found {len(df)} stores!")

    st.download_button(
        label="📥 Download Excel",
        data=output,
        file_name=f"{location.replace(',', '').replace(' ', '_')}_leads.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
