import axios from "axios";

// Использовать относительный URL в продакшене (nginx proxy) или абсолютный URL в разработке
const baseURL = import.meta.env.PROD ? "" : "http://localhost:8000/";

// Глобальный callback выхода - будет установлен AuthContext
let globalLogoutCallback: (() => void) | null = null;

export const setLogoutCallback = (callback: () => void) => {
  globalLogoutCallback = callback;
};

const client = axios.create({
  baseURL,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      // Если это уже запрос на обновление токена, который не удался, выйти немедленно
      if (originalRequest.url === "/auth/token/refresh") {
        // Очистить cookies аутентификации
        document.cookie =
          "access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
        document.cookie =
          "refresh_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";

        // Вызвать callback выхода, если доступен
        if (globalLogoutCallback) {
          globalLogoutCallback();
        }

        // Перенаправить на страницу входа
        if (window.location.pathname !== "/login") {
          window.location.href = "/login";
        }

        return Promise.reject(error);
      }

      // Попытаться обновить токен
      try {
        await client.post("/auth/token/refresh");
        return client(originalRequest);
      } catch (refreshError) {
        // Обновление не удалось - выйти и перенаправить
        document.cookie =
          "access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
        document.cookie =
          "refresh_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";

        if (globalLogoutCallback) {
          globalLogoutCallback();
        }

        if (window.location.pathname !== "/login") {
          window.location.href = "/login";
        }

        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  },
);

export const apiClient = client;
export default client;
