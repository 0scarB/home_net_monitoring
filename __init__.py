import http.server
import math
import random
import time

COMMAND_RUN_CHECKS            = "run-checks"
COMMAND_SERVE_MONITORING_PAGE = "serve"
STATE_COUNTING_NUMBER_OF_CHECKS = 0
STATE_RUNNING_CHECKS            = 1
STATE_SERVING_MONITORING_PAGE   = 2
SUBCHECK_TYPE_REQUEST_URL = "request_url"
STATUS_SUCCEEDED = "succeeded"
STATUS_FAILED    = "failed"

_command             = ""
state                = -1
checks_file_path     = "./checks.jsonld"
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
                checks_file_handle.write('{"timestamp": ' + str(timestamp) + ', checks: [')
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
    checks_file_handle.write('{"type": "'  + SUBCHECK_TYPE_REQUEST_URL + '", ')
    checks_file_handle.write('"status": "' + STATUS_SUCCEEDED          + '", ')
    checks_file_handle.write('"url": "'    + url                       + '", ')
    checks_file_handle.write('"response_time_in_secs": "'
                                           + str(response_time)        + '"}')
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
                self.send_response(200)
                self.send_header("Content-Type", "application/javascript; charset=utf-8")
                self.send_header("Content-Length", str(len(EMBEDDED_JAVASCRIPT_FILE_BYTES)))
                self.end_headers()
                self.wfile.write(EMBEDDED_JAVASCRIPT_FILE_BYTES)
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


EMBEDDED_JAVASCRIPT_FILE_BYTES = b"\x63\x6F\x6E\x73\x6F\x6C\x65\x2E\x6C\x6F\x67\x28\x22\x48\x65\x6C\x6C\x6F\x2C\x20\x57\x6F\x72\x6C\x64\x21\x22\x29\x3B\x0A"
