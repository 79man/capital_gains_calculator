// services/api.js
// const API_BASE_URL = "http://localhost:8000/api";
const API_BASE_URL = import.meta.env.PROD
  ? import.meta.env.VITE_API_BASE_URL
  : "http://localhost:8000/api";

console.log(`API_BASE_URL=${API_BASE_URL}`);

export async function calculateCapitalGains(formData) {
  try {
    const response = await fetch(`${API_BASE_URL}/calculate`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || "Calculation failed");
    }

    return response.blob(); // Returns zip/csv file
  } catch (error) {
    throw new Error(error.message || "Error Invoking Calculate API");
  }
}
