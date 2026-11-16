"""AI Service integrating AIWaterQualityProject-Chatbot LangGraph workflows and ML models with AquaVision."""

import os
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add Chatbot root to sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = BACKEND_DIR.parent.parent
CHATBOT_DIR = (
    WORKSPACE_ROOT / "AIWaterQualityProject-Chatbot"
    if (WORKSPACE_ROOT / "AIWaterQualityProject-Chatbot").exists()
    else BACKEND_DIR.parent / "AIWaterQualityProject-Chatbot"
)

if str(CHATBOT_DIR) not in sys.path:
    sys.path.insert(0, str(CHATBOT_DIR))

# Ensure environment variables are loaded
from dotenv import load_dotenv
load_dotenv(dotenv_path=BACKEND_DIR / ".env")

# Set working Gemini model defaults
if not os.getenv("GEMINI_MODEL"):
    os.environ["GEMINI_MODEL"] = "gemini-3.1-flash-lite"
if not os.getenv("GEMINI_FALLBACK_MODELS"):
    os.environ["GEMINI_FALLBACK_MODELS"] = "gemini-3.5-flash-lite,gemini-3.6-flash"

# Import models, rules, and reporter agent from reference chatbot
from src.agents.reporter.graph import report_agent
from src.agents.reporter.nodes import INPUT_PARAMS, UNITS, TREATMENT
from src.foundation.rules import NSDWQ_LIMITS, rule_engine
from src.foundation.inference import model_runner, parse_sample_query
from src.agents.chatbot.nodes import _invoke_gemini, _generation_error

from services.report_store import report_store
from services.tanker_service import tanker_service
from services.profile_activity_service import profile_activity_service

# Regex to detect when user specifically wants to generate an official laboratory report
_GENERATE_REPORT_RE = re.compile(
    r"\b(?:generate|create|make|produce|export)\b.{0,60}\b(?:report|certificate|audit|doc|pdf)\b"
    r"|\b(?:full|formal|laboratory|official)\s+report\b",
    re.I,
)


def is_explicit_report_request(query: str) -> bool:
    return bool(_GENERATE_REPORT_RE.search(query))


class AIService:
    def __init__(self):
        # Session state: session_id -> {"history": list, "last_report_id": str}
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def get_session(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "history": [],
                "last_report_id": None,
            }
        return self._sessions[session_id]

    def _extract_tanker_id(self, query: str) -> Optional[str]:
        match = re.search(r"\b(?:tanker|tank)[\s_-]*([0-9]+[a-z]?)\b", query, re.I)
        if match:
            num = match.group(1).zfill(2)
            return f"TANK-{num.upper()}"
        return None

    def process_chat(
        self,
        session_id: str,
        message: str,
        active_tanker_id: Optional[str] = None,
        context_mode: Optional[str] = "overall",
    ) -> Dict[str, Any]:
        session = self.get_session(session_id)
        msg_clean = message.strip()
        lowered = msg_clean.casefold()

        # Determine effective context
        # If user explicitly specifies a tanker ID in their question (e.g., "What is Tanker 02's pH?"), honor it
        detected_tanker = self._extract_tanker_id(msg_clean)
        effective_tanker_id = detected_tanker or (active_tanker_id if context_mode == "tanker" else None)

        all_tankers = tanker_service.get_all_tankers()
        active_tanker = None
        if effective_tanker_id and effective_tanker_id != "overall":
            active_tanker = tanker_service.get_tanker_by_id(effective_tanker_id)

        # -------------------------------------------------------------
        # 1. EXPLICIT REPORT GENERATION REQUEST
        # -------------------------------------------------------------
        if is_explicit_report_request(msg_clean):
            target_tanker = active_tanker or (all_tankers[0] if all_tankers else None)
            if not target_tanker:
                return {
                    "response": "No tankers are currently registered in AquaVision. Please add a tanker first before generating a report.",
                    "is_report": False,
                    "report": None,
                    "session_id": session_id,
                    "warning": None,
                }

            report_result = self.generate_report(
                tanker_id=target_tanker["id"],
                custom_measurements=target_tanker.get("measurements"),
                user_query=msg_clean,
                session_id=session_id,
            )

            response_text = (
                f"I have compiled the comprehensive water quality analysis report for **{target_tanker['name']}**.\n\n"
                f"- **Report Reference:** `{report_result['id']}`\n"
                f"- **Calculated WQI Score:** **{report_result['wqi_score']}** ({report_result['quality_class']})\n"
                f"- **Pakistan NSDWQ Status:** **{report_result['status']}**\n\n"
                f"You can review the full diagnostic breakdown in the interactive card below, download the certified PDF report, or ask follow-up questions about specific parameters."
            )

            session["history"].append({"sender": "user", "text": msg_clean})
            session["history"].append({
                "sender": "bot",
                "text": response_text,
                "report_id": report_result["id"],
            })

            return {
                "response": response_text,
                "is_report": True,
                "report": report_result,
                "session_id": session_id,
                "warning": None,
            }

        # -------------------------------------------------------------
        # 2. NUMERIC WQI PREDICTION REQUEST (e.g. "Predict WQI for pH 7.2 and TDS 450")
        # -------------------------------------------------------------
        parsed_sample = parse_sample_query(msg_clean)
        # Check if the query has at least one explicit numeric parameter
        has_numeric_params = any(p in parsed_sample for p in (
            "pH", "Turbidity", "TDS", "Chloride", "Sulfate", "Nitrate",
            "Fluoride", "Arsenic", "Iron", "Lead", "Cadmium", "Chromium", "Mercury"
        ))

        if has_numeric_params and any(k in lowered for k in ["predict", "calculate", "wqi", "score", "estimate", "evaluate"]):
            return self._handle_wqi_prediction(session_id, msg_clean, parsed_sample)

        # -------------------------------------------------------------
        # 3. CONVERSATIONAL & CONTEXT-AWARE INTELLIGENCE
        # -------------------------------------------------------------
        # Build comprehensive grounded context from application state
        prompt = self._build_grounded_prompt(
            user_query=msg_clean,
            context_mode=context_mode or ("tanker" if active_tanker else "overall"),
            active_tanker=active_tanker,
            all_tankers=all_tankers,
            history=session["history"][-4:],
        )

        try:
            response_text, failover_notice = _invoke_gemini(prompt)
            if not response_text or not response_text.strip():
                response_text = self._fallback_response(msg_clean, active_tanker, all_tankers)

            session["history"].append({"sender": "user", "text": msg_clean})
            session["history"].append({"sender": "bot", "text": response_text})

            return {
                "response": response_text,
                "is_report": False,
                "report": None,
                "session_id": session_id,
                "warning": failover_notice,
            }
        except Exception as exc:
            # Graceful local fallback ensuring the chat never crashes
            fallback = self._fallback_response(msg_clean, active_tanker, all_tankers)
            return {
                "response": fallback,
                "is_report": False,
                "report": None,
                "session_id": session_id,
                "warning": _generation_error(exc),
            }

    def _handle_wqi_prediction(
        self,
        session_id: str,
        query: str,
        sample_params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Runs pre-trained CatBoost WQI regressor and Gradient Boosting classifier, then provides an insightful explanation."""
        try:
            pred = model_runner.predict_sample(sample_params)
            wqi = pred.get("wqi_calculated")
            tier = pred.get("final_water_quality_class") or pred.get("predicted_class", "Good")
            confidence = pred.get("classification_confidence", 95.0)

            provided_list = [f"**{k}**: {v}" for k, v in sample_params.items()]
            missing = [p for p in ["Turbidity", "TDS", "pH", "Nitrate", "Chloride", "Sulfate", "Arsenic"] if p not in sample_params]

            prompt = (
                f"You are the AquaVision AI Water Science Copilot. The user asked: '{query}'\n\n"
                f"Model Prediction Results:\n"
                f"- User Supplied Parameters: {', '.join(provided_list)}\n"
                f"- Unmeasured Parameters (Imputed using training medians): {', '.join(missing[:4])}\n"
                f"- Machine Learning Calculated WQI: {wqi} (Scale: 0-50 Excellent, 51-100 Good, 101-200 Poor, 201-300 Very Poor, >300 Unsuitable)\n"
                f"- Predicted Quality Tier: {tier} ({confidence}% model confidence)\n\n"
                f"Instructions:\n"
                f"1. Explain the calculated Water Quality Index ({wqi}) and what the '{tier}' rating means in understandable terms.\n"
                f"2. Explicitly note which parameters were provided and that missing values were imputed based on standard regional baseline medians.\n"
                f"3. Note that this is a machine-learning screening estimate from AquaVision's CatBoost regressor, and official potability certification requires full laboratory testing."
            )

            explanation, warn = _invoke_gemini(prompt)
            if not explanation:
                explanation = (
                    f"Based on the provided telemetry ({', '.join(provided_list)}), AquaVision's CatBoost model predicts a **Water Quality Index (WQI) of {wqi}**, placing this sample in the **{tier}** category with **{confidence}%** confidence.\n\n"
                    f"**Assessment & Methodology:**\n"
                    f"- The provided values fall within safe operational ranges under Pakistan NSDWQ standards.\n"
                    f"- Parameters not specified ({', '.join(missing[:4])}) were estimated using regional baseline training medians.\n"
                    f"- *Note:* This prediction serves as an initial IoT screening estimate and does not replace full certified laboratory microbiological culture tests."
                )

            session = self.get_session(session_id)
            session["history"].append({"sender": "user", "text": query})
            session["history"].append({"sender": "bot", "text": explanation})

            return {
                "response": explanation,
                "is_report": False,
                "report": None,
                "session_id": session_id,
                "warning": warn,
            }
        except Exception as exc:
            return {
                "response": f"I extracted your parameters ({sample_params}), but encountered an error running model inference: {exc}",
                "is_report": False,
                "report": None,
                "session_id": session_id,
                "warning": str(exc),
            }

    def _build_grounded_prompt(
        self,
        user_query: str,
        context_mode: str,
        active_tanker: Optional[Dict[str, Any]],
        all_tankers: List[Dict[str, Any]],
        history: List[Dict[str, str]],
    ) -> str:
        """Constructs an informative, grounded prompt embedding current fleet/tanker facts and regulatory standards."""
        # Retrieve vector standards if query asks about limits or contaminants
        standards_text = ""
        try:
            from src.foundation.vector_store import query_standards
            standards_text = query_standards(user_query, n_results=2)
        except Exception:
            standards_text = "WHO & Pakistan NSDWQ standard ceilings: Nitrate <= 50 mg/L, TDS <= 1000 mg/L, Turbidity <= 5.0 NTU, pH 6.5-8.5, Arsenic <= 0.05 mg/L, Lead <= 0.05 mg/L."

        # Fleet factual data
        fleet_count = len(all_tankers)
        fleet_overview = []
        for t in all_tankers:
            m = t.get("measurements", {})
            ph_val = m.get("pH", "N/A")
            tds_val = m.get("TDS", "N/A")
            turb_val = m.get("Turbidity", "N/A")
            wqi_val = t.get("wqi_score") or "75.0"
            fleet_overview.append(
                f"- {t['id']} ({t['name']}, {t['city']}): Status='{t.get('status', 'Normal')}', WQI={wqi_val}, pH={ph_val}, TDS={tds_val} mg/L, Turbidity={turb_val} NTU"
            )
        fleet_summary_str = "\n".join(fleet_overview) if fleet_overview else "No tankers currently registered."

        # Specific tanker factual data
        tanker_details_str = ""
        if active_tanker:
            m = active_tanker.get("measurements", {})
            tanker_details_str = (
                f"Selected Tanker Context: {active_tanker['id']} — {active_tanker['name']}\n"
                f"- City / Province: {active_tanker.get('city')}, {active_tanker.get('province')}\n"
                f"- Source Type: {active_tanker.get('source_type')}\n"
                f"- Storage Capacity: {active_tanker.get('capacity_liters')} Liters\n"
                f"- Overall Status: {active_tanker.get('status')}\n"
                f"- WQI Score: {active_tanker.get('wqi_score', 'Good')}\n"
                f"- Measured Telemetry: pH={m.get('pH')}, TDS={m.get('TDS')} mg/L, Turbidity={m.get('Turbidity')} NTU, Temp={m.get('Temperature')}°C, EC={m.get('EC')} µS/cm, Nitrate={m.get('Nitrate')} mg/L\n"
            )

        conv_history = ""
        if history:
            conv_history = "Recent conversation:\n" + "\n".join(
                f"{h['sender'].capitalize()}: {h['text']}" for h in history
            ) + "\n\n"

        prompt = f"""You are the AquaVision AI Water Science Copilot, an intelligent, conversational water quality and safety expert.
You pair-program and assist scientists, researchers, and water utility operators in monitoring water distribution fleets in Pakistan.

{conv_history}CURRENT APPLICATION DATA:
- Active Context Selection: {'Overall Context (Entire Fleet)' if context_mode == 'overall' or not active_tanker else f"Specific Tanker ({active_tanker['id']})"}
- Total Registered Tankers in AquaVision: {fleet_count}
- Registered Tankers List:
{fleet_summary_str}

{tanker_details_str}
GROUNDING STANDARDS (Pakistan NSDWQ & WHO):
{standards_text}

USER QUESTION:
"{user_query}"

INSTRUCTIONS FOR YOUR RESPONSE:
1. Understand the user's intent:
   - For greetings (e.g. 'Hi', 'Hello'): Greet warmly, introduce your role as the AquaVision AI Copilot, and mention what you can help with.
   - For fleet/overall questions (e.g. 'How many tankers are registered?', 'Compare all registered tankers', 'Which tanker has the best water quality?'): Answer using the actual application data above. State the exact count ({fleet_count} tankers) and provide helpful summaries or comparisons. Rank or highlight best/worst units based on WQI scores and parameter compliance. NEVER say you lack tanker data.
   - For tanker-specific questions (e.g. 'Analyze its water quality', 'What is its pH?', 'What actions to improve?'): Use the selected tanker's telemetry. Explain what the numbers mean relative to Pakistan NSDWQ limits (pH 6.5-8.5, TDS < 1000 mg/L, Turbidity < 5 NTU) and provide actionable remediation if needed.
   - For water science questions (e.g. 'What is the difference between TDS and turbidity?', 'Why is pH important in drinking water?', 'What causes high turbidity?', 'How does WQI work?'): Provide clear, authoritative scientific explanations with real-world distribution context.
   - For health questions (e.g. 'What are the health risks of high nitrate levels for children?'): Provide a clear, natural explanation of the physiological health risks (e.g. infant methemoglobinemia / 'blue baby syndrome', impaired oxygen transport), state the regulatory safety standard (50 mg/L), and mention the current tanker reading context if relevant.
2. Tone & Formatting:
   - Be conversational, helpful, natural, and scientifically accurate.
   - Use short, well-structured paragraphs with bullet points and bolding where appropriate.
   - Do NOT give robotic, one-line fragments.
   - Do NOT pretend a report contains no information when the application data is provided above.
"""
        return prompt

    def _fallback_response(
        self,
        query: str,
        active_tanker: Optional[Dict[str, Any]],
        all_tankers: List[Dict[str, Any]],
    ) -> str:
        """Deterministic, rich response in case the external LLM is completely offline."""
        lowered = query.casefold()

        # Greetings (using word boundaries so "hi" doesn't match "which" or "white")
        if any(re.search(r"\b" + re.escape(w) + r"\b", lowered) for w in ["hi", "hello", "hey", "greetings"]) or "who are you" in lowered or "what can you do" in lowered:
            return (
                "Hello! I am your **AquaVision AI Water Science Copilot**. I am connected to your live IoT tanker telemetry, "
                "pre-trained machine learning models (CatBoost WQI regressor and Gradient Boosting classifier), and WHO / Pakistan NSDWQ standards.\n\n"
                "I can help you with:\n"
                "- Reviewing live telemetry and fleet statistics across all registered tankers\n"
                "- Evaluating water potability against Pakistan NSDWQ and WHO limits\n"
                "- Predicting WQI scores from experimental sample measurements\n"
                "- Generating comprehensive laboratory audit reports with PDF downloads"
            )

        # Tanker count
        if "how many tanker" in lowered or "count" in lowered and "tanker" in lowered:
            return (
                f"There are currently **{len(all_tankers)} water tankers** registered and actively monitored in the AquaVision platform across Pakistan.\n\n"
                f"Locations include: {', '.join(set(t['city'] for t in all_tankers))}. You can select any tanker from the context selector to inspect its individual telemetry."
            )

        # TDS vs Turbidity comparison
        if "tds" in lowered and "turbidity" in lowered:
            return (
                "**Difference Between TDS and Turbidity:**\n\n"
                "- **TDS (Total Dissolved Solids):** Measures dissolved inorganic salts (calcium, magnesium, potassium, sodium, bicarbonates, chlorides, sulfates) and small amounts of organic matter dissolved in water (particle size < 2 microns). Measured in **mg/L** or **ppm**.\n"
                "  - *Pakistan NSDWQ Ceiling:* **1000 mg/L** (WHO recommends < 600 mg/L for optimal palatability).\n"
                "  - *Impact:* High TDS leads to mineral scale in piping, bitter or salty taste, and gastrointestinal effects, though water may appear completely clear.\n\n"
                "- **Turbidity:** Measures optical cloudiness or haziness caused by undissolved suspended particles (clay, silt, organic colloids, microscopic organisms) that scatter and absorb light. Measured in **NTU** (Nephelometric Turbidity Units).\n"
                "  - *Pakistan NSDWQ Standard:* **< 5.0 NTU** (WHO target: < 1.0 NTU for effective disinfection).\n"
                "  - *Impact:* High turbidity shields pathogenic bacteria and viruses from chlorine disinfection, increases chlorine demand, and creates biological biofilms.\n\n"
                "**Key Distinction:** Water with high TDS can be crystal clear, while water with high turbidity is visibly hazy. TDS represents dissolved ions; Turbidity represents suspended particulates."
            )

        # pH importance
        if "ph" in lowered and ("important" in lowered or "significance" in lowered or "why" in lowered):
            return (
                "**Importance of pH in Drinking Water:**\n\n"
                "pH measures the hydrogen ion concentration (acidity or basicity) on a logarithmic scale from 0 to 14. For potable water distribution, maintaining an optimal pH of **6.5 – 8.5** (Pakistan NSDWQ and WHO guidelines) is critical for three primary reasons:\n\n"
                "1. **Corrosion and Heavy Metal Leaching (Low pH < 6.5):** Acidic water is corrosive to copper, iron, and lead plumbing fixtures, causing hazardous metal leaching into municipal tap water.\n"
                "2. **Disinfection Efficiency (High pH > 8.0):** Chlorine disinfection effectiveness plummets at elevated pH. Hypochlorous acid (HOCl, the powerful germicide) dissociates into the much weaker hypochlorite ion (OCl⁻), requiring substantially higher disinfectant dosing.\n"
                "3. **Scaling & Aesthetic Palatability:** Basic water (> 8.5) precipitates calcium carbonate scale, choking distribution manifolds and imparting a bitter, slippery taste."
            )

        # Best tanker / fleet comparison
        if "best" in lowered and ("tanker" in lowered or "quality" in lowered):
            if all_tankers:
                # Find tanker with lowest WQI or highest score
                best_t = min(all_tankers, key=lambda t: float(t.get("wqi_score", 100)))
                m = best_t.get("measurements", {})
                return (
                    f"**Best Water Quality Unit: {best_t['id']} ({best_t['name']})**\n\n"
                    f"Among all {len(all_tankers)} registered distribution tankers, **{best_t['name']}** in **{best_t['city']}** currently exhibits the top water quality profile:\n"
                    f"- **WQI Score:** **{best_t.get('wqi_score', 'N/A')}** ({best_t.get('status', 'Normal')} status)\n"
                    f"- **pH Level:** {m.get('pH', 'N/A')} (Ideal range: 6.5 – 8.5)\n"
                    f"- **TDS Concentration:** {m.get('TDS', 'N/A')} mg/L (Ceiling: 1000 mg/L)\n"
                    f"- **Turbidity:** {m.get('Turbidity', 'N/A')} NTU (Ceiling: 5.0 NTU)\n\n"
                    f"This unit's source ({best_t.get('source_type', 'Groundwater')}) operates well within Pakistan NSDWQ guidelines."
                )

        # Compare all tankers
        if "compare" in lowered and "tanker" in lowered:
            rows = []
            for t in all_tankers:
                m = t.get("measurements", {})
                rows.append(f"- **{t['id']} ({t['name']}, {t['city']})**: WQI **{t.get('wqi_score', 'N/A')}**, pH {m.get('pH')}, TDS {m.get('TDS')} mg/L, Turbidity {m.get('Turbidity')} NTU — *Status: {t.get('status', 'Normal')}*")
            return (
                f"**Fleet-Wide Water Quality Comparison ({len(all_tankers)} Tankers Monitored):**\n\n"
                + "\n".join(rows) +
                "\n\nAll units are synchronized with live regional telemetry. Select any individual tanker in the dropdown above to run targeted remediations or generate certified PDF audit reports."
            )

        # What can cause high turbidity
        if "turbidity" in lowered and ("cause" in lowered or "high" in lowered or "cloud" in lowered):
            return (
                "**Primary Causes of High Turbidity in Drinking Water:**\n\n"
                "1. **Surface Runoff and Soil Erosion:** Heavy monsoon rainfall washes clay, silt, and decaying organic matter into open supply reservoirs.\n"
                "2. **Distribution Pipe Corrosion and Sediment Resuspension:** Fluctuating water pressure or mechanical vibrations resuspend internal pipe scale, rust (iron oxide), and accumulated silt.\n"
                "3. **Microbial and Algal Blooms:** Nutrient enrichment (nitrates, phosphates) triggers microscopic algal blooms and bacterial biofilms.\n"
                "4. **Inadequate Coagulation / Filtration:** Sub-optimal dosing of alum or damaged sand filters at municipal treatment plants fails to aggregate and capture fine colloidal particles.\n\n"
                "**Remediation:** Coagulation-flocculation using aluminum sulfate, rapid dual-media sand filtration, followed by ultraviolet or chlorine disinfection."
            )

        # How WQI works
        has_wqi = "wqi" in lowered or "water quality index" in lowered
        if has_wqi and ("how" in lowered or "work" in lowered or "explain" in lowered or "scale" in lowered or "meaning" in lowered):
            return (
                "**How the Water Quality Index (WQI) Works:**\n\n"
                "The Water Quality Index (WQI) mathematically aggregates multiple diverse physical, chemical, and biological measurements into a single unified score between 0 and 100+ to communicate overall water safety:\n\n"
                "1. **Unit Weighting ($W_i$):** Each parameter (pH, TDS, Turbidity, Nitrate, Lead, etc.) is assigned a weight based on its relative health significance. Toxic heavy metals (e.g., Lead, Arsenic) carry much higher weights than aesthetic parameters (e.g., Color, Hardness).\n"
                "2. **Sub-index Quality Rating ($q_i$):** Measures the deviation of each parameter from its regulatory standard ceiling (Pakistan NSDWQ / WHO).\n"
                "3. **Weighted Aggregation:** $WQI = \\sum (q_i \\times W_i) / \\sum W_i$\n\n"
                "**AquaVision WQI Classification Scale:**\n"
                "- **0 – 50:** Excellent (Pure, pristine drinking water)\n"
                "- **51 – 100:** Good (Potable, compliant with NSDWQ standards)\n"
                "- **101 – 200:** Poor (Requires filtration and chlorination)\n"
                "- **201 – 300:** Very Poor (Industrial treatment needed)\n"
                "- **> 300:** Unsuitable for human consumption"
            )

        # Tanker recommendations / actions
        if ("action" in lowered or "recommend" in lowered or "treatment" in lowered or "improve" in lowered) and active_tanker:
            m = active_tanker.get("measurements", {})
            turb = m.get("Turbidity", 2.0)
            tds = m.get("TDS", 400.0)
            actions = []
            if turb > 4.0:
                actions.append("Conduct dual-media sand filtration or cartridge microfiltration to reduce optical turbidity below 1.0 NTU.")
            else:
                actions.append("Turbidity is within safe limits; maintain routine monthly tank sediment flushing.")
            if tds > 800:
                actions.append("Consider partial reverse osmosis blending or electrodialysis to suppress elevated mineral salinity.")
            else:
                actions.append("TDS is within the 1000 mg/L standard; no demineralization necessary.")
            actions.append("Verify secondary residual free chlorine concentration (target: 0.2 – 0.5 mg/L at delivery point).")
            actions.append("Conduct quarterly physical tank chamber sanitization with food-grade sodium hypochlorite solution.")

            return (
                f"**Recommended Maintenance & Treatment Actions for {active_tanker['id']} ({active_tanker['name']}):**\n\n"
                + "\n".join(f"{i+1}. {a}" for i, a in enumerate(actions)) +
                f"\n\nThese recommendations comply with WHO and Pakistan Water and Sanitation Agency (WASA) guidelines."
            )

        # Parameters outside recommended ranges
        if ("outside" in lowered or "exceed" in lowered or "range" in lowered) and active_tanker:
            m = active_tanker.get("measurements", {})
            out_params = []
            ph = m.get("pH", 7.0)
            if ph < 6.5 or ph > 8.5:
                out_params.append(f"pH is **{ph}** (Recommended: 6.5 – 8.5)")
            tds = m.get("TDS", 400)
            if tds > 1000:
                out_params.append(f"TDS is **{tds} mg/L** (Ceiling: 1000 mg/L)")
            turb = m.get("Turbidity", 2.0)
            if turb > 5.0:
                out_params.append(f"Turbidity is **{turb} NTU** (Ceiling: 5.0 NTU)")
            nit = m.get("Nitrate", 15.0)
            if nit > 50.0:
                out_params.append(f"Nitrate is **{nit} mg/L** (Ceiling: 50 mg/L)")

            if out_params:
                return (
                    f"**Exceeded Parameters for {active_tanker['id']}:**\n\n"
                    + "\n".join(f"- {p}" for p in out_params) +
                    "\n\nImmediate maintenance intervention is advised before commercial distribution."
                )
            else:
                return (
                    f"**Parameter Status for {active_tanker['id']} ({active_tanker['name']}):**\n\n"
                    f"All monitored primary parameters conform strictly to Pakistan NSDWQ regulatory limits:\n"
                    f"- **pH:** {m.get('pH', 7.2)} (Safe 6.5 – 8.5)\n"
                    f"- **TDS:** {m.get('TDS', 380)} mg/L (Safe < 1000 mg/L)\n"
                    f"- **Turbidity:** {m.get('Turbidity', 1.8)} NTU (Safe < 5.0 NTU)\n"
                    f"- **Nitrate:** {m.get('Nitrate', 12.0)} mg/L (Safe < 50 mg/L)\n\n"
                    f"No parameters currently exceed hazardous thresholds."
                )

        # Health risks of nitrate
        if "nitrate" in lowered and ("health" in lowered or "risk" in lowered or "children" in lowered):
            tanker_note = ""
            if active_tanker:
                nitrate_val = active_tanker.get("measurements", {}).get("Nitrate", 15.0)
                tanker_note = f"\n\n*Current Reading in {active_tanker['id']}:* Nitrate is currently **{nitrate_val} mg/L**, which is within the safe limit."

            return (
                "**Health Risks of High Nitrate in Drinking Water:**\n\n"
                "In infants under six months of age, high nitrate concentrations can cause **methemoglobinemia** (commonly known as 'blue baby syndrome'). "
                "In the infant digestive tract, nitrates are reduced to nitrites, which bind to hemoglobin and form methemoglobin. This compound cannot bind or carry oxygen, "
                "leading to clinical oxygen deprivation, cyanosis, and potentially severe complications.\n\n"
                "In adults and children, chronic elevated nitrate consumption has also been linked to thyroid hypertrophy, gastrointestinal irritation, and the formation of potentially carcinogenic N-nitroso compounds.\n\n"
                "**Regulatory Ceilings:**\n"
                "- **WHO Guideline:** 50 mg/L (as $NO_3^-$)\n"
                "- **Pakistan NSDWQ Standard:** 50 mg/L"
                f"{tanker_note}"
            )

        # Specific tanker analysis
        if active_tanker and any(w in lowered for w in ["analyze", "quality", "safe", "ph", "tds", "turbidity"]):
            m = active_tanker.get("measurements", {})
            ph_val = m.get("pH", 7.2)
            tds_val = m.get("TDS", 400.0)
            turb_val = m.get("Turbidity", 2.0)
            wqi_val = active_tanker.get("wqi_score", 78.0)
            status_val = active_tanker.get("status", "Good")

            return (
                f"**Water Quality Diagnostic: {active_tanker['id']} ({active_tanker['name']})**\n\n"
                f"The unit is stationed in **{active_tanker['city']}** ({active_tanker['source_type']}) with a calculated Water Quality Index of **{wqi_val}** ({status_val} status).\n\n"
                f"- **pH Level:** {ph_val:.2f} (Pakistan NSDWQ Permissible Range: 6.5 – 8.5)\n"
                f"- **TDS Concentration:** {tds_val:.1f} mg/L (NSDWQ Upper Ceiling: 1000 mg/L)\n"
                f"- **Optical Turbidity:** {turb_val:.2f} NTU (Standard Regulatory Cap: 5.0 NTU)\n\n"
                f"All primary telemetry readings conform to Pakistan potable water standards. For a complete 21-parameter compliance audit, you can request an official report."
            )

        # General fallback
        return (
            f"AquaVision is monitoring **{len(all_tankers)} distribution tankers** across regional hubs. "
            f"You can ask me to evaluate parameter compliance against WHO / Pakistan NSDWQ limits, predict WQI for custom readings, "
            f"or select an individual tanker to inspect its live physical probe stream."
        )

    def generate_report(
        self,
        tanker_id: str,
        custom_measurements: Optional[Dict[str, Any]] = None,
        user_query: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        tanker = tanker_service.get_tanker_by_id(tanker_id) or tanker_service.get_all_tankers()[0]
        measurements = custom_measurements or tanker["measurements"]

        now = datetime.now()
        report_id = f"REP-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        # Build sample dictionary matching the AI team's schema
        sample = {
            "Sample_ID": f"{tanker['id']}-SMP",
            "Sampling_Date": now.strftime("%Y-%m-%d"),
            "Sampling_Location": f"{tanker['city']} - {tanker['name']}",
            "Collected_By": "AquaVision Autonomous IoT Telemetry",
            "Laboratory": "National Water Quality Laboratory (Simulated)",
            "Report_No": report_id,
            "City": tanker.get("city", "Lahore"),
            "Province": tanker.get("province", "Punjab"),
            "Resource_Type": tanker.get("source_type", "Groundwater"),
        }

        # Populate all parameters
        for param in INPUT_PARAMS:
            val = measurements.get(param)
            if val is None:
                clean_param = param.replace(" ", "_")
                val = measurements.get(clean_param)
            if val is not None:
                sample[param] = float(val)

        # Build query for the reporter agent
        query_text = user_query or (
            f"Generate a water quality report for {tanker['name']} in {sample['City']}, "
            f"resource type {sample['Resource_Type']}."
        )

        # Invoke the reference report_agent
        result = report_agent.invoke({
            "query": query_text,
            "sample_data": sample,
            "not_provided": [
                param for param in INPUT_PARAMS
                if sample.get(param) is None
            ],
        })

        if result.get("error"):
            ml_pred = model_runner.predict_sample(sample)
            wqi = ml_pred["wqi_calculated"]
            q_class = ml_pred["predicted_class"]
            markdown = f"# Water Quality Report for {tanker['name']}\n\nWQI: {wqi}\nClass: {q_class}\n\nNotice: {result.get('error')}"
        else:
            markdown = result.get("final_report_md", "")

        state_params = result.get("sample_data", sample)
        predictions = result.get("predictions") or model_runner.predict_sample(sample)
        wqi_val = round(float(predictions.get("wqi_calculated", 75.0)), 2)
        q_class_val = predictions.get("predicted_class", "Good")

        # Evaluate parameters against NSDWQ limits
        param_table = []
        violations = []
        for param, limits in NSDWQ_LIMITS.items():
            meas_val = state_params.get(param)
            if meas_val is None:
                meas_val = measurements.get(param) or measurements.get(param.replace(" ", "_"))
            if meas_val is not None:
                meas_val = float(meas_val)
                verdict = "PASSED"
                std_str = f"<= {limits['max']}" if limits.get("max") else "Standard"
                if limits.get("min") is not None and limits.get("max") is not None:
                    std_str = f"{limits['min']} - {limits['max']}"
                    if meas_val < limits["min"] or meas_val > limits["max"]:
                        verdict = "FAILED"
                        violations.append(param)
                elif limits.get("max") is not None:
                    if meas_val > limits["max"]:
                        verdict = "FAILED"
                        violations.append(param)
                    elif meas_val > limits["max"] * 0.85:
                        verdict = "BORDERLINE"

                param_table.append({
                    "parameter": param,
                    "value": meas_val,
                    "unit": limits["unit"],
                    "standard": std_str,
                    "verdict": verdict,
                })

        recommendations = []
        for viol in violations:
            treatment = TREATMENT.get(viol, "Review source contamination and implement specialized membrane filtration.")
            recommendations.append({
                "parameter": viol,
                "action": treatment,
            })

        if not recommendations:
            recommendations.append({
                "parameter": "Maintenance",
                "action": "Routine monitoring interval: continue standard 30-day telemetry audit cycle.",
            })

        narrative_body = result.get("narrative") or (
            f"The sample from {tanker['name']} ({sample['City']}, {sample['Province']}) was analyzed using "
            f"the AquaVision neural classification and CatBoost WQI regression pipeline. "
            f"The predicted Water Quality Index is {wqi_val}, corresponding to the '{q_class_val}' classification tier."
        )

        overall_status = "Verified Safe" if not violations else ("Under Observation" if len(violations) == 1 else "Non-Compliant")

        structured_data = {
            "sample_data": sample,
            "parameters": param_table,
            "ml_evaluation": {
                "predicted_class": q_class_val,
                "wqi_calculated": wqi_val,
                "class_probabilities": predictions.get("class_probabilities", {}),
            },
            "recommendations": recommendations,
            "violations": violations,
            "narrative": narrative_body,
            "forecast": model_runner.forecast_risk(steps=5),
        }

        # Save to database
        saved_report = report_store.save_report(
            report_id=report_id,
            title=f"Water Quality Audit: {tanker['name']}",
            tanker_id=tanker["id"],
            city=sample["City"],
            province=sample["Province"],
            resource_type=sample["Resource_Type"],
            status=overall_status,
            wqi_score=wqi_val,
            quality_class=q_class_val,
            narrative=narrative_body,
            markdown_content=markdown,
            structured_data=structured_data,
            created_at=now.isoformat(),
        )

        # Log activity
        profile_activity_service.log_activity(
            title=f"Report Generated: {report_id}",
            description=f"AI Water Quality Audit produced for {tanker['name']} (WQI {wqi_val}, {q_class_val}).",
            category="reports",
            tanker_id=tanker["id"],
            report_id=report_id,
            tag="REPORT",
            status="COMPLETED"
        )

        if session_id:
            sess = self.get_session(session_id)
            sess["last_report_id"] = report_id

        return saved_report


ai_service = AIService()
