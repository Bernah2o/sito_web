from flask import Flask, send_file
from flask import render_template

app = Flask(__name__)

@app.route('/')
def index():
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

@app.route('/DH2O/principios_coorporativos/')
def principios_coorporativos():
    return render_template('sitio/principios_coorporativos.html')

@app.route('/DH2O/politica_de_tratamiento_de_datos/')
def politica_de_tratamiento_de_datos():
    pdf_filename = 'Política de tratamiento de datos.pdf'
    return send_file(pdf_filename, as_attachment=True)

@app.route('/contacto')
def contacto():
    return render_template('sitio/contacto.html')

@app.route('/productos')
def productos():
    return render_template('sitio/productos.html')



if __name__ == '__main__':
    app.run(debug=True)