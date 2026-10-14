const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

//describes expected response
export interface HealthResponse {
  status: string;
  environment: string;
}

//sends request to Python backend
export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`);

  //if there is an error, throw an exception
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  //responds with JSON
  return (await response.json()) as HealthResponse;
}
