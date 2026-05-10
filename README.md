# ParkSystem — Estacionamiento Público
### MODULO 3 CLASE 11 PROYECTO FINAL

Sistema de gestión de estacionamiento público — Proyecto Final de Base de Datos.

**PHD. MCC. Ramiro Lupercio Coronel**

---

## 🚀 Instrucciones para Ejecutar

### 1. Requisitos
- **Python 3.10+** instalado ([descargar aquí](https://www.python.org/downloads/))
- Al instalar Python, **marca la casilla "Add Python to PATH"**
- **MySQL / XAMPP** corriendo en localhost

### 2. Clonar el repositorio
```bash
git clone https://github.com/OryxSSJ/MODULO-3-CLASE-11-PROYECTO-FINAL.git
cd MODULO-3-CLASE-11-PROYECTO-FINAL
```

### 3. Instalar dependencias
```bash
python -m pip install -r requirements.txt
```

### 4. Configurar variables de entorno
Crea un archivo `.env` en la raíz del proyecto (o copia `.env.example`):
```env
SECRET_KEY=tu-clave-secreta-aqui
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=
DB_NAME=estacionamiento_db
PENSION_MENSUAL_BASE=1500
```

### 5. Inicializar la base de datos
```bash
python setup_db.py
```

### 6. Ejecutar el sistema
```bash
python app.py
```

### 7. Abrir en el navegador
**http://127.0.0.1:5000**

---

## Credenciales de Acceso

| Usuario     | Contraseña    | Rol       |
|-------------|---------------|-----------|
| `admin`     | `admin123`    | Admin     |

> **Admin** = acceso total (Usuarios + Reportes)  
> **Cobrador** = registra entradas/salidas, clientes y vehículos

---

## Modelo de Datos (ER)

| Entidad    | Descripción                                |
|------------|---------------------------------------------|
| CLIENTE    | Registrado u Ocasional, estado Activo/Inactivo |
| VEHICULO   | Placa única, marca, modelo, color, FK cliente |
| ESTANCIA   | Fecha entrada/salida, tarifa aplicada       |
| TARIFA     | Tiempo inicial (min), costo base, costo/min extra |
| PENSION    | Mensual por cliente, fecha inicio/fin, estado |
| PAGO       | Monto, método de pago (efectivo/tarjeta/transferencia) |
| USUARIO    | Nombre, username, perfil (admin/cobrador)  |

### Fórmula de Cobro de Estancia (Dinámica):
```
1. Se calcula el tiempo total en minutos.
2. Se redondea al alza a la hora más cercana (ceil).
3. Si Horas ≤ Horas Límite Reducción:
   Total = Horas × Costo Hora
4. Si Horas > Horas Límite Reducción:
   Total = Horas × Costo Hora Reducida

Ejemplo: 
Tarifa: $30/hr, Límite 5 hrs, Reducida $25/hr.
- Si se queda 4 hrs: 4 * 30 = $120.
- Si se queda 6 hrs: 6 * 25 = $150.
```

> **Interoperabilidad:** Las tarifas se configuran desde el módulo de "Tarifas" y afectan instantáneamente al cálculo de salida.

---

## Páginas del Sistema

| Página      | URL            | Descripción                       |
|-------------|----------------|-----------------------------------|
| Login       | `/login`       | Inicio de sesión                  |
| Dashboard   | `/dashboard`   | Resumen general y vehículos activos |
| Estancias   | `/estancias`   | Entrada / salida vehicular        |
| Pagos       | `/pagos`       | Historial de pagos                |
| Clientes    | `/clientes`    | CRUD de clientes                  |
| Vehículos   | `/vehiculos`   | CRUD de vehículos                 |
| Tarifas     | `/tarifas`     | Configuración de tarifas          |
| Pensiones   | `/pensiones`   | CRUD de pensiones mensuales       |
| Usuarios    | `/usuarios`    | Gestión de usuarios (solo admin)  |
| Reportes    | `/reportes`    | Estadísticas y gráficas (solo admin) |

---

## Tecnologías

- **Python 3** + **Flask 3.1** (backend / routing / templates)
- **MySQL** + **mysql-connector-python** (base de datos)
- **Jinja2** (server-side rendering de templates)
- **HTML5 / CSS3 / JavaScript** (frontend)
- **python-dotenv** (variables de entorno)
- **Werkzeug** (hash seguro de contraseñas)

---

## Características del Sistema

- 🔐 **Autenticación** con sesiones Flask y contraseñas hasheadas (Werkzeug)
- 🚗 **Gestión de estancias** con cálculo automático de cobro desde tarifas configurables
- 💳 **Método de pago** seleccionable (efectivo, tarjeta, transferencia)
- 📋 **Pensiones mensuales** con descuento automático por antigüedad (+2 años → 20% off)
- 📊 **Reportes server-side** renderizados en Jinja2 (gráficas de barras, demanda por hora/mes, ingresos)
- ⚙️ **Configuración por variables de entorno** (DB, secret key, tarifa base de pensión)
- 🛡️ **Control de acceso por roles** (admin vs cobrador)
- 🔒 **Blindaje de Negocio**: Prevención de doble entrada, validación de traslapes en pensiones y protección de tarifas exclusivas.

---

## 🛠️ Pendientes y Próximas Mejoras

- [ ] **Pruebas de Estrés**: Carga masiva de ~500 registros para validar rendimiento de reportes.
- [ ] **Módulo de Facturación**: Generación de PDF para tickets de salida.
- [ ] **Notificaciones**: Avisos automáticos por correo cuando una pensión esté por expirar.
- [ ] **Integración con Hardware**: Conexión con sensores de proximidad para automatizar la apertura de plumas.
