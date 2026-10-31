TRIGGER TRACE 

Link every asthma attack to the air around it .

Theme: SDG 3, Good Health and Well-being

Version: 1.0 (hackathon prototype)

OVERVIEW :

TriggerTrace is an installable Progressive Web App (PWA) that helps people
with asthma identify possible environmental triggers. It connects recorded
asthma attacks with historical air quality and weather conditions (PM2.5,
humidity, temperature and rainfall).
By comparing attack days with confirmed symptom-free days, TriggerTrace
highlights possible personal patterns and generates a one-page PDF
summary that users can share with their doctor.

PROBLEM STATEMENT:

People with asthma are often advised to avoid their triggers, but identifying
personal triggers is difficult. Triggers differ from person to person, while
weather and air quality apps do not connect to an individual's attack history,
and traditional symptom diaries do not capture the environment. Patients
usually reach consultations relying on memory, which makes recurring
patterns hard for patients and doctors to see.
Proposed solution
TriggerTrace makes recording an attack take about two seconds and
automatically attaches the environmental conditions for that time and place.
Over time, it analyses the collected data to highlight possible patterns, states
how confident those patterns are, and produces an organised report for better
doctor consultations.

KEY FEATURES : 

• One-tap attack logging: An "Attack now" button inside the app records an
attack in about two seconds. TriggerTrace | SDG 3: Good Health and Well-being Page 2
• Environmental data tracking: PM2.5, humidity, temperature and rainfall
are attached automatically.
• Follow-up recording: Severity and inhaler use are asked about 30 to 60
minutes later.
• Back-dated entries: Attacks can be added afterwards and are tagged
"logged later".
• Evening check-ins: A one-tap "Any symptoms today?" builds the
symptom-free baseline.
• Pattern detection: Regularized logistic regression, with a simple
attack-rate comparison as a fallback.
• Confidence indicators: Shows a possible pattern with an uncertainty
range, or says more data is needed.
• Doctor-ready PDF: A one-page summary of attack history and observed
patterns.
• Caregiver mode: Caregivers can log attacks for children and older adults.
• Offline support: Environmental data is cached, and logging works offline
and syncs later.

Technology stack

Layer            Technology
Frontend         React (Vite), installable PWA
Backend          Python (Flask)
Database         SQLite
Weather data     Open-Meteo
Air quality data Open-Meteo Air Quality            
Analysis         pandas, scikit-learn     (L2-regularized logistic regression),
bootstrapped intervals
Reports ReportLab (PDF), Recharts or Chart.js (charts)

HOW IT WORKS : 


1 The user taps Attack now. The app stores the timestamp and district.
2 The backend attaches historical air quality and weather data for that time
and place.
3 The user adds follow-up details (severity, inhaler use) and completes
evening check-ins.
4 A daily table is built with one row per day: attack yes or no, plus same-day
and previous 1 to 2 day values of PM2.5, humidity, temperature and
rainfall.
5 Only days with a completed check-in count as symptom-free. Days with no
check-in are excluded.
6 A regularized logistic regression estimates the odds ratio for each factor,
with ranges from bootstrapping. A simple attack-rate comparison runs
alongside it as a sanity check.
7 The app shows possible patterns with confidence notes. If the data is thin
or the range includes "no effect", it says so.
8 A doctor-ready PDF can be generated.

ANALYSIS APPROACH

• Target: Attack that day (yes or no).
• Features: PM2.5, humidity, temperature and rainfall, same-day and
lagged. Few features relative to the number of logged attacks.
• Model: L2-regularized logistic regression on standardized features.
• Output: Odds ratios with ranges, described as "possible patterns", never
as causes.
• Minimum data: "Not enough data" until enough attacks and check-in days
exist (proposed: 10 attacks and 30 check-in days, to be tuned).

PRIVACY AND SAFETY : 

• The prototype uses synthetic data only. No real patient data is used.
• Only district-level location is stored.
• Data is protected in transit with HTTPS.
• Users can delete their data.
• TriggerTrace does not provide diagnosis or treatment
recommendations.
• Emergencies come first: during a severe attack, follow your prescribed
asthma action plan or call emergency services, and log afterwards.

REPOSITORY STRUCTURE : 

triggertrace/
|--■■ README.md
|--■■ docs/ # PRD, architecture diagram
|--■■ backend/ # Flask API, database, analysis, PDF
|--■■ data/ # Synthetic data generator, sample CSV
`--■■ frontend/ # React PWA

Getting started

# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py

# Frontend (second terminal)

cd frontend
npm install
npm run dev
Copy .env.example to .env and fill in any settings before running.

LIMITATIONS :

• A small number of logged attacks cannot prove a trigger. Results are
possible patterns, not causes.
• Air quality data may be coarse for some districts.
• Pollen is not included, because reliable data for India is limited.

FUTURE SCOPE :

• Home-screen widget and lock-screen shortcut for faster logging TriggerTrace | SDG 3: Good Health and Well-being Page 5
• Smart inhaler sensor integration
• Smartwatch-based attack detection
• Voice-based logging
• Tamil and other regional language support
• Telegram and WhatsApp integration
• Clinic-based pilot testing
• Extension to migraines, allergies and eczema

EXPECTED IMPACT : 

TriggerTrace aims to improve asthma awareness, help individuals understand
their personal environmental patterns, and give doctors more organised
health histories.
Built with the vision of making healthcare awareness smarter, simpler and
more accessible.