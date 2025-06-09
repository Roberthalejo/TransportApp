from flask import Flask, render_template_string, request, jsonify
from datetime import datetime
import random
import pandas as pd
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.config['GOOGLE_MAPS_API_KEY'] = 'AIzaSyAm9ZohxgPZhRvuoqmpxrLCImwF1Mjw3Hs'  # Nueva configuración añadida

# Crear carpeta de uploads si no existe
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Datos simulados de rutas (modificado para incluir coordenadas)
rutas = {
    'T1': {
        'nombre': 'Transmilenio Línea Troncal', 
        'saturacion': 'alta', 
        'tiempo_estimado': 45,
        'coordenadas': [
            {'lat': 4.7110, 'lng': -74.0721},
            {'lat': 4.6987, 'lng': -74.0762},
            {'lat': 4.6923, 'lng': -74.0825}
        ]
    },
    'A1': {
        'nombre': 'Ruta Alimentadora Norte', 
        'saturacion': 'media', 
        'tiempo_estimado': 25,
        'coordenadas': [
            {'lat': 4.7210, 'lng': -74.0521},
            {'lat': 4.7187, 'lng': -74.0562},
            {'lat': 4.7123, 'lng': -74.0625}
        ]
    },
    'U1': {
        'nombre': 'Urbano Centro', 
        'saturacion': 'baja', 
        'tiempo_estimado': 30,
        'coordenadas': [
            {'lat': 4.6010, 'lng': -74.0621},
            {'lat': 4.6087, 'lng': -74.0662},
            {'lat': 4.6023, 'lng': -74.0725}
        ]
    },
    'S1': {
        'nombre': 'SITP Portal Sur', 
        'saturacion': 'alta', 
        'tiempo_estimado': 40,
        'coordenadas': [
            {'lat': 4.5810, 'lng': -74.1421},
            {'lat': 4.5787, 'lng': -74.1462},
            {'lat': 4.5723, 'lng': -74.1525}
        ]
    },
    'B2': {
        'nombre': 'Bus Chapinero', 
        'saturacion': 'media', 
        'tiempo_estimado': 35,
        'coordenadas': [
            {'lat': 4.6510, 'lng': -74.0621},
            {'lat': 4.6587, 'lng': -74.0562},
            {'lat': 4.6523, 'lng': -74.0525}
        ]
    }
}

usuarios = []
datos_historicos = []

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TransportApp - Monitor de Saturación</title>
    
    <script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyAm9ZohxgPZhRvuoqmpxrLCImwF1Mjw3Hs&callback=initMap" async defer></script>
    
    
    
    
    
    
    <div class="container">
        <div class="header">
            <h1>🚌 TransportApp</h1>
            <p>Monitor de Saturación en Tiempo Real</p>
        </div>
        
        
        <div class="tabs">
            <button class="tab-btn active" onclick="openTab('mapa-tab')">🗺️ Mapa</button>
        </div>
        
        
        <div id="mapa-tab" class="tab-content active">
            <!-- Contenido del Mapa -->
            <div class="card">
                <h3>📍 Mapa de Rutas</h3>
                <div class="map-container">
                    <div class="map-controls">
                        <select id="ruta-selector" onchange="actualizarMapa()">
                            <option value="all">Todas las rutas</option>
                            {% for codigo, info in rutas.items() %}
                            <option value="{{ codigo }}">{{ codigo }} - {{ info.nombre }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div id="map"></div>
                </div>
                <p style="margin-top: 10px; font-size: 0.9em;">
                    <span class="status alta"></span> Alta saturación 
                    <span class="status media"></span> Media saturación 
                    <span class="status baja"></span> Baja saturación
                </p>
            </div>
        </div>
        
        <div id="rutas-tab" class="tab-content">
            <!-- Contenido de Estado de Rutas -->
            <div class="card">
                <h3>🚍 Estado de Rutas</h3>
                <div id="rutas-container">
                    {% for codigo, info in rutas.items() %}
                    <div class="ruta">
                        <div>
                            <span class="status {{ info.saturacion }}"></span>
                            <strong>{{ codigo }}</strong> - {{ info.nombre }}
                        </div>
                        <span>{{ info.tiempo_estimado }} min</span>
                    </div>
                    {% endfor %}
                </div>
                <button class="btn" onclick="actualizarRutas()">🔄 Actualizar</button>
            </div>
        </div>
        
        <div id="reportes-tab" class="tab-content">
            <!-- Contenido de Reportar Saturación -->
            <div class="card">
                <h3>📢 Reportar Saturación</h3>
                <form onsubmit="reportarSaturacion(event)">
                </form>
            </div>
        </div>
        
        <div id="perfil-tab" class="tab-content">
            <!-- Contenido de Perfil -->
            <div class="card">
                <h3>👤 Perfil de Usuario</h3>
                <form onsubmit="guardarPerfil(event)">
                </form>
            </div>
        </div>
        
        <div id="notificaciones-tab" class="tab-content">
            <!-- Contenido de Notificaciones -->
            <div class="card">
                <h3>🔔 Notificaciones</h3>
            </div>
        </div>
        
        <div id="estadisticas-tab" class="tab-content">
            <!-- Contenido de Estadísticas -->
            <div class="card">
                <h3>📊 Estadísticas</h3>
            </div>
        </div>
        
        <div id="dev-tab" class="tab-content">
            <!-- Contenido de Panel Dev -->
            <div class="card">
                <h3>⚙️ Panel de Desarrolladores</h3>
            </div>
        </div>
    </div>

    <style>
        
        .tabs {
            display: flex;
            flex-wrap: wrap;
            margin-bottom: 20px;
            background: rgba(255,255,255,0.9);
            border-radius: 10px;
            padding: 10px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        }
        
        .tab-btn {
            background: none;
            border: none;
            padding: 10px 15px;
            margin: 0 5px;
            cursor: pointer;
            font-size: 14px;
            border-radius: 5px;
            transition: all 0.3s;
        }
        
        .tab-btn:hover {
            background: #e0e0ff;
        }
        
        .tab-btn.active {
            background: #667eea;
            color: white;
            font-weight: bold;
        }
        
        .tab-content {
            display: none;
            width: 100%;
            animation: fadeIn 0.5s;
        }
        
        .tab-content.active {
            display: block;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
    </style>

    
    
<style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; color: white; margin-bottom: 30px; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card { background: rgba(255,255,255,0.95); border-radius: 15px; padding: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.1); }
        .status { width: 15px; height: 15px; border-radius: 50%; display: inline-block; margin-right: 10px; }
        .alta { background: #f44336; }
        .media { background: #FFC107; }
        .baja { background: #4CAF50; }
        .ruta { display: flex; justify-content: space-between; align-items: center; padding: 10px; margin: 8px 0; background: #f8f9fa; border-radius: 8px; }
        .btn { background: #667eea; color: white; border: none; padding: 8px 16px; border-radius: 5px; cursor: pointer; margin: 5px; }
        .btn:hover { background: #5a6fd8; }
        .form-group { margin: 10px 0; }
        input, select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 5px; margin-top: 5px; }
        .notification { background: #e3f2fd; border-left: 4px solid #2196F3; padding: 10px; margin: 10px 0; border-radius: 5px; }
        /* Modificado: Estilos para el mapa */
        #map { 
            height: 400px; 
            width: 100%;
            border-radius: 10px;
            margin-top: 10px;
        }
        .map-container {
            position: relative;
        }
        .map-controls {
            position: absolute;
            top: 10px;
            left: 10px;
            z-index: 1000;
            background: white;
            padding: 5px 10px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        .dev-section { background: #f8f9fa; border: 2px dashed #6c757d; padding: 15px; margin: 10px 0; border-radius: 10px; }
        .file-upload { border: 2px dashed #007bff; padding: 20px; text-align: center; border-radius: 10px; margin: 10px 0; }
        .file-upload:hover { background: #f8f9ff; }
        .success { background: #d4edda; border-left: 4px solid #28a745; padding: 10px; margin: 10px 0; border-radius: 5px; }
        .error { background: #f8d7da; border-left: 4px solid #dc3545; padding: 10px; margin: 10px 0; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚌 TransportApp</h1>
            <p>Monitor de Saturación en Tiempo Real</p>
        </div>
        
        
            
            
            
            <div class="card">
                <!-- Login -->
    <div class="card">
        <div style="text-align: center;">
            <h3>Trafi-Ruta 🚌</h3>
            <h3>Bienvenidos</h3>
        </div>
        <div class="form-group">
            <label for="usuario">Usuario</label>
            <input type="text" id="usuario" name="usuario" placeholder="Ingresa tu usuario" required />
        </div>
        <div class="form-group">
            <label for="password">Contraseña</label>
            <input type="password" id="password" name="password" placeholder="Ingresa tu contraseña" required />
        </div>
        <button type="submit" class="btn">Login</button>
        </form>
        <div class="extra-options" style="display: block;">
            <a href="#">¿Olvidaste tu contraseña?</a>
            <a href="#">Términos del Acuerdo</a>
        </div>
    </div>

            <!-- Menu -->
        <div class="card" style="display: flex; flex-direction: column;">
            <div style="display: flex; justify-content: space-between;">
                <a href="">🏠</a>
                <a href="">🔍</a>
            </div>
            <div>
                <h3>Trafi-Ruta 🚌</h3>
            </div>
            <div style="display: flex; flex-direction: column; align-items: center;">
                <div style="display: flex; flex-direction: column; align-items: center; margin-top: 4px;">
                    <a href="">🚌</a>
                    <p>Rutas Saturadas</p>
                </div>
                <div style="display: flex; flex-direction: column; align-items: center; margin-top: 4px;">
                    <a href="">🗺️</a>
                    <p>Map</p>
                </div>
                <div style="display: flex; flex-direction: column; align-items: center; margin-top: 4px;">
                    📍
                    <p>Rutas en Camino</p>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: auto;">
                <a href="">📅</a>
                <a href="">📍</a>
                <a href="">🧑‍🦲</a>
            </div>
        </div>
                <h3>🚍 Estado de Rutas</h3>
                <div id="rutas-container">
                    {% for codigo, info in rutas.items() %}
                    <div class="ruta">
                        <div>
                            <span class="status {{ info.saturacion }}"></span>
                            <strong>{{ codigo }}</strong> - {{ info.nombre }}
                        </div>
                        <span>{{ info.tiempo_estimado }} min</span>
                    </div>
                    {% endfor %}
                </div>
                <button class="btn" onclick="actualizarRutas()">🔄 Actualizar</button>
            </div>
            
            
            <div class="card">
                <h3>📢 Reportar Saturación</h3>
                <form onsubmit="reportarSaturacion(event)">
                    <div class="form-group">
                        <label>Ruta:</label>
                        <select id="ruta-reporte" required>
                            {% for codigo, info in rutas.items() %}
                            <option value="{{ codigo }}">{{ codigo }} - {{ info.nombre }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Nivel de Saturación:</label>
                        <select id="nivel-saturacion" required>
                            <option value="baja">🟢 Baja</option>
                            <option value="media">🟡 Media</option>
                            <option value="alta">🔴 Alta</option>
                        </select>
                    </div>
                    <button type="submit" class="btn">📤 Enviar Reporte</button>
                </form>
            </div>
            
            
            <div class="card">
                <h3>👤 Perfil de Usuario</h3>
                <form onsubmit="guardarPerfil(event)">
                    <div class="form-group">
                        <label>Nombre:</label>
                        <input type="text" id="nombre-usuario" placeholder="Tu nombre" required>
                    </div>
                    <div class="form-group">
                        <label>Ruta Frecuente:</label>
                        <select id="ruta-frecuente">
                            {% for codigo, info in rutas.items() %}
                            <option value="{{ codigo }}">{{ codigo }} - {{ info.nombre }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <button type="submit" class="btn">💾 Guardar Perfil</button>
                </form>
            </div>
            
            
            <div class="card">
                <h3>🔔 Notificaciones</h3>
                <div id="notificaciones">
                    <div class="notification">
                        <strong>⚠️ Alerta:</strong> Ruta T1 presenta alta saturación
                    </div>
                    <div class="notification">
                        <strong>ℹ️ Info:</strong> Ruta alternativa A1 disponible
                    </div>
                </div>
                <button class="btn" onclick="toggleNotificaciones()">🔕 Activar/Desactivar</button>
            </div>
            
            
            <div class="card">
                <h3>📊 Estadísticas</h3>
                <div>
                    <p><strong>Reportes Hoy:</strong> <span id="reportes-hoy">15</span></p>
                    <p><strong>Usuarios Activos:</strong> <span id="usuarios-activos">{{ usuarios|length }}</span></p>
                    <p><strong>Ruta Más Saturada:</strong> <span id="ruta-saturada">T1 - Transmilenio</span></p>
                    <p><strong>Tiempo Promedio:</strong> <span id="tiempo-promedio">35 min</span></p>
                    <p><strong>Datos Históricos:</strong> <span id="datos-historicos">{{ datos_historicos|length }} registros</span></p>
                </div>
                <button class="btn" onclick="verEstadisticas()">📈 Ver Más</button>
            </div>
            
            
            <div class="card">
                <h3>⚙️ Panel de Desarrolladores</h3>
                <div class="dev-section">
                    <h4>📁 Cargar Datos Históricos</h4>
                    <p><small>Sube archivos CSV con datos anteriores del transporte público</small></p>
                    
                    <form onsubmit="subirCSV(event)" enctype="multipart/form-data">
                        <div class="file-upload">
                            <input type="file" id="csv-file" name="csv_file" accept=".csv" required>
                            <p>📄 Arrastra tu archivo CSV aquí o haz clic para seleccionar</p>
                            <small>Formato esperado: ruta, fecha, hora, saturacion, tiempo_estimado</small>
                        </div>
                        <button type="submit" class="btn">📤 Subir CSV</button>
                    </form>
                    
                    <div id="upload-status"></div>
                    
                    <div style="margin-top: 15px;">
                        <h5>🔍 Ejemplo de formato CSV:</h5>
                        <pre style="background: #f1f1f1; padding: 10px; border-radius: 5px; font-size: 12px;">
ruta,fecha,hora,saturacion,tiempo_estimado
T1,2024-01-15,08:30,alta,45
A1,2024-01-15,08:35,media,25
U1,2024-01-15,09:00,baja,30</pre>
                    </div>
                    
                    <button class="btn" onclick="procesarDatos()">🔄 Procesar Datos</button>
                    <button class="btn" onclick="exportarDatos()">💾 Exportar Datos</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        
        let map;
        let polylines = [];
        let markers = [];
        
        function initMap() {
            // mapa centrado en Bogotá
            map = new google.maps.Map(document.getElementById('map'), {
                center: { lat: 4.7110, lng: -74.0721 },
                zoom: 12,
                mapTypeId: 'roadmap'
            });
            
            
            map.addControl(new google.maps.NavigationControl());
            
            
            cargarRutasEnMapa();
        }
        
        function cargarRutasEnMapa() {
            
            polylines.forEach(polyline => polyline.setMap(null));
            markers.forEach(marker => marker.setMap(null));
            polylines = [];
            markers = [];
            
            
            const rutaSeleccionada = document.getElementById('ruta-selector').value;
            
            
            const colors = {
                'alta': '#FF0000',
                'media': '#FFA500',
                'baja': '#00FF00'
            };
            
            
            {% for codigo, info in rutas.items() %}
                if (rutaSeleccionada === 'all' || rutaSeleccionada === '{{ codigo }}') {
                    
                    if ({{ info.coordenadas|tojson }}) {
                        const path = {{ info.coordenadas|tojson }};
                        
                        
                        const polyline = new google.maps.Polyline({
                            path: path,
                            geodesic: true,
                            strokeColor: colors['{{ info.saturacion }}'] || '#000000',
                            strokeOpacity: 1.0,
                            strokeWeight: 4
                        });
                        polyline.setMap(map);
                        polylines.push(polyline);
                        
                        
                        if (path.length > 0) {
                            
                            const startMarker = new google.maps.Marker({
                                position: path[0],
                                map: map,
                                title: 'Inicio: {{ info.nombre }}',
                                icon: {
                                    path: google.maps.SymbolPath.CIRCLE,
                                    fillColor: colors['{{ info.saturacion }}'] || '#000000',
                                    fillOpacity: 1,
                                    strokeWeight: 0,
                                    scale: 8
                                }
                            });
                            
                            
                            const startInfoWindow = new google.maps.InfoWindow({
                                content: `<strong>{{ codigo }}</strong><br>{{ info.nombre }}<br>Saturación: {{ info.saturacion }}<br>Tiempo: {{ info.tiempo_estimado }} min`
                            });
                            startMarker.addListener('click', () => {
                                startInfoWindow.open(map, startMarker);
                            });
                            markers.push(startMarker);
                            
                            
                            const endMarker = new google.maps.Marker({
                                position: path[path.length - 1],
                                map: map,
                                title: 'Fin: {{ info.nombre }}',
                                icon: {
                                    path: google.maps.SymbolPath.CIRCLE,
                                    fillColor: colors['{{ info.saturacion }}'] || '#000000',
                                    fillOpacity: 1,
                                    strokeWeight: 0,
                                    scale: 8
                                }
                            });
                            
                            
                            const endInfoWindow = new google.maps.InfoWindow({
                                content: `<strong>{{ codigo }}</strong><br>{{ info.nombre }}<br>Saturación: {{ info.saturacion }}<br>Tiempo: {{ info.tiempo_estimado }} min`
                            });
                            endMarker.addListener('click', () => {
                                endInfoWindow.open(map, endMarker);
                            });
                            markers.push(endMarker);
                        }
                    }
                }
            {% endfor %}
            
            
            if (polylines.length > 0) {
                const bounds = new google.maps.LatLngBounds();
                polylines.forEach(polyline => {
                    polyline.getPath().getArray().forEach(latLng => {
                        bounds.extend(latLng);
                    });
                });
                map.fitBounds(bounds);
            }
        }
        
        function actualizarMapa() {
            cargarRutasEnMapa();
        }

        
        function actualizarRutas() {
            fetch('/api/rutas')
                .then(response => response.json())
                .then(data => {
                    console.log('Rutas actualizadas:', data);
                    location.reload();
                });
        }

        function reportarSaturacion(event) {
            event.preventDefault();
            const ruta = document.getElementById('ruta-reporte').value;
            const nivel = document.getElementById('nivel-saturacion').value;
            
            fetch('/api/reportar', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ruta: ruta, nivel: nivel})
            })
            .then(response => response.json())
            .then(data => {
                alert('✅ Reporte enviado exitosamente');
                actualizarRutas();
            });
        }

        function guardarPerfil(event) {
            event.preventDefault();
            const nombre = document.getElementById('nombre-usuario').value;
            const rutaFrecuente = document.getElementById('ruta-frecuente').value;
            
            fetch('/api/perfil', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({nombre: nombre, ruta_frecuente: rutaFrecuente})
            })
            .then(response => response.json())
            .then(data => {
                alert('👤 Perfil guardado correctamente');
            });
        }

        function toggleNotificaciones() {
            alert('🔔 Notificaciones activadas/desactivadas');
        }

        function verEstadisticas() {
            alert('📊 Mostrando estadísticas detalladas');
        }

        function subirCSV(event) {
            event.preventDefault();
            const formData = new FormData();
            const fileInput = document.getElementById('csv-file');
            
            if (!fileInput.files[0]) {
                alert('❌ Por favor selecciona un archivo CSV');
                return;
            }
            
            formData.append('csv_file', fileInput.files[0]);
            
            const statusDiv = document.getElementById('upload-status');
            statusDiv.innerHTML = '<p>⏳ Subiendo archivo...</p>';
            
            fetch('/api/upload-csv', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    statusDiv.innerHTML = `<div class="success">✅ ${data.message}<br>📊 Registros procesados: ${data.records_count}</div>`;
                    document.getElementById('datos-historicos').textContent = data.total_records + ' registros';
                } else {
                    statusDiv.innerHTML = `<div class="error">❌ Error: ${data.message}</div>`;
                }
            })
            .catch(error => {
                statusDiv.innerHTML = '<div class="error">❌ Error al subir el archivo</div>';
            });
        }

        function procesarDatos() {
            fetch('/api/procesar-datos')
                .then(response => response.json())
                .then(data => {
                    alert(`🔄 Datos procesados: ${data.message}`);
                });
        }

        function exportarDatos() {
            window.open('/api/exportar-datos', '_blank');
        }

        // Actualizar datos cada 30 segundos
        setInterval(actualizarRutas, 30000);
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, rutas=rutas, usuarios=usuarios)

@app.route('/api/rutas')
def api_rutas():
    for ruta in rutas.values():
        ruta['saturacion'] = random.choice(['baja', 'media', 'alta'])
        ruta['tiempo_estimado'] = random.randint(20, 50)
    return jsonify(rutas)

@app.route('/api/reportar', methods=['POST'])
def api_reportar():
    data = request.json
    ruta = data.get('ruta')
    nivel = data.get('nivel')
    
    if ruta in rutas:
        rutas[ruta]['saturacion'] = nivel
        rutas[ruta]['tiempo_estimado'] = random.randint(20, 50)
        return jsonify({'status': 'success', 'message': 'Reporte recibido'})
    
    return jsonify({'status': 'error', 'message': 'Ruta no encontrada'}), 404

@app.route('/api/perfil', methods=['POST'])
def api_perfil():
    data = request.json
    usuario = {
        'nombre': data.get('nombre'),
        'ruta_frecuente': data.get('ruta_frecuente'),
        'fecha_registro': datetime.now().isoformat()
    }
    usuarios.append(usuario)
    return jsonify({'status': 'success', 'message': 'Perfil guardado'})

@app.route('/api/estadisticas')
def api_estadisticas():
    stats = {
        'total_rutas': len(rutas),
        'usuarios_registrados': len(usuarios),
        'reportes_hoy': random.randint(10, 50),
        'ruta_mas_saturada': max(rutas.items(), key=lambda x: x[1]['tiempo_estimado'])[0],
        'datos_historicos': len(datos_historicos)
    }
    return jsonify(stats)

@app.route('/api/upload-csv', methods=['POST'])
def upload_csv():
    try:
        if 'csv_file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No se encontró archivo'}), 400
        
        file = request.files['csv_file']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No se seleccionó archivo'}), 400
        
        if file and file.filename.lower().endswith('.csv'):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            
            df = pd.read_csv(filepath)
            
            
            required_columns = ['ruta', 'fecha', 'hora', 'saturacion', 'tiempo_estimado']
            if not all(col in df.columns for col in required_columns):
                return jsonify({
                    'status': 'error', 
                    'message': f'CSV debe contener columnas: {", ".join(required_columns)}'
                }), 400
            
            
            nuevos_datos = df.to_dict('records')
            datos_historicos.extend(nuevos_datos)
            
            
            actualizar_rutas_con_historicos()
            
            return jsonify({
                'status': 'success',
                'message': 'Archivo CSV procesado exitosamente',
                'records_count': len(nuevos_datos),
                'total_records': len(datos_historicos)
            })
        
        return jsonify({'status': 'error', 'message': 'Archivo debe ser CSV'}), 400
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error procesando archivo: {str(e)}'}), 500

@app.route('/api/procesar-datos')
def procesar_datos():
    try:
        if not datos_historicos:
            return jsonify({'status': 'error', 'message': 'No hay datos históricos para procesar'})
        
        
        df = pd.DataFrame(datos_historicos)
        
        
        stats_por_ruta = df.groupby('ruta').agg({
            'saturacion': lambda x: x.mode()[0] if not x.empty else 'media',
            'tiempo_estimado': 'mean'
        }).to_dict('index')
        
        
        for ruta_code, stats in stats_por_ruta.items():
            if ruta_code in rutas:
                rutas[ruta_code]['saturacion'] = stats['saturacion']
                rutas[ruta_code]['tiempo_estimado'] = int(stats['tiempo_estimado'])
        
        return jsonify({
            'status': 'success',
            'message': f'Procesados {len(datos_historicos)} registros históricos',
            'rutas_actualizadas': len(stats_por_ruta)
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error procesando datos: {str(e)}'})

@app.route('/api/exportar-datos')
def exportar_datos():
    try:
        if not datos_historicos:
            return jsonify({'status': 'error', 'message': 'No hay datos para exportar'})
        
        df = pd.DataFrame(datos_historicos)
        
        
        export_filename = f'datos_historicos_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        export_path = os.path.join(app.config['UPLOAD_FOLDER'], export_filename)
        df.to_csv(export_path, index=False)
        
        return jsonify({
            'status': 'success',
            'message': f'Datos exportados como {export_filename}',
            'records': len(datos_historicos)
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error exportando: {str(e)}'})

def actualizar_rutas_con_historicos():
    """Actualizar rutas actuales basado en datos históricos"""
    if not datos_historicos:
        return
    
    df = pd.DataFrame(datos_historicos)
    
    
    for ruta_code in rutas.keys():
        datos_ruta = df[df['ruta'] == ruta_code]
        if not datos_ruta.empty:
            
            saturacion_freq = datos_ruta['saturacion'].mode()
            if not saturacion_freq.empty:
                rutas[ruta_code]['saturacion'] = saturacion_freq[0]
            
            
            tiempo_promedio = datos_ruta['tiempo_estimado'].mean()
            if not pd.isna(tiempo_promedio):
                rutas[ruta_code]['tiempo_estimado'] = int(tiempo_promedio)

if __name__ == '__main__':
    print("🚌 Iniciando TransportApp...")
    print("📱 Accede a: http://localhost:5000")
    print("🗺️ Google Maps API integrada")
    print("⚙️ Panel de desarrolladores incluido para carga de CSV")
    print("📁 Carpeta de uploads creada en:", os.path.abspath(app.config['UPLOAD_FOLDER']))
    app.run(debug=True, host='0.0.0.0', port=5000)





