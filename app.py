# app.py
from flask import Flask, render_template, request
import ee
import geemap.foliumap as geemap
import datetime

# Autenticación con GEE
try:
    ee.Initialize()
except Exception as e:
    ee.Authenticate()
    ee.Initialize()

# ROI: Provincia de Carchi
roi = ee.FeatureCollection("FAO/GAUL_SIMPLIFIED_500m/2015/level1") \
    .filter(ee.Filter.eq("ADM0_NAME", "Ecuador")) \
    .filter(ee.Filter.eq("ADM1_NAME", "Carchi"))

# App Flask
app = Flask(__name__)

# ----------------------------------------------
# Funciones
# ----------------------------------------------
def calc_pet(img):
    T = img.select('temperature_2m').subtract(273.15)
    Td = img.select('dewpoint_temperature_2m').subtract(273.15)
    Ra = img.select('surface_net_solar_radiation') \
         .add(img.select('surface_net_thermal_radiation')).divide(1e6)
    date = img.date()
    days = ee.Image.constant(date.advance(1, 'month').difference(date, 'day'))
    Rn = Ra.divide(days)
    G = ee.Image.constant(0)
    es = T.expression('0.6108 * exp(17.27 * T / (T + 237.3))', {'T': T})
    ea = Td.expression('0.6108 * exp(17.27 * Td / (Td + 237.3))', {'Td': Td})
    delta = es.multiply(4098).divide(T.add(237.3).pow(2))
    gamma = ee.Image.constant(1.013e-3 * 101.3 / (0.622 * 2.45))
    u = img.select('u_component_of_wind_10m')
    v = img.select('v_component_of_wind_10m')
    wind = u.pow(2).add(v.pow(2)).sqrt().multiply(4.87).divide(ee.Number(67.8 * 10 - 5.42).log())
    pet = delta.multiply(Rn.subtract(G)).multiply(0.408) \
        .add(gamma.multiply(900).divide(T.add(273)).multiply(wind).multiply(es.subtract(ea))) \
        .divide(delta.add(gamma.multiply(ee.Image.constant(1).add(wind.multiply(0.34)))))
    return pet.rename('PET')

def get_balance_image(year, month):
    era5 = ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY") \
        .filterDate(f"{year}-{month:02d}-01", f"{year}-{month:02d}-28")

    petCol = era5.map(calc_pet)
    prCol = era5.select('total_precipitation') \
        .map(lambda img: img.multiply(1000).rename('precip_mm')
             .copyProperties(img, img.propertyNames()))

    pet = petCol.first()
    pr = prCol.first()
    balance = pr.subtract(pet).rename('balance_mm').clip(roi)
    return balance.resample('bicubic')

# ----------------------------------------------
# Rutas
# ----------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calcular', methods=['GET'])
def calcular():
    year = int(request.args.get('year'))
    month = int(request.args.get('month'))
    image = get_balance_image(year, month)
    vis = {
        'min': -100, 'max': 100,
        'palette': ['red', 'yellow', 'lightgreen', 'green', 'blue']
    }
    Map = geemap.Map(center=[0.95, -78.4], zoom=8)
    Map.addLayer(image, vis, f"Balance {year}-{month:02d}")
    map_html = Map.to_html()
    return render_template('mapa.html', map_html=map_html)

@app.route('/predecir', methods=['GET'])
def predecir():
    year_ini = int(request.args.get('year_ini'))
    year_end = int(request.args.get('year_end'))
    # Aquí va el código para usar df_cmip6 y modelo ya entrenado
    return f"Simulación de predicción desde {year_ini} hasta {year_end}"

# ----------------------------------------------
if __name__ == '__main__':
    app.run(debug=True, port=5000)
