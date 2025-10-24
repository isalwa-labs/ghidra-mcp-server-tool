#!/usr/bin/env python3
"""
Ghidra MCP Server - Basic Version
A simple MCP server for Ghidra binary analysis tasks
Author: Isaac Isalwa

LEARNING NOTES:
- MCP uses stdio (standard input/output) to communicate
- Messages are JSON-RPC 2.0 format
- We define "tools" that Claude can call
- Each tool has a handler function
"""

import asyncio
import json
import sys
import os
import subprocess
from typing import Any, Sequence
from pathlib import Path

# For MCP protocol
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

class GhidraMCPServer:
    """
    Simple Ghidra MCP Server
    
    This server provides basic binary analysis capabilities:
    1. analyze_binary - Get basic info about a binary file
    2. list_functions - List all functions in a binary
    3. decompile_function - Decompile a specific function
    4. extract_strings - Find strings in the binary
    """
    
    def __init__(self):
        self.server = Server("ghidra-mcp")
        self.ghidra_path = self._find_ghidra()
        self.workspace = Path.home() / ".ghidra_mcp_workspace"
        self.workspace.mkdir(exist_ok=True)
        
        # Register our tools and handlers
        self._register_handlers()
    
    def _find_ghidra(self) -> str:
        """Find Ghidra installation path"""
        # Common Ghidra paths
        common_paths = [
            "/opt/ghidra",
            "/usr/local/ghidra",
            str(Path.home() / "ghidra"),
            os.environ.get("GHIDRA_INSTALL_DIR", "")
        ]
        
        for path in common_paths:
            if path and Path(path).exists():
                return path
        
        # If not found, we'll use basic tools instead
        return None
    
    def _register_handlers(self):
        """Register all tool handlers with the MCP server"""
        
        # Tell MCP what tools we offer
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """
            This function tells Claude what tools are available.
            Each tool needs: name, description, and input schema
            """
            return [
                Tool(
                    name="analyze_binary",
                    description="Analyze a binary file and get basic information (file type, size, architecture)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the binary file to analyze"
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="extract_strings",
                    description="Extract readable strings from a binary file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the binary file"
                            },
                            "min_length": {
                                "type": "integer",
                                "description": "Minimum string length (default: 4)",
                                "default": 4
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="get_file_info",
                    description="Get detailed file information using 'file' command",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file"
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="check_security",
                    description="Check binary security features (NX, PIE, Stack Canary, RELRO)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the binary file"
                            }
                        },
                        "required": ["file_path"]
                    }
                )
            ]
        
        # Handle tool calls
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
            """
            This function handles when Claude calls one of our tools.
            It routes to the correct handler based on the tool name.
            """
            try:
                if name == "analyze_binary":
                    result = await self.analyze_binary(arguments["file_path"])
                elif name == "extract_strings":
                    min_len = arguments.get("min_length", 4)
                    result = await self.extract_strings(arguments["file_path"], min_len)
                elif name == "get_file_info":
                    result = await self.get_file_info(arguments["file_path"])
                elif name == "check_security":
                    result = await self.check_security(arguments["file_path"])
                else:
                    result = f"Unknown tool: {name}"
                
                return [TextContent(type="text", text=result)]
            
            except Exception as e:
                error_msg = f"Error executing {name}: {str(e)}"
                return [TextContent(type="text", text=error_msg)]
    
    # ============ TOOL IMPLEMENTATIONS ============
    
    async def analyze_binary(self, file_path: str) -> str:
        """
        Analyze a binary file and return basic information
        
        LEARNING NOTE: This is our first tool implementation.
        It runs system commands to gather info about the binary.
        """
        path = Path(file_path)
        
        if not path.exists():
            return f"Error: File not found: {file_path}"
        
        results = []
        results.append(f"=== Binary Analysis: {path.name} ===\n")
        
        # Basic file info
        stat = path.stat()
        results.append(f"File Size: {stat.st_size:,} bytes ({stat.st_size / 1024:.2f} KB)")
        results.append(f"Permissions: {oct(stat.st_mode)[-3:]}")
        
        # File type
        try:
            file_output = subprocess.check_output(
                ["file", str(path)],
                stderr=subprocess.STDOUT,
                text=True
            )
            results.append(f"\nFile Type:\n{file_output.strip()}")
        except subprocess.CalledProcessError as e:
            results.append(f"Could not determine file type: {e}")
        
        # Try to get more info with readelf (for ELF binaries)
        if "ELF" in file_output:
            try:
                readelf_output = subprocess.check_output(
                    ["readelf", "-h", str(path)],
                    stderr=subprocess.STDOUT,
                    text=True
                )
                results.append(f"\nELF Header:\n{readelf_output}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                results.append("\n(readelf not available for detailed ELF analysis)")
        
        return "\n".join(results)
    
    async def extract_strings(self, file_path: str, min_length: int = 4) -> str:
        """
        Extract readable strings from a binary
        
        LEARNING NOTE: This uses the 'strings' command.
        Useful for finding hardcoded passwords, URLs, etc.
        """
        path = Path(file_path)
        
        if not path.exists():
            return f"Error: File not found: {file_path}"
        
        try:
            # Run strings command
            strings_output = subprocess.check_output(
                ["strings", "-n", str(min_length), str(path)],
                stderr=subprocess.STDOUT,
                text=True
            )
            
            lines = strings_output.strip().split('\n')
            
            # Limit output for readability
            if len(lines) > 100:
                result = f"=== Strings Extracted (showing first 100 of {len(lines)}) ===\n\n"
                result += '\n'.join(lines[:100])
                result += f"\n\n... and {len(lines) - 100} more strings"
            else:
                result = f"=== Strings Extracted ({len(lines)} total) ===\n\n"
                result += '\n'.join(lines)
            
            return result
        
        except subprocess.CalledProcessError as e:
            return f"Error extracting strings: {e}"
        except FileNotFoundError:
            return "Error: 'strings' command not found. Install binutils package."
    
    async def get_file_info(self, file_path: str) -> str:
        """Get detailed file information"""
        path = Path(file_path)
        
        if not path.exists():
            return f"Error: File not found: {file_path}"
        
        try:
            output = subprocess.check_output(
                ["file", "-b", str(path)],
                stderr=subprocess.STDOUT,
                text=True
            )
            return f"File Info: {output.strip()}"
        except subprocess.CalledProcessError as e:
            return f"Error: {e}"
    
    async def check_security(self, file_path: str) -> str:
        """
        Check binary security features
        
        LEARNING NOTE: This checks common exploit mitigations.
        Important for understanding binary security posture.
        """
        path = Path(file_path)
        
        if not path.exists():
            return f"Error: File not found: {file_path}"
        
        results = []
        results.append(f"=== Security Features: {path.name} ===\n")
        
        # Try checksec if available
        try:
            checksec_output = subprocess.check_output(
                ["checksec", "--file=" + str(path)],
                stderr=subprocess.STDOUT,
                text=True
            )
            results.append(checksec_output)
            return "\n".join(results)
        except FileNotFoundError:
            pass  # checksec not available, try manual checks
        
        # Manual security checks for ELF
        try:
            # Check for NX (No Execute)
            readelf_wx = subprocess.check_output(
                ["readelf", "-l", str(path)],
                stderr=subprocess.STDOUT,
                text=True
            )
            
            nx_enabled = "GNU_STACK" in readelf_wx and "RW" in readelf_wx
            results.append(f"NX (No Execute): {'Enabled' if nx_enabled else 'Disabled'}")
            
            # Check for PIE (Position Independent Executable)
            readelf_h = subprocess.check_output(
                ["readelf", "-h", str(path)],
                stderr=subprocess.STDOUT,
                text=True
            )
            
            pie_enabled = "DYN (Shared object file)" in readelf_h or "DYN (Position-Independent Executable file)" in readelf_h
            results.append(f"PIE: {'Enabled' if pie_enabled else 'Disabled'}")
            
            # Check for Stack Canary
            symbols = subprocess.check_output(
                ["nm", str(path)],
                stderr=subprocess.STDOUT,
                text=True
            )
            
            canary_enabled = "__stack_chk_fail" in symbols
            results.append(f"Stack Canary: {'Enabled' if canary_enabled else 'Disabled'}")
            
            return "\n".join(results)
        
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            results.append(f"\nNote: Install 'checksec' or 'readelf' for detailed security analysis")
            return "\n".join(results)
    
    async def run(self):
        """Start the MCP server"""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

# ============ MAIN ============

async def main():
    """Entry point for the MCP server"""
    server = GhidraMCPServer()
    await server.run()

if __name__ == "__main__":
    # Run the async server
    asyncio.run(main())
