from doctors.models import Doctor, Specialty #
from django.db.models import Q
from fuzzywuzzy import fuzz # Import fuzzywuzzy

def _normalize_specialty_for_comparison(name):
    name = name.strip().lower()
    # Convert 'cardiologist' -> 'cardiology', 'dermatologist' -> 'dermatology', etc.
    if name.endswith('ologist'):
        return name[:-3] + 'y'  # Replace 'gist' with 'gy'
    if name.endswith('ology'):
        return name[:-1] + 'ist'  # Replace 'y' with 'ist'
    return name

def get_doctors_for_rag(ai_suggested_specialty_names, similarity_threshold=75):
    """
    Returns a list of approved doctor dicts (id, name, specialties, clinic, etc.) matching the AI-suggested specialties.
    Enhanced: 'cardiologist' matches 'cardiology', etc.
    """
    if not ai_suggested_specialty_names:
        return []
    all_db_specialties = list(Specialty.objects.values_list('name', flat=True))
    matched_db_specialty_ids = set()
    matched_specialty_names = []
    normalized_ai_suggestions = [name.strip().lower() for name in ai_suggested_specialty_names]
    # 1. Exact match
    for ai_name_lower in normalized_ai_suggestions:
        for db_name in all_db_specialties:
            if ai_name_lower == db_name.lower():
                try:
                    matched_specialty_obj = Specialty.objects.get(name__iexact=db_name)
                    matched_db_specialty_ids.add(matched_specialty_obj.id)
                    matched_specialty_names.append(db_name)
                except Specialty.DoesNotExist:
                    pass
    # 2. Suffix/root match (ologist <-> ology)
    for ai_name_lower in normalized_ai_suggestions:
        if ai_name_lower not in [n.lower() for n in matched_specialty_names]:
            ai_root = _normalize_specialty_for_comparison(ai_name_lower)
            for db_name in all_db_specialties:
                db_root = _normalize_specialty_for_comparison(db_name)
                if ai_root == db_root:
                    try:
                        matched_specialty_obj = Specialty.objects.get(name__iexact=db_name)
                        if matched_specialty_obj.id not in matched_db_specialty_ids:
                            matched_db_specialty_ids.add(matched_specialty_obj.id)
                            matched_specialty_names.append(db_name)
                    except Specialty.DoesNotExist:
                        pass
    # 3. Fuzzy match (lowered threshold)
    if len(matched_db_specialty_ids) < len(ai_suggested_specialty_names):
        for ai_name_lower in normalized_ai_suggestions:
            if ai_name_lower not in [n.lower() for n in matched_specialty_names]:
                for db_name in all_db_specialties:
                    score = fuzz.ratio(ai_name_lower, db_name.lower())
                    if score >= similarity_threshold:
                        try:
                            matched_specialty_obj = Specialty.objects.get(name__iexact=db_name)
                            if matched_specialty_obj.id not in matched_db_specialty_ids:
                                matched_db_specialty_ids.add(matched_specialty_obj.id)
                                matched_specialty_names.append(db_name)
                        except Specialty.DoesNotExist:
                            pass
    if not matched_db_specialty_ids:
        return []
    approved_doctors = Doctor.objects.filter(
        specialties__id__in=list(matched_db_specialty_ids),
        is_approved=True
    ).prefetch_related('specialties').distinct()
    doctor_dicts = []
    for doctor in approved_doctors:
        doctor_dicts.append({
            'id': doctor.id,
            'name': doctor.full_name,
            'specialties': [s.name for s in doctor.specialties.all()],
            'clinic': doctor.clinic_name,
            'address': doctor.clinic_address,
            'qualifications': doctor.qualifications,
            'contact_phone': doctor.contact_phone,
            'contact_email': doctor.contact_email,
        })
    return doctor_dicts

def format_doctors_for_llm(doctor_dicts):
    if not doctor_dicts:
        return "No approved doctors found in our database for these specialties."
    lines = [
        f"- Dr. {d['name']} (ID: {d['id']}, Specialties: {', '.join(d['specialties'])}, Clinic: {d['clinic']}, Qualifications: {d['qualifications']})"
        for d in doctor_dicts
    ]
    return "List of available doctors in Vaya:\n" + "\n".join(lines)