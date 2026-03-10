DEFAULT_EMAIL_TEMPLATES = {
    "email_confirmation": {
        "subject": "Verifica tu correo",
        "text_template": "jb_drf_auth/mailing/email_confirmation.txt",
        "html_template": "jb_drf_auth/mailing/email_confirmation.html",
    },
    "password_reset": {
        "subject": "Restablece tu contraseña",
        "text_template": "jb_drf_auth/mailing/password_reset.txt",
        "html_template": "jb_drf_auth/mailing/password_reset.html",
    },
}

DEFAULT_MAILING = {
    "brand": {
        "app_name": "Mentalysis",
        "company_name": "MENTALYSIS SAPI DE CV",
    },
    "theme": {
        "primary": "#0071CE",
        "background": "#E7E7E7",
        "surface": "#FFFFFF",
        "text_primary": "#212B35",
        "text_secondary": "#637381",
        "divider": "#DFE3E8",
        "link": "#0071CE",
    },
    "assets": {
        "logo_url": "",
        "logo_alt": "Logo",
    },
    "links": {
        "logo_href": "",
        "privacy_url": "",
        "unsubscribe_url": "",
    },
    "templates": DEFAULT_EMAIL_TEMPLATES,
}
