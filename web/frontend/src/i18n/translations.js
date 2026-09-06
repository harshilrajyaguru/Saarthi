/**
 * Centralized Translation Dictionary
 * Saarthi Multi-Language System
 *
 * Supported languages:
 *   en — English
 *   hi — हिन्दी (Hindi)
 *   gu — ગુજરાતી (Gujarati)
 *   mr — मराठी (Marathi)
 *   kn — ಕನ್ನಡ (Kannada)
 *   te — తెలుగు (Telugu)
 *   ta — தமிழ் (Tamil)
 */

export const SUPPORTED_LANGUAGES = [
  { code: 'en', label: 'English', nativeLabel: 'English' },
  { code: 'hi', label: 'Hindi', nativeLabel: 'हिन्दी' },
  { code: 'gu', label: 'Gujarati', nativeLabel: 'ગુજરાતી' },
  { code: 'mr', label: 'Marathi', nativeLabel: 'मराठी' },
  { code: 'kn', label: 'Kannada', nativeLabel: 'ಕನ್ನಡ' },
  { code: 'te', label: 'Telugu', nativeLabel: 'తెలుగు' },
  { code: 'ta', label: 'Tamil', nativeLabel: 'தமிழ்' },
];

const translations = {
  en: {
    // Navigation — Main
    'nav.menu': 'MENU',
    'nav.dashboard': 'Dashboard',
    'nav.activity': 'Activity',
    'nav.attendance': 'Attendance',
    'nav.government_session': 'Government Session',
    'nav.grade_backlog': 'Grade Backlog',

    // Navigation — Secondary
    'nav.resource': 'Resource',
    'nav.settings': 'Settings',
    'nav.help': 'Help & Support',

    // Header
    'header.dashboard': 'Dashboard',
    'header.activity': 'Activity',
    'header.attendance': 'Attendance',
    'header.government_session': 'Government Session',
    'header.grade_backlog': 'Grade Backlog',
    'header.resource': 'Resource',
    'header.settings': 'Settings',
    'header.help': 'Help & Support',

    // Notifications
    'notifications.title': 'Notifications',
    'notifications.new_count': '{count} New',
    'notifications.empty': 'No new notifications',

    // Teacher Profile
    'profile.settings': 'Settings',
    'profile.sign_out': 'Sign out',
    'profile.teacher': 'Teacher',

    // Language
    'language.title': 'Language',
    'language.change': 'Change language',

    // Theme
    'theme.switch_light': 'Switch to Light Mode',
    'theme.switch_dark': 'Switch to Dark Mode',

    // App content
    'app.foundation_title': 'Foundation & Navigation Surface',
    'app.foundation_desc': 'Saarthi Core UI Components — Phase 1.8 Multi-Language Verification',
    'app.material_label': 'Liquid Glass Material & Tactile Controls',
    'app.primary_action': 'Primary Action',
    'app.secondary_surface': 'Secondary Surface',
    'app.page_content': 'Page content',
  },

  hi: {
    'nav.menu': 'मेन्यू',
    'nav.dashboard': 'डैशबोर्ड',
    'nav.activity': 'गतिविधि',
    'nav.attendance': 'उपस्थिति',
    'nav.government_session': 'सरकारी सत्र',
    'nav.grade_backlog': 'ग्रेड बैकलॉग',

    'nav.resource': 'संसाधन',
    'nav.settings': 'सेटिंग्स',
    'nav.help': 'सहायता',

    'header.dashboard': 'डैशबोर्ड',
    'header.activity': 'गतिविधि',
    'header.attendance': 'उपस्थिति',
    'header.government_session': 'सरकारी सत्र',
    'header.grade_backlog': 'ग्रेड बैकलॉग',
    'header.resource': 'संसाधन',
    'header.settings': 'सेटिंग्स',
    'header.help': 'सहायता',

    'notifications.title': 'सूचनाएँ',
    'notifications.new_count': '{count} नई',
    'notifications.empty': 'कोई नई सूचना नहीं',

    'profile.settings': 'सेटिंग्स',
    'profile.sign_out': 'साइन आउट',
    'profile.teacher': 'शिक्षक',

    'language.title': 'भाषा',
    'language.change': 'भाषा बदलें',

    'theme.switch_light': 'लाइट मोड पर जाएँ',
    'theme.switch_dark': 'डार्क मोड पर जाएँ',

    'app.foundation_title': 'आधार और नेविगेशन सतह',
    'app.foundation_desc': 'Saarthi कोर UI घटक — चरण 1.8 बहुभाषी सत्यापन',
    'app.material_label': 'लिक्विड ग्लास सामग्री और नियंत्रण',
    'app.primary_action': 'मुख्य कार्रवाई',
    'app.secondary_surface': 'सेकेंडरी सतह',
    'app.page_content': 'पृष्ठ सामग्री',
  },

  gu: {
    'nav.menu': 'મેનુ',
    'nav.dashboard': 'ડેશબોર્ડ',
    'nav.activity': 'પ્રવૃત્તિ',
    'nav.attendance': 'હાજરી',
    'nav.government_session': 'સરકારી સત્ર',
    'nav.grade_backlog': 'ગ્રેડ બેકલોગ',

    'nav.resource': 'સંસાધન',
    'nav.settings': 'સેટિંગ્સ',
    'nav.help': 'સહાય',

    'header.dashboard': 'ડેશબોર્ડ',
    'header.activity': 'પ્રવૃત્તિ',
    'header.attendance': 'હાજરી',
    'header.government_session': 'સરકારી સત્ર',
    'header.grade_backlog': 'ગ્રેડ બેકલોગ',
    'header.resource': 'સંસાધન',
    'header.settings': 'સેટિંગ્સ',
    'header.help': 'સહાય',

    'notifications.title': 'સૂચનાઓ',
    'notifications.new_count': '{count} નવી',
    'notifications.empty': 'કોઈ નવી સૂચના નથી',

    'profile.settings': 'સેટિંગ્સ',
    'profile.sign_out': 'સાઇન આઉટ',
    'profile.teacher': 'શિક્ષક',

    'language.title': 'ભાષા',
    'language.change': 'ભાષા બદલો',

    'theme.switch_light': 'લાઇટ મોડ પર જાઓ',
    'theme.switch_dark': 'ડાર્ક મોડ પર જાઓ',

    'app.foundation_title': 'ફાઉન્ડેશન અને નેવિગેશન સપાટી',
    'app.foundation_desc': 'Saarthi કોર UI ઘટકો — તબક્કો 1.8 બહુભાષી ચકાસણી',
    'app.material_label': 'લિક્વિડ ગ્લાસ સામગ્રી અને નિયંત્રણો',
    'app.primary_action': 'મુખ્ય ક્રિયા',
    'app.secondary_surface': 'સેકેન્ડરી સપાટી',
    'app.page_content': 'પૃષ્ઠ સામગ્રી',
  },

  mr: {
    'nav.menu': 'मेनू',
    'nav.dashboard': 'डॅशबोर्ड',
    'nav.activity': 'उपक्रम',
    'nav.attendance': 'उपस्थिती',
    'nav.government_session': 'शासकीय सत्र',
    'nav.grade_backlog': 'ग्रेड बॅकलॉग',

    'nav.resource': 'साधनसामग्री',
    'nav.settings': 'सेटिंग्ज',
    'nav.help': 'मदत',

    'header.dashboard': 'डॅशबोर्ड',
    'header.activity': 'उपक्रम',
    'header.attendance': 'उपस्थिती',
    'header.government_session': 'शासकीय सत्र',
    'header.grade_backlog': 'ग्रेड बॅकलॉग',
    'header.resource': 'साधनसामग्री',
    'header.settings': 'सेटिंग्ज',
    'header.help': 'मदत',

    'notifications.title': 'सूचना',
    'notifications.new_count': '{count} नवीन',
    'notifications.empty': 'नवीन सूचना नाहीत',

    'profile.settings': 'सेटिंग्ज',
    'profile.sign_out': 'साइन आउट',
    'profile.teacher': 'शिक्षक',

    'language.title': 'भाषा',
    'language.change': 'भाषा बदला',

    'theme.switch_light': 'लाइट मोडवर जा',
    'theme.switch_dark': 'डार्क मोडवर जा',

    'app.foundation_title': 'पाया आणि नेव्हिगेशन पृष्ठभाग',
    'app.foundation_desc': 'Saarthi कोर UI घटक — टप्पा 1.8 बहुभाषिक पडताळणी',
    'app.material_label': 'लिक्विड ग्लास साहित्य आणि नियंत्रणे',
    'app.primary_action': 'मुख्य कृती',
    'app.secondary_surface': 'सेकेंडरी पृष्ठभाग',
    'app.page_content': 'पृष्ठ सामग्री',
  },

  kn: {
    'nav.menu': 'ಮೆನು',
    'nav.dashboard': 'ಡ್ಯಾಶ್‌ಬೋರ್ಡ್',
    'nav.activity': 'ಚಟುವಟಿಕೆ',
    'nav.attendance': 'ಹಾಜರಾತಿ',
    'nav.government_session': 'ಸರ್ಕಾರಿ ಅಧಿವೇಶನ',
    'nav.grade_backlog': 'ಗ್ರೇಡ್ ಬ್ಯಾಕ್‌ಲಾಗ್',

    'nav.resource': 'ಸಂಪನ್ಮೂಲ',
    'nav.settings': 'ಸೆಟ್ಟಿಂಗ್‌ಗಳು',
    'nav.help': 'ಸಹಾಯ',

    'header.dashboard': 'ಡ್ಯಾಶ್‌ಬೋರ್ಡ್',
    'header.activity': 'ಚಟುವಟಿಕೆ',
    'header.attendance': 'ಹಾಜರಾತಿ',
    'header.government_session': 'ಸರ್ಕಾರಿ ಅಧಿವೇಶನ',
    'header.grade_backlog': 'ಗ್ರೇಡ್ ಬ್ಯಾಕ್‌ಲಾಗ್',
    'header.resource': 'ಸಂಪನ್ಮೂಲ',
    'header.settings': 'ಸೆಟ್ಟಿಂಗ್‌ಗಳು',
    'header.help': 'ಸಹಾಯ',

    'notifications.title': 'ಅಧಿಸೂಚನೆಗಳು',
    'notifications.new_count': '{count} ಹೊಸ',
    'notifications.empty': 'ಹೊಸ ಅಧಿಸೂಚನೆಗಳಿಲ್ಲ',

    'profile.settings': 'ಸೆಟ್ಟಿಂಗ್‌ಗಳು',
    'profile.sign_out': 'ಸೈನ್ ಔಟ್',
    'profile.teacher': 'ಶಿಕ್ಷಕ',

    'language.title': 'ಭಾಷೆ',
    'language.change': 'ಭಾಷೆ ಬದಲಿಸಿ',

    'theme.switch_light': 'ಲೈಟ್ ಮೋಡ್‌ಗೆ ಬದಲಿಸಿ',
    'theme.switch_dark': 'ಡಾರ್ಕ್ ಮೋಡ್‌ಗೆ ಬದಲಿಸಿ',

    'app.foundation_title': 'ಅಡಿಪಾಯ ಮತ್ತು ನ್ಯಾವಿಗೇಶನ್ ಮೇಲ್ಮೈ',
    'app.foundation_desc': 'Saarthi ಕೋರ್ UI ಘಟಕಗಳು — ಹಂತ 1.8 ಬಹುಭಾಷಾ ಪರಿಶೀಲನೆ',
    'app.material_label': 'ಲಿಕ್ವಿಡ್ ಗ್ಲಾಸ್ ಮೆಟೀರಿಯಲ್ ಮತ್ತು ನಿಯಂತ್ರಣಗಳು',
    'app.primary_action': 'ಪ್ರಾಥಮಿಕ ಕ್ರಿಯೆ',
    'app.secondary_surface': 'ದ್ವಿತೀಯ ಮೇಲ್ಮೈ',
    'app.page_content': 'ಪುಟ ವಿಷಯ',
  },

  te: {
    'nav.menu': 'మెనూ',
    'nav.dashboard': 'డాష్‌బోర్డ్',
    'nav.activity': 'కార్యకలాపం',
    'nav.attendance': 'హాజరు',
    'nav.government_session': 'ప్రభుత్వ సెషన్',
    'nav.grade_backlog': 'గ్రేడ్ బ్యాక్‌లాగ్',

    'nav.resource': 'వనరు',
    'nav.settings': 'సెట్టింగ్‌లు',
    'nav.help': 'సహాయం',

    'header.dashboard': 'డాష్‌బోర్డ్',
    'header.activity': 'కార్యకలాపం',
    'header.attendance': 'హాజరు',
    'header.government_session': 'ప్రభుత్వ సెషన్',
    'header.grade_backlog': 'గ్రేడ్ బ్యాక్‌లాగ్',
    'header.resource': 'వనరు',
    'header.settings': 'సెట్టింగ్‌లు',
    'header.help': 'సహాయం',

    'notifications.title': 'నోటిఫికేషన్‌లు',
    'notifications.new_count': '{count} కొత్త',
    'notifications.empty': 'కొత్త నోటిఫికేషన్‌లు లేవు',

    'profile.settings': 'సెట్టింగ్‌లు',
    'profile.sign_out': 'సైన్ ఔట్',
    'profile.teacher': 'ఉపాధ్యాయుడు',

    'language.title': 'భాష',
    'language.change': 'భాష మార్చండి',

    'theme.switch_light': 'లైట్ మోడ్‌కు మారండి',
    'theme.switch_dark': 'డార్క్ మోడ్‌కు మారండి',

    'app.foundation_title': 'ఫౌండేషన్ మరియు నావిగేషన్ ఉపరితలం',
    'app.foundation_desc': 'Saarthi కోర్ UI భాగాలు — దశ 1.8 బహుభాషా ధృవీకరణ',
    'app.material_label': 'లిక్విడ్ గ్లాస్ మెటీరియల్ మరియు నియంత్రణలు',
    'app.primary_action': 'ప్రాథమిక చర్య',
    'app.secondary_surface': 'ద్వితీయ ఉపరితలం',
    'app.page_content': 'పేజీ కంటెంట్',
  },

  ta: {
    'nav.menu': 'மெனு',
    'nav.dashboard': 'டாஷ்போர்டு',
    'nav.activity': 'செயல்பாடு',
    'nav.attendance': 'வருகை',
    'nav.government_session': 'அரசு அமர்வு',
    'nav.grade_backlog': 'கிரேடு பேக்லாக்',

    'nav.resource': 'வளம்',
    'nav.settings': 'அமைப்புகள்',
    'nav.help': 'உதவி',

    'header.dashboard': 'டாஷ்போர்டு',
    'header.activity': 'செயல்பாடு',
    'header.attendance': 'வருகை',
    'header.government_session': 'அரசு அமர்வு',
    'header.grade_backlog': 'கிரேடு பேக்லாக்',
    'header.resource': 'வளம்',
    'header.settings': 'அமைப்புகள்',
    'header.help': 'உதவி',

    'notifications.title': 'அறிவிப்புகள்',
    'notifications.new_count': '{count} புதிய',
    'notifications.empty': 'புதிய அறிவிப்புகள் இல்லை',

    'profile.settings': 'அமைப்புகள்',
    'profile.sign_out': 'வெளியேறு',
    'profile.teacher': 'ஆசிரியர்',

    'language.title': 'மொழி',
    'language.change': 'மொழி மாற்றவும்',

    'theme.switch_light': 'லைட் பயன்முறைக்கு மாறு',
    'theme.switch_dark': 'டார்க் பயன்முறைக்கு மாறு',

    'app.foundation_title': 'அடிப்படை மற்றும் வழிசெலுத்தல் மேற்பரப்பு',
    'app.foundation_desc': 'Saarthi கோர் UI கூறுகள் — கட்டம் 1.8 பன்மொழி சரிபார்ப்பு',
    'app.material_label': 'லிக்விட் கிளாஸ் மெட்டீரியல் மற்றும் கட்டுப்பாடுகள்',
    'app.primary_action': 'முதன்மை செயல்',
    'app.secondary_surface': 'இரண்டாம் நிலை மேற்பரப்பு',
    'app.page_content': 'பக்க உள்ளடக்கம்',
  },
};

export default translations;
