import streamlit as st
import pandas as pd
from power_plot import PerformancePlotter


def main():
    st.set_page_config(page_title="Performance Plotter", layout="wide")
    st.title("Performance Envelope Visualizer")

    # Sidebar Configuration
    st.sidebar.header("Plot Settings")

    # 1) File Upload (CSV or Excel)
    uploaded_file = st.sidebar.file_uploader("Upload Data (CSV or Excel)", type=["csv", "xlsx"]) 

    # 2) Plot Labels
    plot_title = st.sidebar.text_input("Plot Title", value="Hardware Performance Envelopes")
    y_label = st.sidebar.text_input("Y-axis Label", value="AI Performance")
    y_unit = st.sidebar.text_input("Y-axis Unit", value="TOPS")

    # 3) Axis Scale
    is_log_y = st.sidebar.toggle("Use Logarithmic Scale for Y-axis", value=True)

    # Main Content
    if uploaded_file is not None:
        try:
            # Read input file
            if uploaded_file.name.lower().endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            # Validate required columns
            required_cols = {"name", "pmin", "pmax", "fmin", "fmax"}
            if not required_cols.issubset(df.columns):
                st.error(f"Missing required columns. File must contain: {', '.join(required_cols)}")
                return

            # Build and render plot
            plotter = PerformancePlotter(is_log_y=is_log_y)
            plotter.add_data(df)
            fig = plotter.finalize(plot_title)

            # Override axis labels
            fig.update_xaxes(title="Power (W)")
            fig.update_yaxes(title=f"{y_label} ({y_unit})")

            st.plotly_chart(fig, use_container_width=True)

            # Download button for the plot (HTML format)
            html_bytes = fig.to_html(include_plotlyjs='cdn').encode()
            st.download_button(
                label="Download Plot as HTML",
                data=html_bytes,
                file_name="performance_plot.html",
                mime="text/html",
            )

            # Optional: show uploaded data
            with st.expander("View Uploaded Data"):
                st.dataframe(df)

        except Exception as e:
            st.error(f"Error processing file: {e}")
    else:
        st.info("Please upload a CSV or Excel file to get started.")
        st.write("Expected columns: `name`, `pmin`, `pmax`, `fmin`, `fmax`.")


if __name__ == "__main__":
    main()
