from pathlib import Path

from app.services.esbd_import import import_esbd_csv

def main():
    csv_path = (
        Path.home()
        / "Downloads"
        / "ESBD Solicitations Export.csv"
    )

    if not csv_path.is_file():
        raise FileNotFoundError(csv_path)

    result = import_esbd_csv(csv_path)

    print("ESBD import complete")
    print(f"Collected: {result.collected}")
    print(f"Inserted: {result.inserted}")
    print(f"Updated: {result.updated}")

if __name__ == "__main__":
    main()