🔗 TriggerTrace

Link Every Asthma Attack to the Air Around It

Theme: SDG 3 – Good Health and Well-being
Version: 0.1 (Hackathon Prototype)

🔗 Overview

TriggerTrace is an installable Progressive Web App (PWA) designed to help people with asthma identify possible environmental triggers. It connects recorded asthma attacks with historical air quality and weather conditions such as PM2.5, humidity, temperature, and rainfall.

By analysing attack days against symptom-free days, TriggerTrace identifies possible environmental patterns and generates a one-page PDF summary that users can share with their doctors.

🔗 Problem Statement

People with asthma are often advised to avoid their triggers, but identifying personal triggers is difficult. Environmental conditions vary from person to person, while existing weather applications and traditional symptom diaries do not connect environmental data with individual asthma records. This makes it harder for patients and doctors to understand recurring patterns.

🔗 Proposed Solution

TriggerTrace provides a simple way to record asthma attacks and automatically associate them with environmental information. Over time, it analyses the collected data to highlight possible patterns and provides organised reports for better doctor consultations.

🔗 Key Features

- One-Tap Attack Logging: Record an asthma attack in approximately two seconds.
- Environmental Data Tracking: Automatically collect PM2.5, humidity, temperature, and rainfall.
- Follow-up Recording: Track attack severity and inhaler usage.
- Evening Check-ins: Record whether symptoms occurred during the day.
- Pattern Detection: Compare attack days with confirmed symptom-free days.
- Confidence Indicators: Display possible patterns or indicate when more data is needed.
- Doctor-Ready PDF: Generate a one-page summary of attack history and observed patterns.
- Caregiver Mode: Allow caregivers to record attacks for children and older adults.
- Offline Support: Cache environmental data and support offline logging.

🔗 Technology Stack

- Frontend: Progressive Web App (PWA)
- Backend: Python
- Database: For storing attack records and symptom check-ins
- Weather API: Open-Meteo
- Air Quality API: Open-Meteo Air Quality / OpenAQ
- Analysis: Attack-rate ratios and statistical comparison
- Reports: PDF generation and data visualisation

🔗 How It Works

1. User records an asthma attack using the Attack Now button.
2. The application stores the timestamp and district.
3. Environmental conditions are attached to the recorded event.
4. Users provide follow-up details and daily symptom check-ins.
5. The system compares attack days with symptom-free days.
6. Possible patterns are displayed with confidence notes.
7. A doctor-ready PDF report can be generated.

🔗 Privacy & Safety

- Uses synthetic data for the hackathon prototype.
- Stores only district-level location information.
- Protects data transmission using HTTPS.
- Does not provide medical diagnosis or treatment recommendations.
- Users must follow their prescribed asthma action plan. Emergencies should always be addressed before logging.

🔗 Future Scope

- Smart inhaler sensor integration.
- Smartwatch-based attack detection.
- Voice-based logging.
- Tamil and other regional language support.
- Telegram and WhatsApp integration.
- Clinic-based pilot testing.
- Extension to migraines, allergies, and eczema.

🔗 Expected Impact

TriggerTrace aims to improve asthma awareness, help individuals understand their personal environmental patterns, and provide doctors with more organised health histories.

Built with the vision of making healthcare awareness smarter, simpler, and more accessible.

---