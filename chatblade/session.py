import glob
import re
import os

from . import storage


def list_sessions():
    """List names of sessions"""
    sess_paths = glob.glob(os.path.join(storage.get_cache_path(), "*.yaml"))
    return sorted(
        [
            re.sub("\\.yaml\\Z", "", os.path.basename(sess_path))
            for sess_path in sess_paths
        ]
    )


def rename_session(session, newname):
    """renames session
    Returns None on success, error string otherwise"""
    session_path = storage.get_session_path(session, True)
    if not session_path:
        return f"session {session} does not exist"
    new_session_path = storage.get_session_path(newname, True)
    if new_session_path:
        return f"session {newname} already exists"
    new_session_path = storage.get_session_path(newname)
    os.rename(session_path, new_session_path)


def delete_session(session):
    """deletes a session
    Returns None on success, error string otherwise"""
    session_path = storage.get_session_path(session, True)
    if not session_path:
        return f"session {session} does not exist"
    os.unlink(session_path)
