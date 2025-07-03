from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import threading
import time
from werkzeug.security import check_password_hash
app = Flask(__name__)
app.secret_key = "Harshkumar"  
hourly_data_path = r"W:\MDMS\PLF Calculator using python\Solar Flask\Solar Hourly data of all panels.xlsx"
daily_data_path = r"W:\MDMS\Test Bed\Energy Meter data\2025\Output energy comparison-Solar Test Bed_Updated_V.1.0.1 (Sep 2022 to June 2025).xlsx"
hourly_data = None
daily_data = None
hourly_data_ready = False  
SOLAR_PANELS_PLF = {
    "S-13-Mono": 2.4, "S-13-Bi": 2.4, "E-W-10-Mono": 2.4, "E-W-5-Bi": 2.4,
    "W-90-Bi": 1.2, "E-W-90-Mono": 4.8, "E-90-Bi": 1.2, "S-5-Bi-AgriPV": 5, "N-5-Bi-AgriPV": 5
}
thread_pool = ThreadPoolExecutor(max_workers=4)
def preprocess_daily_data():
    global daily_data
    print("Preprocessing daily_data...")
    start_time = time.time()
    daily_data = pd.read_excel(daily_data_path, sheet_name='Replica of Energy Readings')
    daily_data['Date'] = pd.to_datetime(daily_data['Date'], format='%d-%m-%Y')
    print(f"daily_data preprocessing completed in {time.time() - start_time:.2f} seconds.")
def preprocess_hourly_data():
    global hourly_data, hourly_data_ready
    print("Starting background preprocessing of hourly_data...")
    start_time = time.time()
    hourly_data = pd.read_excel(hourly_data_path, sheet_name=None)
    for panel in hourly_data:
        hourly_data[panel]['Load Time'] = pd.to_datetime(hourly_data[panel]['Load Time'])
    hourly_data_ready = True
    print(f"hourly_data preprocessing completed in {time.time() - start_time:.2f} seconds.")
hourly_data_thread = threading.Thread(target=preprocess_hourly_data)
hourly_data_thread.daemon = True  
hourly_data_thread.start()
preprocess_daily_data()
def verify_login(username, password):
    try:
        with open("credential.txt", "r") as f:
            content = f.read().strip()
            if not content:
                return False  
            stored_hashed_username, stored_hashed_password = content.split(",")  
        if not check_password_hash(stored_hashed_username, username):
            return False  
        return check_password_hash(stored_hashed_password, password)
    except ValueError:
        print("Error: credential.txt is not formatted correctly!")
        return False  
    except FileNotFoundError:
        print("Error: credential.txt not found!")
        return False  
@app.route("/", methods=["GET", "POST"])
def login():
    """Render login page and handle authentication."""
    if request.method == "POST":
        username = request.form.get("login_username")  
        password = request.form.get("login_password")  
        if verify_login(username, password):
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        else:
            return render_template("index.html", error="Invalid Username or Password")
    return render_template("index.html", logged_in=session.get("logged_in", False))
@app.route("/dashboard")
def dashboard():
    """Render dashboard only if user is logged in."""
    if not session.get("logged_in"):
        return redirect(url_for("login"))  
    return render_template("dashboard.html")
@app.route("/logout")
def logout():
    """Logout user and clear session."""
    session.pop("logged_in", None)
    return redirect(url_for("login"))
def calculate_panel_metrics(panel, data, total_hours, start_date, end_date):
    valid_data = data[data[panel].notna() & (data[panel] > 0)]
    num_days = len(valid_data)  
    sum_kwh = valid_data[panel].sum()
    rated_capacity_plf = SOLAR_PANELS_PLF.get(panel, 0)
    plf = float((sum_kwh / (rated_capacity_plf * total_hours)) * 100) if rated_capacity_plf > 0 and total_hours > 0 else 0.0
    total_days = (end_date - start_date).days + 1  
    drr = (num_days / total_days) * 100 if total_days > 0 else 0.0
    return {
        'plf': plf,
        'days': num_days,  
        'drr': drr,  
        'sum' : sum_kwh,
        'rated_capacity_plf': rated_capacity_plf,
    }
@app.route('/calculate_metrics', methods=['POST'])
def calculate_metrics():
    try:
        payload = request.json
        if not payload:
            return jsonify({'error': 'No payload provided'}), 400
        panels = payload.get('panels', [])
        if not panels:
            return jsonify({'error': 'No panels selected'}), 400
        try:
            start_date = datetime.strptime(payload['start_date'], '%d-%m-%Y')
            end_date = datetime.strptime(payload['end_date'], '%d-%m-%Y')
        except (KeyError, ValueError) as e:
            return jsonify({'error': f'Invalid date format: {e}'}), 400
        data = daily_data[(daily_data['Date'] >= start_date) & (daily_data['Date'] <= end_date)]
        if data.empty:
            return jsonify({'error': 'No data available for the selected date range'}), 404
        total_hours = len(data) * 24  
        futures = []
        for panel in panels:
            if panel not in data.columns:
                return jsonify({'error': f'Panel {panel} not found in daily data'}), 404
            futures.append(thread_pool.submit(calculate_panel_metrics, panel, data, total_hours, start_date, end_date))
        results = {}
        for panel, future in zip(panels, futures):
            results[panel] = future.result()
        return jsonify(results)
    except Exception as e:
        print(f"Error in calculate_metrics: {e}")
        return jsonify({'error': 'An internal server error occurred'}), 500
@app.route('/get_graph_data', methods=['POST'])
def get_graph_data():
    payload = request.json
    panels = payload.get('panels', [])
    timeframe = payload.get('timeframe', 'day')
    date = payload.get('date')
    start_date = payload.get('start_date')
    end_date = payload.get('end_date')
    if not panels:
        return jsonify({'error': 'No panels selected'}), 400
    try:
        if timeframe == 'day' and date:
            date = datetime.strptime(date, '%d-%m-%Y')
        elif timeframe == 'month' and date:
            date = datetime.strptime(date, '%d-%m-%Y')
        elif timeframe == 'year' and date:
            date = datetime.strptime(date, '%d-%m-%Y')
        elif timeframe in ['custom']:
            if not start_date or not end_date:
                return jsonify({'error': 'start_date and end_date are required for this timeframe'}), 400
            start_date = datetime.strptime(start_date, '%d-%m-%Y')
            end_date = datetime.strptime(end_date, '%d-%m-%Y')
    except ValueError as e:
        return jsonify({'error': f'Invalid date format: {e}'}), 400
    if timeframe == 'day':
        if not date:
            return jsonify({'error': 'date is required for the "day" timeframe'}), 400
        datasets = []
        for panel in panels:
            if panel not in hourly_data:
                return jsonify({'error': f'Panel {panel} not found in hourly data'}), 404
            data = hourly_data[panel]
            if 'Load Time' not in data.columns or 'kWh(I)' not in data.columns:
                return jsonify({'error': f'Required columns not found for panel {panel}'}), 404
            data = data[data['Load Time'].dt.date == date.date()]
            if data.empty:
                return jsonify({'error': f'No data available for {panel} on the selected date'}), 404
            labels = data['Load Time'].dt.strftime('%H:%M').tolist()
            datasets.append({'label': panel, 'data': data['kWh(I)'].fillna(0).tolist()})  
    elif timeframe == 'month':
        if not date:
            return jsonify({'error': 'date is required for the "month" timeframe'}), 400
        data = daily_data[(daily_data['Date'].dt.year == date.year) & (daily_data['Date'].dt.month == date.month)]
        if data.empty:
            return jsonify({'error': 'No data available for the selected month'}), 404
        labels = data['Date'].dt.strftime('%d-%b-%Y').tolist()
        datasets = [{'label': panel, 'data': data[panel].fillna(0).tolist()} for panel in panels]  
    elif timeframe == 'year':
        if not date:
            return jsonify({'error': 'date is required for the "year" timeframe'}), 400
        data = daily_data[daily_data['Date'].dt.year == date.year]
        if data.empty:
            return jsonify({'error': 'No data available for the selected year'}), 404
        labels = data['Date'].dt.strftime('%b-%Y').unique().tolist()
        datasets = [{'label': panel, 'data': data.groupby(data['Date'].dt.month)[panel].sum().fillna(0).tolist()} for panel in panels]  
    elif timeframe == 'custom':
        data = daily_data[(daily_data['Date'] >= start_date) & (daily_data['Date'] <= end_date)]
        if data.empty:
            return jsonify({'error': 'No data available for the selected date range'}), 404
        if (end_date - start_date).days >= 10:
            labels = data['Date'].dt.strftime('%b-%Y').unique().tolist()
            datasets = [{'label': panel, 'data': data.groupby(data['Date'].dt.to_period('M'))[panel].sum().fillna(0).tolist()} for panel in panels]  
        else:
            labels = data['Date'].dt.strftime('%d-%b-%Y').tolist()
            datasets = [{'label': panel, 'data': data[panel].fillna(0).tolist()} for panel in panels]  
    elif timeframe == 'total':
        data = daily_data
        labels = data['Date'].dt.year.unique().tolist()
        datasets = [{'label': panel, 'data': data.groupby(data['Date'].dt.year)[panel].sum().fillna(0).tolist()} for panel in panels]  
    return jsonify({
        'labels': labels,
        'datasets': datasets,
    })
@app.route('/get_performance_data', methods=['POST'])
def get_performance_data():
    payload = request.json
    panels = payload.get('panels', [])
    if not panels:
        return jsonify({'error': 'No panels selected'}), 400
    try:
        performance_data = {}
        for panel in panels:
            if panel not in daily_data.columns:
                return jsonify({'error': f'Panel {panel} not found in daily data'}), 404
            panel_data = daily_data[['Date', panel]].copy()
            panel_data['Year'] = panel_data['Date'].dt.year
            panel_data['Month'] = panel_data['Date'].dt.month
            grouped_data = panel_data.groupby(['Year', 'Month'])[panel].sum().unstack(level=0)
            performance_data[panel] = {
                'years': {},
                'months': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            }
            for year in grouped_data.columns:
                year_data = []
                for month in range(1, 13):
                    if month in grouped_data.index:
                        year_data.append(float(grouped_data.loc[month, year]) if not pd.isna(grouped_data.loc[month, year]) else 0)
                    else:
                        year_data.append(0)
                performance_data[panel]['years'][str(year)] = year_data
        return jsonify(performance_data)
    except Exception as e:
        print(f"Error in get_performance_data: {e}")
        return jsonify({'error': 'An internal server error occurred'}), 500
@app.route('/get_drr_data', methods=['POST'])
def get_drr_data():
    payload = request.json
    panels = payload.get('panels', [])
    if not panels:
        return jsonify({'error': 'No panels selected'}), 400
    drr_data = {}
    for panel in panels:
        if panel not in daily_data.columns:
            return jsonify({'error': f'Panel {panel} not found in daily data'}), 404
        panel_data = daily_data[['Date', panel]]  
        panel_data['Year'] = panel_data['Date'].dt.year
        panel_data['Month'] = panel_data['Date'].dt.month
        drr_table = {
            'months': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
            'years': {},
            'overall': {}
        }
        years = panel_data['Year'].unique()
        for year in years:
            drr_table['years'][int(year)] = {}  
            yearly_valid_days = 0
            yearly_total_days = 0
            for month in range(1, 13):
                month_data = panel_data[(panel_data['Year'] == year) & (panel_data['Month'] == month)]
                total_days = len(month_data)  
                valid_days = len(month_data[month_data[panel] > 0])  
                if total_days > 0:
                    drr = (valid_days / total_days) * 100
                else:
                    drr = 0  
                drr_table['years'][int(year)][month] = drr
                yearly_valid_days += valid_days
                yearly_total_days += total_days
            if yearly_total_days > 0:
                overall_drr = (yearly_valid_days / yearly_total_days) * 100
            else:
                overall_drr = 0
            drr_table['overall'][int(year)] = overall_drr
        drr_data[panel] = drr_table
    return jsonify(drr_data)
@app.route('/get_panel_info', methods=['POST'])
def get_panel_info():
    panel_info = [
        {"Panel Name": "E-W-10-Mono", "Model Capacity": "2.4 kWp", "Energy Meter Serial No.": "81320513","Rate of Module(Wp)":"400W" ,"Inverter Serial No.": "110E1120C040002-1KW"},
        {"Panel Name": "S-13-Bi", "Model Capacity": "2.4 kWp", "Energy Meter Serial No.": "A1159564", "Rate of Module(Wp)":"400W" ,"Inverter Serial No.": "110331221070185-2KW"},
        {"Panel Name": "S-13-Mono", "Model Capacity": "2.4 kWp", "Energy Meter Serial No.": "A1159561","Rate of Module(Wp)":"400W" , "Inverter Serial No.": "110E3120C040216-2KW"},
        {"Panel Name": "EW-90- Mono", "Model Capacity": "4.8KWp", "Energy Meter Serial No.": "99863099","Rate of Module(Wp)":"400W" , "Inverter Serial No.": "110AA1213100606-4KW"},
        {"Panel Name": "E-90-Bifacial", "Model Capacity": "1.2KWp", "Energy Meter Serial No.": "A1159899","Rate of Module(Wp)":"400W" , "Inverter Serial No.": "110E3120C040224-2KW"},
        {"Panel Name": "W-90-Bifacial", "Model Capacity": "1.2KWp", "Energy Meter Serial No.": "A1159568","Rate of Module(Wp)":"400W" , "Inverter Serial No.": "110331221080234-2KW"},
        {"Panel Name": "EW-5-Bifacial", "Model Capacity": "2.4KWp", "Energy Meter Serial No.": "A1159572","Rate of Module(Wp)":"400W" , "Inverter Serial No.": "110E1120C040047-1KW,110E1120C040018-1KW"},
        {"Panel Name": "Agri PV Model-S", "Model Capacity": "5KWp", "Energy Meter Serial No.": "94016029","Rate of Module(Wp)":"540W" , "Inverter Serial No.": "1801150236270053-5KW"},
        {"Panel Name": "Agri PV Model-N", "Model Capacity": "5KWp", "Energy Meter Serial No.": "994015256", "Rate of Module(Wp)":"540W" ,"Inverter Serial No.": "1801150236270025-5KW"},
    ]
    return jsonify(panel_info)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)