import os
import json
import time
import streamlit as st
from PIL import Image

import paho.mqtt.client as paho
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events

# -----------------------
# MQTT config
# -----------------------
BROKER = "broker.mqttdashboard.com"
PORT = 1883
TOPIC = "voice_ctrl"

def on_publish(client, userdata, result):
    # Solo para log
    print("Mensaje publicado")

# Prepara cliente MQTT (publicaremos solo cuando haya texto)
mqtt_client = paho.Client(client_id="GIT-HUBC")
mqtt_client.on_publish = on_publish

# -----------------------
# UI
# -----------------------
st.title("Swiftie Voice Control — MQTT")
st.subheader("Di un comando y lo publicamos por MQTT (Taylor’s Version)")

# Imagen (cámbiala en tu repo si quieres)
IMG = "swift_voice.jpg"
if os.path.exists(IMG):
    st.image(Image.open(IMG), width=220)
else:
    st.info("Sube una imagen llamada **swift_voice.jpg** a la carpeta del proyecto.")

st.write("Presiona el botón y di tu comando:")

# -----------------------
# Botón de voz (Web Speech API)
# -----------------------
stt_button = Button(label=" Iniciar 🎤 ", width=220)

stt_button.js_on_event(
    "button_click",
    CustomJS(
        code=r"""
const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
if (!SpeechRec) {
    alert("Este navegador no soporta reconocimiento de voz.");
} else {
    const recognition = new SpeechRec();
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onresult = (e) => {
        let value = "";
        for (let i = e.resultIndex; i < e.results.length; i++) {
            if (e.results[i].isFinal) {
                value += e.results[i][0].transcript;
            }
        }
        if (value !== "") {
            document.dispatchEvent(new CustomEvent("GET_TEXT", { detail: value }));
        }
    };
    recognition.start();
}
"""
    ),
)

result = streamlit_bokeh_events(
    stt_button,
    events="GET_TEXT",
    key="listen",
    refresh_on_update=False,
    override_height=75,
    debounce_time=0,
)

# -----------------------
# Publicación por MQTT
# -----------------------
if result and "GET_TEXT" in result:
    text = result.get("GET_TEXT").strip()
    st.write("**Reconocido:**", text)

    # Mensaje JSON (misma estructura que tenías)
    payload = json.dumps({"Act1": text})

    try:
        mqtt_client.connect(BROKER, PORT, keepalive=10)
        # Publica y da un pequeño margen para que salga del socket
        rc, mid = mqtt_client.publish(TOPIC, payload=payload, qos=0, retain=False)
        mqtt_client.loop(0.2)
        st.success("Comando enviado por MQTT ✅")
        st.code(f"TOPIC: {TOPIC}\nPAYLOAD: {payload}", language="json")
    except Exception as e:
        st.error(f"Error publicando por MQTT: {e}")
