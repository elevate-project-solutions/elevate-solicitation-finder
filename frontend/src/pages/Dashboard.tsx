import { useEffect, useMemo, useState } from "react";
import {
    FolderOpen,
    FileCheck2,
    FileWarning,
    CalendarDays,
} from "lucide-react";

import Sidebar from "../components/Sidebar";
import StatCard from "../components/StatCard";
import OpportunityTable from "../components/OpportunityTable";
import {
    getSolicitations,
    type Solicitation,
} from "../lib/api";

export default function Dashboard() {
    const [solicitations, setSolicitations] =
        useState<Solicitation[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let active = true;

        async function load(){
            try{
                const results = await getSolicitations();

                if (active) setSolicitations(results);
            } catch (err) {
                if (active) {
                    setError(
                        err instanceof Error
                        ? err.message
                        : "Unable to load opportunities"
                    );
                }
            } finally {
                if (active) setLoading(false);
            }
        }

        void load();

        return () => {
            active = false;
        };
    }, []);

    const stats = useMemo(() => {
        const now = new Date();
        const nextWeek = new Date(now);
        nextWeek.setDate(now.getDate() + 7);

        const open = solicitations.filter(
            (item) => item.status.toLowerCase() === "open"
        );

        return {
            open: open.length,
            ready: open.filter(
                (item) => item.document_status === "available"
            ).length,
            needsDocuments: open.filter(
                (item) =>
                    item.document_status === "incomplete" ||
                    item.document_status === "access_required"
            ).length,
            deadlines: open.filter((item) => {
                if (!item.due_date) return false;

                const deadline = new Date(item.due_date);
                return deadline >= now && deadline <= nextWeek;
            }).length,
        };
    }, [solicitations]);

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

                {loading && <p role="status">Loading opportunities...</p>}
                {error && <p className="error-message" role="alert">{error}</p>}

                {!loading && !error && (
                    <>
                        <div className="stats-grid">
                            <StatCard
                                title="Open Opportunities"
                                value={stats.open}
                                icon={FolderOpen}
                            />
                            <StatCard
                                title="Ready for Review"
                                value={stats.ready}
                                icon={FileCheck2}
                            />
                            <StatCard
                                title="Documents Needed"
                                value={stats.needsDocuments}
                                icon={FileWarning}
                            />
                            <StatCard
                                title="Deadlines Within 7 Days"
                                value={stats.deadlines}
                                icon={CalendarDays}
                            />
                            </div>
                            
                            <OpportunityTable solicitations={solicitations} />
                        </>
                )}
            </main>
        </div>
    );
}