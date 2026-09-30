PHASE 1.10 ARCHITECTURE PLAN

====================================================
1. PHASE 1.10 FEATURE NAME
====================================================
Crop Growth Stage Detection (ONNX, image-based)

Hindi screen name: "वृद्धि अवस्था पहचान" (Growth Stage Identification)
Intent code: GROWTH_STAGE

====================================================
2. WHY THIS IS THE NATURAL NEXT FEATURE
====================================================
Phases 1.1, 1.6, 1.8 and 1.9 verified the exact image-based ONNX
detection pattern four times (Disease -> Pest -> Weed -> Nutrient
Deficiency): Provider -> Service -> Controller -> Schema -> API ->
Intent routing -> Tests, with a strict MODEL_NOT_CONFIGURED honesty
contract and zero database changes. That pattern is locked, stable and
fully proven.

The crop-photo-analysis family currently answers "what is WRONG with
my crop?" (disease / pest / weed / nutrient stress). It has no answer
for "how far along is my crop?" - the crop growth stage (e.g.
germination, vegetative, flowering, fruiting, maturity). Notably the
existing advisory engine (advisory_service.py:219) and the
recommendation engine (recommendation_provider.py:265) already cite
"according to its growth stage" as a decision factor, yet nothing in
the system can actually determine the stage from a photo. Phase 1.10
closes that real, referenced-but-missing input.

Adding Crop Growth Stage Detection:
- Reuses the exact four-time-verified pattern (fifth image classifier).
- Adds NO database tables, NO migrations, NO authentication changes.
- Provides real farmer value: knowing the growth stage guides
  irrigation, fertilizer and harvest-timing decisions.
- Satisfies every architectural rule: Provider -> Service -> Controller
  -> API, safe ONNX fallback, never-fabricate, independently testable.

This is NOT an invented feature: it is the natural completion of the
leaf/crop photo-analysis suite and supplies a factor the advisory and
recommendation engines already reference.

====================================================
3. USER/FARMER VALUE
====================================================
A farmer photographs the crop canopy/plant. The app honestly reports
the likely growth stage (e.g. "Vegetative" / "Flowering" /
"Fruiting") OR returns MODEL_NOT_CONFIGURED when no validated model is
provisioned - never a fabricated stage. This helps the farmer:
- decide whether to apply irrigation/fertilizer at the right time;
- know whether the crop is near harvest maturity;
- ask the assistant "फसल की वृद्धि अवस्था पहचानो" and be routed to the
  correct screen.

====================================================
4. EXACT FUNCTIONAL OBJECTIVE
====================================================
Provide a secure, authenticated image-upload endpoint
POST /api/growth-stage/detect that:
1. Reuses the existing secure upload layer (magic-byte validation,
   size limit, server-controlled storage).
2. Passes the stored image + optional crop context to a replaceable
   ONNX model provider.
3. Returns a structured GrowthStageOut with status, growth_stage,
   confidence, model, crop, message.
4. Returns MODEL_NOT_CONFIGURED (growth_stage=None, confidence=None)
   when no validated model/labels are configured.
5. Never fabricates a growth stage, confidence or diagnosis.

The assistant intent router additionally maps growth-stage phrases
(Hindi/Hinglish/English) to INTENT_GROWTH_STAGE and returns an honest
Hindi pointer to the "वृद्धि अवस्था पहचान" screen.

====================================================
5. COMPLETE ARCHITECTURE
====================================================
Mirrors the verified Phase 1.9 Nutrient Deficiency architecture exactly:

Farmer photo
  -> FastAPI POST /api/growth-stage/detect (JWT-protected)
  -> GrowthStageController
  -> GrowthStageService
  -> upload_service.save_image() (existing, secure)
  -> GrowthStageProvider (replaceable)
       - OnnxGrowthStageProvider (real model)
       - UnavailableGrowthStageProvider (safe fallback)
  -> structured dict -> GrowthStageOut

Assistant flow (intent routing):
  Farmer text -> intent_router.classify_intent()
    -> INTENT_GROWTH_STAGE
    -> AssistantController.handle()
    -> AssistantService.pointer() (Hindi pointer, no diagnosis)

====================================================
6. EXACT FILES TO CREATE
====================================================
1. config/core/providers/growth_stage_provider.py
2. config/core/schemas/growth_stage.py
3. config/core/services/growth_stage_service.py
4. config/core/controllers/growth_stage_controller.py
5. tests/test_growth_stage_provider.py
6. tests/test_growth_stage.py
7. tests/test_growth_stage_intent.py

====================================================
7. EXACT EXISTING FILES TO MODIFY
====================================================
1. config/core/providers/base.py
   - add STATUS_GROWTH_STAGE_DETECTED, RESULT_GROWTH_STAGE
   - add GrowthStageProvider (ABC) + UnavailableGrowthStageProvider
2. config/core/providers/__init__.py
   - add get_growth_stage_provider() factory
   - import + export UnavailableGrowthStageProvider
3. config/core/schemas/__init__.py
   - export GrowthStageOut
4. config/settings.py
   - add GROWTH_STAGE_MODEL_PATH, _LABELS, _INPUT_SIZE
5. .env.example
   - document the three new settings
6. config/core/services/intent_router.py
   - add INTENT_GROWTH_STAGE constant + _GROWTH_STAGE_WORDS + logic
   - update module docstring + _ALL_INTENTS
7. config/core/services/assistant_service.py
   - import INTENT_GROWTH_STAGE
   - add Hindi pointer in _POINTERS
8. config/core/controllers/assistant_controller.py
   - import INTENT_GROWTH_STAGE
   - add explicit branch in handle()
9. config/core/api/main.py
   - import GrowthStageController, GrowthStageError, GrowthStageOut
   - add /api/growth-stage/detect endpoint
   - add growth_stage_error_handler (502 MODEL_INVALID)

====================================================
8. FILES THAT MUST REMAIN LOCKED
====================================================
- config/core/providers/disease_detection_provider.py (P1.1)
- config/core/providers/pest_detection_provider.py (P1.6)
- config/core/providers/weed_detection_provider.py (P1.8)
- config/core/providers/nutrient_deficiency_provider.py (P1.9)
- config/core/providers/otp_provider.py (P1.5)
- config/core/providers/prediction_provider.py (locked)
- config/core/providers/recommendation_provider.py (locked)
- config/core/services/disease_detection_service.py (P1.1)
- config/core/services/pest_detection_service.py (P1.6)
- config/core/services/weed_detection_service.py (P1.8)
- config/core/services/nutrient_deficiency_service.py (P1.9)
- config/core/services/prediction_service.py (locked)
- config/core/services/recommendation_service.py (locked)
- config/core/services/advisory_service.py (locked)
- config/core/controllers/disease_detection_controller.py (P1.1)
- config/core/controllers/pest_detection_controller.py (P1.6)
- config/core/controllers/weed_detection_controller.py (P1.8)
- config/core/controllers/nutrient_deficiency_controller.py (P1.9)
- config/core/schemas/disease_detection.py (P1.1)
- config/core/schemas/pest_detection.py (P1.6)
- config/core/schemas/weed_detection.py (P1.8)
- config/core/schemas/nutrient_deficiency.py (P1.9)
- config/core/schemas/prediction.py, recommendation.py, advisory.py,
  assistant.py (locked)
- config/core/api/main.py (only additive changes allowed)
- config/core/services/intent_router.py (only additive changes allowed)
- config/core/services/assistant_service.py (only additive pointer)
- config/core/controllers/assistant_controller.py (only additive branch)
- ALL existing tests (test_disease_detection*.py, test_pest_detection*.py,
  test_weed_detection*.py, test_nutrient_deficiency*.py,
  test_otp_auth.py, test_intent_router.py, test_assistant_*.py,
  test_prediction*.py, test_recommendation*.py, test_advisory*.py,
  test_my_farm*.py, test_auth*.py, test_e2e_journey.py, etc.)
- alembic/versions/* (no new migrations)
- config/core/models/*, config/core/repositories/* (no changes)

====================================================
9. PROVIDER DESIGN
====================================================
config/core/providers/growth_stage_provider.py

Base (added to base.py):
- STATUS_GROWTH_STAGE_DETECTED = "GROWTH_STAGE_DETECTED"
- RESULT_GROWTH_STAGE = "growth_stage"
- class GrowthStageProvider(ABC):
    @abstractmethod detect(image_path, crop_name=None) -> dict
- class UnavailableGrowthStageProvider(GrowthStageProvider):
    model_id = "unavailable"
    detect() returns MODEL_NOT_CONFIGURED with growth_stage=None,
    confidence=None, model=None, message="Crop growth stage model is
    not configured".

ONNX provider (new file), mirrors OnnxNutrientDeficiencyProvider
exactly:
- __init__(model_path, labels_path=None, input_size=224)
- model_id -> "onnx:<basename>"
- _ensure_loaded(): lazy; fails safely on missing onnxruntime, missing
  file, corrupt model, missing labels, label-count mismatch
- _preprocess(): NHWC/NCHW detection, resize+normalise to float32
- detect(): returns GROWTH_STAGE_DETECTED with label + softmax
  confidence, or MODEL_NOT_CONFIGURED on any failure. Never fabricates.

Factory in __init__.py:
- get_growth_stage_provider() reads settings GROWTH_STAGE_MODEL_PATH;
  returns real provider only when a valid file exists; otherwise
  UnavailableGrowthStageProvider.

====================================================
10. SERVICE DESIGN
====================================================
config/core/services/growth_stage_service.py
- class GrowthStageError(Exception)
- class GrowthStageService:
    __init__(upload_service=None, provider=None)
    detect(file, crop_name=None):
      - save via existing upload_service.save_image()
      - build server-side absolute image_path from settings.UPLOAD_DIR
      - call provider.detect(image_path, crop_name)
      - normalize to stable dict: success, status, crop,
        growth_stage, confidence, model, message
      - raises UploadError (rejected image) or GrowthStageError
        (provider failure); provider internals never leak.

====================================================
11. CONTROLLER DESIGN
====================================================
config/core/controllers/growth_stage_controller.py
- class GrowthStageController:
    __init__(service=None)
    detect(file, crop_name=None) -> service.detect(file, crop_name)

====================================================
12. API CONTRACT
====================================================
POST /api/growth-stage/detect
- Multipart form: file (required, JPG/JPEG/PNG, max 5 MB),
  crop_name (optional)
- Auth: get_current_user (any authenticated user; farmers intended)
- Success 200: GrowthStageOut
  { success, status, crop, growth_stage, confidence, model, message }
- Upload rejection: 400 { success: False, message, code }
- Provider failure: 502 MODEL_INVALID via GrowthStageError handler
- No model configured: 200 MODEL_NOT_CONFIGURED (growth_stage=None,
  confidence=None) - honest, never a fabricated stage.

No changes to existing endpoints. /api/assistant gains the
GROWTH_STAGE intent (pointer only).

====================================================
13. SCHEMA CHANGES
====================================================
New: config/core/schemas/growth_stage.py
- class GrowthStageOut(BaseModel):
    success: bool = True
    status: str
    crop: Optional[str] = None
    growth_stage: Optional[str] = None
    confidence: Optional[float] = None
    model: Optional[str] = None
    message: Optional[str] = ""
Modified: config/core/schemas/__init__.py (export GrowthStageOut)
No changes to existing schemas.

====================================================
14. CONFIGURATION / .env CHANGES
====================================================
config/settings.py additions (after the Nutrient Deficiency section):
- GROWTH_STAGE_MODEL_PATH: str = ""
- GROWTH_STAGE_MODEL_LABELS: str = ""
- GROWTH_STAGE_MODEL_INPUT_SIZE: int = 224

.env.example additions: same three keys with the same documentation
style used for NUTRIENT_DEFICIENCY_MODEL_*.

Defaults keep the feature in the safe MODEL_NOT_CONFIGURED state.

====================================================
15. INTENT ROUTING CHANGES
====================================================
config/core/services/intent_router.py (additive only):
- INTENT_GROWTH_STAGE = "GROWTH_STAGE"
- _GROWTH_STAGE_WORDS = (
    "वृद्धि अवस्था", "विकास अवस्था", "वृद्धि", "अवस्था", "परिपक्व",
    "growth stage", "growth", "maturity",
  )
  NOTE: bare English "stage" is intentionally NOT a keyword (too
  generic in unrelated sentences).
- Classification placed AFTER _NUTRIENT_WORDS and BEFORE the
  CROP_STATUS status_hits block (preserves priority: DISEASE > PEST >
  WEED > NUTRIENT > GROWTH_STAGE > CROP_STATUS > ADVICE).
- _ALL_INTENTS updated; module docstring updated.

assistant_service.py: add pointer
  INTENT_GROWTH_STAGE:
    "फसल की वृद्धि अवस्था पहचान के लिए पत्ती की फोटो लेकर
     'वृद्धि अवस्था पहचान' स्क्रीन का उपयोग करें।"

assistant_controller.py: add explicit branch
  if intent == INTENT_GROWTH_STAGE:
      return self.service.pointer(intent)

Existing intents and priority order remain unchanged.

====================================================
16. DATABASE CHANGES
====================================================
DATABASE CHANGES: NONE
No tables, no migrations, no model/repository changes. The feature is
stateless like Disease/Pest/Weed/Nutrient deficiency detection.

====================================================
17. AUTHENTICATION CHANGES
====================================================
AUTH CHANGES: NONE
Existing get_current_user JWT dependency reused unchanged.

====================================================
18. SAFETY / FALLBACK CONTRACT
====================================================
- Missing GROWTH_STAGE_MODEL_PATH -> MODEL_NOT_CONFIGURED
- Missing/corrupt labels -> MODEL_NOT_CONFIGURED with clear message
- Invalid/corrupt ONNX model -> safe failure, never crash, never 5xx
- Label-count mismatch -> MODEL_NOT_CONFIGURED
- Invalid image/output -> safe failure; no fabricated growth stage
- Fake prediction prevention: every failure path returns status
  MODEL_NOT_CONFIGURED with growth_stage=None and confidence=None;
  status NEVER equals GROWTH_STAGE_DETECTED in a failure path.
- The assistant intent returns only a static Hindi pointer; it never
  claims a growth stage was identified.
- HTTP errors stay inside the existing envelope with code fields
  (400 upload, 502 MODEL_INVALID).

====================================================
19. FAKE-PREDICTION PREVENTION
====================================================
The honesty contract is structurally identical to the verified
Nutrient Deficiency phase:
1. Unavailable provider always returns MODEL_NOT_CONFIGURED with
   growth_stage=None and confidence=None.
2. Every ONNX failure path (missing runtime, missing file, corrupt
   model, missing labels, label mismatch, empty output) returns
   MODEL_NOT_CONFIGURED - the positive status GROWTH_STAGE_DETECTED is
   ONLY produced by a real, loaded model with matched labels.
3. Invalid image/output raises safely and is converted to a 502
   MODEL_INVALID envelope at the API layer - never a fabricated stage.
4. No model path setting defaults keep the feature in the safe
   MODEL_NOT_CONFIGURED state out of the box.
5. Tests assert both the positive result AND every negative path.

====================================================
20. TEST PLAN
====================================================
New file 1: tests/test_growth_stage_provider.py (12 tests)
1. test_unavailable_provider_returns_not_configured
2. test_provider_factory_returns_unavailable_when_no_path
3. test_provider_factory_existing_model_returns_real_provider
4. test_onnx_provider_loads_model_successfully
5. test_onnx_provider_successful_detection_returns_stage_confidence
6. test_onnx_provider_missing_model_file_returns_not_configured
7. test_onnx_provider_missing_labels_returns_not_configured
8. test_onnx_provider_label_count_mismatch_returns_not_configured
9. test_onnx_provider_corrupt_model_returns_not_configured
10. test_onnx_provider_invalid_image_path_returns_error
11. test_onnx_provider_nhwc_preprocessing
12. test_onnx_provider_nchw_preprocessing

New file 2: tests/test_growth_stage.py (12 tests)
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

New file 3: tests/test_growth_stage_intent.py (10 tests)
1. test_hindi_query (वृद्धि अवस्था पहचानना है)
2. test_english_query (detect crop growth stage)
3. test_multiple_hindi_phrases
4. test_multiple_english_phrases
5. test_existing_intents_not_misclassified (disease/pest/weed/nutrient/
   status/advice/weather unchanged)
6. test_unknown_generic_remains_unknown
7. test_pointer_message (service)
8. test_pointer_contract (service)
9. test_api_intent_routes_to_pointer
10. test_api_existing_intents_unchanged

Total new tests: 12 + 12 + 10 = 34

====================================================
21. EXPECTED TEST COUNT
====================================================
704 (current baseline) + 34 (Phase 1.10) = 738 tests

====================================================
22. REGRESSION PLAN
====================================================
- All 704 existing tests must continue to pass unchanged.
- Run the 34 new tests first, then the full suite (expect 738/738).
- 0 failures, 0 regressions required.

====================================================
23. BACKWARD COMPATIBILITY PLAN
====================================================
- Existing production files only receive additive changes (new
  constants, new factory, new pointer, new branch, new endpoint,
  new settings with safe defaults).
- Intent priority order preserved exactly:
  HELP -> AUTH -> WEATHER -> MY_FARM -> SOIL -> DISEASE -> PEST ->
  WEED -> NUTRIENT_DEFICIENCY -> GROWTH_STAGE -> CROP_STATUS ->
  ADVICE -> UNKNOWN.
- Existing DISEASE/PEST/WEED/NUTRIENT detection behavior, OTP,
  prediction, recommendation, advisory and CROP_STATUS flows unchanged.
- No DB migrations, no auth changes, no config breaking changes.

====================================================
24. IMPLEMENTATION ORDER
====================================================
1. base.py (constants + ABC + Unavailable provider)
2. growth_stage_provider.py (Onnx provider)
3. providers/__init__.py (factory + exports)
4. schemas/growth_stage.py + schemas/__init__.py
5. services/growth_stage_service.py
6. controllers/growth_stage_controller.py
7. settings.py + .env.example
8. intent_router.py
9. assistant_service.py
10. assistant_controller.py
11. main.py (endpoint + error handler)
12. tests: provider -> API -> intent
13. run new tests (34) -> run full suite (expect 738/738)

====================================================
25. WHICH AGENT MUST PERFORM EACH ACTION
====================================================
- kisan-architect: design approval (this plan)
- kisan-builder: implement items 1-11 + tests (items 1-13)
- kisan-tester: independent verification (run 34 new + 704 existing,
  confirm 738/738 PASS, 0 failures, 0 regressions, all safety checks)

====================================================
26. WHETHER PRODUCTION CODE CHANGES WILL BE REQUIRED
====================================================
YES - production code will be changed, but ONLY additively: 4 new
production files (provider, schema, service, controller) + additive
edits to base.py, providers/__init__.py, schemas/__init__.py,
settings.py, .env.example, intent_router.py, assistant_service.py,
assistant_controller.py and main.py. No existing behavior is altered.

====================================================
27. FINAL STATUS
====================================================
PHASE 1.10 READY FOR BUILDER: YES
