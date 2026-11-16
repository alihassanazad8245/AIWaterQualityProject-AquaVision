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

def pdftoimage(pdf_path, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Detect Windows and set poppler_path
    poppler_path = None
    if platform.system() == "Windows":
        poppler_path = r"C:\poppler\Library\bin"

    images = convert_from_path(
        str(pdf_path),
        dpi=200,
        poppler_path=poppler_path
    )

    image_paths = []
    for i, img in enumerate(images):
        img_path = output_dir / f"{pdf_path.stem}_page_{i+1}.png"
        img.save(img_path)
        image_paths.append(img_path)

    # Return first page path (your current code expects one path)
    return image_paths[0]


response_schema = {
    "type": "Legend",
    "properties": {
        "summary_totals": {
            "type": "Legend",
            "properties": {
                #  DETECTORS (Circles) 
                "Smoke Detector": {"type": "INTEGER"},
                "Multi Criteria Detector (opticalheat)": {"type": "INTEGER"},
                "Smoke Detector-Sounder Base": {"type": "INTEGER"},
                "Multi Criteria Detector (opticalheat)-Sounder Base": {"type": "INTEGER"},
                "Smoke Detector- SounderVAD Base": {"type": "INTEGER"},
                "Smoke Detector-VID Base": {"type": "INTEGER"},
                "ASD": {"type": "INTEGER"},
                "VID": {"type": "INTEGER"},
                "VID Base": {"type": "INTEGER"},

                #  MODULES & INTERFACES (Squares/rectangular s) 
                "Relay Interface Module": {"type": "INTEGER"},
                "Contact Input Module": {"type": "INTEGER"},
                "Quad Inputoutput Module": {"type": "INTEGER"},
                "Fire alarm control / interface modules": {"type": "INTEGER"},
                "Sprinkler flow switches": {"type": "INTEGER"},
                "AOV / smoke vent devices": {"type": "INTEGER"},
                "Door entry / release devices": {"type": "INTEGER"},
                "A-PSU": {"type": "INTEGER"},

                #  NOTIFICATION (Horns/Beacons) 
                "Call Point": {"type": "INTEGER"},
                "Sounderbeacon": {"type": "INTEGER"},
                "Sounder": {"type": "INTEGER"},
                "Beacon": {"type": "INTEGER"},
                "Sounder Base": {"type": "INTEGER"},
                "SounderVAD Base": {"type": "INTEGER"},
                "WP": {"type": "INTEGER"},
                "Combined Disabled Refuge & Fire Telephone": {"type": "INTEGER"},

                #  ARCHITECTURAL & CONTROL 
                "FAP": {"type": "INTEGER"},
                "FRP": {"type": "INTEGER"},
                "TSM": {"type": "INTEGER"},
                "Lifts": {"type": "INTEGER"},
                "Denotes ~ Intrinsically Safe": {"type": "INTEGER"}
            },
            "required": ["Smoke Detector", "Relay Interface Module", "Call Point", "Lifts"]
        },
        "processing_metadata": {
            "type": "Legend",
            "properties": {
                "source_res": {"type": "ARRAY", "items": {"type": "INTEGER"}},
                "scale": {"type": "NUMBER"},
                "sector_analysis": {"type": "STRING"}
            }
        },
        "detections": {
            "type": "ARRAY",
            "items": {
                "type": "Legend",
                "properties": {
                    "label": {"type": "STRING"},
                    "box_2d": {
                        "type": "ARRAY",
                        "items": {"type": "NUMBER"},
                        "description": "[ymin, xmin, ymax, xmax] normalized 0-1000"
                    },
                    "room": {"type": "STRING"},
                    "confidence": {"type": "NUMBER"}
                },
                "required": ["label", "box_2d", "room"]
            }
        }
    }
}

def gemini_cad_analysis(image_path,annotated_path,merged_json):
    img1 = PIL.Image.open(image_path)
    img2 = PIL.Image.open(annotated_path)
    annotated_json=merged_json
    # Your full technical list from the legend
    device_list = """DETECTION RULES BY DEVICE SHAPE:

    Here is the NFPA 170 , BS 5839-1 British Standard code of practice for fire detection and alarm systems, standardized list that I will use to calibrate my detection logic:
    lifts, doors  dont miss any object you are keep missing objects.
    The Legends/Objects/symbols used in this layout, correspond to ISO 7010 or BS 5499. 
    Lifts: Detect lift by Text "Lift" and "Evacuation Lift" locating closed rectangular can contours containing an 'X' pattern formed by two intersecting diagonal lines. Additionally, Ignore rectangular s that contain furniture or bathroom fixture symbols.
    Doors: Detect 'Door' objects by identifying the 'Wall Break' (a gap in parallel wall lines). Within this gap, locate a 'Door Leaf' (a line segment) and its 'Swing Path' (a 90-degree or 180-degree arc). Classify as 'Single Swing' if one arc is present, 'Double' if two mirrored arcs are present, and 'Sliding' if two parallel overlapping rectangular s are found with no arcs.
    Rooms/Lobby/Stores/Zones etc: Identify all closed polygons. For each polygon, extract the text string located at its geometric center. Classify the zone based the extracted text.
    1. The Automatic Detection Family (Circle Base)
    Smoke Detector (Ionization/ Smoke):  Detect a square which has a circular Smoker Detection device with 1 bottom-left colored quadrant red shading only 3 missing quadrants. smoker detector should be red with no text around. it can be located on white background with intersecting gray grid lines of door, shops, roof, storage and on walls. circle have 1/4 red quadrant.
    Smoke Detector (Ionization /Smoke) with Ex ai:  Detect a square which has a circular Smoker Detection device with 1 bottom-left colored quadrant red shading only 3 missing quadrants. smoker detector should be red with no text around. it can be located on white background with intersecting gray grid lines of door, roof, storage and on walls. circle have 1/4 red quadrant. with red text Ex ai.
    Smoke Detector & Sounder Base :Detect above smoker detector with a horn icon attached to it.circle have 1/4 red quadrant.
    Multi Criteria Detector (optical /heat/Smoke): Detect a circular Multi Criteria detection device with the 3 top-left, top-right, and bottom-left colored quadrants. 1 missing quadrant.
    Multi Criteria Detector (optical /heat/Smoke)-Sounder Base :  Detect a circular Multi Criteria detection device with a horn icon attached to it and with the 3 top-left, top-right, and bottom-left colored quadrants . 1 missing quadrant.
    Combined Disabled Refuge & Fire Telephone: Detect a vertical/horizontal or rotated red rectangular  containing a "Telephone Handle" and red dot icon.

    2. The Manual & Module Family (Square Base)
    Manual Call Point: Detect a circular Manual Call Point with two Circles place like atom / Bullseye / Target with center nucleus of red dot its Manual Call point. it can be located on white background with intersecting gray grid lines of door, roof, storage and on walls. circle have 1/4 red quadrant.
    Monitor/Input Module (CIM): Detect a text "CIM" or square/rectangular  with text  "CIM".
    Control/Relay Module (RIM): Detect a text "RIM" or square/rectangular  with text  "RIM".
    Isolator Module: Detect a red square or rectangular  with "ISO" or an "X".
    Water Flow Switch: Detect a red square or rectangular  (or Circle) with an arrow pointing in the direction of flow.
    Tamper Switch: Detect a red square or rectangular  (or Circle) with a cross (X) indicating valve monitoring.

    3. The Notification Family (Triangle/Ray Base)
    Sounder / Horn: Detect a rectangular /square Sounder device with a horn icon and filled with red color.Represents a fire alarm horn or fire equipment. it can be placed roof , doors and on walls vertical/horizontal or rotated .
    Sounder / Horn with Ex ai: Detect a rectangular /square with a horn icon and filled with red color with red text Ex ai.it can be placed roof , doors and on walls vertical/horizontal or rotated .
    Sounder base: Detect a circular hollow Sounder base device with a horn icon attached to it. it can be placed roof.
    Sounder Beacon : Detect a rectangular /square Sounder device with a horn icon with radiating lines and filled with red color.Represents a fire alarm horn or fire equipment with radiating lines (sunburst). it can be placed roof , doors and on walls vertical/horizontal or rotated .
    Sounder Beacon with Ex ai: Detect a rectangular /square Sounder Beacon with Ex ai device with a horn icon with radiating lines and filled with red color.Represents a fire alarm horn or fire equipment with radiating lines (sunburst) with red text Ex ai.it can be placed roof , doors and on walls vertical/horizontal or rotated  .
    Beacon: Detect a D shaped Beacon device 'Siren/Alarm' Red D Shape with Sunburst symbol placed with wall by detecting a red 180 degree semi-circle (arc) that is flush against a vertical wall line. The semi-circle must have a series of short, straight red lines radiating outward from its curved edge like a sunburst vertical/horizontal or rotated  . Filter specifically for the red color channel and look for a 'centroid' where the radiating lines would mathematically intersect.

    Sounder / Horn with Ex ai: Detect a red filled square/rectangular Sounder / Horn device and square with a horn icon (no beacon symbol).Represents a fire alarm horn or fire equipment with red text Ex ai.. 
    Sounder Beacon with Ex ai: Detect a red filled square/rectangular Sounder Beacon device and square with a horn icon with beacon symbol.Represents a fire alarm horn or fire equipment with radiating lines (sunburst),with red text Ex ai.
    Strobe / Beacon with Ex ai: Detect a sun like Half red filled D shape with radiating lines (sunburst). red filled sun logo, often depicting a rising or setting sun with red text Ex ai. 
    Sounder base with Ex ai: Detect above Sounder base device & a horn icon attached and with red text Ex ai.

    4. The Control & Infrastructure Family (Large rectangular  Base)
    Fire Alarm Control Panel (FAP): Detect a red square or rectangular  with red text "FAP" Fire Alarm Control Panel .
    FRP / Annunciator: Detect a Fire Repeater Panel (Medium rectangular ).
    Contact Input Module (CIM): Detect a Square labeled "CIM".
    Emergency Telephone: rectangular  containing a telephone handset icon.
    Aspirating Smoke Detector (ASD): Detect a red square or rectangular /rectangular  labeled "ASD" with sampling pipe lines.
    Contact Input Module (CIM): Detect a red square or rectangular  with red text  "CIM".
    FAP / FRP / TSM (Panels): Detect a red square or rectangular  with red text labels FAP, FRP, or TSM.
    VID / VID Base: Detect a has as a red circle with radiating lines (sunburst). representation of the sun, commonly used as an icon for weather applications or sunrise/sunset times.
    WP (Weatherproof): Detect a has as any red device inside a Square containing a "WP" label.
    ASD (Aspirating Smoke Detection): Detect a red square or rectangular  with red text  "ASD" with pipe lines leading out.
    Refuge Point: rectangular  with a wheelchair icon and a telephone.
    Sprinkler flow switches: Detect a has as a red Square/Circle symbol placed directly inline with water pipework lines.

    Final Detection Logic for JSON Output
    When I perform the audit, I follow these "Anchor Rules":
    Hatch Rule: If a circle has exactly 3 missing quadrant it is Smoke Detector (Ionization) 1 shadded quadrant dont mix it with other objects. If a circle has exactly 1 missing quadrant it is Multi Criteria Detector (optical /heat/Smoke) 270 degree shadded. 
    Label Rule: If a square has text, the text overrides the shape (e.g., QIO > RIM).
    Adjacency Rule: If a horn icon is attached to a red bordered circle, it is a Sounder Base.
    Detect other all objects which you knowledge.
        """

    prompt = f"""
    ### ROLE: 
    You are a Senior Fire Protection Engineer and Lead CAD Auditor specializing in NFPA 170 Fire Safety and Emergency Symbols, NFPA 72 Fire Alarm Systems, and construction-grade life-safety drawings.
    
    Your task is to perform a granular, spatial, device-level audit of a high-resolution Fire Alarm floor plan drawing.
    Detect a has all legends , Objects , infrastructure  and with in the diagram give accurate label and bounding box as per instruction below and you can use your own knowldge too.
    Primary Standard: BS 5839-1
    Legal Framework: Regulatory Reform (Fire Safety) Order 2005
    ### Object Detection results of this image:
    {annotated_json}
    ### INPUT DATA:
    - First Image: CAD Floor Plan (9934x7017 resolution or above).
    - Second Image: CAD Floor Plan (9934x7017 resolution or above) with objectdetection labels and boundaries.
    - Here is 90% accurate object detection based json with labels and boundingbox only detect remaining objects.
    - Target Coordinate System: Normalized [0, 1000] scale. Coordinates MUST represent [ymin, xmin, ymax, xmax] of the individual block.
    - If its a new image analyze from start if its already annotated image find remaining objects which are not annotated and labeled.
    ### AUDIT PROTOCOL:
    1. Source Calibration (Legend/Object/symbol Scan): First, locate the Legend/Object/symbol Table. Lock the visual signatures for hatching density (25% vs 75%) and text tags (RIM, QIO, CIM). 
    2. Global Scanning Strategy: Execute a 4x4 sector scan (Sectors A1 to D4). 
    3. De-Clumping Rule: In "Module Stacks" (e.g., CIM/RIM arrays), you MUST generate a unique bounding box and coordinate set for EACH individual square. Do not group them.
    4. Contextual Validation: Extract the "Room Name" by identifying the nearest large MTEXT or DTEXT object to the device coordinate.

    ### TARGET OBJECTS & LEGENDS description Which are given in above json after Detection:
        {device_list} or any which is in the plan but not in list

    ### RULES:
        1. ARCHITECTURAL: Count 'Lifts' and 'Doors' .
        2. COORDINATES: For EVERY object, you must provide its center coordinate [y, x]. image size which you are processing as your coordinates didn't match actual image size.
        3. All Objects : Legend/Object/symbol can be placed on walls, doors, lift or any wall design ,don't miss any of them.
        4. Objects Placed on walls and  near each other should be detected.
        5. Objects are located on  both plain white background or with placed on walls, door , windows or any other lined structure.
    ### SCANNING STRATEGY:
    - We already provide mostly detected device labels with bounding box you have detecting remaining objects.
    - Sector Analysis: Divide the floor plan into a 4x4 grid. Scan each sector individually to ensure clustered RIMs (like the stack of 21) are not grouped into a single box. Every symbol needs its own unique box.
    - Object rotation check: If any object looks similar to any Legend/Object/symbol but have different rotation must detect it.
    - Blank Check: Must check there detected object is actually a Legend/Object/symbol or just a blank box.
    - Detect all Objects : Detect All Objects  dont miss any one with which have background. most Objects  are colored ones and circle or square/rectangular .
    - Room name: Must detect room name and mention it.
    - Recheck every detected Legend/Object/symbol and undetected object whether its correctly detected or not.
    - Repeat the analysis and detect if many objects are undetected.
    - Dont miss any object , you are keep missing detecting each object and symbol. final json should have every lagend/object.
    ### COORDINATE SYSTEM (MANDATORY & STRICT):
    
    You MUST follow this coordinate system for EVERY detected object.
    
    ### NORMALIZED BOUNDING BOX:
    - All bounding boxes MUST be reported in NORMALIZED IMAGE SPACE.
    - Use a [0, 1000] coordinate system, independent of actual image resolution.
    - Bounding box format:
      [ymin, xmin, ymax, xmax]
    Hard constraints:
    
     - 0 ≤ ymin < ymax ≤ 1000
     - 0 ≤ xmin < xmax ≤ 1000
    
    Bounding box MUST fully enclose the entire visible symbol, including:
     - complete circles of detectors
     - complete square/ rectangular s
     - sounder horns
     - concentric bases
     - bounding box should be on object location dony make it on blank spaces.
    labels that are physically part of the device
    ### CENTER COORDINATE:
    - For EVERY object, compute the CENTER POINT from the bounding box.
    - Center coordinate format:
      [y_center, x_center]
    
    Where:
    - y_center = (ymin + ymax) / 2
    - x_center = (xmin + xmax) / 2
    
    ### IMAGE SIZE INDEPENDENCE:
    - The normalized [0,1000] system MUST be used for ALL images,
      regardless of their actual pixel size (e.g., 7017×9934, 4000×3000, etc.).
    - DO NOT output pixel coordinates.
    - DO NOT scale to image resolution.
    - The consuming system will perform pixel scaling.
    
    ### CONSISTENCY RULE:
    - Bounding boxes and center coordinates MUST be internally consistent.
    - Center coordinates MUST lie INSIDE the bounding box.
    - must check that you are giving right coordinates of each object. also fix bounding box as mejority are detting somewhee else
    cross check the each bounding box it much be around relevent object.
    OUTPUT FORMAT:
        Return ONLY a valid JSON Legend/Object/symbol with this structure (which should have our provided json with further detected objects):
        {{
  "zones": [
    {{
      "zoneId": "Z-01",
      "zoneName": "Level 01",
      "devices": [
        {{ "id": "D-001", "type": "Smoke/Heat Detector", "qty": 14 }},
        {{ "id": "D-002", "type": "Manual Call Point (MCP)", "qty": 6 }},
        include all devices  you detect dont miss anything
       ],
      "matrix": [
        {{
          "cause": "Smoke Detector alarm in Level 01 (any flat/corridor)",
          "effect": [
            "Sound alarm on Level 01",
            "Panel alert at Fire Control",
            "Open nearest AOV in affected corridor",
            "Close FD60/FD30 doors on affected route"
            include all cause &  effect you detect dont miss anything
          ]
        }},
      ]
    }}
  ],
  "legend": [
    {{ "abbr": "device name", "meaning": "Automated Opening Vent" }},
    include all Objects   you detect dont miss anything
   ],
  "notes": [
    "This is a simulated parse for investor demo purposes.",
    "Quantities are placeholders; logic reflects typical Level 01 sequences."
  add note according to your understanding
  ]
     }},
          "processing_metadata": {{"source_res": [7017, 9934],
        "scale": 1000.0,
        "sector_analysis": "4x4_grid_complete"}}, # image size which you are processing as your corrdinates didn't match actual image size.
          "detections": [
            {{"label": "Device Name",
          "box_2d": [ymin, xmin, ymax, xmax],
          "center": [y_center, x_center],
          "room": "Room Name from CAD",
          "confidence": 0.0-1.0}}
          ]
        }}
        }}
        Note: If a device from the Legend/Object/symbol is NOT in the diagram, set its count to 0. Do not guess.
        """

    try:
        # Use google.generativeai SDK
        # Try gemini-3-pro-preview first, then fallback to available models
        model_name = "gemini-3-pro-preview"
        try:
            model = genai.GenerativeModel(model_name)
        except Exception:
            # Try gemini-2.5-pro as fallback
            model_name = "gemini-3-pro-preview"
            try:
                model = genai.GenerativeModel(model_name)
            except Exception:
                try:
                    model_name = "gemini-2.5-pro"
                    model = genai.GenerativeModel(model_name)
                except Exception:
                    # Try gemini-2.0-flash as last resort
                    model_name = "gemini-2.0-flash"
                    model = genai.GenerativeModel(model_name)

        response = model.generate_content([
            prompt,
            img1,
            img2,
        ])

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



def extract_json_from_response(response_text):
    """
    Finds and parses a JSON Legend/Object/symbol from a string,
    even if surrounded by Markdown or prose.
    """
    # Check if response_text is None or empty
    if not response_text:
        print("Error: response_text is None or empty")
        return None

    try:
        # 1. Use Regex to find everything between the first '{' and the last '}'
        # This handles Markdown code blocks like ```json ... ```
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)

        if json_match:
            json_string = json_match.group(0)

            # 2. Parse the string into a Python Dictionary
            data = json.loads(json_string)
            return data
        else:
            print("Error: No JSON Legend/Object/symbol found in response.")
            return None

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return None




import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import hashlib
import colorsys


def label_to_color(label: str):
    """
    Deterministically convert label text to a bright RGB color.
    """
    h = int(hashlib.md5(label.encode()).hexdigest(), 16)

    # Hue from hash
    hue = (h % 360) / 360.0

    # Keep saturation/value in readable range
    sat = 0.75
    val = 0.95

    r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
    return (int(r * 255), int(g * 255), int(b * 255))


import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import numpy as np
import cv2
import pytesseract
import hashlib
import colorsys


def label_to_color(label: str):
    """
    Deterministically convert label text to a bright RGB color.
    """
    h = int(hashlib.md5(label.encode()).hexdigest(), 16)

    hue = (h % 360) / 360.0
    sat = 0.75
    val = 0.95

    r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
    return (int(r * 255), int(g * 255), int(b * 255))


def annotate_cad_image(image_path, json_data, output_path="annotated_cad.png"):

    #  SAFETY CHECK 
    if isinstance(json_data, list):
        json_data = json_data[0]

    #  LOAD IMAGE 
    img = PIL.Image.open(image_path).convert("RGB")
    real_width, real_height = img.size
    draw = PIL.ImageDraw.Draw(img)

    # Convert for OpenCV processing
    cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    #  DYNAMIC SCALING 
    font_size = max(24, int(real_height * 0.008))
    line_width = max(3, int(real_width * 0.0015))

    try:
        font = PIL.ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
    except:
        font = PIL.ImageFont.load_default()

    detections = json_data.get('detections', [])

    valid_smoke_count = 0
    filtered_detections = []

    #  DRAW DETECTIONS 
    for detection in detections:

        label = detection.get('label', 'Unknown')
        box = detection.get('box_2d')

        if not box or len(box) != 4:
            continue

        ymin, xmin, ymax, xmax = box

        #  NORMALIZED → PIXEL 
        left   = float(xmin * real_width) / 1000.0
        top    = float(ymin * real_height) / 1000.0
        right  = float(xmax * real_width) / 1000.0
        bottom = float(ymax * real_height) / 1000.0

        #  CLAMP 
        left   = max(0, min(left, real_width))
        top    = max(0, min(top, real_height))
        right  = max(left, min(right, real_width))
        bottom = max(top, min(bottom, real_height))

        left_i, top_i, right_i, bottom_i = map(int, [left, top, right, bottom])

        # ==================================================
        # SMOKE DETECTOR VALIDATION (Circle + OCR Filter)
        # ==================================================
        if "Smoke" in label:

            roi = cv_img[top_i:bottom_i, left_i:right_i]

            if roi.size == 0:
                continue

            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

            # - OCR CHECK -
            ocr_text = pytesseract.image_to_string(
                gray,
                config="--psm 6 -c tessedit_char_whitelist=O0ZERO"
            ).strip().upper()

            if ocr_text:
                continue  # Ignore detection if any text/number exists


            valid_smoke_count += 1

        # Keep valid detection
        filtered_detections.append(detection)

        #  DYNAMIC COLOR 
        color = label_to_color(label)

        #  DRAW BOX 
        draw.rectangle (
            [left, top, right, bottom],
            outline=color,
            width=line_width
        )

        #  LABEL TEXT 
        text = f" {label} "

        bbox = draw.textbbox((left, top), text, font=font)
        label_height = bbox[3] - bbox[1]

        text_rect = [
            left,
            max(0, top - label_height),
            bbox[2],
            top
        ]

        draw.rectangle (text_rect, fill=color)
        draw.text(
            (left, max(0, top - label_height)),
            text,
            font=font,
            fill="black"
        )

    # ==================================================
    # UPDATE SMOKE DETECTOR COUNT IN JSON
    # ==================================================
    for zone in json_data.get("zones", []):
        for device in zone.get("devices", []):
            if "Smoke" in device.get("type", ""):
                device["qty"] = valid_smoke_count

    # Replace detections with filtered ones
    json_data["detections"] = filtered_detections

    img.save(output_path)

    return img, json_data


