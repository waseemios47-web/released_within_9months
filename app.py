import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime, timedelta

# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(
    page_title="iOS Top 1000 Games (Last 9 Months)",
    layout="centered"
)

st.title("📱 iOS Top 1000 Games Scraper")
st.write("Fetch Top 1000 games per category and filter by release date (last 9 months).")

# -------------------------
# APP TWEAK CONFIG
# -------------------------
API_KEY = "CdphJWrEHZ5ZQ1uPeGUnTohm22w"

HEADERS = {
    "accept": "application/json",
    "x-apptweak-key": API_KEY
}

TOP_CHARTS_URL = "https://public-api.apptweak.com/api/public/store/charts/top-results/current.json"
METADATA_URL = "https://public-api.apptweak.com/api/public/store/apps/metadata.json"

# -------------------------
# COUNTRIES (ALL 38)
# -------------------------
COUNTRIES = {
    "United States": "us",
    "Taiwan": "tw",
    "United Kingdom": "gb",
    "Vietnam": "vn",
    "United Arab Emirates": "ae",
    "Ukraine": "ua",
    "Turkey": "tr",
    "Thailand": "th",
    "Sweden": "se",
    "Spain": "es",
    "Australia": "au",
    "Brazil": "br",
    "Canada": "ca",
    "Czech Republic": "cz",
    "Denmark": "dk",
    "France": "fr",
    "Germany": "de",
    "Italy": "it",
    "Malaysia": "my",
    "Japan": "jp",
    "Mexico": "mx",
    "Netherlands": "nl",
    "Norway": "no",
    "Poland": "pl",
    "Russia": "ru",
    "Saudi Arabia": "sa",
    "Switzerland": "ch",
    "Romania": "ro",
    "Hungary": "hu",
    "China": "cn",
    "Croatia": "hr",
    "Finland": "fi",
    "Greece": "gr",
    "Israel": "il",
    "Indonesia": "id",
    "Hong Kong": "hk",
    "Portugal": "pt",
    "Slovakia": "sk",
    "Slovenia": "si",
    "South Korea": "kr"
}

# -------------------------
# GAME CATEGORIES (ALL 16)
# -------------------------
GAME_CATEGORIES = {
    "Action": "7001",
    "Adventure": "7002",
    "Casual": "7003",
    "Board": "7004",
    "Card": "7005",
    "Casino": "7006",
    "Family": "7009",
    "Music": "7011",
    "Puzzle": "7012",
    "Racing": "7013",
    "Role Playing": "7014",
    "Simulation": "7015",
    "Sports": "7016",
    "Strategy": "7017",
    "Trivia": "7018",
    "Word": "7019"
}

# -------------------------
# UI INPUTS
# -------------------------
country_name = st.selectbox("🌍 Select Country", list(COUNTRIES.keys()))
category_name = st.selectbox("🎮 Select Game Category", list(GAME_CATEGORIES.keys()))

# -------------------------
# RUN BUTTON
# -------------------------
if st.button("🚀 Run Scraper"):

    start_time = time.time()
    start_display = datetime.now().strftime("%H:%M:%S")

    timer = st.empty()
    status = st.empty()

    status.info(f"⏱ Started at {start_display}")

    country_code = COUNTRIES[country_name]
    category_id = GAME_CATEGORIES[category_name]

    app_ids = []

    # -------------------------
    # FETCH TOP 1000 APP IDS
    # -------------------------
    for offset in range(0, 1000, 100):

        elapsed = int(time.time() - start_time)
        timer.warning(f"⏳ Fetching chart data... {elapsed}s elapsed")

        params = {
            "categories": category_id,
            "types": "free",
            "country": country_code,
            "device": "iphone",
            "limit": 100,
            "offset": offset
        }

        r = requests.get(TOP_CHARTS_URL, headers=HEADERS, params=params)

        if r.status_code != 200:
            continue

        result = r.json()["result"]
        key = list(result.keys())[0]
        ids = result[key]["free"]["value"]

        if not ids:
            break

        app_ids.extend(ids)
        time.sleep(0.6)

    app_ids = app_ids[:1000]

    # -------------------------
    # FETCH METADATA + FILTER 9 MONTHS
    # -------------------------
    results = []
    nine_months_ago = datetime.now() - timedelta(days=270)

    def chunk(lst, size=5):
        for i in range(0, len(lst), size):
            yield lst[i:i + size]

    for batch in chunk(app_ids):

        elapsed = int(time.time() - start_time)
        timer.warning(f"⏳ Fetching metadata... {elapsed}s")

        params = {
            "apps": ",".join(map(str, batch)),
            "country": country_code,
            "device": "iphone"
        }

        r = requests.get(METADATA_URL, headers=HEADERS, params=params)

        if r.status_code != 200:
            continue

        metadata = r.json()["result"]

        for app_id in batch:
            app_data = metadata.get(str(app_id), {}).get("metadata", {})
            title = app_data.get("title")
            release_date_str = app_data.get("release_date")

            if title and release_date_str:
                release_date = datetime.fromisoformat(
                    release_date_str.replace("Z", "")
                )

                if release_date >= nine_months_ago:
                    results.append({
                        "Game Title": title,
                        "Release Date": release_date.strftime("%Y-%m-%d")
                    })

        time.sleep(0.6)

    # -------------------------
    # FINISH
    # -------------------------
    end_time = time.time()
    end_display = datetime.now().strftime("%H:%M:%S")
    total_time = int(end_time - start_time)

    timer.success(
        f"✅ Finished!\n\n"
        f"Start: {start_display}\n"
        f"End: {end_display}\n"
        f"Total Time: {total_time} seconds"
    )

    df = pd.DataFrame(results)

    st.success(f"🎯 Found {len(df)} games released in last 9 months.")

    st.download_button(
        label="⬇️ Download CSV",
        data=df.to_csv(index=False),
        file_name=f"{category_name.lower().replace(' ','_')}_{country_code}_last9months.csv",
        mime="text/csv"
    )
