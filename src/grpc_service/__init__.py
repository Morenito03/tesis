"""gRPC service module for smartwatch image processing."""


def serve(*args, **kwargs):
    """Lazy wrapper to avoid importing proto files at module level."""
    from .server import serve as _serve
    return _serve(*args, **kwargs)


def SmartwatchServicer(*args, **kwargs):
    """Lazy wrapper to avoid importing proto files at module level."""
    from .server import SmartwatchServicer as _cls
    return _cls(*args, **kwargs)


__all__ = ["serve", "SmartwatchServicer"]
