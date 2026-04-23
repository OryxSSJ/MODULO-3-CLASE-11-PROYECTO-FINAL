# 🅿️ ParkSystem — Estacionamiento Público
### MODULO 3 CLASE 11 PROYECTO FINAL

Sistema de gestión de estacionamiento público — Proyecto Final de Base de Datos.

**PHD. MCC. Ramiro Lupercio Coronel**

---

## 🚀 Instrucciones para Ejecutar

### 1. Requisitos
- **Python 3.10+** instalado ([descargar aquí](https://www.python.org/downloads/))
- Al instalar Python, **marca la casilla "Add Python to PATH"**

### 2. Clonar el repositorio
```bash
git clone https://github.com/TU_USUARIO/MODULO-3-CLASE-11-PROYECTO-FINAL.git
cd MODULO-3-CLASE-11-PROYECTO-FINAL
```

### 3. Instalar dependencias
```bash
python -m pip install flask
```

### 4. Ejecutar el sistema
```bash
python app.py
```

### 5. Abrir en el navegador
**http://127.0.0.1:5000**

---

## 🔑 Credenciales de Acceso

| Usuario     | Contraseña    | Rol       |
|-------------|---------------|-----------|
| `admin`     | `admin123`    | Admin     |
| `cobrador1` | `cobrador123` | Cobrador  |
| `cobrador2` | `cobrador123` | Cobrador  |

> **Admin** = acceso total (Usuarios + Reportes)  
> **Cobrador** = registra entradas/salidas, clientes y vehículos

---

## 📋 Modelo de Datos (ER)

| Entidad    | Descripción                                |
|------------|--------------------------------------------|
| CLIENTE    | Registrado u Ocasional, estado Activo/Inactivo |
| VEHICULO   | Placa única, marca, modelo, color, FK cliente |
| ESTANCIA   | Fecha entrada/salida, tarifa aplicada, pensión |
| TARIFA     | Tiempo inicial, costo inicial, costo/min extra |
| PENSION    | Mensual por cliente, fecha inicio/fin, estado |
| PAGO       | Monto, método (efectivo/tarjeta/transferencia) |

### Fórmula de Cobro:
```
Si tiempo ≤ tiempo_inicial_min → costo_inicial
Si tiempo > tiempo_inicial_min → costo_inicial + (minutos_extra × costo_por_min_extra)

Ejemplo: 90 min, Tarifa Estándar
$20.00 + (30 × $0.25) = $27.50
```

---

## 📋 Páginas del Sistema

| Página      | URL            | Descripción                       |
|-------------|----------------|-----------------------------------|
| Login       | `/login`       | Inicio de sesión                  |
| Dashboard   | `/dashboard`   | Resumen general                   |
| Estancias   | `/estancias`   | Entrada / salida vehicular        |
| Pagos       | `/pagos`       | Historial de pagos                |
| Clientes    | `/clientes`    | CRUD de clientes                  |
| Vehículos   | `/vehiculos`   | CRUD de vehículos                 |
| Tarifas     | `/tarifas`     | Configuración de tarifas          |
| Pensiones   | `/pensiones`   | CRUD de pensiones mensuales       |
| Usuarios    | `/usuarios`    | Gestión de usuarios (solo admin)  |
| Reportes    | `/reportes`    | Estadísticas (solo admin)         |

---

## 🛠️ Tecnologías

- **Python 3** + **Flask** (backend)
- **HTML5 / CSS3 / JavaScript** (frontend)
- **Jinja2** (templates)
