/**
 * auth.js - Sistema de autenticación con localStorage
 * CyberLearn - Plataforma educativa de ciberseguridad
 *
 * Funciones: register, login, logout, checkAuth,
 *            getCurrentUser, getProgress, saveProgress, getUserStats
 */

'use strict';

/* ================================================================
   Claves de almacenamiento
================================================================ */
const AUTH_KEY     = 'cyberlearn_users';
const SESSION_KEY  = 'cyberlearn_session';
const PROGRESS_KEY = 'cyberlearn_progress';

/* ================================================================
   Inicialización
================================================================ */

/**
 * Inicializa el almacenamiento con un usuario demo si no existe.
 */
function initStorage() {
  if (!localStorage.getItem(AUTH_KEY)) {
    const demoUsers = [
      {
        id:        1,
        username:  'demo',
        email:     'demo@cyberlearn.com',
        password:  btoa('Demo1234!'),   // Codificación simple para demo
        createdAt: new Date().toISOString(),
        avatar:    'D',
      },
    ];
    localStorage.setItem(AUTH_KEY, JSON.stringify(demoUsers));
  }

  // Inicializar progreso si no existe
  if (!localStorage.getItem(PROGRESS_KEY)) {
    localStorage.setItem(PROGRESS_KEY, JSON.stringify({}));
  }
}

/* ================================================================
   Helpers internos
================================================================ */

/**
 * Obtiene todos los usuarios registrados.
 * @returns {Array}
 */
function _getUsers() {
  try {
    return JSON.parse(localStorage.getItem(AUTH_KEY)) || [];
  } catch {
    return [];
  }
}

/**
 * Guarda la lista de usuarios.
 * @param {Array} users
 */
function _saveUsers(users) {
  localStorage.setItem(AUTH_KEY, JSON.stringify(users));
}

/**
 * Genera un ID único incremental.
 * @param {Array} users
 * @returns {number}
 */
function _nextId(users) {
  if (users.length === 0) return 1;
  return Math.max(...users.map(u => u.id)) + 1;
}

/**
 * Genera la letra/emoji del avatar a partir del nombre de usuario.
 * @param {string} username
 * @returns {string}
 */
function _avatarChar(username) {
  return username.charAt(0).toUpperCase();
}

/* ================================================================
   Validaciones
================================================================ */

/**
 * Valida el nombre de usuario (3-20 caracteres alfanuméricos y guión bajo).
 * @param {string} username
 * @returns {{ valid: boolean, message: string }}
 */
function _validateUsername(username) {
  if (!username || typeof username !== 'string') {
    return { valid: false, message: 'El nombre de usuario es obligatorio.' };
  }
  const trimmed = username.trim();
  if (trimmed.length < 3 || trimmed.length > 20) {
    return { valid: false, message: 'El nombre de usuario debe tener entre 3 y 20 caracteres.' };
  }
  if (!/^[a-zA-Z0-9_]+$/.test(trimmed)) {
    return { valid: false, message: 'El nombre de usuario solo puede contener letras, números y guiones bajos.' };
  }
  return { valid: true, message: '' };
}

/**
 * Valida el formato del correo electrónico.
 * @param {string} email
 * @returns {{ valid: boolean, message: string }}
 */
function _validateEmail(email) {
  if (!email || typeof email !== 'string') {
    return { valid: false, message: 'El correo electrónico es obligatorio.' };
  }
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email.trim())) {
    return { valid: false, message: 'Introduce un correo electrónico válido.' };
  }
  return { valid: true, message: '' };
}

/**
 * Función segura para codificar cadenas (incluyendo tildes y caracteres especiales).
 * @param {string} str
 * @returns {string}
 */
function _safeHash(str) {
  try {
    return btoa(encodeURIComponent(str));
  } catch (e) {
    try {
      return btoa(str);
    } catch (e2) {
      return str;
    }
  }
}

/**
 * Valida la contraseña:
 *  - Mínimo 6 caracteres
 * @param {string} password
 * @returns {{ valid: boolean, message: string, strength: 'weak'|'medium'|'strong' }}
 */
function _validatePassword(password) {
  if (!password || typeof password !== 'string') {
    return { valid: false, message: 'La contraseña es obligatoria.', strength: 'weak' };
  }

  if (password.length < 6) {
    return { valid: false, message: 'La contraseña debe tener al menos 6 caracteres.', strength: 'weak' };
  }

  return { valid: true, message: '', strength: _passwordStrength(password) };
}

/**
 * Calcula la fortaleza de una contraseña sin validarla.
 * @param {string} password
 * @returns {'weak'|'medium'|'strong'}
 */
function _passwordStrength(password) {
  if (!password) return 'weak';
  let score = 0;
  if (password.length >= 6)             score++;
  if (password.length >= 10)            score++;
  if (/[A-Z]/.test(password))          score++;
  if (/[0-9]/.test(password))          score++;
  if (/[^a-zA-Z0-9]/.test(password))  score++;

  if (score <= 2) return 'weak';
  if (score <= 3) return 'medium';
  return 'strong';
}

/* ================================================================
   API pública
================================================================ */

/**
 * Registra un nuevo usuario.
 * @param {string} username
 * @param {string} email
 * @param {string} password
 * @returns {{ success: boolean, message: string }}
 */
function register(username, email, password) {
  // Validar campos
  const usernameCheck = _validateUsername(username);
  if (!usernameCheck.valid) return { success: false, message: usernameCheck.message };

  const emailCheck = _validateEmail(email);
  if (!emailCheck.valid) return { success: false, message: emailCheck.message };

  const passwordCheck = _validatePassword(password);
  if (!passwordCheck.valid) return { success: false, message: passwordCheck.message };

  const users = _getUsers();
  const lowerUsername = username.trim().toLowerCase();
  const lowerEmail    = email.trim().toLowerCase();

  // Verificar duplicados
  const duplicateUsername = users.find(u => u.username.toLowerCase() === lowerUsername);
  if (duplicateUsername) {
    return { success: false, message: 'El nombre de usuario ya está en uso.' };
  }

  const duplicateEmail = users.find(u => u.email.toLowerCase() === lowerEmail);
  if (duplicateEmail) {
    return { success: false, message: 'El correo electrónico ya está registrado.' };
  }

  // Crear nuevo usuario
  const newUser = {
    id:        _nextId(users),
    username:  username.trim(),
    email:     email.trim().toLowerCase(),
    password:  _safeHash(password),   // Codificación segura
    createdAt: new Date().toISOString(),
    avatar:    _avatarChar(username),
  };

  users.push(newUser);
  _saveUsers(users);

  return { success: true, message: '¡Cuenta creada correctamente! Ahora puedes iniciar sesión.' };
}

/**
 * Inicia sesión con nombre de usuario/email y contraseña.
 * @param {string} usernameOrEmail
 * @param {string} password
 * @returns {{ success: boolean, message: string, user?: object }}
 */
function login(usernameOrEmail, password) {
  if (!usernameOrEmail || !password) {
    return { success: false, message: 'Por favor, completa todos los campos.' };
  }

  const users        = _getUsers();
  const identifier   = usernameOrEmail.trim().toLowerCase();
  const safeEncoded  = _safeHash(password);
  let rawBtoa = '';
  try { rawBtoa = btoa(password); } catch(e) {}

  // Buscar usuario por nombre de usuario o email
  const user = users.find(
    u => u.username.toLowerCase() === identifier || u.email.toLowerCase() === identifier
  );

  if (!user) {
    return { success: false, message: 'Usuario o contraseña incorrectos.' };
  }

  // Verificar contraseña (soporta tanto _safeHash como btoa directo legado)
  if (user.password !== safeEncoded && user.password !== rawBtoa) {
    return { success: false, message: 'Usuario o contraseña incorrectos.' };
  }

  // Crear sesión
  const session = {
    userId:    user.id,
    username:  user.username,
    email:     user.email,
    avatar:    user.avatar,
    loginTime: new Date().toISOString(),
  };

  localStorage.setItem(SESSION_KEY, JSON.stringify(session));
  // Compatibilidad cruzada con otras vistas
  localStorage.setItem('cybersec_user', JSON.stringify({
    username: user.username,
    email: user.email,
    userId: user.id
  }));

  return { success: true, message: `¡Bienvenido, ${user.username}!`, user: session };
}

/**
 * Cierra la sesión y redirige a index.html.
 */
function logout() {
  localStorage.removeItem(SESSION_KEY);
  localStorage.removeItem('cybersec_user');
  sessionStorage.removeItem('cybersec_user');
  window.location.href = 'index.html';
}

/**
 * Verifica si hay sesión iniciada (booleano).
 */
function isLoggedIn() {
  return !!getCurrentUser();
}

/**
 * Alias de getCurrentUser para getSession.
 */
function getSession() {
  return getCurrentUser();
}

/**
 * Verifica si el usuario está autenticado.
 * Si no lo está, redirige a index.html.
 * @returns {object|null} El objeto de sesión si está autenticado.
 */
function checkAuth() {
  const session = getCurrentUser();
  if (!session) {
    window.location.href = 'index.html';
    return null;
  }
  return session;
}

/**
 * Devuelve el usuario de la sesión actual o null.
 * @returns {object|null}
 */
function getCurrentUser() {
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    if (raw) return JSON.parse(raw);
    const fallback = localStorage.getItem('cybersec_user');
    return fallback ? JSON.parse(fallback) : null;
  } catch {
    return null;
  }
}

/* ================================================================
   Progreso y estadísticas
================================================================ */

/**
 * Obtiene todos los datos de progreso de un usuario o del usuario activo actual.
 * @param {number|string} [userId]
 * @returns {object}
 */
function getProgress(userId) {
  try {
    const session = getCurrentUser();
    const uid = userId || (session ? (session.userId || session.username || 1) : 1);
    const all = JSON.parse(localStorage.getItem(PROGRESS_KEY)) || {};
    const defaultData = {
      quizScores:        [],
      gamesCompleted:    0,
      quizzesCompleted:  0,
      glossaryViewed:    [],
      totalPoints:       0,
      points:            0,
      streak:            1,
      quizBestScore:     0,
      history:           []
    };
    const userProg = all[uid] || {};
    return Object.assign({}, defaultData, userProg);
  } catch {
    return {
      quizScores: [],
      gamesCompleted: 0,
      quizzesCompleted: 0,
      glossaryViewed: [],
      totalPoints: 0,
      points: 0,
      streak: 1,
      quizBestScore: 0,
      history: []
    };
  }
}

/**
 * Guarda/actualiza datos de progreso.
 * Acepta:
 * 1) saveProgress(progressObject)
 * 2) saveProgress(userId, type, data)
 * 3) saveProgress(type, data)
 */
function saveProgress(param1, param2, param3) {
  try {
    const session = getCurrentUser();
    const all = JSON.parse(localStorage.getItem(PROGRESS_KEY)) || {};

    // Caso 1: se pasa un objeto completo de progreso (usado por quiz.html)
    if (typeof param1 === 'object' && param1 !== null) {
      const uid = (session ? (session.userId || session.username || 1) : 1);
      const current = all[uid] || {};
      all[uid] = Object.assign({}, current, param1);
      // sincronizar campos equivalentes
      if (all[uid].points !== undefined) all[uid].totalPoints = all[uid].points;
      if (all[uid].totalPoints !== undefined && all[uid].points === undefined) all[uid].points = all[uid].totalPoints;
      localStorage.setItem(PROGRESS_KEY, JSON.stringify(all));
      return;
    }

    // Caso 2 y 3: (userId, type, data) o (type, data)
    let uid, type, data;
    if (typeof param1 === 'string' && (param2 !== undefined)) {
      type = param1;
      data = param2;
      uid = (session ? (session.userId || session.username || 1) : 1);
    } else {
      uid = param1 || (session ? (session.userId || session.username || 1) : 1);
      type = param2;
      data = param3 || {};
    }

    const progress = all[uid] || {
      quizScores:     [],
      gamesCompleted: 0,
      quizzesCompleted: 0,
      glossaryViewed: [],
      totalPoints:    0,
      points:         0,
      streak:         1,
      quizBestScore:  0,
      history:        []
    };

    const now = new Date().toISOString();

    switch (type) {
      case 'quiz': {
        const { quizId, score, total } = data;
        if (!Array.isArray(progress.quizScores)) progress.quizScores = [];
        const existing = progress.quizScores.findIndex(q => q.quizId === quizId);
        const entry    = { quizId, score, total, date: now };
        if (existing >= 0) {
          if (score > progress.quizScores[existing].score) {
            progress.quizScores[existing] = entry;
            progress.totalPoints = (progress.totalPoints || 0) + (score - (progress.quizScores[existing]?.score || 0)) * 10;
          }
        } else {
          progress.quizScores.push(entry);
          progress.totalPoints = (progress.totalPoints || 0) + (score || 0) * 10;
        }
        progress.quizzesCompleted = (progress.quizzesCompleted || 0) + 1;
        progress.points = progress.totalPoints;
        if (score && (!progress.quizBestScore || score > progress.quizBestScore)) {
          progress.quizBestScore = score;
        }
        break;
      }

      case 'game': {
        const { gameId, time } = data;
        progress.gamesCompleted = (typeof progress.gamesCompleted === 'number' ? progress.gamesCompleted : 0) + 1;
        progress.totalPoints = (progress.totalPoints || 0) + 50;
        progress.points = progress.totalPoints;
        break;
      }

      case 'glossary': {
        const { termId } = data;
        if (!Array.isArray(progress.glossaryViewed)) progress.glossaryViewed = [];
        if (!progress.glossaryViewed.includes(termId)) {
          progress.glossaryViewed.push(termId);
          progress.totalPoints = (progress.totalPoints || 0) + 2;
          progress.points = progress.totalPoints;
        }
        break;
      }

      default:
        console.warn(`saveProgress: tipo desconocido "${type}"`);
    }

    all[uid] = progress;
    localStorage.setItem(PROGRESS_KEY, JSON.stringify(all));
  } catch (err) {
    console.error('Error al guardar progreso:', err);
  }
}

/**
 * Calcula y devuelve estadísticas resumidas del usuario.
 * @param {number} userId
 * @returns {{ quizBestScore: number, gamesCompleted: number, glossaryViewed: number, totalPoints: number }}
 */
function getUserStats(userId) {
  const progress = getProgress(userId);

  const quizBestScore = progress.quizScores.length > 0
    ? Math.max(...progress.quizScores.map(q => q.total > 0 ? Math.round((q.score / q.total) * 100) : 0))
    : 0;

  return {
    quizBestScore,
    gamesCompleted: progress.gamesCompleted.length,
    glossaryViewed: progress.glossaryViewed.length,
    totalPoints:    progress.totalPoints,
  };
}

/**
 * Calcula la fortaleza de una contraseña (utilidad expuesta para formularios).
 * @param {string} password
 * @returns {'weak'|'medium'|'strong'}
 */
function checkPasswordStrength(password) {
  return _passwordStrength(password);
}

/* ================================================================
   Inicializar al cargar el script
================================================================ */
initStorage();

/* ================================================================
   Exportar como objeto global window.Auth
================================================================ */
window.Auth = {
  register,
  login,
  logout,
  checkAuth,
  isLoggedIn,
  getSession,
  getCurrentUser,
  getProgress,
  saveProgress,
  getUserStats,
  checkPasswordStrength,
  validatePassword: _validatePassword,
  validateUsername: _validateUsername,
  validateEmail:    _validateEmail,
};
