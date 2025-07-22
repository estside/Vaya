# healthcare_app_motihari/ai_assistant/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import SymptomCheckerForm
from doctors.models import Doctor, Specialty # Keep this if models are in doctors app
import json
from groq import Groq
from django.db.models import Q # Ensure Q is imported
from django.urls import reverse # <--- NEW IMPORT: Import reverse

@login_required
def symptom_checker(request):
    recommended_doctors = []
    ai_response_text = None
    ai_suggested_specialties = []
    disclaimer = "This AI provides general information and suggestions based on your input. It is NOT a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare professional for any health concerns."


    groq_api_key = "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"

    if not groq_api_key:
        messages.error(request, "GROQ API Key is not configured. Please set it in ai_assistant/views.py or environment variables.")
        return render(request, 'ai_assistant/symptom_checker.html', {'form': SymptomCheckerForm(), 'ai_response_text': "API Key not set."})

    client = Groq(api_key=groq_api_key)

    if request.method == 'POST':
        form = SymptomCheckerForm(request.POST)
        if form.is_valid():
            symptoms_input = form.cleaned_data['symptoms']

            prompt = f"""
            As a helpful medical AI assistant, analyze the following symptoms and provide:
            1. A brief, general understanding of what these symptoms might indicate (do NOT provide a diagnosis).
            2. A list of 1-3 medical specialties that would be appropriate to consult for these symptoms.
            3. Emphasize that this is NOT medical advice and a doctor should always be consulted.

            Symptoms: "{symptoms_input}"

            Format your response as a JSON object with the following structure:
            {{
                "understanding": "...",
                "suggested_specialties": ["Specialty 1", "Specialty 2"],
                "disclaimer": "..."
            }}
            """
            try:
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    model="llama3-8b-8192",
                    response_format={"type": "json_object"},
                    temperature=0.7,
                    max_tokens=1024,
                    top_p=1,
                    stream=False,
                    stop=None,
                )

                raw_ai_response = chat_completion.choices[0].message.content
                ai_output = json.loads(raw_ai_response)

                ai_response_text = ai_output.get('understanding', 'Could not generate understanding.')
                ai_suggested_specialties = ai_output.get('suggested_specialties', [])
                ai_disclaimer_from_ai = ai_output.get('disclaimer', disclaimer)
                messages.info(request, ai_disclaimer_from_ai)


                if ai_suggested_specialties:
                    specialty_q_objects = Q()
                    for s_name in ai_suggested_specialties:
                        specialty_q_objects |= Q(specialties__name__icontains=s_name.strip())

                    recommended_doctors = Doctor.objects.filter(
                        is_approved=True
                    ).filter(specialty_q_objects).distinct().prefetch_related('specialties')

                    if not recommended_doctors.exists():
                        messages.warning(request, "We couldn't find specific doctors for the suggested specialties in your area. Consider broadening your search or consulting a General Physician.")
                        recommended_doctors = Doctor.objects.filter(
                            is_approved=True,
                            specialties__name__icontains='General Physician'
                        ).distinct().prefetch_related('specialties')

                # --- CHANGE HERE: Store results in session and redirect ---
                request.session['ai_results'] = {
                    'ai_response_text': ai_response_text,
                    'ai_suggested_specialties': ai_suggested_specialties,
                    'recommended_doctor_ids': [d.id for d in recommended_doctors], # Store IDs
                }
                return redirect(reverse('symptom_checker')) # Redirect to the same URL via GET
                # ---------------------------------------------------------

            except json.JSONDecodeError as e:
                messages.error(request, f"AI response was not valid JSON. Error: {e}. Please try again or refine your symptoms.")
                ai_response_text = "Failed to parse AI response. The AI might not have returned valid JSON."
            except Exception as e:
                messages.error(request, f"An error occurred with the AI service: {e}")
                ai_response_text = "An unexpected error occurred during AI processing."

        else:
            messages.error(request, 'Please correct the errors below.')
    # --- CHANGE HERE: Handle GET request to retrieve results from session ---
    else: # This block handles the initial GET request and subsequent GET requests after redirect
        form = SymptomCheckerForm()
        if 'ai_results' in request.session:
            ai_results = request.session.pop('ai_results') # Retrieve and remove from session
            ai_response_text = ai_results.get('ai_response_text')
            ai_suggested_specialties = ai_results.get('ai_suggested_specialties')
            recommended_doctor_ids = ai_results.get('recommended_doctor_ids')
            recommended_doctors = Doctor.objects.filter(id__in=recommended_doctor_ids).prefetch_related('specialties')
    # -----------------------------------------------------------------------

    context = {
        'form': form,
        'recommended_doctors': recommended_doctors,
        'ai_response_text': ai_response_text,
        'ai_suggested_specialties': ai_suggested_specialties,
    }
    return render(request, 'ai_assistant/symptom_checker.html', context)