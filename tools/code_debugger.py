import ast
import os

def validate_workspace_code(file_path: str) -> str:
    """
    Compiles and parses a Python script to check for syntax errors.
    Returns a detailed explanation of any bugs found, or a confirmation of a clean compile.
    """
    file_path = file_path.strip().strip('"').strip("'")
    if not os.path.exists(file_path):
        # Check if relative path inside workspace
        alt_path = os.path.join(os.getcwd(), file_path)
        if os.path.exists(alt_path):
            file_path = alt_path
        else:
            return f"Error: The target script file could not be located at '{file_path}'."
            
    print(f"\n[🛠️ J.A.R.V.I.S. is debugging code script: '{file_path}'...]")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
            
        # Parse abstract syntax tree to validate syntax
        ast.parse(source, filename=file_path)
        return f"Syntax validation successful, Mr. Pranav. Code file '{os.path.basename(file_path)}' compiled cleanly with zero syntax issues."
        
    except SyntaxError as val_err:
        line_no = val_err.lineno
        offset = val_err.offset or 0
        text = val_err.text or ""
        
        # Read lines around the bug for diagnostic context
        lines = source.splitlines()
        context_str = ""
        
        start_line = max(1, line_no - 2)
        end_line = min(len(lines), line_no + 2)
        
        for idx in range(start_line, end_line + 1):
            line_content = lines[idx - 1]
            if idx == line_no:
                # Add pointer highlighting the syntax error column
                pointer = " " * (offset - 1) + "^" if offset > 0 else ""
                context_str += f"➔ L{idx}: {line_content}\n          {pointer}\n"
            else:
                context_str += f"  L{idx}: {line_content}\n"
                
        error_report = (
            f"❌ SYNTAX BUG DETECTED IN '{os.path.basename(file_path)}':\n"
            f"────────────────────────────────────────\n"
            f"📍 Line {line_no}, Column {offset}:\n"
            f"⚠️ Error: {val_err.msg}\n\n"
            f"🔍 BUG CONTEXT MATRIX:\n"
            f"{context_str}\n"
            f"💡 J.A.R.V.I.S. DIAGNOSTIC:\n"
            f"Please verify indentation levels, closing brackets, or matching quotes on or near Line {line_no}."
        )
        return error_report
        
    except Exception as e:
        return f"An error occurred while attempting to inspect the file. Details: {str(e)}"
