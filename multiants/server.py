# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import cast, TYPE_CHECKING
from typing import Any, Dict, Type, Optional

if TYPE_CHECKING:
    from pendulum.datetime import DateTime
    from .model import Model

import asyncio
import socketio
import pendulum
from math import ceil
from aiohttp import web
from .model_encoder import ModelEncoder
from .logger import Logger


class Server:
    def __init__(self, model_cls: Type[Model], config: Dict[str, Any]):
        """
        A webserver to run the model and send data to the client through a websocket.

        :param model_cls: mesa model class.
        :param model_config: model configuration.
        """
        self._model_cls = model_cls
        self._model_config = config
        self._logger = Logger()
        self._sio = socketio.AsyncServer(
            async_mode="aiohttp",
            cors_allowed_origins="*",
        )
        self._app = web.Application()
        self._sio.attach(self._app)
        self._working: bool = False
        self.init_model()

    @property
    def model_cls(self) -> Type[Model]:
        return self._model_cls

    @property
    def model_config(self) -> Dict[str, Any]:
        return self._model_config

    @property
    def logger(self) -> Logger:
        return self._logger

    @property
    def sio(self) -> socketio.AsyncServer:
        return self._sio

    @property
    def app(self) -> web.Application:
        return self._app

    @property
    def working(self) -> bool:
        return self._working

    def init_model(self):
        """
        Init the model by instantiating a model object.
        """
        self._working = False
        self.model = self.model_cls(config=self.model_config, logger=self.logger)

    def get_remaining_step_from_date(self, goal_date: DateTime) -> int:
        """
        Calculates the number of steps needed to reach a specified date
        in relation to the given time step and a goal date to reach.

        :param goal_date: date when the simulation will be ended.
        :return: the number of time step to render.
        """
        delta = goal_date - self.model.time.current
        return ceil(
            delta / self.model.time.timestep  # pyright: ignore [reportGeneralTypeIssues]
        )

    async def handle_http(self, request: web.Request) -> web.Response:
        """
        Returns a warning for users who have reached this endpoint,
        they must use a client.
        """
        del request
        return web.Response(
            text=(
                "Please use the client interface to control and "
                "visualise the simulation, this server just serves a websocket"
            )
        )

    async def state(self) -> Dict:
        """
        Generates the state message.

        :return: a serialisable model state.
        """
        return cast(
            Dict[str, Any],
            ModelEncoder(self.model.grid.transformer)
            # just pre encode the model, serialisation will be done by socketio
            .pre_encode(self.model),
        )

    async def render(self) -> Dict:
        """
        Renders one step and returns the new state.

        :return: a serialisable model state.
        """
        self.model.step()
        return await self.state()

    async def reset(self) -> Dict:
        """
        Reset the model and returns the new state.

        :return: a serialisable model state.
        """
        self.init_model()
        return await self.state()

    def init_routes(self) -> int:
        """
        Initialise HTTP routes and websocket events.

        :return: the number of generated routes.
        """
        self.app.add_routes([web.get("/", self.handle_http)])

        @self.sio.event
        async def connect(sid: str, environ):
            """Handle connect and sends a ready message."""
            del environ
            self.logger.system_log(f"WS CONNECT: {sid}")
            await self.sio.emit("ready")

        @self.sio.event
        async def get_state(sid: str):
            """Sends state."""
            del sid
            await self.sio.emit("state", await self.state())

        @self.sio.event
        async def is_working(sid: str):
            """Sends working if a task is running."""
            del sid
            if self.working:
                await self.sio.emit("working")

        @self.sio.event
        async def disconnect(sid: str):
            """Handle disconnect."""
            self.logger.system_log(f"WS DISCONNECT: {sid}")

        @self.sio.event
        async def start(
            sid: str,
            options: Optional[Dict[str, int] | Dict[str, str]] = None,
        ):
            """
            Starts the server.

            :param options:
                one key dictionnary to specify a number of steps to
                do or a date to reach {"step": ...} or {"date": ...}.
                If it is None, run indefinitely.
            """
            self.logger.system_log(f"WS START MODEL: {sid} {options}")
            remaining: float = float("inf")
            if options:
                if "step" in options:
                    # run for a specified number of steps
                    remaining = cast(int, options["step"])
                elif "date" in options:
                    # run until specified date is reached
                    remaining = self.get_remaining_step_from_date(
                        pendulum.parse(  # pyright: ignore [reportUndefinedVariable]
                            options["date"]
                        )
                    )
            # Run steps one by one in an asynchronous task
            self._working = True
            await self.sio.emit("working")
            while self.working and remaining > 0:
                remaining -= 1
                task = asyncio.create_task(self.render())
                # Send new state to client
                await self.sio.emit("state", await task)
                # Log
                self.logger.system_log(f"NEW STATE: {self.model.time.current}")
            await self.sio.emit("ready")

        @self.sio.event
        async def stop(sid: str):
            """Handle manual stops."""
            self._working = False
            self.logger.system_log(f"WS STOP MODEL: {sid}")

        @self.sio.event
        async def reset(sid: str):
            """Handle reset and sends the new state."""
            self.logger.system_log(f"WS RESET MODEL: {sid}")
            await self.sio.emit("working")
            task = asyncio.create_task(self.reset())
            await self.sio.emit("state", await task)
            await self.sio.emit("ready")

        # The following line removes false unused warning about routes functions
        return len([connect, get_state, is_working, disconnect, start, stop, reset])

    def start(self, host: str, port: int):
        """Launch server.

        Args:
            host: hostname of the server.
            port: port on which the server listen to.
        """
        web.run_app(self.app, host=host, port=port)
