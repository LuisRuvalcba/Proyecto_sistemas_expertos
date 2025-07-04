import sqlite3
import tkinter as tk
from tkinter import messagebox

# 1. Base de datos con síntomas y enfermedades
# Crear o conectar a la base de datos
def conectar_db():
    conexion = sqlite3.connect("sistema_experto.db")
    return conexion

# Crear tablas si no existen
def inicializar_db():
    conexion = conectar_db()
    cursor = conexion.cursor()

    # Tabla de síntomas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sintomas (
        id_sintoma INTEGER PRIMARY KEY,
        nombre_sintoma TEXT NOT NULL
    )
    ''')

    # Tabla de enfermedades
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS enfermedades (
        id_enfermedad INTEGER PRIMARY KEY,
        nombre_enfermedad TEXT NOT NULL
    )
    ''')

    # Tabla de relaciones síntomas-enfermedades
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS relacion (
        id_relacion INTEGER PRIMARY KEY,
        id_sintoma INTEGER NOT NULL,
        id_enfermedad INTEGER NOT NULL,
        FOREIGN KEY(id_sintoma) REFERENCES sintomas(id_sintoma),
        FOREIGN KEY(id_enfermedad) REFERENCES enfermedades(id_enfermedad)
    )
    ''')

    conexion.commit()
    conexion.close()

# 2. Vaciar conocimiento en la base de datos
def llenar_base_de_datos():
    conexion = conectar_db()
    cursor = conexion.cursor()

    sintomas = [
        (1, "Fiebre"),
        (2, "Tos"),
        (3, "Dolor de cabeza"),
        (4, "Dificultad para respirar"),
        (5, "Pérdida del gusto/olfato"),
        (6, "Dolor de garganta"),
        (7, "Fatiga extrema")
    ]

    enfermedades = [
        (1, "Gripe"),
        (2, "COVID-19"),
        (3, "Bronquitis"),
        (4, "Neumonía")
    ]

    relaciones = [
        (1, 1, 1),  # Fiebre -> Gripe
        (2, 2, 1),  # Tos -> Gripe
        (3, 3, 1),  # Dolor de cabeza -> Gripe
        (4, 1, 2),  # Fiebre -> COVID-19
        (5, 2, 2),  # Tos -> COVID-19
        (6, 5, 2),  # Pérdida del gusto/olfato -> COVID-19
        (7, 2, 3),  # Tos -> Bronquitis
        (8, 4, 3),
        (9, 4, 4),
        (10, 1, 4)  # Fiebre -> Neumonía
    ]

    cursor.executemany("INSERT OR IGNORE INTO sintomas VALUES (?, ?)", sintomas)
    cursor.executemany("INSERT OR IGNORE INTO enfermedades VALUES (?, ?)", enfermedades)
    cursor.executemany("INSERT OR IGNORE INTO relacion VALUES (?, ?, ?)", relaciones)

    conexion.commit()
    conexion.close()

# 3. Motor de inferencia (Sistema experto)
def motor_de_inferencia(respuestas):
    conexion = conectar_db()
    cursor = conexion.cursor()

    # Obtener enfermedades asociadas a los síntomas seleccionados
    placeholders = ', '.join(['?'] * len(respuestas))
    query = f'''
        SELECT e.nombre_enfermedad, COUNT(*) as coincidencias
        FROM enfermedades e
        JOIN relacion r ON e.id_enfermedad = r.id_enfermedad
        WHERE r.id_sintoma IN ({placeholders})
        GROUP BY e.id_enfermedad
        ORDER BY coincidencias DESC
    '''
    cursor.execute(query, respuestas)

    resultados = cursor.fetchall()
    conexion.close()
    return resultados

# 4. Interfaz gráfica
class SistemaExpertoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema Experto de Detección de Enfermedades")

        # Crear interfaz inicial
        self.eleccion_label = tk.Label(root, text="¿Eres paciente o doctor?", font=("Arial", 12))
        self.eleccion_label.pack(pady=20)

        self.botones_frame = tk.Frame(root)
        self.botones_frame.pack(pady=20)

        self.paciente_boton = tk.Button(self.botones_frame, text="Paciente", command=self.modo_paciente)
        self.paciente_boton.pack(side="left", padx=10)

        self.doctor_boton = tk.Button(self.botones_frame, text="Doctor", command=self.modo_doctor)
        self.doctor_boton.pack(side="left", padx=10)

    def modo_paciente(self):
        self.limpiar_interfaz()
        PacienteApp(self.root)

    def modo_doctor(self):
        self.limpiar_interfaz()
        DoctorApp(self.root)

    def limpiar_interfaz(self):
        for widget in self.root.winfo_children():
            widget.destroy()

class PacienteApp:
    def __init__(self, root):
        self.root = root
        self.sintomas_disponibles = self.obtener_sintomas()
        self.seleccionados = []
        self.indice_sintoma = 0

        # Crear interfaz inicial
        self.pregunta_label = tk.Label(root, text="¿Presentas alguno de los siguientes síntomas?", font=("Arial", 12))
        self.pregunta_label.pack(pady=20)

        self.sintoma_var = tk.StringVar(value=list(self.sintomas_disponibles.values())[0])
        self.sintoma_label = tk.Label(root, textvariable=self.sintoma_var, font=("Arial", 14), fg="blue")
        self.sintoma_label.pack(pady=10)

        self.botones_frame = tk.Frame(root)
        self.botones_frame.pack(pady=20)

        self.si_boton = tk.Button(self.botones_frame, text="Sí", command=self.respuesta_si)
        self.si_boton.pack(side="left", padx=10)

        self.no_boton = tk.Button(self.botones_frame, text="No", command=self.respuesta_no)
        self.no_boton.pack(side="left", padx=10)

        self.resultados_text = tk.Text(root, height=10, width=50, state="disabled")
        self.resultados_text.pack(pady=20)

    def obtener_sintomas(self):
        conexion = conectar_db()
        cursor = conexion.cursor()
        cursor.execute("SELECT id_sintoma, nombre_sintoma FROM sintomas")
        resultados = {row[0]: row[1] for row in cursor.fetchall()}
        conexion.close()
        return resultados

    def respuesta_si(self):
        sintoma_id = list(self.sintomas_disponibles.keys())[self.indice_sintoma]
        self.seleccionados.append(sintoma_id)
        self.siguiente_pregunta()

    def respuesta_no(self):
        self.siguiente_pregunta()

    def siguiente_pregunta(self):
        self.indice_sintoma += 1
        if self.indice_sintoma < len(self.sintomas_disponibles):
            nuevo_sintoma = list(self.sintomas_disponibles.values())[self.indice_sintoma]
            self.sintoma_var.set(nuevo_sintoma)
        else:
            self.mostrar_resultados()

    def mostrar_resultados(self):
        resultados = motor_de_inferencia(self.seleccionados)
        self.resultados_text.config(state="normal")
        self.resultados_text.delete(1.0, tk.END)

        if resultados:
            self.resultados_text.insert(tk.END, "Posibles enfermedades:\n")
            for enfermedad, coincidencias in resultados:
                self.resultados_text.insert(tk.END, f"- {enfermedad} (coincidencias con {coincidencias} síntomas)\n")
        else:
            self.resultados_text.insert(tk.END, "No se encontraron enfermedades correspondientes a los síntomas seleccionados.")

        self.resultados_text.insert(tk.END, "\n\nEsto es un prototipo, consulta a tu médico para tener un diagnóstico más exacto.")
        self.resultados_text.config(state="disabled")
        self.pregunta_label.config(text="Diagnóstico completado.")
        self.sintoma_label.pack_forget()
        self.botones_frame.pack_forget()

class DoctorApp:
    def __init__(self, root):
        self.root = root

        # Interfaz para añadir nueva enfermedad y síntomas
        self.titulo_label = tk.Label(root, text="Agregar nueva enfermedad y síntomas", font=("Arial", 14))
        self.titulo_label.pack(pady=20)

        self.enfermedad_label = tk.Label(root, text="Nombre de la enfermedad:")
        self.enfermedad_label.pack()
        self.enfermedad_entry = tk.Entry(root)
        self.enfermedad_entry.pack(pady=10)

        self.sintomas_label = tk.Label(root, text="Selecciona los síntomas asociados:")
        self.sintomas_label.pack()

        self.sintomas_disponibles = self.obtener_sintomas()
        self.sintomas_var = {}

        for sintoma_id, sintoma_nombre in self.sintomas_disponibles.items():
            var = tk.IntVar()
            chk = tk.Checkbutton(root, text=sintoma_nombre, variable=var)
            chk.pack(anchor="w")
            self.sintomas_var[sintoma_id] = var

        self.nuevo_sintoma_label = tk.Label(root, text="Agregar nuevo síntoma (opcional):")
        self.nuevo_sintoma_label.pack()
        self.nuevo_sintoma_entry = tk.Entry(root)
        self.nuevo_sintoma_entry.pack(pady=10)

        self.guardar_boton = tk.Button(root, text="Guardar", command=self.guardar_datos)
        self.guardar_boton.pack(pady=20)

    def obtener_sintomas(self):
        conexion = conectar_db()
        cursor = conexion.cursor()
        cursor.execute("SELECT id_sintoma, nombre_sintoma FROM sintomas")
        resultados = {row[0]: row[1] for row in cursor.fetchall()}
        conexion.close()
        return resultados

    def guardar_datos(self):
        nombre_enfermedad = self.enfermedad_entry.get().strip()
        sintomas_seleccionados = [sintoma_id for sintoma_id, var in self.sintomas_var.items() if var.get() == 1]
        nuevo_sintoma = self.nuevo_sintoma_entry.get().strip()

        if not nombre_enfermedad:
            messagebox.showerror("Error", "Por favor, ingrese el nombre de la enfermedad.")
            return

        conexion = conectar_db()
        cursor = conexion.cursor()

        # Agregar nuevo síntoma si se ingresó
        if nuevo_sintoma:
            cursor.execute("INSERT INTO sintomas (nombre_sintoma) VALUES (?)", (nuevo_sintoma,))
            nuevo_sintoma_id = cursor.lastrowid
            sintomas_seleccionados.append(nuevo_sintoma_id)

        # Agregar la enfermedad
        cursor.execute("INSERT INTO enfermedades (nombre_enfermedad) VALUES (?)", (nombre_enfermedad,))
        id_enfermedad = cursor.lastrowid

        # Relacionar síntomas con la enfermedad
        for sintoma_id in sintomas_seleccionados:
            cursor.execute("INSERT INTO relacion (id_sintoma, id_enfermedad) VALUES (?, ?)", (sintoma_id, id_enfermedad))

        conexion.commit()
        conexion.close()

        messagebox.showinfo("Éxito", "Datos guardados correctamente.")
        self.root.destroy()
        app = SistemaExpertoApp(self.root)

# Inicializar la aplicación
if __name__ == "__main__":
    inicializar_db()
    llenar_base_de_datos()

    root = tk.Tk()
    app = SistemaExpertoApp(root)
    root.mainloop()
