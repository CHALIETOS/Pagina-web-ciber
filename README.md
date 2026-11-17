# 🛡️ CyberLearn - Plataforma Educativa e Interactiva de Ciberseguridad

Plataforma web educativa e interactiva sobre ciberseguridad, diseñada con estética cyberpunk/hacker dark theme (Matrix style) y pensada para todos los niveles: desde principiantes hasta entusiastas y profesionales técnicos.

Alojada en GitHub Pages: **[https://CHALIETOS.github.io/Pagina-web-ciber/](https://CHALIETOS.github.io/Pagina-web-ciber/)**

---

## 🚀 Características Principales

### 1. 🔐 Sistema de Autenticación Local
- Registro e inicio de sesión funcional sin servidor backend (aprovechando `localStorage`).
- Medidor de seguridad de contraseñas en tiempo real (requisitos de mayúsculas, números, caracteres especiales y longitud).
- Persistencia de progreso, puntajes y racha de aprendizaje para cada usuario.
- Cuenta de prueba preconfigurada:
  - **Usuario:** `demo`
  - **Contraseña:** `Demo1234!`

### 2. 🧠 Quiz Interactivo de Ciberseguridad
- **20 preguntas completas** sobre conceptos clave (phishing, inyección SQL, XSS, ransomware, criptografía, 2FA, firewalls, etc.).
- Temporizador interactivo de **30 segundos** por pregunta.
- Retroalimentación inmediata con explicación técnica tras cada respuesta.
- Pantalla final de resultados con desglose, porcentaje, puntuación y clasificación por rango (Principiante, Intermedio, Avanzado, Experto).

### 3. 📚 Glosario de Términos de Ciberseguridad
- **Más de 50 términos** esenciales explicados en español claro y conciso.
- Buscador en tiempo real y filtrado por abecedario (A-Z).
- Categorización por etiquetas temáticas:
  - *Ataques*
  - *Defensas*
  - *Protocolos*
  - *Herramientas*
  - *Conceptos*
- Indicador de nivel de dificultad para cada término.

### 4. 🐛 Caza la Vulnerabilidad en el Código
- **8 desafíos progresivos** con fragmentos de código real (Python, JavaScript/Node.js).
- Análisis interactivo de vulnerabilidades críticas:
  - Inyección SQL (SQLi)
  - Cross-Site Scripting (XSS)
  - Credenciales hardcodeadas
  - Inyección de comandos del sistema
  - Hashing inseguro de contraseñas (MD5)
  - Path Traversal
  - IDOR (Insecure Direct Object Reference)
  - Falla en validación de tokens JWT
- Sistema de pistas, puntuación y explicación detallada de cómo corregir cada fallo (remediación segura).

---

## 📂 Estructura del Proyecto

```text
Pagina-web-ciber/
├── index.html            # Pantalla de login / registro con efecto Matrix Canvas
├── dashboard.html        # Panel principal con estadísticas, tips y acceso a módulos
├── quiz.html             # Módulo de quiz interactivo con temporizador
├── glosario.html         # Diccionario interactivo y buscador de términos
├── vulnerabilidades.html # Juego interactivo de análisis de código vulnerable
├── css/
│   └── style.css         # Estilos globales cyberpunk, animaciones y diseño responsivo
├── js/
│   └── auth.js           # Lógica de autenticación, sesiones y progreso en localStorage
└── README.md             # Documentación del proyecto
```

---

## 🛠️ Tecnologías Utilizadas

- **HTML5 semántico**
- **CSS3 puro** (Variables CSS, Flexbox, CSS Grid, animaciones y diseño responsivo)
- **JavaScript (Vanilla JS - ES6+)** (Canvas API para animación Matrix, manipulación DOM, almacenamiento local con `localStorage`)
- **Git & GitHub Pages** para control de versiones y despliegue estático gratuito.

---

## 👥 Autor

- **Usuario:** [@CHALIETOS](https://github.com/CHALIETOS)
- **Repositorio:** [Pagina-web-ciber](https://github.com/CHALIETOS/Pagina-web-ciber)
