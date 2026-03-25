"""
Meal photo nutrition analysis service.

Sends a meal photo to Claude Vision and returns a structured nutrition estimate
for the user to confirm before logging.
"""
import base64
import json
import logging
from pathlib import Path

import anthropic

from app.config import settings
from app.models.nutrition_log import MealType
from app.schemas.health import MealAnalysis

logger = logging.getLogger(__name__)

NUTRITION_ANALYSIS_PROMPT = """You are a nutrition expert analysing a meal photo.

Identify all food items visible, estimate portion sizes, and calculate the nutritional content.

Return a JSON object in this exact format:

{
  "description": "Brief description of what you see e.g. 'Grilled chicken breast with roasted sweet potato and green salad'",
  "meal_type": one of: "breakfast", "lunch", "dinner", "snack", "other",
  "calories": estimated total calories as integer,
  "protein_g": total protein in grams as float,
  "fat_g": total fat in grams as float,
  "carbs_net_g": total net carbs (total carbs minus fibre) in grams as float,
  "fibre_g": total dietary fibre in grams as float,
  "omega3_g": estimated omega-3 (EPA+DHA) in grams as float — 0 if no fish/seafood/flaxseed,
  "confidence": "high" if you can clearly see the meal, "medium" if partially obscured or mixed dish, "low" if unclear,
  "notes": "Any caveats about the estimate — e.g. 'Portion size of pasta difficult to assess' or null"
}

Rules:
- Be realistic with portions — don't underestimate
- If you cannot confidently see the food, say so in confidence and notes
- Return ONLY the JSON object, no other text"""


async def analyse_meal_photo(image_path: str) -> MealAnalysis:
    """
    Analyse a meal photo using Claude Vision.

    Args:
        image_path: Local filesystem path to the image file.

    Returns:
        MealAnalysis with nutrition estimates for user confirmation.
    """
    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    image_bytes = Path(image_path).read_bytes()
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    # Detect media type from extension
    ext = Path(image_path).suffix.lower()
    media_type_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    media_type = media_type_map.get(ext, "image/jpeg")

    logger.info(f"Sending meal photo to Claude Vision: {image_path} ({len(image_bytes)} bytes)")

    response = await client.messages.create(
        model=settings.LLM_MODEL,
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": NUTRITION_ANALYSIS_PROMPT,
                    },
                ],
            }
        ],
    )

    raw = response.content[0].text.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    data = json.loads(raw)

    meal_type_str = data.get("meal_type", "other")
    try:
        meal_type = MealType(meal_type_str)
    except ValueError:
        meal_type = MealType.OTHER

    return MealAnalysis(
        description=data.get("description", ""),
        meal_type=meal_type,
        calories=data.get("calories"),
        protein_g=data.get("protein_g"),
        fat_g=data.get("fat_g"),
        carbs_net_g=data.get("carbs_net_g"),
        fibre_g=data.get("fibre_g"),
        omega3_g=data.get("omega3_g"),
        confidence=data.get("confidence", "medium"),
        notes=data.get("notes"),
    )


async def analyse_meal_from_bytes(image_bytes: bytes, media_type: str = "image/jpeg") -> MealAnalysis:
    """
    Analyse a meal photo from raw bytes (e.g. from a multipart upload).
    """
    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    response = await client.messages.create(
        model=settings.LLM_MODEL,
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": NUTRITION_ANALYSIS_PROMPT,
                    },
                ],
            }
        ],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    data = json.loads(raw)

    meal_type_str = data.get("meal_type", "other")
    try:
        meal_type = MealType(meal_type_str)
    except ValueError:
        meal_type = MealType.OTHER

    return MealAnalysis(
        description=data.get("description", ""),
        meal_type=meal_type,
        calories=data.get("calories"),
        protein_g=data.get("protein_g"),
        fat_g=data.get("fat_g"),
        carbs_net_g=data.get("carbs_net_g"),
        fibre_g=data.get("fibre_g"),
        omega3_g=data.get("omega3_g"),
        confidence=data.get("confidence", "medium"),
        notes=data.get("notes"),
    )
