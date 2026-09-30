PHASE 1.11 ARCHITECTURE PLAN

====================================================
1. FEATURE NAME
====================================================
Crop Water Stress Detection (ONNX, image-based)

Hindi screen name: "जल तनाव पहचान" (Water Stress Identification)
Intent code: WATER_STRESS

====================================================
2. WHY THIS IS THE CORRECT NEXT FEATURE
====================================================
The system now has five verified image-based ONNX classifiers forming a
complete "crop stress diagnosis" suite:

- Disease Detection (Phase 1.1) - pathogen stress
- Pest Detection (Phase 1.6) - insect damage stress
- Weed Detection (Phase 1.8) - competition stress
- Nutrient Deficiency Detection (Phase 1.9) - nutrition stress
- Growth Stage Detection (Phase 1.10) - developmental status

All five follow the exact same Provider → Service → Controller → API →
Intent → Tests pattern, with strict MODEL_NOT_CONFIGURED safety
contract, zero database changes, and 100% backward compatibility.

The only major "stress" category missing from the visual diagnosis suite
is **water stress (hydration status)**. A farmer who can identify
disease, pest, weed, nutrient deficiency, and growth stage still lacks
the critical answer to "does my crop need water right now?"

Water Stress Detection completes the stress diagnosis suite as the
sixth image classifier, providing real farmer value:
- Prevents water stress damage before visible wilting
- Optimizes irrigation timing and water usage
- Complements soil moisture data (when available) with visual evidence
- Actionable output: NO_STRESS / MILD_STRESS / MODERATE_STRESS / SEVERE_STRESS

This feature:
- Reuses the exact 5x-verified pattern (sixth image classifier)
- Adds NO database tables, NO migrations, NO authentication changes
- Provides maximum farmer value for minimal architectural risk
- Satisfies every architectural rule: Provider → Service → Controller
  → API, safe ONNX fallback, never-fabricate, independently testable
- Is NOT an invented feature: it completes the established
  stress-diagnosis family

====================================================
3. FARMER / USER VALUE
====================================================
A farmer photographs the crop canopy/leaves. The app honestly reports
the water stress level (NO_STRESS, MILD_STRESS, MODERATE_STRESS,
SEVERE_STRESS) OR returns MODEL_NOT_CONFIGURED when no validated model
is provisioned - never a fabricated stress level. This helps the farmer:
- Decide whether to irrigate immediately, schedule soon, or wait
- Prevent yield loss from undetected water stress
- Conserve water by avoiding unnecessary irrigation
- Ask the assistant "जल तनाव पहचानो" and be routed to the correct
  "जल तनाव पहचान" screen

====================================================
4. EXACT USER FLOW
====================================================
1. Farmer opens "जल तनाव पहचान" screen or asks assistant
2. Takes/uploads crop photo (canopy or leaves)
3. System validates image (magic bytes, 5 MB max, JPG/PNG)
4. Image stored securely under server-controlled path
5. OnnxWaterStressProvider runs inference (or returns unavailable)
6. Returns structured WaterStressOut:
   - success, status, crop, stress_level, confidence, model, message
7. If MODEL_NOT_CONFIGURED: honest "model not configured" message
8. If stress detected: level + confidence + model ID
9. Assistant intent "जल तनाव पहचानो" → honest Hindi pointer

====================================================
5. ARCHITECTURE
====================================================
Mirrors Phases 1.1, 1.6, 1.8, 1.9, 1.10 exactly:

Farmer photo
  -> FastAPI POST /api/water-stress/detect (JWT-protected)
  -> WaterStressController
  -> WaterStressService
  -> upload_service.save_image() (existing, secure)
  -> WaterStressProvider (replaceable)
       - OnnxWaterStressProvider (real model)
       - UnavailableWaterStressProvider (safe fallback)
  -> structured dict -> WaterStressOut

Assistant flow (intent routing):
  Farmer text -> intent_router.classify_intent()
    -> INTENT_WATER_STRESS
    -> AssistantController.handle()
    -> AssistantService.pointer() (Hindi pointer, no diagnosis)

====================================================
6. FILES TO CREATE
====================================================
1. config/core/providers/water_stress_provider.py
2. config/core/schemas/water_stress.py
3. config/core/services/water_stress_service.py
4. config/core/controllers/water_stress_controller.py
5. tests/test_water_stress_provider.py
6. tests/test_water_stress.py
7. tests/test_water_stress_intent.py

====================================================
7. FILES TO MODIFY (ADDITIVE ONLY)
====================================================
1. config/core/providers/base.py
   - add STATUS_WATER_STRESS_DETECTED, RESULT_STRESS_LEVEL
   - add WaterStressProvider (ABC) + UnavailableWaterStressProvider
2. config/core/providers/__init__.py
   - add get_water_stress_provider() factory
   - import + export UnavailableWaterStressProvider
3. config/core/schemas/__init__.py
   - export WaterStressOut
4. config/settings.py
   - add WATER_STRESS_MODEL_PATH, _LABELS, _INPUT_SIZE
5. .env.example
   - document the three new settings
6. config/core/services/intent_router.py
   - add INTENT_WATER_STRESS constant + _WATER_STRESS_WORDS + logic
   - update module docstring + _ALL_INTENTS
7. config/core/services/assistant_service.py
   - import INTENT_WATER_STRESS
   - add Hindi pointer in _POINTERS
8. config/core/controllers/assistant_controller.py
   - import INTENT_WATER_STRESS
   - add explicit branch in handle()
9. config/core/api/main.py
   - import WaterStressController, WaterStressError, WaterStressOut
   - add /api/water-stress/detect endpoint
   - add water_stress_error_handler (502 MODEL_INVALID)

====================================================
8. FILES THAT MUST REMAIN LOCKED
====================================================
- All Phase 1.1–1.10 providers/services/controllers/schemas
  (disease, pest, weed, nutrient_deficiency, growth_stage)
- config/core/providers/otp_provider.py, prediction_provider.py,
  recommendation_provider.py
- config/core/services/prediction_service.py, recommendation_service.py,
  advisory_service.py
- config/core/api/main.py (only additive changes)
- config/core/services/intent_router.py (only additive)
- config/core/services/assistant_service.py (only additive pointer)
- config/core/controllers/assistant_controller.py (only additive branch)
- ALL existing tests (738 baseline)
- alembic/versions/* (no new migrations)
- config/core/models/*, config/core/repositories/* (no changes)

====================================================
9. DATABASE CHANGES
====================================================
DATABASE CHANGES: NONE
No tables, no migrations, no model/repository changes. The feature is
stateless like all prior image detection phases.

====================================================
10. AUTHENTICATION CHANGES
====================================================
AUTH CHANGES: NONE
Existing get_current_user JWT dependency reused unchanged.

====================================================
11. CONFIGURATION CHANGES
====================================================
config/settings.py additions (after Growth Stage section):
- WATER_STRESS_MODEL_PATH: str = ""
- WATER_STRESS_MODEL_LABELS: str = ""
- WATER_STRESS_MODEL_INPUT_SIZE: int = 224

.env.example additions: same three keys with identical documentation
style.

Defaults keep the feature in safe MODEL_NOT_CONFIGURED state.

====================================================
12. API CONTRACT
====================================================
POST /api/water-stress/detect
- Multipart form: file (required, JPG/JPEG/PNG, max 5 MB),
  crop_name (optional)
- Auth: get_current_user (any authenticated user; farmers intended)
- Success 200: WaterStressOut
  { success, status, crop, stress_level, confidence, model, message }
- Upload rejection: 400 { success: False, message, code }
- Provider failure: 502 MODEL_INVALID via WaterStressError handler
- No model configured: 200 MODEL_NOT_CONFIGURED (stress_level=None,
  confidence=None) - honest, never fabricated stress level.

No changes to existing endpoints. /api/assistant gains WATER_STRESS
intent (pointer only).

====================================================
13. SCHEMA DESIGN
====================================================
New: config/core/schemas/water_stress.py
- class WaterStressOut(BaseModel):
    success: bool = True
    status: str
    crop: Optional[str] = None
    stress_level: Optional[str] = None   # NO_STRESS / MILD_STRESS / MODERATE_STRESS / SEVERE_STRESS
    confidence: Optional[float] = None
    model: Optional[str] = None
    message: Optional[str] = ""

Modified: config/core/schemas/__init__.py (export WaterStressOut)
No changes to existing schemas.

====================================================
14. INTENT ROUTING
====================================================
config/core/services/intent_router.py (additive only):
- INTENT_WATER_STRESS = "WATER_STRESS"
- _WATER_STRESS_WORDS = (
    "जल तनाव", "पानी की कमी", "सूखा", "सिंचाई", "विल्ट", "पत्ती लटक",
    "water stress", "waterstress", "irrigation", "drought", "wilting",
    "thirsty", "dry", "moisture stress",
  )
  NOTE: bare "पानी" (water) intentionally NOT a keyword (too generic).
- Classification placed AFTER _GROWTH_STAGE_WORDS and BEFORE the
  CROP_STATUS status_hits block (preserves priority: DISEASE > PEST >
  WEED > NUTRIENT > GROWTH_STAGE > WATER_STRESS > CROP_STATUS > ADVICE).
- _ALL_INTENTS updated; module docstring updated.

assistant_service.py: add pointer
  INTENT_WATER_STRESS:
    "जल तनाव पहचान के लिए पत्ती या फसल की फोटो लेकर "
    "'जल तनाव पहचान' स्क्रीन का उपयोग करें।"

assistant_controller.py: add explicit branch
  if intent == INTENT_WATER_STRESS:
      return self.service.pointer(intent)

====================================================
15. INTENT PRIORITY POSITION
====================================================
Exact position in verified priority order:

HELP
→ AUTH
→ WEATHER
→ MY_FARM
→ SOIL
→ DISEASE_DETECTION
→ PEST_DETECTION
→ WEED_DETECTION
→ NUTRIENT_DEFICIENCY
→ GROWTH_STAGE
→ WATER_STRESS          <-- NEW
→ CROP_STATUS
→ CROP_ADVICE
→ AI_ADVICE
→ UNKNOWN

Existing intents and priority order remain completely unchanged.

====================================================
16. SAFETY CONTRACT
====================================================
- Missing WATER_STRESS_MODEL_PATH -> MODEL_NOT_CONFIGURED
- Missing/corrupt labels -> MODEL_NOT_CONFIGURED with clear message
- Invalid/corrupt ONNX model -> safe failure, never crash, never 5xx
- Label-count mismatch -> MODEL_NOT_CONFIGURED
- Invalid image/output -> safe failure; no fabricated stress level
- Fake prediction prevention: every failure path returns status
  MODEL_NOT_CONFIGURED with stress_level=None and confidence=None;
  status NEVER equals WATER_STRESS_DETECTED in a failure path.
- The assistant intent returns only a static Hindi pointer; it never
  claims a stress level was identified.
- HTTP errors stay inside existing envelope with code fields
  (400 upload, 502 MODEL_INVALID).

====================================================
17. ANTI-FABRICATION RULES
====================================================
The honesty contract is structurally identical to all five prior image
detection phases:
1. Unavailable provider always returns MODEL_NOT_CONFIGURED with
   stress_level=None and confidence=None.
2. Every ONNX failure path (missing runtime, missing file, corrupt
   model, missing labels, label mismatch, empty output) returns
   MODEL_NOT_CONFIGURED - the positive status WATER_STRESS_DETECTED is
   ONLY produced by a real, loaded model with matched labels.
3. Invalid image/output raises safely and is converted to a 502
   MODEL_INVALID envelope at the API layer - never a fabricated stress.
4. No model path setting defaults keep the feature in the safe
   MODEL_NOT_CONFIGURED state out of the box.
5. Tests assert both the positive result AND every negative path.

====================================================
18. MODEL FAILURE / FALLBACK BEHAVIOR
====================================================
| Failure Condition              | Response                          |
|--------------------------------|-----------------------------------|
| No model path configured       | MODEL_NOT_CONFIGURED              |
| Model file missing             | MODEL_NOT_CONFIGURED              |
| onnxruntime unavailable        | MODEL_NOT_CONFIGURED              |
| Corrupt model file             | MODEL_NOT_CONFIGURED              |
| Labels file missing            | MODEL_NOT_CONFIGURED              |
| Label count mismatch           | MODEL_NOT_CONFIGURED              |
| Invalid image path             | Safe exception (never fabricate)  |
| Model inference error          | MODEL_NOT_CONFIGURED              |

All failure paths return honest MODEL_NOT_CONFIGURED with
stress_level=None, confidence=None, model=None.

====================================================
19. IMAGE VALIDATION REQUIREMENTS
====================================================
Identical to all prior image detection endpoints:
- Magic-byte validation: JPEG (FF D8 FF) or PNG (89 50 4E 47)
- Maximum size: 5 MB (configurable via MAX_UPLOAD_SIZE_MB)
- Accepted MIME: image/jpeg, image/png
- Rejection: 400 with structured error envelope
- Secure storage: server-controlled random filename under UPLOAD_DIR
- No client-controlled paths ever reach the provider

====================================================
20. TEST PLAN
====================================================
New file 1: tests/test_water_stress_provider.py (12 tests)
1. test_unavailable_provider_returns_not_configured
2. test_provider_factory_returns_unavailable_when_no_path
3. test_provider_factory_existing_model_returns_real_provider
4. test_onnx_provider_loads_model_successfully
5. test_onnx_provider_successful_detection_returns_stress_confidence
6. test_onnx_provider_missing_model_file_returns_not_configured
7. test_onnx_provider_missing_labels_returns_not_configured
8. test_onnx_provider_label_count_mismatch_returns_not_configured
9. test_onnx_provider_corrupt_model_returns_not_configured
10. test_onnx_provider_invalid_image_path_returns_error
11. test_onnx_provider_nhwc_preprocessing
12. test_onnx_provider_nchw_preprocessing

New file 2: tests/test_water_stress.py (12 tests)
1. test_requires_auth
2. test_allows_any_authenticated_user
3. test_valid_png
4. test_echoes_crop_context
5. test_no_crop_context_is_null
6. test_model_not_configured_status
7. test_no_fake_prediction
8. test_structured_response_shape
9. test_response_never_exposes_local_path
10. test_model_path_set_but_no_loader_still_not_configured
11. test_invalid_image_400
12. test_oversized_image_400

New file 3: tests/test_water_stress_intent.py (10 tests)
1. test_hindi_query (जल तनाव पहचानना है)
2. test_english_query (detect water stress)
3. test_multiple_hindi_phrases
4. test_multiple_english_phrases
5. test_existing_intents_not_misclassified (disease/pest/weed/nutrient/growth/status/advice/weather unchanged)
6. test_unknown_generic_remains_unknown
7. test_pointer_message (service)
8. test_pointer_contract (service)
9. test_api_intent_routes_to_pointer
10. test_api_existing_intents_unchanged

Total new tests: 12 + 12 + 10 = 34

====================================================
21. NUMBER OF NEW TESTS
====================================================
34 new tests (12 provider + 12 API + 10 intent)

====================================================
22. EXPECTED TOTAL TEST COUNT
====================================================
738 (current baseline) + 34 (Phase 1.11) = 772 tests

====================================================
23. REGRESSION REQUIREMENTS
====================================================
- All 738 existing tests must continue to pass unchanged.
- Run the 34 new tests first, then the full suite (expect 772/772).
- 0 failures, 0 regressions required.

====================================================
24. BACKWARD COMPATIBILITY REQUIREMENTS
====================================================
- Existing production files only receive additive changes (new
  constants, new factory, new pointer, new branch, new endpoint,
  new settings with safe defaults).
- Intent priority order preserved exactly:
  HELP -> AUTH -> WEATHER -> MY_FARM -> SOIL -> DISEASE -> PEST ->
  WEED -> NUTRIENT_DEFICIENCY -> GROWTH_STAGE -> WATER_STRESS ->
  CROP_STATUS -> ADVICE -> UNKNOWN.
- All Phase 1.1–1.10 behavior unchanged.
- No DB migrations, no auth changes, no config breaking changes.

====================================================
25. SECURITY REQUIREMENTS
====================================================
- JWT authentication mandatory for detection endpoint
- Image validation via existing secure upload layer (magic bytes,
  size limit, server-controlled storage)
- No local filesystem paths exposed in responses
- Provider internals never leaked to API responses
- Error envelopes follow existing convention (400 upload, 502
  MODEL_INVALID)

====================================================
26. IMPLEMENTATION ORDER
====================================================
1. base.py (constants + ABC + Unavailable provider)
2. water_stress_provider.py (Onnx provider)
3. providers/__init__.py (factory + exports)
4. schemas/water_stress.py + schemas/__init__.py
5. services/water_stress_service.py
6. controllers/water_stress_controller.py
7. settings.py + .env.example
8. intent_router.py
9. assistant_service.py
10. assistant_controller.py
11. main.py (endpoint + error handler)
12. tests: provider -> API -> intent
13. run new tests (34) -> run full suite (expect 772/772)

====================================================
27. BUILDER INSTRUCTIONS
====================================================
- Implement ONLY the files and modifications specified above.
- Reuse the EXACT pattern from Phase 1.10 (Growth Stage) as template.
- Do not refactor unrelated code.
- Do not modify locked previous-phase files except where explicitly
  listed as additive.
- Do not add database migrations, auth changes, or new dependencies.
- Run new tests first, then full suite. Stop if any test fails.
- Do not start Phase 1.12.

====================================================
28. INDEPENDENT TESTER REQUIREMENTS
====================================================
- Run 34 new Phase 1.11 tests independently
- Run full suite (expect 772/772)
- Verify all safety/anti-fabrication checks
- Verify intent routing priority and Hindi/English phrases
- Verify zero regressions on Phase 1.1–1.10
- Do not modify production code or tests

====================================================
29. RISKS / BLOCKERS
====================================================
- Low: pattern is identical to five-time-verified Disease/Pest/Weed/
  Nutrient/Growth Stage detection chain
- No new third-party dependencies
- No database migrations, no auth changes
- Intent keyword risk: bare "पानी" (water) deliberately excluded to
  prevent false positives; specific stress keywords only
- onnxruntime stubbed in tests exactly as in prior phases; missing
  runtime degrades to MODEL_NOT_CONFIGURED safely
- No real model bundled - honest MODEL_NOT_CONFIGURED default expected
  and verified by tests

====================================================
30. FINAL READY-FOR-BUILDER STATUS
====================================================
PHASE 1.11 READY FOR BUILDER: YES