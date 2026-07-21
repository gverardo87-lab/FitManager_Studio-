import axios from "axios";

/** Solo una risposta HTTP 404 certifica che l'entità non esiste. */
export function isNotFoundError(error: unknown): boolean {
  return axios.isAxiosError(error) && error.response?.status === 404;
}

