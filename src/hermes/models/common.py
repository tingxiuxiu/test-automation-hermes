from pydantic import BaseModel


class PopenOutput(BaseModel):
    stdout: bytes
    stderr: bytes

    def get_stdout(self) -> str:
        return self.stdout.decode("utf-8", errors="replace")

    def get_stderr(self) -> str:
        return self.stderr.decode("utf-8", errors="replace")

    def get_stdout_list(self) -> list[str]:
        return self.stdout.decode("utf-8", errors="replace").split("\n")

    def get_stderr_list(self) -> list[str]:
        return self.stderr.decode("utf-8", errors="replace").split("\n")
