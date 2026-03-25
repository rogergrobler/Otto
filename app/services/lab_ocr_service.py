"""
Lab PDF OCR pipeline.

Sends a lab report PDF to Claude Vision, extracts structured biomarker data,
and returns a LabOCRResult for the user to confirm before saving.
"""
import base64
import json
import logging
from datetime import date
from pathlib import Path

import anthropic

from app.config import settings
from app.schemas.health import LabOCRResult, LabResultCreate

logger = logging.getLogger(__name__)

LAB_OCR_PROMPT = """You are a medical lab report parser. You will be given a lab report PDF rendered as an image or text.

Extract ALL biomarker results and return a JSON object in this exact format:

{
  "lab_name": "string or null",
  "test_date": "YYYY-MM-DD or null",
  "markers": [
    {
      "marker_name": "full marker name as shown on report",
      "value": numeric value as float or null if non-numeric,
      "value_text": "raw text value if non-numeric e.g. 'Positive' or null",
      "unit": "unit string e.g. 'mmol/L' or null",
      "ref_range_low": numeric lower reference range or null,
      "ref_range_high": numeric upper reference range or null,
      "optimal_low": null,
      "optimal_high": null,
      "flag": one of: "optimal", "normal", "borderline", "high", "low", "critical_high", "critical_low" — based on lab's flag or your assessment of where the value falls vs reference range; null if unknown,
      "test_date": "YYYY-MM-DD" — use the report date if individual marker date not shown,
      "lab_name": null,
      "notes": "any relevant clinical note on this marker or null"
    }
  ]
}

Rules:
- Extract every single result, even if flagged or abnormal
- Use the exact marker name from the report (e.g. "LDL Cholesterol", "HbA1c", "eGFR")
- Convert all values to floats where possible
- For reference ranges like "< 5.7" set ref_range_high=5.7 and ref_range_low=null
- For ranges like "3.5 - 5.0" set ref_range_low=3.5, ref_range_high=5.0
- If the lab has flagged a result as High/Low/Critical, use that for the flag field
- Return ONLY the JSON object, no other text"""


async def extract_labs_from_pdf(pdf_path: str) -> LabOCRResult:
    """
    Extract lab results from a PDF file using Claude Vision.

    Args:
        pdf_path: Local filesystem path to the PDF file.

    Returns:
        LabOCRResult with extracted markers for user confirmation.
    """
    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    pdf_bytes = Path(pdf_path).read_bytes()
    pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")

    logger.info(f"Sending lab PDF to Claude OCR: {pdf_path} ({len(pdf_bytes)} bytes)")

    response = await client.messages.create(
        model=settings.LLM_MODEL,
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": LAB_OCR_PROMPT,
                    },
                ],
            }
        ],
    )

    raw = response.content[0].text.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    data = json.loads(raw)

    test_date_str = data.get("test_date")
    test_date = date.fromisoformat(test_date_str) if test_date_str else None

    markers = []
    for m in data.get("markers", []):
        # Ensure test_date falls back to report-level date
        marker_date_str = m.get("test_date") or test_date_str
        marker_date = date.fromisoformat(marker_date_str) if marker_date_str else date.today()

        markers.append(
            LabResultCreate(
                marker_name=m.get("marker_name", "Unknown"),
                value=m.get("value"),
                value_text=m.get("value_text"),
                unit=m.get("unit"),
                ref_range_low=m.get("ref_range_low"),
                ref_range_high=m.get("ref_range_high"),
                optimal_low=m.get("optimal_low"),
                optimal_high=m.get("optimal_high"),
                flag=m.get("flag"),
                test_date=marker_date,
                lab_name=data.get("lab_name"),
                notes=m.get("notes"),
            )
        )

    logger.info(f"Extracted {len(markers)} markers from lab PDF")
    return LabOCRResult(
        lab_name=data.get("lab_name"),
        test_date=test_date,
        markers=markers,
    )
