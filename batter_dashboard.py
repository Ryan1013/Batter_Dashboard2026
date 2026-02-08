import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from PIL import Image

st.set_page_config(layout="wide")
st.title("Batter Dashboard")

# ---------------- LOAD DATA ---------------- #

@st.cache_data
def load_data():
    df = pd.read_csv("MB50_25.csv", low_memory=False)

    bowling_type_mapping = {
        'LLB': 'Spin', 'LOB': 'Spin', 'RLB': 'Spin', 'ROB': 'Spin',
        'LF': 'Pace', 'LFM': 'Pace', 'LM': 'Pace',
        'RF': 'Pace', 'RFM': 'Pace', 'RM': 'Pace'
    }

    df['Bowling Type'] = df['Bowler Type'].map(bowling_type_mapping)

    return df

data = load_data()

# ---------------- SIDEBAR FILTERS ---------------- #

st.sidebar.header("Filters")

teams = sorted(data['Batting Team'].dropna().unique())
selected_teams = st.sidebar.multiselect(
    "Batting Team",
    teams,
    default=teams
)

batters = sorted(data['Batter'].dropna().unique())
selected_batters = st.sidebar.multiselect(
    "Batter",
    batters,
    default=batters[:1]
)

selected_bowling = st.sidebar.multiselect(
    "Bowling Type",
    ["Spin", "Pace"],
    default=["Spin", "Pace"]
)

selected_runs = st.sidebar.multiselect(
    "Runs to Display",
    [1,2,3,4,5,6],
    default=[1,2,3,4,5,6]
)

# ---------------- APPLY FILTERS ---------------- #

filtered = data.copy()

if selected_teams:
    filtered = filtered[filtered['Batting Team'].isin(selected_teams)]

if selected_batters:
    filtered = filtered[filtered['Batter'].isin(selected_batters)]

if selected_bowling:
    filtered = filtered[filtered['Bowling Type'].isin(selected_bowling)]

# ---------------- KPI SECTION ---------------- #

st.subheader("Performance Metrics")

total_runs = filtered['Runs'].sum()

# Balls faced (exclude wides only)
balls_faced = filtered[
    ~filtered['Extra'].astype(str).str.contains("Wide", case=False, na=False)
].shape[0]

dismissals_count = filtered[
    filtered['Wicket'].notna() &
    ~filtered['Wicket'].isin([
        'Retired Hurt',
        'Retired - Not Out',
        'Absent'
    ])
].shape[0]

if dismissals_count > 0:
    batting_average = round(total_runs / dismissals_count, 2)
else:
    batting_average = "∞"

if balls_faced > 0:
    strike_rate = round((total_runs / balls_faced) * 100, 2)
else:
    strike_rate = 0

boundary_runs = filtered[filtered['Runs'].isin([4,6])]['Runs'].sum()

if total_runs > 0:
    boundary_percentage = round((boundary_runs / total_runs) * 100, 2)
else:
    boundary_percentage = 0

col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("Runs", total_runs)
col2.metric("Balls Faced", balls_faced)
col3.metric("Dismissals", dismissals_count)
col4.metric("Average", batting_average)
col5.metric("Strike Rate", strike_rate)
col6.metric("Boundary Runs %", boundary_percentage)

# ---------------- WAGON WHEEL ---------------- #

st.subheader("Wagon Wheel")

wagon = filtered[
    (filtered['Runs'].isin(selected_runs)) &
    (filtered['Runs'] > 0) &
    filtered['FieldX'].notna() &
    filtered['FieldY'].notna()
]

if len(wagon) > 0:

    center_x = 175
    center_y = 175

    run_colors = {
        1: "#00FFFF",
        2: "#0057FF",
        3: "#FF00FF",
        4: "#00C800",
        5: "#FFA500",
        6: "#FF0000"
    }

    fig = go.Figure()

    try:
        img = Image.open("wagon_background.png")
        fig.add_layout_image(
            dict(
                source=img,
                xref="x",
                yref="y",
                x=-180,
                y=180,
                sizex=360,
                sizey=360,
                sizing="stretch",
                layer="below"
            )
        )
    except:
        pass

    for _, row in wagon.iterrows():

        x = row['FieldX'] - center_x
        y = center_y - row['FieldY']
        run_val = row['Runs']
        color = run_colors.get(run_val, "grey")

        fig.add_trace(go.Scatter(
            x=[0, x],
            y=[0, y],
            mode="lines",
            line=dict(color=color, width=4),
            showlegend=False
        ))

    for r, c in run_colors.items():
        fig.add_trace(go.Scatter(
            x=[None],
            y=[None],
            mode="lines",
            line=dict(color=c, width=4),
            name=f"{r} Run"
        ))

    fig.update_layout(
        xaxis=dict(range=[-180,180], visible=False),
        yaxis=dict(range=[-180,180], visible=False),
        height=750,
        legend=dict(
            orientation="h",
            y=1.05,
            x=0.5,
            xanchor="center"
        ),
        margin=dict(l=0, r=0, t=0, b=0)
    )

    fig.update_yaxes(scaleanchor="x")

    st.plotly_chart(fig, width="stretch")

else:
    st.write("No scoring shots available.")

# ---------------- DISMISSAL PIE ---------------- #

st.subheader("Dismissal Breakdown")

dismissals = filtered[filtered['Wicket'].notna()]

if len(dismissals) > 0:

    counts = dismissals['Wicket'].value_counts()

    fig_pie = go.Figure(go.Pie(
        labels=counts.index,
        values=counts.values,
        textinfo="label+value",
        textposition="inside",
        hole=0.35,
        textfont=dict(size=22, family="Arial Black", color="black")
    ))

    fig_pie.update_layout(
        height=550,
        legend=dict(
            orientation="v",
            y=0.5,
            yanchor="middle",
            x=1.02
        ),
        margin=dict(l=20, r=150, t=20, b=20)
    )

    st.plotly_chart(fig_pie, width="stretch")

else:
    st.write("No dismissals recorded.")

# ---------------- CATCH MAP ---------------- #

st.subheader("Catch Map (Caught Only)")

caught = filtered[
    (filtered['Wicket'] == "Caught") &
    filtered['FieldX'].notna() &
    filtered['FieldY'].notna()
]

if len(caught) > 0:

    fig_catch = go.Figure()

    try:
        img = Image.open("wagon_background.png")
        fig_catch.add_layout_image(
            dict(
                source=img,
                xref="x",
                yref="y",
                x=-180,
                y=180,
                sizex=360,
                sizey=360,
                sizing="stretch",
                layer="below"
            )
        )
    except:
        pass

    x_vals = caught['FieldX'] - 175
    y_vals = 175 - caught['FieldY']

    fig_catch.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode="markers",
        marker=dict(
            symbol="x",
            size=14,
            color="black",
            line=dict(width=2)
        )
    ))

    fig_catch.update_layout(
        xaxis=dict(range=[-180,180], visible=False),
        yaxis=dict(range=[-180,180], visible=False),
        height=700,
        showlegend=False
    )

    fig_catch.update_yaxes(scaleanchor="x")

    st.plotly_chart(fig_catch, width="stretch")

else:
    st.write("No caught dismissals.")

# ---------------- BEEHIVE ---------------- #

st.subheader("Beehive")

beehive_data = filtered[
    filtered['Analyst Arrival Line'].notna() &
    filtered['Analyst Arrival Height'].notna()
].copy()

if len(beehive_data) > 0:

    fig = go.Figure()

    img = Image.open("beehive_background.jpg")
    img_width, img_height = img.size

    # 🔽 Wider look, reduced vertical height
    x_min_m = -1.83
    x_max_m =  1.83

    y_min_m = 0
    y_max_m = 2.0   # ← reduce this to compress vertically

    fig.add_layout_image(
        dict(
            source=img,
            xref="x",
            yref="y",
            x=x_min_m,
            y=y_max_m,
            sizex=(x_max_m - x_min_m),
            sizey=(y_max_m - y_min_m),
            sizing="stretch",
            layer="below"
        )
    )

    fig.add_trace(go.Scatter(
        x=beehive_data[beehive_data['Runs'] == 4]['Analyst Arrival Line'],
        y=beehive_data[beehive_data['Runs'] == 4]['Analyst Arrival Height'],
        mode="markers",
        marker=dict(size=9, color="green",
                    line=dict(width=1, color="black")),
        name="4 Runs"
    ))

    fig.add_trace(go.Scatter(
        x=beehive_data[beehive_data['Runs'] == 6]['Analyst Arrival Line'],
        y=beehive_data[beehive_data['Runs'] == 6]['Analyst Arrival Height'],
        mode="markers",
        marker=dict(size=11, color="red",
                    line=dict(width=1, color="black")),
        name="6 Runs"
    ))

    fig.add_trace(go.Scatter(
        x=beehive_data[beehive_data['Wicket'].notna()]['Analyst Arrival Line'],
        y=beehive_data[beehive_data['Wicket'].notna()]['Analyst Arrival Height'],
        mode="markers",
        marker=dict(symbol="x", size=14,
                    color="black", line=dict(width=2)),
        name="Dismissal"
    ))

    fig.update_layout(
        height=700,
        xaxis=dict(range=[x_min_m, x_max_m], visible=False),
        yaxis=dict(range=[y_min_m, y_max_m], visible=False),
        legend=dict(
            orientation="h",
            y=1,
            x=0.5,
            xanchor="center"
        ),
        margin=dict(l=0, r=0, t=0, b=0)
    )

    fig.update_yaxes(scaleanchor="x")

    st.plotly_chart(fig, width="stretch")

else:
    st.write("No delivery data available.")
