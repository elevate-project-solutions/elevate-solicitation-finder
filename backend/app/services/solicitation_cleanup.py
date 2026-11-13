from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.models import Solicitation, SolicitationDuplicateCandidate


def normalize(value: str | None) -> str:
    return " ".join((value or "").casefold().split())

def delete_confirmed_duplicate(
        session: Session,
        *,
        keep_id: int,
        delete_id: int,
) -> None:
    """
    Deletes a confirmed redundant solicitations ONLY when safe.
    
    Does not commit. The caller owns the transaction.
    """

    if keep_id == delete_id:
        raise ValueError("Cannot delete the record being kept")

    keep = session.get(Solicitation, keep_id)
    duplicate = session.get(Solicitation, delete_id)

    if keep is None or duplicate is None:
        raise ValueError("One or both solicitations do not exist")

    same_agency_and_number = (
        bool(keep.agency and duplicate.agency)
        and bool(keep.solicitation_number and duplicate.solicitation_number)
        and normalize(keep.agency) == normalize(duplicate.agency)
        and normalize(keep.solicitation_number)
        == normalize(duplicate.solicitation_number)
    )

    same_url = (
        bool(keep.source_url and duplicate.source_url)
        and keep.source_url.strip() == duplicate.source_url.strip()
    )

    if not (same_agency_and_number or same_url):
        raise ValueError(
            "Records do not share a dupported duplicate identifier"
        )

    # Checks every foreign key that points to solicitations
    # Refuses deletion if any related records exist.
    connection = session.connection()
    inspector = inspect(connection)

    for table_name in inspector.get_table_names():
        for fk in inspector.get_foreign_keys(table_name):
            if fk["referred_table"] != "solicitations":
                continue

            columns = fk["constrained_columns"]
            referred = fk["referred_columns"]

            if len(columns) != 1 or referred != ["id"]:
                raise ValueError(
                    f"Unsupported relationship in {table_name}"
                )

            # Review candidates are handled separately below.
            if table_name == "solicitation_duplicate_candidates":
                continue

            from sqlalchemy import MetaData, Table

            table = Table(
                table_name,
                MetaData(),
                autoload_with=connection,
            )

            related = session.execute(
                select(table.c[columns[0]])
                .where(table.c[columns[0]] == delete_id)
                .limit(1)
            ).first()

            if related is not None:
                raise ValueError(
                    f"Cannot delete solicitation {delete_id}: "
                    f"related records exist in {table_name}"
                )

    # Removes review candidates referencing the redundant record.
    candidates = list(
        session.scalars(
            select(SolicitationDuplicateCandidate).where(
                (
                    SolicitationDuplicateCandidate.solicitation_id_1
                    == delete_id
                )
                |
                (
                    SolicitationDuplicateCandidate.solicitation_id_2
                    == delete_id
                )
            )
        )
    )

    for candidate in candidates:
        session.delete(candidate)

    session.flush()
    session.delete(duplicate)
    session.flush()