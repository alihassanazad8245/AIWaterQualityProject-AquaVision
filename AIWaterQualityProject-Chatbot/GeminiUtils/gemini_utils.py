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

def pdftoimagegemini(pdf_path, output_dir):
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

from PIL import Image, ImageEnhance
import PIL


def enhance_for_gemini(img):

    # Upscale (helps when original is 6000px)
    w, h = img.size
    img = img.resize((int(w*1.3), int(h*1.3)), Image.LANCZOS)

    # Increase contrast
    contrast = ImageEnhance.Contrast(img)
    img = contrast.enhance(1.5)

    # Increase sharpness
    sharp = ImageEnhance.Sharpness(img)
    img = sharp.enhance(2.0)

    # Slight color boost (helps red symbols)
    color = ImageEnhance.Color(img)
    img = color.enhance(1.2)

    return img


def gemini_fire_alarm_analysis(image_path,merged_json=None):

    img1 = PIL.Image.open(image_path)
    #img2 = PIL.Image.open(annotated_path)

    # Enhance both images before sending to Gemini
    img1 = enhance_for_gemini(img1)
    #img2 = enhance_for_gemini(img2)
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
    ### Object Detection results of this image give exect objects (if not detecting well detect by yourself):
    {annotated_json}
    ### INPUT DATA:
    - First Image: CAD Floor Plan (9934x7017 resolution or above).
    - Second Image: CAD Floor Plan (9934x7017 resolution or above) with objectdetection labels and boundaries.
    - its possibly 100% percent accurate detections if all the object you see are accurate consider them in your analysis and detect remaining too.
    - Target Coordinate System: Normalized [0, 1000] scale. Coordinates MUST represent [ymin, xmin, ymax, xmax] of the individual block.
    - Remove Legends from results.
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
      include all devices you detect dont miss anything dont include objects from legend section.
    ],
    "matrix": [
      {{
        "cause": "Smoke Detector alarm in Level 01 (any flat/corridor)",
        "effect": [
          "Sound alarm on Level 01",
          "Panel alert at Fire Control",
          "Open nearest AOV in affected corridor",
          "Close FD60/FD30 doors on affected route",
          include all cause & effect you detect in the analysis of this image and provided json dont miss anything
        ]
        list causes you identified by your analysis. above are just example formate.
      }}
    ]
  }},

  {{
    "zoneId": "Z-02",
    "zoneName": "Level 02",
    "devices": [
      {{ "id": "D-101", "type": "Smoke/Heat Detector", "qty": 12 }},
      {{ "id": "D-102", "type": "Manual Call Point (MCP)", "qty": 5 }},
      include all devices you detect for this zone dont miss anything dont include objects from legend section.
    ],
    "matrix": [
      {{
        "cause": "Smoke Detector alarm in Level 02 (any flat/corridor)", (this cause and effect is just for formate)
        "effect": [
          "Sound alarm on Level 02",
          "Panel alert at Fire Control",
          "Open nearest AOV in affected corridor",
          "Close FD60/FD30 doors on affected route",
          include all cause & effect iin detail paragraph  you detect in the analysis of this image and provided json dont miss anything
        ]
        list causes & effects in detail paragraph  you identified by your analysis. above are just example formate.
      }}
    ]

    }}
  ],
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
  "confidence": 0.0,
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
        Note: If a device from the Legend/Object/symbol is NOT in the diagram, set its count to 0. Do not guess. dont include bounding boxes of objects detected on legends legend section.
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

        response = model.generate_content(
            [prompt, img1],
            generation_config={
                "temperature": 0.0,
                "top_p": 1.0,
                "top_k": 1,
                "max_output_tokens":65536
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


def resize_for_llm(img):
    w, h = img.size

    if max(w, h) > 4000:
        img.thumbnail((2048, 2048))  # aggressive downscale
    elif max(w, h) > 2000:
        img.thumbnail((2560, 2560))  # moderate
    else:
        pass  # keep original

    return img
def get_image_tiles(img, tile_size=2000, overlap=250):
    """Splits a 9000px image into high-res chunks Gemini can actually read."""
    w, h = img.size
    tiles = []
    for y in range(0, h, tile_size - overlap):
        for x in range(0, w, tile_size - overlap):
            # Define crop box (left, upper, right, lower)
            box = (x, y, min(x + tile_size, w), min(y + tile_size, h))
            tile = img.crop(box)
            tiles.append(tile)
    return tiles


def gemini_aov_analysis1(image_path, ocr=None,merged_json=None):
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

    # img2 = enhance_for_gemini(img2)
    annotated_json = merged_json
    # Your full technical list from the legend
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

    AIRFLOW:
    - 2157 L/s
    - zone labels (B2-A)

    VELOCITY:
    - m/s

    PRESSURE DROP:
    - Pa / Pa/m

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
    
      "building_summary": {{
        "building_type": "Unknown",
        "total_levels": 0,
        "levels": []
      }},
    
      "project_info": {{
        "project_name": "",
        "drawing_title": ""
      }},
    
      "confidence": 0.0,
    
      "legend": [
        {{ "abbr": "AOV", "meaning": "Automatic Opening Vent" }}
      ],
    
      "notes": [
        "Engineering data extracted",
        "Tags, sizes, airflow captured"
      ],
    
      "processing_metadata": {{
        "source_res": [7017, 9934],
        "scale": 1000.0,
        "sector_analysis": "4x4"
      }},
    
      "detections": [
        {{
          "label": "Smoke Damper",
          "box_2d": [0,0,0,0],
          "center": [0,0],
          "room": "",
          "confidence": 0.0,
          "attributes": {{  Each attribute i mention in drawing 400x800  I.L 3680 etc
              "tag": "",               # device tag/ID from drawing (example: VCD-B1-S-407)
              "size": "",              # duct size (example: 400x800, 750x400)
              "level": "",             # invert/bottom level text (example: I.L 3680)
              "airflow": "",           # service/system type (example: SUPPLY, EXTRACT, CIN FRESH)
              "velocity": "",          # airflow velocity if mentioned if diagram is semantic values struture will be mention of its a ventilation layout their1    
              "pressure_drop": "",     # pressure drop if mentioned
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
                "max_output_tokens":65536
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

def gemini_architectural_analysis(image_path, merged_json=None):
    img1 = PIL.Image.open(image_path)
    # img2 = PIL.Image.open(annotated_path)

    # Enhance both images before sending to Gemini
    img1 = enhance_for_gemini(img1)
    # img2 = enhance_for_gemini(img2)
    annotated_json = merged_json
    # Your full technical list from the legend
    device_list = """DETECTION RULES FOR ARCHITECTURAL GENERAL ARRANGEMENT (GA) DRAWINGS (UK STANDARD):

    This drawing type is Architectural GA. Focus on SPACES, CORES, TAGS, and ARCHITECTURAL ELEMENTS.

    -----------------------------------
    1. SPACES / ROOMS (PRIMARY OBJECTS)
    -----------------------------------

    Detect ALL closed room polygons and extract the room name text located at the geometric center.

    Examples of room names to detect:
    - Residents Gym
    - Residents Lounge
    - Entrance Pavilion
    - Entrance Lobby
    - Lobby
    - Circulation
    - Refuse Store
    - Car Park Vent
    - Meeting Room
    - Study Room
    - Kitchen
    - WC
    - Acc WC (Accessible WC)
    - Post Room
    - PT Room
    - Any other labeled room

    Every closed boundary with text is a space and MUST be detected.

    -----------------------------------
    2. APARTMENT / UNIT TAGS (CRITICAL)
    -----------------------------------

    Detect apartment reference tags such as:
    202-C-GF-07-3B-5P

    These tags define apartment identity.

    Extract and classify:
    - Plot number
    - Core letter
    - Level
    - Unit number
    - Bedroom count
    - Person count

    Treat each apartment tag as an object.

    -----------------------------------
    3. CORES / VERTICAL CIRCULATION
    -----------------------------------

    Detect and classify:

    Stair:
    Detect stair flight symbols inside cores labeled Core C/D/E/F Stair.

    Lift:
    Detect rectangular lift shafts labeled:
    - Lift 1
    - Lift 2 (FF)
    - Cycle Lift

    -----------------------------------
    4. RISERS / SHAFTS / AOV RISERS
    -----------------------------------

    Detect vertical shafts labeled:
    - Riser
    - AOV Riser
    - Vent Riser
    - Service Riser

    These are enclosed rectangular shafts with text labels.

    -----------------------------------
    5. DOORS
    -----------------------------------

    Detect doors using:
    Wall break + swing arc.
    Classify as single or double door where possible.

    -----------------------------------
    6. WALLS / ROOM BOUNDARIES
    -----------------------------------

    Detect wall lines forming closed polygons.
    These define rooms and circulation areas.

    -----------------------------------
    7. SPECIAL FUNCTIONAL AREAS
    -----------------------------------

    Detect special zones such as:
    - Refuse Store per core
    - Car Park Vent rooms
    - Entrance lobbies per core
    - Shared resident facilities

    -----------------------------------
    FINAL RULE:

    This is a SPACE-DOMINANT drawing.

    Every closed room, apartment tag, core element, riser, stair, lift, and door MUST be detected.

    If a closed boundary has a name, it is an object.
    """
    prompt = f"""
    ### ROLE: 
    You are a Senior Architectural CAD Auditor specializing in UK Architectural General Arrangement (GA) drawings used for coordination with Fire, AOV, Smoke Ventilation, and MEP disciplines.

    Your task is to perform a granular, spatial, object-level audit of a high-resolution GA floor plan drawing.

    Detect all rooms, apartment tags, cores, stairs, lifts, risers, doors, circulation areas, and architectural spaces within the diagram and provide accurate labels and bounding boxes as per instructions below.

    Primary Context: Architectural GA Drawings (UK)

    ### Object Detection results of this image give exact objects (if result is given and not detecting well detect by yourself):
    {annotated_json}

    ### INPUT DATA:
    - First Image: CAD Floor Plan (9934x7017 resolution or above).
    - Second Image: CAD Floor Plan with object detection labels and boundaries.
    - It is possibly 100% accurate detections; if objects are correct, use them and detect remaining.
    - Target Coordinate System: Normalized [0, 1000] scale.
    - Coordinates MUST represent [ymin, xmin, ymax, xmax].
    - Remove Legends from results.
    - If new image, analyze from start. If annotated, detect remaining objects.

    ### AUDIT PROTOCOL:
    1. Source Calibration (Legend/Object/Text Scan):
       Identify apartment tag format, room naming style, and core labels (Core C/D/E/F).

    2. Global Scanning Strategy:
       Execute a 4x4 sector scan (A1 to D4).

    3. De-Clumping Rule:
       In clustered rooms or tags, generate UNIQUE bounding boxes for EACH object.

    4. Contextual Validation:
       Extract "Room/Space Name" from MTEXT/DTEXT nearest to object.

    ### TARGET OBJECTS & LEGENDS:
    {device_list} or any which is in the plan but not in list

    ### RULES:
    1. ARCHITECTURAL: Count 'Lifts' and 'Doors'.
    2. COORDINATES: For EVERY object, provide center coordinate [y, x].
    3. Objects may be on walls, inside rooms, inside cores—do not miss any.
    4. Detect overlapping or adjacent spaces.
    5. Objects exist on white background and CAD wall structures.

    ### SCANNING STRATEGY:
    - Use provided detections and find missing objects.
    - 4x4 sector scan — no grouping allowed.
    - Detect rotated text and symbols.
    - Validate objects are real spaces/tags (not blank areas).
    - Detect ALL rooms, apartment tags, cores, stairs, lifts, risers, doors.
    - Detect room names.
    - Recheck detections multiple times.
    - DO NOT miss any object.

    ### COORDINATE SYSTEM (MANDATORY):

    ### NORMALIZED BOUNDING BOX:
    - Use [0, 1000] coordinate system.
    - Format: [ymin, xmin, ymax, xmax]

    Constraints:
    - 0 ≤ ymin < ymax ≤ 1000
    - 0 ≤ xmin < xmax ≤ 1000

    Bounding boxes MUST fully enclose:
    - room boundaries
    - apartment tag text
    - stair symbols
    - lift shafts
    - riser shafts
    - doors

    ### CENTER COORDINATE:
    - y_center = (ymin + ymax) / 2
    - x_center = (xmin + xmax) / 2

    ### CONSISTENCY RULE:
    - Center MUST lie inside bounding box
    - Boxes MUST align to actual object
    - Validate every coordinate

    ### OUTPUT FORMAT:

    Return ONLY valid JSON with this structure:

    {{
      "zones": [
        {{
          "zoneId": "Z-01",
          "zoneName": "Core C - Ground Floor",
          "devices": [
            {{ "id": "D-001", "type": "Room", "qty": 14 }},
            {{ "id": "D-002", "type": "Apartment Tag", "qty": 6 }},
            {{ "id": "D-003", "type": "Stair", "qty": 1 }},
            {{ "id": "D-004", "type": "Lift", "qty": 2 }},
            {{ "id": "D-005", "type": "Riser", "qty": 3 }},
            {{ "id": "D-006", "type": "Door", "qty": 18 }}
          ],
          "matrix": [
            {{
              "cause": "Apartment located within Core",
              "effect": [
                "Connected to core lobby",
                "Accessed via door from circulation",
                "Adjacent to rooms/spaces",
                "Served by lift and stair",
                "Contains service riser"
              ]
            }}
          ]
        }}
      ],

      "building_summary": {{
        "building_type": "Residential / Commercial / Mixed-use / Unknown",
        "total_levels": 0,
        "levels": [
          "Ground Floor",
          "Level 01",
          "Level 02",
          "Roof"
        ]
      }},

      "project_info": {{
        "project_name": "",
        "drawing_title": ""
      }},

      "confidence": 0.0,

      "legend": [
        {{ "abbr": "Room", "meaning": "Closed space with text label" }},
        {{ "abbr": "Apartment Tag", "meaning": "Unit identification string" }},
        {{ "abbr": "Riser", "meaning": "Vertical service shaft" }}
      ],

      "notes": [
        "Legend excluded from counts",
        "All spaces and architectural elements detected",
        "Apartment and core relationships mapped"
      ],

      "processing_metadata": {{
        "source_res": [7017, 9934],
        "scale": 1000.0,
        "sector_analysis": "4x4_grid_complete"
      }},

      "detections": [
        {{
          "label": "Object Name",
          "box_2d": [ymin, xmin, ymax, xmax],
          "center": [y_center, x_center],
          "room": "Room/Space Name",
          "confidence": 0.0
        }}
      ]
    }}

    Note:
    - If an object is NOT present, set qty = 0 (do not guess)
    - DO NOT include legend detections
    - Ensure every object has bounding box + center
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

        response = model.generate_content(
            [prompt, img1],
            generation_config={
                "temperature": 0.0,
                "top_p": 1.0,
                "top_k": 1,
                "max_output_tokens":65536
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

def gemini_electrical_analysis(image_path, merged_json=None):
    img1 = PIL.Image.open(image_path)
    # img2 = PIL.Image.open(annotated_path)

    # Enhance both images before sending to Gemini
    img1 = enhance_for_gemini(img1)
    # img2 = enhance_for_gemini(img2)
    annotated_json = merged_json
    # Your full technical list from the legend
    device_list = """DETECTION RULES FOR ELECTRICAL LIFE SAFETY / LV DISTRIBUTION SCHEMATICS (UK):

    This drawing is an Electrical Single Line / Distribution schematic.

    Focus on PANELS, SWITCHBOARDS, MCCBs, ATS, CONTROL PANELS, CABLE REFERENCES, LOAD EQUIPMENT.

    -----------------------------------
    1. LV SWITCHBOARDS / PANELS (PRIMARY OBJECTS)
    -----------------------------------

    Detect rectangular panels labeled:
    - LV SWITCHBOARD
    - LIFE SAFETY PANEL (LSP)
    - DB-LS-RF-01 / DB-LS-RF-02
    - RF-LS-RF-01 / RF-LS-RF-02
    - B1-LSP / B2-LSP
    - Landlords Life Safety Panel
    - Roof Life Safety Panel
    - Basement Life Safety Switchroom

    -----------------------------------
    2. PROTECTION DEVICES
    -----------------------------------

    Detect all MCCB symbols with ratings:
    - 63A TPN MCCB
    - 125A TPN MCCB
    - 160A TPN MCCB
    - 200A / 250A / 400A / 630A MCCB
    - 4 Pole MCCB (Motorised / N/O)

    Each MCCB is an individual object.

    -----------------------------------
    3. ATS / CHANGEOVER SYSTEMS
    -----------------------------------

    Detect:
    - ATS (Automatic Transfer Switch)
    - MTSQ1
    - LBS Q2
    - SOCOMEC ATyS T ATS
    - Primary Supply / Secondary Supply / Bypass

    -----------------------------------
    4. SURGE & MONITORING DEVICES
    -----------------------------------

    Detect:
    - Surge Arrester
    - ESP 415 Type 1
    - Phase Failure Relay
    - PFR

    -----------------------------------
    5. CONTROL PANELS (CRITICAL LOADS)
    -----------------------------------

    Detect panels labeled:
    - Wet Riser Duty Pump Control Panel
    - Wet Riser Standby Pump Control Panel
    - Sprinkler Duty Pump Control Panel
    - Sprinkler Standby Pump Control Panel
    - BCW Pump Control Panel
    - Smoke Extract Fan
    - Passenger Lift
    - Sump Pump
    - Oil Transfer Pump
    - Generator Fuel Pump

    -----------------------------------
    6. LOAD EQUIPMENT
    -----------------------------------

    Detect connected loads:
    - Smoke Extract 1/2/3
    - Passenger Lift 1–7
    - Energy Centre
    - Landlord Lighting & Small Power
    - Bin Store Smoke Extract
    - Roof Smoke Extract

    -----------------------------------
    7. CABLE REFERENCES (IMPORTANT)
    -----------------------------------

    Detect cable callouts:
    Examples:
    - 1x1x4c 70mm F120+50mm CPC
    - 5c 16mm F120
    - 4c 95mm F120+50mm CPC

    Each cable reference is an object tied between panels.

    -----------------------------------
    FINAL RULE:

    This is a POWER FLOW diagram.

    Every panel, MCCB, ATS, control panel, load, and cable reference MUST be detected.
    """

    prompt = f"""
    ### ROLE: 
    You are a Senior Electrical Engineer and Lead CAD Auditor specializing in Life Safety LV Distribution, ATS systems, MCCB protection, and essential services power schematics in accordance with BS 7671 and BS 8519.

    Your task is to perform a granular, spatial, device-level audit of a high-resolution Electrical Life Safety distribution schematic.

    Detect all panels, switchboards, MCCBs, ATS, control panels, loads, and cable references within the diagram and provide accurate labels and bounding boxes as per instructions below.

    Primary Standards: BS 7671, BS 8519

    ### Object Detection results of this image give exact objects (if not detecting well detect by yourself):
    {annotated_json}

    ### INPUT DATA:
    - First Image: Electrical schematic drawing (very high resolution).
    - Second Image: Annotated detections (if provided).
    - Target Coordinate System: Normalized [0, 1000].
    - Coordinates MUST represent [ymin, xmin, ymax, xmax].
    - Remove legends from results.
    - If annotated, detect remaining objects.

    ### AUDIT PROTOCOL:

    1. Source Calibration (Legend/Object/Text Scan):
       Identify panel naming style (B1-LSP, B2-LSP, RF-LS, DB-LS, etc.), MCCB ratings, ATS symbols, and cable callout formats.

    2. Global Scanning Strategy:
       Execute a 4x4 sector scan (A1 to D4).

    3. De-Clumping Rule:
       In clustered protection devices (MCCBs, ATS, relays), generate UNIQUE bounding boxes for EACH object.

    4. Contextual Validation:
       Follow the power flow path from main switchboards to loads and associate objects logically.

    ### TARGET OBJECTS & LEGENDS:
    {device_list} or any which is in the plan but not in list

    ### RULES:
    1. Detect EVERY panel / switchboard.
    2. Detect EVERY MCCB with rating.
    3. Detect EVERY ATS / changeover system.
    4. Detect EVERY control panel (pumps, fans, lifts, etc.).
    5. Detect EVERY connected load.
    6. Detect EVERY cable reference text.
    7. Provide center coordinate [y, x] for EVERY object.

    ### SCANNING STRATEGY:
    - Use provided detections and find missing objects.
    - 4x4 sector scan — no grouping allowed.
    - Detect rotated symbols and text.
    - Validate objects are real electrical symbols.
    - Recheck detections multiple times.
    - DO NOT miss any object.

    ### COORDINATE SYSTEM (MANDATORY):

    ### NORMALIZED BOUNDING BOX:
    - Use [0, 1000] coordinate system.
    - Format: [ymin, xmin, ymax, xmax]

    Constraints:
    - 0 ≤ ymin < ymax ≤ 1000
    - 0 ≤ xmin < xmax ≤ 1000

    Bounding boxes MUST fully enclose:
    - panel rectangles
    - MCCB symbols
    - ATS symbols
    - control panels
    - cable reference text

    ### CENTER COORDINATE:
    - y_center = (ymin + ymax) / 2
    - x_center = (xmin + xmax) / 2

    ### CONSISTENCY RULE:
    - Center MUST lie inside bounding box
    - Boxes MUST align to actual object
    - Validate every coordinate

    ### OUTPUT FORMAT:

    Return ONLY valid JSON with this structure:

    {{
      "zones": [
        {{
          "zoneId": "Z-01",
          "zoneName": "Life Safety Panel Group",
          "devices": [
            {{ "id": "D-001", "type": "LV Switchboard", "qty": 1 }},
            {{ "id": "D-002", "type": "MCCB", "qty": 12 }},
            {{ "id": "D-003", "type": "ATS", "qty": 2 }},
            {{ "id": "D-004", "type": "Control Panel", "qty": 6 }},
            {{ "id": "D-005", "type": "Load Equipment", "qty": 10 }},
            {{ "id": "D-006", "type": "Cable Reference", "qty": 20 }}
          ],
          "matrix": [
            {{
              "cause": "Power supplied from Life Safety Panel",
              "effect": [
                "Feeds MCCB protection devices",
                "Passes through ATS changeover",
                "Supplies control panels for pumps/fans/lifts",
                "Connected via fire rated cables",
                "Distributes power to life safety loads"
              ]
            }}
          ]
        }}
      ],

      "building_summary": {{
        "building_type": "Residential / Commercial / Mixed-use / Unknown",
        "total_levels": 0,
        "levels": [
          "Basement",
          "Ground",
          "Roof"
        ]
      }},

      "project_info": {{
        "project_name": "",
        "drawing_title": ""
      }},

      "confidence": 0.0,

      "legend": [
        {{ "abbr": "MCCB", "meaning": "Moulded Case Circuit Breaker" }},
        {{ "abbr": "ATS", "meaning": "Automatic Transfer Switch" }},
        {{ "abbr": "LSP", "meaning": "Life Safety Panel" }}
      ],

      "notes": [
        "Legend excluded from counts",
        "Electrical power topology inferred from schematic",
        "All panels, protection, and load elements detected"
      ],

      "processing_metadata": {{
        "source_res": [7017, 9934],
        "scale": 1000.0,
        "sector_analysis": "4x4_grid_complete"
      }},

      "detections": [
        {{
          "label": "Electrical Object",
          "box_2d": [ymin, xmin, ymax, xmax],
          "center": [y_center, x_center],
          "room": "Panel / Load Reference",
          "confidence": 0.0
        }}
      ]
    }}

    Note:
    - If an object is NOT present, set qty = 0 (do not guess)
    - DO NOT include legend detections
    - Ensure every object has bounding box + center
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

def gemini_fire_spec_analysis(image_path, merged_json=None):
    img1 = PIL.Image.open(image_path)
    # img2 = PIL.Image.open(annotated_path)

    # Enhance both images before sending to Gemini
    img1 = enhance_for_gemini(img1)
    # img2 = enhance_for_gemini(img2)
    annotated_json = merged_json
    # Your full technical list from the legend
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
    """

    prompt = f"""
    ### ROLE: 
    You are a Senior Mechanical (HVAC) Engineer and Lead CAD Auditor specializing in Smoke Ventilation Systems, AOV systems, and ductwork layouts in accordance with BS 9999 and BS EN 12101.

    Your task is to perform a granular, spatial, device-level audit of a high-resolution Smoke Ventilation / HVAC floor plan drawing.

    Detect all legends, objects, infrastructure within the diagram and provide accurate labels and bounding boxes as per instructions below. You can also use your own domain knowledge.

    Primary Standard: BS 9999, BS EN 12101  
    Ductwork Standard: DW144  

    ### Object Detection results of this image give exact objects (if not detecting well detect by yourself):
    {annotated_json}

    ### INPUT DATA:
    - First Image: CAD Floor Plan (9934x7017 resolution or above).
    - Second Image: CAD Floor Plan (9934x7017 resolution or above) with object detection labels and boundaries.
    - It is possibly 100% accurate detections; if all objects you see are accurate, consider them in your analysis and detect remaining too.
    - Target Coordinate System: Normalized [0, 1000] scale.
    - Coordinates MUST represent [ymin, xmin, ymax, xmax] of the individual block.
    - Remove Legends from results.
    - If it's a new image, analyze from start. If annotated, detect remaining objects.

    ### AUDIT PROTOCOL:
    1. Source Calibration (Legend/Object/symbol Scan):
       Locate the legend and lock visual signatures (duct types, dampers, AOV symbols, sensors, fans).

    2. Global Scanning Strategy:
       Execute a 4x4 sector scan (A1 to D4).

    3. De-Clumping Rule:
       In clustered elements (dampers, sensors, grilles), generate UNIQUE bounding boxes for EACH symbol.

    4. Contextual Validation:
       Extract "Room Name" from nearest MTEXT/DTEXT and associate each object.

    ### TARGET OBJECTS & LEGENDS:
    {device_list} or any which is in the plan but not in list

    ### RULES:
    1. ARCHITECTURAL: Count 'Lifts' and 'Doors'.
    2. COORDINATES: For EVERY object, provide center coordinate [y, x].
    3. All Objects: Symbols can be on walls, ducts, ceilings, shafts—do not miss any.
    4. Detect objects even when overlapping or near each other.
    5. Objects exist on both white background and structured CAD layers.

    ### SCANNING STRATEGY:
    - Use provided detections and find missing objects.
    - 4x4 sector scan—no grouping allowed.
    - Detect rotated symbols.
    - Validate objects are real symbols (not empty boxes).
    - Detect ALL objects (colored, circular, rectangular, duct-based).
    - Detect room names.
    - Recheck detections multiple times.
    - DO NOT miss any object.

    ### COORDINATE SYSTEM (MANDATORY):

    ### NORMALIZED BOUNDING BOX:
    - Use [0, 1000] coordinate system.
    - Format: [ymin, xmin, ymax, xmax]

    Constraints:
    - 0 ≤ ymin < ymax ≤ 1000
    - 0 ≤ xmin < xmax ≤ 1000

    Bounding boxes MUST fully enclose:
    - entire symbols
    - dampers
    - grilles
    - fans
    - sensors
    - AOV components

    ### CENTER COORDINATE:
    - y_center = (ymin + ymax) / 2
    - x_center = (xmin + xmax) / 2

    ### CONSISTENCY RULE:
    - Center MUST lie inside bounding box
    - Boxes MUST align to actual object (not blank space)
    - Validate every coordinate

    ### OUTPUT FORMAT:

    Return ONLY valid JSON with this structure:

    {{
      "zones": [
        {{
          "zoneId": "Z-01",
          "zoneName": "Level 01",
          "devices": [
            {{ "id": "D-001", "type": "Smoke Damper", "qty": 14 }},
            {{ "id": "D-002", "type": "Extract Grille", "qty": 6 }},
            include all detected devices (AOV, dampers, fans, sensors, grilles, ducts etc.)
          ],
          "matrix": [
            {{
              "cause": "Smoke detected in Level 01 ventilation zone",
              "effect": [
                "Activate smoke extract system",
                "Open AOV dampers",
                "Start extract fans",
                "Isolate affected duct zones",
                include all cause & effect based on system behavior
              ]
            }}
          ]
        }}
      ],

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

      "confidence": 0.0,

      "legend": [
        {{ "abbr": "AOV", "meaning": "Automatic Opening Vent" }},
        include all detected HVAC / ventilation objects
      ],

      "notes": [
        "Legend excluded from counts",
        "Smoke ventilation logic inferred from system layout",
        "All duct and AOV related elements detected"
      ],

      "processing_metadata": {{
        "source_res": [7017, 9934],
        "scale": 1000.0,
        "sector_analysis": "4x4_grid_complete"
      }},

      "detections": [
        {{
          "label": "Device Name",
          "box_2d": [ymin, xmin, ymax, xmax],
          "center": [y_center, x_center],
          "room": "Room Name",
          "confidence": 0.0
        }}
      ]
    }}

    Note:
    - If a device is NOT present, set qty = 0 (do not guess)
    - DO NOT include legend detections
    - Ensure every object has bounding box + center
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
def gemini_sprinkler_analysis(image_path, merged_json=None):
    img1 = PIL.Image.open(image_path)
    # img2 = PIL.Image.open(annotated_path)

    # Enhance both images before sending to Gemini
    img1 = enhance_for_gemini(img1)
    # img2 = enhance_for_gemini(img2)
    annotated_json = merged_json
    # Your full technical list from the legend
    device_list = """DETECTION RULES FOR FIRE SPRINKLER SYSTEM DRAWINGS (BS EN 12845 / NFPA 13):

    This drawing represents a Fire Sprinkler / Wet Riser / Dry Riser / Fire Protection piping layout.

    Focus on SPRINKLER HEADS, VALVES, RISERS, PIPEWORK, PUMPS, FLOW DEVICES, and CONTROL EQUIPMENT.

    -----------------------------------
    1. SPRINKLER HEADS (PRIMARY OBJECTS)
    -----------------------------------

    Detect all sprinkler heads:
    - Pendant Sprinkler
    - Upright Sprinkler
    - Sidewall Sprinkler
    - Concealed Sprinkler

    Usually represented as small circles, crosses, or star-like symbols connected to pipework.

    Each sprinkler head MUST be counted individually.

    -----------------------------------
    2. PIPEWORK SYSTEM
    -----------------------------------

    Detect:
    - Main pipe
    - Branch pipe
    - Loop connections
    - Vertical risers

    Pipework shown as continuous lines connecting sprinkler heads.

    -----------------------------------
    3. RISERS / SYSTEM TYPES
    -----------------------------------

    Detect:
    - Wet Riser
    - Dry Riser
    - Pre-action system
    - Sprinkler riser

    Usually labeled near vertical shafts or service cores.

    -----------------------------------
    4. VALVES (CRITICAL)
    -----------------------------------

    Detect all valve types:
    - Alarm Valve
    - Gate Valve
    - Butterfly Valve
    - Check Valve / Non-return valve
    - Zone Control Valve (ZCV)
    - Pressure Reducing Valve (PRV)
    - Test & Drain Valve

    Each valve is a separate object.

    -----------------------------------
    5. FLOW & ALARM DEVICES
    -----------------------------------

    Detect:
    - Flow Switch
    - Pressure Switch
    - Water Motor Gong
    - Alarm Bell

    Usually placed near risers or valve sets.

    -----------------------------------
    6. FIRE PUMPS & TANKS
    -----------------------------------

    Detect:
    - Fire Pump
    - Jockey Pump
    - Diesel Pump
    - Water Storage Tank

    Located in plant rooms or basement areas.

    -----------------------------------
    7. HYDRANT & HOSE SYSTEMS
    -----------------------------------

    Detect:
    - Landing Valve
    - Hose Reel
    - Fire Hydrant

    Usually wall-mounted or in shafts.

    -----------------------------------
    8. SPECIAL COMPONENTS
    -----------------------------------

    Detect:
    - Air Compressor (for dry systems)
    - Test Point
    - Drain Point
    - End of Line Test Valve
    - Inspector’s Test Valve

    -----------------------------------
    FINAL RULE:

    This is a WATER-BASED FIRE PROTECTION SYSTEM.

    Every sprinkler head, valve, riser, pipe, pump, and flow device MUST be detected individually.
    """

    prompt = f"""
    ### ROLE: 
    You are a Senior Fire Protection Engineer and Lead CAD Auditor specializing in Fire Sprinkler Systems, Wet/Dry Risers, and automatic suppression systems in accordance with BS EN 12845 and NFPA 13.

    Your task is to perform a granular, spatial, device-level audit of a high-resolution Fire Sprinkler system drawing.

    Detect all sprinkler heads, pipework, valves, risers, pumps, and fire protection components within the diagram and provide accurate labels and bounding boxes as per instructions below.

    Primary Standards: BS EN 12845, NFPA 13

    ### Object Detection results of this image give exact objects (if not detecting well detect by yourself):
    {annotated_json}

    ### INPUT DATA:
    - First Image: CAD Floor Plan (9934x7017 resolution or above).
    - Second Image: CAD Floor Plan with object detection labels and boundaries.
    - It is possibly 100% accurate detections; if correct, use them and detect remaining objects.
    - Target Coordinate System: Normalized [0, 1000].
    - Coordinates MUST represent [ymin, xmin, ymax, xmax].
    - Remove Legends from results.
    - If new image, analyze from start. If annotated, detect remaining.

    ### AUDIT PROTOCOL:

    1. Source Calibration (Legend/Object/symbol Scan):
       Identify sprinkler symbols, pipe types, valve symbols, riser labels, and pump representations.

    2. Global Scanning Strategy:
       Execute a 4x4 sector scan (A1 to D4).

    3. De-Clumping Rule:
       In clustered sprinkler heads or valves, generate UNIQUE bounding boxes for EACH symbol.

    4. Contextual Validation:
       Extract "Room Name" and associate each sprinkler and component with nearest space.

    ### TARGET OBJECTS & LEGENDS:
    {device_list} or any which is in the plan but not in list

    ### RULES:
    1. Detect EVERY sprinkler head individually.
    2. Detect EVERY valve and classify its type.
    3. Detect risers and system type (wet/dry/pre-action).
    4. Detect pumps and tanks.
    5. Detect flow switches and alarm devices.
    6. Detect pipework routes and connections.
    7. Provide center coordinate [y, x] for EVERY object.

    ### SCANNING STRATEGY:
    - Use provided detections and find missing objects.
    - 4x4 sector scan — no grouping allowed.
    - Detect rotated symbols.
    - Validate objects are real symbols (not blank graphics).
    - Detect ALL sprinkler heads, valves, pumps, and piping.
    - Detect room names.
    - Recheck detections multiple times.
    - DO NOT miss any object.

    ### COORDINATE SYSTEM (MANDATORY):

    ### NORMALIZED BOUNDING BOX:
    - Use [0, 1000] coordinate system.
    - Format: [ymin, xmin, ymax, xmax]

    Constraints:
    - 0 ≤ ymin < ymax ≤ 1000
    - 0 ≤ xmin < xmax ≤ 1000

    Bounding boxes MUST fully enclose:
    - sprinkler heads
    - valve symbols
    - pumps
    - flow switches
    - pipe junctions (if treated as objects)

    ### CENTER COORDINATE:
    - y_center = (ymin + ymax) / 2
    - x_center = (xmin + xmax) / 2

    ### CONSISTENCY RULE:
    - Center MUST lie inside bounding box
    - Boxes MUST align to actual object
    - Validate every coordinate

    ### OUTPUT FORMAT:

    Return ONLY valid JSON with this structure:

    {{
      "zones": [
        {{
          "zoneId": "Z-01",
          "zoneName": "Level 01",
          "devices": [
            {{ "id": "D-001", "type": "Sprinkler Head", "qty": 120 }},
            {{ "id": "D-002", "type": "Valve", "qty": 18 }},
            {{ "id": "D-003", "type": "Riser", "qty": 2 }},
            {{ "id": "D-004", "type": "Fire Pump", "qty": 1 }},
            {{ "id": "D-005", "type": "Flow Switch", "qty": 6 }}
          ],
          "matrix": [
            {{
              "cause": "Sprinkler activation due to heat/fire",
              "effect": [
                "Water discharged from activated sprinkler head",
                "Flow switch triggers alarm signal",
                "Fire pump starts automatically",
                "Zone control valve allows water flow",
                "System pressure maintained by jockey pump"
              ]
            }}
          ]
        }}
      ],

      "building_summary": {{
        "building_type": "Residential / Commercial / Mixed-use / Unknown",
        "total_levels": 0,
        "levels": [
          "Basement",
          "Ground",
          "Level 01",
          "Roof"
        ]
      }},

      "project_info": {{
        "project_name": "",
        "drawing_title": ""
      }},

      "confidence": 0.0,

      "legend": [
        {{ "abbr": "ZCV", "meaning": "Zone Control Valve" }},
        {{ "abbr": "PRV", "meaning": "Pressure Reducing Valve" }},
        {{ "abbr": "NRV", "meaning": "Non-return Valve" }}
      ],

      "notes": [
        "Legend excluded from counts",
        "Sprinkler system layout interpreted as per standard practice",
        "All sprinkler heads and control devices detected"
      ],

      "processing_metadata": {{
        "source_res": [7017, 9934],
        "scale": 1000.0,
        "sector_analysis": "4x4_grid_complete"
      }},

      "detections": [
        {{
          "label": "Sprinkler / Valve / Pump",
          "box_2d": [ymin, xmin, ymax, xmax],
          "center": [y_center, x_center],
          "room": "Room Name",
          "confidence": 0.0
        }}
      ]
    }}

    Note:
    - If an object is NOT present, set qty = 0 (do not guess)
    - DO NOT include legend detections
    - Ensure every object has bounding box + center
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


def _coerce_analysis_root(json_data):
    """
    Gemini sometimes returns a top-level list (e.g. only detections) or a list
    wrapping one object. Normalize to a dict so downstream code never does
    list[\"detections\"] (TypeError: list indices must be integers or slices, not str).
    """
    if json_data is None:
        return {"detections": [], "zones": []}
    if isinstance(json_data, dict):
        return json_data
    if isinstance(json_data, list):
        if not json_data:
            return {"detections": [], "zones": []}
        # List of detection-like dicts (each has box_2d / label, not a full schema)
        if all(isinstance(x, dict) for x in json_data):
            looks_like_detection = ("box_2d" in json_data[0]) or (
                "label" in json_data[0]
                and "detections" not in json_data[0]
                and "zones" not in json_data[0]
            )
            if looks_like_detection:
                return {"detections": json_data, "zones": []}
            for item in json_data:
                if isinstance(item, dict) and (
                    "detections" in item
                    or "zones" in item
                    or "summary_totals" in item
                    or "processing_metadata" in item
                ):
                    return item
        first = json_data[0]
        if isinstance(first, dict):
            return first
        return {"detections": [], "zones": []}
    return {"detections": [], "zones": []}




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

    json_data = _coerce_analysis_root(json_data)
    if not isinstance(json_data, dict):
        json_data = {"detections": [], "zones": []}

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

    raw_detections = json_data.get("detections", [])
    if not isinstance(raw_detections, list):
        raw_detections = []
    detections = raw_detections

    valid_smoke_count = 0
    filtered_detections = []

    #  DRAW DETECTIONS 
    for detection in detections:
        if not isinstance(detection, dict):
            continue

        label = detection.get("label", "Unknown")
        box = detection.get("box_2d")

        if isinstance(box, dict):
            ymin = box.get("ymin", box.get("y_min"))
            xmin = box.get("xmin", box.get("x_min"))
            ymax = box.get("ymax", box.get("y_max"))
            xmax = box.get("xmax", box.get("x_max"))
            if None in (ymin, xmin, ymax, xmax):
                continue
        elif isinstance(box, (list, tuple)) and len(box) == 4:
            ymin, xmin, ymax, xmax = box
        else:
            continue

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
        if not isinstance(zone, dict):
            continue
        devices = zone.get("devices", [])
        if not isinstance(devices, list):
            continue
        for device in devices:
            if not isinstance(device, dict):
                continue
            if "Smoke" in device.get("type", ""):
                device["qty"] = valid_smoke_count

    # Replace detections with filtered ones
    json_data["detections"] = filtered_detections

    img.save(output_path)

    return img, json_data


def gemini_cad_level_analysis_step_1(image_path,ocr=None,drawing_json=None):
    img = PIL.Image.open(image_path)

    # Your full technical list from the legend

    prompt = f"""
    ### ROLE:
    You are a Senior Fire Protection Engineer, Building Intelligence Analyst, and Lead CAD Auditor.

    You specialize in:
    - BS 5839-1 Fire Alarm Design
    - NFPA 72 & NFPA 170 standards
    - General Arrangement (GA) Drawing Interpretation
    - Spatial and architectural intelligence extraction from CAD drawings

    You are given:
    1. A GA drawing image (visual input)
    2. Structured OCR JSON with bounding boxes

    Your task is to extract structured building intelligence.
    This is the FOUNDATION layer for fire strategy automation.

    

    ### INPUT:

    OCR_OBJECTS:
    {ocr}

    

    ### CORE OBJECTIVE:

    Extract COMPLETE GA Drawing Intelligence including:

    - Building name
    - Drawing title
    - Drawing reference
    - Building type
    - Levels and FFL
    - Basement configuration
    - Core details (with contents)
    - Zones (exact names + standardized types)
    - Devices per zone
    - Spatial relationships

    

    ## SPATIAL UNDERSTANDING (CRITICAL)

    Use bounding boxes to:
    - Group text into zones
    - Detect title block (bottom-right)
    - Identify levels
    - Identify cores
    - Determine adjacency

    

    ## BUILDING IDENTIFICATION

    Extract:
    - building_name
    - drawing_title
    - drawing_reference
    - building_type

    

    ## LEVELS

    - Extract exact level names
    - Maintain order (lowest → highest)
    - Count total_levels

    

    ## FFL

    - Extract and map FFL per level

    

    ## BASEMENT

    - Identify basement levels
    - Extract usage

    

    ## CORE DETECTION (UPDATED)

    For each core:

    Extract:
    - core_id
    - type (stair / lift / refuge / mixed)
    - contents (MANDATORY list)

    ### Core contents may include:
    - "staircase"
    - "passenger lift"
    - "firefighter lift"
    - "refuge area"

    

    ## ZONE DETECTION (CRITICAL)

    For EACH level:

    ### 1. ZONE NAME (RAW – EXACT)
    - MUST match drawing text exactly

    ### 2. ZONE TYPE (STANDARDIZED – NEW REQUIREMENT)

    Assign zone_type using ONLY the following categories:

    - Plant Room
    - Electrical Room
    - Energy Centre
    - Storage
    - Lobby
    - Assembly
    - Circulation
    - Office
    - Staircase
    - Lift Shaft
    - Refuse Room
    
    ### Classification Rules:
    
    - "BCWS TANK", "AHU", "AIR HANDLING", "FAN ROOM", "PUMP ROOM", "WATER TANK", "TANK", "PLANT", "PLANT ROOM", "MECHANICAL", "HVAC", "CHILLER", "BOILER", "GENERATOR", "UPS", "SPRINKLER PLANT", "FIRE PUMP", "RISER TANK", "PRESSURISATION" → Plant Room  
    
    - "LV SWITCHROOM", "SWITCHROOM", "SWITCH ROOM", "ELECTRICAL", "SUBSTATION", "TRANSFORMER", "COMMS", "COMMUNICATION", "DATA ROOM", "SERVER ROOM", "IT ROOM", "TELECOM", "RISER", "ELECTRICAL RISER", "ELV", "BMS ROOM" → Electrical Room  
    
    - "ENERGY CENTRE", "ENERGY CENTER" → Energy Centre  
    
    - "STORE", "STORAGE", "STOREROOM", "STORE ROOM", "WORKSHOP", "CUPBOARD", "CABINET", "LOCKER", "JANITOR", "CLEANER", "CLEANER'S ROOM", "SUPPLIES", "PET ROOM", "BIKE STORE", "CYCLE STORE" → Storage  
    
    - "LOBBY", "ENTRANCE", "RECEPTION", "FOYER", "WAITING", "WAITING AREA", "ARRIVAL", "VESTIBULE", "CONCIERGE", "CINEMA LOBBY" → Lobby  
    
    - "SCREEN", "CINEMA", "THEATRE", "AUDITORIUM", "GYM", "FITNESS", "STUDIO", "CLASS", "LOUNGE", "CLUB", "BAR", "RESTAURANT", "DINING", "CAFE", "FOOD COURT", "RETAIL", "SHOP", "EXHIBITION" → Assembly  
    
    - "CORRIDOR", "CIRCULATION", "HALL", "HALLWAY", "PASSAGE", "WALKWAY", "ACCESS", "ROUTE", "LINK", "BRIDGE" → Circulation  
    
    - "OFFICE", "SECURITY OFFICE", "SECURITY", "CONTROL ROOM", "MANAGEMENT", "ADMIN", "STAFF ROOM", "MEETING", "BOARDROOM" → Office  
    
    - "STAIR", "STAIRCASE", "ESCAPE STAIR", "FIRE STAIR", "CORE STAIR" → Staircase  
    
    - "LIFT", "ELEVATOR", "SHAFT", "LIFT SHAFT", "PASSENGER LIFT", "SERVICE LIFT", "FIREFIGHTER LIFT" → Lift Shaft  
    
    - "WASTE STORE", "WASTE", "REFUSE", "BIN ROOM", "BIN STORE", "REFUSE ROOM", "RECYCLING", "GARBAGE", "COMPACTOR" → Refuse Room  
    
    - "APARTMENT", "FLAT", "UNIT", "PLOT", "BEDROOM", "LIVING", "KITCHEN" → Residential Unit  
    
    ---
    
    ### Priority Rules (Apply in order):
    
    - "ENERGY CENTRE" overrides Plant Room  
    - "WASTE / REFUSE" overrides Storage  
    - "ELECTRICAL" overrides Plant Room  
    - "STAIR" overrides Circulation  
    = "PET ROOM" overrides Storage 
    - "LIFT / SHAFT" overrides Lobby  
    
    ---
    
    ### Fallback Rule:
    
    If still unclear:
    - Use best-fit category based on functional fire behavior  
    - Avoid "Unknown" unless absolutely necessary  


    

    ### 3. SPECIAL RULE – CYCLE STORES

    If multiple cycle stores exist:

    - Rename as:
      - "Cycle Store A"
      - "Cycle Store B"

    - Add:
      - capacity (number of spaces)

    Example:

    {{
      "zone_name": "Cycle Store A",
      "capacity": 120
    }}

    

    ### 4. ZONE OUTPUT

    For each zone extract:

    - zone_id
    - zone_name
    - zone_type (standardized)
    - capacity (ONLY for cycle stores, else null)
    - devices
    - adjacent_to (zone_name only)
    - confidence

    

    ## ADJACENCY RULE

    - MUST use zone_name (NOT zone_id)
    - Must be human-readable

    

    ## DEVICES

    - Extract per zone:
      - type
      - label

    

    ## SPATIAL RELATIONSHIPS

    Use zone_name:

    - from
    - to
    - type = "adjacent"

    

    ## UNITS

    If residential:
    - Extract unit count and types

    

    ## CONFIDENCE

    Provide:

    - overall confidence
    - breakdown:
      - building_identification
      - level_detection
      - ffl_extraction
      - zone_detection
      - adjacency_mapping
      - core_detection

    Also:
    - zone-level confidence
    - low confidence areas (<0.85)

    

    ## OUTPUT FORMAT (STRICT JSON ONLY)

    {{
      "building_summary": {{
        "building_name": "",
        "drawing_title": "",
        "drawing_reference": "",
        "building_type": "",
        "total_levels": 0,
        "levels": [
          {{
            "level_name": "",
            "ffl": "",
            "zones": [
              {{
                "zone_id": "",
                "zone_name": "",
                "zone_type": "",
                "capacity": null,
                "devices": [
                  {{
                    "type": "",
                    "label": ""
                  }}
                ],
                "adjacent_to": [],
                "confidence": 0.0
              }}
            ]
          }}
        ]
      }},
      "basement_levels": [
        {{
          "level_name": "",
          "usage": []
        }}
      ],
      "cores": [
        {{
          "core_id": "",
          "type": "",
          "contents": []
        }}
      ],
      "units": {{
        "per_floor": 0,
        "unit_types": []
      }},
      "spatial_relationships": [
        {{   # zone ids with Full names
          "from": "",
          "to": "",
          "type": "adjacent"
        }}
      ],
      "confidence": 0.0,
      "confidence_breakdown": {{
        "building_identification": 0.0,
        "level_detection": 0.0,
        "ffl_extraction": 0.0,
        "zone_detection": 0.0,
        "adjacency_mapping": 0.0,
        "core_detection": 0.0
      }},
      "low_confidence_areas": [
        {{
          "zone_name": "",
          "issue": "",
          "confidence": 0.0
        }}
      ]
    }}

    

    ## RULES

    - OUTPUT ONLY JSON
    - DO NOT hallucinate
    - zone_name = exact drawing text (except cycle store renaming rule)
    - zone_type = standardized category
    - adjacency uses zone_name only
    - include core contents
    - include cycle store capacity
    - must support fire strategy automation

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
            img
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


def gemini_cad_level_analysis_Step_2(image_path,ga_json=None,form_inputs=None):
    img = PIL.Image.open(image_path)

    # Your full technical list from the legend

    prompt = f"""
    ### ROLE:
    You are a Senior Fire Engineer responsible for generating a structured Fire Strategy Framework.

    This is NOT a narrative report.
    This is a structured, traceable engineering document used by professionals.

    

    ### INPUT 1: GA BUILDING JSON
    {ga_json}

    

    ### INPUT 2: ENGINEER FORM INPUTS
    {form_inputs}

    

    ## 🚨 ENGINEER INPUT VALIDATION (MANDATORY)

    You MUST explicitly use ALL of the following fields:

    - building_type (override GA if provided)
    - height
    - storeys
    - new_or_refurbishment
    - basement_presence_and_use
    - ancillary_uses
    - regulatory_route (ADB / BS9991)
    - evacuation_strategy (Simultaneous / Phased / Stay Put / Progressive Horizontal)
    - compartmentation_approach
    - firefighting_provisions (sprinklers, risers, lifts)
    - occupancy_assumptions

    If any field is missing → mark as "Unknown"

    

    ## 🔥 CORE OBJECTIVE

    Generate a COMPLETE structured Fire Strategy Framework:

    - Fully traceable
    - Per level + per zone
    - Ready for PDF generation
    - Editable by engineer

    

    ## 🚨 TRACEABILITY RULE (STRICT)

    Every entry MUST include:

    "source": {{
      "type": "GA / Form / Inferred",
      "reference": "exact zone name / input field"
    }}

    

    ## 🔥 OUTPUT STRUCTURE (STRICT JSON)

    {{
      "project_information": {{
        "building_name": {{"value": "", "source": {{"type": "GA", "reference": ""}}, "editable": true}},
        "building_type": {{"value": "", "source": {{"type": "GA/Form", "reference": ""}}, "editable": true}},
        "storeys": {{"value": "", "source": {{"type": "GA/Form", "reference": ""}}, "editable": true}},
        "height": {{"value": "", "source": {{"type": "Form", "reference": "height"}}, "editable": true}},
        "new_or_refurbishment": {{"value": "", "source": {{"type": "Form", "reference": "new_or_refurbishment"}}, "editable": true}},
        "basement": {{"value": "", "source": {{"type": "GA", "reference": "basement_levels"}}, "editable": true}},
        "ancillary_uses": {{"value": "", "source": {{"type": "Form", "reference": "ancillary_uses"}}, "editable": true}},
        "drawing_references": {{"value": [], "source": {{"type": "GA", "reference": "drawing_reference"}}, "editable": false}}
      }},

      "scope_and_regulatory_basis": {{
        "regulatory_route": {{"value": "", "source": {{"type": "Form", "reference": "regulatory_route"}}, "editable": true}},
        "standards_applied": [
          {{
            "standard": "",
            "reason": "",
            "source": {{"type": "Form/Inferred", "reference": ""}},
            "editable": true
          }}
        ]
      }},

      "means_of_escape": [
        {{
          "level": "",
          "zone": "",
          "evacuation_strategy": "",
          "escape_route": "",
          "source": {{"type": "GA/Form", "reference": ""}},
          "editable": true
        }}
      ],

      "compartmentation": [
        {{
          "level": "",
          "zone": "",
          "fire_resistance": "",
          "compartmentation_type": "",
          "source": {{"type": "Form/Inferred", "reference": ""}},
          "editable": true
        }}
      ],

      "fire_detection_alarm": {{
        "system_type": {{
          "value": "",
          "source": {{"type": "Inferred", "reference": "building_type"}},
          "editable": true
        }},
        "zone_schedule": [
          {{
            "level": "",
            "zone_name": "",
            "coverage": "",
            "detector_type": "",
            "source": {{"type": "GA/Inferred", "reference": ""}},
            "editable": true
          }}
        ]
      }},

      "smoke_control": {{
        "zones": [
          {{
            "level": "",
            "zone_name": "",
            "system": "",
            "trigger": "",
            "source": {{"type": "GA/Inferred", "reference": ""}},
            "editable": true
          }}
        ]
      }},

      "sprinkler_suppression": {{
        "coverage": [
          {{
            "level": "",
            "zone_name": "",
            "provided": true,
            "source": {{"type": "Form", "reference": "firefighting_provisions"}},
            "editable": true
          }}
        ]
      }},

      "firefighting_provisions": {{
        "risers": [
          {{
            "location": "",
            "type": "dry / wet",
            "source": {{"type": "GA/Form", "reference": "core"}},
            "editable": true
          }}
        ],
        "firefighting_lifts": [
          {{
            "core_id": "",
            "serves_levels": [],
            "source": {{"type": "GA/Form", "reference": "core"}},
            "editable": true
          }}
        ]
      }},

      "lift_recall_logic": [
        {{
          "lift_id": "",
          "recall_floor": "",
          "trigger": "",
          "override_condition": "",
          "source": {{"type": "GA/Inferred", "reference": ""}},
          "editable": true
        }}
      ],

      "engineer_review_notes": {{
        "value": "",
        "editable": true
      }}
    }}

    

    ## 🔥 ENGINEERING RULES (MANDATORY)

    ### Means of Escape:
    - Generate PER LEVEL and PER ZONE
    - Use evacuation strategy from form
    - Infer escape route via adjacent zones and cores

    ### Compartmentation:
    - Use compartmentation_approach from form
    - Assign fire resistance (60 / 90 / 120 min based on zone risk)

    ### Fire Detection:
    - Assembly → smoke detection
    - Plant/Electrical → heat detection
    - Circulation → smoke detection

    ### Smoke Control:
    - Lobby → AOV
    - Corridor → mechanical extract
    - Basement → extract + pressurisation

    ### Sprinklers:
    - Use form input directly
    - Apply per zone

    ### Firefighting:
    - Use cores to assign risers
    - Firefighting lifts must map to cores

    ### Lift Recall:
    - Passenger lifts → recall to ground
    - Firefighter lifts → override active
    - Trigger: fire alarm in zone

    

    ## 🚨 RULES (STRICT)

    - OUTPUT JSON ONLY
    - NO narrative text
    - MUST use ALL engineer inputs
    - MUST be per-zone (NOT grouped)
    - MUST include traceability with references

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
            img
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