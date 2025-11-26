# OvenMediaEngine Web UI

Una interfaz web moderna e intuitiva para configurar y gestionar el servidor de streaming OvenMediaEngine.

![OvenMediaEngine Web UI](https://img.shields.io/badge/Estado-Listo-success)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)

## Características

✨ **Interfaz Moderna** - Hermoso tema oscuro con efectos glassmorphism y animaciones suaves  
🔐 **Segura** - Autenticación JWT con control de acceso basado en roles (Admin, Operador, Visor)  
📊 **Dashboard en Tiempo Real** - Monitorea el estado del servidor, streams y aplicaciones de un vistazo  
🎛️ **Configuración Completa** - Gestiona todas las configuraciones de OvenMediaEngine mediante formularios intuitivos  
📝 **Control de Versiones** - Snapshots de configuración con capacidad de rollback  
🔍 **Registro de Auditoría** - Rastro completo de auditoría de todos los cambios de configuración  
🚀 **REST API** - Comunicación con OvenMediaEngine vía su REST API  
📱 **Responsive** - Funciona perfectamente en escritorio, tablet y móvil  

## Arquitectura

### Backend (Flask)
- **Modelos**: User, ConfigurationSnapshot, AuditLog
- **Servicios**: Parser XML, Cliente API OME, Gestor de Configuración
- **Blueprints API**: Auth, Server, VirtualHosts, Applications, Streams, Logs

### Frontend
- **Sistema de Diseño**: CSS moderno con tokens de diseño
- **Autenticación**: Autenticación segura basada en JWT
- **UI Dinámica**: JavaScript vanilla con Fetch API
- **Componentes**: Cards, Formularios, Tablas, Modales, Toasts

## Instalación

### Requisitos Previos
- Python 3.8+
- OvenMediaEngine instalado y ejecutándose
- REST API de OvenMediaEngine habilitada

### Configuración

1. **Clonar el repositorio**
```bash
cd /Volumes/DatosApp/Proyects/OvenMediaUI
```

2. **Crear entorno virtual**
```bash
python3 -m venv venv
source venv/bin/activate  # En Mac/Linux
# venv\Scripts\activate  # En Windows
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

Variables de entorno requeridas:
- `OME_SERVER_XML_PATH`: Ruta a Server.xml (default: `/usr/share/ovenmediaengine/conf/Server.xml`)
- `OME_API_URL`: URL de la API de OvenMediaEngine (default: `http://localhost:8081`)
- `OME_API_ACCESS_TOKEN`: Token de acceso para la API de OME
- `SECRET_KEY`: Clave secreta de Flask (¡cambiar en producción!)
- `JWT_SECRET_KEY`: Clave secreta JWT (¡cambiar en producción!)

5. **Inicializar base de datos**
```bash
python app.py
```

Esto hará:
- Crear la base de datos SQLite
- Crear las tablas
- Agregar usuario admin por defecto (usuario: `admin`, contraseña: `admin123`)

6. **Ejecutar la aplicación**
```bash
# Desarrollo
python app.py

# Producción (con Gunicorn)
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

7. **Acceder a la interfaz**
Abre tu navegador y navega a `http://localhost:5000`

Credenciales por defecto:
- Usuario: `admin`
- Contraseña: `admin123`

⚠️ **IMPORTANTE**: ¡Cambia la contraseña por defecto inmediatamente después del primer login!

## Uso

### Dashboard
- Ver estado del servidor y estadísticas
- Monitorear streams y aplicaciones activas
- Revisar logs de actividad reciente

### Configuración del Servidor
- Ver y editar configuración Server.xml
- Crear snapshots de configuración
- Revertir a configuraciones previas
- Validar cambios antes de aplicar

### Virtual Hosts
- Crear, actualizar y eliminar virtual hosts
- Configurar nombres de host y ajustes
- Ver aplicaciones dentro de cada virtual host

### Aplicaciones
- Gestionar aplicaciones de streaming
- Configurar providers (RTMP, WebRTC, etc.)
- Configurar publishers y streams de salida

### Monitoreo
- Ver logs de auditoría con filtros
- Rastrear cambios de configuración
- Monitorear actividad de usuarios

## Seguridad

### Autenticación
- Autenticación basada en JWT
- Gestión de sesiones
- Renovación automática de tokens

### Autorización
Tres roles de usuario con diferentes permisos:
- **Admin**: Acceso completo incluyendo gestión de usuarios
- **Operador**: Acceso de lectura y escritura a configuraciones
- **Visor**: Acceso solo de lectura

### Rastro de Auditoría
Todas las acciones se registran con:
- Identificación del usuario
- Marca de tiempo
- Tipo de acción
- Recurso afectado
- Dirección IP y user agent

## Desarrollo

### Estructura del Proyecto
```
OvenMediaUI/
├── app.py                 # Aplicación principal Flask
├── config.py              # Configuraciones
├── requirements.txt       # Dependencias Python
├── models/                # Modelos de base de datos
│   ├── user.py
│   ├── configuration.py
│   └── audit.py
├── services/              # Lógica de negocio
│   ├── xml_parser.py
│   ├── ome_client.py
│   └── config_manager.py
├── api/                   # Blueprints API
│   ├── auth.py
│   ├── server.py
│   ├── virtualhosts.py
│   ├── applications.py
│   ├── streams.py
│   └── logs.py
├── templates/             # Plantillas HTML
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── virtualhosts.html
│   └── monitoring.html
└── static/                # Recursos estáticos
    ├── css/
    │   └── main.css
    └── js/
        └── app.js
```

### Ejecutar Pruebas
```bash
pytest tests/ -v --cov=.
```

## Despliegue con Docker

```bash
docker build -t ome-web-ui .
docker run -d -p 5000:5000 \
  -e OME_API_URL=http://tu-servidor-ome:8081 \
  -e OME_API_ACCESS_TOKEN=tu_token \
  ome-web-ui
```

## Contribuir

¡Las contribuciones son bienvenidas! No dudes en enviar un Pull Request.

## Licencia

Licencia MIT - ver archivo LICENSE para detalles

## Soporte

Para problemas y preguntas:
- Abre un issue en GitHub
- Consulta la documentación de OvenMediaEngine: https://docs.ovenmediaengine.com/

## Créditos

Construido con:
- [Flask](https://flask.palletsprojects.com/) - Framework web
- [OvenMediaEngine](https://github.com/AirenSoft/OvenMediaEngine) - Servidor de streaming
- [Font Awesome](https://fontawesome.com/) - Iconos
- [Inter Font](https://rsms.me/inter/) - Tipografía
