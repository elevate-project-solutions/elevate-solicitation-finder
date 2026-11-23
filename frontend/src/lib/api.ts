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

export type SolicitationListResponse = {
    items: Solicitation[];
    total: number;
    page: number;
    page_size: number;
};

export async function getSolicitations(
    page = 1,
    pageSize = 50,
    status = "all",
    search = ""
): Promise<SolicitationListResponse> {
    const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
        status,
        search,
    });

    const response = await fetch(
        `${API_URL}/api/solicitations?${params.toString()}`
    );

    if (!response.ok) {
        throw new Error(
            `Unable to load soliciations: ${response.status}`
        );
    }

    return response.json() as Promise<SolicitationListResponse>;
}

export type SolicitationStats = {
    open_opportunities: number;
    unknown_status: number;
    eligible_opportunities: number;
};

export async function getSolicitationStats(): Promise<SolicitationStats> {
    const response = await fetch(
        `${API_URL}/api/solicitations/stats`
    );

    if (!response.ok) {
        throw new Error(
            `Failed to fetch solicitation stats: ${response.status}`
        );
    }

    return response.json() as Promise<SolicitationStats>;
}