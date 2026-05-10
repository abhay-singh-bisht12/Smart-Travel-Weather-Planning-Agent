from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any

import requests

from config import AppConfig


@dataclass(frozen=True)
class WeatherSnapshot:
    city: str
    country: str | None
    description: str
    temperature_c: float
    feels_like_c: float
    humidity_pct: int
    wind_mps: float
    rain_1h_mm: float | None


@dataclass(frozen=True)
class ForecastDay:
    date: str
    temp_min_c: float
    temp_max_c: float
    avg_humidity_pct: int
    rain_mm: float
    dominant_condition: str


class WeatherAPIError(RuntimeError):
    pass


class GeminiAPIError(RuntimeError):
    pass


class GroqAPIError(RuntimeError):
    pass


def _raise_for_status(resp: requests.Response) -> None:
    if resp.status_code >= 400:
        try:
            payload = resp.json()
        except Exception:
            payload = {"message": resp.text}

        raise WeatherAPIError(f"OpenWeather API error ({resp.status_code}): {payload}")


def fetch_current_weather(
    cfg: AppConfig,
    *,
    destination: str,
    country: str | None = None,
) -> WeatherSnapshot:
    q = destination.strip()

    if country:
        q = f"{q},{country.strip()}"

    url = f"{cfg.openweather_base_url}/weather"
    params = {
        "q": q,
        "appid": cfg.openweather_api_key,
        "units": "metric",
    }

    resp = requests.get(url, params=params, timeout=20)
    _raise_for_status(resp)

    data = resp.json()

    weather_desc = (data.get("weather") or [{}])[0].get("description", "unknown")
    main = data.get("main") or {}
    wind = data.get("wind") or {}
    rain = data.get("rain") or {}

    return WeatherSnapshot(
        city=(data.get("name") or destination).strip(),
        country=(data.get("sys") or {}).get("country"),
        description=str(weather_desc).title(),
        temperature_c=float(main.get("temp", 0.0)),
        feels_like_c=float(main.get("feels_like", 0.0)),
        humidity_pct=int(main.get("humidity", 0)),
        wind_mps=float(wind.get("speed", 0.0)),
        rain_1h_mm=float(rain.get("1h")) if "1h" in rain else None,
    )


def fetch_5day_forecast(
    cfg: AppConfig,
    *,
    destination: str,
    country: str | None = None,
) -> list[ForecastDay]:
    q = destination.strip()

    if country:
        q = f"{q},{country.strip()}"

    url = f"{cfg.openweather_base_url}/forecast"
    params = {
        "q": q,
        "appid": cfg.openweather_api_key,
        "units": "metric",
    }

    resp = requests.get(url, params=params, timeout=20)
    _raise_for_status(resp)

    data = resp.json()

    items: list[dict[str, Any]] = data.get("list") or []
    by_day: dict[str, list[dict[str, Any]]] = {}

    for it in items:
        stamp = it.get("dt_txt")
        if not stamp:
            continue

        day = str(stamp).split(" ")[0]
        by_day.setdefault(day, []).append(it)

    def safe_float(x: Any, default: float = 0.0) -> float:
        try:
            return float(x)
        except Exception:
            return default

    def safe_int(x: Any, default: int = 0) -> int:
        try:
            return int(round(float(x)))
        except Exception:
            return default

    days: list[ForecastDay] = []

    for day, slots in sorted(by_day.items()):
        temps = [safe_float((s.get("main") or {}).get("temp")) for s in slots]
        hums = [safe_int((s.get("main") or {}).get("humidity")) for s in slots]
        rain_mm = sum(
            safe_float(((s.get("rain") or {}).get("3h")), 0.0)
            for s in slots
        )

        conditions: dict[str, int] = {}

        for s in slots:
            desc = ((s.get("weather") or [{}])[0].get("main")) or "Unknown"
            conditions[str(desc)] = conditions.get(str(desc), 0) + 1

        dominant = max(conditions.items(), key=lambda kv: kv[1])[0] if conditions else "Unknown"

        tmin = min(temps) if temps else 0.0
        tmax = max(temps) if temps else 0.0
        avg_h = int(round(sum(hums) / max(len(hums), 1)))

        days.append(
            ForecastDay(
                date=day,
                temp_min_c=float(tmin),
                temp_max_c=float(tmax),
                avg_humidity_pct=avg_h,
                rain_mm=float(rain_mm),
                dominant_condition=str(dominant),
            )
        )

    return days


def get_mock_weather(destination: str) -> tuple[WeatherSnapshot, list[ForecastDay]]:
    today = dt.date.today()

    snapshot = WeatherSnapshot(
        city=destination.title(),
        country="IN",
        description="Partly Cloudy",
        temperature_c=28.0,
        feels_like_c=30.0,
        humidity_pct=68,
        wind_mps=3.5,
        rain_1h_mm=0.0,
    )

    forecast = [
        ForecastDay(
            date=(today + dt.timedelta(days=i)).isoformat(),
            temp_min_c=24.0 + i,
            temp_max_c=31.0 + i,
            avg_humidity_pct=65 + i,
            rain_mm=1.5 if i % 2 == 0 else 0.0,
            dominant_condition="Clouds" if i % 2 == 0 else "Clear",
        )
        for i in range(1, 6)
    ]

    return snapshot, forecast


def suggest_best_travel_dates(
    forecast: list[ForecastDay],
    *,
    max_suggestions: int = 3,
) -> list[str]:
    def score(d: ForecastDay) -> float:
        rain_penalty = min(d.rain_mm, 50.0) * 2.0
        mid = (d.temp_min_c + d.temp_max_c) / 2.0
        temp_penalty = abs(mid - 24.0) * 1.5
        humidity_penalty = max(0, d.avg_humidity_pct - 70) * 0.3
        return rain_penalty + temp_penalty + humidity_penalty

    ranked = sorted(forecast, key=score)
    return [d.date for d in ranked[:max_suggestions]]


def format_rupees(amount_in_inr: float) -> str:
    return f"₹{amount_in_inr:,.0f}"


def estimate_budget_inr(
    *,
    starting_city: str,
    destination: str,
    days: int,
    travel_style: str,
    user_budget_inr: float,
) -> dict[str, float]:
    style = travel_style.lower().strip()

    if style == "budget":
        hotel_per_night = 1200
        food_per_day = 500
        local_transport_per_day = 300
        activities_per_day = 400
        travel_base = 4000

    elif style == "premium":
        hotel_per_night = 4500
        food_per_day = 1500
        local_transport_per_day = 900
        activities_per_day = 1200
        travel_base = 10000

    else:
        hotel_per_night = 2500
        food_per_day = 900
        local_transport_per_day = 600
        activities_per_day = 700
        travel_base = 6500

    length_factor = 1.0 if days <= 3 else 0.95 if days <= 6 else 0.92

    travel = travel_base
    hotel = hotel_per_night * max(days - 1, 1) * length_factor
    food = food_per_day * days * length_factor
    local_transport = local_transport_per_day * days * length_factor
    activities = activities_per_day * days * length_factor

    total = travel + hotel + food + local_transport + activities

    return {
        "Travel (round-trip)": float(travel),
        "Hotel": float(hotel),
        "Food": float(food),
        "Local transport": float(local_transport),
        "Activities": float(activities),
        "Estimated total": float(total),
        "User budget": float(user_budget_inr),
    }


def groq_generate_text(cfg: AppConfig, *, prompt: str) -> str:
    if not getattr(cfg, "groq_api_key", ""):
        raise GroqAPIError("GROQ_API_KEY missing")

    try:
        from groq import Groq

        client = Groq(api_key=cfg.groq_api_key)

        model_name = getattr(cfg, "groq_model", "llama-3.1-8b-instant")

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a smart travel planning assistant for an Indian student project. "
                        "Give practical, clean, markdown-formatted travel answers."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.7,
            max_tokens=1400,
        )

        text = response.choices[0].message.content

        if text:
            return str(text).strip()

        raise GroqAPIError("Groq returned empty response")

    except Exception as e:
        raise GroqAPIError(str(e))


def _static_safe_fallback() -> str:
    return """
**Day 1:** Arrival, hotel check-in, local sightseeing, and evening food exploration.

**Day 2:** Visit main tourist attractions, enjoy local activities, and explore nearby markets.

**Day 3:** Weather-friendly outdoor plan, photography spots, cultural places, and relaxed cafe time.

**Day 4:** Shopping, packing, final local visit, and return travel.

Packing Checklist

- Comfortable clothes
- Walking shoes
- Umbrella or raincoat
- Sunglasses
- Water bottle
- Power bank
- ID proof
- Basic medicines

Final Recommendation

AI response is temporarily unavailable, so safe fallback itinerary is active. The app is working without crashing.
"""


def gemini_generate_text(cfg: AppConfig, *, prompt: str) -> str:
    gemini_error = ""

    try:
        if not getattr(cfg, "gemini_api_key", ""):
            raise GeminiAPIError("GEMINI_API_KEY missing")

        from google import genai  # type: ignore

        client = genai.Client(api_key=cfg.gemini_api_key)

        models_to_try = [
            getattr(cfg, "gemini_model", "gemini-1.5-flash"),
            "gemini-1.5-flash-latest",
            "gemini-1.5-flash-8b-latest",
            "gemini-2.0-flash-lite",
            "gemini-2.0-flash",
        ]

        for model_name in models_to_try:
            try:
                res = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )

                text = getattr(res, "text", None)

                if text:
                    return str(text).strip()

            except Exception as e:
                gemini_error = str(e)
                continue

        raise GeminiAPIError(gemini_error or "Gemini returned empty response")

    except Exception as e:
        gemini_error = str(e)
        print("Gemini failed. Switching to Groq fallback:", gemini_error)

        try:
            return groq_generate_text(cfg, prompt=prompt)

        except Exception as groq_error:
            print("Groq fallback also failed:", groq_error)
            return _static_safe_fallback()