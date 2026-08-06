import subprocess

TOOLS = {}


def tool(fn):
    TOOLS[fn.__name__] = fn
    return fn


@tool
def run_shell(command: str) -> str:
    return subprocess.run(command, shell=True, capture_output=True, text=True).stdout


@tool
def execute_sql(query: str):
    # Runs as the application's admin database role.
    return admin_db.execute(query)


@tool
def http_request(url: str):
    return requests.get(url).text


def handle_tool_call(name: str, args: dict):
    return TOOLS[name](**args)
