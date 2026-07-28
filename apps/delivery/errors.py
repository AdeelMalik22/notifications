class PermanentProviderError(Exception):
    """The provider rejected the message permanently."""


class TransientProviderError(Exception):
    """The provider may accept a later retry."""


class AmbiguousProviderError(Exception):
    """The provider outcome cannot safely be inferred after a timeout."""
