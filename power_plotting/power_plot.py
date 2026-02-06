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

    def _get_envelope_coords(self, pmin, pmax, fmin, fmax) -> Tuple[np.ndarray, np.ndarray]:
        """Calculates tilted ellipsoid coordinates in the specified coordinate space."""
        # 1. Coordinate Space Transformation
        x1, x2 = pmin, pmax
        y1, y2 = (np.log10(fmin), np.log10(fmax)) if self.is_log_y else (fmin, fmax)

        # 2. Geometry Calculation
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        dx, dy = x2 - x1, y2 - y1
        dist = np.sqrt(dx**2 + dy**2)
        angle = np.arctan2(dy, dx)
        
        if dist == 0:
            return np.array([cx]), np.array([cy])

        a = dist / 2
        # b is half the perpendicular distance from rectangle corners to major axis
        b = (dx * dy) / (2 * dist)

        # 3. Generate and Rotate Points
        t = np.linspace(0, 2 * np.pi, 100)
        xs, ys = a * np.cos(t), b * np.sin(t)
        
        x_rot = cx + (xs * np.cos(angle) - ys * np.sin(angle))
        y_rot = cy + (xs * np.sin(angle) + ys * np.cos(angle))

        return x_rot, (10 ** y_rot if self.is_log_y else y_rot)

    def add_data(self, df: pd.DataFrame):
        """Iterates through the DataFrame and adds traces to the figure."""
        n_items = len(df)
        for i, row in enumerate(df.itertuples()):
            # Select color from the monotonic scale
            color_idx = int((i / max(1, n_items - 1)) * (len(self.colors) - 1))
            color = self.colors[color_idx]
            
            x_env, y_env = self._get_envelope_coords(row.pmin, row.pmax, row.fmin, row.fmax)

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

    # 2. Initialize Plotter (set is_log_y=False for linear scale)
    plotter = PerformancePlotter(is_log_y=True)
    
    # 3. Add data and finalize
    plotter.add_data(data_df)
    fig = plotter.finalize("Hardware Performance Envelopes: Power vs. Performance")
    
    # 4. Show plot
    fig.show()
