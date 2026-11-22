import type { LucideIcon } from "lucide-react";

type Props = {
    title: string;
    value: number | string;
    icon: LucideIcon;
};

export default function StatCard({
    title,
    value,
    icon: Icon,
}: Props) {
    return (
        <div className="stat-card">
            <div className="stat-icon">
                <Icon size={21} />
            </div>
            <div className="stat-value">{value}</div>
            <div className="stat-title">{title}</div>
        </div>
    );
}