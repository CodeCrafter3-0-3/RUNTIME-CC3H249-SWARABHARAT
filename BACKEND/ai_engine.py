import os
import json
import time
import threading
from datetime import date
from pathlib import Path
# import telemetry without causing circular imports
try:
    from telemetry import increment as telemetry_increment
except Exception:
    telemetry_increment = None
import re
import requests
from typing import List, Optional
from dotenv import load_dotenv

"""
AI Engine
- Pluggable provider via env: OPENAI (default) or HUGGINGFACE.
- Robust JSON extraction and validation.
- Safe fallbacks to deterministic output when APIs are unavailable.
"""

load_dotenv()

# Try to import OpenAI client if available (new SDK)
try:
    from openai import OpenAI
    _HAS_OPENAI = True
except Exception:
    OpenAI = None
    _HAS_OPENAI = False

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai").lower()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
HF_DEFAULT_MODEL = os.getenv("HF_MODEL", "bigscience/bloomz-1b1")


def _parse_model_list(raw_value: Optional[str], defaults: List[str]) -> List[str]:
    """Parse comma-separated model names and keep unique, non-empty values."""
    items = []
    if raw_value:
        items.extend([part.strip() for part in raw_value.split(",")])
    items.extend(defaults)

    unique = []
    seen = set()
    for item in items:
        if not item:
            continue
        lowered = item.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        unique.append(item)
    return unique


OPENAI_MODELS = _parse_model_list(
    os.getenv("OPENAI_MODELS"),
    [OPENAI_MODEL, "gpt-4.1-mini", "gpt-4o-mini"]
)
HF_MODELS = _parse_model_list(
    os.getenv("HF_MODELS"),
    [HF_DEFAULT_MODEL, "google/flan-t5-base", "mistralai/Mistral-7B-Instruct-v0.2"]
)

client: Optional[OpenAI] = None
if AI_PROVIDER == "openai" and OPENAI_API_KEY and _HAS_OPENAI:
    client = OpenAI(api_key=OPENAI_API_KEY)

# -------------------------
# Simple quota management
# -------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
QUOTA_FILE = os.path.join(DATA_DIR, 'ai_quota.json')
_quota_lock = threading.Lock()

MAX_DAILY = int(os.getenv('MAX_DAILY_REQUESTS', '1000'))
MAX_PER_MINUTE = int(os.getenv('MAX_REQUESTS_PER_MINUTE', '60'))

def _load_quota():
    try:
        if os.path.exists(QUOTA_FILE):
            with open(QUOTA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    # default structure
    return {"daily": {"date": str(date.today()), "count": 0}, "minute": {"start": int(time.time()), "count": 0}}

def _save_quota(q):
    try:
        with open(QUOTA_FILE + '.tmp', 'w', encoding='utf-8') as f:
            json.dump(q, f)
        os.replace(QUOTA_FILE + '.tmp', QUOTA_FILE)
    except Exception:
        pass

def check_and_increment_quota():
    """Return True if request allowed; increments counters on success."""
    now = int(time.time())
    with _quota_lock:
        q = _load_quota()
        # daily
        if q.get('daily', {}).get('date') != str(date.today()):
            q['daily'] = {'date': str(date.today()), 'count': 0}
        # minute window
        window_start = q.get('minute', {}).get('start', now)
        if now - int(window_start) >= 60:
            q['minute'] = {'start': now, 'count': 0}

        # check
        if q['daily']['count'] >= MAX_DAILY or q['minute']['count'] >= MAX_PER_MINUTE:
            _save_quota(q)
            return False

        # increment
        q['daily']['count'] += 1
        q['minute']['count'] += 1
        _save_quota(q)
        # telemetry
        try:
            if telemetry_increment:
                telemetry_increment('ai_calls', 1)
        except Exception:
            pass
        return True

def get_quota_status():
    q = _load_quota()
    return {
        'daily_date': q.get('daily', {}).get('date'),
        'daily_count': q.get('daily', {}).get('count', 0),
        'daily_limit': MAX_DAILY,
        'minute_count': q.get('minute', {}).get('count', 0),
        'minute_limit': MAX_PER_MINUTE
    }

# Allowed values (hard constraints)
ISSUES = ["Water", "Health", "Food", "Education", "Safety", "Employment", "Accident", "Other"]
EMOTIONS = ["Calm", "Distress", "Anger", "Fear", "Hope"]
URGENCY = ["Low", "Medium", "High"]

SYSTEM_PROMPT = """
You are an AI civic intelligence system for India.

Your job:
- Understand citizen problems in ANY language or dialect
- Convert them into structured, anonymized insights
- NEVER include personal data
- Be neutral, factual, and empathetic

You MUST return STRICT JSON only.
"""


def build_prompt(message: str) -> str:
    return f"""
Analyze the citizen message below.

Return ONLY valid JSON with these exact keys:
- issue (one of: {ISSUES})
- emotion (one of: {EMOTIONS})
- urgency (one of: {URGENCY})
- summary (one short English sentence)

Citizen message:
{message}

Rules:
- Do NOT explain
- Do NOT add extra text
- Do NOT include names or locations
- If unsure, choose "Other" issue and "Medium" urgency
"""


def safe_json_load(text: str):
    try:
        return json.loads(text)
    except Exception:
        # Attempt to extract JSON substring if model wrapped it in text
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
        return None


def _match_model_name(model_hint: Optional[str], candidates: List[str]) -> Optional[str]:
    if not model_hint:
        return None
    wanted = model_hint.strip().lower()
    for candidate in candidates:
        if candidate.lower() == wanted:
            return candidate
    return None


def _ordered_models(primary: Optional[str], candidates: List[str]) -> List[str]:
    ordered = []
    if primary:
        ordered.append(primary)
    for candidate in candidates:
        if candidate not in ordered:
            ordered.append(candidate)
    return ordered


def get_available_models() -> List[dict]:
    """Return model catalog used by frontend model selectors."""
    models = [
        {
            "id": "heuristic",
            "provider": "heuristic",
            "label": "Heuristic Fast Classifier",
            "enabled": True,
            "default": AI_PROVIDER not in ("openai", "huggingface")
        }
    ]

    openai_enabled = bool(OPENAI_API_KEY and _HAS_OPENAI)
    for model_id in OPENAI_MODELS:
        models.append({
            "id": model_id,
            "provider": "openai",
            "label": f"OpenAI - {model_id}",
            "enabled": openai_enabled,
            "default": AI_PROVIDER == "openai" and model_id == OPENAI_MODEL
        })

    hf_enabled = bool(HUGGINGFACE_API_KEY)
    for model_id in HF_MODELS:
        models.append({
            "id": model_id,
            "provider": "huggingface",
            "label": f"HuggingFace - {model_id}",
            "enabled": hf_enabled,
            "default": AI_PROVIDER == "huggingface" and model_id == HF_DEFAULT_MODEL
        })

    return models


def _call_hf_model(model: str, prompt: str, timeout: int = 20) -> Optional[str]:
    if not HUGGINGFACE_API_KEY:
        return None
    url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    payload = {"inputs": prompt, "options": {"use_cache": False}, "parameters": {"max_new_tokens": 512}}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list) and data:
            # many HF endpoints return a list with 'generated_text'
            first = data[0]
            if isinstance(first, dict):
                return first.get("generated_text") or first.get("text")
        if isinstance(data, dict):
            if "generated_text" in data:
                return data["generated_text"]
            choices = data.get("choices")
            if choices and isinstance(choices, list):
                return choices[0].get("text")
        return None
    except Exception as e:
        print("[AI_ENGINE][HF] error:", e)
        return None


def analyze_issue(message: str, model_hint: Optional[str] = None) -> dict:
    """
    Main AI brain.
    Never crashes. Always returns valid structured output.
    """
    # Heuristics: urgency, issue, and emotion cues from keywords
    URGENT_KEYWORDS = [r"\burgent\b", r"\bemergency\b", r"\basap\b", r"\bimmediately\b", r"\bhelp now\b"]
    ACCIDENT_KEYWORDS = [r"\baccident\b", r"\baccdient\b", r"\bcrash\b", r"\broad crash\b", r"\bvehicle crash\b"]
    HEALTH_KEYWORDS = [r"\bhospital\b", r"\bdeath\b", r"\bdied\b", r"\bdying\b", r"\bdead\b", r"\bfatal\b"]
    WATER_KEYWORDS = [r"\bwater\b", r"\bno water\b", r"\bdrinking water\b", r"\btap water\b", r"\bwater supply\b", r"\bcontaminated water\b", r"\bwatr\b"]
    FOOD_KEYWORDS = [r"\bfood\b", r"\bhunger\b", r"\bno food\b", r"\bstarv\b", r"\bstarving\b"]
    EDUCATION_KEYWORDS = [r"\bschool\b", r"\bteacher\b", r"\beducation\b", r"\bstudents\b"]
    SAFETY_KEYWORDS = [r"\bstreet light\b", r"\bstreet lights\b", r"\bsafety\b", r"\bcrime\b", r"\btheft\b"]
    EMPLOYMENT_KEYWORDS = [r"\bjob\b", r"\bunemployment\b", r"\bjobs\b", r"\blost my job\b"]

    forced_urgent = False
    forced_issue = None
    forced_emotion = None
    try:
        lowerm = (message or "").lower()
        for kw in URGENT_KEYWORDS:
            if re.search(kw, lowerm):
                forced_urgent = True
                break
        for kw in ACCIDENT_KEYWORDS:
            if re.search(kw, lowerm):
                forced_issue = "Accident"
                forced_emotion = "Fear"
                break
        # health/death/hospital related -> Health issue and likely Fear
        for kw in HEALTH_KEYWORDS:
            if re.search(kw, lowerm):
                forced_issue = "Health"
                forced_emotion = "Fear"
                break
        # water related problems
        if not forced_issue:
            for kw in WATER_KEYWORDS:
                if re.search(kw, lowerm):
                    forced_issue = "Water"
                    forced_emotion = "Distress"
                    break
        # food problems
        if not forced_issue:
            for kw in FOOD_KEYWORDS:
                if re.search(kw, lowerm):
                    forced_issue = "Food"
                    forced_emotion = "Distress"
                    break
        # education
        if not forced_issue:
            for kw in EDUCATION_KEYWORDS:
                if re.search(kw, lowerm):
                    forced_issue = "Education"
                    forced_emotion = "Distress"
                    break
        # safety
        if not forced_issue:
            for kw in SAFETY_KEYWORDS:
                if re.search(kw, lowerm):
                    forced_issue = "Safety"
                    forced_emotion = "Fear"
                    break
        # employment
        if not forced_issue:
            for kw in EMPLOYMENT_KEYWORDS:
                if re.search(kw, lowerm):
                    forced_issue = "Employment"
                    forced_emotion = "Distress"
                    break
    except Exception:
        forced_urgent = False
        forced_issue = None
        forced_emotion = None

    # Human-readable heuristic summaries for forced issues
    HEURISTIC_SUMMARIES = {
        "Accident": "Report of a traffic or other accident requiring immediate attention.",
        "Health": "Report indicating serious medical need or potential fatality.",
        "Water": "Report of problems with drinking water supply or quality.",
        "Food": "Report of food shortage or hunger in the community.",
        "Education": "Report about school/teacher shortages or education access problems.",
        "Safety": "Report of safety concerns such as poor lighting or crime.",
        "Employment": "Report about job loss or employment difficulties.",
        "Other": "A citizen shared a general concern."
    }

    fallback = {
        "issue": forced_issue or "Other",
        "emotion": forced_emotion or "Calm",
        "urgency": "High" if forced_urgent else "Medium",
        "summary": HEURISTIC_SUMMARIES.get(forced_issue or "Other")
    }

    if not message or not message.strip():
        out = {**fallback, 'confidence': 0.5, 'model': 'heuristic', 'provider': 'heuristic'}
        return out

    selected_model = (model_hint or "").strip()
    if selected_model.lower() == "heuristic":
        return {**fallback, 'confidence': 0.5, 'model': 'heuristic', 'provider': 'heuristic'}

    selected_openai = _match_model_name(selected_model, OPENAI_MODELS)
    selected_hf = _match_model_name(selected_model, HF_MODELS)

    if selected_openai:
        provider_sequence = ["openai", "huggingface"]
    elif selected_hf:
        provider_sequence = ["huggingface", "openai"]
    else:
        provider_sequence = ["huggingface", "openai"] if AI_PROVIDER == "huggingface" else ["openai", "huggingface"]

    openai_models_to_try = _ordered_models(
        selected_openai or (OPENAI_MODEL if AI_PROVIDER == "openai" else None),
        OPENAI_MODELS,
    )
    hf_models_to_try = _ordered_models(
        selected_hf or (HF_DEFAULT_MODEL if AI_PROVIDER == "huggingface" else None),
        HF_MODELS,
    )

    prompt = build_prompt(message)

    def _sanitize_output(parsed: dict):
        issue = parsed.get("issue", "Other")
        emotion = parsed.get("emotion", "Calm")
        urgency = parsed.get("urgency", "Medium")
        summary = parsed.get("summary", fallback["summary"]) or fallback["summary"]

        if forced_urgent:
            urgency = "High"
        if forced_issue:
            issue = forced_issue
        if forced_emotion:
            emotion = forced_emotion
        if forced_issue:
            summary = HEURISTIC_SUMMARIES.get(forced_issue, summary)

        if issue not in ISSUES:
            issue = "Other"
        if emotion not in EMOTIONS:
            emotion = "Calm"
        if urgency not in URGENCY:
            urgency = "Medium"

        return issue, emotion, urgency, summary

    for provider in provider_sequence:
        if provider == "openai" and client is not None:
            for model_name in openai_models_to_try:
                for attempt in range(2):
                    try:
                        if not check_and_increment_quota():
                            raise RuntimeError('AI quota exceeded')

                        response = client.chat.completions.create(
                            model=model_name,
                            messages=[
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.2
                        )

                        content = ""
                        if hasattr(response, "choices") and response.choices:
                            choice = response.choices[0]
                            message_obj = getattr(choice, "message", None)
                            if message_obj:
                                if isinstance(message_obj, dict):
                                    content = message_obj.get("content", "")
                                else:
                                    content = getattr(message_obj, "content", "")
                            elif isinstance(choice, dict):
                                content = choice.get("text", "")

                        content = str(content).strip()
                        parsed = safe_json_load(content or "")
                        if not parsed:
                            raise ValueError("Invalid JSON from model")

                        issue, emotion, urgency, summary = _sanitize_output(parsed)
                        return {
                            "issue": issue,
                            "emotion": emotion,
                            "urgency": urgency,
                            "summary": summary,
                            'confidence': 0.85,
                            'model': f'openai:{model_name}',
                            'provider': 'openai'
                        }

                    except Exception as e:
                        print(f"[AI_ENGINE][OpenAI:{model_name}] Attempt {attempt+1} failed:", e)
                        time.sleep(0.5)

        if provider == "huggingface" and HUGGINGFACE_API_KEY:
            for hf_model in hf_models_to_try:
                text = _call_hf_model(hf_model, prompt)
                if not text:
                    continue

                parsed = safe_json_load(text)
                if not parsed:
                    continue

                issue, emotion, urgency, summary = _sanitize_output(parsed)
                return {
                    "issue": issue,
                    "emotion": emotion,
                    "urgency": urgency,
                    "summary": summary,
                    'confidence': 0.7,
                    'model': f'huggingface:{hf_model}',
                    'provider': 'huggingface'
                }

    # Final fallback
    return {**fallback, 'confidence': 0.5, 'model': 'heuristic', 'provider': 'heuristic'}

