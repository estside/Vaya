# Vaya: Your Local Healthcare Connection

## Overview

**Vaya** is a web application designed to simplify healthcare access for patients in smaller towns like Motihari, Bihar, by connecting them with trusted private clinics and doctors. The platform offers digital appointment booking, medical record management, and an AI-powered symptom checker for smart doctor recommendations.

---

## Key Features

* **Clinic/Doctor Registration:** A detailed web form allows doctors to register their clinic and create a user account. New doctor profiles are set to "pending approval" and require an administrator to activate them before they appear on the public list.
* **Enhanced Admin Panel:** Vaya administrators can manage doctors, specialties, appointments, and reports through a customized Django Admin interface. This includes visual approval status indicators, color-coded specialty displays, and bulk actions for approving or rejecting multiple doctors at once.
* **Patient Dashboard:** A personalized dashboard for patients to view their profile, appointments, and reports.
* **Doctor Discovery:** A public page where patients can search for and filter approved doctors by name and specialty.
* **AI-Powered Symptom Checker:** Users can input symptoms and receive a general understanding of their symptoms, suggested medical specialties, and recommended approved doctors from the database.
* **Appointment Booking System:** Patients can view a doctor's available time slots and book an appointment. Doctors can confirm or cancel these requests. Doctors can also book follow-up appointments for their patients.
* **Real-time Chat:** A secure messaging system for patients and doctors, linked to specific appointments. It uses WebSockets for real-time communication, and all messages are saved to the database to ensure chat history is persistent.
* **Digital Report Management:** Allows patients to upload their own medical reports and doctors to upload reports for their patients. These reports can be downloaded from the respective dashboards.
* **Slot Management:** Doctors can manually add, generate, and toggle the availability of time slots.

---

## Project Structure

healthcare_app_motihari/
├── ai_assistant/      # AI symptom checker and doctor recommendation
├── chat/              # Real-time chat functionality using Django Channels
├── config/            # Main project settings, URLs, and root-level views
├── doctors/           # Doctor, specialty, appointment, and report management
├── users/             # Custom user model and authentication
├── templates/         # HTML templates for all apps
├── media/             # Uploaded patient reports
├── db.sqlite3         # SQLite database (default for development)
├── manage.py
└── .env               # Environment variables (API keys, etc.)


---

## Setup Instructions

### Prerequisites

* Python 3.9+
* pip
* Git

### Installation

1.  **Clone the repository:**
    ```sh
    git clone [https://github.com/estside/Vaya](https://github.com/estside/Vaya)
    cd healthcare_app_motihari
    ```

2.  **Create and activate a virtual environment:**
    ```sh
    python -m venv venv
    # On Windows: venv\Scripts\activate
    # On macOS/Linux: source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```sh
    pip install Django psycopg2-binary channels channels-redis groq httpx
    ```

4.  **Set up environment variables:**
    * Create a `.env` file in the project root.
    * Add your Groq API key, as it is required for the AI Assistant:
        ```
        GROQ_API_KEY=your_groq_api_key_here
        ```

5.  **Apply database migrations:**
    ```sh
    python manage.py makemigrations doctors
    python manage.py migrate
    ```
6.  **Create a superuser for admin access:**
    ```sh
    python manage.py createsuperuser
    ```

7.  **Run the development server (with Daphne for WebSockets):**
    ```sh
    daphne config.asgi:application
    ```

---

## Usage

* Visit `http://localhost:8000/` to access the landing page.
* Register as a patient or a doctor.
* Admins must approve new doctor registrations via the admin panel at `/admin/`.
* Patients can use the AI Symptom Checker at `/ai/symptom-checker/`.
* All chat history, including with the AI Assistant, is saved.

---

## Admin Features

* Visual approval status for doctors (✓ Approved / ✗ Pending Approval).
* Color-coded specialty display.
* Bulk approval/rejection actions.
* Organized doctor profile sections.
* Registration date tracking.

---

## License

This project is for demonstration and educational purposes.

---

## Contributing

Pull requests and suggestions are welcome!

---

## Contact

For questions or support, please contact the project maintainer.

**Portfolio:** [https://saurav-portfolio-mandi.vercel.app](https://saurav-portfolio-mandi.vercel.app)