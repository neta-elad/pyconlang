from typing import List, Optional

class FileSystemEvent: ...
class FileSystemEventHandler: ...

class PatternMatchingEventHandler(FileSystemEventHandler):
    def __init__(
        self,
        patterns: Optional[List[str]] = None,
        ignore_patterns: Optional[List[str]] = None,
        ignore_directories: bool = False,
        case_sensitive: bool = False,
    ) -> None: ...
