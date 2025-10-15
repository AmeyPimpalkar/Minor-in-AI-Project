# core/code_analyzer.py
import ast
import re

def analyze_code_style(code):
    """Analyze Python code for basic inefficiencies and style issues."""
    suggestions = []

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return ["❌ Could not analyze code due to syntax errors."]

    # 1️⃣ Check for nested loops
    nested_loops = sum(isinstance(node, ast.For) and any(isinstance(child, ast.For) for child in ast.walk(node)) for node in ast.walk(tree))
    if nested_loops > 0:
        suggestions.append("⚙️ Consider reducing nested loops — they may slow down large datasets (O(n²) complexity).")

    # 2️⃣ Check for range(len(...))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "range":
            if len(node.args) == 1 and isinstance(node.args[0], ast.Call) and isinstance(node.args[0].func, ast.Name) and node.args[0].func.id == "len":
                suggestions.append("💡 You used `for i in range(len(x))`. Prefer `for item in x:` for cleaner, more Pythonic code.")

    # 3️⃣ Check for hardcoded magic numbers
    if re.search(r"\b\d{2,}\b", code):
        suggestions.append("🔢 Consider replacing hardcoded numbers with named constants for readability.")

    # 4️⃣ Check for multiple print statements
    if code.count("print(") > 3:
        suggestions.append("🖨 Too many print statements — consider using logging or formatted summary output.")

    # 5️⃣ Check for unused imports
    if re.search(r"import\s+\w+", code) and "used" not in code:
        suggestions.append("🧹 It seems you imported modules that are never used — clean them up to simplify your script.")

    return suggestions if suggestions else ["✅ No major issues found — great job!"]