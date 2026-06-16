from flask import Flask, render_template,request,redirect,url_for,flash
import requests
from datetime import datetime,date
import sqlite3
import os
from datetime import datetime
from flask import session

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

API_KEY = "600e30a2596cdb96245f9b61f187beab"

# ---------------- DATABASE ---------------- #
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "weather.db")

print("Database path:", DB_PATH)
def get_db_connection():
    conn = sqlite3.connect("weather.db")
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    conn = get_db_connection()
    conn.execute("""
            CREATE TABLE IF NOT EXISTS weather_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT,
            temperature REAL,
            humidity INTEGER,
            description TEXT,
            date TEXT)""")
    conn.commit()
    conn.close()

create_table()

def create_feedback_table():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            rating INTEGER CHECK(rating >= 1 AND rating <= 5),
            comment TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

create_feedback_table()

# ---------------- WEATHER FUNCTION ---------------- #

def get_weather(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    data = response.json()

    # Safely extract values
    temp = data.get("main", {}).get("temp", 0)
    humidity = data.get("main", {}).get("humidity", 0)
    desc = data.get("weather", [{}])[0].get("description", "N/A")
    wind = data.get("wind", {}).get("speed", 0)
    precip = 0
    if "rain" in data:
        precip = data["rain"].get("1h", 0)

    return {
        "city": data.get("name", city),
        "temp": temp,
        "humidity": humidity,
        "desc": desc,
        "wind": wind,
        "precip": precip
    }
def get_forecast(city):
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(url)

    if response.status_code != 200:
        return None

    data = response.json()
    forecast_days = {}
    today_str = datetime.now().strftime("%Y-%m-%d")

    for item in data["list"]:
        date_str, time_str = item["dt_txt"].split(" ")

        if date_str == today_str:
            continue

        if time_str == "12:00:00" and date_str not in forecast_days:
            day_name = datetime.strptime(date_str,"%Y-%m-%d").strftime("%A")

            forecast_days[date_str] = {
                "date": day_name,
                "temp": item.get("main", {}).get("temp", 0),
                "desc": item.get("weather", [{}])[0].get("description", "N/A")
            }

        if len(forecast_days) == 5:
            break

    return list(forecast_days.values())
        
#--------------home page-----------------#
@app.route('/')
def home_page():
    return render_template("home_page.html")

#---------------weather page--------------#

@app.route("/single", methods=["GET", "POST"])
def single_city():

    user_searched = False
    weather = None
    forecast = []
    hours, temps, winds, precip = [], [], [], []
    comparison = None
    city = None

    lat = request.form.get("lat")
    lon = request.form.get("lon")
    
    rows=[]

    # ---- Auto location ----
    if lat and lon:
        try:
            lat, lon = float(lat), float(lon)
        except ValueError:
            return redirect(url_for("single_city"))

        city = get_city_from_latlon(lat, lon) or "Your Location"

        # Current weather
        try:
            data = requests.get(
                f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
            ).json()
            if data.get("cod") != 200:
                weather = None
            else:
                weather = {
                    "city": data.get("name", city),
                    "temp": data.get("main", {}).get("temp", 0),
                    "humidity": data.get("main", {}).get("humidity", 0),
                    "desc": data.get("weather", [{}])[0].get("description", "N/A"),
                    "wind": data.get("wind", {}).get("speed", 0)
                }
        except Exception:
            weather = None

        # Forecast for graphs
        try:
            fdata = requests.get(
                f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
            ).json()
        except Exception:
            fdata = {}

        # Graph (next 12 points)
        for item in fdata.get("list", [])[:12]:
            hours.append(item.get("dt_txt", "").split(" ")[1][:5])
            temps.append(item.get("main", {}).get("temp", 0))
            winds.append(item.get("wind", {}).get("speed", 0))
            precip.append(item.get("pop", 0) * 100)

        # Forecast approx 10-day
        seen_dates = set()
        for item in fdata.get("list", []):
            dt = item.get("dt_txt", "")
            if dt:
                date_str, time_str = dt.split(" ")
                if time_str == "12:00:00" and date_str not in seen_dates:
                    forecast.append({
                        "date": datetime.strptime(date_str, "%Y-%m-%d").strftime("%A"),
                        "temp": item.get("main", {}).get("temp", 0),
                        "desc": item.get("weather", [{}])[0].get("description", "N/A")
                    })
                    seen_dates.add(date_str)
                if len(forecast) >= 5:
                    break

    # ---- City search ----
    elif request.method == "POST" and request.form.get("city"):
        city = request.form.get("city")
        weather = get_weather(city)
        forecast = get_forecast(city)
        user_searched =True

        # Graph from forecast
        try:
            fdata = requests.get(
                f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
            ).json()
        except Exception:
            fdata = {}

        for item in fdata.get("list", [])[:12]:
            hours.append(item.get("dt_txt", "").split(" ")[1][:5])
            temps.append(item.get("main", {}).get("temp", 0))
            winds.append(item.get("wind", {}).get("speed", 0))
            precip.append(item.get("pop", 0) * 100)

    # ---- Default city ----
    if not city:
        city = "Mangalore"
        weather = get_weather(city)
        forecast = get_forecast(city)

        user_searched=False
        fdata = requests.get(
            f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
        ).json()
        for item in fdata.get("list", [])[:12]:
            hours.append(item.get("dt_txt", "").split(" ")[1][:5])
            temps.append(item.get("main", {}).get("temp", 0))
            winds.append(item.get("wind", {}).get("speed", 0))
            precip.append(item.get("pop", 0) * 100)

    # ---- Save to DB ONLY for user search ----
        if request.method == "POST" and request.form.get("city") and weather:
                    
                conn = get_db_connection()
                today = date.today().isoformat()

                conn.execute(
                     "INSERT INTO weather_data (city, temperature, humidity, description, date) VALUES (?, ?, ?, ?, ?)",
                        (weather["city"], weather["temp"], weather["humidity"], weather["desc"], today)
                     )
                conn.commit()

                rows = conn.execute(
                        "SELECT * FROM weather_data WHERE city=? ORDER BY id DESC LIMIT 2",
                        (weather["city"],)
                         ).fetchall()
                conn.close()

    if len(rows) == 2:
        diff = rows[0]["temperature"] - rows[1]["temperature"]

        if diff > 0:
            comparison = f"Temperature increased by {diff:.1f}°C compared to previous search"
        elif diff < 0:
            comparison = f"Temperature decreased by {abs(diff):.1f}°C compared to previous search"
        else:
            comparison = "Temperature is same as previous search"
   # in your single_city() route, before render_template
    location_loaded = bool(request.form.get("lat") and request.form.get("lon"))

    return render_template(
        "single_city.html",
        location_loaded=True,
        weather=weather,
        forecast=forecast,
        hours=hours,
        temps=temps,
        winds=winds,
        precip=precip,
        comparison=comparison
    )

 # ---------- TWO CITY COMPARISON ----------
@app.route("/compare", methods=["GET", "POST"])
def compare_city():

    city_compare = None

    if request.method == "POST":

        city1 = request.form.get("city1")
        city2 = request.form.get("city2")

        w1 = get_weather(city1)
        w2 = get_weather(city2)

        if w1 is None or w2 is None:
            city_compare = {"error": "Invalid city name entered"}

        else:

            f1 = get_forecast(city1)
            f2 = get_forecast(city2)

            diff = w1["temp"] - w2["temp"]

            if diff > 0:
                result = f"{city1} is {diff:.1f}°C hotter than {city2}"
            elif diff < 0:
                result = f"{city1} is {abs(diff):.1f}°C cooler than {city2}"
            else:
                result = "Both cities have same temperature"


            # -------- GRAPH DATA CITY 1 --------
            forecast_data1 = requests.get(
                f"https://api.openweathermap.org/data/2.5/forecast?q={city1}&appid={API_KEY}&units=metric"
            ).json()

            hours1, temps1, winds1, precip1 = [], [], [], []

            for item in forecast_data1["list"][:12]:
                hours1.append(item["dt_txt"].split(" ")[1][:5])
                temps1.append(item["main"]["temp"])
                winds1.append(item["wind"]["speed"])
                precip1.append(item.get("pop",0)*100)


            # -------- GRAPH DATA CITY 2 --------
            forecast_data2 = requests.get(
                f"https://api.openweathermap.org/data/2.5/forecast?q={city2}&appid={API_KEY}&units=metric"
            ).json()

            hours2, temps2, winds2, precip2 = [], [], [], []

            for item in forecast_data2["list"][:12]:
                hours2.append(item["dt_txt"].split(" ")[1][:5])
                temps2.append(item["main"]["temp"])
                winds2.append(item["wind"]["speed"])
                precip2.append(item.get("pop",0)*100)


            city_compare = {
                "city1": w1,
                "city2": w2,
                "forecast1": f1,
                "forecast2": f2,
                "result": result,

                "graph1": {
                    "hours": hours1,
                    "temps": temps1,
                    "winds": winds1,
                    "precip": precip1
                },

                "graph2": {
                    "hours": hours2,
                    "temps": temps2,
                    "winds": winds2,
                    "precip": precip2
                }
            }

    return render_template("compare_city.html", city_compare=city_compare)
            
# ---------------- REVERSE GEOCODING FUNCTION ---------------- #
def get_city_from_latlon(lat, lon):
    """
    Converts latitude and longitude into nearest city/town/village
    using the free Nominatim (OpenStreetMap) API.
    """
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
    response = requests.get(url, headers={"User-Agent": "MyWeatherApp"})
    
    if response.status_code != 200:
        return None
    
    data = response.json()
    city = data.get("address", {}).get("city") \
        or data.get("address", {}).get("town") \
        or data.get("address", {}).get("village") \
        or data.get("address", {}).get("hamlet")
    
    return city

#---------------location--------------
@app.route("/location-weather", methods=["POST"])
def location_weather():
    lat = request.form.get("lat")
    lon = request.form.get("lon")

    if not lat or not lon:
        return redirect(url_for("single_city"))

    try:
        lat, lon = float(lat), float(lon)
    except ValueError:
        return redirect(url_for("single_city"))

    city = get_city_from_latlon(lat, lon) or "Your Location"

    # --- Current Weather using 'weather' endpoint ---
    try:
        current_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        response = requests.get(current_url)
        data = response.json()
    except Exception as e:
        print("Weather API error:", e)
        return redirect(url_for("single_city"))

    if data.get("cod") != 200:  # API returned error
        print("API error:", data)
        return redirect(url_for("single_city"))

    weather = {
        "city": data.get("name", city),
        "temp": data.get("main", {}).get("temp", 0),
        "humidity": data.get("main", {}).get("humidity", 0),
        "desc": data.get("weather", [{}])[0].get("description", "N/A"),
        "wind": data.get("wind", {}).get("speed", 0)
    }

    # --- Forecast (5-day / 3-hourly) ---
    try:
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        fdata = requests.get(forecast_url).json()
    except Exception as e:
        print("Forecast API error:", e)
        fdata = {}

    # Hourly graph (next 12 points)
    hours, temps, winds, precip = [], [], [], []
    for item in fdata.get("list", [])[:12]:
        hours.append(item.get("dt_txt", "").split(" ")[1][:5])
        temps.append(item.get("main", {}).get("temp", 0))
        winds.append(item.get("wind", {}).get("speed", 0))
        precip.append(item.get("pop", 0) * 100)

    # 10-day forecast approximation (take 12:00 data)
    forecast = []
    seen_dates = set()
    for item in fdata.get("list", []):
        date_str, time_str = item.get("dt_txt", "").split(" ")
        if time_str == "12:00:00" and date_str not in seen_dates:
            day_name = datetime.strptime(date_str, "%Y-%m-%d").strftime("%A")
            forecast.append({
                "date": day_name,
                "temp": item.get("main", {}).get("temp", 0),
                "desc": item.get("weather", [{}])[0].get("description", "N/A")
            })
            seen_dates.add(date_str)
        if len(forecast) >= 10:
            break

    # --- Save to DB ---
    conn = get_db_connection()
    today = date.today().isoformat()
    conn.execute(
        "INSERT INTO weather_data (city, temperature, humidity, description, date) VALUES (?, ?, ?, ?, ?)",
        (weather["city"], weather["temp"], weather["humidity"], weather["desc"], today)
    )
    conn.commit()

    # Compare with previous entry
    rows = conn.execute(
        "SELECT * FROM weather_data WHERE city=? ORDER BY id DESC LIMIT 2",
        (weather["city"],)
    ).fetchall()
    conn.close()

    comparison = None
    if len(rows) == 2:
        diff = rows[0]["temperature"] - rows[1]["temperature"]
        if diff > 0:
            comparison = f"Temperature increased by {diff:.1f}°C compared to yesterday"
        elif diff < 0:
            comparison = f"Temperature decreased by {abs(diff):.1f}°C compared to yesterday"
        else:
            comparison = "Temperature is same as yesterday"

    return render_template(
        "single_city.html",
        location_loaded=True,
        weather=weather,
        forecast=forecast,
        hours=hours,
        temps=temps,
        winds=winds,
        precip=precip,
        comparison=comparison
    )

@app.route("/trends", methods=["GET", "POST"])
def trends():

    city_name = None
    trendData = {"dates": [], "temps": [], "winds": [], "precip": []}
    avg_temp = None
    trend_message = None

    if request.method == "POST":
        city_name = request.form.get("city")

        url = f"https://api.openweathermap.org/data/2.5/forecast?q={city_name}&appid={API_KEY}&units=metric"

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            dates, temps, winds, precip = [], [], [], []

            for item in data["list"][:5]:
                date = item["dt_txt"].split(" ")[0]

                dates.append(date)
                temps.append(item["main"]["temp"])
                winds.append(item["wind"]["speed"])
                precip.append(item.get("pop", 0) * 100)

            trendData = {
                "dates": dates,
                "temps": temps,
                "winds": winds,
                "precip": precip
            }

            # -------- EXTRA ANALYTICS --------
            if temps:
                avg_temp = round(sum(temps) / len(temps), 2)

            if len(temps) > 1:
                if temps[-1] > temps[0]:
                    trend_message = "Temperature is rising 📈"
                elif temps[-1] < temps[0]:
                    trend_message = "Temperature is falling 📉"
                else:
                    trend_message = "Temperature is stable"

            print("API Trend Data:", trendData)

        except Exception as e:
            print("API Error:", e)

# -------- DATABASE ANALYTICS --------
    conn = get_db_connection()

    # Updated: average temperature per day for better chart trends
    history = conn.execute("""
        SELECT date, AVG(temperature) as avg_temp
        FROM weather_data
        GROUP BY date
        ORDER BY date ASC
        LIMIT 10
    """).fetchall()

    history_dates = [row["date"] for row in history]
    history_temps = [row["avg_temp"] for row in history]

    # Most searched cities
    cities = conn.execute(
        "SELECT city, COUNT(city) as count FROM weather_data GROUP BY city ORDER BY count DESC LIMIT 5"
    ).fetchall()

    city_names = [row["city"] for row in cities]
    city_counts = [row["count"] for row in cities]

    conn.close()    
    return render_template(
        "trends.html",
        trendData=trendData,
        city_name=city_name,
        avg_temp=avg_temp,
        trend_message=trend_message,
        history_dates=history_dates,
        history_temps=history_temps,
        city_names=city_names,
        city_counts=city_counts
    )
@app.route("/about")
def about():
    return render_template("about.html")

# ---------------- HISTORY PAGE ---------------- #
@app.route("/history", methods=["GET", "POST"])
def history():
    conn = get_db_connection()
    
    search = request.form.get("search") if request.method == "POST" else None
    start_date = request.form.get("start_date") if request.method == "POST" else None
    end_date = request.form.get("end_date") if request.method == "POST" else None
    # ✅ ADD THIS BLOCK HERE
    if request.method == "POST":
        if not start_date or not end_date:
            conn.close()
            return render_template(
                "history.html",
                error="Please select both start and end date",
                rows=[],
                graph_dates=[],
                graph_temps=[]
            )
    query = "SELECT id, city, temperature, date FROM weather_data WHERE 1=1"
    params = []

    if search:
        query += " AND city LIKE ?"
        params.append(f"%{search}%")
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    query += " ORDER BY date ASC"

    rows = conn.execute(query, params).fetchall()
    conn.close()

    graph_dates = [row["date"] for row in rows] if rows else []
    graph_temps = [row["temperature"] for row in rows] if rows else []

    return render_template(
        "history.html",
        rows=rows,
        graph_dates=graph_dates,
        graph_temps=graph_temps
    )

# ---------------- DELETE HISTORY ---------------- #
@app.route("/delete_selected_history", methods=["POST"])
def delete_selected_history():
    if not session.get("admin_logged_in"):
        return "Access Denied ❌"

    selected_ids = request.form.getlist("selected_ids")
    if selected_ids:
        selected_ids = [int(i) for i in selected_ids]  # convert to int
        conn = get_db_connection()
        query = f"DELETE FROM weather_data WHERE id IN ({','.join('?' for _ in selected_ids)})"
        conn.execute(query, selected_ids)
        conn.commit()
        conn.close()

    return redirect(url_for("history"))

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    message = None

    if session.get("admin_logged_in"):
        return redirect(url_for("history"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # empty check
        if not username or not password:
            message = "Please enter username and password"
            return render_template("admin_login.html", message=message)

        # both wrong
        if username != ADMIN_USERNAME and password != ADMIN_PASSWORD:
            message = "Incorrect username and password"
            return render_template("admin_login.html", message=message)

        # only username wrong
        if username != ADMIN_USERNAME:
            message = "Incorrect username"
            return render_template("admin_login.html", message=message)

        # only password wrong
        if password != ADMIN_PASSWORD:
            message = "Incorrect password"
            return render_template("admin_login.html", message=message)

        # success
        session["admin_logged_in"] = True
        return redirect(url_for("history"))

    return render_template("admin_login.html", message=message)
# Admin logout
@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    flash("Logged out successfully!", "success")
    return redirect(url_for("single_city"))

#-----------------time aago-----------------------#
def time_ago(time_str):
    now = datetime.now()
    past = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")

    diff = now - past
    seconds = diff.total_seconds()

    if seconds < 60:
        return "Just now"
    elif seconds < 3600:
        return f"{int(seconds // 60)} minutes ago"
    elif seconds < 86400:
        return f"{int(seconds // 3600)} hours ago"
    else:
        return f"{int(seconds // 86400)} days ago"
# ---------------- FEEDBACK ROUTE ---------------- #
@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    message = None

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        rating = request.form.get("rating")
        comment = request.form.get("comment")

        # ---------------- VALIDATION ---------------- #

        if not rating:
            return render_template("feedback.html", message="Please select rating", latest_feedback=[])

        if not name or not email or not comment:
            return render_template("feedback.html", message="Please fill all fields", latest_feedback=[])

        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                return render_template("feedback.html", message="Rating must be 1 to 5", latest_feedback=[])
        except:
            return render_template("feedback.html", message="Invalid rating", latest_feedback=[])

        # ---------------- INSERT INTO DB ---------------- #
        conn = get_db_connection()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn.execute(
            "INSERT INTO feedback (name, email, rating, comment, created_at) VALUES (?, ?, ?, ?, ?)",
            (name, email, rating, comment, created_at)
        )
        conn.commit()
        conn.close()

        message = "Thank you for your feedback! ⭐"

    # ---------------- FETCH FEEDBACK ---------------- #
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT id, name, rating, comment, created_at FROM feedback ORDER BY created_at DESC"
    ).fetchall()
    conn.close()

    feedback_list = []

    for row in rows:
        feedback_list.append({
            "id": row["id"],
            "name": row["name"],
            "rating": row["rating"],
            "comment": row["comment"],
            "created_at": time_ago(row["created_at"])
        })

    return render_template(
        "feedback.html",
        message=message,
        latest_feedback=feedback_list
    )
# ---------------- DELETE FEEDBACK (ADMIN ONLY) ---------------- #
@app.route("/delete_feedback", methods=["POST"])
def delete_feedback():
    if not session.get("admin_logged_in"):
        return "Access Denied ❌"

    selected_ids = request.form.getlist("selected_ids")

    # remove empty values
    selected_ids = [i for i in selected_ids if i.strip()]

    if not selected_ids:
        return redirect(url_for("feedback"))

    selected_ids = [int(i) for i in selected_ids]

    conn = get_db_connection()
    query = f"DELETE FROM feedback WHERE id IN ({','.join(['?'] * len(selected_ids))})"
    conn.execute(query, selected_ids)
    conn.commit()
    conn.close()

    return redirect(url_for("feedback"))


# ---------------- RUN APP ---------------- #
if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)