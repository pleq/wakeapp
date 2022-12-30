import dash
from dash import Dash, html, dcc, Input, Output, callback, clientside_callback, State
import dash_mantine_components as dmc
from dash_iconify import DashIconify
from wakeonlan import send_magic_packet
import waitress
from paste.translogger import TransLogger
import iptools
import re
from datetime import datetime

logger_format = ('%(REMOTE_ADDR)s - %(REMOTE_USER)s [%(time)s] '
                 '"%(REQUEST_METHOD)s %(REQUEST_URI)s %(HTTP_VERSION)s" '
                 '%(status)s %(bytes)s "%(HTTP_REFERER)s"')

user_info = {
    'lhagva@tvsi.ru': ['b4:2e:99:e1:b1:12', '172.16.6.69'],
    'emir_m@tvsi.ru': ['4C-CC-6A-00-B9-4E', '172.16.6.74']
} 

scripts = [
    "https://cdnjs.cloudflare.com/ajax/libs/dayjs/1.10.8/dayjs.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/dayjs/1.10.8/locale/ru.min.js",
]

app = Dash(
    __name__,
    use_pages=False,
    external_scripts=scripts,
    update_title=None,
    title="ТСИ.Wake-on-Lan",
    prevent_initial_callbacks=True
)

app.layout = dmc.MantineProvider(
    id="theme-provider-1",
    theme={
        "colorScheme": "light",
        "primaryColor": "indigo",
    },
    #styles={"Button": {"root": {"fontWeight": 400}}},
    withGlobalStyles=True,
    withNormalizeCSS=True,
    children=[
        dcc.Location(id="url"),
        html.Div(
            children=[
                dmc.Group(
                    position="right",
                    align="center",
                    spacing="xl",
                    style={"paddingLeft": 20, "paddingRight": 20, "paddingTop": 20, "paddingBottom": 0},
                    children=[
                        dmc.Tooltip(
                            label="emir_m@tvsi.ru",
                            position="left",
                            placement="center",
                            gutter=3,
                            children=[
                                dmc.ActionIcon(
                                    DashIconify(icon="fa-regular:question-circle"), variant="hover"
                                ),
                            ],
                        ),
                        dmc.ThemeSwitcher(
                            id="color-scheme-toggle",
                            style={"cursor": "pointer"},
                        ),
                    ],
                ),
                dmc.Center(
                    style={"height": 800, "width": "100%"},
                    children=[
                        dmc.Group(
                            direction="column", spacing="xl", align="center",
                            children=[
                                dmc.Paper(
                                    children=[
                                        dmc.Group(
                                            children=[
                                                dmc.Group(
                                                    direction="column", spacing="xs", align="center", 
                                                    children=[
                                                        DashIconify(icon="akar-icons:globe", width=35, color="gray"),
                                                        dmc.Text(
                                                            children="Cервис Wake-on-Lan", weight=500, color="indigo", 
                                                            style={"marginTop": 0, "marginBottom": 5, "fontSize": 20}),
                                                    ]
                                                ),
                                                dmc.Stack(
                                                    [
                                                        #dmc.Select(
                                                        #    label="Выберите шаблон пользователя:",
                                                        #    placeholder="",
                                                        #    id="user-select",
                                                        #    searchable=False,
                                                        #    persistence=True,
                                                        #    #value="emir_m@tvsi.ru",
                                                        #    data=[
                                                        #        {"value": "4C-CC-6A-00-B9-4E", "label": "emir_m@tvsi.ru"},
                                                        #        {"value": "b4:2e:99:e1:b1:12", "label": "lhagva@tvsi.ru"},
                                                        #    ],
                                                        #    style={"width": 250},
                                                        #),
                                                        dmc.TextInput(
                                                            label="Введите MAC-адрес хоста:",
                                                            id="input-mac-adress",
                                                            style={"width": 250},
                                                            placeholder="ff-ff-ff-ff-ff-ff",
                                                            icon=[DashIconify(icon="material-symbols:desktop-mac-outline-rounded")],
                                                            required=True,
                                                        ),
                                                        dmc.TextInput(
                                                            label="Введите IP-адрес:",
                                                            id="input-ip-adress",
                                                            style={"width": 250},
                                                            placeholder="255.255.255.255",
                                                            description="Опционально",
                                                            icon=[DashIconify(icon="material-symbols:bring-your-own-ip")],
                                                        ),
                                                        dmc.NumberInput(
                                                            label="Введите порт:",
                                                            description="Опционально",
                                                            id="input-port",
                                                            value=9,
                                                            min=0,
                                                            step=1,
                                                            style={"width": 250},
                                                        )
                                                    ],
                                                ),
                                                dmc.Button(
                                                    "Отправить запрос Wake-on-Lan",
                                                    id="submit-wol",
                                                    variant="outline", compact=False,
                                                    n_clicks=0, size="sm", disabled=False,
                                                ),
                                                html.Br(),
                                                dmc.Text("Статус запроса: не отправлен", id="wol-status-text", color="dimmed")
                                            ],
                                            direction="column", spacing="xl", align="center"
                                        )
                                    ],
                                    radius="md",
                                    p="xl",
                                    withBorder=True,
                                    shadow="md",
                                    #style={"width":140, "height": 140}
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ],
)


""" @app.callback(
    Output("user-select", "value"),
    Input("input-mac-adress", "value"),
    prevent_initial_call=True,
)
def choose_default(preset):
    print(preset)
    return preset
 """

@app.callback(
    Output("wol-status-text", "children"),
    [Input("submit-wol", "n_clicks"),
     State("input-mac-adress", "value"),
     State("input-ip-adress", "value"),
     State("input-port", "value")],
    prevent_initial_call=True,
)
def send_wol(n_clicks, mac, ip, port):
    if mac:
        if re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", mac.lower()):
            
            if ip == None or ip == '':
                ip = '255.255.255.255'
            if port == None:
                port = 9
            
            if iptools.ipv4.validate_ip(ip):
                print(mac, ip, port)
                send_magic_packet(mac, ip_address=str(ip), port=port)
                current_time = datetime.now().strftime("%H:%M:%S")
                return f"Статус запроса: отправлен {current_time}"
            else:
                return "Некорректный формат IP-адреса"
            
        else:
            return "Некорректный формат MAC"


clientside_callback(
    """function(colorScheme) {
        return {
            colorScheme,
            primaryColor: "indigo"
        }
    }""",
    Output("theme-provider", "theme"),
    Input("color-scheme-toggle", "value"),
)

if __name__ == "__main__":
    host = "0.0.0.0"
    #app.run(debug=False, host=host, port=8888, threaded=True)
    waitress.serve(TransLogger(app.server, format=logger_format), host=host, port=9999)
    
    
    
    