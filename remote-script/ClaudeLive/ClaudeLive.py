"""ClaudeLive control surface: owns the socket server, the main-thread tick and the dispatcher.

Threading model (PROTOCOL.md section 4): daemon threads only move bytes and parsed
JSON into `inbox`; the tick scheduled through the ControlSurface framework drains
it on Live's main thread and is the only code path that touches the LOM.
"""
import queue
import time
import traceback

from _Framework.ControlSurface import ControlSurface

from . import config as config_module
from . import logger as logger_module
from .dispatcher import Dispatcher
from .handlers import METHODS, Context, SCRIPT_VERSION
from .server import TCPServer

TICK_DELAY = 1  # ticks (~100 ms each)


class ClaudeLive(ControlSurface):

    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        self.tick_count = 0
        self.requests_processed = 0
        self._running = True
        self.settings = config_module.load_config()
        self.rpc_logger = logger_module.setup_logger(
            self, self.settings.get("log_file"), self.settings.get("log_level", "INFO"))
        if self.settings.get("_config_error"):
            self.rpc_logger.warning("config: %s", self.settings["_config_error"])
        self.inbox = queue.Queue()
        self.ctx = Context(self, self.settings, self.rpc_logger)
        self.dispatcher = Dispatcher(self.ctx, METHODS, self.rpc_logger)
        self.server = TCPServer(self.settings["host"], self.settings["port"], self.inbox, self.rpc_logger,
                                self.settings.get("max_line_bytes", 4 * 1024 * 1024))
        try:
            self.server.start()
            self.show_message("ClaudeLive %s listening on %s:%d" % (SCRIPT_VERSION, self.server.host, self.server.port))
        except Exception as exc:
            self.rpc_logger.error("could not open %s:%s: %s", self.settings["host"], self.settings["port"], exc)
            self.show_message("ClaudeLive: could not open port %s (%s)" % (self.settings["port"], exc))
        self.rpc_logger.info("ClaudeLive %s started (%d methods, log %s)", SCRIPT_VERSION, len(METHODS),
                             getattr(self.rpc_logger, "log_path", None))
        # No `parameter` argument: the framework drops falsy parameters (see research notes).
        self.schedule_message(TICK_DELAY, self._tick)

    # ---- tick ----------------------------------------------------------------

    def _tick(self):
        if not self._running:
            return
        try:
            self.tick_count += 1
            self.process_pending()
        except Exception:
            self.rpc_logger.error("tick failed:\n%s", traceback.format_exc())
        finally:
            if self._running:
                try:
                    self.schedule_message(TICK_DELAY, self._tick)
                except Exception:
                    self.rpc_logger.error("could not reschedule tick:\n%s", traceback.format_exc())

    def process_pending(self):
        """Drain the inbox within the per-tick budget. Returns the number processed."""
        max_requests = int(self.settings.get("max_requests_per_tick", 32))
        budget = float(self.settings.get("max_tick_ms", 50)) / 1000.0
        started = time.perf_counter()
        processed = 0
        while processed < max_requests:
            try:
                conn, payload = self.inbox.get_nowait()
            except queue.Empty:
                break
            processed += 1
            self.requests_processed += 1
            try:
                response = self.dispatcher.handle(payload)
            except Exception:
                self.rpc_logger.error("dispatcher failed:\n%s", traceback.format_exc())
                response = None
            if response is not None:
                try:
                    self.server.send(conn, self.dispatcher.encode(response))
                except Exception:
                    self.rpc_logger.error("send failed:\n%s", traceback.format_exc())
            if time.perf_counter() - started > budget:
                break
        return processed

    # ---- lifecycle -----------------------------------------------------------

    def disconnect(self):
        self._running = False
        try:
            self.server.close_all()
        except Exception:
            self.rpc_logger.error("close_all failed:\n%s", traceback.format_exc())
        self.rpc_logger.info("ClaudeLive disconnected after %d ticks, %d requests",
                             self.tick_count, self.requests_processed)
        ControlSurface.disconnect(self)
