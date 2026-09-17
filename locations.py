"""
Where challenges can come from.

West Bengal and Jharkhand are covered district by district, because that is the
level a state innovation cell actually works at. Every other state is represented
by its major cities, which is enough for a national rollout view and keeps the
dropdown usable.

Add a place by putting it in the right state's list below. Nothing else needs to
change - the dropdowns, filters and the state-level dashboard all read from here.
"""

LOCATIONS = {
    "West Bengal": [
        "Alipurduar", "Bankura", "Birbhum", "Cooch Behar", "Dakshin Dinajpur",
        "Darjeeling", "Hooghly", "Howrah", "Jalpaiguri", "Jhargram", "Kalimpong",
        "Kolkata", "Malda", "Murshidabad", "Nadia", "North 24 Parganas",
        "Paschim Bardhaman", "Paschim Medinipur", "Purba Bardhaman",
        "Purba Medinipur", "Purulia", "South 24 Parganas", "Uttar Dinajpur",
    ],
    "Jharkhand": [
        "Bokaro", "Chatra", "Deoghar", "Dhanbad", "Dumka", "East Singhbhum",
        "Garhwa", "Giridih", "Godda", "Gumla", "Hazaribagh", "Jamtara", "Khunti",
        "Koderma", "Latehar", "Lohardaga", "Pakur", "Palamu", "Ramgarh", "Ranchi",
        "Sahibganj", "Seraikela-Kharsawan", "Simdega", "West Singhbhum",
    ],
    "Odisha": ["Bhubaneswar", "Cuttack", "Rourkela", "Sambalpur", "Puri"],
    "Bihar": ["Patna", "Gaya", "Muzaffarpur", "Bhagalpur"],
    "Assam": ["Guwahati", "Dibrugarh", "Silchar"],
    "Andhra Pradesh": ["Visakhapatnam", "Vijayawada", "Tirupati", "Kakinada"],
    "Telangana": ["Hyderabad", "Warangal"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Tiruchirappalli"],
    "Karnataka": ["Bengaluru", "Mysuru", "Hubballi"],
    "Kerala": ["Kochi", "Thiruvananthapuram", "Kozhikode"],
    "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot"],
    "Madhya Pradesh": ["Bhopal", "Indore", "Jabalpur"],
    "Chhattisgarh": ["Raipur", "Bilaspur"],
    "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur"],
    "Uttar Pradesh": ["Lucknow", "Kanpur", "Varanasi", "Prayagraj", "Noida"],
    "Uttarakhand": ["Dehradun", "Haridwar"],
    "Punjab": ["Ludhiana", "Amritsar"],
    "Haryana": ["Gurugram", "Faridabad"],
    "Delhi": ["New Delhi"],
    "Himachal Pradesh": ["Shimla"],
    "Jammu & Kashmir": ["Srinagar", "Jammu"],
    "Goa": ["Panaji"],
    "Sikkim": ["Gangtok"],
    "Manipur": ["Imphal"],
    "Meghalaya": ["Shillong"],
    "Tripura": ["Agartala"],
    "Nagaland": ["Kohima"],
    "Mizoram": ["Aizawl"],
    "Arunachal Pradesh": ["Itanagar"],
    "Chandigarh": ["Chandigarh"],
    "Puducherry": ["Puducherry"],
}

# flat list, and a reverse lookup so a district always knows its state
DISTRICTS = [d for places in LOCATIONS.values() for d in places]
DISTRICT_STATE = {d: state for state, places in LOCATIONS.items() for d in places}

# The two focus states appear first in every dropdown; the rest follow alphabetically.
FOCUS_STATES = ["West Bengal", "Jharkhand"]
STATES = FOCUS_STATES + sorted(s for s in LOCATIONS if s not in FOCUS_STATES)


def state_of(district):
    return DISTRICT_STATE.get(district, "Other")


def grouped():
    """[(state, [districts]), ...] in dropdown order - used by the <optgroup> selects."""
    return [(s, LOCATIONS[s]) for s in STATES]
