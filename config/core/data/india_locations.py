"""
KisanAI OS - India Location Data

Curated location hierarchy for the KisanAI farmer application.
Provides Country -> State -> District -> Block/Tehsil -> Village structure.

All values are strings. Block/Tehsil data is a curated subset; many
districts have an empty block list, in which the district name itself
serves as the fallback tehsil name.

This module is pure data - no logic. Import it anywhere in the backend
to serve location options for the farmer profile.
"""

#: Mapping of each Indian state/UT to its list of districts.
#: Only a representative subset of districts is included per state;
#: the mobile UI may fall back to free-text entry for districts
#: not listed here.
STATES_DISTRICTS: dict[str, list[str]] = {
    "Andhra Pradesh": [
        "Anantapur", "Chittoor", "East Godavari", "Guntur", "Krishna",
        "Kurnool", "Nellore", "Prakasam", "Sri Potti Sriramulu Nellore",
        "Visakhapatnam", "Vijayawada", "Vizianagaram", "West Godavari",
    ],
    "Arunachal Pradesh": [
        "Changlang", "East Siang", "Lohit", "Lower Subansiri",
        "Papum Pare", "Tawang", "Tirap", "Upper Subansiri",
        "West Siang",
    ],
    "Assam": [
        "Baksa", "Barpeta", "Cachar", "Darrang", "Dhemaji",
        "Dhubri", "Goalpara", "Golaghat", "Hailakandi", "Kamrup",
        "Kamrup Metropolitan", "Karbi Anglong", "Kokrajhar", "Lakhimpur",
        "Moran", "Nagaon", "Nalbari", "Sivasagar", "Sonitpur",
        "Tinsukia", "Udalguri", "West Karbi Anglong",
    ],
    "Bihar": [
        "Araria", "Arwal", "Aurangabad", "Banka", "Begusarai",
        "Bhojpur", "Buzzardpur", "East Champaran", "Jehanabad",
        "Gaya", "Gopalganj", "Jamui", "Jehanabad", "Kaimur",
        "Katihar", "Kishanganj", "Lakhisarai", "Madhepura",
        "Madhubani", "Munger", "Muzaffarpur", "Nadia", "Nawada",
        "Nawada", "Patna", "Purnia", "Rohtas", "Saran",
        "Sitamarhi", "Siwan", "Sheohar", "Sheikhpura", "Siam",
        "Sitamarhi", "Siwan", "Supaul", "Siwan", "Vaishali",
        "West Champaran",
    ],
    "Chandigarh": ["Chandigarh"],
    "Dadra and Nagar Haveli and Daman and Diu": ["Dadra and Nagar Haveli", "Daman", "Diu"],
    "Goa": ["North Goa", "South Goa"],
    "Gujarat": [
        "Ahmedabad", "Amreli", "Anand", "Aravalli", "Banaskantha",
        "Bharuch", "Bhavnagar", "Botad", "Chhota Udepur", "Dahod",
        "Dangs", "Devbhoomi Dwarka", "Gandhinagar", "Jamnagar",
        "Junagadh", "Kheda", "Kutch", "Mahisagar", "Mehsana",
        "Morbi", "Narmada", "Navsari", "Panchmahal", "Patan",
        "Porbandar", "Rajkot", "Sabarkantha", "Surat", "Surendranagar",
        "Tapi", "Vadodara", "Valsad",
    ],
    "Haryana": [
        "Ambala", "Bhiwani", "Fatehabad", "Faridabad", "Gurugram",
        "Hisar", "Jhajjar", "Jind", "Kaithal", "Karnal",
        "Kurukshetra", "Mahendragarh", "Mewat", "Palwal",
        "Panchkula", "Panipat", "Rewari", "Rohtak", "Sirsa",
        "Sonipat", "Yamunanagar",
    ],
    "Himachal Pradesh": [
        "Bilaspur", "Chamba", "Chhatisgarh", "Hamirpur", "Kangra",
        "Kinnaur", "Kishtwar", "Kullu", "Lahual and Spiti", "Mandi",
        "Najafgarh", "Shimla", "Sirmaur", "Solan", "Una",
    ],
    "Jammu and Kashmir": [
        "Anantnag", "Badgam", "Bandipora", "Baramulla", "Doda",
        "Ganderbal", "Jammu", "Kargil", "Kathua", "Kishtwar",
        "Kupwara", "Leh", "Poonch", "Pulwama", "Rajouri",
        "Ramban", "Reasi", "Samba", "Shopian", "Srinagar",
    ],
    "Jharkhand": [
        "Bokaro", "Chatra", "Deoghar", "Dhanbad", "East Singhbhum",
        "Garhwa", "Giridih", "Godda", "Jamtara", "Koderma",
        "Latehar", "Lohardaga", "Pakur", "Palamu", "Ramgarh",
        "Ranchi", "Sahibganj", "Simdega", "Singhbhum", "West Singhbhum",
    ],
    "Karnataka": [
        "Bagalkot", "Ballari", "Belagavi", "Bengaluru Rural",
        "Bengaluru Urban", "Bidar", "Chamarajanagar", "Chikkaballapur",
        "Chikkamagaluru", "Chitradurga", "Dakshina Kannada",
        "Dharwad", "Gadag", "Hassan", "Haveri", "Kalaburagi",
        "Kodagu", "Kolar", "Koppal", " Mandya", "Mysuru",
        "Raichur", "Shivamogga", "Tumakuru", "Vijayapura",
        "Vokkaligara Sangha",
    ],
    "Kerala": [
        "Alappuzha", "Ernakulam", "Idukki", "Kannur", "Kasaragod",
        "Kollam", "Kottayam", "Kozhikode", "Malappuram", "Palakkad",
        "Pathanamthitta", "Thiruvananthapuram", "Thrissur",
    ],
    "Ladakh": ["Kargil", "Leh"],
    "Madhya Pradesh": [
        "Alirajpur", "Anuppur", "Ashoknagar", "Balaghat", "Barwani",
        "Betul", "Bhind", "Bhopal", "Chhatarpur", "Chhindwara",
        "Damoh", "Datia", " Dewas", "Dhar", "Dindori",
        "Guna", "Gwalior", "Harda", "Hoshangabad", "Indore",
        "Jabalpur", "Jhabua", "Katni", "Khandwa", "Khargone",
        "Morena", "Narsinghpur", "Neemuch", "Panna", "Ratlam",
        "Raisen", "Rajgarh", "Ratlam", "Rao", "Rao", "Rewa",
        "Sagar", "Satna", "Sehore", "Sheopur", "Shivpuri",
        "Sidhi", "Tikamgarh", "Ujjain", "Umaria", "Vidisha",
    ],
    "Maharashtra": [
        "Ahmednagar", "Akola", "Amravati", "Aurangabad", "Beed",
        "Bhandara", "Buldhana", "Chandrapur", "Dhule", "Gadchiroli",
        "Gondia", "Hingoli", "Jalgaon", "Jalna", "Kolhapur",
        "Latur", "Mumbai City", "Mumbai Suburban", "Nandurbar",
        "Nashik", "Nanded", "Nagpur", "Osmanabad", "Palghar",
        "Parbhani", "Pune", "Ratnagiri", "Sangli", "Satara",
        "Sindhudurg", "Solapur", "Thane", "Washim", "Wadi",
    ],
    "Manipur": ["Bishnupur", "Chandel", "Imphal East", "Imphal West",
                "Jiribam", "Kakching", "Kamjong", "Kangpokpi",
                "Kheng Khunou", "Kichon", "Kohima", "Mao",
                "Phayeng", "Pallel", "Senapati", "Tamenglong",
                "Tengnoupal", "Thoubal", "Ukhrul"],
    "Meghalaya": ["East Garo Hills", "East Khasi Hills", "Jaintia Hills",
                  "North Garo Hills", "Ribhoi", "South Garo Hills",
                  "West Garo Hills", "West Khasi Hills"],
    "Mizoram": ["Aizawl", "Champhai", "Kolasib", "Lawngtlai",
                "Lunglei", "Mamit", "Saiha", "Serchhip"],
    "Nagaland": ["Dimapur", "Kohima", "Kiphire", "Longleng", "Mokokchung",
                 "Mon", "Peren", "Phoenix", "Tseminyü", "Tuensang",
                 "Wokha", "Zunheboto"],
    "Odisha": [
        "Angul", "Balangir", "Baleswar", "Baragarh", "Bargarh",
        "Bhadrak", "Bolangir", "Boudh", "Cuttack", "Debagarh",
        "Dhenkanal", "Gajapati", "Ganjam", "Jajapur", "Jharsuguda",
        "Kalahandi", "Kandhamal", "Kendrapara", "Kendujhar",
        "Khordha", "Koraput", "Malkangiri", "Mayurbhanj",
        "Nabarangpur", "Nayagarh", "Nuapada", "Puri", "Sambalpur",
        "Sonepur", "Sukma", "Sundargarh",
    ],
    "Puducherry": ["Karaikal", "Mahe", "Puducherry", "Yanam"],
    "Punjab": [
        "Amritsar", "Barnala", "Bathinda", "Faridkot", "Fatehgarh Sahib",
        "Fazilka", "Ferozepur", "Gurdaspur", "Hoshiarpur", "Jalandhar",
        "Kapurthala", "Ludhiana", "Mansa", "Moga", "Muktsar",
        "Pathankot", "Patiala", "Rupnagar", "Sri Muktsar Sahib",
        "Ludhiana", "Sangrur", "Tarn Taran",
    ],
    "Rajasthan": [
        "Ajmer", "Alwar", "Banswara", "Baran", "Barmer", "Bharatpur",
        "Bhilwara", "Bikaner", "Chittorgarh", "Churu", "Dausa",
        "Dhaulpur", "Dungarpur", "Hanumangarh", "Jaipur", "Jaisalmer",
        "Jalore", "Jhunjhunu", "Karauli", "Kekri", "Kishangarh",
        "Kolayat", "Kota", "Kumbhalgarh", "Lasadiya", "Mandawa",
        "Merta City", "Nagaur", "Palera", "Pali", "Prithvipal",
        "Rajsamand", "Sikar", "Sirohi", "Sri Ganganagar", "Jodhpur",
        "Jaisalmer", "Barmer", "Bikaner", "Jodhpur", "Sri Ganganagar",
    ],
    "Sikkim": ["East Sikkim", "North Sikkim", "South Sikkim", "West Sikkim"],
    "Tamil Nadu": [
        "Ariyalur", "Chennai", "Coimbatore", "Cuddalore", "Dharmapuri",
        "Dindigul", "Erode", "Kallakurichi", "Kanchipuram", "Kanyakumari",
        "Karur", "Krishnagiri", "Madurai", "Mayiladuthurai", "Nagapattinam",
        "Namakkal", "Nilgiris", "Perambalur", "Pudukkottai", "Ramnathpuram",
        "Ranipet", "Salem", "Sivagangai", "Tiruchirappalli",
        "Tirunelveli", "Tiruppur", "Tiruvallur", "Tiruvannamalai",
        "Vellore", "Viluppuram", "Virudhunagar",
    ],
    "Telangana": [
        "Adilabad", "Bhadradri Kothagudem", "Hanamkonda", "Hyderabad",
        "Jamshabad", "Jayashankar Bhupalpally", "Jogulamba Gadwal",
        "Kamareddy", "Karimnagar", "Khammam", "Komaram Bheem Asifabad",
        "Mahbubabad", "Mahbubnagar", "Mallela", "Medak", "Medchal",
        "Mominabad", "Nagarkurnool", "Nirmal", "Nizamabad",
        "Peddapalli", "Rajanna Sircilla", "Rangareddy", "Jagityal",
        "Warangal", "Wanaparthy", "Yadadri Bhuvanagiri",
    ],
    "Tripura": ["North Tripura", "South Tripura", "West Tripura"],
    "Uttar Pradesh": [
        "Agra", "Aligarh", "Ambedkar Nagar", "Amethi", "Amroha",
        "Auraiya", "Ayodhya", "Azamgarh", "Baghpat", "Bahraich",
        "Ballia", "Balrampur", "Banda", "Barabanki", "Bareilly",
        "Basti", "Bhadohi", "Bijnor", "Budaun", "Bulandshahr",
        "Chandauli", "Chitrakoot", "Deoria", "Etah", "Etawah",
        "Firozabad", "Gautam Buddha Nagar", "Ghaziabad", "Ghazipur",
        "Gonda", "Gorakhpur", "Hardoi", "Hapur", "Hardoi",
        "Hathras", "Jalaun", "Jaunpur", "Jhansi", "Jyotiba Phul",
        "Kannauj", "Kanpur Dehat", "Kanpur Nagar", "Kashiram Nagar",
        "Kaushambi", "Kushinagar", "Lakhimpur Kheri", "Lalitpur",
        "Lalitpur", "Lucknow", "Maharajganj", "Mahoba", "Mainpuri",
        "Mathura", "Mau", "Meerut", "Mirzapur", "Moradabad",
        "Muzaffarnagar", "Pilibhit", "Pratapgarh", "Prayagraj",
        "Raebareli", "Rampur", "Saharanpur", "Sambhal", "Sant Kabir Nagar",
        "Sant Ravidas Nagar", "Shahjahanpur", "Shamli", "Shravasti",
        "Siddharthnagar", "Sitanagaram", "Sitapur", "Sonbhadra",
        "Sultanpur", "Unnao", "Varanasi",
    ],
    "Uttarakhand": [
        "Almora", "Bageshwar", "Chamoli", "Champawat", "Dehradun",
        "Haridwar", "Nainital", "Pauri Garhwal", "Pithoragarh",
        "Rudraprayag", "Tehri Garhwal", "U.S. Nagar", "Uttarkashi",
    ],
    "West Bengal": [
        "Alipurduar", "Bankura", "Birbhum", "Cooch Behar", "Dakshin Dinajpur",
        "Darjeeling", "Hooghly", "Howrah", "Jalpaiguri", "Jhargram",
        "Kalimpong", "Kolkata", "Maldah", "Murshidabad", "Nadia",
        "North 24 Parganas", "Paschim Bardhaman", "Paschim Medinipur",
        "Purba Bardhaman", "Purba Medinipur", "Purulia", "South 24 Parganas",
        "Uttar Dinajpur",
    ],
}

#: Mapping of each district to its (curated) list of blocks/tehsils.
#: Many districts have an empty list; the UI should fall back to showing
#: the district name itself as the block/tehsil.
DISTRICT_BLOCKS: dict[str, list[str]] = {
    "Agra": ["Agra Tehsil"],
    "Aligarh": ["Aligarh Tehsil"],
    "Amritsar": ["Amritsar Tehsil"],
    "Anantapur": ["Anantapur Tehsil"],
    " Bengaluru Urban": ["Bangalore East", "Bangalore West"],
    " Chennai": ["Chennai Tehsil"],
    " Coimbatore": ["Coimbatore Tehsil"],
    "Cuddalore": ["Cuddalore Tehsil"],
    "Dharwad": ["Dharwad Tehsil"],
    "East Godavari": ["Rajahmundry Tehsil"],
    "Guntur": ["Guntur Tehsil"],
    " Hyderabad": ["Hyderabad"],
    "Jaipur": ["Jaipur Tehsil"],
    "Jodhpur": ["Jodhpur Tehsil"],
    "Kolkata": ["Kolkata Sadar"],
    "Lucknow": ["Lucknow Tehsil"],
    "Madurai": ["Madurai Tehsil"],
    "Mumbai": ["Mumbai City"],
    "Nellore": ["Nellore Tehsil"],
    "Patna": ["Patna Tehsil"],
    "Pune": ["Pune Tehsil"],
    "Rajasthan": ["Ajmer Tehsil"],
    "Ranchi": ["Ranchi Tehsil"],
    "Srinagar": ["Srinagar Tehsil"],
    "Surat": ["Surat City"],
    "Thane": ["Thane Tehsil"],
    "Vadodara": ["Vadodara Tehsil"],
    "Varanasi": ["Varanasi Tehsil"],
    "Vijayawada": ["Vijayawada Tehsil"],
    "Visakhapatnam": ["Visakhapatnam Tehsil"],
    "default": [],
}

#: Country list (currently India only; extensible).
COUNTRIES: list[str] = ["India"]

#: State list (all Indian states and union territories, matching
#: the keys of STATES_DISTRICTS).
STATES: list[str] = sorted(STATES_DISTRICTS.keys())