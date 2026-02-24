import streamlit as st
import requests
import pandas as pd
from io import BytesIO
import urllib.parse

st.set_page_config(page_title="Jewellery Leads Generator", layout="wide")
st.title("💎 Jewellery Leads Generator")

# Inputs
location = st.text_input("Enter Location (e.g., Kondapur, Hyderabad, Telangana, India)")
category = st.text_input("Enter Category (e.g., jewellery store)")

# Get API key from Streamlit secrets
api_key = st.secrets["GOOGLE_API_KEY"]

if st.button("Search & Download Excel"):
    if not location or not category:
        st.warning("Please enter both Location and Category.")
        st.stop()

    # Encode location for URL
    encoded_location = urllib.parse.quote(location.strip())
    geo_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_location}&key={api_key}"
    geo_response = requests.get(geo_url).json()

    # Check if Google returned results
    if geo_response.get("status") != "OK" or not geo_response.get("results"):
        st.error("❌ Location not found. Please check spelling or try a different location.")
        st.stop()

    # Get latitude & longitude
    coords = geo_response["results"][0]["geometry"]["location"]
    lat = coords["lat"]
    lng = coords["lng"]

    st.info(f"Fetching stores near **{location}** in category **{category}**...")

    # Google Places Nearby Search
    places_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=5000&keyword={urllib.parse.quote(category)}&key={api_key}"
    places_response = requests.get(places_url).json()

    if not places_response.get("results"):
        st.warning("No places found for this category in this location.")
        st.stop()

    data = []

    # Loop through places
    for place in places_response.get("results", []):
        name = place.get("name")
        address = place.get("vicinity")
        place_id = place.get("place_id")

        # Get details (phone, website, rating)
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
