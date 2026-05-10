# Smart Travel & Weather Planning Agent (Streamlit + Gemini + OpenWeather)

An AI-powered travel planning app where you enter a destination, budget, number of days, travel month/date preference, and starting city.  
The app fetches **real-time weather**, suggests **best travel dates**, generates a **day-wise itinerary**, estimates **total travel cost**, and recommends a **packing list**.

## Features

- **Streamlit GUI** with modern, presentation-ready UI
- **Real-time weather** (OpenWeather)
- **5-day forecast summary** + **best travel date suggestion**
- **Budget breakdown** in **Indian Rupees (INR)**
- **Day-wise itinerary** (Gemini)
- **Packing checklist** (Gemini, weather-aware)
- **Final AI recommendation**
- **Spinner/loading state** while agents are working
- **Error handling** for missing API keys and weather API failures

## Tech Stack

- Python
- Streamlit
- OpenWeather API (real-time + 5-day forecast)
- Google Gemini API via the official `google-genai` package
- LangChain + CrewAI are included in dependencies (the app uses a clean, beginner-friendly “agent class” structure; CrewAI wrapper is optional)
- `python-dotenv` for environment variables

## Project Structure

```
smart_travel_agent/
│── app.py
│── agents.py
│── tools.py
│── config.py
│── requirements.txt
│── .env.example
│── .gitignore
│── README.md
```

## Setup (Windows / macOS / Linux)

### 1) Create and activate a virtual environment (recommended)

```bash
python -m venv venv
```

- **Windows (PowerShell):**

```bash
venv\Scripts\Activate.ps1
```

- **macOS/Linux:**

```bash
source venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Add API keys in a `.env` file

Create a new file named `.env` inside `smart_travel_agent/` (same folder as `app.py`).

`.env` structure:

```bash
OPENWEATHER_API_KEY="YOUR_OPENWEATHER_KEY"
GEMINI_API_KEY="YOUR_GEMINI_KEY"

# Optional
DEFAULT_CURRENCY="INR"
DEFAULT_COUNTRY="IN"
GEMINI_MODEL="gemini-2.0-flash"
```

You can copy from `.env.example`.

### 4) Run the app

From inside the `smart_travel_agent/` folder:

```bash
streamlit run app.py
```

## Demo Input (for college presentation)

- **Destination**: Goa  
- **Starting city**: Pune  
- **Budget (INR)**: 25000  
- **Number of days**: 4  
- **Travel style**: Standard  
- **Travel month/date**: June 2026  

## Expected Output (what you’ll see)

- A **Weather card** showing:
  - temperature, feels-like, humidity, wind, rain (if available)
- **Best travel date suggestion** (top 2–3 dates from forecast)
- **Day-wise itinerary** with:
  - Morning / Afternoon / Evening plan
  - local transport tip + food suggestion per day
- **Estimated cost table** in INR (travel, hotel, food, local transport, activities, total)
- **Packing checklist** (weather-aware)
- **Final recommendation** (safety + budget + weather tips)

## Notes / Limitations (Demo-friendly)

- The budget numbers are **estimates** (not live booking prices).
- Date suggestions are based on the **OpenWeather 5-day forecast**. For long-month planning, the app still uses Gemini + current conditions and gives best-effort guidance.

## Troubleshooting

- **“Missing required API key(s)”**  
  Add `OPENWEATHER_API_KEY` and `GEMINI_API_KEY` to your `.env`.

- **Weather API failed**  
  Check destination spelling (try “Goa,IN”), verify your OpenWeather key, and ensure your internet is working.

## Credits

Built as a clean, beginner-friendly AI project for demos using Streamlit + Gemini + OpenWeather.

