/**
 * Parses axios or generic error objects to extract a clean string message.
 * 
 * @param {object} error - The error object to parse
 * @returns {string} Friendly error message
 */
export function parseError(error) {
  if (!error) return 'An unknown error occurred.';

  // If it's a string, return it
  if (typeof error === 'string') return error;

  // Handle Axios response errors
  if (error.response) {
    const data = error.response.data;
    if (data && data.error) {
      return data.error;
    }
    if (data && data.message) {
      return data.message;
    }
    return `Error: Server returned code ${error.response.status}`;
  }

  // Handle Axios request errors (no response received)
  if (error.request) {
    return 'No response received from the server. Please verify the backend API is running.';
  }

  // Handle generic JS exceptions
  if (error.message) {
    return error.message;
  }

  return 'A network or system error occurred.';
}
