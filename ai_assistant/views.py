import json
import os
import re
from django.shortcuts import render
from django.conf import settings
from groq import Groq # Groq API client
from .forms import SymptomCheckerForm
from doctors.models import Doctor # This imports the Doctor model
from .utils import get_doctors_info_by_specialty_names # Helper for RAG doctor retrieval
from chat.models import Message # Message model for chat history
from django.contrib.auth import get_user_model # To get CustomUser model
from django.db.models import Q # For complex database queries
from django.urls import reverse # Required for generating URLs
from django.utils.safestring import mark_safe # Required for rendering safe HTML


# Get the CustomUser model
User = get_user_model()

# Initialize Groq client with API key
# IMPORTANT: Replace "YOUR_GROQ_API_KEY_HERE" with your actual Groq API Key
# For production, it's highly recommended to set this as an environment variable
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")
client = Groq(api_key=GROQ_API_KEY)

# Store AI Assistant User globally to avoid repeated DB lookups
AI_ASSISTANT_USER = None

def get_ai_assistant_user():
    """
    Retrieves or attempts to create the dedicated AI Assistant User.
    This user acts as the sender for AI-generated messages in the chat history.
    """
    global AI_ASSISTANT_USER
    if AI_ASSISTANT_USER is None:
        try:
            AI_ASSISTANT_USER = User.objects.get(username='AI_Assistant')
        except User.DoesNotExist:
            print("ERROR: 'AI_Assistant' user not found. Please create it in Django Admin.")
            AI_ASSISTANT_USER = None # Ensure it remains None if not found
        except Exception as e:
            print(f"ERROR: Could not retrieve AI_Assistant user: {e}")
            AI_ASSISTANT_USER = None
    return AI_ASSISTANT_USER


def symptom_checker(request):
    # Initialize variables at the top of the function
    form = SymptomCheckerForm()
    ai_response = None
    is_medical_query = False
    
    # Get the AI Assistant user (essential for saving AI messages)
    ai_assistant_user = get_ai_assistant_user()
    if ai_assistant_user is None:
        context = {
            'form': form,
            'ai_response': "AI Assistant is not configured. Please ensure 'AI_Assistant' user exists in the admin panel.",
            'is_medical_query': False,
            'conversation_history': [],
        }
        return render(request, 'ai_assistant/symptom_checker.html', context)


    if request.method == 'POST':
        form = SymptomCheckerForm(request.POST)
        if form.is_valid():
            user_symptoms = form.cleaned_data['symptoms']

            # 1. Save the user's message to the database for history
            user_message_obj = Message.objects.create(
                sender=request.user,
                content=user_symptoms,
                appointment=None, # Mark as AI chat (not tied to an appointment)
                ai_chat_for_user=request.user # CRUCIAL: Link this AI chat message to the specific user
            )


            # 2. Retrieve the relevant AI chat history for this specific user
            recent_messages = Message.objects.filter(
                ai_chat_for_user=request.user, # Filter by the current user's AI conversations
                appointment__isnull=True # Ensure it's an AI chat message
            ).order_by('-timestamp')[:10] # Get the last 10 messages (adjust as needed)
            recent_messages = list(reversed(recent_messages))

            # --- RAG Step (Phase 1): First AI call to get specialties ---
            initial_ai_query = f"""
            Analyze the following user input for symptoms and suggest relevant medical specialties.
            Return ONLY a JSON object with a 'specialties' key (list of strings).
            Example: {{"specialties": ["General Physician", "Pediatrician"]}}

            User input: "{user_symptoms}"
            """
            # Add history to the first AI call too, for better specialty suggestion context
            messages_for_initial_llm = []
            messages_for_initial_llm.append({"role": "system", "content": "You are a medical AI that identifies relevant specialties from user symptoms. Respond in JSON format only."})
            for msg in recent_messages:
                role = "user" if msg.sender == request.user else "assistant"
                messages_for_initial_llm.append({"role": role, "content": msg.content})
            messages_for_initial_llm.append({"role": "user", "content": initial_ai_query})


            suggested_specialties = []
            try:
                initial_chat_completion = client.chat.completions.create(
                    messages=messages_for_initial_llm,
                    model="llama3-8b-8192",
                    response_format={"type": "json_object"},
                )
                raw_initial_response = initial_chat_completion.choices[0].message.content
                parsed_initial_response = json.loads(raw_initial_response)
                suggested_specialties = parsed_initial_response.get("specialties", [])
            except (json.JSONDecodeError, Exception) as e:
                ai_response = "I couldn't process your symptoms to suggest specialties right now. Please try again or rephrase."
                # Fallback if initial specialty extraction fails, no doctor retrieval
                context = {
                    'form': form,
                    'ai_response': ai_response,
                    'is_medical_query': False,
                    'conversation_history': Message.objects.filter(ai_chat_for_user=request.user, appointment__isnull=True).order_by('timestamp'),
                }
                return render(request, 'ai_assistant/symptom_checker.html', context)


            # --- RAG Step (Retrieve from DB): Get doctors based on suggested specialties ---
            recommended_doctors_text = get_doctors_info_by_specialty_names(suggested_specialties)


            # --- RAG Step (Augment Prompt & Final Generation): Second AI call with context ---
            final_ai_prompt_template = f"""
            You are a highly knowledgeable medical AI assistant of an App named Vaya and u from india so give answers in indian context . Provide a general understanding of the user's symptoms, suggest relevant medical specialties, and recommend approved doctors ONLY from the provided "List of available doctors in Vaya". If no doctors are provided, or if none fit, state that. You MUST always include a clear medical disclaimer.

            User's Symptoms: "{user_symptoms}"

            Here is the LIST OF AVAILABLE DOCTORS in Vaya's database (Format: - Dr. Full Name (ID: DoctorID, Specialties: X, Y)):
            {recommended_doctors_text}

            Your response MUST be a JSON object with the following keys. Adhere strictly to this format:
            "is_medical_query" (boolean)
            "understanding" (string)
            "specialties" (list of strings, derived from original input/context)
            "recommended_doctors" (list of objects, where each object has "name" and "id" keys. ONLY from the provided list above. If no doctors are recommended, this list should be empty []):
                Example: {{"name": "Dr. Smith", "id": 123}}
            "disclaimer" (string)

            Example medical response JSON:
            ```json
            {{
                "is_medical_query": true,
                "understanding": "The symptoms you described often indicate a common cold or flu, which are viral infections affecting the respiratory system.",
                "specialties": ["General Physician", "Pulmonologist"],
                "recommended_doctors": [{{"name": "Dr. Ankush Kumar", "id": 15}}, {{"name": "Dr. Rohan Tiwari", "id": 21}}],
                "disclaimer": "This information is for general knowledge and is not a substitute for professional medical advice. Always consult a qualified healthcare provider for any health concerns."
            }}
            ```
            Example non-medical response JSON:
            ```json
            {{
                "is_medical_query": false,
                "message": "As a healthcare AI, I specialize in medical queries. How can I assist you with your health today?"
            }}
            ```
            """

            messages_for_final_llm = []
            messages_for_final_llm.append({"role": "system", "content": final_ai_prompt_template})
            for msg in recent_messages:
                role = "user" if msg.sender == request.user else "assistant"
                messages_for_final_llm.append({"role": role, "content": msg.content})
            messages_for_final_llm.append({"role": "user", "content": user_symptoms})

            try:
                final_chat_completion = client.chat.completions.create(
                    messages=messages_for_final_llm,
                    model="llama3-8b-8192",
                    response_format={"type": "json_object"},
                )
                raw_final_response_content = final_chat_completion.choices[0].message.content
                
                parsed_final_response = json.loads(raw_final_response_content)

                is_medical_query = parsed_final_response.get("is_medical_query", False)

                if is_medical_query:
                    ai_understanding = parsed_final_response.get("understanding", "Could not get understanding.")
                    final_suggested_specialties = parsed_final_response.get("specialties", [])
                    # recommended_doctors_by_ai is now a list of objects {"name": "...", "id": ...}
                    recommended_doctors_by_ai = parsed_final_response.get("recommended_doctors", [])
                    disclaimer = parsed_final_response.get("disclaimer", "This information is for general knowledge and is not a substitute for professional medical advice. Always consult a qualified healthcare provider for any health concerns.")

                    # Build the display string for doctors with HTML links
                    doctors_display_with_links_html = []
                    for doctor_rec in recommended_doctors_by_ai:
                        doctor_name = doctor_rec.get("name")
                        doctor_id = doctor_rec.get("id")
                        if doctor_name and doctor_id:
                            try:
                                # Generate the URL for the doctor's detail page
                                doctor_url = reverse('doctor_detail', args=[doctor_id]) # 'doctor_detail' is the URL name
                                doctors_display_with_links_html.append(f'<a href="{doctor_url}">{doctor_name}</a>')
                            except Exception as url_e:
                                # Fallback if URL generation fails
                                doctors_display_with_links_html.append(f"{doctor_name} (Link Error)")
                        else:
                            doctors_display_with_links_html.append(doctor_name if doctor_name else "Unknown Doctor (No ID)")
                    
                    # Combine all parts for final display to the user
                    final_display_response_to_user = f"{ai_understanding}\n\n"
                    if final_suggested_specialties:
                        final_display_response_to_user += f"Suggested Medical Specialties: {', '.join(final_suggested_specialties)}\n\n"
                    
                    if doctors_display_with_links_html: # Use the HTML list for display
                        final_display_response_to_user += "Based on your symptoms, Vaya recommends these approved doctors:\n"
                        final_display_response_to_user += "\n".join(doctors_display_with_links_html) + "\n\n"
                    elif "No approved doctors found in our database for these specialties." in recommended_doctors_text:
                        final_display_response_to_user += "We couldn't find approved doctors for these specialties in our current database. Please try another query.\n\n"
                    else:
                        final_display_response_to_user += "While we found some relevant specialties, the AI didn't recommend specific doctors. You can browse our doctor list manually.\n\n"

                    final_display_response_to_user += disclaimer
                    
                    # Mark the entire string as safe HTML so Django doesn't escape the <a> tags
                    ai_response_content_for_db = final_display_response_to_user # Store the raw HTML string
                    ai_response = mark_safe(ai_response_content_for_db) # Mark safe for template rendering

                    # Save the AI's final, combined response to the database (saving the raw HTML string)
                    ai_message_obj = Message.objects.create(
                        sender=ai_assistant_user,
                        content=ai_response_content_for_db, # Save the string content (with HTML)
                        appointment=None,
                        ai_chat_for_user=request.user
                    )

                else:
                    ai_response = parsed_final_response.get("message", "I am an AI healthcare assistant and can only help with medical queries.")
                    ai_message_obj = Message.objects.create(
                        sender=ai_assistant_user,
                        content=ai_response,
                        appointment=None,
                        ai_chat_for_user=request.user
                    )

            except json.JSONDecodeError as jde:
                ai_response = "I apologize, but I received an unexpected (non-JSON) response from the AI in the final step. Please try rephrasing your query."
                print(f"ERROR: Final JSON Decode Error: {jde}. Raw content: {raw_final_response_content if 'raw_final_response_content' in locals() else 'N/A'}")
            except Exception as e:
                ai_response = f"An error occurred in the final AI response generation: {e}"
                print(f"CRITICAL ERROR in final AI generation: {e}")
        else:
            ai_response = "Please enter your symptoms."

    else: # Initial GET request
        pass

    # 5. Retrieve the full AI chat history for display in the template
    conversation_history = Message.objects.filter(
        ai_chat_for_user=request.user,
        appointment__isnull=True
    ).order_by('timestamp')

    context = {
        'form': form,
        'ai_response': ai_response, # This will be the latest AI response for immediate display (already mark_safe'd)
        'is_medical_query': is_medical_query,
        'conversation_history': conversation_history, # This list contains Message objects
    }
    return render(request, 'ai_assistant/symptom_checker.html', context)