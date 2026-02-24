import streamlit as st
import requests
import pandas as pd
from io import BytesIO

st.title("💎 Jewellery Leads Generator")

location = st.text_input("Enter Location")
category = st.text_input("Enter Category (e.g. jewellery store)")

api_key = st.secrets["GOOGLE_API_KEY"]

if st.button("Search & Download Excel"):
    if location and category:
        # Step 1: Get coordinates safely
        geo_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={api_key}"
        geo_response = requests.get(geo_url).json()

        if geo_response.get('status') != "OK" or not geo_response.get('results'):
            st.error("❌ Location not found. Please check spelling or try a different location.")
            st.stop()

        coords = geo_response['results'][0]['geometry']['location']
        lat = coords['lat']
        lng = coords['lng']

        # Step 2: Search nearby places
        places_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=5000&keyword={category}&key={api_key}"
        places_response = requests.get(places_url).json()

        data = []

        for place in places_response.get("results", []):
            name = place.get("name")
            address = place.get("vicinity")
            place_id = place.get("place_id")

            # Step 3: Get phone number
            details_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=formatted_phone_number,website,rating&key={api_key}"
            details = requests.get(details_url).json().get("result", {})

            phone = details.get("formatted_phone_number", "N/A")
            website = details.get("website", "N/A")
            rating = details.get("rating", "N/A")

            data.append([name, category, address, rating, phone, website])

        # Step 4: Create Excel
        df = pd.DataFrame(data, columns=["Store Name", "Category", "Address", "Rating", "Phone", "Website"])
        output = BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)

        st.download_button(
            label="📥 Download Excel",
            data=output,
            file_name="leads.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("Please enter both Location and Category.")
