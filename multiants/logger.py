import pendulum
from enum import Enum
from collections import namedtuple
from colorama import Fore, Style


__all__ = ["Logger", "NoLogger"]


class Level(Enum):
    NONE = Fore.WHITE
    INFO = Fore.YELLOW
    ERROR = Fore.RED
    MODEL = Fore.BLUE


class Logger:
    def __init__(self, timezone=None):
        self._buffer = []
        if timezone is None:
            self._timezone = pendulum.now().timezone
        else:
            self._timezone = pendulum.timezone(timezone)

    def system_time(self):
        return pendulum.now(tz=self._timezone)

    def model_log(
        self,
        message,
        model,
        error=False,
        add_to_buffer=True,
        print_replace=False,
    ):
        if error:
            self.log(
                message,
                model.time.current,
                Level.ERROR,
                add_to_buffer,
                print_replace,
            )
        else:
            self.log(
                message,
                model.time.current,
                Level.MODEL,
                add_to_buffer,
                print_replace,
            )

    def system_log(
        self,
        message,
        error=False,
        add_to_buffer=True,
        print_replace=False,
    ):
        if error:
            self.log(
                message,
                self.system_time(),
                Level.ERROR,
                add_to_buffer,
                print_replace,
            )
        else:
            self.log(
                message,
                self.system_time(),
                Level.INFO,
                add_to_buffer,
                print_replace,
            )

    def log(
        self,
        message: str,
        time: pendulum.DateTime,
        level: Level.NONE,
        add_to_buffer=True,
        print_replace=False,
    ):
        """Log message"""
        formated_message = f"[{time}] [{level.name}] {message}"
        coloured_message = f"{level.value}{formated_message}{Style.RESET_ALL}"
        # Print in python
        print(
            f"{coloured_message}{' ' * 5 if print_replace else ''}",
            end="\n" if not print_replace else "\r",
        )
        # Add to messages buffer, will be sent to connected clients over the
        # websocket
        if add_to_buffer:
            self._buffer.append(formated_message)

    def get_oldest_message(self) -> str:
        return self._buffer.pop(0)

    def buffered_messages(self) -> list[str]:
        messages = self._buffer[:]
        self._buffer = []
        return messages


class NoLogger(Logger):
    def model_log(
        self,
        message,
        model,
        error=False,
        add_to_buffer=True,
        print_replace=False,
    ):
        pass

    def system_log(
        self,
        message,
        error=False,
        add_to_buffer=True,
        print_replace=False,
    ):
        pass

    def log(
        self,
        message: str,
        time: pendulum.DateTime,
        level: Level.NONE,
        add_to_buffer=True,
        print_replace=False,
    ):
        pass


if __name__ == "__main__":
    Model = namedtuple("Model", ["time"])
    Time = namedtuple("Time", ["current"])

    model = Model(Time(pendulum.now()))

    logger = Logger()
    logger.log("FUCK", pendulum.now(), Level.ERROR)

    logger.model_log("FUCK", model)
