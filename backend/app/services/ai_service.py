"""
CarbonTrack — AI Service.
Integrates with Groq to personalized daily challenges based on templates,
and provides a sustainability chatbot restricted to relevant topics.
"""
import json
import logging
from typing import List, Dict, Any, Optional
from groq import AsyncGroq

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ─── Challenge Templates ──────────────────────────────────────────

CHALLENGE_TEMPLATES = {
    "transit-trips": {
        "slug": "transit-trips",
        "title": "Ride Public Transit",
        "description_template": "Take the bus, metro, or train instead of driving for {n} trips.",
        "difficulty_formula": lambda n: "easy" if n <= 2 else ("medium" if n <= 5 else "hard"),
        "co2_saved_formula": lambda n: float(round(n * 5.0, 2)),
        "xp_formula": lambda n: int(n * 15),
        "default_n": 3,
        "max_n": 20,
    },
    "meatless-meals": {
        "slug": "meatless-meals",
        "title": "Meat-Free Eating",
        "description_template": "Eat vegetarian or vegan meals for {n} meals this week.",
        "difficulty_formula": lambda n: "easy" if n <= 3 else ("medium" if n <= 7 else "hard"),
        "co2_saved_formula": lambda n: float(round(n * 1.5, 2)),
        "xp_formula": lambda n: int(n * 10),
        "default_n": 5,
        "max_n": 21,
    },
    "reduce-ac": {
        "slug": "reduce-ac",
        "title": "Cooler Comfort",
        "description_template": "Reduce air conditioning or heating run-time by {n} hours.",
        "difficulty_formula": lambda n: "easy" if n <= 4 else ("medium" if n <= 10 else "hard"),
        "co2_saved_formula": lambda n: float(round(n * 0.8, 2)),
        "xp_formula": lambda n: int(n * 8),
        "default_n": 6,
        "max_n": 24,
    },
    "reusable-bottle": {
        "slug": "reusable-bottle",
        "title": "Hydration Station",
        "description_template": "Use a reusable water bottle or coffee cup {n} times.",
        "difficulty_formula": lambda n: "easy" if n <= 3 else ("medium" if n <= 5 else "hard"),
        "co2_saved_formula": lambda n: float(round(n * 0.2, 2)),
        "xp_formula": lambda n: int(n * 5),
        "default_n": 5,
        "max_n": 10,
    }
}


class AIService:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        if self.api_key:
            self.client = AsyncGroq(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("GROQ_API_KEY is not set. AIService will run in fallback mode.")

    def get_fallback_challenges(self) -> List[Dict[str, Any]]:
        """Generates default challenges if Groq is unavailable or fails."""
        defaults = ["transit-trips", "meatless-meals"]
        results = []
        for slug in defaults:
            template = CHALLENGE_TEMPLATES[slug]
            n = template["default_n"]
            desc = template["description_template"].format(n=n)
            diff = template["difficulty_formula"](n)
            co2 = template["co2_saved_formula"](n)
            xp = template["xp_formula"](n)
            results.append({
                "title": template["title"],
                "description": f"{desc} Recommended for you.",
                "challenge_type": "daily",
                "template_slug": slug,
                "difficulty": diff,
                "co2_saved_estimate_kg": co2,
                "xp_reward": xp,
                "is_active": True,
            })
        return results

    async def generate_challenges(
        self,
        user_id: str,
        recent_footprint: Dict[str, float],
        habit_completions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Calls Groq to select 1-3 challenge templates and customize the 'n' parameter.
        Uses JSON mode and validates the structure. Falls back to static defaults if anything fails.
        """
        if not self.client:
            return self.get_fallback_challenges()

        # Construct context for user footprint
        footprint_summary = (
            f"Transportation emissions: {recent_footprint.get('transport', 0.0):.1f} kg CO2.\n"
            f"Energy emissions: {recent_footprint.get('energy', 0.0):.1f} kg CO2.\n"
            f"Food emissions: {recent_footprint.get('food', 0.0):.1f} kg CO2.\n"
            f"Shopping emissions: {recent_footprint.get('shopping', 0.0):.1f} kg CO2."
        )

        # Construct context for user habits
        habit_summary = ""
        for h in habit_completions:
            habit_summary += f"- Habit '{h.get('slug')}': logged {h.get('logged_days')} days in range.\n"
        if not habit_summary:
            habit_summary = "No recent eco habits logged."

        system_prompt = (
            "You are a helpful carbon footprint coach. You must output a JSON object containing "
            "personalized daily sustainability challenges for a user based on their carbon footprint and habit logs.\n\n"
            "You must choose between 1 to 3 challenge templates from this list and fill their 'n' parameter:\n"
            "1. 'transit-trips': Walk/bike/bus instead of driving. Choose 'n' between 1 and 20 (number of trips).\n"
            "2. 'meatless-meals': Eat vegetarian/vegan meals. Choose 'n' between 1 and 21 (number of meals).\n"
            "3. 'reduce-ac': Turn off air conditioning or heater. Choose 'n' between 1 and 24 (number of hours).\n"
            "4. 'reusable-bottle': Avoid single-use cups/bottles. Choose 'n' between 1 and 10 (number of days).\n\n"
            "Select templates that target their highest carbon areas or where they have logged fewer habits. "
            "Choose a realistic, achievable 'n' difficulty value based on their current profile (don't make it too high or low).\n\n"
            "Your output must follow this JSON schema exactly:\n"
            "{\n"
            "  \"challenges\": [\n"
            "    {\n"
            "      \"template_slug\": \"string (must be one of the 4 slugs above)\",\n"
            "      \"n\": integer (must be a positive integer within the allowed bounds for the template),\n"
            "      \"personalized_blurb\": \"string (1-2 sentences explaining why this challenge was picked and how it helps)\"\n"
            "    }\n"
            "  ]\n"
            "}\n"
        )

        user_prompt = (
            f"User Footprint Data:\n{footprint_summary}\n\n"
            f"User Habit Completion Log:\n{habit_summary}\n\n"
            "Generate 1 to 3 daily challenges now."
        )

        try:
            chat_completion = await self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
            )
            response_text = chat_completion.choices[0].message.content
            parsed = json.loads(response_text)
            
            challenges_list = parsed.get("challenges", [])
            if not isinstance(challenges_list, list) or len(challenges_list) == 0:
                raise ValueError("Parsed challenges is empty or not a list")

            generated = []
            for item in challenges_list:
                slug = item.get("template_slug")
                n_val = item.get("n")
                blurb = item.get("personalized_blurb", "")

                # Validate template slug
                if slug not in CHALLENGE_TEMPLATES:
                    continue

                template = CHALLENGE_TEMPLATES[slug]

                # Validate and clamp n parameter
                try:
                    n = int(n_val)
                    if n <= 0:
                        n = template["default_n"]
                    elif n > template["max_n"]:
                        n = template["max_n"]
                except Exception:
                    n = template["default_n"]

                # Fill details
                desc = template["description_template"].format(n=n)
                full_desc = f"{desc} {blurb}".strip()
                diff = template["difficulty_formula"](n)
                co2 = template["co2_saved_formula"](n)
                xp = template["xp_formula"](n)

                generated.append({
                    "title": template["title"],
                    "description": full_desc,
                    "challenge_type": "daily",
                    "template_slug": slug,
                    "difficulty": diff,
                    "co2_saved_estimate_kg": co2,
                    "xp_reward": xp,
                    "is_active": True,
                })

            if not generated:
                return self.get_fallback_challenges()

            return generated

        except Exception as e:
            logger.error(f"Error calling Groq for challenges generation: {e}", exc_info=True)
            return self.get_fallback_challenges()

    async def chat_sustainability(self, message: str, chat_history: List[Dict[str, str]]) -> str:
        """
        Accepts a user message and context history, calls Groq to respond to sustainability topics.
        Strictly enforces refusal/redirection on medical, legal, and financial queries,
        and enforces metric hedging to prevent hallucinated precise stats.
        """
        if not self.client:
            return (
                "Hi! I'm sorry, but my AI service is currently offline. "
                "Please make sure your GROQ_API_KEY is configured so we can chat about sustainability!"
            )

        system_prompt = (
            "You are CarbonTrack's Sustainability Chatbot. "
            "You must answer questions strictly related to carbon footprints, climate change, recycling, "
            "sustainability, green living, and eco-friendly habits.\n\n"
            "If the user asks for legal, medical, or financial advice (even if it claims to be green-related, "
            "like green investment funds advice, health concerns about pollution, or environmental regulations compliance advice), "
            "you must refuse to answer. Re-direct the conversation back to general sustainability topics, "
            "for example: 'I can only provide guidance on carbon footprint reductions and daily eco-friendly habits. "
            "For legal/medical/financial issues, please consult a certified professional.'\n\n"
            "For any metrics, figures, or statistics: do not state unverified details as exact fact. "
            "Always hedge your numbers using terms like 'estimated at,' 'approximately,' 'roughly,' or 'around' "
            "to reflect that these are estimates rather than precise calculations, unless quoting a well-known standard "
            "(like the carbon intensity of an average car being around 0.18 kg CO2/km)."
        )

        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent chat history (capped to last 10 messages to save token context)
        for h in chat_history[-10:]:
            role = h.get("role", "user")
            content = h.get("content", "")
            if role in ("user", "assistant"):
                messages.append({"role": role, "content": content})

        # Add current user message
        messages.append({"role": "user", "content": message})

        try:
            chat_completion = await self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.5,
                max_tokens=800,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Error calling Groq for chatbot: {e}", exc_info=True)
            return "I'm sorry, I encountered an issue processing your message. Please try again in a moment!"
