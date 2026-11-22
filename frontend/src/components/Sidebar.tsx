import {
    LayoutDashboard,
    Search,
    Users,
    CalendarDays,
    Settings,
    Flower2,
 } from "lucide-react";

const navigation = [
    { label: "Dashboard", icon: LayoutDashboard, active: true },
    { label: "Opportunities", icon: Search, active: false },
    { label: "Contractors", icon: Users, active: false },
    { label: "Deadlines", icon: CalendarDays, active: false },
    { label: "Settings", icon: Settings, active: false },
];

export default function Sidebar() {
    return (
        <aside className="sidebar">
            <div className="sidebar-brand">
                <div className="brand-icon">
                    <Flower2 size={25} />
                </div>
                <div>
                    <strong>Elevate</strong>
                    <span>Solicitation Finder</span>
                </div>
            </div>

            <nav className="sidebar-nav" aria-label="Main navigation">
                {navigation.map(({ label, icon: Icon, active }) => (
                    <div
                        key={label}
                        className={`nav-item ${active ? "active" : ""}`}
                        aria-current={active ? "page" : undefined}
                    >
                        <Icon size={19} />
                        <span>{label}</span>
                    </div>
                ))}
            </nav>

            <div className="sidebar-footer">
                <Flower2 size={22} />
                <p>Beautiful opporunities bloom here.</p>
            </div>
        </aside>
    );
}