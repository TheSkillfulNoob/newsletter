import pandas as pd
import os
from io import StringIO

def generate_appended_csv(payload, week_tag, original_csv="past-content.csv"):
    columns = ["week", "title", "events-prof", "events-pers", "gratitude",
               "productivity", "up_next", "facts", "weekly"]

    if os.path.exists(original_csv):
        df = pd.read_csv(original_csv)
    else:
        df = pd.DataFrame(columns=columns)

    new_row = {col: "" for col in columns}
    new_row["week"] = week_tag
    for key in payload:
        if key in new_row:
            new_row[key] = payload[key]

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    buffer = StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue()
