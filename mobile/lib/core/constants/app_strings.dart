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
  static const String recommendationsCard = 'AI सलाह';
  static const String farmersCard = 'किसान';

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

  // Errors
  static const String connectionError =
      'नेटवर्क कनेक्शन नहीं मिल पाया। इंटरनेट कनेक्शन जाँचें और पुनः प्रयास करें।';
  static const String serverError =
      'सर्वर से संपर्क नहीं हो पाया। कुछ समय बाद पुनः प्रयास करें।';
  static const String sessionExpired = 'आपका सत्र समाप्त हो गया। कृपया फिर से लॉगिन करें।';
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
      'रोग पहचान मॉडल अभी सर्वर पर तैयार नहीं है। बाद में पुनः प्रयास करें।';
  static const String detectedDiseaseLabel = 'पहचाना रोग';
  static const String confidenceLabel = 'विश्वास';
  static const String healthyCrop = 'फसल स्वस्थ';
  static const String healthyCropHint = 'इस फोटो में कोई रोग नहीं पाया गया।';
  static const String noImageSelected = 'कृपया पहले एक फोटो चुनें';
  static const String resultHeading = 'परिणाम';

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

  // Profile
  static const String profileTitle = 'प्रोफ़ाइल';
  static const String roleLabel = 'भूमिका';
  static const String logout = 'लॉग आउट';
  static const String logoutConfirm = 'क्या आप लॉग आउट करना चाहते हैं?';
  static const String cancel = 'रद्द करें';
  static const String mobileLabel = 'मोबाइल';
  static const String activeAccount = 'सक्रिय खाता';
  static const String statusLabel = 'स्थिति';
}
