PHASE 1.8 FEATURE:
Weed Detection ONNX Provider

BUSINESS PURPOSE:
Farmers need to identify weeds in their crops to apply the correct herbicide at the right time. Weeds compete with crops for nutrients, water, and sunlight, reducing yields. A farmer taking a photo of a suspicious plant in the field needs an honest, server-controlled AI classification — never a fabricated identification. This feature provides the same safety contract as Disease Detection and Pest Detection: if no model is configured, the API returns MODEL_NOT_CONFIGURED; if a model exists, it runs locally via ONNX and returns the weed name with confidence.

WHY THIS IS THE NEXT PHASE:
- Phase 1.1 established Disease Detection (image-based ONNX)
- Phase 1.6 established Pest Detection (image-based ONNX)
- Phase 1.7 wired Pest Detection into the Intent Router
- The "Crop Health Analysis" trilogy (Disease + Pest + Weed) is the natural completion of image-based AI for field diagnostics
- Every component pattern already exists and is verified: provider factory, service, controller, upload layer, intent routing, MODEL_NOT_CONFIGURED fallback, test patterns
- This is the smallest safe architectural change that moves KisanAI-OS forward — one more ONNX image classifier following the exact established pattern
- No new infrastructure, no database changes, no new auth requirements

CURRENT COMPONENTS TO REUSE:
- config/core/providers/base.py — abstract PestDetectionProvider interface pattern → add WeedDetectionProvider
- config/core/providers/disease_detection_provider.py — OnnxDiseaseDetectionProvider pattern → model for OnnxWeedDetectionProvider
- config/core/providers/pest_detection_provider.py — OnnxPestDetectionProvider pattern → model for OnnxWeedDetectionProvider
- config/core/providers/__init__.py — get_disease_detection_provider(), get_pest_detection_provider() → add get_weed_detection_provider()
- config/core/services/disease_detection_service.py — DiseaseDetectionService pattern → WeedDetectionService
- config/core/services/pest_detection_service.py — PestDetectionService pattern → WeedDetectionService
- config/core/controllers/disease_detection_controller.py — DiseaseDetectionController pattern → WeedDetectionController
- config/core/controllers/pest_detection_controller.py — PestDetectionController pattern → WeedDetectionController
- config/core/schemas/disease_detection.py — DiseaseDetectionOut pattern → WeedDetectionOut
- config/core/schemas/pest_detection.py — PestDetectionOut pattern → WeedDetectionOut
- config/core/api/main.py — /api/disease-detection, /api/pest/detect endpoints → /api/weed/detect
- config/core/services/intent_router.py — INTENT_DISEASE_DETECTION, INTENT_PEST_DETECTION → INTENT_WEED_DETECTION
- config/core/services/assistant_service.py — DISEASE_DETECTION, PEST_DETECTION pointers → WEED_DETECTION pointer
- config/core/controllers/assistant_controller.py — intent handling → WEED_DETECTION branch
- config/settings.py — DISEASE_MODEL_PATH, PEST_MODEL_PATH → WEED_MODEL_PATH, WEED_MODEL_LABELS, WEED_MODEL_INPUT_SIZE
- .env.example — DISEASE_*, PEST_* docs → WEED_* docs
- tests/test_disease_detection_provider.py, tests/test_pest_detection_provider.py — provider test patterns
- tests/test_disease_detection.py, tests/test_pest_detection.py — API test patterns
- tests/test_intent_router.py, tests/test_assistant_service.py, tests/test_assistant_api.py — intent routing test patterns

FILES TO CREATE:
1. config/core/providers/weed_detection_provider.py
2. config/core/schemas/weed_detection.py
3. config/core/services/weed_detection_service.py
4. config/core/controllers/weed_detection_controller.py
5. tests/test_weed_detection_provider.py
6. tests/test_weed_detection.py

FILES TO MODIFY:
1. config/core/providers/base.py
   - Add WeedDetectionProvider abstract class
   - Add UnavailableWeedProvider (MODEL_NOT_CONFIGURED fallback)
   - Add STATUS_WEED_DETECTED, RESULT_WEED_NAME constants
2. config/core/providers/__init__.py
   - Add get_weed_detection_provider() factory
   - Export new classes/constants
3. config/core/schemas/__init__.py
   - Export WeedDetectionOut
4. config/core/services/__init__.py (if exists) or rely on direct imports
5. config/settings.py
   - Add WEED_MODEL_PATH, WEED_MODEL_LABELS, WEED_MODEL_INPUT_SIZE
6. .env.example
   - Add WEED_MODEL_PATH, WEED_MODEL_LABELS, WEED_MODEL_INPUT_SIZE documentation
7. config/core/services/intent_router.py
   - Add INTENT_WEED_DETECTION constant
   - Add _WEED_WORDS keyword tuple (Hindi/Hinglish/English)
   - Add classification logic after PEST_DETECTION, before CROP_STATUS
   - Update module docstring intent list
8. config/core/services/assistant_service.py
   - Import INTENT_WEED_DETECTION
   - Add WEED_DETECTION pointer to _POINTERS dict
9. config/core/controllers/assistant_controller.py
   - Import INTENT_WEED_DETECTION
   - Add explicit WEED_DETECTION branch in handle()
10. config/core/api/main.py
    - Import WeedDetectionController, WeedDetectionServiceError
    - Add /api/weed/detect POST endpoint
    - Add weed_detection_error_handler (502 MODEL_INVALID)

FILES LOCKED / DO NOT TOUCH:
- config/core/providers/disease_detection_provider.py (Phase 1.1, locked)
- config/core/providers/pest_detection_provider.py (Phase 1.6, locked)
- config/core/providers/otp_provider.py (Phase 1.5, locked)
- config/core/providers/prediction_provider.py (existing, locked)
- config/core/providers/recommendation_provider.py (existing, locked)
- config/core/services/disease_detection_service.py (Phase 1.1, locked)
- config/core/services/pest_detection_service.py (Phase 1.6, locked)
- config/core/services/prediction_service.py (existing, locked)
- config/core/services/recommendation_service.py (existing, locked)
- config/core/services/advisory_service.py (existing, locked)
- config/core/services/assistant_service.py (only additive pointer change allowed)
- config/core/services/intent_router.py (only additive intent change allowed)
- config/core/controllers/disease_detection_controller.py (Phase 1.1, locked)
- config/core/controllers/pest_detection_controller.py (Phase 1.6, locked)
- config/core/controllers/assistant_controller.py (only additive intent change allowed)
- config/core/api/main.py (only additive endpoint/handler changes allowed)
- config/core/schemas/disease_detection.py (Phase 1.1, locked)
- config/core/schemas/pest_detection.py (Phase 1.6, locked)
- config/core/schemas/prediction.py (existing, locked)
- config/core/schemas/recommendation.py (existing, locked)
- config/core/schemas/assistant.py (existing, locked)
- tests/test_disease_detection_provider.py (locked)
- tests/test_pest_detection_provider.py (locked)
- tests/test_disease_detection.py (locked)
- tests/test_pest_detection.py (locked)
- tests/test_pest_detection_intent.py (Phase 1.7, locked)
- tests/test_intent_router.py (locked - only verify existing pass)
- tests/test_assistant_service.py (locked - only verify existing pass)
- tests/test_assistant_api.py (locked - only verify existing pass)
- tests/test_otp_auth.py (Phase 1.5, locked)
- tests/test_prediction_provider.py, tests/test_prediction_engine.py (locked)
- tests/test_recommendation_provider.py, tests/test_recommendation_engine.py (locked)
- tests/test_advisory_provider.py, tests/test_advisory.py (locked)
- tests/test_my_farm.py, tests/test_my_farm_persistence.py (Phase 1.2, locked)
- tests/test_auth.py, tests/test_auth_regression.py (Phase 1.5, locked)
- alembic/versions/0001_baseline.py through 0007_*.py (no new migrations)
- config/core/models/*.py (no new models needed)
- config/core/repositories/*.py (no new repositories needed)

IMPLEMENTATION ORDER:
1. config/core/providers/base.py — add WeedDetectionProvider interface + UnavailableWeedProvider + constants
2. config/core/providers/weed_detection_provider.py — OnnxWeedDetectionProvider (mirror OnnxPestDetectionProvider)
3. config/core/providers/__init__.py — add get_weed_detection_provider() factory + exports
4. config/core/schemas/weed_detection.py — WeedDetectionOut schema (mirror PestDetectionOut)
5. config/core/schemas/__init__.py — export WeedDetectionOut
6. config/core/services/weed_detection_service.py — WeedDetectionService + WeedDetectionError (mirror PestDetectionService)
7. config/core/controllers/weed_detection_controller.py — WeedDetectionController (mirror PestDetectionController)
8. config/settings.py — add WEED_MODEL_PATH, WEED_MODEL_LABELS, WEED_MODEL_INPUT_SIZE
9. .env.example — add WEED_* documentation
10. config/core/services/intent_router.py — add INTENT_WEED_DETECTION + _WEED_WORDS + classification
11. config/core/services/assistant_service.py — add WEED_DETECTION pointer
12. config/core/controllers/assistant_controller.py — add WEED_DETECTION branch in handle()
13. config/core/api/main.py — add /api/weed/detect endpoint + error handler
14. tests/test_weed_detection_provider.py — 12 provider tests (mirror test_pest_detection_provider.py)
15. tests/test_weed_detection.py — 12 API tests (mirror test_pest_detection.py)

API CHANGES:
- New endpoint: POST /api/weed/detect (multipart: file + optional crop_name)
  - Response: WeedDetectionOut { status, weed_name, confidence, model, message }
  - Error: 502 MODEL_INVALID via WeedDetectionError handler
- No changes to existing endpoints
- Existing /api/assistant gains WEED_DETECTION intent routing (already handled by Phase 1.7 pattern)

DATABASE CHANGES:
NONE. No new tables, no migrations. Weed Detection is stateless like Disease/Pest Detection.

SCHEMA CHANGES:
- New file: config/core/schemas/weed_detection.py (WeedDetectionOut)
- Modified: config/core/schemas/__init__.py (export)
- No changes to existing schemas

CONFIG CHANGES:
- config/settings.py: WEED_MODEL_PATH (str, default ""), WEED_MODEL_LABELS (str, default ""), WEED_MODEL_INPUT_SIZE (int, default 224)
- .env.example: corresponding documentation lines

SECURITY:
- Endpoint requires JWT authentication (get_current_user dependency, same as /api/disease-detection, /api/pest/detect)
- File upload validated by existing UploadService (5 MB limit, JPG/JPEG/PNG, MIME + magic bytes check)
- No client-controlled model paths — server-controlled via settings.WEED_MODEL_PATH only
- No credentials or secrets exposed
- Error responses follow existing envelope with code field (MODEL_INVALID for provider errors)

SAFETY/FALLBACK:
- UnavailableWeedProvider returns MODEL_NOT_CONFIGURED with weed_name=None, confidence=None — never fabricates a weed identification
- OnnxWeedDetectionProvider validates model file, labels, input shape; any failure returns MODEL_NOT_CONFIGURED
- API returns 502 MODEL_INVALID for provider exceptions (never 500)
- No pest/disease/weed name is ever fabricated — "no model" is clearly distinguished from "weed detected"
- Intent router returns honest Hindi pointer: "खरपतवार पहचान के लिए पत्ती की फोटो लेकर 'खरपतवार पहचान' स्क्रीन का उपयोग करें।"

BACKWARD COMPATIBILITY:
- All 636 existing tests must continue to pass
- No existing provider, service, controller, schema, or API endpoint modified (only additive changes)
- Intent router priority order preserved: HELP → AUTH → WEATHER → MY_FARM → SOIL → DISEASE → PEST → WEED → CROP_STATUS → ADVICE → UNKNOWN
- Existing DISEASE_DETECTION and PEST_DETECTION intents unchanged
- No database migrations
- No config breaking changes (new settings are optional with safe defaults)
- No authentication changes

TEST PLAN:
Provider tests (tests/test_weed_detection_provider.py — 12 tests):
1. test_unavailable_provider_returns_not_configured
2. test_onnx_provider_loads_model_successfully (monkeypatch onnxruntime)
3. test_onnx_provider_missing_model_file_returns_not_configured
4. test_onnx_provider_corrupt_model_returns_not_configured
5. test_onnx_provider_missing_labels_returns_not_configured
6. test_onnx_provider_label_count_mismatch_returns_not_configured
7. test_onnx_provider_invalid_image_path_returns_error
8. test_onnx_provider_successful_detection_returns_weed_name_confidence
9. test_onnx_provider_nhwc_preprocessing
10. test_onnx_provider_nchw_preprocessing
11. test_onnx_provider_lazy_load (session created on first predict)
12. test_provider_factory_returns_unavailable_when_no_path

API tests (tests/test_weed_detection.py — 12 tests):
1. test_weed_detect_requires_auth
2. test_weed_detect_invalid_file_type_rejected
3. test_weed_detect_oversized_file_rejected
4. test_weed_detect_no_model_returns_not_configured
5. test_weed_detect_with_model_returns_detection (monkeypatch provider)
6. test_weed_detect_optional_crop_name_passed_to_provider
7. test_weed_detect_provider_error_returns_502_model_invalid
8. test_weed_detect_response_schema_matches_weeddetectionout
9. test_weed_detect_multiple_concurrent_requests_handled
10. test_weed_detect_image_validation_magic_bytes
11. test_weed_detect_no_fabricated_weed_name_when_no_model
12. test_weed_detect_confidence_range_0_to_1

Intent routing tests (tests/test_weed_detection_intent.py — 10 tests, NEW FILE):
1. test_weed_detection_hindi_query (e.g., "खरपतवार पहचान")
2. test_weed_detection_english_query (e.g., "weed detect")
3. test_weed_detection_multiple_hindi_phrases
4. test_weed_detection_multiple_english_phrases
5. test_existing_intents_not_misclassified_as_weed
6. test_unknown_generic_remains_unknown
7. test_weed_detection_pointer_message (service)
8. test_weed_detection_pointer_contract (service)
9. test_api_weed_detection_intent_routes_to_pointer
10. test_api_existing_intents_unchanged

EXPECTED NEW TEST COUNT:
- Provider tests: 12
- API tests: 12
- Intent routing tests: 10
Total: 34 new tests

EXPECTED FINAL TEST COUNT:
636 + 34 = 670 tests

RISKS/BLOCKERS:
- Low risk: Pattern is identical to Phase 1.6 (Pest Detection) which is verified
- No new dependencies (onnxruntime already in requirements if needed)
- No database migrations
- No configuration breaking changes
- Intent router keyword overlap: "पत्ती" exists in _DISEASE_WORDS; "खरपतवार" (weed) is distinct. Must ensure _WEED_WORDS uses specific Hindi terms (खरपतवार, घास, जंगली घास, weed, unwanted plant) to avoid false positives with DISEASE/Pest
- onnxruntime may not be installed in test environment — provider tests must monkeypatch or the unavailable provider will be used (which is the correct safe behavior)

BUILDER IMPLEMENTATION ORDER:
1. Providers: base.py → weed_detection_provider.py → __init__.py
2. Schemas: weed_detection.py → __init__.py
3. Services: weed_detection_service.py
4. Controllers: weed_detection_controller.py
5. Config: settings.py → .env.example
6. Intent routing: intent_router.py → assistant_service.py → assistant_controller.py
7. API: main.py (endpoint + error handler)
8. Tests: test_weed_detection_provider.py → test_weed_detection.py → test_weed_detection_intent.py
9. Verification: run new tests → run full regression suite (expect 670/670 PASS)

READY FOR BUILDER:
YES