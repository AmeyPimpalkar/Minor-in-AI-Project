import streamlit as st
import json
import sys
import builtins
import traceback
from io import StringIO
from core.code_analyzer import analyze_code_style # Add this line
from core.error_handler import explain_error, log_user_error
import os
import time
from core.progress import log_progress
# from st_ace import st_ace

TASKS_DB = "data/coding_task.json"

#Load tasks safely, return list (empty list if file missing/invalid).
def load_tasks():
    if not os.path.exists(TASKS_DB):
        return []
    try:
        with open(TASKS_DB, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            data = json.loads(content)
            if isinstance(data, list):
                return data
            # if someone saved as dict, attempt to convert to list
            if isinstance(data, dict):
                return list(data.values())
            return []
    except json.JSONDecodeError as e:
        st.error(f"Failed to load tasks JSON: {e}")
        return []

# collapse whitespace, strip.
def normalize_text(s):
    if s is None:
        return ""
    if not isinstance(s, str):
        s = str(s)
    return " ".join(s.strip().split())

def compare_outputs(user_out, expected_out):
    return normalize_text(user_out) == normalize_text(expected_out)

def make_input_fn(input_str):
    if input_str is None:
        parts = []
    elif "\n" in input_str:
        parts = [p for p in input_str.splitlines()]
    else:
        parts = [p for p in input_str.split()] if input_str.strip() else []
    it = iter(parts)

    def _input(prompt=""):
        try:
            return next(it)
        except StopIteration:
            # If code tries to read more input than provided, raise EOFError similar to real input
            raise EOFError("No more input provided for this test case.")
    return _input

def exercises(username):
    start_time = time.time()
    st.subheader("Coding Exercises")
    tasks = load_tasks()
    if not tasks:
        st.info("No coding tasks found in data/coding_task.json")
        return

    # select index using format_func to show readable titles
    idx = st.selectbox(
        "Choose a problem:",
        list(range(len(tasks))),
        format_func=lambda i: tasks[i].get("task_description", f"Task {i+1}")
    )
    task = tasks[idx]

    # show description/hint
    st.markdown(f"**Problem:** {task.get('task_description', 'No description')}")
    if task.get("hint"):
        st.markdown(f"**Hint:** {task.get('hint')}")

    # Prepare test cases:
    test_cases = task.get("test_cases")
    if not test_cases:
        # support legacy fields
        ex_input = task.get("example_input", "")
        ex_output = task.get("expected_output", "")
        if ex_input or ex_output:
            test_cases = [{"input": ex_input, "expected_output": ex_output}]
        else:
            # empty: create one dummy test to allow free-running
            test_cases = [{"input": "", "expected_output": ""}]

    # Show test cases (summary)
    st.markdown("**Test cases (preview):**")
    for i, case in enumerate(test_cases[:5], 1):
        st.write(f"{i}. input: `{case.get('input','')}` → expected: `{case.get('expected_output','')}`")

    # Use session state to preserve code between runs
    code_key = f"code_input_{task.get('id', idx)}"
    if code_key not in st.session_state:
        st.session_state[code_key] = "" # Initialise if not present

    code = st.text_area("Write your solution here:", value=st.session_state[code_key], height=240, key=code_key + "_widget")
    st.session_state[code_key] = code # Update session state as user types

    passed = 0
    total = 0
    duration = 0 # Initialise duration

    if st.button("Run Solution"):
        start_time = time.time()   # Start timing when Run button is clicked
        total = len(test_cases) if test_cases else 0
        passed = 0 # Reset passed count for this run

        for i, case in enumerate(test_cases, start=1):
            st.markdown(f"---\n**Running test case #{i}**")
            user_input = case.get("input", "")
            expected = case.get("expected_output", "")

            old_stdout = sys.stdout
            old_input = builtins.input
            sys.stdout = mystdout = StringIO()
            builtins.input = make_input_fn(user_input)

            # Execute user code
            try:
                local_vars = {}
                exec(code, {}, local_vars)
                output = mystdout.getvalue()
                if output is None:
                    output = ""
                output = output.rstrip("\n") 
                st.write("🔹 Output:")
                st.code(output or "<no output>", language="text")

                # compare
                if expected != "": # Only compare if expected output is defined
                    ok = compare_outputs(output, expected)
                else:
                    # If no expected output, consider it passed if no error occurred
                    ok = True # Assume pass if code runs without error and no output expected

                if ok:
                    st.success(f"✅ Test case #{i} passed")
                    passed += 1

                    if passed == total:
                        st.markdown("---") # separator
                        ai_feedback = analyze_code_style(code)
                        if ai_feedback:
                            st.markdown("### 💡 Code Improvement Suggestions")
                            st.write(ai_feedback)
                else:
                    st.error(f"❌ Test case #{i} failed")
                    if expected != "": # Show expected only if it was defined
                        st.write("Expected:")
                        st.code(expected, language="text")

            except Exception as e:
                # show full traceback to help debugging
                tb = traceback.format_exc()
                st.error(f"⚠️ Runtime error on test case #{i}: {e}")
                st.code(tb, language="text")        
                explanation, fix_hint, example, predicted_category = explain_error(str(e), username)

                if predicted_category:
                    log_user_error(username, predicted_category)
                else:
                    # Log generically if explain_error couldn't categorize
                    log_user_error(username, "UnknownExerciseError")

                if explanation:
                    if predicted_category:
                       st.info(f"🤖 AI thinks this might be a **{predicted_category}**.")
                    st.info(f"📘 Explanation: {explanation}") 
                    st.warning(f"💡 Hint: {fix_hint}")
                    if example:
                        st.code(example, language="python")

                # don't continue other test cases if runtime error occurs for safety
                break # Stop processing further test cases on error

            finally:
                # restore stdout and input
                sys.stdout = old_stdout
                builtins.input = old_input

        # End timing after all test cases for this run
        end_time = time.time()
        duration = int(end_time - start_time)

        st.markdown("---")
        if total > 0:
            st.write(f"**Summary:** Passed {passed}/{total} test cases.")
        else:
            st.info("No defined test cases for this problem.") # Clarified message

        # Save progress *after* the run is complete
        log_progress(
            username=username,
            task_id=task.get("id", f"task_{idx}"), # Use task ID if available
            passed=passed,
            total=total,
            code=code, # Log the code that was run
            duration=duration
        )
        st.success("Progress saved!")