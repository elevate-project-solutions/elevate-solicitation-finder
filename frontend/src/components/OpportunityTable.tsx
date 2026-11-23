
import type { Solicitation, DocumentStatus } from "../lib/api";

type Props = {
  solicitations: Solicitation[];
  loading: boolean;
  total: number;
  page: number;
  pageSize: number;
  search: string;
  onSearchChange: (value: string) => void;
  onPageChange: (page: number) => void;
};

const documentLabels: Record<DocumentStatus, string> = {
  available: "Available",
  incomplete: "Incomplete",
  access_required: "Access needed",
  not_verified: "Not verified",
};

export default function OpportunityTable({
  solicitations,
  loading,
  total,
  page,
  pageSize,
  search,
  onSearchChange,
  onPageChange,
}: Props) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const firstResult =
    total === 0 ? 0 : (page - 1) * pageSize + 1;

  const lastResult = Math.min(page * pageSize, total);

  return (
    <section className="opportunity-panel">
      <div className="panel-heading">
        <div>
          <h2>Find Opportunities</h2>
          <p>Explore government solicitations and documents.</p>
        </div>

        <span className="result-count">
          {loading ? "Loading..." : `${total} results`}
        </span>
      </div>

      <div className="table-controls">
        <input
          aria-label="Search opportunities"
          placeholder="Search titles, agencies, solicitation numbers..."
          value={search}
          onChange={(event) =>
            onSearchChange(event.target.value)
          }
        />
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
            {!loading &&
              solicitations.map((item) => {
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

        {loading && (
          <p className="empty-state" role="status">
            Loading opportunities...
          </p>
        )}

        {!loading && solicitations.length === 0 && (
          <p className="empty-state">
            No opportunities match your filters.
          </p>
        )}
      </div>

      <div
        className="table-pagination"
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "12px",
          paddingTop: "20px",
        }}
      >
        <span className="result-count">
          {loading
            ? "Loading..."
            : `Showing ${firstResult}–${lastResult} of ${total}`}
        </span>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
          }}
        >
          <button
            type="button"
            disabled={loading || page <= 1}
            onClick={() => onPageChange(page - 1)}
          >
            Previous
          </button>

          <span>
            Page {page} of {totalPages}
          </span>

          <button
            type="button"
            disabled={loading || page >= totalPages}
            onClick={() => onPageChange(page + 1)}
          >
            Next
          </button>
        </div>
      </div>
    </section>
  );
}
