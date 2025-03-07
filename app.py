from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import qrcode
from io import BytesIO
import os
from datetime import date

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
from datetime import date  # 👈 Importar date para manejar fechas

@app.route('/registrar_consumo', methods=['POST'])
def registrar_consumo():
    try:
        data = request.json
        print("📥 Datos recibidos:", data)

        # Validar que los datos requeridos están en la solicitud
        required_fields = ["id_alumno", "id_paquete", "fecha"]
        for field in required_fields:
            if field not in data or not isinstance(data[field], (int, str)):
                return jsonify({"error": f"Falta el campo requerido o es inválido: {field}"}), 400

        # Convertir a enteros para asegurarnos de que son números
        id_alumno = int(data["id_alumno"])
        id_paquete = int(data["id_paquete"])
        fecha_actual = data["fecha"]

        # Verificar si el alumno ya tiene un registro de consumo en la fecha actual
        consumo_existente = RegistroConsumo.query.filter_by(
            id_alumno=id_alumno, fecha=fecha_actual
        ).first()

        if consumo_existente:
            return jsonify({"error": "⚠️ Ya existe un registro de consumo para este alumno hoy."}), 409  # 409: Conflict

        # Verificar si el alumno y el paquete existen
        alumno = Alumno.query.get(id_alumno)
        paquete = Paquete.query.get(id_paquete)

        if not alumno:
            return jsonify({"error": "❌ El alumno no existe"}), 404
        if not paquete:
            return jsonify({"error": "❌ El paquete no existe"}), 404

        # Crear nuevo registro de consumo
        nuevo_registro = RegistroConsumo(
            id_alumno=id_alumno,
            id_paquete=id_paquete,
            fecha=fecha_actual
        )

        db.session.add(nuevo_registro)
        db.session.commit()

        return jsonify({"mensaje": "✅ Consumo registrado con éxito"}), 201

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error al registrar consumo: {e}")
        return jsonify({"error": "Error interno del servidor", "detalle": str(e)}), 500

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
@app.route('/alumnos/<int:id_alumno>', methods=['GET'])
def obtener_alumno(id_alumno):
    alumno = Alumno.query.get(id_alumno)
    if alumno:
        return jsonify({
            "id": alumno.id_alumno,
            "nombre": alumno.nombre,
            "apellido": alumno.apellido,
            "grado": alumno.grado
        })
    return jsonify({"error": "Alumno no encontrado"}), 404


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Crea las tablas si no existen
    app.run(debug=True)
