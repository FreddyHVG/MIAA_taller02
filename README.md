
# UNIVERSIDAD TÉCNICA PARTICULAR DE LOJA

<img src="https://drive.google.com/uc?id=1X5UmWVlUX9XmckJgFLmv6mTTX81GEr0c" width="300">

## FACULTAD DE INGENIERÍAS Y ARQUITECTURA  
### MAESTRÍA EN INTELIGENCIA ARTIFICIAL APLICADA

---

## Práctica 2: Uso de una herramienta para desplegar un modelo de inteligencia artificial

**Autor:** Freddy Hernán Villota González  
**Docente:** M.Sc. Alexandra Cristina González Eras  
**Fecha:** 18 de mayo de 2025  

---

# Balance Hídrico Mensual en Carchi, Ecuador

Este proyecto desarrolla una solución completa para modelar y predecir el **balance hídrico mensual (P - PET)** en la provincia de **Carchi, Ecuador**, integrando:

- Datos de reanálisis (ERA5-Land)
- Cálculo de PET mediante la ecuación de Penman–Monteith (FAO-56)
- Modelado con **XGBoost** y **LSTM**
- Proyecciones futuras con datos **CMIP6**
- Registro de experimentos con **MLflow**
- Despliegue web interactivo mediante **Flask** y **ngrok**

---

## 1. Preparación del entorno

### Google Colab y autenticación

```python
from google.colab import drive
drive.mount('/content/drive')

!pip install geemap mlflow flask pyngrok --quiet
```

### Google Earth Engine (GEE)

```python
import ee
ee.Authenticate()
ee.Initialize(project="ee-freddyvillota")
```

---

## 2. Cálculo de PET con Penman–Monteith (FAO-56)

Se aplicó la ecuación de Penman–Monteith estándar recomendada por FAO-56:

\[
	ext{PET} = rac{0.408 \Delta (R_n - G) + \gamma rac{900}{T + 273} u_2 (e_s - e_a)}{\Delta + \gamma (1 + 0.34 u_2)}
\]

Donde:

- \( \Delta \): pendiente de la curva de presión de vapor (kPa/°C)  
- \( R_n \): radiación neta (MJ/m²/día)  
- \( G \): flujo de calor al suelo (≈ 0 para mensual)  
- \( \gamma \): constante psicrométrica (kPa/°C)  
- \( T \): temperatura media del aire (°C)  
- \( u_2 \): velocidad del viento a 2 m (m/s)  
- \( e_s \), \( e_a \): presión de vapor de saturación y real (kPa)

### Variables ERA5 utilizadas:

- `temperature_2m`, `dewpoint_temperature_2m`
- `u_component_of_wind_10m`, `v_component_of_wind_10m`
- `surface_net_solar_radiation`, `surface_net_thermal_radiation`

---

## 3. Dataset y balance hídrico

El **balance hídrico mensual** se calcula como:

```python
balance_mm = precip_mm - PET_mm_month
```

Se combinan datos mensuales desde 1981 a 2024, y se exportan para entrenamiento.

---

## 4. Entrenamiento de modelos de predicción

Se seleccionaron las variables climáticas:

```python
features = ['precip_mm', 'temp_c', 'wind_u', 'wind_v', 'solar_rad']
target = 'balance_mm'
```

### XGBoost

```python
from xgboost import XGBRegressor
model = XGBRegressor(n_estimators=100, learning_rate=0.1)
model.fit(X_train, y_train)
```

### LSTM

Modelo secuencial multistep con `timesteps = 3`, usando:

```python
Sequential([
    LSTM(64, activation='relu', return_sequences=False),
    Dense(1)
])
```

---

## 5. Registro y gestión con MLflow

Se utilizó **MLflow Tracking** para:

- Registrar hiperparámetros y métricas
- Almacenar múltiples versiones del modelo XGBoost
- Recuperar el mejor modelo directamente desde MLflow

```python
import mlflow
mlflow.set_experiment("balance_hidrico_modelo_xgboost")

with mlflow.start_run():
    mlflow.log_param("n_estimators", 100)
    mlflow.log_metric("rmse", rmse)
    mlflow.sklearn.log_model(model, "xgboost_model")
```

Para cargar el mejor modelo desde MLflow:

```python
model = mlflow.sklearn.load_model("runs:/<run_id>/xgboost_model")
```

---

## 6. Proyecciones futuras con CMIP6

Se descargaron proyecciones climáticas mensuales (2025–2050):

- Temperatura (K → °C)
- Precipitación (kg/m²/s → mm/día)
- Radiación solar (W/m² → MJ/m²/mes)

Estas variables fueron transformadas y adaptadas al formato del modelo entrenado.

---

## 7. Despliegue con Flask y ngrok (en Google Colab)

Se construyó una **aplicación web ligera con Flask**, que permite al usuario:

- Seleccionar un mes y año para visualizar el **balance hídrico GEE**
- Ingresar un rango de años para obtener un **gráfico proyectado de balance hídrico**

### Estructura de la app:

```python
@app.route("/")
def index():  # Página principal con formulario

@app.route("/balance")
def balance():  # Visualiza el mapa mensual desde GEE

@app.route("/predecir")
def predecir():  # Realiza predicción multianual con XGBoost y muestra gráfico
```

### Uso de ngrok:

```python
from pyngrok import ngrok
ngrok.set_auth_token("TU_TOKEN")
public_url = ngrok.connect(5000)
```

El servidor Flask corre en segundo plano con `threading`.

---

## 8. Visualización y exportación

Se generaron visualizaciones como:

- Mapa suavizado de balance mensual (`resample('bicubic')`)
- Gráfico de predicción multianual (línea temporal con `matplotlib.dates`)
- Comparaciones entre modelos en 2021–2023

Los resultados se exportan como:

```python
df.to_csv("/content/drive/MyDrive/.../df_balanceH_historico.csv")
```

---

## ✅ Resultado final

Este flujo de trabajo permite:

- Construir modelos de predicción climática del balance hídrico
- Registrar experimentos y modelos con MLflow
- Realizar proyecciones realistas con XGBoost y LSTM
- Visualizar mapas dinámicos desde Earth Engine
- Desplegar una app web en **Google Colab** con **Flask + ngrok** sin necesidad de servidor propio

> Esta solución es modular y escalable, y puede adaptarse a otras provincias o escenarios hídricos para fines de planificación, monitoreo ambiental o investigación científica.
