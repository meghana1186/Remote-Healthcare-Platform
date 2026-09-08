const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function request(path: string, init?: RequestInit) {
  const response = await fetch(`${API_URL}${path}`, init);
  if (!response.ok) throw new Error(`API ${response.status}`);
  return response.json();
}

export async function runTriage(message: string, language = "English") {
  return request("/triage", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({message, language})
  });
}

export async function getPatients() { return request("/demo/patients"); }
export async function getProviders() { return request("/demo/providers"); }
export async function getHealth() { return request("/status"); }
