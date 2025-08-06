# Vaya: Your Local Healthcare Connection

## Overview

**Vaya** is a web application designed to simplify healthcare access for patients in smaller towns like Motihari, Bihar, by connecting them with trusted private clinics and doctors. The platform offers digital appointment booking, medical record management, and an AI-powered symptom checker for smart doctor recommendations.

---

## Key Features

- **Clinic/Doctor Registration:** Doctors and clinics can register, creating a profile pending admin approval.
- **Enhanced Admin Panel:** Admins can manage doctors, specialties, appointments, and reports with visual approval indicators and bulk actions.
- **Patient Dashboard:** Patients can view their profile, appointments, and reports.
- **Doctor Discovery:** Patients can search and filter approved doctors by name and specialty.
- **AI-Powered Symptom Checker:** Users can input symptoms and receive:
  - General understanding of symptoms
  - Suggested medical specialties
  - Recommended approved doctors from the database
  - Medical disclaimers
- **Chat History:** All AI interactions are saved for each user.

---

## Project Structure

```
healthcare_app_motihari/
├── ai_assistant/      # AI symptom checker and doctor recommendation
├── chat/              # Chat models and consumers
├── config/            # Django project settings and root URLs
├── doctors/           # Doctor, specialty, appointment, and report management
├── users/             # Custom user model and authentication
├── templates/         # HTML templates
├── media/             # Uploaded patient reports
├── db.sqlite3         # SQLite database (default)
├── manage.py
└── .env               # Environment variables (API keys, etc.)
```

---

## Setup Instructions

### Prerequisites

- Python 3.9+
- pip
- Git

### Installation

1. **Clone the repository:**
    ```sh
    git clone <your-repo-url>
    cd healthcare_app_motihari
    ```

2. **Create and activate a virtual environment:**
    ```sh
    python -m venv venv
    # On Windows: venv\Scripts\activate
    # On macOS/Linux: source venv/bin/activate
    ```

3. **Install dependencies:**
    ```sh
    pip install Django psycopg2-binary channels channels-redis groq httpx
    ```

4. **Set up environment variables:**
    - Create a `.env` file in the project root.
    - Add your Groq API key:
      ```
      GROQ_API_KEY=your_groq_api_key_here
      ```

5. **Apply database migrations:**
    ```sh
    python manage.py migrate
    ```

6. **Create a superuser for admin access:**
    ```sh
    python manage.py createsuperuser
    ```

7. **Run the development server:**
    ```sh
    python manage.py runserver
    ```

---

## Usage

- Visit `http://localhost:8000/` to access the landing page.
- Register as a doctor or patient.
- Admins can approve doctors via the admin panel at `/admin/`.
- Patients can use the AI Symptom Checker at `/ai/symptom-checker/`.
- All chat history is saved and viewable per user.

---

## AI Assistant

- Integrates with the Groq API (Llama3 model).
- Prompts the AI for structured JSON responses.
- Recommends doctors based on specialties extracted from user symptoms.
- Handles non-medical queries gracefully.
- **Note:** The AI Assistant requires a user named `AI_Assistant` in the database for chat attribution.

---

## Admin Features

- Visual approval status for doctors (✓ Approved / ✗ Pending)
- Color-coded specialty display
- Bulk approval/rejection actions
- Organized doctor profile sections
- Registration date tracking

---

## License

This project is for demonstration and educational purposes.

---

## Contributing

Pull requests and suggestions are welcome!

---

## Contact

For questions or support, please contact the project maintainer.