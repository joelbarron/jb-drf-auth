DEFAULT_EMAIL_TEMPLATES = {
    "email_confirmation": {
        "subject": "Verifica tu correo",
        "text": (
            "Hola {user_email},\n\n"
            "Verifica tu correo usando este enlace:\n"
            "{verify_url}\n\n"
            "Si no solicitaste esta acción, ignora este mensaje."
        ),
        "html": (
            "<!doctype html>"
            "<html>"
            "<body style=\"margin:0;padding:0;background:#f7f7f7;font-family:Arial,sans-serif;\">"
            "<div style=\"max-width:560px;margin:24px auto;background:#ffffff;border-radius:12px;"
            "padding:24px;box-shadow:0 8px 24px rgba(0,0,0,.08);\">"
            "<h2 style=\"margin:0 0 12px 0;color:#111;\">Verifica tu correo</h2>"
            "<p style=\"margin:0 0 16px 0;color:#444;\">Hola {user_email},</p>"
            "<p style=\"margin:0 0 20px 0;color:#444;\">"
            "Confirma tu cuenta haciendo clic en el botón:"
            "</p>"
            "<a href=\"{verify_url}\" "
            "style=\"display:inline-block;padding:12px 18px;background:#111;color:#fff;"
            "text-decoration:none;border-radius:8px;\">Verificar correo</a>"
            "<p style=\"margin:20px 0 0 0;color:#777;font-size:12px;\">"
            "Si no solicitaste esta acción, ignora este mensaje."
            "</p>"
            "</div>"
            "</body>"
            "</html>"
        ),
    },
    "password_reset": {
        "subject": "Restablece tu contraseña",
        "text": (
            "Hola {user_email},\n\n"
            "Restablece tu contraseña usando este enlace:\n"
            "{reset_url}\n\n"
            "Si no solicitaste este cambio, ignora este mensaje."
        ),
        "html": (
            "<!doctype html>"
            "<html>"
            "<body style=\"margin:0;padding:0;background:#f7f7f7;font-family:Arial,sans-serif;\">"
            "<div style=\"max-width:560px;margin:24px auto;background:#ffffff;border-radius:12px;"
            "padding:24px;box-shadow:0 8px 24px rgba(0,0,0,.08);\">"
            "<h2 style=\"margin:0 0 12px 0;color:#111;\">Restablece tu contraseña</h2>"
            "<p style=\"margin:0 0 16px 0;color:#444;\">Hola {user_email},</p>"
            "<p style=\"margin:0 0 20px 0;color:#444;\">"
            "Haz clic en el botón para cambiar tu contraseña:"
            "</p>"
            "<a href=\"{reset_url}\" "
            "style=\"display:inline-block;padding:12px 18px;background:#111;color:#fff;"
            "text-decoration:none;border-radius:8px;\">Restablecer</a>"
            "<p style=\"margin:20px 0 0 0;color:#777;font-size:12px;\">"
            "Si no solicitaste este cambio, ignora este mensaje."
            "</p>"
            "</div>"
            "</body>"
            "</html>"
        ),
    },
}
