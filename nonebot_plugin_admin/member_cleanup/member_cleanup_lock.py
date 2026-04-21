from pathlib import Path


def get_cleanup_lock_path(lock_root: Path, group_id: int) -> Path:
    """
    获取清理锁路径
    :param lock_root: lock_root 参数
    :param group_id: 群号
    :return: Path
    """
    return lock_root / f"{group_id}.lock"


def ensure_cleanup_lock(lock_path: Path) -> bool:
    """
    确保清理锁
    :param lock_path: 路径对象
    :return: bool
    """
    if lock_path.exists():
        return False
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.touch()
    return True


def clear_cleanup_lock(lock_path: Path) -> None:
    """
    清理清理锁
    :param lock_path: 路径对象
    :return: None
    """
    if lock_path.exists():
        lock_path.unlink()


