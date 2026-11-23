import { useEffect, useState } from "react";
import {
    FolderOpen,
    CircleHelp,
    CalendarDays,
} from "lucide-react";

import Sidebar from "../components/Sidebar";
import StatCard from "../components/StatCard";
import OpportunityTable from "../components/OpportunityTable";

import {
    getSolicitations,
    getSolicitationStats,
    type Solicitation,
    type SolicitationStats,
} from "../lib/api";

const PAGE_SIZE = 50;

export default function Dashboard() {
    const [solicitations, setSolicitations] =
        useState<Solicitation[]>([]);

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const [stats, setStats] = 
        useState<SolicitationStats | null>(null);

    const [statsError, setStatsError] = 
        useState<string | null>(null);

    const [status, setStatus] = useState("all");
    const [search, setSearch] = useState("");
    const [page, setPage] = useState(1);
    const [total, setTotal] = useState(0)

    useEffect(() => {
        let active = true;

        async function loadOpportunities(){
            setLoading(true);
            setError(null);

            try{
                const results = await getSolicitations(
                    page,
                    PAGE_SIZE,
                    status,
                    search
                );

                if (active) {
                    setSolicitations(results.items);
                    setTotal(results.total)
                }
            } catch (err) {
                if (active) {
                    setError(
                        err instanceof Error
                        ? err.message
                        : "Unable to load opportunities"
                    );
                }
            } finally {
                if (active) {
                    setLoading(false);
                }
            }
        }

        void loadOpportunities();

        return () => {
            active = false;
        };
    }, [page, status, search]);

    useEffect(() => {
        let active = true;
        
        async function loadStats() {
            try {
                const results = await getSolicitationStats();

                if (active) {
                    setStats(results);
                }
            } catch (err) {
                if (active) {
                    setStatsError(
                        err instanceof Error
                        ? err.message
                        : "Unable to load dashboard stats"
                    );
                }
            }
        }

        void loadStats();

        return () => {
            active = false;
        };
    }, []);

    function handleStatusChange(value: string) {
        setStatus(value);
        setPage(1);
    }

    function handleSearchChange(value: string) {
        setSearch(value);
        setPage(1);
    }

    return (
        <div className="app-shell">
            <Sidebar />

            <main className="dashboard-main">
                <header className="dashboard-header">
                    <div>
                        <span className="eyebrow">
                            YOUR PROCUREMENT WORKSPACE
                        </span>
                        <h1>Welcome back, Ev</h1>
                        <p>Let's find a great opportunity.</p>
                    </div>
                </header>

                {statsError && (
                    <p className="error-message" role="alert">
                        {statsError}
                    </p>
                )}
                    
                <div className="stats-grid">
                    <StatCard
                        title="Open Opportunities"
                        value={stats?.open_opportunities ?? "-"}
                        icon={FolderOpen}
                    />
                    
                    <StatCard
                        title="Unknown Status"
                        value={stats?.unknown_status ?? "-"}
                        icon={CircleHelp}
                    />
                        
                    <StatCard
                        title="30+ Days Until Deadline"
                        value={stats?.eligible_opportunities ?? "-"}
                        icon={CalendarDays}
                    />  
                </div>

                {error && (
                    <p className="error-message" role="alert">
                        {error}
                    </p>
                )}

                <OpportunityTable 
                    solicitations={solicitations}
                    loading={loading}
                    total={total}
                    page={page}
                    pageSize={PAGE_SIZE}
                    status={status}
                    search={search}
                    onStatusChange={handleStatusChange}
                    onSearchChange={handleSearchChange}
                    onPageChange={setPage} 
                />
            </main>
        </div>
    );
}