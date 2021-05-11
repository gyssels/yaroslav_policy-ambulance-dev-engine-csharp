from engine.code_set import CodeSet, TransportKind

origin_letters      = set("DEGHIJNPRS")  # First  Character- Origin      List: D, E, G, H, I, J, N, P, R, S
destination_letters = set("DEGHIJNPRSX") # Second Character- Destination List: D, E, G, H, I, J, N, P, R, S, X

specialty_care_transport_code = 'A0434'
ground_transport_code_list = ['A0426', 'A0427', 'A0428', 'A0429', 'A0433',
    specialty_care_transport_code, 'A0999']
ground_transport_code_set = CodeSet("Ground Transport", set(ground_transport_code_list))
fixed_wing_air_transport_code = 'A0430'
rotary_wing_air_transport_code = 'A0431'
air_transport_code_list = [fixed_wing_air_transport_code, rotary_wing_air_transport_code]
air_transport_code_set = CodeSet("Air Transport", set(air_transport_code_list))

ground_and_air_transport_code_set = CodeSet("Ground Transport and Air Transport",
    set(ground_transport_code_list).union(set(air_transport_code_list))
)

waiting_time_code = "A0420"
extra_attendant_code = "A0424"

emergency_medical_conditions_code_list = [
    "B9689",
    "B999", "E869", "F068", "F10929", "F19939", "F29", "G4489", "G8929", "H579", "I469", "I499", "J9600", "J984",
    "M549", "O2690", "R002", "R0602", "R0603", "R0689", "R079", "R092", "R0989", "R100", "R109", "R238",  "R4182",
    "R4189", "R4589", "R509", "R52", "R55", "R569", "R58", "R6889", "R7309",     "S0590XA", "T07XXXA", "T148XXA",
    "T1490XA", "T1491XA", "T17300A", "T300", "T50904A", "T59891A", "T5994XA", "T672XXA", "T675XXA", "T68XXXA",
    "T699XXA", "T7500XA", "T751XXA", "T754XXA", "T782XXA", "T7840XA", "T8189XA", "T82519A", "T887XXA",
    "Y710", "Y828", "Z209", "Z7401", "Z779", "Z9181", "Z9981", "Z9989"
    ]
emergency_medical_conditions_code_set = CodeSet("Emergency Medical Conditions",
    set(emergency_medical_conditions_code_list)
)

disposable_supplies_code_list = ["A0382", "A0398"]
oxygen_supplies_code = "A0422"

cms1500_places_of_service_code_set = CodeSet("CMS-1500 Places of Service",
    set("123456789")
)

fixed_wing_transport = TransportKind(CodeSet("Fixed Wing Air Transport code " + fixed_wing_air_transport_code, set([fixed_wing_air_transport_code])), 
    "A0435", "Fixed Wing Air Transport")

rotary_wing_transport = TransportKind(CodeSet("Rotary Wing Air Transport code " + rotary_wing_air_transport_code, set([rotary_wing_air_transport_code])), 
    "A0436", "Rotary Wing Air Transport")

ground_transport = TransportKind(ground_transport_code_set, "A0425", "Ground Transport")
