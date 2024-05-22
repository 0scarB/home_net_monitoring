import http.server
import math
import random
import time

COMMAND_RUN_CHECKS            = "run-checks"
COMMAND_SERVE_MONITORING_PAGE = "serve"
STATE_COUNTING_NUMBER_OF_CHECKS = 0
STATE_RUNNING_CHECKS            = 1
STATE_SERVING_MONITORING_PAGE   = 2
CHECK_TYPE_REQUEST_URL = "request_url"
STATUS_SUCCEEDED = "succeeded"
STATUS_FAILED    = "failed"

_command             = ""
state                = -1
checks_file_path     = "./checks.jsonl"
checks_file_handle   = None
checks_n             = 0
current_check        = 0
monitoring_page_ip   = "127.0.0.1"
monitoring_page_port = 8000


def command(command_):
    global _command
    _command = command_


def run_monitor(func):
    global state, checks_file_handle

    if _command == COMMAND_RUN_CHECKS:
        state = STATE_COUNTING_NUMBER_OF_CHECKS
        func()
        state = STATE_RUNNING_CHECKS
        with open(checks_file_path, "a") as checks_file_handle:
            while current_check < checks_n:
                timestamp = math.floor(time.time())
                if checks_file_handle == None: raise Exception
                checks_file_handle.write('{"timestamp": ' + str(timestamp) + ', "checks": [')
                func()
                checks_file_handle.write("]}\n")
        return
    if _command == COMMAND_SERVE_MONITORING_PAGE:
        serve_monitoring_page()
        return
    raise Exception


def next_check():
    if state == STATE_COUNTING_NUMBER_OF_CHECKS:
        global checks_n
        checks_n += 1
        return False
    if state == STATE_RUNNING_CHECKS:
        global current_check
        print(f"Running check {current_check}.")
        current_check += 1
        return True
    if state == STATE_SERVING_MONITORING_PAGE:
        return False
    raise Exception


def request_url(url):
    print(f"Making request to '{url}'.")
    print("Not implemented!")
    response_time = random.randrange(1000)/1000
    if checks_file_handle == None: raise Exception
    checks_file_handle.write('{"type": "'  + CHECK_TYPE_REQUEST_URL + '", ')
    checks_file_handle.write('"status": "' + STATUS_SUCCEEDED          + '", ')
    checks_file_handle.write('"url": "'    + url                       + '", ')
    checks_file_handle.write('"response_time_in_secs": '
                                           + str(response_time)        + '}'  )
    if current_check < checks_n:
        checks_file_handle.write(", ")


def serve_monitoring_page():

    class RequestHandler(http.server.BaseHTTPRequestHandler):

        def do_GET(self):
            if self.path == "/":
                response_content = build_monitoring_page_html()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(response_content)))
                self.end_headers()
                self.wfile.write(bytes(response_content, "utf-8"))
            elif self.path == "/index.js":
                # Uncomment for "dev"
                with open(__file__[:-len("__init__.py")] + "index.js") as f:
                    response_content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/javascript; charset=utf-8")
                self.send_header("Content-Length", str(len(response_content)))
                self.end_headers()
                self.wfile.write(bytes(response_content, "utf-8"))

                # Uncomment for "prod"
                #self.send_response(200)
                #self.send_header("Content-Type", "application/javascript; charset=utf-8")
                #self.send_header("Content-Length", str(len(EMBEDDED_JAVASCRIPT_FILE_BYTES)))
                #self.end_headers()
                #self.wfile.write(EMBEDDED_JAVASCRIPT_FILE_BYTES)
            elif self.path.startswith("/checks"):
                # Attempt to parse start and end timestamps in query string
                start_timestamp = -1
                end_timestamp   = -1
                try:
                    i = len("/checks")
                    if self.path[i] != '?':
                        raise
                    i += 1
                    if self.path[i:i + 6] != "start=":
                        raise
                    i += 6
                    timestamp_start_i = i
                    while self.path[i].isdigit():
                        i += 1
                    start_timestamp = int(self.path[timestamp_start_i:i])
                    if self.path[i] != '&':
                        raise
                    i += 1
                    if self.path[i:i + 4] != "end=":
                        raise
                    i += 4
                    timestamp_start_i = i
                    while i < len(self.path) and self.path[i].isdigit():
                        i += 1
                    end_timestamp = int(self.path[timestamp_start_i:i])
                # Reponse with 400 on failure
                except Exception:
                    response_content = "Invalid /checks request!"
                    self.send_response(400)
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                    self.send_header("Content-Length", str(len(response_content)))
                    self.end_headers()
                    self.wfile.write(bytes(response_content, "utf-8"))
                # Respond with JSON on success
                else:
                    timestamp_line_offset = len('{"timestamp": ')
                    response_content = "["
                    with open(checks_file_path) as f:
                        first_item = True
                        for line in f.readlines():
                            i = timestamp_start_i = timestamp_line_offset
                            while i < len(line) and line[i].isdigit():
                                i += 1
                            timestamp = int(line[timestamp_start_i:i])
                            if start_timestamp <= timestamp <= end_timestamp:
                                if first_item:
                                    first_item = False
                                else:
                                    response_content += ", "
                                response_content += line[:-1]
                    response_content += "]"

                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Content-Length", str(len(response_content)))
                    self.end_headers()
                    self.wfile.write(bytes(response_content, "utf-8"))
            else:
                response_content = "File not found!"
                self.send_response(404)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(response_content)))
                self.end_headers()
                self.wfile.write(bytes(response_content, "utf-8"))

    server = http.server.HTTPServer(
            (monitoring_page_ip, monitoring_page_port),
            RequestHandler)
    server.serve_forever()


def build_monitoring_page_html():
    NODE_TYPE_HTML     = 0
    NODE_TYPE_CSS_RULE = 1

    html = ""
    node_stack = []

    def tag(name, **attrs):
        nonlocal html
        html += "<" + name
        for attr_name, attr_value in attrs.items():
            html += " " + attr_name + "=\"" + attr_value + "\""
        html += ">"
        node_stack.append((NODE_TYPE_HTML, name))
        return True

    def end(void=False):
        nonlocal html
        node_type, node_name = node_stack.pop()
        if node_type == NODE_TYPE_HTML:
            if not void:
                html += "</" + node_name + ">"
        elif node_type == NODE_TYPE_CSS_RULE:
            html += "} "

    def text(s):
        nonlocal html
        html += s

    def doctype():
        nonlocal html
        html += "<!DOCTYPE HTML>"

    def rule(css_selector):
        nonlocal html
        html += css_selector + " {"
        node_stack.append((NODE_TYPE_CSS_RULE, css_selector))
        return True

    def prop(css_prop_name, css_prop_value):
        nonlocal html
        html += css_prop_name + ": " + str(css_prop_value) + "; "

    page_title = "Monitoring"
    doctype()
    if tag("html"):
        if tag("head"):
            tag("title"); text(page_title); end()
            tag("script", src="index.js"); end()
            if tag("style"):
                if rule("html, body, main"):
                    prop("padding", 0)
                    prop("margin", 0)
                    prop("color", "#FFF")
                    prop("background-color", "#000")
                    prop("font-family", "sans-serif")
                end()
            end()
        end()
        if tag("body"):
            if tag("main"):
                tag("h1"); text(page_title); end()
            end()
        end()
    end()

    return html


EMBEDDED_JAVASCRIPT_FILE_BYTES = b"\x61\x73\x79\x6E\x63\x20\x66\x75\x6E\x63\x74\x69\x6F\x6E\x20\x6D\x61\x69\x6E\x28\x29\x20\x7B\x0A\x20\x20\x20\x20\x72\x65\x73\x20\x3D\x20\x61\x77\x61\x69\x74\x20\x66\x65\x74\x63\x68\x28\x60\x2F\x63\x68\x65\x63\x6B\x73\x3F\x73\x74\x61\x72\x74\x3D\x30\x26\x65\x6E\x64\x3D\x24\x7B\x4D\x61\x74\x68\x2E\x63\x65\x69\x6C\x28\x44\x61\x74\x65\x2E\x6E\x6F\x77\x28\x29\x2F\x31\x30\x30\x30\x29\x7D\x60\x29\x0A\x20\x20\x20\x20\x63\x68\x65\x63\x6B\x73\x20\x3D\x20\x72\x65\x73\x2E\x6A\x73\x6F\x6E\x28\x29\x0A\x20\x20\x20\x20\x63\x6F\x6E\x73\x6F\x6C\x65\x2E\x6C\x6F\x67\x28\x63\x68\x65\x63\x6B\x73\x29\x0A\x7D\x0A\x0A\x6D\x61\x69\x6E\x28\x29\x0A\x0A"
