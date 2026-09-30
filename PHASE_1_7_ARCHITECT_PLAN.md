PHASE 1.7 FEATURE:
Pest Detection Intent Integration

WHY PHASE 1.7:
Phase 1.6 added the complete Pest Detection ONNX provider pipeline (model provider, service, controller, API endpoint at `/api/pest/detect`). However, the Intent Router (the conversational entry point for farmers) only has a `DISEASE_DETECTION` intent — no `PEST_DETECTION` intent exists. A farmer asking "कीट पहचान", "पेस्ट डिटेक्शन", "कीड़ा लग गया" or "pest detection" currently receives the generic UNKNOWN pointer instead of being routed to the pest detection screen. This is a clear architectural gap: every image-based AI feature (Disease Detection in Phase 1.1, Pest Detection in Phase 1.6) must be reachable through the Intent Router. Phase 1.7 completes the Phase 1.6 feature by wiring Pest Detection into the conversational layer, following the exact same pattern as DISEASE_DETECTION.

CURRENT ARCHITECTURE:
- Intent Router (`config/core/services/intent_router.py`): Rule-based classifier with 10 stable intents (CROP_STATUS, WEATHER, MY_FARM, DISEASE_DETECTION, CROP_ADVICE, SOIL, AI_ADVICE, AUTH, HELP, UNKNOWN). Keyword lists drive classification; priority ordering prevents misclassification.
- Assistant Service (`config/core/services/assistant_service.py`): Routes intents to handlers. CROP_STATUS and WEATHER return real verified data; all other intents return honest Hindi pointer messages via `_POINTERS` dict.
- Assistant Controller (`config/core/controllers/assistant_controller.py`): Thin controller calling `AssistantService.handle()`.
- Assistant API (`/api/assistant` in `main.py`): POST endpoint accepting `AssistantRequest(text, soil?, disease?)`, returns `AssistantOut(intent, status, message, data)`.
- Pest Detection API (`/api/pest/detect` in `main.py`): POST multipart endpoint (image + optional crop_name), returns `PestDetectionOut(status, pest_name, confidence, model, ...)`. Implemented in Phase 1.6, fully tested.

EXACT FILES TO CREATE:
None — this phase only modifies existing files.

EXACT FILES TO MODIFY:
1. `config/core/services/intent_router.py`
   - Add `INTENT_PEST_DETECTION = "PEST_DETECTION"` constant
   - Add `_PEST_WORDS` tuple with Hindi/Hinglish/English pest keywords (e.g., "कीट", "कीड़ा", "पेस्ट", "pest", "कीटनाशक", "कीट पहचान", "पेस्ट डिटेक्शन", "पौधे पर कीट")
   - Add PEST_DETECTION to `_ALL_INTENTS`
   - Add classification logic for PEST_DETECTION (after DISEASE_DETECTION, before CROP_STATUS to avoid false positives on "फसल")
2. `config/core/services/assistant_service.py`
   - Import `INTENT_PEST_DETECTION` from intent_router
   - Add pointer message to `_POINTERS` dict: `"कीट पहचान के लिए पत्ती की फोटो लेकर 'कीट पहचान' स्क्रीन का उपयोग करें।"`
3. `config/core/controllers/assistant_controller.py`
   - Import `INTENT_PEST_DETECTION` from intent_router
   - Add `elif intent == INTENT_PEST_DETECTION: return self.service.pointer(intent)` branch in `handle()`

FILES THAT MUST NOT BE TOUCHED:
- `config/core/providers/pest_detection_provider.py` — Phase 1.6 provider, locked
- `config/core/providers/disease_detection_provider.py` — Phase 1.1 provider, locked
- `config/core/services/pest_detection_service.py` — Phase 1.6 service, locked
- `config/core/services/disease_detection_service.py` — Phase 1.1 service, locked
- `config/core/api/main.py` — Pest detection endpoint already wired, no changes needed
- `config/core/schemas/pest_detection.py` — Phase 1.6 schema, locked
- `config/core/schemas/assistant.py` — Request/response already support optional context, no changes needed
- `tests/test_pest_detection_provider.py` — Phase 1.6 tests, locked
- `tests/test_pest_detection.py` — Phase 1.6 tests, locked
- `tests/test_disease_detection_provider.py` — Phase 1.1 tests, locked
- `tests/test_disease_detection.py` — Phase 1.1 tests, locked
- `tests/test_intent_router.py` — existing intent router tests, only additive changes
- `tests/test_assistant_service.py` — existing assistant tests, only additive changes
- `tests/test_assistant_api.py` — existing API tests, only additive changes

IMPLEMENTATION ORDER:
1. `config/core/services/intent_router.py` — add intent constant, keywords, classification logic
2. `config/core/services/assistant_service.py` — add pointer message
3. `config/core/controllers/assistant_controller.py` — handle new intent
4. `tests/test_intent_router.py` — add PEST_DETECTION classification tests
5. `tests/test_assistant_service.py` — add pointer response test
6. `tests/test_assistant_api.py` — add API integration test for PEST_DETECTION intent

API CHANGES:
None. No new endpoints. Existing `/api/assistant` already returns `AssistantOut` with `intent` and `message` fields — the new intent fits the existing contract.

DATABASE CHANGES:
None. No new tables, no migrations. Intent router is stateless; assistant is stateless.

CONFIGURATION CHANGES:
None. No new settings required. The intent router uses hardcoded keyword tuples.

SECURITY REQUIREMENTS:
- No new attack surface — same `/api/assistant` endpoint with existing JWT authentication
- Pest detection intent returns a pointer message only (no image analysis in the chat flow); actual pest detection remains on the dedicated `/api/pest/detect` endpoint with image upload validation
- No credentials or secrets involved
- Hindi-first error messages preserved

SAFETY/FALLBACK:
- Unknown/misspelled pest queries fall through to UNKNOWN intent (existing behavior)
- No fabricated results — pointer message is static, honest Hindi text
- If intent router misclassifies, priority ordering (DISEASE_DETECTION before PEST_DETECTION before CROP_STATUS) ensures disease queries still route correctly
- Missing/empty query → UNKNOWN (unchanged)

BACKWARD COMPATIBILITY:
- All existing intents unchanged: CROP_STATUS, WEATHER, MY_FARM, DISEASE_DETECTION, CROP_ADVICE, SOIL, AI_ADVICE, AUTH, HELP, UNKNOWN
- `AssistantOut` schema unchanged — new intent is just a new string value in `intent` field
- All existing tests for intent router, assistant service, assistant API must continue to pass
- No changes to disease detection, pest detection, weather, my farm, or auth flows

TEST PLAN:
1. `tests/test_intent_router.py` — add 6 tests:
   - `test_intent_pest_detection_hindi_keywords` — "कीट पहचान", "पत्ती पर कीड़ा", "कीट लगा है" → PEST_DETECTION
   - `test_intent_pest_detection_hinglish_keywords` — "pest detection", "keet pehchan" → PEST_DETECTION
   - `test_intent_pest_detection_english_keywords` — "pest detect", "insect identification" → PEST_DETECTION
   - `test_intent_pest_priority_over_crop_status` — "फसल पर कीट" → PEST_DETECTION (not CROP_STATUS)
   - `test_intent_pest_priority_after_disease` — "रोग और कीट दोनों" → DISEASE_DETECTION (disease words checked first)
   - `test_intent_pest_no_false_positive` — "कीटनाशक दवा" → PEST_DETECTION (acceptable; keyword-based)
2. `tests/test_assistant_service.py` — add 2 tests:
   - `test_pointer_pest_detection` — `service.pointer(INTENT_PEST_DETECTION)` returns correct Hindi pointer message
   - `test_pointer_pest_detection_structure` — response has `intent=PEST_DETECTION`, `status=OK`, `message` non-empty, `data=None`
3. `tests/test_assistant_api.py` — add 2 tests:
   - `test_api_pest_detection_intent` — POST `/api/assistant` with "कीट पहचान" → 200, `intent=PEST_DETECTION`, pointer message in `message`
   - `test_api_pest_detection_intent_no_fabrication` — response `data` is None, no pest name/confidence fabricated

EXPECTED TEST COUNT:
- Baseline: 626/626 PASS
- New tests: 10 (6 intent router + 2 assistant service + 2 assistant API)
- Expected total: 636/636 PASS

REGRESSION REQUIREMENT:
All 626 existing tests must continue to pass. No modifications to Phase 1.1–1.6 code paths.

RISKS/BLOCKERS:
- Low risk: Changes are purely additive to keyword lists and pointer dict
- No new dependencies, no database changes, no API contract changes
- Priority ordering in intent router must be verified: DISEASE_DETECTION keywords checked before PEST_DETECTION to prevent "रोग और कीट" from routing to pest
- Hindi keyword coverage should be reviewed by native speaker (but existing disease keywords work as precedent)

READY FOR BUILDER:
YES