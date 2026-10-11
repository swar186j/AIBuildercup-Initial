export type GovernmentService = {
  id: string;
  name: string;
  description: string;
  status: string;
};

export type ServiceListResponse = {
  services: GovernmentService[];
};

export async function fetchServices(): Promise<GovernmentService[]> {
  const response = await fetch("/api/services");

  if (!response.ok) {
    throw new Error(`Services API returned ${response.status}`);
  }

  const data: ServiceListResponse = await response.json();
  return data.services;
}