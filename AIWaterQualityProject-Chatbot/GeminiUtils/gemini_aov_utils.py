import os
import re
import json
import time
import platform
from pathlib import Path
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
from pdf2image import convert_from_path
import google.generativeai as genai

from GeminiUtils.gemini_utils import enhance_for_gemini, resize_for_llm


def preprocess(image_path):
    img1 = PIL.Image.open(image_path)
    img1= resize_for_llm(img1 )
    # 1. Load the original high-res image (Don't downscale to 2048!)

    #full_img = PIL.Image.open(image_path)

    # 2. Get Tiles (This preserves the 9000px detail in manageable chunks)
    # If the image is small, get_image_tiles will just return one tile.
    #tiles = get_image_tiles(full_img)
    # img2 = PIL.Image.open(annotated_path)

    # Enhance both images before sending to Gemini
    img1 = enhance_for_gemini(img1)

    return img1

def get_gemini_model():
    try:
        return genai.GenerativeModel("gemini-3-pro-preview")
    except Exception:
        return genai.GenerativeModel("gemini-3.1-pro-preview")

def extract_json_from_response(response_text):
    """
    Finds and parses a JSON Legend/Object/symbol from a string,
    even if surrounded by Markdown or prose.
    """
    # Check if response_text is None or empty
    if not response_text:
        print("Error: response_text is None or empty")
        return None

    text = response_text.strip()

    try:
        # Prefer whole-response JSON (object or array)
        data = json.loads(text)
        return data
    except json.JSONDecodeError:
        pass

    try:
        # Regex: outermost object (Markdown / prose wrappers)
        json_match = re.search(r'\{.*\}', text, re.DOTALL)

        if json_match:
            json_string = json_match.group(0)
            return json.loads(json_string)
        # Root-level array of detections (common model slip)
        arr_match = re.search(r'\[.*\]', text, re.DOTALL)
        if arr_match:
            return json.loads(arr_match.group(0))

        print("Error: No JSON Legend/Object/symbol found in response.")
        return None

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return None
def fallback_classification(ocr):
    ocr_upper = ocr.upper()

    if any(x in ocr_upper for x in ["DUCT", "L/S", "AHU", "GRILLE", "DIFFUSER"]):
        return "VENTILATION_LAYOUT"

    if any(x in ocr_upper for x in ["CONTROL", "SCHEMATIC", "PANEL", "INTERLOCK"]):
        return "SCHEMATIC"

    return "UNKNOWN"


def extract_drawing_number(ocr):
    # Typical drawing number pattern
    match = re.search(r'[A-Z0-9\-]{15,}', ocr)
    return match.group() if match else ""


def extract_continuations(ocr):
    refs = re.findall(r'REFER TO\s+([A-Z0-9\-]+)', ocr.upper())
    return list(set(refs))

def detect_drawing_type(img, ocr):
    prompt = f"""
    Classify HVAC drawing.

    OCR:
    {ocr}

    RULES:
    - drawing_type:
        - VENTILATION_LAYOUT → mentioned in DRAWING TITLE
        - SCHEMATIC → mentioned in DRAWING TITLE

    - Extract current drawing number from current DRAWING No. block
    - Extract continuation references from: 
      "FOR CONTINUATION REFER TO XXXXX"
      reference drawing ids which is mentioned in drawing
    RETURN STRICT JSON ONLY (NO TEXT, NO MARKDOWN):
    {{
      "drawing_type": "VENTILATION_LAYOUT" or "SCHEMATIC", # extract from DRAWING TITLE
      "confidence": 0.0,
      "current_drawing_no": "TH-IS-01-001-M-00481-60-5704B1", #its just a example give the current DRAWING No. which is mentioned in drawing
      "continuation_refs": [
        "TH-IS-02-001-M-00481-60-5702B1", #its just a example
        # give the reference drawing ids which is mentioned in drawing
      ]
    }}
    """

    try:
        # -------------------------------
        # Model fallback (same style)
        # -------------------------------
        model_name = "gemini-3-pro-preview"
        try:
            model = genai.GenerativeModel(model_name)
        except Exception:
            try:
                model = genai.GenerativeModel("gemini-3.1-pro-preview")
            except Exception:
                model = genai.GenerativeModel("gemini-2.0-flash")

        # -------------------------------
        # Generate response
        # -------------------------------
        response = model.generate_content(
            [prompt, img],
            generation_config={
                "temperature": 0.0,
                "top_p": 1.0,
                "top_k": 1,
                "max_output_tokens": 5536
            }
        )

        # Extract text from response
        if not response:
            return None

        response_text = None
        # -------------------------------
        # Use JSON FIRST
        # -------------------------------
        if hasattr(response, 'text') and response.text:
            response_text = response.text
        elif hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, 'content'):
                    if hasattr(candidate.content, 'parts'):
                        for part in candidate.content.parts:
                            if hasattr(part, 'text'):
                                response_text = part.text
                                break
                    elif hasattr(candidate.content, 'text'):
                        response_text = candidate.content.text

                if response_text:
                    break

        # Debug (VERY IMPORTANT)
        print("\n===== RAW MODEL RESPONSE =====\n", response_text)
        # -------------------------------
        # Parse JSON
        # -------------------------------
        drawing_json = extract_json_from_response(response_text) or {}

        drawing_type = drawing_json.get("drawing_type")
        drawing_no = drawing_json.get("current_drawing_no")
        confidence =  drawing_json.get("confidence")
        continuation_refs = drawing_json.get("continuation_refs", [])

        # -------------------------------
        # Normalize drawing_type
        # -------------------------------
        if drawing_type:
            drawing_type = drawing_type
            if drawing_type not in ["VENTILATION_LAYOUT", "SCHEMATIC"]:
                drawing_type = fallback_classification(ocr)

        # -------------------------------
        # Fallback extraction if missing
        # -------------------------------
        if not drawing_no:
            drawing_no = extract_drawing_number(ocr)

        if not continuation_refs:
            continuation_refs = extract_continuations(ocr)
        # -------------------------------
        # Final structured output
        # -------------------------------
        return drawing_type,confidence,drawing_no,continuation_refs

    except Exception as e:
        print(f"Error in detect_drawing_type: {e}")

        # HARD fallback (never return None)
        return fallback_classification(ocr),extract_drawing_number(ocr),extract_continuations(ocr)



def aov_layout_devices(drawing):
    if drawing in ["VENTILATION_LAYOUT","VENTILATION LAYOUT"]:
        device_list = """DETECTION RULES BY HVAC / SMOKE VENTILATION DEVICE SHAPE:
        
        Here is the BS 9999, BS EN 12101 and DW144 standard reference list for Smoke Ventilation and HVAC systems, which will be used to calibrate detection logic.
        
        lifts, doors dont miss any object you are keep missing objects.
        
        The Legends/Objects/symbols used in this layout correspond to ISO / BS HVAC and Smoke Ventilation standards.
        
        -----------------------------------
        ARCHITECTURAL ELEMENTS
        -----------------------------------
        
        Lifts:
        Detect lift by Text "Lift" and "Evacuation Lift" locating closed rectangular contours containing an 'X' pattern formed by two intersecting diagonal lines.
        
        Doors:
        Detect 'Door' objects by identifying the 'Wall Break' and swing arc. Classify as Single, Double, or Sliding.
        
        Rooms/Lobby/Stores/Zones:
        Identify all closed polygons and extract center text for zone classification.
        
        ### COLOR INTERPRETATION ENGINE (MANDATORY)
        
        This drawing is COLOR-CODED. You MUST use color as PRIMARY signal.
        
        Priority Order:
        1. TEXT (highest priority)
        2. COLOR (second priority)
        3. SHAPE (fallback only)
        
        System Mapping:
        
        - RED / PURPLE → Smoke Extract System (LIFE SAFETY CRITICAL)
        - ORANGE → Extract Air System
        - DARK GREEN → Supply Air
        - LIGHT GREEN → Return Air
        - LIGHT BLUE → Fresh Air
        - TEAL → Relief Air
        - LIGHT PINK → Transfer Air
        
        If a duct has color:
        → classify system EVEN IF text is missing
        
        If RED/PURPLE system exists:
        → you MUST fully trace it end-to-end (NO PARTIAL DETECTION ALLOWED)
        
        -----------------------------------
        1. AOV & SMOKE CONTROL FAMILY
        -----------------------------------
        
        AOV (Automatic Opening Vent):
        Detect rectangular or louvered symbols labeled "AOV", "SMOKE VENT". Usually placed on façade or shaft walls.
        
        Smoke Shaft:
        Detect enclosed vertical zones labeled "SMOKE SHAFT" or "SHAFT".
        
        AOV Damper:
        Detect rectangular damper labeled "AOV DAMPER" or "24V DAMPER".
        
        -----------------------------------
        2. DUCTWORK FAMILY (CRITICAL)
        -----------------------------------
        
        Ductwork:
        Detect continuous duct paths represented by:
        - double parallel lines
        - single line schematic
        - dashed hidden ducts
        
        Classify ducts using text or context:
        - Supply Air (SA)
        - Extract Air (EA)
        - Smoke Extract (SE)
        
        Fire Rated Duct:
        Detect ducts labeled "FR", "FIRE RATED", "FD".
        
        -----------------------------------
        3. DAMPER FAMILY
        -----------------------------------
        
        Smoke Damper (SD / SD1):
        Detect rectangular damper with cross/blade or labeled SD / SD1.
        
        Fire Damper (FD):
        Detect rectangular damper labeled FD.
        
        Volume Control Damper (VCD):
        Detect damper symbol within duct without fire/smoke label.
        
        Refuge Damper (RFD):
        Detect labeled "RFD".
        
        Slot / Enviro Damper:
        Detect labeled "ED" or "Enviro Slot Damper".
        
        -----------------------------------
        4. AIR TERMINAL FAMILY
        -----------------------------------
        
        Extract Grille:
        Detect rectangular grille labeled EG or airflow outward.
        
        Supply Grille:
        Detect rectangular grille labeled SG.
        
        Ceiling Transfer Grille:
        Detect labeled "Transfer Grille".
        
        Diffusers:
        Detect circular or square ceiling diffusers.
        
        -----------------------------------
        5. FAN & EQUIPMENT FAMILY
        -----------------------------------
        
        Extract Fan (EF):
        Detect fan symbol or label "EF".
        
        Supply Fan (SF):
        Detect fan symbol or label "SF".
        
        Smoke Extract Fan:
        Detect fan connected to smoke extract system.
        
        AHU (Air Handling Unit):
        Detect rectangular equipment labeled "AHU".
        
        -----------------------------------
        6. SENSOR & CONTROL FAMILY
        -----------------------------------
        
        Pressure Sensor:
        Detect labeled "PRESSURE SENSOR".
        
        Thermostat:
        Detect labeled "THERMOSTAT".
        
        Rain Sensor:
        Detect labeled "RAIN SENSOR".
        
        Key Switch:
        Detect labeled "KEY SWITCH".
        
        Fireman Override Switch:
        Detect labeled "FIREMAN'S OVERRIDE SWITCH".
        
        Control Panel (OS / OS2 Panel):
        Detect labeled control panels.
        
        -----------------------------------
        7. SUPPORT / ELECTRICAL INTERFACE
        -----------------------------------
        
        Junction Box (JB):
        Detect labeled "JB" or "JUNCTION BOX".
        
        -----------------------------------
        ADDITIONAL SMOKE CONTROL COMPONENTS (CRITICAL FOR THIS DRAWING)
        -----------------------------------
        
        OS / OS2 Smoke Control Panel:
        Detect labeled "OS", "OS2", smoke control panel near shafts or lobbies.
        
        Fireman’s Override Switch:
        Detect labeled "FIREMAN OVERRIDE" or similar near shafts.
        
        Pressure Relief Damper (PRD):
        Detect labeled "PRD" within duct or shaft.
        
        Backdraft Damper (BD):
        Detect labeled "BD" or gravity damper in duct branches.
        
        Attenuator / Silencer:
        Detect rectangular block inside duct labeled attenuator or silencer.
        
        Access Panel (AP):
        Detect small labeled "AP" on ducts.
        
        Motorised Smoke Damper:
        Differentiate dampers labeled motorised vs standard.
        
        Vertical Duct Indicators:
        Detect text:
        "DROP FROM ABOVE", "RISE TO ABOVE"
        
        Transfer Air Arrows:
        Detect airflow arrows between rooms without ducts.
        
        Smoke Extract Point (SEP):
        Detect labeled "SEP" near grilles.
        
        -----------------------------------
        FINAL DETECTION LOGIC:
        
        Label Rule:
        If a shape has text, the text overrides the shape classification.
        
        Adjacency Rule:
        If a damper is placed inside a duct, associate it with that duct system.
        
        System Awareness Rule:
        Ducts, dampers, AOVs, and fans are interconnected—detect them together logically.
        
        Detect all objects, including:
        - rotated symbols
        - wall-mounted symbols
        - ceiling-mounted symbols
        
        Detect other all objects which you knowledge.
        
        BS 9999, BS EN 12101, DW144 standards apply.
        
        -----------------------------------
        ARCHITECTURAL ELEMENTS
        -----------------------------------
        
        Lifts:
        Detect "Lift" / "Evacuation Lift" → rectangle with X.
        
        Doors:
        Detect wall breaks with swing arcs.
        
        Rooms:
        Closed polygons with text.
        
        -----------------------------------
        1. AOV & SMOKE CONTROL
        -----------------------------------
        
        AOV:
        Detect labeled "AOV", "SMOKE VENT"
        
        Smoke Shaft:
        Detect labeled "SMOKE SHAFT"
        
        AOV Damper:
        Detect labeled "AOV DAMPER"
        
        -----------------------------------
        2. DUCTWORK (CRITICAL)
        -----------------------------------
        
        Detect:
        - double line ducts
        - single line ducts
        - dashed ducts
        
        Classify:
        - SA
        - EA
        - SE
        
        Fire Rated:
        Detect "FR", "FIRE"
        
        -----------------------------------
        3. DAMPERS
        -----------------------------------
        
        SD / SD1 → Smoke Damper  
        FD → Fire Damper  
        VCD → Volume Control  
        PRD → Pressure Relief  
        BD → Backdraft  
        
        -----------------------------------
        4. AIR TERMINALS
        -----------------------------------
        
        EG → Extract Grille  
        SG → Supply Grille  
        Transfer Grille  
        Diffuser  
        
        -----------------------------------
        5. FANS
        -----------------------------------
        
        EF → Extract Fan  
        SF → Supply Fan  
        Smoke Extract Fan  
        AHU  
        
        -----------------------------------
        6. CONTROLS
        -----------------------------------
        
        Pressure Sensor  
        Thermostat  
        Rain Sensor  
        Key Switch  
        Fireman Override  
        OS / OS2 Panel  
        
        -----------------------------------
        7. ELECTRICAL
        -----------------------------------
        
        JB → Junction Box  
        
        -----------------------------------
        8. ENGINEERING DATA EXTRACTION (CRITICAL)
        -----------------------------------
        
        You MUST extract ALL engineering text near objects.
        
        DAMPER TAGS:
        - SCD-B1-S-416
        - VCD-B1-S-407
        
        DUCT SIZE:
        - 750x400
        - 600x400
        
        
        AHU:
        - AHU-01, AHU-02
        - Duty / Standby
        
        GRILLE SIZE:
        - e.g. 600x600
        
        FFL:
        - floor levels
        
        RULE:
        - Extract EXACT text
        - Attach to nearest object
        - DO NOT skip small text
        """
    elif drawing in ["SCHEMATIC","VENTILATION SCHEMATIC"]:
        device_list = """DETECTION RULES BY HVAC / SMOKE VENTILATION DEVICE SHAPE + COLOR (CRITICAL):

        This drawing uses COLOR-CODED HVAC SYSTEMS. Color is a PRIMARY classification signal and MUST be used along with shape and text.

        -----------------------------------
        COLOR → SYSTEM MAPPING (MANDATORY)
        -----------------------------------

        Yellow:
        Unused / Future Services → Ignore for active system logic but detect as infrastructure.

        Light Blue (Cyan):
        Fresh Air Duct (FA) → Incoming air system

        Teal (Blue-Green):
        Relief Air Duct (RA Relief) → Pressure relief system

        Dark Green:
        Supply Air Duct (SA) → Clean air supply system

        Light Green:
        Return Air Duct (RA) → Return air path

        Light Pink:
        Transfer Air → Passive airflow between rooms (no duct sometimes)

        Orange:
        Extract Air Duct (EA) → Mechanical extract system

        Red:
        Exhaust Air / Smoke Extract Duct (SE) → CRITICAL LIFE SAFETY SYSTEM

        Purple (Violet):
        Smoke Extract Duct (Dedicated Fire Rated)

        Magenta:
        Smoke Extract Shaft / Riser

        Black Arrow:
        Airflow Direction → ALWAYS detect for system flow validation

        -----------------------------------
        ARCHITECTURAL ELEMENTS
        -----------------------------------

        Lifts:
        Detect by "Lift" / "Evacuation Lift" text + rectangle with X.
        Typically located near Smoke Shafts and AOV systems.

        Doors:
        Detect wall breaks with arcs.
        IMPORTANT: Transfer air (light pink) often occurs across doors.

        Rooms/Zones:
        Closed polygons with text.

        -----------------------------------
        1. AOV & SMOKE CONTROL FAMILY (HIGH PRIORITY)
        -----------------------------------

        AOV (Automatic Opening Vent):
        Usually connected to RED or PURPLE systems.
        Detect façade openings or shaft vents labeled AOV.

        Smoke Shaft:
        Often MAGENTA or connected to RED/PURPLE ducts.
        Vertical enclosure.

        AOV Damper:
        Rectangular damper in RED/PURPLE ducts.

        -----------------------------------
        2. DUCTWORK FAMILY (COLOR-DRIVEN CORE LOGIC)
        -----------------------------------

        Duct Classification MUST use COLOR FIRST, then text:

        Red / Purple:
        → Smoke Extract / Exhaust (SE) (CRITICAL)

        Orange:
        → Extract Air (EA)

        Dark Green:
        → Supply Air (SA)

        Light Green:
        → Return Air (RA)

        Light Blue:
        → Fresh Air (FA)

        Teal:
        → Relief Air

        Light Pink:
        → Transfer Air (may not have ducts)

        Detect:
        - Double line ducts
        - Single line schematic
        - Dashed ducts

        Fire Rated Duct:
        Usually RED / PURPLE + labeled FR / FIRE

        -----------------------------------
        3. DAMPER FAMILY (CONTEXT + COLOR)
        -----------------------------------

        Smoke Damper (SD):
        INSIDE RED / PURPLE ducts

        Fire Damper (FD):
        Located at wall penetrations, any duct color but often RED systems

        VCD:
        Inside GREEN / ORANGE ducts (non-fire control)

        PRD (Pressure Relief Damper):
        Inside TEAL (relief air) ducts

        Backdraft Damper (BD):
        Located in ORANGE / EXTRACT branches

        Motorised Dampers:
        Typically in RED smoke systems

        -----------------------------------
        4. AIR TERMINAL FAMILY
        -----------------------------------

        Extract Grille:
        Connected to ORANGE or RED ducts

        Supply Grille:
        Connected to DARK GREEN ducts

        Return Grille:
        Connected to LIGHT GREEN ducts

        Transfer Grille:
        LIGHT PINK airflow arrows (may not connect to ducts)

        Diffusers:
        Circular/square, typically on supply (green)

        Smoke Extract Point (SEP):
        Connected to RED system

        -----------------------------------
        5. FAN & EQUIPMENT FAMILY
        -----------------------------------

        Extract Fan (EF):
        Connected to ORANGE ducts

        Supply Fan (SF):
        Connected to GREEN ducts

        Smoke Extract Fan:
        Connected to RED / PURPLE ducts (CRITICAL)

        AHU:
        Connected to GREEN + BLUE systems

        -----------------------------------
        6. SENSOR & CONTROL FAMILY
        -----------------------------------

        Pressure Sensors:
        Often near shafts or TEAL systems

        Thermostat:
        Room-based

        Rain Sensor:
        Linked with AOV systems

        Key Switch / Fireman Override:
        Near shafts / smoke systems

        Control Panels (OS / OS2):
        Near smoke shafts (MAGENTA / RED systems)

        -----------------------------------
        7. ADDITIONAL SMOKE CONTROL COMPONENTS
        -----------------------------------

        Attenuator / Silencer:
        Rectangular block in ducts (often GREEN or ORANGE)

        Access Panel (AP):
        Small label on ducts

        Vertical Indicators:
        "DROP FROM ABOVE", "RISE TO ABOVE"

        Transfer Arrows:
        LIGHT PINK airflow without ducts

        -----------------------------------
        CRITICAL DETECTION LOGIC (UPDATED)
        -----------------------------------

        1. COLOR PRIORITY RULE:
        If color is visible → it OVERRIDES shape classification.

        2. TEXT PRIORITY RULE:
        If text exists → it OVERRIDES both shape and color.

        3. SYSTEM GROUPING RULE:
        Group objects by duct color to form systems:
        - Red/Purple → Smoke system
        - Green → Supply/Return system
        - Orange → Extract system

        4. LIFE SAFETY RULE:
        Red + Purple systems MUST be fully detected with ZERO misses.

        5. FLOW VALIDATION RULE:
        Use BLACK arrows to confirm airflow direction.

        6. ADJACENCY RULE:
        Dampers, grilles, fans MUST belong to nearest colored duct system.

        -----------------------------------
        8. AIRFLOW DATA BLOCK (VERY IMPORTANT)
        -----------------------------------
        
        Many devices (especially dampers, grilles, duct branches, MSFD, SCD, VCD) have a 4-line numerical information block placed beside them.
        
        This MUST be detected and linked to the nearest device.
        
        This block is NOT a separate device.
        It is ATTRIBUTE INFORMATION for the connected HVAC object.
        
        Typical format from legend:
        
        LEFT COLUMN:
        1. FLOW (L/s)
        2. FLOW (SMOKE) (L/s)
        3. PRESSURE DROP (Pa/m)
        4. PRESS. DROP (SMOKE) (Pa/m)
        
        RIGHT COLUMN:
        1. VELOCITY (m/s)
        2. VEL. (SMOKE) (m/s)
        3. DUCT WIDTH (mm)
        4. DUCT HEIGHT (mm)
        
        Example block:
        
        2247    9.36
        —       —
        1.62    600
        —       400
        
        Interpretation:
        - Flow = 2247 L/s
        - Velocity = 9.36 m/s
        - Pressure Drop = 1.62 Pa/m
        - Duct Size = 600x400 mm
        
        Another Example:
        
        89      2.23
        444     11.10
        0.35    200
        6.50    200
        
        Interpretation:
        - Normal Flow = 89 L/s
        - Smoke Flow = 444 L/s
        - Normal Velocity = 2.23 m/s
        - Smoke Velocity = 11.10 m/s
        - Pressure Drop = 0.35 Pa/m
        - Smoke Pressure Drop = 6.50 Pa/m
        - Duct Size = 200x200 mm
        
        MANDATORY RULES:
        
        1. This 4-line block MUST be attached to nearest:
           - Damper
           - Grille
           - Fan
           - Duct branch
           - Smoke control device
        
        2. NEVER detect this block as a separate object.
        
        3. Extract values into attributes:
           - flow_normal
           - flow_smoke
           - velocity_normal
           - velocity_smoke
           - pressure_drop_normal
           - pressure_drop_smoke
           - size
        
        4. If only partial values exist:
           → extract available values only
        
        5. If values are unclear:
           → infer from nearest aligned block carefully
        
        6. This data block is CRITICAL for system validation and must not be ignored.
        
        7. each type of damper's quantity "qty" should be given accurately and separately from drawing
        
        -----------------------------------
        ### DEVICE COUNTING RULE (CRITICAL FIX)
        
        Each device in schematic drawings is identified by a UNIQUE TAG.
        
        Examples:
        - SCD-B1-S-401
        - VCD-B1-E-406
        - MSFD-B1-S-402
        
        RULES:
        
        1. EACH UNIQUE TAG = EXACTLY ONE DEVICE
           → qty MUST be 1 per unique tag
        
        2. DO NOT use total detection count as qty
           ❌ WRONG: qty = 74 for every device
           ✅ CORRECT: qty = number of UNIQUE tags for that device type
        
        3. GROUPING RULE:
           Devices must be grouped by TYPE, but counted by UNIQUE TAGS
        
           Example:
           Smoke Damper:
           Tags:
           [SCD-B1-S-401, SCD-B1-S-402, SCD-B1-S-403]
        
           → qty = 3
        
        4. IF tag exists:
           → qty = number of UNIQUE tags
        
        5. IF tag is missing:
           → qty = number of detected instances ONLY for that type
        
        6. NEVER:
           - assign same qty to all devices
           - use total object count
           - duplicate tags
        
        7. TAG LIST MUST MATCH QTY:
           len(tags) == qty
        
        8. VALIDATION (MANDATORY):
           - If qty > unique tags → FIX IT
           - If all devices have same qty → ERROR → RECALCULATE
         -----------------------------------
        ### AIR TERMINAL EXTRACTION (GRILLES & DIFFUSERS) — CRITICAL FIX
        -----------------------------------
        
        Grilles in layout/sementic drawings DO NOT always have tags.
        
        You MUST detect and process them using SHAPE + SIZE TEXT.
        
        -----------------------------------
        DETECTION RULES
        -----------------------------------
        
        1. Detect ALL grille symbols:
           - rectangular grille (Extract / Supply)
           - square diffuser
           - linear slot diffuser
        
        2. Identify type:
           - Extract Grille → airflow outward / EA / EXTRACT
           - Supply Grille → airflow inward / SA / SUPPLY
           - Transfer Grille → between rooms
        
        -----------------------------------
        SIZE EXTRACTION (MANDATORY)
        -----------------------------------
        
        Search near each grille for size text:
        
        Examples:
        - 600x600
        - 450x300
        - 1200x300
        
        RULE:
        - Assign size to the NEAREST grille
        - Distance-based association (closest text wins)
        
        If multiple grilles share same nearby size text:
        → assign same size to all
        
        -----------------------------------
        ZONE GROUPING (VERY IMPORTANT)
        -----------------------------------
        
        Grilles MUST be grouped by ZONE.
        
        Zone = nearest room text / enclosed space.
        
        Example:
        
        Zone: LOBBY
        Extract Grille:
        - size: 600x600
        - qty: 4
        
        -----------------------------------
        QUANTITY RULE (CRITICAL)
        -----------------------------------
        
        For grilles:
        
        qty = COUNT OF SYMBOLS (NOT TAGS)
        
        Group by:
        - type
        - size
        - zone
        
        Example:
        
        Zone A:
        - 4 × Extract Grille 600x600
        - 2 × Supply Grille 600x600

        -----------------------------------
        -----------------------------------
        FINAL REQUIREMENT:
        -----------------------------------

        DO NOT MISS:
        - Colored ducts (primary system carriers)
        - Dampers inside ducts
        - Grilles at terminals
        - AOV components
        - Smoke shafts (magenta zones)

        Color + Shape + Text MUST be used TOGETHER for detection accuracy.
        """
    else:
        device_list = "None"

    return device_list


def gemini_aov_zones(img1, device_list=None, ocr=None, merged_json=None):

    # img2 = enhance_for_gemini(img2)
    annotated_json = merged_json
    # Your full technical list from the legend

    prompt = f"""
    ### ROLE:
    You are a Senior HVAC Engineer + CAD Auditor
    Here is the NFPA 170 , BS 9999, BS EN 12101, DW144, BS 5839-1 British Standard code of practice for HVAC and AOV systems  specially for UK, standardized list that I will use to calibrate my detection logic:
    lifts, doors  dont miss any object you are keep missing objects.
    The Legends/Objects/symbols used in this layout, correspond to ISO 7010 or BS 5499. 


    You must:
    - Detect ALL objects
    - Extract ALL engineering data
    - Link text to objects
    - Ensure engineering-level completeness

    Standards:
    BS 9999, BS EN 12101, DW144

    ---

    ### INPUT:
    annotated_json = {annotated_json}
    ocr_json = {ocr}

    ---

    ### TARGET Devices and Legends:
    {device_list}
    If device or legend is missing, detect using engineering knowledge.

    ---

    ### DETECTION STRATEGY:

    PASS 1 → Ducts (structure first)  
    PASS 2 → Dampers (inside ducts)  
    PASS 3 → Grilles / terminals  
    PASS 4 → Equipment (AHU, fans)  
    PASS 5 → TEXT extraction (CRITICAL)  
    PASS 6 → Attribute linking  
    PASS 7 → Validation & correction  

    ---

    ## CORE PRINCIPLE

    TEXT = PRIMARY SOURCE OF TRUTH

    ---

    ## TEXT EXTRACTION ENGINE

    PASS 5A → Parse ALL OCR text  
    PASS 5B → Classify  
    PASS 5C → Link  
    PASS 5D → Validate  

    ---

    ## TEXT CLASSIFICATION

    - TAG → SCD-B1-S-416  
    - SIZE → 750x400  
    - AIRFLOW → 2157 L/s  
    - VELOCITY → 6.2 m/s  
    - PRESSURE → 120 Pa / 1.5 Pa/m  
    - ZONE → B2-A  
    - LEVEL → FFL +12.000  
    - AHU → AHU-01  
    - STATUS → Duty / Standby  
    - SYSTEM → SA / EA / SE  

    ---

    ## SPATIAL LINKING

    - Above duct → duct  
    - Inline → duct segment  
    - Near damper → damper  
    - Near grille → grille  

    Never leave text unassigned.

    ---

    ## DUCT RULES

    Extract:
    - size
    - airflow
    - velocity
    - pressure_drop
    - system_type
    - fire_rating
    ## attributes must capture ALL text written near the detected device/symbol.
    # Example values from drawing:
    # size: "400x800", "750x400"
    # level: "I.L 3680", "I.L 4415"
    # airflow: "SUPPLY", "EXTRACT", "CIN FRESH", "CIN EXHAUST", "REFUSE SUPPLY", "REFUSE EXTRACT AIR"
    # tag: "VCD-B1-S-407", "SCD-B1-E-418", "ATT-B1-E-405"
    # ahu: "AHU 01", "AHU 02 CINEMA"
    #
    # IMPORTANT:
    # Do not leave these empty if text is visible near the object.
    # Read nearby annotations carefully and assign them to the correct device only.
    # Preserve exact text from drawing without guessing or normalization.
    Split if values change.
    ### HVAC PERFORMANCE PARAMETER EXTRACTION (MANDATORY – TOP PRIORITY)

    For EACH duct segment (especially Supply, Extract, Smoke ducts), you MUST extract or infer:

    1. Airflow Rate (L/s)
    2. Velocity (m/s)
    3. Pressure Drop (Pa)

    -----------------------------------
    STEP 1: DIRECT TEXT EXTRACTION
    -----------------------------------

    Search near duct segments for text patterns:

    - "xxx L/s"
    - "xxx l/s"
    - "xxx m3/s"
    - "xxx m/s"
    - "xxx Pa"
    - "xxx Pa/m"

    If found:
    → Assign values directly to that duct segment

    -----------------------------------
    STEP 2: CONTEXTUAL ASSOCIATION
    -----------------------------------

    If airflow text is not directly on duct:

    - Look near:
      - grilles
      - diffusers
      - fans
      - branch labels

    → Assign airflow to nearest connected duct

    -----------------------------------
    STEP 3: ENGINEERING INFERENCE (MANDATORY FALLBACK)
    -----------------------------------

    If airflow is NOT found:

    You MUST estimate using:

    - Duct size (width x height)
    - System type (color-based)

    Use standard assumptions:

    Velocity Defaults:
    - Supply Air: 3–5 m/s
    - Extract Air: 4–6 m/s
    - Smoke Extract (RED/PURPLE): 6–10 m/s

    Formula:
    Airflow (L/s) = Area (m²) × Velocity (m/s) × 1000

    -----------------------------------
    STEP 4: PRESSURE DROP ESTIMATION
    -----------------------------------

    If not explicitly given:

    Use standard engineering approximation:

    - Supply ducts: 0.8 – 1.2 Pa/m
    - Extract ducts: 1.0 – 1.5 Pa/m
    - Smoke ducts: 1.5 – 2.5 Pa/m

    Multiply by duct length (estimate from drawing scale)

    -----------------------------------
    STEP 5: CONSISTENCY RULE (CRITICAL)
    -----------------------------------

    - Same duct size + same system → SAME velocity
    - Same branch → airflow must be conserved

    Example:
    Main duct = 1000 L/s  
    Branch splits:
    → 600 + 400 (NOT random values)
    ### DETERMINISTIC OUTPUT RULE (ANTI-VARIATION)

    The same drawing MUST always produce the SAME results.

    To enforce this:

    1. Use fixed assumptions:
       - Velocity ranges MUST NOT change between runs
       - Pressure assumptions MUST NOT change

    2. Sort detections:
       - Left → Right
       - Top → Bottom

    3. Stable ID assignment:
       D-001, D-002, D-003 in spatial order ONLY

    4. Group ducts BEFORE counting devices

    5. DO NOT use randomness or probabilistic variation

    -----------------------------------
    STEP 6: NEVER LEAVE EMPTY FIELDS
    -----------------------------------

    If exact value not found:
    → ALWAYS provide estimated value
    → Mark confidence lower (0.6–0.8)

    EMPTY = FAILURE

    ---

    ## VALIDATION

    - qty = detections  
    - tags = unique  
    - retry if missing  

    ---
    ### HARD CONSTRAINT: BASE DETECTIONS (MANDATORY)

    You are given annotated_json which contains pre-detected objects.

    RULES:
    1. You MUST include ALL objects from annotated_json
    2. You MUST NOT remove or ignore any annotated object
    3. You MAY only:
       - refine labels
       - enrich attributes
       - add missing objects

    4. Final detection count MUST be:
       >= annotated_json count

    If your final count is LESS → REPROCESS until it matches

    ### SELF-CONSISTENCY CHECK (MANDATORY)

    Before finalizing:

    1. Count total detections
    2. Compare with annotated_json count

    IF:
    - detections < annotated_json → RE-RUN detection mentally
    - any duct missing airflow → RE-COMPUTE
    - any empty attribute → FILL using inference

    Repeat until stable and complete

    ## OUTPUT FORMAT

    Return ONLY JSON:

    {{
      "zones": [
        {{
          "zoneId": "Z-01",
          "zoneName": "Level 01",
          "devices": [
            {{
              "id": "D-001",
              "type": "Smoke Damper",
              "qty": 0,
              "tags": []
            }},
            {{
              "id": "D-002",
              "type": "Extract Grille",
              "qty": 0,
              "tags": []
            }}
          ],
          "matrix": [
            {{
              "cause": "Smoke detected",
              "effect": [
                "Activate smoke system",
                "Open dampers",
                "Start fans"
              ]
            }}
          ]
        }}
      ],

      "confidence": 0.0,

      "legend": [
        {{ "abbr": "AOV", "meaning": "Automatic Opening Vent" }}
      ],
    }}

    ---

    ## HARD RULES

    - List all devices you found in drawing
    - List all requirements you found in drawing
    - DO NOT miss text  
    - DO NOT miss colored Legends
    - DO NOT miss size and airflow , velocity and other details mentioned under each legend
    - DO NOT skip small annotations  
    - DO NOT hallucinate  
    - ONLY extract visible data  
    - qty MUST match detections  
    - EVERY object MUST have attributes  
    - DO NOT finalize if critical data missing 
    - DO NOT include legend in detections
    - Make sure json should have all complete result
    """

    try:
        # Use google.generativeai SDK
        # Try gemini-3-pro-preview first, then fallback to available models
        model_name = "gemini-3-pro-preview"
        try:
            model = genai.GenerativeModel(model_name)
        except Exception:
            # Try gemini-2.5-pro as fallback
            model_name = "gemini-3.1-pro-preview"
            try:
                model = genai.GenerativeModel(model_name)
            except Exception:
                try:
                    model_name = "gemini-3.1-pro-preview"
                    model = genai.GenerativeModel(model_name)
                except Exception:
                    # Try gemini-2.0-flash as last resort
                    model_name = "gemini-3.1-pro-preview"
                    model = genai.GenerativeModel(model_name)

        response = model.generate_content(
            [prompt, img1],
            generation_config={
                "temperature": 0.0,
                "top_p": 1.0,
                "top_k": 1,
                "max_output_tokens": 65536
            }
        )

        # Extract text from response
        if not response:
            return None

        response_text = None

        # Try multiple ways to extract text from response
        if hasattr(response, 'text'):
            response_text = response.text
        elif hasattr(response, 'candidates') and response.candidates:
            # Try to get text from candidates
            for candidate in response.candidates:
                if hasattr(candidate, 'content'):
                    if hasattr(candidate.content, 'parts'):
                        parts = candidate.content.parts
                        for part in parts:
                            if hasattr(part, 'text'):
                                response_text = part.text
                                break
                    elif hasattr(candidate.content, 'text'):
                        response_text = candidate.content.text
                        break
                if response_text:
                    break

        return response_text

    except Exception as e:
        print(f"Error in gemini_cad_analysis: {e}")
        return None

def gemini_aov_info(img1, device_list=None, ocr=None, merged_json=None):

    # img2 = enhance_for_gemini(img2)
    annotated_json = merged_json
    # Your full technical list from the legend

    prompt = f"""
    ### ROLE:
    You are a Senior HVAC Engineer + CAD Auditor
    Here is the NFPA 170 , BS 9999, BS EN 12101, DW144, BS 5839-1 British Standard code of practice for HVAC and AOV systems  specially for UK, standardized list that I will use to calibrate my detection logic:
    lifts, doors  dont miss any object you are keep missing objects.
    The Legends/Objects/symbols used in this layout, correspond to ISO 7010 or BS 5499. 


    You must:
    - Detect ALL objects
    - Extract ALL engineering data
    - Link text to objects
    - Ensure engineering-level completeness

    Standards:
    BS 9999, BS EN 12101, DW144

    ---

    ### INPUT:
    annotated_json = {annotated_json}
    ocr_json = {ocr}

    ---

    ### TARGET Devices and Legends:
    {device_list}
    If device or legend is missing, detect using engineering knowledge.

    ---

    ### DETECTION STRATEGY:

    PASS 1 → Ducts (structure first)  
    PASS 2 → Dampers (inside ducts)  
    PASS 3 → Grilles / terminals  
    PASS 4 → Equipment (AHU, fans)  
    PASS 5 → TEXT extraction (CRITICAL)  
    PASS 6 → Attribute linking  
    PASS 7 → Validation & correction  

    ---

    ## CORE PRINCIPLE

    TEXT = PRIMARY SOURCE OF TRUTH

    ---

    ## TEXT EXTRACTION ENGINE

    PASS 5A → Parse ALL OCR text  
    PASS 5B → Classify  
    PASS 5C → Link  
    PASS 5D → Validate  

    ---

    ## TEXT CLASSIFICATION

    - TAG → SCD-B1-S-416  
    - SIZE → 750x400  
    - AIRFLOW → 2157 L/s  
    - VELOCITY → 6.2 m/s  
    - PRESSURE → 120 Pa / 1.5 Pa/m  
    - ZONE → B2-A  
    - LEVEL → FFL +12.000  
    - AHU → AHU-01  
    - STATUS → Duty / Standby  
    - SYSTEM → SA / EA / SE  

    ---

    ## SPATIAL LINKING

    - Above duct → duct  
    - Inline → duct segment  
    - Near damper → damper  
    - Near grille → grille  

    Never leave text unassigned.

    ---

    ## DUCT RULES

    Extract:
    - size
    - airflow
    - velocity
    - pressure_drop
    - system_type
    - fire_rating
    ## attributes must capture ALL text written near the detected device/symbol.
    # Example values from drawing:
    # size: "400x800", "750x400"
    # level: "I.L 3680", "I.L 4415"
    # airflow: "SUPPLY", "EXTRACT", "CIN FRESH", "CIN EXHAUST", "REFUSE SUPPLY", "REFUSE EXTRACT AIR"
    # tag: "VCD-B1-S-407", "SCD-B1-E-418", "ATT-B1-E-405"
    # ahu: "AHU 01", "AHU 02 CINEMA"
    #
    # IMPORTANT:
    # Do not leave these empty if text is visible near the object.
    # Read nearby annotations carefully and assign them to the correct device only.
    # Preserve exact text from drawing without guessing or normalization.
    Split if values change.
    ### HVAC PERFORMANCE PARAMETER EXTRACTION (MANDATORY – TOP PRIORITY)

    For EACH duct segment (especially Supply, Extract, Smoke ducts), you MUST extract or infer:

    1. Airflow Rate (L/s)
    2. Velocity (m/s)
    3. Pressure Drop (Pa)

    -----------------------------------
    STEP 1: DIRECT TEXT EXTRACTION
    -----------------------------------

    Search near duct segments for text patterns:

    - "xxx L/s"
    - "xxx l/s"
    - "xxx m3/s"
    - "xxx m/s"
    - "xxx Pa"
    - "xxx Pa/m"

    If found:
    → Assign values directly to that duct segment

    -----------------------------------
    STEP 2: CONTEXTUAL ASSOCIATION
    -----------------------------------

    If airflow text is not directly on duct:

    - Look near:
      - grilles
      - diffusers
      - fans
      - branch labels

    → Assign airflow to nearest connected duct

    -----------------------------------
    STEP 3: ENGINEERING INFERENCE (MANDATORY FALLBACK)
    -----------------------------------

    If airflow is NOT found:

    You MUST estimate using:

    - Duct size (width x height)
    - System type (color-based)

    Use standard assumptions:

    Velocity Defaults:
    - Supply Air: 3–5 m/s
    - Extract Air: 4–6 m/s
    - Smoke Extract (RED/PURPLE): 6–10 m/s

    Formula:
    Airflow (L/s) = Area (m²) × Velocity (m/s) × 1000

    -----------------------------------
    STEP 4: PRESSURE DROP ESTIMATION
    -----------------------------------

    If not explicitly given:

    Use standard engineering approximation:

    - Supply ducts: 0.8 – 1.2 Pa/m
    - Extract ducts: 1.0 – 1.5 Pa/m
    - Smoke ducts: 1.5 – 2.5 Pa/m

    Multiply by duct length (estimate from drawing scale)

    -----------------------------------
    STEP 5: CONSISTENCY RULE (CRITICAL)
    -----------------------------------

    - Same duct size + same system → SAME velocity
    - Same branch → airflow must be conserved

    Example:
    Main duct = 1000 L/s  
    Branch splits:
    → 600 + 400 (NOT random values)
    ### DETERMINISTIC OUTPUT RULE (ANTI-VARIATION)

    The same drawing MUST always produce the SAME results.

    To enforce this:

    1. Use fixed assumptions:
       - Velocity ranges MUST NOT change between runs
       - Pressure assumptions MUST NOT change

    2. Sort detections:
       - Left → Right
       - Top → Bottom

    3. Stable ID assignment:
       D-001, D-002, D-003 in spatial order ONLY

    4. Group ducts BEFORE counting devices

    5. DO NOT use randomness or probabilistic variation

    -----------------------------------
    STEP 6: NEVER LEAVE EMPTY FIELDS
    -----------------------------------

    If exact value not found:
    → ALWAYS provide estimated value
    → Mark confidence lower (0.6–0.8)

    EMPTY = FAILURE

    ---

    ## VALIDATION

    - qty = detections  
    - tags = unique  
    - retry if missing  

    ---
    ### HARD CONSTRAINT: BASE DETECTIONS (MANDATORY)

    You are given annotated_json which contains pre-detected objects.

    RULES:
    1. You MUST include ALL objects from annotated_json
    2. You MUST NOT remove or ignore any annotated object
    3. You MAY only:
       - refine labels
       - enrich attributes
       - add missing objects

    4. Final detection count MUST be:
       >= annotated_json count

    If your final count is LESS → REPROCESS until it matches

    ### SELF-CONSISTENCY CHECK (MANDATORY)

    Before finalizing:

    1. Count total detections
    2. Compare with annotated_json count

    IF:
    - detections < annotated_json → RE-RUN detection mentally
    - any duct missing airflow → RE-COMPUTE
    - any empty attribute → FILL using inference

    Repeat until stable and complete

    ## OUTPUT FORMAT

    Return ONLY JSON:
    
    {{
      "notes": [
        "Engineering data extracted",
        "Tags, sizes, airflow captured"
      ],
    
      "processing_metadata": {{
        "source_res": [7017, 9934],
        "scale": 1000.0,
        "sector_analysis": "4x4"
      }},
      
        "building_summary": {{
        "building_type": "Residential / Commercial / Mixed-use / Unknown",
        "total_levels": 0,
        "levels": [
          "Level 00",
          "Level 01",
          "Level 02",
          "Roof"
        ]
      }},
      "project_info": {{
        "project_name": "",
        "drawing_title": ""
      }},
    }}

    ---

    ## HARD RULES

    - List all devices you found in drawing
    - List all requirements you found in drawing
    - DO NOT miss text  
    - DO NOT miss colored Legends
    - DO NOT miss size and airflow , velocity and other details mentioned under each legend
    - DO NOT skip small annotations  
    - DO NOT hallucinate  
    - ONLY extract visible data  
    - qty MUST match detections  
    - EVERY object MUST have attributes  
    - DO NOT finalize if critical data missing 
    - DO NOT include legend in detections
    - Make sure json should have all complete result
    """

    try:
        # Use google.generativeai SDK
        # Try gemini-3-pro-preview first, then fallback to available models
        model_name = "gemini-3-pro-preview"
        try:
            model = genai.GenerativeModel(model_name)
        except Exception:
            # Try gemini-2.5-pro as fallback
            model_name = "gemini-3.1-pro-preview"
            try:
                model = genai.GenerativeModel(model_name)
            except Exception:
                try:
                    model_name = "gemini-3.1-pro-preview"
                    model = genai.GenerativeModel(model_name)
                except Exception:
                    # Try gemini-2.0-flash as last resort
                    model_name = "gemini-3.1-pro-preview"
                    model = genai.GenerativeModel(model_name)

        response = model.generate_content(
            [prompt, img1],
            generation_config={
                "temperature": 0.0,
                "top_p": 1.0,
                "top_k": 1,
                "max_output_tokens": 65536
            }
        )

        # Extract text from response
        if not response:
            return None

        response_text = None

        # Try multiple ways to extract text from response
        if hasattr(response, 'text'):
            response_text = response.text
        elif hasattr(response, 'candidates') and response.candidates:
            # Try to get text from candidates
            for candidate in response.candidates:
                if hasattr(candidate, 'content'):
                    if hasattr(candidate.content, 'parts'):
                        parts = candidate.content.parts
                        for part in parts:
                            if hasattr(part, 'text'):
                                response_text = part.text
                                break
                    elif hasattr(candidate.content, 'text'):
                        response_text = candidate.content.text
                        break
                if response_text:
                    break

        return response_text

    except Exception as e:
        print(f"Error in gemini_cad_analysis: {e}")
        return None


def gemini_aov_sementic_devices(img1, device_list=None, ocr=None, merged_json=None):
    # img2 = enhance_for_gemini(img2)
    annotated_json = merged_json
    # Your full technical list from the legend

    prompt = f"""
    ### ROLE:
    You are a Senior HVAC Engineer + CAD Auditor
    Here is the NFPA 170 , BS 9999, BS EN 12101, DW144, BS 5839-1 British Standard code of practice for HVAC and AOV systems  specially for UK, standardized list that I will use to calibrate my detection logic:
    lifts, doors  dont miss any object you are keep missing objects.
    The Legends/Objects/symbols used in this layout, correspond to ISO 7010 or BS 5499. 


    You must:
    - Detect ALL objects
    - Extract ALL engineering data
    - Link text to objects
    - Ensure engineering-level completeness

    Standards:
    BS 9999, BS EN 12101, DW144

    ---

    ### INPUT:
    annotated_json = {annotated_json}
    ocr_json = {ocr}

    ---

    ### TARGET Devices and Legends:
    {device_list}
    If device or legend is missing, detect using engineering knowledge.

    ---

    ### DETECTION STRATEGY:

    PASS 1 → Ducts (structure first)  
    PASS 2 → Dampers (inside ducts)  
    PASS 3 → Grilles / terminals  
    PASS 4 → Equipment (AHU, fans)  
    PASS 5 → TEXT extraction (CRITICAL)  
    PASS 6 → Attribute linking  
    PASS 7 → Validation & correction  

    ---

    ## CORE PRINCIPLE

    TEXT = PRIMARY SOURCE OF TRUTH

    ---

    ## TEXT EXTRACTION ENGINE

    PASS 5A → Parse ALL OCR text  
    PASS 5B → Classify  
    PASS 5C → Link  
    PASS 5D → Validate  

    ---

    ## TEXT CLASSIFICATION

    - TAG → SCD-B1-S-416  
    - SIZE → 750x400  
    - AIRFLOW → 2157 L/s  
    - VELOCITY → 6.2 m/s  
    - PRESSURE → 120 Pa / 1.5 Pa/m  
    - ZONE → B2-A  
    - LEVEL → FFL +12.000  
    - AHU → AHU-01  
    - STATUS → Duty / Standby  
    - SYSTEM → SA / EA / SE  

    ---

    ## SPATIAL LINKING

    - Above duct → duct  
    - Inline → duct segment  
    - Near damper → damper  
    - Near grille → grille  

    Never leave text unassigned.

    ---

    ## DUCT RULES

    Extract:
    - size
    - airflow
    - velocity
    - pressure_drop
    - system_type
    - fire_rating
    ## attributes must capture ALL text written near the detected device/symbol.
    # Example values from drawing:
    # size: "400x800", "750x400"
    # level: "I.L 3680", "I.L 4415"
    # airflow: "SUPPLY", "EXTRACT", "CIN FRESH", "CIN EXHAUST", "REFUSE SUPPLY", "REFUSE EXTRACT AIR"
    # tag: "VCD-B1-S-407", "SCD-B1-E-418", "ATT-B1-E-405"
    # ahu: "AHU 01", "AHU 02 CINEMA"
    #
    # IMPORTANT:
    # Do not leave these empty if text is visible near the object.
    # Read nearby annotations carefully and assign them to the correct device only.
    # Preserve exact text from drawing without guessing or normalization.
    Split if values change.
    ### HVAC PERFORMANCE PARAMETER EXTRACTION (MANDATORY – TOP PRIORITY)

    For EACH duct segment (especially Supply, Extract, Smoke ducts), you MUST extract or infer:

    1. Airflow Rate (L/s)
    2. Velocity (m/s)
    3. Pressure Drop (Pa)

    -----------------------------------
    STEP 1: DIRECT TEXT EXTRACTION
    -----------------------------------

    Search near duct segments for text patterns:

    - "xxx L/s"
    - "xxx l/s"
    - "xxx m3/s"
    - "xxx m/s"
    - "xxx Pa"
    - "xxx Pa/m"

    If found:
    → Assign values directly to that duct segment

    -----------------------------------
    STEP 2: CONTEXTUAL ASSOCIATION
    -----------------------------------

    If airflow text is not directly on duct:

    - Look near:
      - grilles
      - diffusers
      - fans
      - branch labels

    → Assign airflow to nearest connected duct

    -----------------------------------
    STEP 3: ENGINEERING INFERENCE (MANDATORY FALLBACK)
    -----------------------------------

    If airflow is NOT found:

    You MUST estimate using:

    - Duct size (width x height)
    - System type (color-based)

    Use standard assumptions:

    Velocity Defaults:
    - Supply Air: 3–5 m/s
    - Extract Air: 4–6 m/s
    - Smoke Extract (RED/PURPLE): 6–10 m/s

    Formula:
    Airflow (L/s) = Area (m²) × Velocity (m/s) × 1000

    -----------------------------------
    STEP 4: PRESSURE DROP ESTIMATION
    -----------------------------------

    If not explicitly given:

    Use standard engineering approximation:

    - Supply ducts: 0.8 – 1.2 Pa/m
    - Extract ducts: 1.0 – 1.5 Pa/m
    - Smoke ducts: 1.5 – 2.5 Pa/m

    Multiply by duct length (estimate from drawing scale)

    -----------------------------------
    STEP 5: CONSISTENCY RULE (CRITICAL)
    -----------------------------------

    - Same duct size + same system → SAME velocity
    - Same branch → airflow must be conserved

    Example:
    Main duct = 1000 L/s  
    Branch splits:
    → 600 + 400 (NOT random values)
    ### DETERMINISTIC OUTPUT RULE (ANTI-VARIATION)

    The same drawing MUST always produce the SAME results.

    To enforce this:

    1. Use fixed assumptions:
       - Velocity ranges MUST NOT change between runs
       - Pressure assumptions MUST NOT change

    2. Sort detections:
       - Left → Right
       - Top → Bottom

    3. Stable ID assignment:
       D-001, D-002, D-003 in spatial order ONLY

    4. Group ducts BEFORE counting devices

    5. DO NOT use randomness or probabilistic variation

    -----------------------------------
    STEP 6: NEVER LEAVE EMPTY FIELDS
    -----------------------------------

    If exact value not found:
    → ALWAYS provide estimated value
    → Mark confidence lower (0.6–0.8)

    EMPTY = FAILURE

    ---

    ## VALIDATION

    - qty = detections  
    - tags = unique  
    - retry if missing  

    ---
    ### HARD CONSTRAINT: BASE DETECTIONS (MANDATORY)

    You are given annotated_json which contains pre-detected objects.

    RULES:
    1. You MUST include ALL objects from annotated_json
    2. You MUST NOT remove or ignore any annotated object
    3. You MAY only:
       - refine labels
       - enrich attributes
       - add missing objects

    4. Final detection count MUST be:
       >= annotated_json count

    If your final count is LESS → REPROCESS until it matches

    ### SELF-CONSISTENCY CHECK (MANDATORY)

    Before finalizing:

    1. Count total detections
    2. Compare with annotated_json count

    IF:
    - detections < annotated_json → RE-RUN detection mentally
    - any duct missing airflow → RE-COMPUTE
    - any empty attribute → FILL using inference

    Repeat until stable and complete
    -----------------------------------
    ### AIR TERMINAL EXTRACTION (GRILLES & DIFFUSERS) — CRITICAL FIX
    -----------------------------------
    
    Grilles in layout/sementic drawings DO NOT always have tags.
    
    You MUST detect and process them using SHAPE + SIZE TEXT.
    
    -----------------------------------
    DETECTION RULES
    -----------------------------------
    
    1. Detect ALL grille symbols:
       - rectangular grille (Extract / Supply)
       - square diffuser
       - linear slot diffuser
    
    2. Identify type:
       - Extract Grille → airflow outward / EA / EXTRACT
       - Supply Grille → airflow inward / SA / SUPPLY
       - Transfer Grille → between rooms
    
    -----------------------------------
    SIZE EXTRACTION (MANDATORY)
    -----------------------------------
    
    Search near each grille for size text:
    
    Examples:
    - 600x600
    - 450x300
    - 1200x300
    
    RULE:
    - Assign size to the NEAREST grille
    - Distance-based association (closest text wins)
    
    If multiple grilles share same nearby size text:
    → assign same size to all
    
    -----------------------------------
    ZONE GROUPING (VERY IMPORTANT)
    -----------------------------------
    
    Grilles MUST be grouped by ZONE.
    
    Zone = nearest room text / enclosed space.
    
    Example:
    
    Zone: LOBBY
    Extract Grille:
    - size: 600x600
    - qty: 4
    
    -----------------------------------
    QUANTITY RULE (CRITICAL)
    -----------------------------------
    
    For grilles:
    
    qty = COUNT OF SYMBOLS (NOT TAGS)
    
    Group by:
    - type
    - size
    - zone
    
    Example:
    
    Zone A:
    - 4 × Extract Grille 600x600
    - 2 × Supply Grille 600x600

    ## OUTPUT FORMAT

    Return ONLY JSON:
    
    {{
      "detections": [
        {{
          "label": "Smoke Damper",
          "box_2d": [0,0,0,0],
          "center": [0,0],
          "room": "",
          "confidence": 0.0,
          "attributes": {{  Each attribute i mention in drawing 400x800  I.L 3680 etc
              "tag": "",               # device tag/ID from drawing (example: VCD-B1-S-407)
              "duct_size": "",         # duct size DUCT WIDTH (mm) DUCT HEIGHT (mm)(example: 400x800, 750x400) IF DUCK
              "grille_size": "",       #
              "level": "",             # invert/bottom level text (example: I.L 3680)
              "airflow": "",           # FLOW (L/s) FLOW (SMOKE) (L/s)
              "velocity": "",          # airflow velocity VELOCITY (m/s) VEL. (SMOKE) (L/s) if mentioned if diagram is semantic values struture will be mention of its a ventilation layout their1    
              "pressure_drop": "",     # pressure drop PRESSURE DROP (Pa/m) PRESS. DROP (SMOKE) (Pa/m) if mentioned
              "zone": "",              # zone reference if shown
              "ahu": "",               # linked AHU reference (example: AHU 01)
              "status": ""             # status like FD, SD, MD, OPEN/CLOSED if shown
          }}
        }}
      ]
    }}

    ---

    ## HARD RULES

    - List all devices you found in drawing
    - List all requirements you found in drawing
    - DO NOT miss text  
    - DO NOT miss colored Legends
    - DO NOT miss size and airflow , velocity and other details mentioned under each legend
    - DO NOT skip small annotations  
    - DO NOT hallucinate  
    - ONLY extract visible data  
    - qty MUST match detections  
    - EVERY object MUST have attributes  
    - DO NOT finalize if critical data missing 
    - DO NOT include legend in detections
    - Make sure json should have all complete result
    """

    try:
        # Use google.generativeai SDK
        # Try gemini-3-pro-preview first, then fallback to available models
        model_name = "gemini-3-pro-preview"
        try:
            model = genai.GenerativeModel(model_name)
        except Exception:
            # Try gemini-2.5-pro as fallback
            model_name = "gemini-3.1-pro-preview"
            try:
                model = genai.GenerativeModel(model_name)
            except Exception:
                try:
                    model_name = "gemini-3.1-pro-preview"
                    model = genai.GenerativeModel(model_name)
                except Exception:
                    # Try gemini-2.0-flash as last resort
                    model_name = "gemini-3.1-pro-preview"
                    model = genai.GenerativeModel(model_name)

        response = model.generate_content(
            [prompt, img1],
            generation_config={
                "temperature": 0.0,
                "top_p": 1.0,
                "top_k": 1,
                "max_output_tokens": 65536
            }
        )

        # Extract text from response
        if not response:
            return None

        response_text = None

        # Try multiple ways to extract text from response
        if hasattr(response, 'text'):
            response_text = response.text
        elif hasattr(response, 'candidates') and response.candidates:
            # Try to get text from candidates
            for candidate in response.candidates:
                if hasattr(candidate, 'content'):
                    if hasattr(candidate.content, 'parts'):
                        parts = candidate.content.parts
                        for part in parts:
                            if hasattr(part, 'text'):
                                response_text = part.text
                                break
                    elif hasattr(candidate.content, 'text'):
                        response_text = candidate.content.text
                        break
                if response_text:
                    break

        return response_text

    except Exception as e:
        print(f"Error in gemini_cad_analysis: {e}")
        return None


def gemini_aov_ventilation_devices(img1, device_list=None, ocr=None, merged_json=None):
    # img2 = enhance_for_gemini(img2)
    annotated_json = merged_json
    # Your full technical list from the legend

    prompt = f"""
    ### ROLE:
    You are a Senior HVAC Engineer + CAD Auditor
    Here is the NFPA 170 , BS 9999, BS EN 12101, DW144, BS 5839-1 British Standard code of practice for HVAC and AOV systems  specially for UK, standardized list that I will use to calibrate my detection logic:
    lifts, doors  dont miss any object you are keep missing objects.
    The Legends/Objects/symbols used in this layout, correspond to ISO 7010 or BS 5499. 


    You must:
    - Detect ALL objects
    - Extract ALL engineering data
    - Link text to objects
    - Ensure engineering-level completeness

    Standards:
    BS 9999, BS EN 12101, DW144

    ---

    ### INPUT:
    annotated_json = {annotated_json}
    ocr_json = {ocr}

    ---

    ### TARGET Devices and Legends:
    {device_list}
    If device or legend is missing, detect using engineering knowledge.

    ---

    ### DETECTION STRATEGY:

    PASS 1 → Ducts (structure first)  
    PASS 2 → Dampers (inside ducts)  
    PASS 3 → Grilles / terminals  
    PASS 4 → Equipment (AHU, fans)  
    PASS 5 → TEXT extraction (CRITICAL)  
    PASS 6 → Attribute linking  
    PASS 7 → Validation & correction  

    ---

    ## CORE PRINCIPLE

    TEXT = PRIMARY SOURCE OF TRUTH

    ---

    ## TEXT EXTRACTION ENGINE

    PASS 5A → Parse ALL OCR text  
    PASS 5B → Classify  
    PASS 5C → Link  
    PASS 5D → Validate  

    ---

    ## TEXT CLASSIFICATION

    - TAG → SCD-B1-S-416  
    - SIZE → 750x400  
    - ZONE → B2-A  
    - LEVEL → FFL +12.000  
    - AHU → AHU-01  
    - STATUS → Duty / Standby  
    - SYSTEM → SA / EA / SE  

    ---

    ## SPATIAL LINKING

    - Above duct → duct  
    - Inline → duct segment  
    - Near damper → damper  
    - Near grille → grille  

    Never leave text unassigned.

    ---

    ## DUCT RULES

    Extract:
    - size
    - airflow
    - system_type
    - fire_rating
    ## attributes must capture ALL text written near the detected device/symbol.
    # Example values from drawing:
    # size: "400x800", "750x400"
    # level: "I.L 3680", "I.L 4415"
    # airflow: "SUPPLY", "EXTRACT", "CIN FRESH", "CIN EXHAUST", "REFUSE SUPPLY", "REFUSE EXTRACT AIR"
    # tag: "VCD-B1-S-407", "SCD-B1-E-418", "ATT-B1-E-405"
    # ahu: "AHU 01", "AHU 02 CINEMA"
    #
    # IMPORTANT:
    # Do not leave these empty if text is visible near the object.
    # Read nearby annotations carefully and assign them to the correct device only.
    # Preserve exact text from drawing without guessing or normalization.
    Split if values change.

    -----------------------------------
    STEP 2: CONTEXTUAL ASSOCIATION
    -----------------------------------

    If airflow text is not directly on duct:

    - Look near:
      - grilles
      - diffusers
      - fans
      - branch labels

    → Assign airflow to nearest connected duct

    -----------------------------------
    STEP 3: ENGINEERING INFERENCE (MANDATORY FALLBACK)
    -----------------------------------

    If airflow is NOT found:

    You MUST estimate using:

    - Duct size (width x height)
    - System type (color-based)


    -----------------------------------
    STEP 5: CONSISTENCY RULE (CRITICAL)
    -----------------------------------

    - Same duct size + same system → SAME velocity
    - Same branch → airflow must be conserved

    Example:
    Main duct = 1000 L/s  
    Branch splits:
    → 600 + 400 (NOT random values)
    ### DETERMINISTIC OUTPUT RULE (ANTI-VARIATION)

    The same drawing MUST always produce the SAME results.

    To enforce this:

    1. Use fixed assumptions:
       - Velocity ranges MUST NOT change between runs
       - Pressure assumptions MUST NOT change

    2. Sort detections:
       - Left → Right
       - Top → Bottom

    3. Stable ID assignment:
       D-001, D-002, D-003 in spatial order ONLY

    4. Group ducts BEFORE counting devices

    5. DO NOT use randomness or probabilistic variation

    -----------------------------------
    STEP 6: NEVER LEAVE EMPTY FIELDS
    -----------------------------------

    If exact value not found:
    → ALWAYS provide estimated value
    → Mark confidence lower (0.6–0.8)

    EMPTY = FAILURE

    ---

    ## VALIDATION

    - qty = detections  
    - tags = unique  
    - retry if missing  

    ---
    ### HARD CONSTRAINT: BASE DETECTIONS (MANDATORY)

    You are given annotated_json which contains pre-detected objects.

    RULES:
    1. You MUST include ALL objects from annotated_json
    2. You MUST NOT remove or ignore any annotated object
    3. You MAY only:
       - refine labels
       - enrich attributes
       - add missing objects

    4. Final detection count MUST be:
       >= annotated_json count

    If your final count is LESS → REPROCESS until it matches

    ### SELF-CONSISTENCY CHECK (MANDATORY)

    Before finalizing:

    1. Count total detections
    2. Compare with annotated_json count

    IF:
    - detections < annotated_json → RE-RUN detection mentally
    - any duct missing airflow → RE-COMPUTE
    - any empty attribute → FILL using inference

    Repeat until stable and complete
   
    ## OUTPUT FORMAT

    Return ONLY JSON:

    {{
      "detections": [
        {{
          "label": "Smoke Damper",
          "box_2d": [0,0,0,0],
          "center": [0,0],
          "room": "",
          "confidence": 0.0,
          "attributes": {{  Each attribute i mention in drawing 400x800  I.L 3680 etc
              "qty": " "               # Count tag/ID from drawing of this devices specially SCD 
              "tag": "",               # device tag/ID from drawing (example: VCD-B1-S-407)
              "size": "",              # duct size (example: 400x800, 750x400)
              "level": "",             # invert/bottom level text (example: I.L 3680)
              "zone": "",              # zone reference if shown
              "ahu": "",               # linked AHU reference (example: AHU 01)
              "status": ""             # status like FD, SD, MD, OPEN/CLOSED if shown
          }}
        }}
      ]
    }}

    ---

    ## HARD RULES

    - List all devices you found in drawing
    - List all requirements you found in drawing
    - DO NOT miss text  
    - DO NOT miss colored Legends
    - DO NOT miss size and airflow , velocity and other details mentioned under each legend
    - DO NOT skip small annotations  
    - DO NOT hallucinate  
    - ONLY extract visible data  
    - qty MUST match detections  
    - EVERY object MUST have attributes  
    - DO NOT finalize if critical data missing 
    - DO NOT include legend in detections
    - Make sure json should have all complete result
    """

    try:
        # Use google.generativeai SDK
        # Try gemini-3-pro-preview first, then fallback to available models
        model_name = "gemini-3-pro-preview"
        try:
            model = genai.GenerativeModel(model_name)
        except Exception:
            # Try gemini-2.5-pro as fallback
            model_name = "gemini-3.1-pro-preview"
            try:
                model = genai.GenerativeModel(model_name)
            except Exception:
                try:
                    model_name = "gemini-3.1-pro-preview"
                    model = genai.GenerativeModel(model_name)
                except Exception:
                    # Try gemini-2.0-flash as last resort
                    model_name = "gemini-3.1-pro-preview"
                    model = genai.GenerativeModel(model_name)

        response = model.generate_content(
            [prompt, img1],
            generation_config={
                "temperature": 0.0,
                "top_p": 1.0,
                "top_k": 1,
                "max_output_tokens": 65536
            }
        )

        # Extract text from response
        if not response:
            return None

        response_text = None

        # Try multiple ways to extract text from response
        if hasattr(response, 'text'):
            response_text = response.text
        elif hasattr(response, 'candidates') and response.candidates:
            # Try to get text from candidates
            for candidate in response.candidates:
                if hasattr(candidate, 'content'):
                    if hasattr(candidate.content, 'parts'):
                        parts = candidate.content.parts
                        for part in parts:
                            if hasattr(part, 'text'):
                                response_text = part.text
                                break
                    elif hasattr(candidate.content, 'text'):
                        response_text = candidate.content.text
                        break
                if response_text:
                    break

        return response_text

    except Exception as e:
        print(f"Error in gemini_cad_analysis: {e}")
        return None


def gemini_aov_pipeline(image_path, ocr=None, merged_json=None):
    # -------------------------------
    # STEP 0: PREPROCESS
    # -------------------------------
    img = preprocess(image_path)

    model = get_gemini_model()
    gen_config = {
        "temperature": 0.0,
        "top_p": 1.0,
        "top_k": 1,
        "max_output_tokens": 65536
    }

    # -------------------------------
    # STEP 1: DRAWING TYPE
    # -------------------------------
    drawing_type, confidence,current_drawing_no,continuation_refs = detect_drawing_type(img, ocr)
    print("drawing_type",drawing_type)
    # -------------------------------
    # STEP 2: DEVICE RULE SET
    # -------------------------------
    device_list = aov_layout_devices(drawing_type)
    print("device_list", device_list)
    # -------------------------------
    # STEP 3: ZONES
    # -------------------------------
    zones_raw = gemini_aov_zones(img, device_list, ocr, merged_json)
    zones_json = extract_json_from_response(zones_raw) or {}
    print("zones_json", zones_json)
    # -------------------------------
    # STEP 4: DEVICES (CORE DETECTION)
    # -------------------------------
    if drawing_type == "VENTILATION_LAYOUT":
        devices_raw = gemini_aov_ventilation_devices(img, device_list, ocr, merged_json)
        devices_json = extract_json_from_response(devices_raw) or {}
    elif drawing_type == "SCHEMATIC":
        devices_raw = gemini_aov_sementic_devices(img, device_list, ocr, merged_json)
        devices_json = extract_json_from_response(devices_raw) or {}
    else:
        devices_json = None
    print("devices_json", devices_json)
    # -------------------------------
    # STEP 5: INFO / METADATA
    # -------------------------------
    info_raw = gemini_aov_info(img, device_list, ocr, merged_json)
    info_json = extract_json_from_response(info_raw) or {}
    print("info_json", info_json)
    # -------------------------------
    # STEP 6: MERGE ALL OUTPUTS
    # -------------------------------
    final_json = {
        "drawing_file_info":{
         "drawing_type": drawing_type,
         "confidence": confidence,
         "current_drawing_no": current_drawing_no,
         "continuation_refs": continuation_refs
        },
        "zones": zones_json.get("zones", []),

        "building_summary": {
            "building_type": "Unknown",
            "total_levels": len(zones_json.get("zones", [])),
            "levels": [z.get("zoneName", "") for z in zones_json.get("zones", [])]
        },

        "project_info": {
            "project_name": "",
            "drawing_title": drawing_type
        },

        "confidence": 0.9,

        "legend": zones_json.get("legend", []),

        "notes": info_json.get("notes", [
            "Engineering data extracted",
            "Multi-pass Gemini pipeline"
        ]),

        "processing_metadata": info_json.get("processing_metadata", {
            "source_res": [],
            "scale": 1.0,
            "sector_analysis": "full"
        }),

        "detections": devices_json.get("detections", [])
    }
    print("final_json",final_json)
    return final_json
