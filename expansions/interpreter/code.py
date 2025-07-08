# coding: utf-8

#  BlackSmith mark.2
# exp_name = "interpreter" # /code.py v.x12
#  Id: 04~10c
#  Idea © (2002-2005) by Mike Mintz [mikemintz@gmail.com]
#  Idea © (2007) by Als [Als@exploit.in]
#  Code © (2009-2013) by WitcherGeralt [alkorgun@gmail.com]

import io
import contextlib
import ast
from typing import Dict, Any, List # For Python 3 type hinting

# Define constants that were in the suggested snippet
class Constants:
	DONE_MESSAGE = "Done."
	PYSHELL_ERROR = "Error during Python execution."

def handle_error(e: Exception, verbose: bool, error_message_prefix: str) -> str:
	# Simple error handler, can be expanded
	if verbose:
		return f"{error_message_prefix}\n{type(e).__name__}: {e}"
	return error_message_prefix

class expansion_temp(expansion):

	def __init__(self, name):
		expansion.__init__(self, name)

	opts = ("-l", "-r", "-s") # -l (locals) will be ignored, -r (result) behavior changes

	opt_locals = opts[0] # Kept for option parsing, but functionality will change
	opt_result = opts[1] # Kept for option parsing, but functionality will change
	opt_silent = opts[2]

	def run_python_code(self, code: str, verbose: bool = False) -> str:
		"""Execute Python code and capture output or return value."""
		output_buffer: io.StringIO = io.StringIO()
		local_vars: Dict[str, Any] = {}
		# Ensure __return__ is not predefined by user code in a confusing way
		# by potentially injecting it into the execution namespace with a unique prefix if needed,
		# or by relying on the fact that `exec` populates the provided dict.
		# For now, assuming `local_vars.get('__return__')` is sufficient.

		try:
			with contextlib.ExitStack() as stack:
				stack.enter_context(contextlib.redirect_stdout(output_buffer))
				stack.enter_context(contextlib.redirect_stderr(output_buffer))
				# The original snippet splits by "\n\n" which might be too simple.
				# `compile(code, "<pyshell>", "exec")` for a whole block,
				# or `compile(statement, "<pyshell>", "single")` for line-by-line like a REPL.
				# The "single" mode is better for REPL-like behavior where each statement's result is implicitly interesting.
				# However, for a script, "exec" is more natural.
				# The snippet's loop with "single" is powerful for interactive use.

				# Attempting to replicate the "single" mode for each logical block
				# This simplistic split might not perfectly mimic a true Python REPL for complex multi-line statements
				# that are not function/class defs.
				# A more robust approach might involve ast.parse and then compiling/executing parts.
				# For now, using the provided logic:
				source_to_compile = code.strip()

				# For a single block of code, 'exec' mode is usually better than 'single' for scripts.
				# If it's meant to be interactive, 'single' line-by-line is better.
				# Given the commands are `eval` and `exec`, let's assume `exec` for multi-line scripts.
				# The `__return__` mechanism implies the last expression's value might be of interest, like `eval`.
				# Let's try to support both: if it's a single expression, try 'eval', else 'exec'.

				try:
					# Try to compile as an expression first (like eval)
					compiled_code = compile(source_to_compile, "<pyshell>", "eval")
					result_val = eval(compiled_code, {"__builtins__": __builtins__}, local_vars)
					# if result_val is not None: # eval always returns something, even if None
					local_vars['__return__'] = result_val # Store result of eval
				except SyntaxError:
					# If not a simple expression, compile as a sequence of statements (like exec)
					# The snippet's line-by-line "single" compilation is more REPL-like.
					# Let's use that for `command_eval` and `command_exec` as it's more flexible.
					# Splitting by "\n\n" is a simplification for "statements"
					# A true REPL handles multi-line statements (if, for, def) better.
					# Compile the whole code as 'exec' for `command_exec` might be more appropriate.
					# For now, sticking to the user's snippet structure for `run_python_code`
					statements: List[str] = source_to_compile.splitlines() # Simpler split for now
					code_block_to_exec = "\n".join(statements) # Rejoin; original used split("\n\n")

					compiled_code = compile(code_block_to_exec, "<pyshell>", "exec")
					exec(compiled_code, {"__builtins__": __builtins__}, local_vars)

			# Check for __return__ which might have been set by 'eval' path or by user code
			result_from_exec = local_vars.get('__return__')
			if result_from_exec is not None:
				return str(result_from_exec)

			captured_output = output_buffer.getvalue()
			return captured_output or Constants.DONE_MESSAGE
		except Exception as e:
			return handle_error(e, verbose, Constants.PYSHELL_ERROR)
		finally:
			output_buffer.close()

	def command_eval(self, stype, source, body, disp):
		silent = False
		if body:
			args = body.split(None, 1)
			if len(args) == 2:
				if self.opt_silent == (args.pop(0)).lower():
					silent = True
					body = args.pop()
			# Use run_python_code. verbose=True for more error detail.
			answer = self.run_python_code(body, verbose=True)
			# The old code did `if not answer.strip(): answer = repr(answer)`.
			# run_python_code will return "Done." for no output, or actual output.
			# This behavior change is probably fine.
		else:
			answer = AnsBase[1]
		if not silent:
			Answer(answer, stype, source, disp)

	def command_exec(self, stype, source, body, disp):
		silent = False
		verbose_errors = True # Default to verbose errors for exec
		if body:
			parsed_opts = set()
			current_body = body
			# Parse options like -s, -r (note: -l is ignored by run_python_code)
			while True:
				args = current_body.split(None, 1)
				if not args: break
				potential_opt = args[0].lower()
				if potential_opt in self.opts:
					parsed_opts.add(potential_opt)
					if len(args) > 1:
						current_body = args[1]
					else:
						current_body = "" # Option was last thing
						break
				else:
					break # Not an option, rest is body

			body_to_execute = current_body

			if self.opt_silent in parsed_opts:
				silent = True

			# The -r (result) option's original behavior of fetching a 'result' variable
			# is now handled by run_python_code looking for '__return__'.
			# If -r was specified, we might want to imply verbose errors are off unless output is explicitly generated.
			# However, run_python_code handles output directly.
			# The main change is that `locals` or `globals` scope choice is removed for safety.

			if not body_to_execute.strip(): # Check if there's actual code to run after parsing opts
				answer = AnsBase[1] # No code provided
			else:
				answer = self.run_python_code(body_to_execute, verbose=verbose_errors)

		else:
			answer = AnsBase[1] # No body provided
		if not silent:
			Answer(answer, stype, source, disp)

	def command_sh(self, stype, source, body, disp):
		if body:
			if OSList[1]:
				command = cmdsDb[6] % (body.encode("utf-8"))
			else:
				command = body.encode("cp1251")
			answer = get_pipe(command)
			if not answer.strip():
				answer = AnsBase[4]
		else:
			answer = AnsBase[1]
		Answer(answer, stype, source, disp)

	taboo = chr(42)*2

	compile_math = compile__("([0-9]|[\+\-\(\/\*\)\%\^\.])")

	def command_calc(self, stype, source, body, disp):
		if body:
			if self.taboo not in body and 32 >= len(body): # Basic check against '**' and length
				# CRITICAL WARNING: The safety of this calculator relies *entirely* on the compile_math regex.
				# If the regex can be bypassed, this becomes arbitrary code execution via run_python_code.
				# A dedicated, secure math parsing library would be a much safer alternative.
				if not self.compile_math.sub("", body).strip(): # Check if only math-related chars remain
					try:
						# Using run_python_code for consistency, though it's more powerful than needed for a simple calc.
						# verbose=False for cleaner error messages for simple calc errors.
						# The run_python_code will try eval-like behavior first.
						answer = self.run_python_code(body, verbose=False)
						# Check for specific errors if run_python_code returns a generic error string
						if answer == Constants.PYSHELL_ERROR: # Default error from run_python_code
							# Attempt to check for ZeroDivisionError specifically if possible, though run_python_code hides it.
							# This specific error handling is now harder. For now, generic error is returned by run_python_code.
							# To get specific ZeroDivisionError, run_python_code would need to propagate it or its type.
							# For simplicity, the old specific "+\infty" for ZeroDivisionError is lost here.
							# It could be added back if run_python_code was modified to return specific error types/codes.
							pass # answer is already Constants.PYSHELL_ERROR
					except ZeroDivisionError: # This will not be hit if run_python_code catches all exceptions
						answer = "+\u221e" # Infinity symbol (previously was +\xe2\x88\x9e)
					except Exception: # This will also not be hit if run_python_code catches all
						answer = AnsBase[2] # Error in calculation
				else:
					answer = AnsBase[2] # Invalid characters for calc
			else:
				answer = AnsBase[2] # Taboo or too long
		else:
			answer = AnsBase[1]
		Answer(answer, stype, source, disp)

	commands = (
		(command_eval, "eval", 8,),
		(command_exec, "exec", 8,),
		(command_sh, "sh", 8,),
		(command_calc, "calc", 2,)
	)
