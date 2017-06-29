from http.server import BaseHTTPRequestHandler, HTTPServer


class Collector(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        # TODO Do the ioctl to the custom isgx driver
        self.wfile.write(b"Hello, World!\n")


def run_server_forever():
    httpd = HTTPServer(('', 4567), Collector)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run_server_forever()
