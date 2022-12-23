import dash
from dash import Dash, html, dcc, Input, Output, callback,  clientside_callback, State
import dash_mantine_components as dmc
from dash_iconify import DashIconify
from wakeonlan import send_magic_packet
from ldap3 import Server, Connection, ALL, SUBTREE
from ldap3.core.exceptions import LDAPException, LDAPBindError
import waitress
from paste.translogger import TransLogger

logger_format = ('%(REMOTE_ADDR)s - %(REMOTE_USER)s [%(time)s] '
                 '"%(REQUEST_METHOD)s %(REQUEST_URI)s %(HTTP_VERSION)s" '
                 '%(status)s %(bytes)s "%(HTTP_REFERER)s"')

LDAP_SERVER = '172.16.0.1'
LDAP_FILTER = '(objectclass=person)'
#LDAP_FILTER2 = "(&(objectClass=user)(sAMAccountName=" + LDAP_USER + "))"
LDAP_ATTRS = ['cn','sn','uid','uidNumber']
SEARCH_BASE = 'dc=tvsi,dc=ru'

user_mac = {
    'lhagva@tvsi.ru': 'b4:2e:99:e1:b1:12',
    'emir_m@tvsi.ru': '4C-CC-6A-00-B9-4E' # swapped
} 

user_ip = {
    'lhagva@tvsi.ru': '172.16.6.69',
    'emir_m@tvsi.ru': '172.16.6.74'
}

user_broadcast = {
    'lhagva@tvsi.ru': '172.16.6.127',
    'emir_m@tvsi.ru': '172.16.6.127'
}

def ldap_auth(LDAP_USER, LDAP_PASSWORD):
    server = Server(LDAP_SERVER, get_info=ALL)
    try: 
        with Connection(server, user=LDAP_USER, password=LDAP_PASSWORD, auto_bind=True) as conn:
            if (conn.bind() == True):
                #print('LDAP Bind Successful')
                return "Login successful"
            else:
                return "Login unsuccessful"
            #print(f'LDAP Bind Successful: {conn.bind()}')
            #conn.search(search_base=SEARCH_BASE, search_filter=LDAP_FILTER)
            #for entry in conn.entries:
            #    print(entry)

    except LDAPException as e:
        return str(e)

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
    id="theme-provider",
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
                                    DashIconify(icon="fa-regular:question-circle"), variant="hover",
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
                                                        DashIconify(icon="akar-icons:globe", width=35,),
                                                        dmc.Text(
                                                            children="Cервис Wake-on-Lan", weight=500, color="indigo", 
                                                            style={"marginTop": 0, "marginBottom": 5, "fontSize": 20}),
                                                    ]
                                                ),
                                                dmc.Stack(
                                                    [
                                                        #dmc.TextInput(
                                                        #    label="Введите имя пользователя:",
                                                        #    id="username",
                                                        #    style={"width": 250},
                                                        #    placeholder="user_name@tvsi.ru",
                                                        #    icon=[DashIconify(icon="radix-icons:person")],
                                                        #),
                                                        dmc.Select(
                                                            label="Выберите пользователя:",
                                                            placeholder="",
                                                            id="user-select",
                                                            searchable=True,
                                                            persistence=True,
                                                            #value="emir_m@tvsi.ru",
                                                            data=[
                                                                {"value": "emir_m@tvsi.ru", "label": "emir_m@tvsi.ru"},
                                                                {"value": "lhagva", "label": "lhagva@tvsi.ru"},
                                                            ],
                                                            style={"width": 250, "marginBottom": 10},
                                                        ),
                                                        dmc.PasswordInput(
                                                            label="Введите пароль:",
                                                            id="password",
                                                            style={"width": 250},
                                                            placeholder="Пароль",
                                                            icon=[DashIconify(icon="radix-icons:lock-closed")],
                                                        ),
                                                    ],
                                                ),
                                                dmc.Button(
                                                    "Авторизация",
                                                    id="submit-btn",
                                                    variant="outline",
                                                    n_clicks=0,
                                                    leftIcon=[DashIconify(icon="el:ok-sign")],
                                                ),
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
                                html.Br(),
                                dmc.Modal(
                                    title="Статус LDAP-авторизации:",
                                    id="modal-centered",
                                    centered=True,
                                    closeOnClickOutside=False,
                                    children=[
                                        dmc.Group(
                                            direction="column", spacing="xl", align="left", 
                                            style={"paddingLeft": 0, "paddingRight": 0, "paddingTop": 10, "paddingBottom": 0},
                                            children=[
                                                dmc.Text(id="modal-text"),
                                                dmc.Text(id="mac-address", children="MAC-адрес:"),
                                                dmc.Text(id="modal-text-wol", children="Статус запроса:"),
                                                dmc.Button(
                                                    "Отправить запрос Wake-on-Lan",
                                                    id="submit-wol",
                                                    variant="outline", compact=False,
                                                    n_clicks=0, size="xs", disabled=False,
                                                ),
                                                dmc.Text(
                                                    children="Внимание! Закрытие данного окна сбросит авторизованную сессию", 
                                                    color="dimmed", size="xs", style={"marginTop": 0, "marginBottom": 0}
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                                #dmc.Text(children="Статус LDAP авторизации:", weight=500, color="dimmed", style={"marginTop": 5, "marginBottom": 5, "fontSize": 15}),
                                #dmc.Text(children=" ", id="text-out", weight=500, color="dimmed", style={"marginTop": 5, "marginBottom": 5, "fontSize": 15}),
                            ],
                        ),
                    ],
                ),
            ]
        ),
    ],
)

@app.callback(
    Output("modal-text", "children"),
    Output("modal-centered", "opened"),
    Output("mac-address", "children"),
    Output("submit-wol", "disabled"),
    Input("submit-btn", "n_clicks"),
    State("user-select", "value"),
    State("password", "value"),
    State("modal-centered", "opened"),
    prevent_initial_call=True,
)
def authorize(n_clicks, username, password, opened):
    if (len(password) > 4):
        login_state = str(ldap_auth(username, password))
        if (login_state == "Login successful"):
            return 'Авторизация прошла успешно', not opened, f"MAC-адрес: {user_mac[username]}", False
        else:
            return f'Ошибка авторизации: {login_state}', not opened, "MAC-адрес: ", True

@app.callback(
    Output("modal-text-wol", "children"),
    Input("submit-wol", "n_clicks"),
    State("user-select", "value"),
    prevent_initial_call=True,
)
def send_wol(n_clicks, username):
    send_magic_packet(user_mac[username], ip_address=user_ip[username])
    return "Статус запроса: отправлен"


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