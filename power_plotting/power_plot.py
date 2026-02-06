import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from typing import Tuple

class PerformancePlotter:
    """Handles geometry and Plotly visualizations directly from DataFrame rows."""
    
    def __init__(self, is_log_y: bool = True):
        self.is_log_y = is_log_y
        self.fig = go.Figure()
        # Use a monotonic/sequential scale (e.g., 'Blues_r' for a professional look)
        self.colors = px.colors.sequential.Cividis

    def _get_envelope_coords(self, pmin, pmax, fmin, fmax, df_context=None) -> Tuple[np.ndarray, np.ndarray]:
        """Calculates tilted ellipsoid coordinates using normalized space to maintain alignment."""
        # 1. Coordinate Space Transformation (Log handling)
        x1, x2 = pmin, pmax
        y1, y2 = (np.log10(fmin), np.log10(fmax)) if self.is_log_y else (fmin, fmax)

        # 2. Normalization (Advanced Aspect Ratio Handling)
        # If we have the full data range, we can normalize to a 0-1 square
        # This prevents the 'stretching' effect on the rotation angle
        if df_context is not None and not self.is_log_y:
            x_range = df_context['pmax'].max() - df_context['pmin'].min()
            y_range = df_context['fmax'].max() - df_context['fmin'].min()

            # Scale factor to equalize visual units
            scale_y = x_range / y_range if y_range != 0 else 1.0
            y1_norm, y2_norm = y1 * scale_y, y2 * scale_y
        else:
            scale_y = 1.0
            y1_norm, y2_norm = y1, y2

        # 3. Geometry Calculation in (Normalized) Space
        cx, cy_norm = (x1 + x2) / 2, (y1_norm + y2_norm) / 2
        dx, dy_norm = x2 - x1, y2_norm - y1_norm
        dist = np.sqrt(dx**2 + dy_norm**2)
        angle = np.arctan2(dy_norm, dx)

        if dist == 0:
            return np.array([cx]), np.array([10**y1 if self.is_log_y else y1])

        a = dist / 2
        if self.is_log_y:
            # Revert to original b calculation for log scale (half perpendicular distance)
            b = (dx * dy_norm) / (2 * dist)
        else:
            # Use constant factor for linear scale to ensure visibility
            b = a * 0.2

        # 4. Generate and Rotate Points
        t = np.linspace(0, 2 * np.pi, 100)
        xs, ys = a * np.cos(t), b * np.sin(t)

        x_rot = cx + (xs * np.cos(angle) - ys * np.sin(angle))
        y_rot_norm = cy_norm + (xs * np.sin(angle) + ys * np.cos(angle))

        # 5. Reverse Normalization and Log Transform
        y_final = y_rot_norm / scale_y
        return x_rot, (10 ** y_final if self.is_log_y else y_final)

    def add_data(self, df: pd.DataFrame):
        """Iterates through the DataFrame and adds traces to the figure."""
        n_items = len(df)
        for i, row in enumerate(df.itertuples()):
            # Select color from the monotonic scale
            color_idx = int((i / max(1, n_items - 1)) * (len(self.colors) - 1))
            color = self.colors[color_idx]

            x_env, y_env = self._get_envelope_coords(row.pmin, row.pmax, row.fmin, row.fmax, df_context=df)

            # Add Envelope with the monotonic color
            self.fig.add_trace(go.Scatter(
                x=x_env, y=y_env, fill="toself", fillcolor=color, opacity=0.3,
                line=dict(color=color, width=1.5), name=row.name,
                legendgroup=row.name, hoverinfo='skip'
            ))

            # Add Markers
            self.fig.add_trace(go.Scatter(
                x=[row.pmin, row.pmax], y=[row.fmin, row.fmax],
                mode='markers', marker=dict(color=color, size=8, symbol='circle'),
                name=f"{row.name} Range", legendgroup=row.name, showlegend=False
            ))

            # Add Label inside the ellipse
            cx = (row.pmin + row.pmax) / 2
            cy = np.sqrt(row.fmin * row.fmax) if self.is_log_y else (row.fmin + row.fmax) / 2

            self.fig.add_trace(go.Scatter(
                x=[cx], y=[cy],
                mode='text',
                text=[row.name],
                textposition="middle center",
                textfont=dict(color="black", size=10),
                showlegend=False,
                legendgroup=row.name,
                hoverinfo='skip'
            ))

    def finalize(self, title: str):
        """Styles the layout and returns the figure."""
        self.fig.update_xaxes(title="Power Consumption (Watts)", gridcolor='lightgrey')
        self.fig.update_yaxes(type="log" if self.is_log_y else "linear", 
                              title="AI Performance (TOPS)", gridcolor='lightgrey')
        self.fig.update_layout(title=title, template="plotly_white", height=600)
        return self.fig

if __name__ == "__main__":
    # 1. Load your table (e.g., from Excel: df = pd.read_excel("data.xlsx"))
    # Creating a sample DataFrame for demonstration:
    data_df = pd.DataFrame([
        {'name': 'Jetson Nano', 'pmin': 5, 'pmax': 10, 'fmin': 0.2, 'fmax': 0.5},
        {'name': 'Jetson TX2', 'pmin': 7.5, 'pmax': 15, 'fmin': 0.6, 'fmax': 1.3},
        {'name': 'Jetson Xavier NX', 'pmin': 10, 'pmax': 20, 'fmin': 14, 'fmax': 21},
        {'name': 'Jetson AGX Orin 64GB', 'pmin': 15, 'pmax': 60, 'fmin': 50, 'fmax': 275},
    ])

    # 2. Initialize Plotter (set is_log_y=True for log scale)
    plotter = PerformancePlotter(is_log_y=True)
    
    # 3. Add data and finalize
    plotter.add_data(data_df)
    fig = plotter.finalize("Hardware Performance Envelopes: Power vs. Performance")
    
    # 4. Show plot
    fig.show()
