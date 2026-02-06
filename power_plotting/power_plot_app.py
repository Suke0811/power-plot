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
        use_container_width=True,
        column_config={
            "pmin": st.column_config.NumberColumn(format="%.2f"),
            "pmax": st.column_config.NumberColumn(format="%.2f"),
            "fmin": st.column_config.NumberColumn(format="%.2f"),
            "fmax": st.column_config.NumberColumn(format="%.2f"),
        }
    )

    # 3) Download button for CSV
    if not edited_df.empty:
        csv = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Edited CSV",
            data=csv,
            file_name="edited_data.csv",
            mime="text/csv",
        )

    # 4) Build and render plot
    if not edited_df.empty and set(required_cols).issubset(edited_df.columns):
        try:
            plotter = PerformancePlotter(is_log_y=is_log_y)
            plotter.add_data(edited_df)
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

        except Exception as e:
            st.error(f"Error generating plot: {e}")
    else:
        if edited_df.empty:
            st.info("The table is empty. Add some rows to see the plot.")
        else:
            st.error(f"Missing required columns. Table must contain: {', '.join(required_cols)}")


if __name__ == "__main__":
    main()
