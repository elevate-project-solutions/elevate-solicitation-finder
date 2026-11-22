
import { useMemo, useState } from "react";
import type { Solicitation, DocumentStatus } from "../lib/api";

type Props = {
  solicitations: Solicitation[];
};

const documentLabels: Record<DocumentStatus, string> = {
  available: "Available",
  incomplete: "Incomplete",
  access_required: "Access needed",
  not_verified: "Not verified",
};

export default function OpportunityTable({
  solicitations,
}: Props) {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();

    return solicitations.filter((item) => {
      const matchesSearch = [
        item.title,
        item.agency,
        item.solicitation_number,
      ]
        .filter(Boolean)
        .some((value) =>
          String(value).toLowerCase().includes(query)
        );

      const matchesStatus =
        status === "all" ||
        item.status.toLowerCase() === status;

      return matchesSearch && matchesStatus;
    });
  }, [solicitations, search, status]);

  return (
    <section className="opportunity-panel">
      <div className="panel-heading">
        <div>
          <h2>Find Opportunities</h2>
          <p>Explore government solicitations and documents.</p>
        </div>
        <span className="result-count">
          {filtered.length} results
        </span>
      </div>

      <div className="table-controls">
        <input
          aria-label="Search opportunities"
          placeholder="Search titles, agencies, solicitation numbers..."
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />

        <select
          aria-label="Filter by status"
          value={status}
          onChange={(event) => setStatus(event.target.value)}
        >
          <option value="all">All statuses</option>
          <option value="open">Open</option>
          <option value="closed">Closed</option>
          <option value="awarded">Awarded</option>
          <option value="unknown">Unknown</option>
        </select>
      </div>

      <div className="table-scroll">
        <table className="opportunity-table">
          <thead>
            <tr>
              <th>Opportunity</th>
              <th>Agency</th>
              <th>Deadline</th>
              <th>Documents</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((item) => {
              const docStatus =
                item.document_status ?? "not_verified";

              return (
                <tr key={item.id}>
                  <td>
                    <strong>{item.title}</strong>
                    <small>
                      {item.solicitation_number ?? "—"}
                    </small>
                  </td>
                  <td>{item.agency ?? "—"}</td>
                  <td>
                    {item.due_date
                      ? item.due_date.slice(0, 10)
                      : "Not listed"}
                  </td>
                  <td>
                    <span
                      className={`document-pill doc-${docStatus}`}
                    >
                      {documentLabels[docStatus]}
                    </span>
                  </td>
                  <td>{item.status}</td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {filtered.length === 0 && (
          <p className="empty-state">
            No opportunities match your filters.
          </p>
        )}
      </div>
    </section>
  );
}
