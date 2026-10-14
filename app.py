from flask import Flask, render_template, request, redirect, url_for, flash, session
import pymysql
import pymysql.cursors
import traceback
import io
import qrcode
from flask import send_file

app = Flask(__name__)
app.secret_key = "sistema_solar_secreto"

# ==========================
# CONEXIÓN A LA BASE DE DATOS
# ==========================
def conectar_db():
    return pymysql.connect(
        host="127.0.0.1",
        port=3307,
        user="root",
        password="",
        database="sistema_solar_db",
        cursorclass=pymysql.cursors.DictCursor
    )

# ==========================
# INICIO Y RUTAS GENERALES
# ==========================
@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/dashboard")
def dashboard():
    if "id_usuario" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", nombre=session.get("nombre", "Explorador"))

# ==========================
# LOGIN & REGISTRO
# ==========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form["correo"]
        contrasena = request.form["contrasena"]

        try:
            conexion = conectar_db()
            with conexion.cursor() as cursor:
                cursor.execute("SELECT * FROM usuarios WHERE correo=%s", (correo,))
                usuario = cursor.fetchone()
            conexion.close()

            if usuario and usuario["contrasena"] == contrasena:
                session["id_usuario"] = usuario["id_usuario"]
                session["nombre"] = usuario["nombre_usuario"]
                session["correo"] = usuario["correo"]
                return redirect(url_for("dashboard"))
            else:
                flash("Credenciales incorrectas.")

        except Exception as e:
            print(e)
            traceback.print_exc()
            flash("Error al conectar con la base de datos.")

    return render_template("login.html")

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form["nombre"]
        correo = request.form["correo"]
        contrasena = request.form["contrasena"]
        edad = request.form["edad"]

        try:
            conexion = conectar_db()
            with conexion.cursor() as cursor:
                cursor.execute("SELECT * FROM usuarios WHERE correo=%s", (correo,))
                if cursor.fetchone():
                    flash("Ese correo ya está registrado.")
                    conexion.close()
                    return redirect(url_for("registro"))

                cursor.execute("""
                    INSERT INTO usuarios (nombre_usuario, correo, contrasena, edad)
                    VALUES (%s, %s, %s, %s)
                """, (nombre, correo, contrasena, edad))

            conexion.commit()
            conexion.close()
            flash("Registro exitoso.")
            return redirect(url_for("login"))

        except Exception as e:
            print(e)
            traceback.print_exc()
            flash("Error al registrar el usuario.")

    return render_template("registro.html")

# ==========================
# MÓDULO DE PLANETAS
# ==========================
@app.route("/planetas")
def planetas():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conexion = conectar_db()
    with conexion.cursor() as cursor:
        cursor.execute("SELECT * FROM planetas")
        lista_planetas = cursor.fetchall()
    conexion.close()

    return render_template("planetas.html", planetas=lista_planetas, nombre=session.get("nombre", "Explorador"))

@app.route("/planeta/<int:id_planeta>")
def planeta(id_planeta):
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conexion = conectar_db()
    with conexion.cursor() as cursor:
        cursor.execute("SELECT * FROM planetas WHERE id_planeta=%s", (id_planeta,))
        planeta_info = cursor.fetchone()
    conexion.close()

    if not planeta_info:
        flash("El planeta no existe.")
        return redirect(url_for("planetas"))

    return render_template("planeta.html", planeta=planeta_info)
    # ==========================
# GENERAR CÓDIGO QR DINÁMICO
# ==========================
@app.route("/qr_planeta/<int:id_planeta>")
def qr_planeta(id_planeta):
    ip_servidor = "192.168.1.8" 
    url_planeta = f"http://{ip_servidor}:5000/planeta/{id_planeta}"

    img = qrcode.make(url_planeta)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return send_file(buffer, mimetype="image/png")

# ==========================
# OTRAMENTE Y PERFIL
# ==========================
@app.route("/escanear-qr")
def escanear_qr():
    if "id_usuario" not in session:
        return redirect(url_for("login"))
    return render_template("escanear_qr.html")

@app.route("/perfil", methods=["GET", "POST"])
def perfil():
    if "id_usuario" not in session:
        return redirect(url_for("login"))

    conexion = conectar_db()

    if request.method == "POST":
        nuevo_nombre = request.form.get("nombre_usuario")
        nuevo_correo = request.form.get("correo")
        nueva_edad = request.form.get("edad")

        try:
            with conexion.cursor() as cursor:
                cursor.execute("""
                    UPDATE usuarios 
                    SET nombre_usuario=%s, correo=%s, edad=%s 
                    WHERE id_usuario=%s
                """, (nuevo_nombre, nuevo_correo, nueva_edad, session["id_usuario"]))
            conexion.commit()

            session["nombre"] = nuevo_nombre
            session["correo"] = nuevo_correo
            flash("Perfil actualizado con éxito.")
        except Exception as e:
            print(e)
            traceback.print_exc()
            flash("Error al actualizar el perfil.")

    with conexion.cursor() as cursor:
        cursor.execute("SELECT * FROM usuarios WHERE id_usuario=%s", (session["id_usuario"],))
        usuario = cursor.fetchone()
    conexion.close()

    return render_template("perfil.html", usuario=usuario)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)