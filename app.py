import dash
import dash_bootstrap_components as dbc
import dropbox

app = dash.Dash(external_stylesheets=[dbc.themes.CERULEAN])
app.title = 'ORFEUS Data Website'

# dropbox access token
APP_KEY = "XX"
APP_SECRET = "XX"
REFRESH_TOKEN = "XXX"
dbx = dropbox.Dropbox(app_key=APP_KEY,
                      app_secret=APP_SECRET,
                      oauth2_refresh_token=REFRESH_TOKEN)
