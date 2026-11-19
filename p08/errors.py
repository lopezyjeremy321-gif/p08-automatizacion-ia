class P08Error(Exception):
    """Base de errores del proyecto. Los mensajes nunca contienen datos del correo."""


class ValidationError(P08Error):
    pass


class ApprovalError(P08Error):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code
