Solar Energy Monitoring Dashboard:-

Overview:

This project is a web-based dashboard designed to monitor and analyze the performance of solar panel test beds in real-time. It provides interactive visualizations, performance metrics, and historical data analysis to help users track energy generation, efficiency, and reliability of different solar panel configurations.

Built with Python Flask for the backend and HTML/CSS/JavaScript with Chart.js for the frontend, this dashboard offers:

Real-time & historical data visualization

Performance metrics (PLF, DRR, Energy Output)

Panel specifications & photo gallery

User authentication & secure access

Features:-

1. Interactive Data Visualization
Multiple timeframes: Hourly, Daily, Monthly, Yearly, and Custom date ranges

Dynamic charts (Line & Bar graphs) using Chart.js

Performance comparison across different solar panels

2. Performance Metrics
Plant Load Factor (PLF%) – Measures efficiency relative to rated capacity

Daily Recovery Rate (DRR%) – Tracks operational days vs. total days

Energy Output (kWh) – Total energy generated

ALB (Acceptable Loss Boundary), GHI, DNI, DHI – Additional solar metrics

3. Solar Panel Information
Technical specifications (Model Capacity, Inverter Serial No., Energy Meter details)

Photo gallery of all test bed installations

4. User-Friendly Interface
Responsive design (works on desktop & tablet)

Interactive modals for detailed data tables

Draggable & resizable pop-ups for better UX

5. Secure Authentication
Login/logout system with session management

Password hashing for security

Technical Stack:-

Backend (Python Flask):

Flask – Web framework for API endpoints

Pandas – Data processing & Excel file handling

ThreadPoolExecutor – Concurrent data loading

Werkzeug Security – Password hashing

Frontend (HTML/CSS/JavaScript):

Chart.js – Interactive graphs

Responsive CSS – Adapts to different screen sizes

Dynamic DOM Manipulation – Real-time updates

Data Storage:

Excel files (xlsx) for hourly & daily energy readings

Structured data processing with Pandas

Installation & Setup
Prerequisites

Python 3.8+

Flask, Pandas, OpenPyXL (pip install flask pandas openpyxl)
