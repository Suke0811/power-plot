import streamlit as st
import pandas as pd
from power_plot import PerformancePlotter
import io
import zipfile
import re


def sanitize_filename(name, default="plot"):
    # Replace spaces with underscores
    name = name.replace(" ", "_")
    # Remove any non-alphanumeric, underscores or hyphens
    name = re.sub(r'[^\w\-]', '', name)
    return name if name else default


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
    is_log_y = st.sidebar.toggle("Use Logarithmic Scale for Y-axis", value=False)

    # Main Content
    required_cols = ["name", "pmin", "pmax", "fmin", "fmax"]
    
    # 1) Load data
    if uploaded_file is not None:
        try:
            if uploaded_file.name.lower().endswith(".csv"):
                df_input = pd.read_csv(uploaded_file)
            else:
                df_input = pd.read_excel(uploaded_file)
        except Exception as e:
            st.error(f"Error processing file: {e}")
            return
    else:
        # Provide an empty template if no file is uploaded
        df_input = pd.DataFrame(columns=required_cols)

    # 2) Display editable table
    st.subheader("Edit Data")
    edited_df = st.data_editor(
        df_input, 
        num_rows="dynamic", 
        width="stretch",
        column_config={
            "name": st.column_config.TextColumn("Name", help="Name of the device or accelerator"),
            "pmin": st.column_config.NumberColumn("Power Min (W)", format="%.2f", help="Minimum power consumption in Watts"),
            "pmax": st.column_config.NumberColumn("Power Max (W)", format="%.2f", help="Maximum power consumption in Watts"),
            "fmin": st.column_config.NumberColumn("Perf Min", format="%.2f", help="Minimum performance (e.g. TOPS)"),
            "fmax": st.column_config.NumberColumn("Perf Max", format="%.2f", help="Maximum performance (e.g. TOPS)"),
        }
    )

    # 4) Build and render plot
    if not edited_df.empty and set(required_cols).issubset(edited_df.columns):
        try:
            plotter = PerformancePlotter(is_log_y=is_log_y)
            plotter.add_data(edited_df)
            fig = plotter.finalize(plot_title)

            # Override axis labels
            fig.update_xaxes(title="Power (W)")
            y_axis_title = f"{y_label} ({y_unit})"
            if is_log_y:
                y_axis_title += " (log scale)"
            fig.update_yaxes(title=y_axis_title)

            st.plotly_chart(fig, width="stretch")

            # --- Download options ---
            st.subheader("Download Options")
            col1, col2, col3, col4 = st.columns(4)

            base_name = sanitize_filename(plot_title, default="performance_plot")

            # 1. Download HTML
            html_bytes = fig.to_html(include_plotlyjs='cdn').encode()
            with col1:
                st.download_button(
                    label="Download HTML",
                    data=html_bytes,
                    file_name=f"{base_name}.html",
                    mime="text/html",
                )

            # 2. Download PNG
            try:
                png_bytes = fig.to_image(format="png")
                with col2:
                    st.download_button(
                        label="Download PNG",
                        data=png_bytes,
                        file_name=f"{base_name}.png",
                        mime="image/png",
                    )
            except Exception as e:
                with col2:
                    st.error(f"Error generating PNG: {e}")
                png_bytes = None

            # 3. Download CSV (from the editor)
            csv_bytes = edited_df.to_csv(index=False).encode('utf-8')
            with col3:
                st.download_button(
                    label="Download CSV",
                    data=csv_bytes,
                    file_name=f"{base_name}_data.csv",
                    mime="text/csv",
                )

            # 4. Download All (ZIP)
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                zf.writestr(f"{base_name}.html", html_bytes)
                if png_bytes:
                    zf.writestr(f"{base_name}.png", png_bytes)
                zf.writestr(f"{base_name}_data.csv", csv_bytes)
            
            with col4:
                st.download_button(
                    label="Download All (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name=f"{base_name}_assets.zip",
                    mime="application/zip",
                )

        except Exception as e:
            st.error(f"Error generating plot: {e}")
    else:
        if edited_df.empty:
            st.info("The table is empty. Add some rows to see the plot.")
        else:
            st.error(f"Missing required columns. Table must contain: {', '.join(required_cols)}")


if __name__ == "__main__":
    main()
