"""Functions that use streams (open files)."""


def get_file_size(stream) -> int:
    """Given a seekable file, return its size."""
    assert stream.seekable(), 'Streams of type {} are not seekable'.format(
        type(stream))
    stream.seek(0, 2)  # Seek to the end of the stream
    size = stream.tell()  # Get the position of EOF
    stream.seek(0)  # Reset the stream position to the beginning
    return size
