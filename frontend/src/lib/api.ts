export type DocumentStatus = 
    | "available"
    | "incomplete"
    | "access_required"
    | "not_verified";

export type Solicitation = {
    id: number | string;
    solicitation_number: string | null;
    title: string;
    agency: string | null;
    status: string;
    due_date: string | null;
    source: string | null;
    document_status: DocumentStatus;
};

const API_URL =
    import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export async function getSolicitations(): Promise<Solicitation[]> {
    const response = await fetch(`${API_URL}/api/solicitations`);

    if (!response.ok) {
        throw new Error(
            `Unable to load soliciations (${response.status})`
        );
    }

    const data: unknown = await response.json();

    if (!Array.isArray(data)) {
        throw new Error("Unexpected API response");
    }

    return data as Solicitation[];
}