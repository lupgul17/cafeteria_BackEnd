from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import qrcode
from io import BytesIO
import os

app = Flask(__name__)
CORS(app)  # Habilita comunicación con el frontend

# 📺 CONFIGURAR BASE DE DATOS (Railway MySQL)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "mysql+pymysql://root:HMbkSmfFQyyjfUzNJFbblKjfLuvVlOLp@tramway.proxy.rlwy.net:41577/railway")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 📺 MODELOS DE BASE DE DATOS
class Responsable(db.Model):
    id_responsable = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    celular = db.Column(db.String(15), nullable=False)

class Alumno(db.Model):
    id_alumno = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    grado = db.Column(db.String(50))
    id_responsable = db.Column(db.Integer, db.ForeignKey('responsable.id_responsable'), nullable=False)

class Paquete(db.Model):
    id_paquete = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.Text, nullable=False)
    comidas_disponibles = db.Column(db.Integer, nullable=False)
    precio = db.Column(db.Numeric(10, 2), nullable=False)

class Pago(db.Model):
    id_pago = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    id_paquete = db.Column(db.Integer, db.ForeignKey('paquete.id_paquete'), nullable=False)
    id_responsable = db.Column(db.Integer, db.ForeignKey('responsable.id_responsable'), nullable=False)
    id_alumno = db.Column(db.Integer, db.ForeignKey('alumno.id_alumno'), nullable=False)

class RegistroConsumo(db.Model):
    id_registro = db.Column(db.Integer, primary_key=True)
    id_alumno = db.Column(db.Integer, db.ForeignKey('alumno.id_alumno'), nullable=False)
    id_paquete = db.Column(db.Integer, db.ForeignKey('paquete.id_paquete'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)

# 📺 GENERAR QR
@app.route('/generar_qr/<int:alumno_id>')
def generar_qr(alumno_id):
    qr = qrcode.make(f"https://cafeteria-qr.vercel.app/scan/{alumno_id}")
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)
    return send_file(buffer, mimetype='image/png')

# 📺 REGISTRAR CONSUMO
@app.route('/registrar_consumo', methods=['POST'])
def registrar_consumo():
    data = request.json
    nuevo_registro = RegistroConsumo(
        id_alumno=data['id_alumno'],
        id_paquete=data['id_paquete'],
        fecha=data['fecha']
    )
    db.session.add(nuevo_registro)
    db.session.commit()
    return jsonify({"mensaje": "Consumo registrado con éxito"})

# 📺 OBTENER TODOS LOS ALUMNOS
@app.route('/alumnos', methods=['GET'])
def obtener_alumnos():
    alumnos = Alumno.query.all()
    return jsonify([{ "id": a.id_alumno, "nombre": a.nombre, "apellido": a.apellido, "grado": a.grado } for a in alumnos])

# 📺 OBTENER TODOS LOS PAGOS
@app.route('/pagos', methods=['GET'])
def obtener_pagos():
    pagos = Pago.query.all()
    return jsonify([
        { "id": p.id_pago, "monto": str(p.monto), "fecha": p.fecha.strftime('%Y-%m-%d'), "alumno": p.id_alumno }
        for p in pagos
    ])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Crea las tablas si no existen
    app.run(debug=True)
