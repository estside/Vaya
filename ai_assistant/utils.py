from doctors.models import Doctor, Specialty #
from django.db.models import Q
from fuzzywuzzy import fuzz # Import fuzzywuzzy

def get_doctors_info_by_specialty_names(ai_suggested_specialty_names, similarity_threshold=90):
    """
    Retrieves approved doctors and their specialties based on stricter fuzzy matching (fuzz.ratio)
    of AI-suggested specialty names against database specialties.
    Prioritizes direct matches.
    Returns a formatted string of doctor information (Name, ID, Specialties) suitable for LLM prompt.
    """
    
    if not ai_suggested_specialty_names:
        return "No specific specialties provided by AI for doctor retrieval."

    all_db_specialties = list(Specialty.objects.values_list('name', flat=True))

    matched_db_specialty_ids = set()
    matched_specialty_names = []
    
    # Normalize AI suggestions for comparison
    normalized_ai_suggestions = [name.strip().lower() for name in ai_suggested_specialty_names]

    # --- Strategy 1: Attempt exact (case-insensitive) match first ---
    for ai_name_lower in normalized_ai_suggestions:
        for db_name in all_db_specialties:
            if ai_name_lower == db_name.lower():
                try:
                    matched_specialty_obj = Specialty.objects.get(name__iexact=db_name)
                    matched_db_specialty_ids.add(matched_specialty_obj.id)
                    matched_specialty_names.append(db_name)
                except Specialty.DoesNotExist:
                    pass # Should not happen if db_name came from Specialty.objects
    
    # --- Strategy 2: If not all suggested specialties have exact matches, try strict fuzz.ratio ---
    if len(matched_db_specialty_ids) < len(ai_suggested_specialty_names):
        for ai_name_lower in normalized_ai_suggestions:
            if ai_name_lower not in [n.lower() for n in matched_specialty_names]: # Avoid re-matching already exact ones
                for db_name in all_db_specialties:
                    score = fuzz.ratio(ai_name_lower, db_name.lower())
                    
                    if score >= similarity_threshold:
                        try:
                            matched_specialty_obj = Specialty.objects.get(name__iexact=db_name)
                            if matched_specialty_obj.id not in matched_db_specialty_ids:
                                matched_db_specialty_ids.add(matched_specialty_obj.id)
                                matched_specialty_names.append(db_name)
                        except Specialty.DoesNotExist:
                            pass # Should not happen

    if not matched_db_specialty_ids:
        return "No approved doctors found in our database for these specialties."

    # Now, use the matched specialty IDs to filter doctors
    approved_doctors = Doctor.objects.filter(
        specialties__id__in=list(matched_db_specialty_ids), # Filter by IDs of matched specialties
        is_approved=True
    ).prefetch_related('specialties').distinct() #

    doctors_info_for_llm = []
    if approved_doctors.exists():
        for doctor in approved_doctors:
            specs = ", ".join([s.name for s in doctor.specialties.all()])
            # Format: "- Dr. Full Name (ID: DoctorID, Specialties: X, Y)"
            doctors_info_for_llm.append(f"- Dr. {doctor.full_name} (ID: {doctor.id}, Specialties: {specs})")
        
        return "List of available doctors in Vaya:\n" + "\n".join(doctors_info_for_llm)
    else:
        # This message will be sent to the AI if no doctors are found for the matched specialties
        return f"No approved doctors found for the matched specialties: {', '.join(matched_specialty_names if matched_specialty_names else ai_suggested_specialty_names)}."