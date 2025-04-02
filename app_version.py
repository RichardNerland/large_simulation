import dash
import flask
import plotly

print("Dash version:", dash.__version__)
print("Flask version:", flask.__version__)
print("Plotly version:", plotly.__version__)

# Check for Dash components
try:
    import dash_core_components
    print("dash_core_components version:", dash_core_components.__version__)
except ImportError:
    print("dash_core_components not installed separately (part of dash)")

try:
    import dash_html_components
    print("dash_html_components version:", dash_html_components.__version__)
except ImportError:
    print("dash_html_components not installed separately (part of dash)")

try:
    import dash_table
    print("dash_table version:", dash_table.__version__)
except ImportError:
    print("dash_table not installed separately (part of dash)") 