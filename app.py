from flask import Flask
from flask import render_template

app = Flask(__name__)

@app.route('/')
def inicio():
    return render_template('sitio/index.html')

@app.route('/DH2O/servicios/')
def servicios():
    return render_template('sitio/servicios.html')

@app.route('/DH2O/quienes_somos/')
def quienes_somos():
    return render_template('sitio/quienes_somos.html')

@app.route('/DH2O/mision_vision/')
def mision_vision():
    return render_template('sitio/mision_vision.html')

if __name__ == '__main__':
    app.run(debug=True)