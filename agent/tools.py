import subprocess
import tempfile
import os
from langchain_core.tools import tool
from rag.retriever import search_codebase as _search, format_search_results


@tool
def search_codebase(query: str) -> str:
    """Search the indexed codebase for code relevant to the query.
    Use this to understand how changed code fits into the broader project,
    find similar patterns, or check how a function/class is used elsewhere.
    Args:
        query: Natural language or code snippet to search for.
    """
    hits = _search(query, top_k=4)
    return format_search_results(hits)


@tool
def run_security_scan(code_snippet: str, language: str = "python") -> str:
    """Run a static security scan on a code snippet using Semgrep.
    Use this when the diff touches authentication, authorization, database queries,
    file I/O, network calls, or input handling.
    Args:
        code_snippet: The code to scan (paste the relevant section from the diff).
        language: Programming language of the snippet (python, javascript, java, etc.)
    """
    suffix_map = {
        "python": ".py", "javascript": ".js", "typescript": ".ts",
        "java": ".java", "go": ".go", "ruby": ".rb"
    }
    suffix = suffix_map.get(language.lower(), ".py")
    with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False) as f:
        f.write(code_snippet)
        tmp_path = f.name
    try:
        result = subprocess.run(
            ["semgrep", "--config=auto", "--quiet", tmp_path],
            capture_output=True, text=True, timeout=30
        )
        output = result.stdout.strip() or result.stderr.strip()
        if not output:
            return "No security issues detected by Semgrep."
        return output[:3000]
    except FileNotFoundError:
        return "Semgrep not installed. Install with: pip install semgrep"
    except subprocess.TimeoutExpired:
        return "Security scan timed out."
    finally:
        os.unlink(tmp_path)


@tool
def run_tests(test_path: str = ".", extra_args: str = "") -> str:
    """Run pytest on the specified path and return the results.
    Use this when the diff contains logic changes to catch regressions.
    Args:
        test_path: Directory or file to run tests in (default: current dir).
        extra_args: Extra pytest arguments e.g. '-k test_auth'.
    """
    cmd = ["pytest", test_path, "--tb=short", "-q"]
    if extra_args:
        cmd += extra_args.split()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        output = result.stdout + result.stderr
        return output[-2500:] if len(output) > 2500 else output or "No output from pytest."
    except FileNotFoundError:
        return "pytest not installed. Install with: pip install pytest"
    except subprocess.TimeoutExpired:
        return "Tests timed out after 60 seconds."


@tool
def check_complexity(code_snippet: str) -> str:
    """Analyse cyclomatic complexity of a Python snippet using radon.
    Use this when a function looks deeply nested or overly complex.
    Args:
        code_snippet: Python code to analyse.
    """
    try:
        import radon.complexity as radon_cc
        blocks = radon_cc.cc_visit(code_snippet)
        if not blocks:
            return "No functions/methods found to analyse."
        lines = []
        for block in blocks:
            grade = radon_cc.cc_rank(block.complexity)
            lines.append(f"  {block.name} - complexity: {block.complexity} (grade {grade})")
        return "Cyclomatic complexity:\n" + "\n".join(lines)
    except ImportError:
        return "radon not installed. Install with: pip install radon"
    except Exception as e:
        return f"Complexity check failed: {e}"


ALL_TOOLS = [search_codebase, run_security_scan, run_tests, check_complexity]
