import pandas as pd


def split_name(name):
    """Splits a full name formatted as 'Last, First' into (First Name, Last Name).

    Falls back to whitespace splitting if no comma is present.
    """
    if pd.isna(name) or not str(name).strip():
        return "", ""

    name_str = str(name).strip()

    if "," in name_str:
        # Split on the first comma: 'Last, First' -> ['Last', 'First']
        parts = name_str.split(",", 1)
        last = parts[0].strip()
        first = parts[1].strip()
    else:
        # Fallback if a row is formatted as 'First Last' without a comma
        parts = name_str.split(maxsplit=1)
        first = parts[0].strip()
        last = parts[1].strip() if len(parts) > 1 else ""

    return first, last


def combine_address(addr1, addr2):
    """Combines Address Line 1 and Address Line 2."""
    a1 = "" if pd.isna(addr1) else str(addr1).strip()
    a2 = "" if pd.isna(addr2) else str(addr2).strip()
    if a1 and a2:
        return f"{a1}, {a2}"
    return a1 or a2


def process_parents(row):
    """Determines primary (p1) and secondary (p2) parents.

    Matches Registration Email to Parent 1 or Parent 2.
    Raises ValueError if Registration Email matches neither.
    """
    reg_email = str(row.get("Registration Email", "")).strip().lower()

    # Parent 1 raw data
    p1_name = row.get("Parent 1 Name", "")
    p1_email = str(row.get("Parent 1 Email", "")).strip()
    p1_cell = row.get("Parent 1 Cell", "")

    # Parent 2 raw data
    p2_name = row.get("Parent 2 Name", "")
    p2_email = str(row.get("Parent 2 Email", "")).strip()
    p2_cell = row.get("Parent 2 Cell", "")

    p1_match = reg_email and (p1_email.lower() == reg_email)
    p2_match = reg_email and (p2_email.lower() == reg_email)

    if reg_email and not (p1_match or p2_match):
        # Raise exception if registration email exists but matches neither parent
        row_id = row.name  # Pandas Index
        raise ValueError(
            f"Row {row_id}: Registration Email '{reg_email}' does not match "
            f"Parent 1 Email ('{p1_email}') or Parent 2 Email ('{p2_email}')."
        )

    # Assign primary/secondary based on match
    if p2_match:
        # Swap: Parent 2 becomes primary (p1), Parent 1 becomes secondary (p2)
        primary_name, primary_email, primary_cell = p2_name, p2_email, p2_cell
        secondary_name, secondary_email, secondary_cell = (
            p1_name,
            p1_email,
            p1_cell,
        )
    else:
        # Parent 1 matches or no registration email was provided
        primary_name, primary_email, primary_cell = p1_name, p1_email, p1_cell
        secondary_name, secondary_email, secondary_cell = (
            p2_name,
            p2_email,
            p2_cell,
        )

    p1fn, p1ln = split_name(primary_name)
    p2fn, p2ln = split_name(secondary_name)

    return pd.Series(
        {
            "p1fn": p1fn,
            "p1ln": p1ln,
            "p1email": primary_email,
            "p1cell": primary_cell if pd.notna(primary_cell) else "",
            "p1relation": "Parent" if p1fn else "",
            "p2fn": p2fn,
            "p2ln": p2ln,
            "p2email": secondary_email,
            "p2cell": secondary_cell if pd.notna(secondary_cell) else "",
            "p2relation": "Parent" if p2fn else "",
        }
    )


def transform_excel_to_csv(input_file_path, output_csv_path):
    df = pd.read_excel(input_file_path)

    target_columns = [
        "first",
        "last",
        "Non-Player",
        "address",
        "city",
        "state",
        "zip",
        "birthdate",
        "Jersey Number",
        "Position",
        "email",
        "email_label",
        "phone_number",
        "gender",
        "p1fn",
        "p1ln",
        "p1relation",
        "p1email",
        "p1home",
        "p1cell",
        "p1work",
        "p2fn",
        "p2ln",
        "p2relation",
        "p2email",
        "p2home",
        "p2cell",
        "p2work",
        "Team",
        "Division",
    ]

    out_df = pd.DataFrame(index=df.index, columns=target_columns)

    # Athlete Information
    athlete_names = df["Athlete Name"].apply(split_name)
    out_df["first"] = [n[0] for n in athlete_names]
    out_df["last"] = [n[1] for n in athlete_names]

    # Address & Contact
    out_df["address"] = [
        combine_address(a1, a2)
        for a1, a2 in zip(df.get("Address Line 1"), df.get("Address Line 2"))
    ]
    out_df["city"] = df.get("City", "")
    out_df["state"] = df.get("State", "")
    out_df["zip"] = df.get("ZIP", "")
    out_df["birthdate"] = df.get("DOB", "")
    out_df["email"] = df.get("Registration Email", "")
    out_df["Team"] = df.get("Team", "")
    out_df["Division"] = df.get("Division", "")

    # Parent Logic (Strict validation - raises ValueError on mismatch)
    parent_data = df.apply(process_parents, axis=1)
    for col in [
        "p1fn",
        "p1ln",
        "p1email",
        "p1cell",
        "p1relation",
        "p2fn",
        "p2ln",
        "p2email",
        "p2cell",
        "p2relation",
    ]:
        out_df[col] = parent_data[col]

    # Blank/Unmapped fields
    blank_fields = [
        "Non-Player",
        "Jersey Number",
        "Position",
        "email_label",
        "phone_number",
        "gender",
        "p1home",
        "p1work",
        "p2home",
        "p2work",
    ]
    for col in blank_fields:
        out_df[col] = ""

    out_df.to_csv(output_csv_path, index=False)
    print(
        f"Successfully transformed {len(df)} rows and saved to '{output_csv_path}'."
    )


if __name__ == "__main__":
    transform_excel_to_csv("/tmp/Admin.xlsx", "output_roster.csv")
