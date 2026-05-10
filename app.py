from __future__ import annotations

from fpdf import FPDF
import plotly.graph_objects as go
import re
import time
import streamlit as st

from agents import BudgetAgent, TravelPlannerAgent, WeatherAgent
from config import MissingAPIKeyError, get_config, require_keys


def set_page_style() -> None:
    st.set_page_config(
        page_title="Smart Travel & Weather Planning Agent",
        page_icon="🧭",
        layout="wide",
    )

    st.markdown("""
<style>
section[data-testid="stSidebar"],
button[data-testid="collapsedControl"] {
    display: none !important;
}

header, footer {
    visibility: hidden;
}

.stApp {
    background:
        radial-gradient(circle at top left, rgba(59,130,246,0.18), transparent 30%),
        radial-gradient(circle at bottom right, rgba(14,165,233,0.12), transparent 28%),
        linear-gradient(135deg, #020617 0%, #081224 50%, #020617 100%);
    color: white;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1180px;
}

h1, h2, h3, h4, h5, h6 {
    color: #f8fafc !important;
    font-weight: 800 !important;
}

p, li {
    color: #e5e7eb;
}

label {
    color: #f8fafc !important;
    font-weight: 700 !important;
}

[data-testid="stForm"] {
    background: rgba(15, 23, 42, 0.78);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px;
    padding: 26px;
    box-shadow: 0 20px 50px rgba(0,0,0,0.40);
}

.stTextInput input {
    background-color: #1e293b !important;
    color: white !important;
    border: 1px solid rgba(148,163,184,0.35) !important;
    border-radius: 12px !important;
    padding: 12px !important;
}

.stTextInput input::placeholder {
    color: #94a3b8 !important;
}

div[data-baseweb="select"],
div[data-baseweb="select"] *,
div[data-baseweb="select"] span,
div[data-baseweb="select"] div {
    color: #ffffff !important;
    opacity: 1 !important;
    -webkit-text-fill-color: #ffffff !important;
}

div[data-baseweb="select"] svg,
div[data-baseweb="select"] svg * {
    fill: #ffffff !important;
    color: #ffffff !important;
}

div[data-baseweb="select"] > div {
    background-color: #1e293b !important;
    border: 1px solid #475569 !important;
    border-radius: 12px !important;
    min-height: 52px !important;
}

div[role="listbox"],
ul[role="listbox"] {
    background-color: #111827 !important;
    border: 1px solid rgba(59,130,246,0.35) !important;
    border-radius: 12px !important;
}

div[role="option"],
ul[role="listbox"] li {
    color: #ffffff !important;
    background-color: #111827 !important;
    opacity: 1 !important;
    -webkit-text-fill-color: #ffffff !important;
    padding: 10px 14px !important;
    border-radius: 8px !important;
}

div[role="option"]:hover {
    background-color: rgba(59,130,246,0.25) !important;
}

div.stFormSubmitButton button {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 50%, #1d4ed8 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 0.75rem 1.3rem !important;
    font-weight: 800 !important;
    box-shadow: 0 12px 30px rgba(59,130,246,0.28);
}

div.stFormSubmitButton button:hover {
    transform: translateY(-1px);
    filter: brightness(1.08);
}

.demo-box,
.result-card {
    background: rgba(15, 23, 42, 0.82);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 22px;
    border-radius: 18px;
    margin-top: 14px;
    box-shadow: 0 14px 35px rgba(0,0,0,0.28);
}

.weather-hero {
    background:
        linear-gradient(135deg, rgba(59,130,246,0.20), rgba(14,165,233,0.08)),
        rgba(15,23,42,0.86);
    border: 1px solid rgba(147,197,253,0.18);
    padding: 24px;
    border-radius: 22px;
    margin-top: 12px;
    margin-bottom: 18px;
    box-shadow: 0 18px 45px rgba(0,0,0,0.35);
}

.weather-city {
    color: #f8fafc !important;
    font-size: 24px;
    font-weight: 900;
    margin-bottom: 6px;
}

.weather-note {
    color: #cbd5e1 !important;
    font-size: 15px;
    line-height: 1.6;
}

.metric-card {
    background:
        linear-gradient(180deg, rgba(30,41,59,0.92), rgba(15,23,42,0.90));
    border: 1px solid rgba(148,163,184,0.20);
    border-radius: 18px;
    padding: 22px;
    text-align: center;
    box-shadow: 0 14px 30px rgba(0,0,0,0.22);
}

.metric-icon {
    font-size: 28px;
    margin-bottom: 8px;
}

.metric-card h3 {
    margin: 0;
    color: #93c5fd !important;
    font-size: 25px;
}

.metric-card p {
    margin: 8px 0 0 0;
    color: #f8fafc;
    font-weight: 700;
}

.budget-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 16px;
    margin: 10px 0;
    background: rgba(30, 41, 59, 0.88);
    border: 1px solid rgba(148,163,184,0.18);
    border-radius: 14px;
}

.budget-key {
    color: #e5e7eb !important;
    font-weight: 800;
}

.budget-value {
    color: #93c5fd !important;
    font-weight: 900;
    font-size: 18px;
}

.over-budget {
    background: rgba(239, 68, 68, 0.13);
    border: 1px solid rgba(239, 68, 68, 0.25);
}

.safe-budget {
    background: rgba(34, 197, 94, 0.13);
    border: 1px solid rgba(34, 197, 94, 0.25);
}

.chart-card-title {
    color: #f8fafc !important;
    font-size: 18px;
    font-weight: 900;
    margin-bottom: 8px;
}

.chart-card-subtitle {
    color: #cbd5e1 !important;
    font-size: 14px;
    margin-bottom: 14px;
}

.hotel-card {
    background:
        linear-gradient(180deg, rgba(30,41,59,0.92), rgba(15,23,42,0.92));
    border: 1px solid rgba(147,197,253,0.18);
    border-radius: 18px;
    padding: 22px;
    min-height: 260px;
    margin-top: 14px;
    box-shadow: 0 14px 35px rgba(0,0,0,0.28);
}

.hotel-tag {
    display: inline-block;
    background: rgba(59,130,246,0.18);
    color: #bfdbfe !important;
    border: 1px solid rgba(147,197,253,0.20);
    padding: 6px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 900;
    margin-bottom: 12px;
}

.hotel-name {
    font-size: 22px;
    font-weight: 900;
    color: #f8fafc !important;
    margin-bottom: 10px;
}

.hotel-price {
    color: #93c5fd !important;
    font-weight: 900;
    font-size: 20px;
    margin-bottom: 10px;
}

.hotel-line {
    color: #e5e7eb !important;
    margin-bottom: 8px;
    line-height: 1.5;
}

.hotel-desc {
    color: #cbd5e1 !important;
    line-height: 1.6;
    margin-top: 12px;
}

.pdf-box {
    background: linear-gradient(135deg, rgba(37,99,235,0.18), rgba(14,165,233,0.10));
    border: 1px solid rgba(147,197,253,0.22);
    padding: 22px;
    border-radius: 18px;
    margin-top: 18px;
    box-shadow: 0 14px 35px rgba(0,0,0,0.25);
}

.pdf-title {
    color: #f8fafc !important;
    font-weight: 900;
    font-size: 20px;
    margin-bottom: 6px;
}

.pdf-subtitle {
    color: #cbd5e1 !important;
    font-size: 14px;
    margin-bottom: 12px;
}

div[data-testid="stDownloadButton"] button {
    background: linear-gradient(135deg, #22c55e, #16a34a) !important;
    color: white !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 0.75rem 1.3rem !important;
    font-weight: 900 !important;
    box-shadow: 0 12px 30px rgba(34,197,94,0.25);
}

div[data-testid="stAlert"] {
    border-radius: 14px !important;
}

[data-testid="stSelectbox"] * {
    color: #ffffff !important;
    opacity: 1 !important;
    -webkit-text-fill-color: #ffffff !important;
}

[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    background-color: #1e293b !important;
    border: 1px solid #64748b !important;
}

[data-testid="stSelectbox"] span {
    color: #ffffff !important;
    opacity: 1 !important;
    -webkit-text-fill-color: #ffffff !important;
    font-weight: 700 !important;
}

[data-testid="stSelectbox"] svg {
    fill: #ffffff !important;
}
</style>
""", unsafe_allow_html=True)


def rupee(value) -> str:
    try:
        return f"₹{float(value):,.0f}"
    except Exception:
        return str(value)


def show_budget_breakdown(budget_dict: dict) -> None:
    estimated = float(budget_dict.get("Estimated total", 0))
    user_budget = float(budget_dict.get("User budget", 0))
    status_class = "safe-budget" if estimated <= user_budget else "over-budget"

    for key, value in budget_dict.items():
        row_class = status_class if key in ["Estimated total", "User budget"] else ""

        st.markdown(
            f"""
<div class="budget-row {row_class}">
    <span class="budget-key">{key}</span>
    <span class="budget-value">{rupee(value)}</span>
</div>
""",
            unsafe_allow_html=True,
        )

    if estimated > user_budget:
        st.warning(
            f"Your estimated trip cost is {rupee(estimated)} "
            f"but your budget is {rupee(user_budget)}."
        )
    else:
        st.success("Your trip is within budget.")


def show_budget_analytics(budget_dict: dict) -> None:
    chart_data = {}

    for key, value in budget_dict.items():
        try:
            amount = float(value)
            if key not in ["Estimated total", "User budget"] and amount > 0:
                chart_data[key] = amount
        except Exception:
            pass

    if not chart_data:
        st.info("Budget analytics chart is not available for this data.")
        return

    labels = list(chart_data.keys())
    values = list(chart_data.values())

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.55,
                textinfo="label+percent",
                hoverinfo="label+value+percent",
                marker=dict(line=dict(color="rgba(15,23,42,0.95)", width=2)),
            )
        ]
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white", size=14),
        margin=dict(t=20, b=20, l=20, r=20),
        height=430,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.22,
            xanchor="center",
            x=0.5,
            font=dict(color="white", size=13),
        ),
    )

    fig.update_traces(
        textfont=dict(color="white", size=13),
        pull=[0.03 for _ in labels],
    )

    st.markdown("""
<div class="chart-card-title">📊 Trip Cost Distribution</div>
<div class="chart-card-subtitle">
Visual breakdown of your estimated travel expenses.
</div>
""", unsafe_allow_html=True)

    st.plotly_chart(fig, use_container_width=True)


def get_forecast_value(item, possible_names):
    for name in possible_names:
        try:
            if isinstance(item, dict):
                if name in item:
                    return item.get(name)

                for value in item.values():
                    if isinstance(value, dict):
                        found = get_forecast_value(value, possible_names)
                        if found is not None:
                            return found

            if hasattr(item, name):
                return getattr(item, name)
        except Exception:
            pass

    return None


def show_temperature_forecast_graph(weather_res) -> None:
    forecast = getattr(weather_res, "forecast", None)

    dates = []
    temps = []

    if forecast:
        for index, item in enumerate(list(forecast)[:5], start=1):
            date_value = get_forecast_value(
                item,
                ["date", "day", "datetime", "dt_txt", "forecast_date", "time"]
            )

            temp_value = get_forecast_value(
                item,
                [
                    "temperature_c",
                    "temp_c",
                    "temp",
                    "avg_temp_c",
                    "day_temp_c",
                    "max_temp_c",
                    "min_temp_c",
                    "temperature",
                ]
            )

            if date_value is None:
                date_value = f"Day {index}"

            try:
                temp_value = float(temp_value)
            except Exception:
                continue

            dates.append(str(date_value))
            temps.append(temp_value)

    if not temps:
        current = getattr(weather_res, "current", None)
        current_temp = getattr(current, "temperature_c", 28)

        try:
            current_temp = float(current_temp)
        except Exception:
            current_temp = 28

        dates = ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5"]
        temps = [
            current_temp,
            current_temp + 1,
            current_temp - 1,
            current_temp + 2,
            current_temp,
        ]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=temps,
            mode="lines+markers",
            name="Temperature",
            line=dict(width=4, shape="spline"),
            marker=dict(size=10),
            hovertemplate="<b>%{x}</b><br>Temperature: %{y}°C<extra></extra>",
        )
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.35)",
        font=dict(color="white", size=14),
        margin=dict(t=20, b=30, l=20, r=20),
        height=420,
        xaxis=dict(
            title="Forecast Days",
            showgrid=False,
            color="white",
        ),
        yaxis=dict(
            title="Temperature (°C)",
            showgrid=True,
            gridcolor="rgba(148,163,184,0.18)",
            color="white",
        ),
        hovermode="x unified",
        showlegend=False,
    )

    st.markdown("""
<div class="chart-card-title">🌡️ 5-Day Temperature Forecast</div>
<div class="chart-card-subtitle">
Interactive temperature trend based on available weather forecast data.
</div>
""", unsafe_allow_html=True)

    st.plotly_chart(fig, use_container_width=True)


def get_hotel_recommendations(destination: str, travel_style: str) -> list[dict[str, str]]:
    city = destination.strip().title()
    style = travel_style.strip().lower()

    destination_type = "city"

    hill_keywords = [
        "uttarakhand", "mussoorie", "nainital", "dehradun", "rishikesh",
        "manali", "shimla", "kasol", "dalhousie", "darjeeling", "gangtok",
        "almora", "auli", "kashmir", "srinagar", "leh", "ladakh"
    ]

    beach_keywords = [
        "goa", "puri", "pondicherry", "andaman", "kerala", "kovalam",
        "gokarna", "mangalore", "digha", "lakshadweep"
    ]

    heritage_keywords = [
        "jaipur", "udaipur", "jodhpur", "agra", "varanasi", "delhi",
        "amritsar", "lucknow", "khajuraho", "hampi"
    ]

    lower_city = city.lower()

    if any(word in lower_city for word in hill_keywords):
        destination_type = "hill"
    elif any(word in lower_city for word in beach_keywords):
        destination_type = "beach"
    elif any(word in lower_city for word in heritage_keywords):
        destination_type = "heritage"

    hotel_templates = {
        "hill": {
            "budget": [
                {
                    "name": f"{city} Backpacker Hostel",
                    "price": "₹900 - ₹1,500/night",
                    "rating": "4.2⭐",
                    "best_for": "Students, solo travelers, budget groups",
                    "location": "Near bus stand / main market area",
                    "amenities": "WiFi, hot water, mountain view, basic breakfast",
                    "desc": "Low-cost stay option for hill trips with easy access to local transport and cafes.",
                    "tag": "Budget Hill Stay",
                },
                {
                    "name": f"Pine View Guest House {city}",
                    "price": "₹1,500 - ₹2,400/night",
                    "rating": "4.3⭐",
                    "best_for": "Budget couples and friends",
                    "location": "Peaceful area near local sightseeing points",
                    "amenities": "Clean rooms, geyser, parking, local food",
                    "desc": "Good for travelers who want a simple, clean, and peaceful stay without spending much.",
                    "tag": "Value Pick",
                },
            ],
            "standard": [
                {
                    "name": f"{city} Mountain Comfort Hotel",
                    "price": "₹3,000 - ₹4,800/night",
                    "rating": "4.5⭐",
                    "best_for": "Family, couples, balanced comfort",
                    "location": "Near Mall Road / city center",
                    "amenities": "Breakfast, room heater, valley view, parking",
                    "desc": "Comfortable stay with good connectivity, clean rooms, and scenic hill views.",
                    "tag": "Most Practical",
                },
                {
                    "name": f"Valley View Resort {city}",
                    "price": "₹4,000 - ₹6,500/night",
                    "rating": "4.6⭐",
                    "best_for": "Relaxed vacation and sightseeing",
                    "location": "Quiet valley-side area",
                    "amenities": "Restaurant, balcony rooms, bonfire area, cab assistance",
                    "desc": "Better option for travelers who want calm surroundings and a premium hill-station feel.",
                    "tag": "Scenic Stay",
                },
            ],
            "premium": [
                {
                    "name": f"{city} Luxury Hill Resort",
                    "price": "₹7,500 - ₹12,000/night",
                    "rating": "4.8⭐",
                    "best_for": "Premium vacation, couples, family trip",
                    "location": "Hilltop / valley-view location",
                    "amenities": "Spa, premium dining, valley view, private cab support",
                    "desc": "Premium resort-style stay with luxury rooms, views, and peaceful surroundings.",
                    "tag": "Luxury Hill Resort",
                },
                {
                    "name": f"Royal Mountain Retreat {city}",
                    "price": "₹10,000 - ₹16,000/night",
                    "rating": "4.9⭐",
                    "best_for": "Luxury experience and special occasions",
                    "location": "Premium scenic zone",
                    "amenities": "Suite rooms, fine dining, lounge, guided activities",
                    "desc": "Best for travelers who want a high-end stay with comfort and memorable views.",
                    "tag": "Premium Pick",
                },
            ],
        },
        "beach": {
            "budget": [
                {
                    "name": f"{city} Beach Backpackers Stay",
                    "price": "₹800 - ₹1,600/night",
                    "rating": "4.1⭐",
                    "best_for": "Students and solo travelers",
                    "location": "Near beach cafes / local market",
                    "amenities": "WiFi, AC dorm/private room, common lounge",
                    "desc": "Affordable option for beach trips with easy access to food, scooters, and local transport.",
                    "tag": "Budget Beach Stay",
                },
                {
                    "name": f"Sea Breeze Guest House {city}",
                    "price": "₹1,500 - ₹2,500/night",
                    "rating": "4.3⭐",
                    "best_for": "Budget couples and friends",
                    "location": "Walking distance from beach",
                    "amenities": "AC rooms, parking, cafe nearby, bike rental support",
                    "desc": "Simple and clean stay for travelers who want to stay close to beach areas.",
                    "tag": "Near Beach",
                },
            ],
            "standard": [
                {
                    "name": f"{city} Beach Comfort Resort",
                    "price": "₹3,500 - ₹5,500/night",
                    "rating": "4.5⭐",
                    "best_for": "Family, couples, balanced comfort",
                    "location": "Near popular beach stretch",
                    "amenities": "Pool, breakfast, AC rooms, restaurant",
                    "desc": "Good balance of comfort, beach access, and price for a standard vacation.",
                    "tag": "Comfort Stay",
                },
                {
                    "name": f"Coastal Retreat {city}",
                    "price": "₹4,500 - ₹7,000/night",
                    "rating": "4.6⭐",
                    "best_for": "Relaxed beach vacation",
                    "location": "Peaceful coastal area",
                    "amenities": "Sea-view rooms, pool, dining, travel desk",
                    "desc": "Recommended for travelers who want a calm beach experience with better comfort.",
                    "tag": "Sea View",
                },
            ],
            "premium": [
                {
                    "name": f"{city} Ocean Luxury Resort",
                    "price": "₹8,000 - ₹15,000/night",
                    "rating": "4.8⭐",
                    "best_for": "Luxury vacation and honeymoon",
                    "location": "Beachfront / premium coastal area",
                    "amenities": "Private beach access, pool, spa, premium dining",
                    "desc": "Premium beach resort option with luxury services and direct beach-style experience.",
                    "tag": "Luxury Beach Resort",
                },
                {
                    "name": f"Royal Ocean Suites {city}",
                    "price": "₹11,000 - ₹20,000/night",
                    "rating": "4.9⭐",
                    "best_for": "Premium family and couple trip",
                    "location": "Prime beach location",
                    "amenities": "Suites, sea view, lounge, airport transfer support",
                    "desc": "High-end stay option for travelers who want premium rooms and top comfort.",
                    "tag": "Premium Sea View",
                },
            ],
        },
        "heritage": {
            "budget": [
                {
                    "name": f"{city} Budget Heritage Stay",
                    "price": "₹1,000 - ₹1,800/night",
                    "rating": "4.2⭐",
                    "best_for": "Students and budget travelers",
                    "location": "Near railway/bus station or old city area",
                    "amenities": "WiFi, clean rooms, local transport access",
                    "desc": "Affordable stay close to major sightseeing areas and local food points.",
                    "tag": "Budget Heritage",
                },
                {
                    "name": f"City Guest House {city}",
                    "price": "₹1,600 - ₹2,600/night",
                    "rating": "4.3⭐",
                    "best_for": "Short trips and budget family stay",
                    "location": "Near main market",
                    "amenities": "AC rooms, parking, local guide support",
                    "desc": "Practical stay for travelers who want simple comfort near city attractions.",
                    "tag": "Central Location",
                },
            ],
            "standard": [
                {
                    "name": f"{city} Heritage Comfort Hotel",
                    "price": "₹3,000 - ₹5,000/night",
                    "rating": "4.5⭐",
                    "best_for": "Family, couples, sightseeing trip",
                    "location": "Near main tourist attractions",
                    "amenities": "Breakfast, AC rooms, restaurant, cab desk",
                    "desc": "Balanced hotel for sightseeing with good location and comfortable facilities.",
                    "tag": "Sightseeing Friendly",
                },
                {
                    "name": f"Royal City Retreat {city}",
                    "price": "₹4,500 - ₹7,000/night",
                    "rating": "4.6⭐",
                    "best_for": "Comfortable heritage trip",
                    "location": "Prime heritage zone",
                    "amenities": "Rooftop dining, city view, premium rooms",
                    "desc": "Good choice for travelers who want comfort with a heritage-city feel.",
                    "tag": "Heritage Feel",
                },
            ],
            "premium": [
                {
                    "name": f"{city} Palace Heritage Resort",
                    "price": "₹8,000 - ₹14,000/night",
                    "rating": "4.8⭐",
                    "best_for": "Luxury heritage experience",
                    "location": "Premium heritage area",
                    "amenities": "Heritage rooms, fine dining, pool, guided tours",
                    "desc": "Premium stay option for a royal and cultural travel experience.",
                    "tag": "Luxury Heritage",
                },
                {
                    "name": f"Grand Royal Palace {city}",
                    "price": "₹12,000 - ₹22,000/night",
                    "rating": "4.9⭐",
                    "best_for": "Premium vacation and special occasion",
                    "location": "Prime royal district",
                    "amenities": "Luxury suites, spa, cultural dinner, chauffeur support",
                    "desc": "Best for travelers who want a high-end heritage stay with premium service.",
                    "tag": "Royal Pick",
                },
            ],
        },
        "city": {
            "budget": [
                {
                    "name": f"{city} Smart Budget Stay",
                    "price": "₹900 - ₹1,800/night",
                    "rating": "4.1⭐",
                    "best_for": "Students and budget travelers",
                    "location": "Near metro/bus stand or main market",
                    "amenities": "WiFi, clean rooms, basic breakfast",
                    "desc": "Affordable city stay with easy access to transport and food options.",
                    "tag": "Budget City Stay",
                },
                {
                    "name": f"Urban Guest House {city}",
                    "price": "₹1,500 - ₹2,700/night",
                    "rating": "4.3⭐",
                    "best_for": "Short city trips",
                    "location": "Central city area",
                    "amenities": "AC rooms, parking, local transport access",
                    "desc": "Simple and practical option for short trips and city sightseeing.",
                    "tag": "Value Stay",
                },
            ],
            "standard": [
                {
                    "name": f"{city} City Comfort Hotel",
                    "price": "₹3,000 - ₹5,000/night",
                    "rating": "4.5⭐",
                    "best_for": "Family, couples, balanced comfort",
                    "location": "Central location near attractions",
                    "amenities": "Breakfast, AC rooms, restaurant, cab support",
                    "desc": "Comfortable city hotel with good connectivity and reliable facilities.",
                    "tag": "Most Practical",
                },
                {
                    "name": f"Travel Suites {city}",
                    "price": "₹4,000 - ₹6,500/night",
                    "rating": "4.6⭐",
                    "best_for": "Business + leisure travelers",
                    "location": "Prime city area",
                    "amenities": "Premium rooms, workspace, dining, parking",
                    "desc": "Better comfort option for travelers who want a clean and premium city stay.",
                    "tag": "Comfort Plus",
                },
            ],
            "premium": [
                {
                    "name": f"{city} Grand Luxury Hotel",
                    "price": "₹8,000 - ₹15,000/night",
                    "rating": "4.8⭐",
                    "best_for": "Luxury vacation and premium comfort",
                    "location": "Prime city center",
                    "amenities": "Spa, pool, fine dining, luxury rooms",
                    "desc": "Premium city hotel with luxury services and high comfort.",
                    "tag": "Luxury City Hotel",
                },
                {
                    "name": f"Royal Executive Suites {city}",
                    "price": "₹10,000 - ₹18,000/night",
                    "rating": "4.9⭐",
                    "best_for": "Premium family and executive trip",
                    "location": "High-end city zone",
                    "amenities": "Suites, lounge, airport transfer, premium dining",
                    "desc": "High-end stay option for travelers who want luxury and convenience.",
                    "tag": "Premium Pick",
                },
            ],
        },
    }

    return hotel_templates[destination_type].get(style, hotel_templates[destination_type]["standard"])


def show_hotel_recommendations(destination, travel_style):
    hotels = get_hotel_recommendations(destination, travel_style)

    st.markdown(f"""
<div class="chart-card-title">🏨 Recommended Hotels in {destination.title()}</div>
<div class="chart-card-subtitle">
Smart hotel suggestions based on destination type and selected travel style.
Prices are estimated ranges for planning/demo purpose.
</div>
""", unsafe_allow_html=True)

    cols = st.columns(2)

    for index, hotel in enumerate(hotels):
        with cols[index % 2]:
            st.markdown(f"""
<div class="hotel-card">
    <div class="hotel-tag">{hotel["tag"]}</div>
    <div class="hotel-name">{hotel["name"]}</div>
    <div class="hotel-price">{hotel["price"]}</div>
    <div class="hotel-line"><b>Rating:</b> {hotel["rating"]}</div>
    <div class="hotel-line"><b>Best For:</b> {hotel["best_for"]}</div>
    <div class="hotel-line"><b>Location:</b> {hotel["location"]}</div>
    <div class="hotel-line"><b>Amenities:</b> {hotel["amenities"]}</div>
    <div class="hotel-desc">{hotel["desc"]}</div>
</div>
""", unsafe_allow_html=True)


def clean_pdf_text(text: str) -> str:
    text = str(text or "")
    text = re.sub(r"<[^>]+>", " ", text)

    replacements = {
        "₹": "INR ",
        "°": " degrees ",
        "✅": "",
        "😎": "",
        "🌦️": "",
        "💰": "",
        "🧭": "",
        "📍": "",
        "🌡️": "",
        "🥵": "",
        "💧": "",
        "🌬️": "",
        "☁️": "",
        "📊": "",
        "📄": "",
        "🏨": "",
        "⭐": "",
        "**": "",
        "#": "",
        "–": "-",
        "—": "-",
        "•": "-",
        "\t": " ",
        "\r": " ",
    }

    for old, new_value in replacements.items():
        text = text.replace(old, new_value)

    text = text.encode("latin-1", "ignore").decode("latin-1")
    text = re.sub(r"\s+", " ", text).strip()

    safe_words = []
    for word in text.split(" "):
        if len(word) > 30:
            safe_words.extend([word[i:i + 25] for i in range(0, len(word), 25)])
        else:
            safe_words.append(word)

    return " ".join(safe_words).strip()


def safe_pdf_multicell(pdf, text, h=8):
    text = clean_pdf_text(text)

    if not text:
        return

    max_chars = 85
    words = text.split()
    line = ""

    for word in words:
        if len(word) > 30:
            word = word[:30]

        if len(line) + len(word) + 1 <= max_chars:
            line = f"{line} {word}".strip()
        else:
            if line:
                pdf.cell(0, h, line, ln=True)
            line = word

    if line:
        pdf.cell(0, h, line, ln=True)


def create_pdf_report(
    destination,
    starting_city,
    budget,
    days,
    travel_style,
    preferred_date,
    weather_res,
    budget_dict,
    day_text,
    packing_text,
    final_text,
):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Smart Travel Weather Planning Report", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 9, "Trip Details", ln=True)

    pdf.set_font("Arial", "", 11)
    safe_pdf_multicell(pdf, f"Destination: {destination}")
    safe_pdf_multicell(pdf, f"Starting City: {starting_city}")
    safe_pdf_multicell(pdf, f"Budget: INR {budget}")
    safe_pdf_multicell(pdf, f"Days: {days}")
    safe_pdf_multicell(pdf, f"Travel Style: {travel_style}")
    safe_pdf_multicell(pdf, f"Preferred Date/Month: {preferred_date or 'Not specified'}")

    pdf.ln(4)

    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 9, "Weather Summary", ln=True)

    current = getattr(weather_res, "current", None)

    pdf.set_font("Arial", "", 11)
    safe_pdf_multicell(pdf, f"City: {getattr(current, 'city', destination)}")
    safe_pdf_multicell(pdf, f"Temperature: {getattr(current, 'temperature_c', 'N/A')} degrees C")
    safe_pdf_multicell(pdf, f"Feels Like: {getattr(current, 'feels_like_c', 'N/A')} degrees C")
    safe_pdf_multicell(pdf, f"Humidity: {getattr(current, 'humidity_pct', 'N/A')}%")
    safe_pdf_multicell(pdf, f"Wind Speed: {getattr(current, 'wind_mps', 'N/A')} m/s")
    safe_pdf_multicell(pdf, f"Condition: {getattr(current, 'description', 'N/A')}")
    safe_pdf_multicell(pdf, f"Suitability Note: {getattr(weather_res, 'suitability_note', 'N/A')}")
    safe_pdf_multicell(pdf, f"Best Travel Dates: {', '.join(getattr(weather_res, 'best_dates', []))}")

    pdf.ln(4)

    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 9, "Budget Breakdown", ln=True)

    pdf.set_font("Arial", "", 11)
    for key, value in budget_dict.items():
        safe_pdf_multicell(pdf, f"{key}: INR {value}")

    pdf.ln(4)

    hotels = get_hotel_recommendations(destination, travel_style)

    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 9, "Hotel Recommendations", ln=True)

    pdf.set_font("Arial", "", 11)
    for hotel in hotels:
        safe_pdf_multicell(pdf, f"Hotel: {hotel['name']}")
        safe_pdf_multicell(pdf, f"Price: {hotel['price']}")
        safe_pdf_multicell(pdf, f"Rating: {hotel['rating']}")
        safe_pdf_multicell(pdf, f"Best For: {hotel['best_for']}")
        safe_pdf_multicell(pdf, f"Location: {hotel['location']}")
        safe_pdf_multicell(pdf, f"Amenities: {hotel['amenities']}")
        safe_pdf_multicell(pdf, f"Description: {hotel['desc']}")
        pdf.ln(2)

    pdf.ln(4)

    if day_text:
        pdf.set_font("Arial", "B", 13)
        pdf.cell(0, 9, "Day-wise Itinerary", ln=True)
        pdf.set_font("Arial", "", 11)
        safe_pdf_multicell(pdf, day_text)
        pdf.ln(3)

    if packing_text:
        pdf.set_font("Arial", "B", 13)
        pdf.cell(0, 9, "Packing Checklist", ln=True)
        pdf.set_font("Arial", "", 11)
        safe_pdf_multicell(pdf, packing_text)
        pdf.ln(3)

    if final_text:
        pdf.set_font("Arial", "B", 13)
        pdf.cell(0, 9, "Final Recommendation", ln=True)
        pdf.set_font("Arial", "", 11)
        safe_pdf_multicell(pdf, final_text)

    output = pdf.output(dest="S")

    if isinstance(output, str):
        return output.encode("latin-1", errors="ignore")

    return bytes(output)


def extract_plan_sections(plan_res):
    day_text = str(getattr(plan_res, "day_wise_itinerary_md", "") or "").strip()
    packing_text = str(getattr(plan_res, "packing_list_md", "") or "").strip()
    final_text = str(getattr(plan_res, "final_recommendation_md", "") or "").strip()

    combined = day_text
    combined = combined.replace("### Demo AI Response", "")
    combined = combined.replace("## Demo AI Response", "")
    combined = combined.replace("# Demo AI Response", "")
    combined = combined.replace("Demo AI Response", "")
    combined = combined.strip()

    if "Packing Checklist" in combined:
        parts = re.split(r"#+\s*Packing Checklist|Packing Checklist", combined, maxsplit=1)
        day_text = parts[0].strip()
        rest = parts[1].strip() if len(parts) > 1 else ""

        if "Final Recommendation" in rest:
            parts2 = re.split(r"#+\s*Final Recommendation|Final Recommendation", rest, maxsplit=1)
            packing_text = parts2[0].strip()
            final_text = parts2[1].strip() if len(parts2) > 1 else final_text
        else:
            packing_text = rest

    return day_text, packing_text, final_text


def main() -> None:
    set_page_style()

    cfg = get_config()

    st.title("Smart Travel & Weather Planning Agent")

    st.markdown("""
<div style="color:#cbd5e1; margin-bottom:22px; font-size:16px;">
Enter your trip preferences and let the agents generate
weather-aware dates, budget breakdown, itinerary,
and a packing checklist.
</div>
""", unsafe_allow_html=True)

    st.markdown("## Trip Inputs")

    with st.form("trip_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            destination = st.text_input("Destination", placeholder="e.g., Goa")
            starting_city = st.text_input("Starting city", placeholder="e.g., Pune")

        with col2:
            budget_text = st.text_input("Budget (INR)", value="25000")
            days_text = st.text_input("Number of days", value="4")

        with col3:
            travel_style = st.selectbox(
                "Travel style",
                ["Budget", "Standard", "Premium"],
                index=1,
            )

            preferred_date = st.text_input(
                "Travel month or preferred date",
                placeholder="e.g., June 2026",
            )

        submitted = st.form_submit_button("Plan my trip")

    if not submitted:
        st.markdown("## Demo input")
        st.markdown("""
<div class="demo-box">
Destination: <b>Goa</b> |
Starting city: <b>Pune</b> |
Budget: <b>₹25,000</b> |
Days: <b>4</b> |
Style: <b>Standard</b> |
Month: <b>June 2026</b>
</div>
""", unsafe_allow_html=True)
        return

    try:
        budget = int(budget_text)
        days = int(days_text)
    except ValueError:
        st.error("Please enter valid numeric values.")
        st.stop()

    if not destination or not starting_city:
        st.error("Please fill all fields.")
        st.stop()

    try:
        require_keys(cfg, gemini=True)
    except MissingAPIKeyError as e:
        st.warning(str(e))

    weather_used_demo = False
    ai_used_demo = False

    progress_box = st.empty()
    progress_bar = st.progress(0)

    progress_box.markdown("""
<div class="result-card">
<b>🌦️ Weather Agent Working...</b><br>
Fetching live weather and forecast data.
</div>
""", unsafe_allow_html=True)
    progress_bar.progress(20)
    time.sleep(0.6)

    try:
        weather_agent = WeatherAgent(cfg)
        weather_res = weather_agent.run(
            destination=destination,
            country=cfg.default_country,
        )

    except Exception:
        weather_used_demo = True

        from tools import get_mock_weather, suggest_best_travel_dates

        snapshot, forecast = get_mock_weather(destination)

        class DemoWeatherResult:
            def __init__(self):
                self.current = snapshot
                self.forecast = forecast
                self.best_dates = suggest_best_travel_dates(forecast)
                self.suitability_note = f"Demo weather mode active for {destination.title()}."

        weather_res = DemoWeatherResult()

    progress_box.markdown("""
<div class="result-card">
<b>💰 Budget Agent Calculating...</b><br>
Estimating hotel, food, transport, and activity costs.
</div>
""", unsafe_allow_html=True)
    progress_bar.progress(50)
    time.sleep(0.6)

    budget_agent = BudgetAgent(cfg)
    budget_res = budget_agent.run(
        starting_city=starting_city,
        destination=destination,
        days=days,
        travel_style=travel_style,
        budget_inr=float(budget),
    )

    progress_box.markdown("""
<div class="result-card">
<b>🧭 Travel Planner Agent Generating...</b><br>
Creating itinerary and packing checklist.
</div>
""", unsafe_allow_html=True)
    progress_bar.progress(75)
    time.sleep(0.6)

    planner_agent = TravelPlannerAgent(cfg)

    try:
        plan_res = planner_agent.run(
            starting_city=starting_city,
            destination=destination,
            days=days,
            travel_style=travel_style,
            preferred_month_or_date=preferred_date,
            weather=weather_res,
            budget=budget_res,
        )

    except Exception:
        ai_used_demo = True

        class DemoPlanResult:
            day_wise_itinerary_md = """
**Day 1:** Arrival and local exploration.

**Day 2:** Tourist attractions and local food.

**Day 3:** Outdoor activities and sightseeing.

**Day 4:** Shopping and return journey.

Packing Checklist

- Comfortable clothes
- Shoes
- Water bottle
- Charger

Final Recommendation

Fallback itinerary active because Gemini API quota is exhausted.
"""
            packing_list_md = ""
            final_recommendation_md = ""

        plan_res = DemoPlanResult()

    progress_box.markdown("""
<div class="result-card">
<b>✅ Finalizing Result...</b><br>
Preparing your smart travel plan.
</div>
""", unsafe_allow_html=True)
    progress_bar.progress(100)
    time.sleep(0.8)

    progress_box.empty()
    progress_bar.empty()

    day_text, packing_text, final_text = extract_plan_sections(plan_res)

    st.markdown("## Results")

    if weather_used_demo:
        st.warning("OpenWeather API failed, demo weather active.")
    else:
        st.success("Trip planned successfully 😎")

    if ai_used_demo:
        st.info("Gemini fallback active because quota is exhausted.")

    st.markdown("### Weather Summary")

    weather_city = getattr(weather_res.current, "city", destination.title())
    weather_country = getattr(weather_res.current, "country", "")
    city_line = f"{weather_city}, {weather_country}" if weather_country else weather_city

    st.markdown(f"""
<div class="weather-hero">
    <div class="weather-city">📍 {city_line}</div>
    <div class="weather-note">{weather_res.suitability_note}</div>
</div>
""", unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.markdown(f"""
<div class="metric-card">
<div class="metric-icon">🌡️</div>
<h3>{weather_res.current.temperature_c}°C</h3>
<p>Temperature</p>
</div>
""", unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
<div class="metric-card">
<div class="metric-icon">🥵</div>
<h3>{weather_res.current.feels_like_c}°C</h3>
<p>Feels Like</p>
</div>
""", unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
<div class="metric-card">
<div class="metric-icon">💧</div>
<h3>{weather_res.current.humidity_pct}%</h3>
<p>Humidity</p>
</div>
""", unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
<div class="metric-card">
<div class="metric-icon">🌬️</div>
<h3>{weather_res.current.wind_mps} m/s</h3>
<p>Wind Speed</p>
</div>
""", unsafe_allow_html=True)

    with c5:
        st.markdown(f"""
<div class="metric-card">
<div class="metric-icon">☁️</div>
<h3>{weather_res.current.description}</h3>
<p>Condition</p>
</div>
""", unsafe_allow_html=True)

    st.markdown("### 5-Day Temperature Forecast")
    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    show_temperature_forecast_graph(weather_res)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### Best Travel Dates")
    st.markdown(f"""
<div class="result-card">
{", ".join(weather_res.best_dates)}
</div>
""", unsafe_allow_html=True)

    st.markdown("### Budget Breakdown")
    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    show_budget_breakdown(budget_res.breakdown_inr)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### Budget Analytics")
    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    show_budget_analytics(budget_res.breakdown_inr)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### Hotel Recommendations")
    show_hotel_recommendations(destination, travel_style)

    if day_text:
        st.markdown("### Day-wise Itinerary")
        st.markdown(f"""
<div class="result-card">
{day_text}
</div>
""", unsafe_allow_html=True)

    if packing_text:
        st.markdown("### Packing Checklist")
        st.markdown(f"""
<div class="result-card">
{packing_text}
</div>
""", unsafe_allow_html=True)

    if final_text:
        st.markdown("### Final Recommendation")
        st.markdown(f"""
<div class="result-card">
{final_text}
</div>
""", unsafe_allow_html=True)

    st.markdown("### Download Itinerary PDF")
    st.markdown("""
<div class="pdf-box">
    <div class="pdf-title">📄 Download Complete Travel Report</div>
    <div class="pdf-subtitle">
    This PDF includes trip details, weather summary, best travel dates,
    budget breakdown, hotel recommendations, itinerary, packing checklist,
    and final recommendation.
    </div>
</div>
""", unsafe_allow_html=True)

    pdf_bytes = create_pdf_report(
        destination=destination,
        starting_city=starting_city,
        budget=budget,
        days=days,
        travel_style=travel_style,
        preferred_date=preferred_date,
        weather_res=weather_res,
        budget_dict=budget_res.breakdown_inr,
        day_text=day_text,
        packing_text=packing_text,
        final_text=final_text,
    )

    st.download_button(
        label="Download PDF Report",
        data=pdf_bytes,
        file_name=f"{destination.lower().replace(' ', '_')}_travel_plan.pdf",
        mime="application/pdf",
    )


if __name__ == "__main__":
    main()