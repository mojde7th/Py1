import dash
from dash import dcc, html, Input, Output, State, dash_table
import plotly.express as px
from fetch_data import fetch_data

# Fetch data from SQL Server
df = fetch_data()

# PINK COMMENT: Aggregate data for the main table to remove `SEX_CODE` split initially
df_main_table = (
    df.groupby(["NodeId", "Title"])
    .agg({"NationalIdCount": "sum"})
    .reset_index()
)

# Initialize Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Hierarchy Dashboard"
server = app.server

# Layout for displaying all nodes
all_nodes_table = dash_table.DataTable(
    id="all-nodes-table",
    columns=[
        {"name": "NodeId", "id": "NodeId"},
        {"name": "Title", "id": "Title"},
        {"name": "NationalIdCount", "id": "NationalIdCount"},
    ],
    data=df_main_table.to_dict("records"),  # PINK COMMENT: Use aggregated data here
    style_table={"height": "300px", "overflowY": "auto"},
    row_selectable="single",
    selected_rows=[],
)

# Main layout
app.layout = html.Div([
    html.H1("Hierarchy Dashboard", style={"textAlign": "center"}),

    html.Div([
        html.H3("All Nodes"),
        all_nodes_table,
    ], style={"marginBottom": "20px"}),

    html.Div(id="filtered-data-container"),

    html.Div(id="gender-chart-container", style={"marginTop": "20px"}),  # PINK COMMENT: Added container for the donut chart
])

# PINK COMMENT: Callback to display filtered data and gender distribution automatically
@app.callback(
    Output("filtered-data-container", "children"),
    Output("gender-chart-container", "children"),  # PINK COMMENT: Added output for the donut chart
    Input("all-nodes-table", "selected_rows"),
    prevent_initial_call=True,
)
def display_node_and_gender(selected_rows):
    if not selected_rows:
        return html.H3("No Node Selected"), None

    selected_row = selected_rows[0]
    node_id = df_main_table.iloc[selected_row]["NodeId"]  # PINK COMMENT: Use aggregated data for NodeId

    # Filter data for the selected node
    filtered_data = df[df["NodeId"] == node_id]

    # Gender Count and Donut Chart Section
    if filtered_data["SEX_CODE"].isnull().all():
        return html.H3(f"Filtered Data for Node ID {node_id}"), html.H3("No Gender Data Available")

    # PINK COMMENT: Calculate gender distribution
    gender_count = (
        filtered_data.groupby("SEX_CODE")
        .agg({"NationalIdCount": "sum", "Title": "first"})
        .reset_index()
    )
    gender_map = {"1": "Male", "2": "Female"}
    gender_count["SEX_CODE"] = gender_count["SEX_CODE"].map(gender_map)

    # PINK COMMENT: Create the gender distribution chart
    fig = px.pie(
        gender_count,
        names="SEX_CODE",
        values="NationalIdCount",
        title=f"Gender Distribution for Node ID {node_id}",
        hole=0.4,  # Create the donut effect
    )
    fig.update_traces(textinfo="percent+label", hoverinfo="label+value")

    # PINK COMMENT: Return filtered table and chart
    return (
        html.Div([
            html.H3(f"Filtered Data for Node ID {node_id}"),
            dash_table.DataTable(
                id="filtered-data-table",
                columns=[
                    {"name": col, "id": col}
                    for col in filtered_data.columns if col != "SEX_CODE"
                ],
                data=filtered_data.to_dict("records"),
                style_table={"overflowX": "auto"},
            ),
        ]),
        dcc.Graph(figure=fig, id="gender-donut-chart"),  # PINK COMMENT: Display the donut chart
    )

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8080)
