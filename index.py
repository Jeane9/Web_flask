from __future__ import division, print_function
# coding=utf-8
import sys
import os
import glob
import re
import numpy as np
import tensorflow as tf 
# Keras
from keras.models import load_model
from keras.preprocessing import image
# Flask utils
from flask import Flask, redirect, url_for, request, render_template, session
from werkzeug.utils import secure_filename
from mysqlconnection import connectToMySQL
from werkzeug.security import check_password_hash as checkph
from werkzeug.security import generate_password_hash as genph

import sys
sys.path.insert(0, 'C:/Users/Jeanette/Desktop/cursoP/Red_Neuronal_Convolucional_rnc/Cancer_cervical-web/package/')
# Define a flask app
from package import densenet_M
from package import imagenet_utils_M
# from keras.applications.imagenet_utils import preprocess_input, decode_predictions

app = Flask(__name__)

# Model saved with Keras model.save()
MODEL_PATH = 'C:/Users/Jeanette/Desktop/cursoP/Red_Neuronal_Convolucional_rnc/Cancer_cervical-web/model/modelo_densenet_v2_entrenado.h5'
model =tf.keras.models.load_model(MODEL_PATH)
# model._make_predict_function()          # Necessary ----compila la función predict
# print('Model loaded. Start serving...')

# You can also use pretrained model from Keras
# Check https://keras.io/applications/
#from keras.applications.resnet50 import ResNet50
#model = ResNet50(weights='imagenet')
#model.save('')
print('Model loaded. Check http://127.0.0.1:5000/')

app.secret_key='appLogin'

mysql = connectToMySQL('cancer')   # db
@app.route('/')
def main():
    return render_template('login.html')

@app.route('/busqueda')
def busqueda():
    if 'nombre' in session:
        return render_template('index.html')
    else:
        return redirect( url_for('ingresar'))

@app.route('/ingresar', methods=['GET','POST'])
def ingresar():
    if (request.method == 'GET'):
        if 'nombre' in session:
            return render_template('index.html')
        else:
            return render_template('login.html')
    else:
        nombre = request.form['username']
        contrasena = request.form['pass']
        session['nombre'] = nombre
        hash_contrasena = genph(contrasena)
        usuario = mysql.query_db("select nombre, contrasena from users where nombre =%s", [nombre])

        if (len(usuario) != 0):
            print(usuario)   #diccionario [{'nombre': 'admin', 'contrasena': 'admin'}]
            for row in usuario: 
                username = row['nombre']
                password = row['contrasena']
                print(username, password)
                
            if (checkph(hash_contrasena, password)):
                return redirect(url_for('busqueda', usr=username))
            else:
                # Flask("La contraseña es incorrecta", "alert-warning")
                return render_template("login.html")
        else:
            return render_template("login.html")

@app.route('/historial')
def historial():
    if 'nombre' in session:
        print("a 1111")
        return render_template("historico.html")
    else:
        return render_template("login.html")

# @app.route('/buscar', methods=['GET','POST'])
# def buscar():
#     if (request.method == 'GET'):
#         if 'nombre' in session:
#             return render_template('index.html')
#         else:
#             return render_template('login.html')
#     else:
#         print("a 2222")
#         desde = request.form['inicio']
#         hasta = request.form['fin']
#         print("desde",desde)
#         print(hasta)
#         histo = mysql.query_db("select * from historial where fecha =%s between =%s", [desde][hasta])
#         return histo

@app.route('/salir')
def salir():
    session.clear()
    return redirect(url_for('ingresar'))

def model_predict(img_path, model):
    # img = image.load_img(img_path, target_size=(150, 150))
    img = image.load_img(img_path, target_size=(224, 224))
    # Preprocessing the image
    x = image.img_to_array(img)
    # x = np.true_divide(x, 255)
    x = np.expand_dims(x, axis=0)
    # Be careful how your trained model deals with the input
    # otherwise, it won't make correct prediction!
    x = imagenet_utils_M.preprocess_input(x, mode='caffe')
    preds = model.predict(x)
    print("model predict.................")
    return preds

@app.route('/predict', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Get the file from post request        
        f = request.files['file']
        print('file::::',f)
        # Save the file to ./uploads
        basepath = os.path.dirname(__file__)
        file_path = os.path.join(
            basepath, 'uploads', secure_filename(f.filename))
        f.save(file_path)
        # Make prediction
        preds = model_predict(file_path, model)
        # Process your result for human
        # pred_class = preds.argmax(axis=-1)            # Simple argmax
        pred_class = imagenet_utils_M.decode_predictions(preds, top=1)   # ImageNet Decode
        result = str(pred_class[0][0][1])               # Convert to string
        return result        
    return None  # GET


if __name__ == '__main__':
    app.run(debug=True, port=5000)