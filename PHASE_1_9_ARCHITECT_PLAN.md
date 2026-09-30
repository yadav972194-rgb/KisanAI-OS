PHASE 1.9 ARCHITECTURE PLAN

====================================================
1. PHASE 1.9 FEATURE NAME
====================================================
Nutrient Deficiency Detection (ONNX, image-based)

Hindi screen name: "पोषक तत्व पहचान" (Nutrient Identification)
Intent code: NUTRIENT_DEFICIENCY

====================================================
2. WHY THIS IS THE NATURAL NEXT FEATURE
====================================================
Phases 1.1 (Disease), 1.6 (Pest) and 1.8 (Weed) established a
three-time-verified image-based ONNX detection pattern:
Provider -> Service -> Controller -> Schema -> API -> Intent routing,
with a strict MODEL_NOT_CONFIGURED safety contract and zero database
changes. That pattern is proven, locked and stable.

A classic, everyday farmer problem remains unsolved by the existing
suite: when a leaf turns yellow or pale, is it a disease, a pest
attack, a weed, or simply a NUTRIENT DEFICIENCY (nitrogen,
phosphorus, potassium)? Today the app can diagnose disease, pest and
weed from a photo, but not nutrient deficiency - so a yellowing leaf
with no visible pathogen falls through to UNKNOWN or is mislabeled as
a disease.

Adding Nutrient Deficiency Detection is the smallest safe
architectural change that:
- Completes the established "crop health diagnosis" family with the
  fourth image classifier, reusing the exact verified pattern.
- Adds no database tables, no migrations, no authentication changes.
- Follows every architectural rule: Provider -> Service -> Controller
  -> API, safe ONNX fallback, never-fabricate, independently testable.
- Provides direct real farmer value (distinguish disease from
  nutrient stress before spending money on pesticides/fertilizers).

This is NOT an invented feature: it is the natural completion of the
leaf/crop-health diagnosis suite already present in Phases 1.1, 1.6
and 1.8.

====================================================
3. USER/FARMER VALUE
====================================================
A farmer photographs a yellowing/pale leaf. The app honestly
identifies the likely nutrient deficiency (e.g. Nitrogen, Phosphorus,
Potassium) OR reports MODEL_NOT_CONFIGURED when no validated model is
provisioned - never a fabricated diagnosis. This lets the farmer:
- distinguish a nutrient stress from a disease/pest/weed problem;
- decide whether fertilizer is needed instead of spending on
  pesticide;
- ask the assistant "पोषक तत्व की कमी पहचानो" and be routed to the
  correct screen.

====================================================
4. EXACT FUNCTIONAL OBJECTIVE
====================================================
Provide a secure, authenticated image-upload endpoint
POST /api/nutrient-deficiency/detect that:
1. Reuses the existing secure upload layer (magic-byte validation,
   size limit, server-controlled storage).
2. Passes the stored image + optional crop context to a replaceable
   ONNX model provider.
3. Returns a structured NutrientDeficiencyOut with status,
   deficiency_name, confidence, model, crop, message.
4. Returns MODEL_NOT_CONFIGURED (deficiency_name=None, confidence=None)
   when no validated model/labels are configured.
5. Never fabricates a deficiency name, confidence or diagnosis.

The assistant intent router additionally maps nutrient-deficiency
phrases (Hindi/Hinglish/English) to INTENT_NUTRIENT_DEFICIENCY and
returns an honest Hindi pointer to the "पोषक तत्व पहचान" screen.

====================================================
5. COMPLETE ARCHITECTURE
====================================================
Mirrors the verified Phase 1.8 Weed Detection architecture exactly:

Farmer photo
  -> FastAPI POST /api/nutrient-deficiency/detect (JWT-protected)
  -> NutrientDeficiencyController
  -> NutrientDeficiencyService
  -> upload_service.save_image() (existing, secure)
  -> NutrientDeficiencyProvider (replaceable)
       - OnnxNutrientDeficiencyProvider (real model)
       - UnavailableNutrientDeficiencyProvider (safe fallback)
  -> structured dict -> NutrientDeficiencyOut

Assistant flow (intent routing):
  Farmer text -> intent_router.classify_intent()
    -> INTENT_NUTRIENT_DEFICIENCY
    -> AssistantController.handle()
    -> AssistantService.pointer() (Hindi pointer, no diagnosis)

====================================================
6. EXACT FILES TO CREATE
====================================================
1. config/core/providers/nutrient_deficiency_provider.py
2. config/core/schemas/nutrient_deficiency.py
3. config/core/services/nutrient_deficiency_service.py
4. config/core/controllers/nutrient_deficiency_controller.py
5. tests/test_nutrient_deficiency_provider.py
6. tests/test_nutrient_deficiency.py
7. tests/test_nutrient_deficiency_intent.py

====================================================
7. EXACT EXISTING FILES TO MODIFY
====================================================
1. config/core/providers/base.py
   - add STATUS_NUTRIENT_DEFICIENCY_DETECTED, RESULT_DEFICIENCY_NAME
   - add NutrientDeficiencyProvider (ABC) + UnavailableNutrientDeficiencyProvider
2. config/core/providers/__init__.py
   - add get_nutrient_deficiency_provider() factory
   - import + export UnavailableNutrientDeficiencyProvider
3. config/core/schemas/__init__.py
   - export NutrientDeficiencyOut
4. config/settings.py
   - add NUTRIENT_DEFICIENCY_MODEL_PATH, _LABELS, _INPUT_SIZE
5. .env.example
   - document the three new settings
6. config/core/services/intent_router.py
   - add INTENT_NUTRIENT_DEFICIENCY constant + _NUTRIENT_WORDS + logic
   - update module docstring + _ALL_INTENTS
7. config/core/services/assistant_service.py
   - import INTENT_NUTRIENT_DEFICIENCY
   - add Hindi pointer in _POINTERS
8. config/core/controllers/assistant_controller.py
   - import INTENT_NUTRIENT_DEFICIENCY
   - add explicit branch in handle()
9. config/core/api/main.py
   - import NutrientDeficiencyController, NutrientDeficiencyError,
     NutrientDeficiencyOut
   - add /api/nutrient-deficiency/detect endpoint
   - add nutrient_deficiency_error_handler (502 MODEL_INVALID)

====================================================
8. FILES THAT MUST REMAIN LOCKED
====================================================
- config/core/providers/disease_detection_provider.py (P1.1)
- config/core/providers/pest_detection_provider.py (P1.6)
- config/core/providers/weed_detection_provider.py (P1.8)
- config/core/providers/otp_provider.py (P1.5)
- config/core/providers/prediction_provider.py (locked)
- config/core/providers/recommendation_provider.py (locked)
- config/core/services/disease_detection_service.py (P1.1)
- config/core/services/pest_detection_service.py (P1.6)
- config/core/services/weed_detection_service.py (P1.8)
- config/core/services/prediction_service.py (locked)
- config/core/services/recommendation_service.py (locked)
- config/core/services/advisory_service.py (locked)
- config/core/controllers/disease_detection_controller.py (P1.1)
- config/core/controllers/pest_detection_controller.py (P1.6)
- config/core/controllers/weed_detection_controller.py (P1.8)
- config/core/schemas/disease_detection.py (P1.1)
- config/core/schemas/pest_detection.py (P1.6)
- config/core/schemas/weed_detection.py (P1.8)
- config/core/schemas/prediction.py, recommendation.py, advisory.py,
  assistant.py (locked)
- config/core/api/main.py (only additive changes allowed)
- config/core/services/intent_router.py (only additive changes allowed)
- config/core/services/assistant_service.py (only additive pointer)
- config/core/controllers/assistant_controller.py (only additive branch)
- ALL existing tests (test_disease_detection*.py, test_pest_detection*.py,
  test_weed_detection*.py, test_otp_auth.py, test_intent_router.py,
  test_assistant_*.py, test_prediction*.py, test_recommendation*.py,
  test_advisory*.py, test_my_farm*.py, test_auth*.py, test_e2e_journey.py,
  etc.)
- alembic/versions/* (no new migrations)
- config/core/models/*, config/core/repositories/* (no changes)

====================================================
9. PROVIDER DESIGN
====================================================
config/core/providers/nutrient_deficiency_provider.py

Base (added to base.py):
- STATUS_NUTRIENT_DEFICIENCY_DETECTED = "NUTRIENT_DEFICIENCY_DETECTED"
- RESULT_DEFICIENCY_NAME = "deficiency_name"
- class NutrientDeficiencyProvider(ABC):
    @abstractmethod detect(image_path, crop_name=None) -> dict
- class UnavailableNutrientDeficiencyProvider(NutrientDeficiencyProvider):
    model_id = "unavailable"
    detect() returns MODEL_NOT_CONFIGURED with deficiency_name=None,
    confidence=None, model=None, message="Nutrient deficiency model is
    not configured".

ONNX provider (new file), mirrors OnnxWeedDetectionProvider exactly:
- __init__(model_path, labels_path=None, input_size=224)
- model_id -> "onnx:<basename>"
- _ensure_loaded(): lazy; fails safely on missing onnxruntime, missing
  file, corrupt model, missing labels, label-count mismatch
- _preprocess(): NHWC/NCHW detection, resize+normalise to float32
- detect(): returns NUTRIENT_DEFICIENCY_DETECTED with label + softmax
  confidence, or MODEL_NOT_CONFIGURED on any failure. Never fabricates.

Factory in __init__.py:
- get_nutrient_deficiency_provider() reads settings
  NUTRIENT_DEFICIENCY_MODEL_PATH; returns real provider only when a
  valid file exists; otherwise UnavailableNutrientDeficiencyProvider.

====================================================
10. SERVICE DESIGN
====================================================
config/core/services/nutrient_deficiency_service.py
- class NutrientDeficiencyError(Exception)
- class NutrientDeficiencyService:
    __init__(upload_service=None, provider=None)
    detect(file, crop_name=None):
      - save via existing upload_service.save_image()
      - build server-side absolute image_path from settings.UPLOAD_DIR
      - call provider.detect(image_path, crop_name)
      - normalize to stable dict: success, status, crop,
        deficiency_name, confidence, model, message
      - raises UploadError (rejected image) or NutrientDeficiencyError
        (provider failure); provider internals never leak.

====================================================
11. CONTROLLER DESIGN
====================================================
config/core/controllers/nutrient_deficiency_controller.py
- class NutrientDeficiencyController:
    __init__(service=None)
    detect(file, crop_name=None) -> service.detect(file, crop_name)

====================================================
12. API CONTRACT
====================================================
POST /api/nutrient-deficiency/detect
- Multipart form: file (required, JPG/JPEG/PNG, max 5 MB),
  crop_name (optional)
- Auth: get_current_user (any authenticated user; farmers intended)
- Success 200: NutrientDeficiencyOut
  { success, status, crop, deficiency_name, confidence, model, message }
- Upload rejection: 400 { success: False, message, code }
- Provider failure: 502 MODEL_INVALID via NutrientDeficiencyError handler
- No model configured: 200 MODEL_NOT_CONFIGURED (deficiency_name=None,
  confidence=None) - honest, never a fabricated diagnosis.

No changes to existing endpoints. /api/assistant gains the
NUTRIENT_DEFICIENCY intent (pointer only).

====================================================
13. SCHEMA CHANGES
====================================================
New: config/core/schemas/nutrient_deficiency.py
- class NutrientDeficiencyOut(BaseModel):
    success: bool = True
    status: str
    crop: Optional[str] = None
    deficiency_name: Optional[str] = None
    confidence: Optional[float] = None
    model: Optional[str] = None
    message: Optional[str] = ""
Modified: config/core/schemas/__init__.py (export NutrientDeficiencyOut)
No changes to existing schemas.

====================================================
14. CONFIGURATION / .env CHANGES
====================================================
config/settings.py additions (after the WEED section):
- NUTRIENT_DEFICIENCY_MODEL_PATH: str = ""
- NUTRIENT_DEFICIENCY_MODEL_LABELS: str = ""
- NUTRIENT_DEFICIENCY_MODEL_INPUT_SIZE: int = 224

.env.example additions: same three keys with the same documentation
style used for WEED_MODEL_*.

Defaults keep the feature in the safe MODEL_NOT_CONFIGURED state.

====================================================
15. INTENT ROUTING CHANGES
====================================================
config/core/services/intent_router.py (additive only):
- INTENT_NUTRIENT_DEFICIENCY = "NUTRIENT_DEFICIENCY"
- _NUTRIENT_WORDS = (
    "पोषक", "पोषण", "पोषक तत्व", "खाद की कमी",
    "nutrient", "deficiency", "nitrogen", "phosphorus", "potassium",
    "नाइट्रोजन", "फास्फोरस", "पोटेशियम",
  )
  NOTE: bare "कमी" is intentionally NOT a keyword (too generic).
- Classification placed AFTER _WEED_WORDS and BEFORE the CROP_STATUS
  status_hits block (preserves priority: DISEASE > PEST > WEED >
  NUTRIENT > CROP_STATUS > ADVICE).
- _ALL_INTENTS updated; module docstring updated.

assistant_service.py: add pointer
  INTENT_NUTRIENT_DEFICIENCY:
    "पोषक तत्व की कमी पहचान के लिए पत्ती की फोटो लेकर
     'पोषक तत्व पहचान' स्क्रीन का उपयोग करें।"

assistant_controller.py: add explicit branch
  if intent == INTENT_NUTRIENT_DEFICIENCY:
      return self.service.pointer(intent)

Existing intents and priority order remain unchanged.

====================================================
16. DATABASE CHANGES
====================================================
DATABASE CHANGES: NONE
No tables, no migrations, no model/repository changes. The feature is
stateless like Disease/Pest/Weed detection.

====================================================
17. AUTHENTICATION CHANGES
====================================================
AUTH CHANGES: NONE
Existing get_current_user JWT dependency reused unchanged.

====================================================
18. SAFETY / FALLBACK CONTRACT
====================================================
- Missing NUTRIENT_DEFICIENCY_MODEL_PATH -> MODEL_NOT_CONFIGURED
- Missing/corrupt labels -> MODEL_NOT_CONFIGURED with clear message
- Invalid/corrupt ONNX model -> safe failure, never crash, never 5xx
- Label-count mismatch -> MODEL_NOT_CONFIGURED
- Invalid image/output -> safe failure; no fabricated deficiency name
- Fake prediction prevention: every failure path returns status
  MODEL_NOT_CONFIGURED with deficiency_name=None and confidence=None;
  status NEVER equals NUTRIENT_DEFICIENCY_DETECTED in a failure path.
- The assistant intent returns only a static Hindi pointer; it never
  claims a deficiency was identified.
- HTTP errors stay inside the existing envelope with code fields
  (400 upload, 502 MODEL_INVALID).

====================================================
19. FAILURE CASES
====================================================
1. Unauthenticated request -> 401
2. Invalid file type / magic bytes -> 400
3. Oversized file -> 400
4. No model configured -> 200 MODEL_NOT_CONFIGURED
5. Model path set but file missing -> 200 MODEL_NOT_CONFIGURED
6. onnxruntime unavailable -> 200 MODEL_NOT_CONFIGURED
7. Corrupt model file -> 200 MODEL_NOT_CONFIGURED
8. Missing labels file -> 200 MODEL_NOT_CONFIGURED
9. Label count mismatch -> 200 MODEL_NOT_CONFIGURED
10. Provider runtime exception -> 502 MODEL_INVALID (never 500)
11. Invalid image path -> safe exception, no fabricated output
12. Unrelated query with "कमी" only -> NOT misrouted to NUTRIENT
    (bare "कमी" is not a keyword)

====================================================
20. BACKWARD COMPATIBILITY PLAN
====================================================
- All 670 existing tests must continue to pass unchanged.
- Existing production files only receive additive changes (new
  constants, new factory, new pointer, new branch, new endpoint,
  new settings with safe defaults).
- Intent priority order preserved exactly:
  HELP -> AUTH -> WEATHER -> MY_FARM -> SOIL -> DISEASE -> PEST ->
  WEED -> NUTRIENT_DEFICIENCY -> CROP_STATUS -> ADVICE -> UNKNOWN.
- Existing DISEASE/PEST/WEED detection behavior, OTP, prediction,
  recommendation, advisory and CROP_STATUS flows unchanged.
- No DB migrations, no auth changes, no config breaking changes.

====================================================
21. TEST PLAN
====================================================
New file 1: tests/test_nutrient_deficiency_provider.py (12 tests)
1. test_unavailable_provider_returns_not_configured
2. test_provider_factory_returns_unavailable_when_no_path
3. test_provider_factory_existing_model_returns_real_provider
4. test_onnx_provider_loads_model_successfully
5. test_onnx_provider_successful_detection_returns_name_confidence
6. test_onnx_provider_missing_model_file_returns_not_configured
7. test_onnx_provider_missing_labels_returns_not_configured
8. test_onnx_provider_label_count_mismatch_returns_not_configured
9. test_onnx_provider_corrupt_model_returns_not_configured
10. test_onnx_provider_invalid_image_path_returns_error
11. test_onnx_provider_nhwc_preprocessing
12. test_onnx_provider_nchw_preprocessing

New file 2: tests/test_nutrient_deficiency.py (12 tests)
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

New file 3: tests/test_nutrient_deficiency_intent.py (10 tests)
1. test_hindi_query (पोषक तत्व की कमी पहचानना है)
2. test_english_query (detect nutrient deficiency)
3. test_multiple_hindi_phrases
4. test_multiple_english_phrases
5. test_existing_intents_not_misclassified (disease/pest/weed/status/
   advice/weather unchanged)
6. test_unknown_generic_remains_unknown
7. test_pointer_message (service)
8. test_pointer_contract (service)
9. test_api_intent_routes_to_pointer
10. test_api_existing_intents_unchanged

Total new tests: 12 + 12 + 10 = 34

====================================================
22. EXPECTED FINAL TEST COUNT
====================================================
670 (current baseline) + 34 (Phase 1.9) = 704 tests

====================================================
23. RISKS / BLOCKERS
====================================================
- Low: pattern is identical to the three-time-verified Disease/Pest/
  Weed detection chain.
- No new third-party dependencies.
- No database migrations, no auth changes.
- Intent keyword risk: bare "कमी" deliberately excluded to prevent
  false positives; specific nutrient keywords only.
- onnxruntime is stubbed in tests exactly as in the Weed/Pest provider
  tests; a missing runtime degrades to MODEL_NOT_CONFIGURED safely.
- No real model is bundled (same as all prior AI phases) - the honest
  MODEL_NOT_CONFIGURED default is expected and verified by tests.

====================================================
24. IMPLEMENTATION ORDER
====================================================
1. base.py (constants + ABC + Unavailable provider)
2. nutrient_deficiency_provider.py (Onnx provider)
3. providers/__init__.py (factory + exports)
4. schemas/nutrient_deficiency.py + schemas/__init__.py
5. services/nutrient_deficiency_service.py
6. controllers/nutrient_deficiency_controller.py
7. settings.py + .env.example
8. intent_router.py
9. assistant_service.py
10. assistant_controller.py
11. main.py (endpoint + error handler)
12. tests: provider -> API -> intent
13. run new tests (34) -> run full suite (expect 704/704)

====================================================
25. WHICH AGENT MUST PERFORM EACH ACTION
====================================================
- kisan-architect: design approval (this plan)
- kisan-builder: implement items 1-11 + tests (items 1-13)
- kisan-tester: independent verification (run 34 new + 670 existing,
  confirm 704/704 PASS, 0 failures, 0 regressions, all safety checks)

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
PHASE 1.9 READY FOR BUILDER: YES
