from flask import Flask, render_template_string, request, jsonify
import csv, os, json, math, requests
from datetime import datetime

app = Flask(__name__)

def calc_metrics(t, h, p):
    tf = round(t * 9/5 + 32, 1)
    dp = round(t - ((100 - h) / 5), 1)
    dpf = round(dp * 9/5 + 32, 1)
    vp = round(0.6108 * math.exp((17.27 * t) / (t + 237.3)) * (h / 100), 2)
    hi = round(t + 0.5555 * (6.11 * math.exp(5417.753 * (1/273.16 - 1/(273.15+dp))) - 10), 1)
    hif = round(hi * 9/5 + 32, 1)
    ah = round(216.7 * (vp / (273.15 + t)), 2)
    density = round(1.2929 * (273.15 / (273.15 + t)) * ((p - 0.3783 * vp) / 1013.25), 3)
    altitude = round(44330 * (1 - math.pow(p / 1013.25, 0.1903)))
    if h < 30: comfort, comfort_color = "Too Dry", "warning"
    elif h > 70: comfort, comfort_color = "Too Humid", "info"
    else: comfort, comfort_color = "Comfortable", "success"
    if h > 70: mold, mold_color = "High Risk", "danger"
    elif h > 60 and t > 20: mold, mold_color = "Moderate", "warning"
    else: mold, mold_color = "Low Risk", "success"
    if h < 25 or h > 75 or t > 30 or t < 15: aqi, aqi_color = "Poor", "danger"
    elif h < 30 or h > 65 or t > 28: aqi, aqi_color = "Acceptable", "warning"
    else: aqi, aqi_color = "Optimal", "success"
    return dict(tf=tf, dp=dp, dpf=dpf, vp=vp, hi=hi, hif=hif, ah=ah, density=density,
                altitude=altitude, comfort=comfort, comfort_color=comfort_color,
                mold=mold, mold_color=mold_color, aqi=aqi, aqi_color=aqi_color)

def get_forecast(lat=40.7128, lon=-74.0060):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode,windspeed_10m_max&timezone=auto&forecast_days=7"
        r = requests.get(url, timeout=5)
        data = r.json()
        days = []
        codes = {0:"Sunny",1:"Mostly Clear",2:"Partly Cloudy",3:"Overcast",45:"Foggy",48:"Foggy",
                 51:"Drizzle",53:"Drizzle",55:"Drizzle",61:"Rain",63:"Rain",65:"Heavy Rain",
                 71:"Snow",73:"Snow",75:"Heavy Snow",80:"Showers",81:"Showers",82:"Heavy Showers",
                 95:"Thunderstorm",96:"Thunderstorm",99:"Thunderstorm"}
        icons = {0:"☀️",1:"🌤️",2:"⛅",3:"☁️",45:"🌫️",48:"🌫️",51:"🌦️",53:"🌦️",55:"🌦️",
                 61:"🌧️",63:"🌧️",65:"🌧️",71:"❄️",73:"❄️",75:"❄️",80:"🌦️",81:"🌦️",82:"🌦️",
                 95:"🌩️",96:"🌩️",99:"🌩️"}
        for i in range(7):
            code = data['daily']['weathercode'][i]
            date = data['daily']['time'][i]
            day_name = datetime.strptime(date, "%Y-%m-%d").strftime("%a") if i > 0 else "Today"
            days.append({
                'day': day_name,
                'icon': icons.get(code, "🌤️"),
                'desc': codes.get(code, "Clear"),
                'high': round(data['daily']['temperature_2m_max'][i], 1),
                'low': round(data['daily']['temperature_2m_min'][i], 1),
                'rain': data['daily']['precipitation_probability_max'][i],
                'wind': round(data['daily']['windspeed_10m_max'][i], 1),
            })
        return days
    except:
        return []

def get_city_weather(city):
    try:
        geo = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1", timeout=5).json()
        if not geo.get('results'): return None
        r = geo['results'][0]
        lat, lon, name, country = r['latitude'], r['longitude'], r['name'], r.get('country','')
        weather = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=relativehumidity_2m&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max&timezone=auto&forecast_days=1", timeout=5).json()
        temp = round(weather['current_weather']['temperature'], 1)
        wind = round(weather['current_weather']['windspeed'], 1)
        humidity = weather['hourly']['relativehumidity_2m'][0]
        high = round(weather['daily']['temperature_2m_max'][0], 1)
        low = round(weather['daily']['temperature_2m_min'][0], 1)
        rain = weather['daily']['precipitation_probability_max'][0]
        feels = round(temp - 0.4 * (temp - 10) * (1 - humidity/100), 1)
        return dict(city=name, country=country, temp=temp, feels=feels, humidity=humidity,
                    wind=wind, high=high, low=low)
    except:
        return None

FIXED_CITIES = ["New York","London","Tokyo","Sydney","Dubai","Los Angeles","Paris","Toronto","Miami","Chicago"]

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Weather Station</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="10">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: Arial, sans-serif; background: #1a1a2e; color: white; padding: 16px; }
        h1 { color: #00d4ff; font-size: 22px; }
        h2 { color: #00d4ff; font-size: 15px; margin: 20px 0 10px; }
        .meta { color: #888; font-size: 11px; margin: 4px 0 16px; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
        .btn { background: #16213e; color: white; border: 1px solid #333; border-radius: 8px; padding: 6px 12px; cursor: pointer; font-size: 12px; text-decoration: none; }
        .btn-primary { background: #00d4ff; color: #1a1a2e; border: none; font-weight: bold; }
        .tabs { display: flex; gap: 4px; border-bottom: 1px solid #333; margin-bottom: 16px; }
        .tab { background: none; border: none; color: #888; padding: 8px 16px; cursor: pointer; font-size: 13px; border-bottom: 2px solid transparent; margin-bottom: -1px; }
        .tab.active { color: #00d4ff; border-bottom-color: #00d4ff; font-weight: bold; }
        .range-btns { display: flex; gap: 6px; margin-bottom: 16px; flex-wrap: wrap; }
        .range-btn { background: #16213e; color: white; border: 1px solid #333; border-radius: 8px; padding: 4px 12px; cursor: pointer; font-size: 11px; }
        .range-btn.active { background: #00d4ff; color: #1a1a2e; font-weight: bold; border-color: #00d4ff; }
        .grid3 { display: grid; grid-template-columns: repeat(3,1fr); gap: 12px; margin-bottom: 12px; }
        .grid4 { display: grid; grid-template-columns: repeat(4,1fr); gap: 12px; margin-bottom: 12px; }
        .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px; }
        .card { background: #16213e; border-radius: 12px; padding: 14px 16px; }
        .card-label { color: #00d4ff; font-size: 12px; margin-bottom: 4px; }
        .card-value { font-size: 26px; font-weight: bold; }
        .card-sub { font-size: 12px; color: #888; margin-top: 2px; }
        .status-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 12px; margin-bottom: 12px; }
        .status-card { border-radius: 10px; padding: 10px 14px; text-align: center; }
        .status-card.success { background: #0d2e1a; }
        .status-card.warning { background: #2e1f0d; }
        .status-card.danger { background: #2e0d0d; }
        .status-card.info { background: #0d1e2e; }
        .status-label { font-size: 11px; color: #888; margin-bottom: 4px; }
        .status-value.success { color: #00ff99; font-weight: bold; font-size: 13px; }
        .status-value.warning { color: #ff9900; font-weight: bold; font-size: 13px; }
        .status-value.danger { color: #ff4444; font-weight: bold; font-size: 13px; }
        .status-value.info { color: #00d4ff; font-weight: bold; font-size: 13px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fill,minmax(150px,1fr)); gap: 10px; }
        .metric { background: #0f1729; border-radius: 8px; padding: 10px 12px; }
        .metric-label { font-size: 11px; color: #666; margin-bottom: 4px; }
        .metric-value { font-size: 15px; font-weight: bold; }
        .chart-wrap { background: #16213e; border-radius: 12px; padding: 16px; margin-bottom: 12px; }
        .chart-title { font-size: 12px; color: #888; margin-bottom: 10px; }
        .forecast-grid { display: grid; grid-template-columns: repeat(7,1fr); gap: 8px; }
        .forecast-card { background: #0f1729; border-radius: 10px; padding: 10px 6px; text-align: center; }
        .forecast-day { font-size: 11px; color: #888; margin-bottom: 4px; }
        .forecast-icon { font-size: 20px; margin-bottom: 4px; }
        .forecast-high { font-size: 13px; font-weight: bold; color: #ff6b6b; }
        .forecast-low { font-size: 12px; color: #00d4ff; }
        .forecast-rain { font-size: 10px; color: #888; margin-top: 4px; }
        .search-wrap { margin-bottom: 12px; display: flex; gap: 8px; }
        .search-input { flex: 1; background: #0f1729; border: 1px solid #333; border-radius: 8px; padding: 8px 12px; color: white; font-size: 13px; }
        .city-grid { display: grid; grid-template-columns: repeat(auto-fill,minmax(180px,1fr)); gap: 10px; }
        .city-card { background: #0f1729; border-radius: 10px; padding: 12px 14px; }
        .city-name { font-weight: bold; font-size: 14px; margin-bottom: 2px; }
        .city-country { font-size: 11px; color: #888; margin-bottom: 8px; }
        .city-temp { font-size: 24px; font-weight: bold; color: #00d4ff; margin-bottom: 6px; }
        .city-row { display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 3px; }
        .city-row span { color: #888; }
        .compare-table { width: 100%; border-collapse: collapse; font-size: 12px; }
        .compare-table th { background: #00d4ff; color: #1a1a2e; padding: 8px 10px; text-align: left; }
        .compare-table td { padding: 7px 10px; border-bottom: 1px solid #333; }
        .compare-table tr.local td { color: #00ff99; }
        .section { background: #16213e; border-radius: 12px; padding: 16px; margin-bottom: 12px; }
        .hidden { display: none; }
        .footer { text-align: center; color: #555; font-size: 10px; margin-top: 20px; }
        table { width: 100%; border-collapse: collapse; font-size: 12px; }
        th { background: #00d4ff; color: #1a1a2e; padding: 8px 10px; text-align: left; }
        td { padding: 7px 10px; border-bottom: 1px solid #333; }
        @media(max-width:600px) { .grid3,.grid4,.forecast-grid { grid-template-columns: repeat(2,1fr); } .grid2 { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>🌤️ Weather Station</h1>
            <p class="meta">📍 My Home &bull; Last updated: {{ now }} &bull; Auto-refreshes every 10s</p>
        </div>
        <div style="display:flex;gap:8px;">
            <a href="/export" class="btn">⬇️ Export CSV</a>
        </div>
    </div>

    <div class="tabs">
        <button class="tab active" onclick="showTab('local',this)">📡 My Station</button>
        <button class="tab" onclick="showTab('world',this)">🌍 World Weather</button>
    </div>

    <div id="tab-local">
        <div class="range-btns">
            {% for r in ['1h','6h','24h','7d','All'] %}
            <button class="range-btn {% if loop.first %}active{% endif %}" onclick="setRange('{{r}}',this)">{{r}}</button>
            {% endfor %}
        </div>

        <div class="grid4">
            <div class="card">
                <div class="card-label">🌡️ Temperature</div>
                <div class="card-value">{{ latest.temperature_c }}°C</div>
                <div class="card-sub">{{ metrics.tf }}°F</div>
            </div>
            <div class="card">
                <div class="card-label">💧 Humidity</div>
                <div class="card-value">{{ latest.humidity }}%</div>
                <div class="card-sub">Relative humidity</div>
            </div>
            <div class="card">
                <div class="card-label">📊 Pressure</div>
                <div class="card-value">{{ latest.pressure_hpa }}</div>
                <div class="card-sub">hPa</div>
            </div>
            <div class="card">
                <div class="card-label">🌡️ Heat Index</div>
                <div class="card-value">{{ metrics.hi }}°C</div>
                <div class="card-sub">{{ metrics.hif }}°F feels like</div>
            </div>
        </div>

        <div class="status-grid">
            <div class="status-card {{ metrics.comfort_color }}">
                <div class="status-label">Comfort</div>
                <div class="status-value {{ metrics.comfort_color }}">{{ metrics.comfort }}</div>
            </div>
            <div class="status-card {{ metrics.mold_color }}">
                <div class="status-label">Mold Risk</div>
                <div class="status-value {{ metrics.mold_color }}">{{ metrics.mold }}</div>
            </div>
            <div class="status-card {{ metrics.aqi_color }}">
                <div class="status-label">Air Quality</div>
                <div class="status-value {{ metrics.aqi_color }}">{{ metrics.aqi }}</div>
            </div>
        </div>

        <div class="chart-wrap">
            <div class="chart-title">Temperature over time</div>
            <canvas id="tempChart" height="80"></canvas>
        </div>

        <div class="grid2">
            <div class="chart-wrap">
                <div class="chart-title">Humidity over time</div>
                <canvas id="humChart" height="80"></canvas>
            </div>
            <div class="chart-wrap">
                <div class="chart-title">Pressure over time</div>
                <canvas id="presChart" height="80"></canvas>
            </div>
        </div>

        <div class="section">
            <h2>🔬 Calculated Metrics</h2>
            <div class="metrics-grid">
                <div class="metric"><div class="metric-label">Dew Point</div><div class="metric-value" style="color:#00d4ff">{{ metrics.dp }}°C / {{ metrics.dpf }}°F</div></div>
                <div class="metric"><div class="metric-label">Humidex</div><div class="metric-value" style="color:#ff9900">{{ metrics.hi }}</div></div>
                <div class="metric"><div class="metric-label">Vapor Pressure</div><div class="metric-value" style="color:#9b59b6">{{ metrics.vp }} kPa</div></div>
                <div class="metric"><div class="metric-label">Absolute Humidity</div><div class="metric-value" style="color:#1abc9c">{{ metrics.ah }} g/m³</div></div>
                <div class="metric"><div class="metric-label">Air Density</div><div class="metric-value" style="color:#3498db">{{ metrics.density }} kg/m³</div></div>
                <div class="metric"><div class="metric-label">Est. Altitude</div><div class="metric-value" style="color:#e74c3c">{{ metrics.altitude }} m</div></div>
            </div>
        </div>

        <div class="section">
            <h2>📈 Min / Max / Avg</h2>
            <div class="grid3">
                {% for s in stats %}
                <div style="background:#0f1729;border-radius:8px;padding:10px 14px;">
                    <div style="color:{{ s.color }};font-size:12px;margin-bottom:8px;font-weight:bold;">{{ s.label }}</div>
                    {% for k,v in [('Min',s.min),('Max',s.max),('Avg',s.avg)] %}
                    <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:3px;">
                        <span style="color:#888">{{k}}</span><strong>{{v}}</strong>
                    </div>
                    {% endfor %}
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="section">
            <h2>📋 History</h2>
            <div style="overflow-x:auto;">
                <table>
                    <tr><th>Time</th><th>Temp (°C)</th><th>Temp (°F)</th><th>Humidity (%)</th><th>Pressure (hPa)</th></tr>
                    {% for row in rows[:50] %}
                    <tr><td>{{ row.timestamp }}</td><td>{{ row.temperature_c }}</td><td>{{ row.temperature_f }}</td><td>{{ row.humidity }}</td><td>{{ row.pressure_hpa }}</td></tr>
                    {% endfor %}
                </table>
            </div>
        </div>
    </div>

    <div id="tab-world" class="hidden">
        <div class="section">
            <h2>📅 7-Day Forecast — New York</h2>
            <div class="forecast-grid">
                {% for f in forecast %}
                <div class="forecast-card">
                    <div class="forecast-day">{{ f.day }}</div>
                    <div class="forecast-icon">{{ f.icon }}</div>
                    <div style="font-size:10px;color:#888;margin-bottom:6px;">{{ f.desc }}</div>
                    <div class="forecast-high">{{ f.high }}°</div>
                    <div class="forecast-low">{{ f.low }}°</div>
                    <div class="forecast-rain">💧{{ f.rain }}%</div>
                    <div class="forecast-rain">💨{{ f.wind }}km/h</div>
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="section">
            <h2>🔍 Search Any City</h2>
            <div class="search-wrap">
                <input class="search-input" id="citySearch" placeholder="Search city..." onkeydown="if(event.key==='Enter')searchCity()"/>
                <button class="btn btn-primary" onclick="searchCity()">Search</button>
            </div>
            <div id="searchResult"></div>
        </div>

        <div class="section">
            <h2>🌍 World Cities</h2>
            <div class="city-grid" id="cityGrid">
                {% for city in cities %}
                <div class="city-card">
                    <div class="city-name">{{ city.city }}</div>
                    <div class="city-country">{{ city.country }}</div>
                    <div class="city-temp">{{ city.temp }}°C</div>
                    <div class="city-row"><span>Feels like</span><strong>{{ city.feels }}°C</strong></div>
                    <div class="city-row"><span>Humidity</span><strong>{{ city.humidity }}%</strong></div>
                    <div class="city-row"><span>Wind</span><strong>{{ city.wind }} km/h</strong></div>
                    <div class="city-row"><span>H / L</span><strong>{{ city.high }}° / {{ city.low }}°</strong></div>
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="section">
            <h2>⚖️ Compare with My Station</h2>
            <div style="overflow-x:auto;">
                <table class="compare-table">
                    <tr><th>Location</th><th>Temp</th><th>Humidity</th><th>Wind</th></tr>
                    <tr class="local"><td>📡 My Station</td><td>{{ latest.temperature_c }}°C</td><td>{{ latest.humidity }}%</td><td>—</td></tr>
                    {% for city in cities %}
                    <tr><td>{{ city.city }}, {{ city.country }}</td><td>{{ city.temp }}°C</td><td>{{ city.humidity }}%</td><td>{{ city.wind }} km/h</td></tr>
                    {% endfor %}
                </table>
            </div>
        </div>
    </div>

    <p class="footer">⚡ Raspberry Pi 3B · BME280 · Flask · Open-Meteo API</p>

    <script>
        const labels = {{ labels | safe }};
        const temps = {{ temps | safe }};
        const hums = {{ hums | safe }};
        const pres = {{ pres | safe }};
        const gc = 'rgba(255,255,255,0.06)', tc = 'rgba(255,255,255,0.35)';
        function mkChart(id,data,color,fill,h=80){
            const ctx=document.getElementById(id);
            if(!ctx)return;
            new Chart(ctx,{type:'line',data:{labels,datasets:[{data,borderColor:color,backgroundColor:fill,borderWidth:1.5,tension:0.4,fill:true,pointRadius:0}]},options:{responsive:true,animation:false,plugins:{legend:{display:false}},scales:{x:{grid:{color:gc},ticks:{color:tc,font:{size:10},maxTicksLimit:8}},y:{grid:{color:gc},ticks:{color:tc,font:{size:10}}}}}});
        }
        mkChart('tempChart',temps,'#00d4ff','rgba(0,212,255,0.1)');
        mkChart('humChart',hums,'#00ff99','rgba(0,255,153,0.1)');
        mkChart('presChart',pres,'#ff9900','rgba(255,153,0,0.1)');

        function showTab(name,btn){
            document.getElementById('tab-local').classList.add('hidden');
            document.getElementById('tab-world').classList.add('hidden');
            document.getElementById('tab-'+name).classList.remove('hidden');
            document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
            btn.classList.add('active');
        }
        function setRange(r,btn){
            document.querySelectorAll('.range-btn').forEach(b=>b.classList.remove('active'));
            btn.classList.add('active');
        }
        async function searchCity(){
            const city = document.getElementById('citySearch').value.trim();
            if(!city)return;
            document.getElementById('searchResult').innerHTML='<p style="color:#888;font-size:13px;">Searching...</p>';
            const res = await fetch('/api/city?name='+encodeURIComponent(city));
            const data = await res.json();
            if(data.error){
                document.getElementById('searchResult').innerHTML='<p style="color:#ff4444;font-size:13px;">City not found</p>';
            } else {
                document.getElementById('searchResult').innerHTML=`
                <div class="city-card" style="max-width:220px;margin-bottom:12px;">
                    <div class="city-name">${data.city}</div>
                    <div class="city-country">${data.country}</div>
                    <div class="city-temp">${data.temp}°C</div>
                    <div class="city-row"><span>Feels like</span><strong>${data.feels}°C</strong></div>
                    <div class="city-row"><span>Humidity</span><strong>${data.humidity}%</strong></div>
                    <div class="city-row"><span>Wind</span><strong>${data.wind} km/h</strong></div>
                    <div class="city-row"><span>H / L</span><strong>${data.high}° / ${data.low}°</strong></div>
                </div>`;
            }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    rows = []
    if os.path.exists('weather_data.csv'):
        with open('weather_data.csv','r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    for row in rows:
        row['temperature_f'] = round(float(row['temperature_c'])*9/5+32,1)
    if rows:
        latest = rows[-1]
        temps_l = [float(r['temperature_c']) for r in rows]
        hums_l = [float(r['humidity']) for r in rows]
        pres_l = [float(r['pressure_hpa']) for r in rows]
        stats = [
            {'label':'🌡️ Temperature','min':f"{min(temps_l)}°C",'max':f"{max(temps_l)}°C",'avg':f"{round(sum(temps_l)/len(temps_l),1)}°C",'color':'#00d4ff'},
            {'label':'💧 Humidity','min':f"{min(hums_l)}%",'max':f"{max(hums_l)}%",'avg':f"{round(sum(hums_l)/len(hums_l),1)}%",'color':'#00ff99'},
            {'label':'📊 Pressure','min':f"{min(pres_l)}",'max':f"{max(pres_l)}",'avg':f"{round(sum(pres_l)/len(pres_l),1)} hPa",'color':'#ff9900'},
        ]
        metrics = calc_metrics(float(latest['temperature_c']),float(latest['humidity']),float(latest['pressure_hpa']))
    else:
        latest = {'temperature_c':'N/A','humidity':'N/A','pressure_hpa':'N/A','temperature_f':'N/A'}
        stats = []
        metrics = {}
    rows_reversed = list(reversed(rows))
    labels = json.dumps([r['timestamp'] for r in rows])
    temps = json.dumps([float(r['temperature_c']) for r in rows])
    hums = json.dumps([float(r['humidity']) for r in rows])
    pres = json.dumps([float(r['pressure_hpa']) for r in rows])
    forecast = get_forecast()
    cities = [c for c in [get_city_weather(city) for city in FIXED_CITIES] if c]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return render_template_string(HTML, latest=latest, rows=rows_reversed, stats=stats,
        metrics=metrics, labels=labels, temps=temps, hums=hums, pres=pres,
        forecast=forecast, cities=cities, now=now)

@app.route('/api/city')
def api_city():
    name = request.args.get('name','')
    result = get_city_weather(name)
    if result: return jsonify(result)
    return jsonify({'error':'not found'})

@app.route('/export')
def export():
    if os.path.exists('weather_data.csv'):
        with open('weather_data.csv','r') as f:
            content = f.read()
        from flask import Response
        return Response(content, mimetype='text/csv',
            headers={'Content-Disposition':'attachment;filename=weather_data.csv'})
    return 'No data yet'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
