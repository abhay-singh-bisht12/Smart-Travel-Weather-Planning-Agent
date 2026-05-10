from __future__ import annotations

from dataclasses import dataclass

from config import AppConfig
from tools import (
    WeatherSnapshot,
    ForecastDay,
    estimate_budget_inr,
    fetch_5day_forecast,
    fetch_current_weather,
    gemini_generate_text,
    suggest_best_travel_dates,
)


@dataclass(frozen=True)
class WeatherAgentResult:
    current: WeatherSnapshot
    forecast: list[ForecastDay]
    best_dates: list[str]
    suitability_note: str


class WeatherAgent:
    """Weather Agent: real-time weather + forecast-based date suggestions."""

    def __init__(self, cfg: AppConfig):
        self.cfg = cfg

    def run(self, *, destination: str, country: str | None = None) -> WeatherAgentResult:
        current = fetch_current_weather(self.cfg, destination=destination, country=country)
        forecast = fetch_5day_forecast(self.cfg, destination=destination, country=country)
        best_dates = suggest_best_travel_dates(forecast, max_suggestions=3) if forecast else []

        note_bits: list[str] = []

        if current.rain_1h_mm and current.rain_1h_mm >= 2:
            note_bits.append("It’s currently rainy—carry a raincoat/umbrella and prefer indoor attractions.")

        if current.humidity_pct >= 80:
            note_bits.append("Humidity is high—stay hydrated and plan lighter outdoor activities mid-day.")

        if current.temperature_c >= 35:
            note_bits.append("It’s quite hot—avoid afternoon outdoor travel and use sunscreen.")

        if current.temperature_c <= 10:
            note_bits.append("It’s cold—pack warm layers and plan more indoor stops.")

        if not note_bits:
            note_bits.append("Weather looks generally suitable for travel with normal precautions.")

        return WeatherAgentResult(
            current=current,
            forecast=forecast,
            best_dates=best_dates,
            suitability_note=" ".join(note_bits),
        )


@dataclass(frozen=True)
class BudgetAgentResult:
    breakdown_inr: dict[str, float]
    warning: str | None
    cheaper_alternatives: str | None


class BudgetAgent:
    """Budget Agent: estimate trip cost and warn if budget is low."""

    def __init__(self, cfg: AppConfig):
        self.cfg = cfg

    def run(
        self,
        *,
        starting_city: str,
        destination: str,
        days: int,
        travel_style: str,
        budget_inr: float,
    ) -> BudgetAgentResult:
        breakdown = estimate_budget_inr(
            starting_city=starting_city,
            destination=destination,
            days=days,
            travel_style=travel_style,
            user_budget_inr=budget_inr,
        )

        total = breakdown.get("Estimated total", 0.0)

        warning = None
        cheaper = None

        if budget_inr < total:
            warning = (
                f"Your budget looks low for this plan. Estimated total is about ₹{total:,.0f}, "
                f"but your budget is ₹{budget_inr:,.0f}."
            )

            prompt = f"""
You are a budget travel advisor for Indian travelers.

Suggest 5 concrete ways to reduce trip cost for:
- Starting city: {starting_city}
- Destination: {destination}
- Days: {days}
- Travel style: {travel_style}
- Budget (INR): {budget_inr}
- Estimated total (INR): {total}

Rules:
- Keep it realistic and actionable.
- Mention cheaper alternatives for stays, local transport, and activities.
- Output as short bullet points.
"""

            try:
                cheaper = gemini_generate_text(self.cfg, prompt=prompt)
            except Exception:
                cheaper = None

        return BudgetAgentResult(
            breakdown_inr=breakdown,
            warning=warning,
            cheaper_alternatives=cheaper,
        )


@dataclass(frozen=True)
class PlannerAgentResult:
    best_time_to_travel: str
    day_wise_itinerary_md: str
    packing_list_md: str
    final_recommendation_md: str


class TravelPlannerAgent:
    """Travel Planner Agent: itinerary + packing list + final recommendation."""

    def __init__(self, cfg: AppConfig):
        self.cfg = cfg

    def run(
        self,
        *,
        starting_city: str,
        destination: str,
        days: int,
        travel_style: str,
        preferred_month_or_date: str,
        weather: WeatherAgentResult,
        budget: BudgetAgentResult,
    ) -> PlannerAgentResult:
        best_dates_text = ", ".join(weather.best_dates) if weather.best_dates else "N/A (forecast not available)"

        prompt = f"""
You are an AI travel planner.
Create a practical, budget-aware travel plan for an Indian student demo app.

Trip inputs:
- Starting city: {starting_city}
- Destination: {destination}
- Days: {days}
- Travel style: {travel_style}
- Preferred month/date: {preferred_month_or_date}

Weather snapshot:
- Condition: {weather.current.description}
- Temperature: {weather.current.temperature_c}°C (feels like {weather.current.feels_like_c}°C)
- Humidity: {weather.current.humidity_pct}%
- Wind: {weather.current.wind_mps} m/s
- Rain (1h): {weather.current.rain_1h_mm if weather.current.rain_1h_mm is not None else "not reported"} mm
- Best suggested dates (from forecast): {best_dates_text}
- Suitability note: {weather.suitability_note}

Budget:
- User budget (INR): {budget.breakdown_inr.get("User budget", 0)}
- Estimated total (INR): {budget.breakdown_inr.get("Estimated total", 0)}
- Notes: {budget.warning or "Within budget (estimated)."}

Output format IMPORTANT:
1) Best travel window: 2-3 lines.
2) Day-wise itinerary in Markdown with headings:
   - Day 1, Day 2, ... Day {days}
   - Each day: Morning / Afternoon / Evening + local transport tip + food suggestion.
   - Keep it realistic.
3) Packing list in Markdown checklist:
   - Essentials, Clothing, Weather-based items, Documents, Health.
4) Final recommendation in Markdown:
   - 4-6 bullet points including safety, budget, and weather advice.
"""

        text = gemini_generate_text(self.cfg, prompt=prompt)

        best_time = "Suggested dates: " + (best_dates_text or "N/A")
        itinerary = text
        packing = ""
        final_rec = ""

        lower = text.lower()

        if "packing" in lower and "itinerary" in lower:
            parts = text.split("2)", 1)

            if len(parts) == 2:
                best_time = parts[0].strip()
                rest = "2)" + parts[1]
            else:
                rest = text

            it_split = rest.split("3)", 1)

            if len(it_split) == 2:
                itinerary = it_split[0].strip()
                rest2 = "3)" + it_split[1]

                pack_split = rest2.split("4)", 1)

                if len(pack_split) == 2:
                    packing = pack_split[0].strip()
                    final_rec = ("4)" + pack_split[1]).strip()
                else:
                    packing = rest2.strip()
            else:
                itinerary = rest.strip()

        return PlannerAgentResult(
            best_time_to_travel=best_time.strip(),
            day_wise_itinerary_md=itinerary.strip(),
            packing_list_md=packing.strip(),
            final_recommendation_md=final_rec.strip(),
        )


def crewai_available() -> bool:
    try:
        import crewai  # noqa: F401
        return True
    except Exception:
        return False