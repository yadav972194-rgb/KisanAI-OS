/// User-facing strings for KisanAI.
///
/// The primary app language is Hindi (Devanagari) with a bilingual fallback
/// for technical labels so the app stays usable for both audiences.
class AppStrings {
  AppStrings._();

  static const String appName = 'KisanAI';
  static const String tagline = 'खेती का डिजिटल साथी';

  // Dashboard
  static const String homeTitle = 'किसान होम';
  static const String weatherCard = 'मौसम';
  static const String cropsCard = 'फसल';
  static const String soilCard = 'मिट्टी';
  static const String diseasesCard = 'रोग ज्ञान';
  static const String diagnosisCard = 'रोग पहचान';
  static const String detectionHubCard = 'फसल निदान';
  static const String recommendationsCard = 'AI सलाह';
  static const String farmersCard = 'किसान';
  static const String myFarmCard = 'मेरा खेत';
  static const String assistantCard = 'फसल सहायक';

  // My Farm
  static const String myFarmTitle = 'मेरा खेत';
  static const String noFarmHint =
      'अपने खेत की जानकारी भरकर बेहतर सलाह पाएं।';
  static const String farmSizeLabel = 'खेत का आकार (एकड़)';
  static const String farmSizeHint = 'वैकल्पिक — उदा. 2.5';
  static const String farmSizeInvalid = 'सही खेत का आकार दर्ज करें';
  static const String villageLabel = 'गाँव';
  static const String districtLabel = 'जिला';
  static const String stateLabel = 'राज्य';
  static const String villageRequired = 'गाँव आवश्यक है';
  static const String districtRequired = 'जिला आवश्यक है';
  static const String stateRequired = 'राज्य आवश्यक है';
  static const String createFarmButton = 'खेत बनाएं';
  static const String updateFarmButton = 'खेत अपडेट करें';
  static const String deleteFarmButton = 'खेत हटाएं';
  static const String editFarmButton = 'खेत संपादित करें';
  static const String farmCreated = 'खेत बना दिया गया';
  static const String farmUpdated = 'खेत अपडेट हो गया';
  static const String farmDeleted = 'खेत हटा दिया गया';
  static const String deleteFarmConfirm =
      'क्या आप अपना खेत हटाना चाहते हैं? इसकी सभी फसलें भी हट जाएंगी।';
  static const String myCropsTitle = 'मेरी फसलें';
  static const String addCropButton = 'फसल जोड़ें';
  static const String noCropsYet = 'अभी कोई फसल नहीं जोड़ी गई';
  static const String cropNameLabel = 'फसल का नाम';
  static const String cropNameRequired = 'फसल का नाम आवश्यक है';
  static const String seasonLabel = 'मौसम';
  static const String seasonRequired = 'मौसम आवश्यक है';
  static const String durationDaysLabel = 'अवधि (दिन)';
  static const String durationDaysInvalid = 'सही अवधि (दिन) दर्ज करें';
  static const String waterRequirementLabel = 'पानी की आवश्यकता';
  static const String waterRequirementRequired = 'पानी की आवश्यकता आवश्यक है';
  static const String saveCropButton = 'सेव करें';
  static const String cropAdded = 'फसल जोड़ दी गई';
  static const String cropUpdated = 'फसल अपडेट हो गई';
  static const String cropDeleted = 'फसल हटा दी गई';
  static const String deleteCropConfirm = 'क्या आप यह फसल हटाना चाहते हैं?';
  static const String editCropButton = 'संपादित करें';
  static const String farmSizeUnit = 'एकड़';
  static const String cropsCountLabel = 'फसलें';

  // Auth
  static const String loginTitle = 'लॉगिन';
  static const String loginSubtitle = 'अपने खाते में प्रवेश करें';
  static const String usernameLabel = 'उपयोगकर्ता नाम';
  static const String usernameHint = 'अपना उपयोगकर्ता नाम दर्ज करें';
  static const String passwordLabel = 'पासवर्ड';
  static const String passwordHint = 'अपना पासवर्ड दर्ज करें';
  static const String loginButton = 'लॉगिन करें';
  static const String loggingIn = 'लॉगिन हो रहा है…';
  static const String usernameRequired = 'उपयोगकर्ता नाम आवश्यक है';
  static const String passwordRequired = 'पासवर्ड आवश्यक है';
  static const String invalidCredentials = 'उपयोगकर्ता नाम या पासवर्ड गलत है';
  static const String forgotPasswordLink = 'पासवर्ड भूल गए?';
  static const String forgotPasswordTitle = 'पासवर्ड भूल गए';
  static const String forgotPasswordHint =
      'अपना मोबाइल नंबर दर्ज करें। पासवर्ड बदलने के लिए OTP भेजा जाएगा।';
  static const String otpLabel = 'OTP कोड';
  static const String otpHint = 'SMS में मिला 6 अंकों का कोड';
  static const String otpRequired = 'OTP कोड आवश्यक है';
  static const String newPasswordLabel = 'नया पासवर्ड';
  static const String sendOtpButton = 'OTP भेजें';
  static const String resetPasswordButton = 'पासवर्ड बदलें';
  static const String otpSent = 'OTP भेज दिया गया।';
  static const String devOtpHint = 'डेवलपमेंट OTP';
  static const String passwordResetSuccess =
      'पासवर्ड बदल दिया गया। अब लॉगिन करें।';
  static const String backToLogin = 'लॉगिन करें';

  // Sign up
  static const String noAccountHint = 'क्या आपका कोई अकाउंट नहीं है?';
  static const String signUpLink = 'नया अकाउंट बनाएं';
  static const String signUpTitle = 'नया अकाउंट बनाएं';
  static const String signUpSubtitle = 'अपना अकाउंट बनाकर लॉगिन करें';
  static const String createAccountButton = 'अकाउंट बनाएं';
  static const String creatingAccount = 'अकाउंट बन रहा है…';
  static const String fullNameLabel = 'पूरा नाम';
  static const String fullNameHint = 'अपना पूरा नाम दर्ज करें';
  static const String fullNameRequired = 'पूरा नाम आवश्यक है';
  static const String mobileNumberLabel = 'मोबाइल नंबर';
  static const String mobileHint = '10 अंकों का मोबाइल नंबर';
  static const String mobileInvalid = 'सही 10 अंकों का मोबाइल नंबर दर्ज करें';
  static const String confirmPasswordLabel = 'पासवर्ड दोबारा';
  static const String confirmPasswordRequired = 'पासवर्ड दोबारा दर्ज करें';
  static const String passwordsMismatch = 'पासवर्ड मेल नहीं खाते';
  static const String passwordMinLength = 'पासवर्ड कम से कम 6 अक्षर का होना चाहिए';
  static const String registrationSuccess = 'अकाउंट बन गया! अब लॉगिन करें।';
  static const String duplicateAccount =
      'यह username या mobile number पहले से मौजूद है।';

  // Errors
  static const String connectionError =
      'नेटवर्क कनेक्शन नहीं मिल पाया। कृपया इंटरनेट जांचकर फिर कोशिश करें।';
  static const String serverError =
      'सर्वर अभी उपलब्ध नहीं है। थोड़ी देर बाद फिर कोशिश करें।';
  static const String sessionExpired =
      'आपका सत्र समाप्त हो गया है। कृपया दोबारा लॉगिन करें।';
  static const String accountNotFound =
      'इस मोबाइल नंबर से कोई खाता नहीं मिला।';
  static const String tooManyAttempts =
      'बहुत अधिक असफल प्रयास। कृपया कुछ समय बाद फिर कोशिश करें।';
  static const String genericError = 'कुछ गड़बड़ हो गई। पुनः प्रयास करें।';
  static const String retry = 'पुनः प्रयास करें';

  // Weather
  static const String weatherTitle = 'मौसम';
  static const String temperatureLabel = 'तापमान';
  static const String humidityLabel = 'नमी';
  static const String windLabel = 'हवा की गति';
  static const String conditionLabel = 'स्थिति';
  static const String updatedLabel = 'अद्यतन समय';
  static const String refreshWeather = 'रीफ्रेश करें';

  // Diagnosis
  static const String diagnosisTitle = 'रोग पहचान';
  static const String pickImage = 'फोटो चुनें';
  static const String changeImage = 'फोटो बदलें';
  static const String cropHint = 'फसल का नाम (वैकल्पिक)';
  static const String detectButton = 'पहचान करें';
  static const String analyzing = 'पहचान हो रही है…';
  static const String modelNotConfigured = 'मॉडल अभी कॉन्फ़िगर नहीं है';
  static const String modelNotConfiguredHint =
      'रोग पहचान मॉडल अभी उपलब्ध नहीं है। बाद में पुनः प्रयास करें।';
  static const String detectedDiseaseLabel = 'पहचाना रोग';
  static const String confidenceLabel = 'विश्वास';
  static const String healthyCrop = 'फसल स्वस्थ';
  static const String healthyCropHint = 'इस फोटो में कोई रोग नहीं पाया गया।';
  static const String noImageSelected = 'कृपया पहले एक फोटो चुनें';
  static const String resultHeading = 'परिणाम';

  // Detection Hub
  static const String detectionHubTitle = 'फसल निदान';

  // Pest Detection
  static const String pestTitle = 'कीट पहचान';

  // Weed Detection
  static const String weedTitle = 'खरपतवार पहचान';

  // Nutrient Deficiency Detection
  static const String nutrientTitle = 'पोषक तत्व पहचान';

  // Growth Stage Detection
  static const String growthStageTitle = 'वृद्धि अवस्था पहचान';

  // Water Stress Detection
  static const String waterStressTitle = 'जल तनाव पहचान';

  // Assistant deep-link
  static const String openDetectionScreen = 'स्क्रीन खोलें';

  // Recommendations
  static const String recommendationsTitle = 'AI सलाह';
  static const String recommendationsSubtitle =
      'फसल, मिट्टी और मौसम की जानकारी भरें';
  static const String cropField = 'फसल का नाम';
  static const String phField = 'मिट्टी का pH';
  static const String moistureField = 'मिट्टी नमी (%)';
  static const String nitrogenField = 'नाइट्रोजन (N)';
  static const String phosphorusField = 'फॉस्फोरस (P)';
  static const String potassiumField = 'पोटैशियम (K)';
  static const String temperatureField = 'तापमान (°C)';
  static const String humidityField = 'हवा में नमी (%)';
  static const String diseaseNameField = 'रोग का नाम (वैकल्पिक)';
  static const String severityField = 'रोग की गंभीरता (वैकल्पिक)';
  static const String getRecommendations = 'सलाह प्राप्त करें';
  static const String loadingRecommendations = 'सलाह बन रही है…';
  static const String recommendationAvailable = 'आपके लिए सलाह';
  static const String noRecommendations = 'कोई सलाह उपलब्ध नहीं';
  static const String insufficientData = 'अपर्याप्त जानकारी';
  static const String insufficientDataHint =
      'सलाह देने के लिए कुछ जानकारी और चाहिए। नीचे देखें।';
  static const String requiredContextLabel = 'आवश्यक जानकारी';
  static const String warningsLabel = 'सावधानियाँ';
  static const String reasonLabel = 'कारण';
  static const String sourceLabel = 'स्रोत';
  static const String severityNone = '— चुनें —';
  static const String severityLow = 'कम';
  static const String severityMedium = 'मध्यम';
  static const String severityHigh = 'अधिक';
  static const String cropNameEmptyError = 'फसल का नाम भरें';
  static const String phRangeError = 'pH 0–14 के बीच होना चाहिए';
  static const String moistureRangeError = 'नमी 0–100 के बीच होनी चाहिए';

  // Lists
  static const String farmersTitle = 'किसान';
  static const String cropsTitle = 'फसल';
  static const String soilTitle = 'मिट्टी';
  static const String diseasesTitle = 'रोग ज्ञान';
  static const String emptyState = 'अभी कोई डेटा उपलब्ध नहीं';
  static const String loading = 'लोड हो रहा है…';
  static const String refresh = 'रीफ्रेश';

  // Assistant
  static const String assistantTitle = 'फसल सहायक';
  static const String assistantHint = 'हिंदी में सवाल पूछें…';
  static const String askButton = 'पूछें';
  static const String assistantSuggestion = 'मेरी फसल के क्या हाल हैं?';
  static const String assistantIntro =
      'अपने खेत या फसल के बारे में सवाल पूछें। उत्तर केवल आपकी सत्यापित जानकारी से दिए जाएँगे।';

  // Voice
  static const String startVoiceInput = 'आवाज़ से पूछें';
  static const String stopListening = 'सुनना बंद करें';
  static const String playVoice = 'बोलें';
  static const String stopVoice = 'बोलना बंद करें';
  static const String voiceUnavailable =
      'वॉइस उपलब्ध नहीं (ऑफलाइन या अनुमति नहीं)';
  static const String micPermissionNeeded =
      'माइक्रोफोन अनुमति चाहिए। सेटिंग्स से दें।';
  static const String farmSectionLabel = 'खेत';
  static const String cropsSectionLabel = 'फसलें';
  static const String weatherSectionLabel = 'मौसम';
  static const String adviceSectionLabel = 'सलाह';
  static const String notAvailable = 'उपलब्ध नहीं';

  // Profile
  static const String profileTitle = 'प्रोफ़ाइल';
  static const String roleLabel = 'भूमिका';
  static const String logout = 'लॉग आउट';
  static const String logoutConfirm = 'क्या आप लॉग आउट करना चाहते हैं?';
  static const String cancel = 'रद्द करें';
  static const String delete = 'हटाएं';
  static const String mobileLabel = 'मोबाइल';
  static const String activeAccount = 'सक्रिय खाता';
  static const String statusLabel = 'स्थिति';
}
