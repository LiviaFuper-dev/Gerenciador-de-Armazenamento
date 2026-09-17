class AppError(Exception):
    """Erro esperado que pode ser mostrado diretamente na interface."""


class MissingClientSecretError(AppError):
    """O arquivo OAuth do Google ainda não foi configurado."""


class WrongAccountError(AppError):
    """Uma conta diferente da conta autorizada para o piloto foi conectada."""


class OperationCancelled(AppError):
    """A operação foi cancelada antes de alterar mensagens."""

