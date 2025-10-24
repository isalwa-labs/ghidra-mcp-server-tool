# 🎓 Ghidra MCP Server - Student Guide

**Welcome to your first MCP server!** Let's learn step by step.

---

## 📚 What You'll Learn

1. **What is MCP** and how it works
2. **How to structure** an MCP server
3. **How to define tools** that Claude can use
4. **How to test** your MCP server
5. **How to expand** it with more features

---

## 🔧 Part 1: Installation (5 minutes)

### Step 1: Install Dependencies

```bash
# Create a new directory
mkdir ghidra-mcp-server
cd ghidra-mcp-server

# Create requirements.txt
cat > requirements.txt << EOF
mcp>=0.9.0
EOF

# Install
pip install -r requirements.txt
```

### Step 2: Install Required Tools

```bash
# On Ubuntu/Debian
sudo apt-get install binutils file

# On macOS
brew install binutils

# Optional (for better security analysis)
# Install checksec
pip install checksec.py
```

### Step 3: Save the Server Code

Save the Python code as `ghidra_mcp_server.py`

---

## 🎯 Part 2: Understanding the Code (10 minutes)

Let's break down what each part does:

### A. The Server Class

```python
class GhidraMCPServer:
    def __init__(self):
        self.server = Server("ghidra-mcp")  # Creates MCP server
        # ... setup workspace, find tools
```

**What it does:** Initializes the server and prepares the environment.

### B. Tool Registration

```python
@self.server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="analyze_binary",      # Tool name
            description="...",           # What it does
            inputSchema={...}            # What inputs it needs
        )
    ]
```

**What it does:** Tells Claude "Hey, these are the tools you can use!"

### C. Tool Handler

```python
@self.server.call_tool()
async def call_tool(name: str, arguments: Any):
    if name == "analyze_binary":
        result = await self.analyze_binary(arguments["file_path"])
    return [TextContent(type="text", text=result)]
```

**What it does:** When Claude calls a tool, this routes it to the right function.

### D. Tool Implementation

```python
async def analyze_binary(self, file_path: str) -> str:
    # 1. Check if file exists
    # 2. Run system commands (file, readelf, etc.)
    # 3. Format and return results
```

**What it does:** The actual work - analyzing the binary!

---

## 🚀 Part 3: Testing Your Server (10 minutes)

### Test 1: Run the Server Standalone

```bash
python ghidra_mcp_server.py
```

If it starts without errors, good! But it won't do much because it's waiting for MCP messages.

### Test 2: Configure Claude Desktop

Create/edit: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
Or: `%APPDATA%/Claude/claude_desktop_config.json` (Windows)

```json
{
  "mcpServers": {
    "ghidra-mcp": {
      "command": "python",
      "args": [
        "/full/path/to/ghidra_mcp_server.py"
      ]
    }
  }
}
```

**Important:** Use the FULL path to your script!

### Test 3: Restart Claude Desktop

1. Quit Claude Desktop completely
2. Restart it
3. Look for the 🔌 icon (bottom right) - it shows connected MCP servers

### Test 4: Try It Out!

In Claude, try asking:

```
"Can you analyze this binary file for me: /path/to/some/binary"
```

Claude should use your MCP server! 🎉

---

## 🧪 Part 4: What Each Tool Does

### 1. `analyze_binary`
**Purpose:** Get basic information about a binary
**Uses:** `file`, `readelf` commands
**Good for:** Understanding what type of binary you're dealing with

**Example:**
```
Claude: "Analyze /bin/ls for me"
Result: File type, size, architecture, ELF header info
```

### 2. `extract_strings`
**Purpose:** Find readable text in binaries
**Uses:** `strings` command
**Good for:** Finding hardcoded passwords, URLs, error messages

**Example:**
```
Claude: "Extract strings from this binary"
Result: List of all readable strings (min 4 chars)
```

### 3. `get_file_info`
**Purpose:** Quick file type check
**Uses:** `file` command
**Good for:** Fast identification

### 4. `check_security`
**Purpose:** Check exploit mitigations
**Uses:** `readelf`, `nm`, or `checksec`
**Good for:** Understanding security features (NX, PIE, Canary)

---

## 🔍 Part 5: How MCP Communication Works

```
You → Claude Desktop → MCP Server → System Commands → Results → Claude → You
```

**Step by step:**
1. You ask Claude to analyze a binary
2. Claude recognizes it needs the `analyze_binary` tool
3. Claude sends a JSON-RPC message to your MCP server
4. Your server runs the `analyze_binary` function
5. Results are sent back to Claude
6. Claude formats and shows you the results

**The messages look like this:**

```json
// Claude calls tool
{
  "method": "tools/call",
  "params": {
    "name": "analyze_binary",
    "arguments": {
      "file_path": "/bin/ls"
    }
  }
}

// Your server responds
{
  "result": [
    {
      "type": "text",
      "text": "=== Binary Analysis: ls ===\nFile Size: 12345 bytes..."
    }
  ]
}
```

---

## 🎓 Part 6: Exercises (Learn by Doing!)

### Exercise 1: Add a New Tool (Easy)
Add a tool that counts functions in a binary:

```python
Tool(
    name="count_functions",
    description="Count the number of functions in a binary",
    inputSchema={
        "type": "object",
        "properties": {
            "file_path": {"type": "string"}
        },
        "required": ["file_path"]
    }
)
```

Then implement:
```python
async def count_functions(self, file_path: str) -> str:
    # Use: nm --defined-only file_path | wc -l
    pass
```

### Exercise 2: Add Filtering (Medium)
Modify `extract_strings` to filter by pattern:

```python
"pattern": {
    "type": "string",
    "description": "Regex pattern to filter strings"
}
```

### Exercise 3: Add Caching (Advanced)
Cache analysis results to speed up repeated queries.

---

## 🐛 Part 7: Common Issues & Solutions

### Issue 1: "Server not connecting"
**Solution:** Check the config file path is correct. Use full absolute paths.

### Issue 2: "Tool not found (strings, readelf, etc.)"
**Solution:** Install the missing tools:
```bash
sudo apt-get install binutils  # Linux
brew install binutils          # macOS
```

### Issue 3: "Permission denied"
**Solution:** Make sure the binary you're analyzing is readable:
```bash
chmod +r /path/to/binary
```

### Issue 4: "MCP module not found"
**Solution:** Install MCP:
```bash
pip install mcp
```

---

## 🚀 Part 8: Next Steps

Now that you understand the basics, you can:

1. **Add Ghidra Integration**
   - Use Ghidra's headless analyzer
   - Decompile functions
   - Generate call graphs

2. **Add More Analysis Tools**
   - Disassembly (`objdump`)
   - Symbol extraction
   - Import/export analysis

3. **Add Database Support**
   - Store analysis results
   - Compare binaries
   - Track changes

4. **Add Visualization**
   - Function call graphs
   - Control flow graphs
   - Dependency trees

---

## 📖 Quick Reference

### File Structure
```
ghidra-mcp-server/
├── ghidra_mcp_server.py    # Main server
├── requirements.txt         # Dependencies
├── README.md               # This guide
└── .ghidra_mcp_workspace/  # Working directory (auto-created)
```

### Key MCP Concepts

| Concept | Purpose | Example |
|---------|---------|---------|
| **Server** | Main MCP instance | `Server("ghidra-mcp")` |
| **Tool** | A function Claude can call | `analyze_binary` |
| **Input Schema** | Defines tool parameters | `{"file_path": "string"}` |
| **Handler** | Routes tool calls | `@server.call_tool()` |

### Useful Commands

```bash
# Test if binutils is installed
which readelf nm objdump strings file

# Check a binary manually
file /bin/ls
readelf -h /bin/ls
strings /bin/ls

# View MCP logs (helpful for debugging)
# Check Claude Desktop logs in:
# macOS: ~/Library/Logs/Claude/
# Windows: %APPDATA%/Claude/logs/
```

---

## 🎯 Summary: What You've Learned

✅ How MCP servers work (JSON-RPC over stdio)
✅ How to define tools with input schemas
✅ How to implement tool handlers
✅ How to integrate with system commands
✅ How to test and debug MCP servers
✅ How to configure Claude Desktop

**Next:** Try building your own tool! Start small, test often, and gradually add complexity.

---

## 💡 Pro Tips

1. **Start Simple:** Get one tool working before adding more
2. **Test Incrementally:** Test each tool separately
3. **Log Everything:** Add logging to debug issues
4. **Handle Errors:** Always catch exceptions and return helpful messages
5. **Document Well:** Future you will thank present you

---

## 🤝 Need Help?

- Read the [MCP Documentation](https://modelcontextprotocol.io)
- Check Claude Desktop logs for errors
- Test system commands manually first
- Start with simpler tools and build up

**Happy Learning! 🎓**

*"The best way to learn is by building." - Every programmer ever*
