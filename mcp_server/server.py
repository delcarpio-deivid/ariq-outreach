"""FastMCP server entry point with auto-discovery of tools."""

from __future__ import annotations

import importlib
import logging
import pkgutil

from fastmcp import FastMCP

import mcp_server.tools as tools_package

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("ariq-outreach")


def _register_tools() -> None:
    for module_info in pkgutil.iter_modules(tools_package.__path__):
        if module_info.name.startswith("_"):
            continue
        module = importlib.import_module(f"mcp_server.tools.{module_info.name}")
        register = getattr(module, "register", None)
        if callable(register):
            register(mcp)
            logger.info("Registered tools from mcp_server.tools.%s", module_info.name)


_register_tools()


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
