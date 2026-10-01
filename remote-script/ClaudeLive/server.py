"""Localhost TCP server. Runs entirely on daemon threads and never touches the LOM.

- One accept thread; one reader thread and one writer thread per connection.
- Reader threads split the byte stream on "\\n", parse JSON and push
  (connection, request_or_FrameError) onto a *bounded* queue.Queue. When the
  queue is full they block (back-pressure through TCP) instead of growing memory.
  The main-thread tick (ClaudeLive.py) drains that queue.
- send(conn, line) is called from the main thread and only enqueues the line on
  the connection's outbox; the connection's writer thread does the blocking
  sendall(). A client that stops reading can therefore never stall Live's UI.
- At most `max_connections` clients are served; extra connections are closed
  right after accept.
"""
import json
import queue
import socket
import threading

from . import errors

RECV_SIZE = 65536
SOCKET_TIMEOUT = 5.0  # seconds; keeps reader/writer threads responsive
OUTBOX_MAX = 1024  # pending response lines per connection before the client is dropped
QUEUE_PUT_TIMEOUT = 0.5  # seconds between stop-flag checks while the inbox is full
WRITER_JOIN_TIMEOUT = 0.5  # seconds close() waits for the writer thread
DEFAULT_MAX_CONNECTIONS = 8


class Connection(object):
    """One accepted client socket with its own writer thread."""

    _counter = 0
    _counter_lock = threading.Lock()

    def __init__(self, sock, address, start_writer=True):
        with Connection._counter_lock:
            Connection._counter += 1
            self.id = Connection._counter
        self.sock = sock
        self.address = address
        self.closed = False
        self._close_lock = threading.Lock()
        self.outbox = queue.Queue(maxsize=OUTBOX_MAX)
        self.lines_sent = 0
        self._writer = None
        if start_writer:
            self._writer = threading.Thread(
                target=self._write_loop, name="ClaudeLive-writer-%d" % self.id, daemon=True)
            self._writer.start()

    # ---- main-thread side -------------------------------------------------

    def send_line(self, data):
        """Queue one framed line (bytes, newline-terminated). Never blocks on the socket."""
        if self.closed:
            return False
        try:
            self.outbox.put_nowait(data)
            return True
        except queue.Full:
            # The client has stopped reading; it is not coming back for these.
            self.close()
            return False

    # ---- writer thread ----------------------------------------------------

    def _write_loop(self):
        while not self.closed:
            try:
                data = self.outbox.get(timeout=QUEUE_PUT_TIMEOUT)
            except queue.Empty:
                continue
            if data is None:  # close() sentinel
                break
            try:
                self.sock.sendall(data)
                self.lines_sent += 1
            except (OSError, socket.error, ValueError):
                self.close()
                break

    # ---- lifecycle --------------------------------------------------------

    def close(self):
        """Idempotent. Safe against a concurrent writer: flag -> shutdown -> sentinel -> join -> close."""
        with self._close_lock:
            if self.closed:
                return
            self.closed = True
        try:
            self.sock.shutdown(socket.SHUT_RDWR)  # wakes a blocked recv()/sendall()
        except (OSError, socket.error):
            pass
        try:
            self.outbox.put_nowait(None)
        except queue.Full:
            pass  # the writer checks `closed` after its current line
        writer = self._writer
        if writer is not None and writer is not threading.current_thread():
            writer.join(WRITER_JOIN_TIMEOUT)
        try:
            self.sock.close()
        except (OSError, socket.error):
            pass

    def __repr__(self):
        return "Connection(%d, %r)" % (self.id, self.address)


class TCPServer(object):
    """Newline-delimited JSON listener bound to 127.0.0.1."""

    def __init__(self, host, port, inbox, logger, max_line_bytes=4 * 1024 * 1024,
                 max_connections=DEFAULT_MAX_CONNECTIONS):
        self.host = host
        self.requested_port = port
        self.port = None
        self.inbox = inbox
        self.logger = logger
        self.max_line_bytes = max_line_bytes
        self.max_connections = max(1, int(max_connections))
        self.running = False
        self._listener = None
        self._accept_thread = None
        self._connections = {}
        self._connections_lock = threading.Lock()
        self.lines_received = 0
        self.connections_refused = 0

    # ---- lifecycle -------------------------------------------------------

    def start(self):
        """Bind, listen and start the accept thread. Raises OSError if the port is taken."""
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            listener.bind((self.host, self.requested_port))
            listener.listen(8)
        except Exception:
            listener.close()
            raise
        listener.settimeout(1.0)
        self._listener = listener
        self.port = listener.getsockname()[1]
        self.running = True
        self._accept_thread = threading.Thread(
            target=self._accept_loop, name="ClaudeLive-accept", daemon=True)
        self._accept_thread.start()
        self.logger.info("listening on %s:%d", self.host, self.port)

    def close_all(self):
        """Stop accepting and drop every client. Safe to call twice."""
        self.running = False
        listener = self._listener
        self._listener = None
        if listener is not None:
            try:
                listener.shutdown(socket.SHUT_RDWR)  # wakes a blocked accept() immediately
            except (OSError, socket.error):
                pass
            try:
                listener.close()
            except (OSError, socket.error):
                pass
        with self._connections_lock:
            conns = list(self._connections.values())
            self._connections.clear()
        for conn in conns:
            conn.close()
        thread = self._accept_thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(2.0)
        self._accept_thread = None

    stop = close_all

    @property
    def connection_count(self):
        with self._connections_lock:
            return len(self._connections)

    def connections(self):
        with self._connections_lock:
            return list(self._connections.values())

    # ---- main-thread entry point ---------------------------------------

    def send(self, conn, data):
        """Hand one encoded response line to a connection's outbox (duck-typed: needs send_line)."""
        if isinstance(data, str):
            data = data.encode("utf-8")
        try:
            return conn.send_line(data)
        except Exception as exc:
            self.logger.warning("send failed on %r: %s", conn, exc)
            return False

    # ---- threads ---------------------------------------------------------

    def _accept_loop(self):
        while self.running:
            listener = self._listener
            if listener is None:
                break
            try:
                sock, address = listener.accept()
            except socket.timeout:
                continue
            except (OSError, socket.error):
                if self.running:
                    self.logger.debug("accept() failed; retrying")
                continue
            if not self.running:
                try:
                    sock.close()
                except (OSError, socket.error):
                    pass
                break
            with self._connections_lock:
                at_capacity = len(self._connections) >= self.max_connections
            if at_capacity:
                self.connections_refused += 1
                self.logger.warning("refusing connection from %r: already serving %d clients (max_connections)",
                                    address, self.max_connections)
                try:
                    sock.close()
                except (OSError, socket.error):
                    pass
                continue
            try:
                sock.settimeout(SOCKET_TIMEOUT)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            except (OSError, socket.error):
                pass
            conn = Connection(sock, address)
            with self._connections_lock:
                # close_all() clears `running` before it takes this lock, so a connection
                # accepted during shutdown is never left registered behind its back.
                if not self.running:
                    conn.close()
                    break
                self._connections[conn.id] = conn
            self.logger.info("client connected: %r", conn)
            reader = threading.Thread(
                target=self._reader_loop, args=(conn,), name="ClaudeLive-reader-%d" % conn.id, daemon=True)
            reader.start()

    def _push(self, conn, payload):
        """Queue a request; block (with back-pressure) while the inbox is full."""
        while self.running and not conn.closed:
            try:
                self.inbox.put((conn, payload), timeout=QUEUE_PUT_TIMEOUT)
                return True
            except queue.Full:
                continue
        return False

    def _reader_loop(self, conn):
        buf = bytearray()
        discarding = False
        try:
            while self.running and not conn.closed:
                try:
                    chunk = conn.sock.recv(RECV_SIZE)
                except socket.timeout:
                    continue
                except (OSError, socket.error, ValueError):
                    break
                if not chunk:
                    break
                buf += chunk
                while True:
                    newline = buf.find(b"\n")
                    if newline < 0:
                        if len(buf) > self.max_line_bytes:
                            # The line is already too long; drop what we have and
                            # keep dropping until the terminating newline arrives.
                            discarding = True
                            del buf[:]
                        break
                    line = bytes(buf[:newline])
                    del buf[:newline + 1]
                    if discarding:
                        discarding = False
                        self._push(conn, errors.FrameError(
                            errors.INVALID_REQUEST,
                            "Line too long (limit is %d bytes)" % self.max_line_bytes))
                        continue
                    self._handle_line(conn, line)
        except Exception as exc:  # never let a reader thread die noisily
            self.logger.warning("reader for %r failed: %s", conn, exc)
        finally:
            conn.close()
            with self._connections_lock:
                self._connections.pop(conn.id, None)
            self.logger.info("client disconnected: %r", conn)

    def _handle_line(self, conn, line):
        if len(line) > self.max_line_bytes:
            self._push(conn, errors.FrameError(
                errors.INVALID_REQUEST, "Line too long (limit is %d bytes)" % self.max_line_bytes))
            return
        stripped = line.strip()
        if not stripped:
            return
        self.lines_received += 1
        try:
            payload = json.loads(stripped.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            self._push(conn, errors.FrameError(errors.PARSE_ERROR, "Parse error: %s" % exc))
            return
        self._push(conn, payload)
