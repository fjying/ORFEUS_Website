import dash
import dash_bootstrap_components as dbc
import dropbox

app = dash.Dash(external_stylesheets=[dbc.themes.CERULEAN])
app.title = 'ORFEUS Data Website'

# dropbox access token
APP_KEY = "uya754jfrwnq1o8"
APP_SECRET = "qcvxuobkaviuvc4"
REFRESH_TOKEN = "d7NocTXgLgwAAAAAAAAAAeuKMBIVWwMJK3fCD1t9rtcwsrHXV1DMDwyQ_-SJhNXp"
dbx = dropbox.Dropbox(app_key=APP_KEY,
                      app_secret=APP_SECRET,
                      oauth2_refresh_token=REFRESH_TOKEN)