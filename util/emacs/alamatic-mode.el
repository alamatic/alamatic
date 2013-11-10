;;; alamatic-mode.el --- Major mode for editing Alamatic programs

;; This is currently just a hacked-up version of Python mode and contains lots of
;; stuff that doesn't really make sense for Alamatic. This is just enough to get
;; syntax highlighting and indenting working. Further improvements are welcomed.

;; Parts are copyright (C) 2013 Martin Atkins
;; Based on python-mode, which is copyright (C) 1992,1993,1994  Tim Peters

;; Author: 2013-     (As alamatic-mode) Martin Atkins
;          2003-2009 (As python-mode) https://launchpad.net/python-mode
;;         1995-2002 (As python-mode) Barry A. Warsaw
;;         1992-1994 (As python-mode) Tim Peters
;; Maintainer: Martin Atkins
;; Created:    Nov 2013
;; Keywords:   alamatic languages oop

(defconst ala-version "0.0.1"
  "`alamatic-mode' version number.")

;; This file is part of alamatic-mode.el.
;;
;; alamatic-mode.el is free software: you can redistribute it and/or modify it
;; under the terms of the GNU General Public License as published by the Free
;; Software Foundation, either version 3 of the License, or (at your option)
;; any later version.
;;
;; alamatic-mode.el is distributed in the hope that it will be useful, but
;; WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
;; or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
;; for more details.
;;
;; You should have received a copy of the GNU General Public License along
;; with alamatic-mode.el.  If not, see <http://www.gnu.org/licenses/>.

;; INSTALLATION:

;; To install, just drop this file into a directory on your load-path and
;; byte-compile it.  To set up Emacs to automatically edit files ending in
;; ".ala" using alamatic-mode add the following to your ~/.emacs file (GNU
;; Emacs) or ~/.xemacs/init.el file (XEmacs):
;;    (setq auto-mode-alist (cons '("\\.ala$" . alamatic-mode) auto-mode-alist))
;;    (setq interpreter-mode-alist (cons '("alamatic" . alamatic-mode)
;;                                       interpreter-mode-alist))
;;    (autoload 'alamatic-mode "alamatic-mode" "Alamatic editing mode." t)
;;
;; In XEmacs syntax highlighting should be enabled automatically.  In GNU
;; Emacs you may have to add these lines to your ~/.emacs file:
;;    (global-font-lock-mode t)
;;    (setq font-lock-maximum-decoration t)

;;; Code:

(require 'comint)
(require 'custom)
(require 'cl)
(require 'compile)
(require 'ansi-color)


;; user definable variables
;; vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv

(defgroup alamatic nil
  "Support for the Alamatic programming language, <http://www.alamatic.com/>"
  :group 'languages
  :prefix "ala-")

(defcustom ala-tab-always-indent t
  "*Non-nil means TAB in Alamatic mode should always reindent the current line,
regardless of where in the line point is when the TAB command is used."
  :type 'boolean
  :group 'alamatic)

(defcustom ala-alamatic-command "alamatic"
  "*Shell command used to start Alamatic interpreter."
  :type 'string
  :group 'alamatic)

(make-obsolete-variable 'ala-jalamatic-command 'ala-jython-command)
(defcustom ala-jython-command "jython"
  "*Shell command used to start the Jython interpreter."
  :type 'string
  :group 'alamatic
  :tag "Jython Command")

(defcustom ala-default-interpreter 'calamatic
  "*Which Alamatic interpreter is used by default.
The value for this variable can be either `calamatic' or `jython'.

When the value is `calamatic', the variables `ala-alamatic-command' and
`ala-alamatic-command-args' are consulted to determine the interpreter
and arguments to use.

When the value is `jython', the variables `ala-jython-command' and
`ala-jython-command-args' are consulted to determine the interpreter
and arguments to use.

Note that this variable is consulted only the first time that a Alamatic
mode buffer is visited during an Emacs session.  After that, use
\\[ala-toggle-shells] to change the interpreter shell."
  :type '(choice (const :tag "Alamatic (a.k.a. CAlamatic)" calamatic)
                 (const :tag "Jython" jython))
  :group 'alamatic)

(defcustom ala-alamatic-command-args '("-i")
  "*List of string arguments to be used when starting a Alamatic shell."
  :type '(repeat string)
  :group 'alamatic)

(make-obsolete-variable 'ala-jalamatic-command-args 'ala-jython-command-args)
(defcustom ala-jython-command-args '("-i")
  "*List of string arguments to be used when starting a Jython shell."
  :type '(repeat string)
  :group 'alamatic
  :tag "Jython Command Args")

(defcustom ala-indent-offset 4
  "*Amount of offset per level of indentation.
`\\[ala-guess-indent-offset]' can usually guess a good value when
you're editing someone else's Alamatic code."
  :type 'integer
  :group 'alamatic)

(defcustom ala-continuation-offset 4
  "*Additional amount of offset to give for some continuation lines.
Continuation lines are those that immediately follow a backslash
terminated line.  Only those continuation lines for a block opening
statement are given this extra offset."
  :type 'integer
  :group 'alamatic)

(defcustom ala-smart-indentation t
  "*Should `alamatic-mode' try to automagically set some indentation variables?
When this variable is non-nil, two things happen when a buffer is set
to `alamatic-mode':

    1. `ala-indent-offset' is guessed from existing code in the buffer.
       Only guessed values between 2 and 8 are considered.  If a valid
       guess can't be made (perhaps because you are visiting a new
       file), then the value in `ala-indent-offset' is used.

    2. `indent-tabs-mode' is turned off if `ala-indent-offset' does not
       equal `tab-width' (`indent-tabs-mode' is never turned on by
       Alamatic mode).  This means that for newly written code, tabs are
       only inserted in indentation if one tab is one indentation
       level, otherwise only spaces are used.

Note that both these settings occur *after* `alamatic-mode-hook' is run,
so if you want to defeat the automagic configuration, you must also
set `ala-smart-indentation' to nil in your `alamatic-mode-hook'."
  :type 'boolean
  :group 'alamatic)

(defcustom ala-align-multiline-strings-p t
  "*Flag describing how multi-line triple quoted strings are aligned.
When this flag is non-nil, continuation lines are lined up under the
preceding line's indentation.  When this flag is nil, continuation
lines are aligned to column zero."
  :type '(choice (const :tag "Align under preceding line" t)
                 (const :tag "Align to column zero" nil))
  :group 'alamatic)

(defcustom ala-block-comment-prefix "##"
  "*String used by \\[comment-region] to comment out a block of code.
This should follow the convention for non-indenting comment lines so
that the indentation commands won't get confused (i.e., the string
should be of the form `#x...' where `x' is not a blank or a tab, and
`...' is arbitrary).  However, this string should not end in whitespace."
  :type 'string
  :group 'alamatic)

(defcustom ala-honor-comment-indentation t
  "*Controls how comment lines influence subsequent indentation.

When nil, all comment lines are skipped for indentation purposes, and
if possible, a faster algorithm is used (i.e. X/Emacs 19 and beyond).

When t, lines that begin with a single `#' are a hint to subsequent
line indentation.  If the previous line is such a comment line (as
opposed to one that starts with `ala-block-comment-prefix'), then its
indentation is used as a hint for this line's indentation.  Lines that
begin with `ala-block-comment-prefix' are ignored for indentation
purposes.

When not nil or t, comment lines that begin with a single `#' are used
as indentation hints, unless the comment character is in column zero."
  :type '(choice
          (const :tag "Skip all comment lines (fast)" nil)
          (const :tag "Single # `sets' indentation for next line" t)
          (const :tag "Single # `sets' indentation except at column zero"
                 other)
          )
  :group 'alamatic)

(defcustom ala-temp-directory
  (let ((ok '(lambda (x)
               (and x
                    (setq x (expand-file-name x)) ; always true
                    (file-directory-p x)
                    (file-writable-p x)
                    x))))
    (or (funcall ok (getenv "TMPDIR"))
        (funcall ok "/usr/tmp")
        (funcall ok "/tmp")
        (funcall ok "/var/tmp")
        (funcall ok  ".")
        (error
         "Couldn't find a usable temp directory -- set `ala-temp-directory'")))
  "*Directory used for temporary files created by a *Alamatic* process.
By default, the first directory from this list that exists and that you
can write into: the value (if any) of the environment variable TMPDIR,
/usr/tmp, /tmp, /var/tmp, or the current directory."
  :type 'string
  :group 'alamatic)

(defcustom ala-beep-if-tab-change t
  "*Ring the bell if `tab-width' is changed.
If a comment of the form

  \t# vi:set tabsize=<number>:

is found before the first code line when the file is entered, and the
current value of (the general Emacs variable) `tab-width' does not
equal <number>, `tab-width' is set to <number>, a message saying so is
displayed in the echo area, and if `ala-beep-if-tab-change' is non-nil
the Emacs bell is also rung as a warning."
  :type 'boolean
  :group 'alamatic)

(defcustom ala-jump-on-exception t
  "*Jump to innermost exception frame in *Alamatic Output* buffer.
When this variable is non-nil and an exception occurs when running
Alamatic code synchronously in a subprocess, jump immediately to the
source code of the innermost traceback frame."
  :type 'boolean
  :group 'alamatic)

(defcustom ala-ask-about-save t
  "If not nil, ask about which buffers to save before executing some code.
Otherwise, all modified buffers are saved without asking."
  :type 'boolean
  :group 'alamatic)

(defcustom ala-backspace-function 'backward-delete-char-untabify
  "*Function called by `ala-electric-backspace' when deleting backwards."
  :type 'function
  :group 'alamatic)

(defcustom ala-delete-function 'delete-char
  "*Function called by `ala-electric-delete' when deleting forwards."
  :type 'function
  :group 'alamatic)

(defcustom ala-imenu-show-method-args-p nil
  "*Controls echoing of arguments of functions & methods in the Imenu buffer.
When non-nil, arguments are printed."
  :type 'boolean
  :group 'alamatic)
(make-variable-buffer-local 'ala-indent-offset)

(defcustom ala-pdbtrack-do-tracking-p t
  "*Controls whether the pdbtrack feature is enabled or not.
When non-nil, pdbtrack is enabled in all comint-based buffers,
e.g. shell buffers and the *Alamatic* buffer.  When using pdb to debug a
Alamatic program, pdbtrack notices the pdb prompt and displays the
source file and line that the program is stopped at, much the same way
as gud-mode does for debugging C programs with gdb."
  :type 'boolean
  :group 'alamatic)
(make-variable-buffer-local 'ala-pdbtrack-do-tracking-p)

(defcustom ala-pdbtrack-minor-mode-string " PDB"
  "*String to use in the minor mode list when pdbtrack is enabled."
  :type 'string
  :group 'alamatic)

(defcustom ala-import-check-point-max
  20000
  "Maximum number of characters to search for a Java-ish import statement.
When `alamatic-mode' tries to calculate the shell to use (either a
CAlamatic or a Jython shell), it looks at the so-called `shebang' line
-- i.e. #! line.  If that's not available, it looks at some of the
file heading imports to see if they look Java-like."
  :type 'integer
  :group 'alamatic
  )

(make-obsolete-variable 'ala-jalamatic-packages 'ala-jython-packages)
(defcustom ala-jython-packages
  '("java" "javax" "org" "com")
  "Imported packages that imply `jython-mode'."
  :type '(repeat string)
  :group 'alamatic)

;; Not customizable
(defvar ala-master-file nil
  "If non-nil, execute the named file instead of the buffer's file.
The intent is to allow you to set this variable in the file's local
variable section, e.g.:

    # Local Variables:
    # ala-master-file: \"master.ala\"
    # End:

so that typing \\[ala-execute-buffer] in that buffer executes the named
master file instead of the buffer's file.  If the file name has a
relative path, the value of variable `default-directory' for the
buffer is prepended to come up with a file name.")
(make-variable-buffer-local 'ala-master-file)

(defcustom ala-pychecker-command "pychecker"
  "*Shell command used to run Pychecker."
  :type 'string
  :group 'alamatic
  :tag "Pychecker Command")

(defcustom ala-pychecker-command-args '("--stdlib")
  "*List of string arguments to be passed to pychecker."
  :type '(repeat string)
  :group 'alamatic
  :tag "Pychecker Command Args")

(defvar ala-shell-alist
  '(("jython" . 'jython)
    ("alamatic" . 'calamatic))
  "*Alist of interpreters and alamatic shells. Used by `ala-choose-shell'
to select the appropriate alamatic interpreter mode for a file.")

(defcustom ala-shell-input-prompt-1-regexp "^>>> "
  "*A regular expression to match the input prompt of the shell."
  :type 'string
  :group 'alamatic)

(defcustom ala-shell-input-prompt-2-regexp "^[.][.][.] "
  "*A regular expression to match the input prompt of the shell after the
  first line of input."
  :type 'string
  :group 'alamatic)

(defcustom ala-shell-switch-buffers-on-execute t
  "*Controls switching to the Alamatic buffer where commands are
  executed.  When non-nil the buffer switches to the Alamatic buffer, if
  not no switching occurs."
  :type 'boolean
  :group 'alamatic)


;; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
;; NO USER DEFINABLE VARIABLES BEYOND THIS POINT

(defvar ala-line-number-offset 0
  "When an exception occurs as a result of ala-execute-region, a
subsequent ala-up-exception needs the line number where the region
started, in order to jump to the correct file line.  This variable is
set in ala-execute-region and used in ala-jump-to-exception.")

(defconst ala-emacs-features
  (let (features)
   features)
  "A list of features extant in the Emacs you are using.
There are many flavors of Emacs out there, with different levels of
support for features needed by `alamatic-mode'.")

;; Face for None, True, False, self, and Ellipsis
(defvar ala-pseudo-keyword-face 'ala-pseudo-keyword-face
  "Face for pseudo keywords in Alamatic mode, like self, True, False, Ellipsis.")
(make-face 'ala-pseudo-keyword-face)

;; PEP 318 decorators
(defvar ala-decorators-face 'ala-decorators-face
  "Face method decorators.")
(make-face 'ala-decorators-face)

;; Face for builtins
(defvar ala-builtins-face 'ala-builtins-face
  "Face for builtins like TypeError, object, open, and exec.")
(make-face 'ala-builtins-face)

;; XXX, TODO, and FIXME comments and such
(defvar ala-XXX-tag-face 'ala-XXX-tag-face
  "Face for XXX, TODO, and FIXME tags")
(make-face 'ala-XXX-tag-face)

;(defun ala-font-lock-mode-hook ()
;  (or (face-differs-from-default-p 'ala-pseudo-keyword-face)
;      (coala-face 'font-lock-keyword-face 'ala-pseudo-keyword-face))
;  (or (face-differs-from-default-p 'ala-builtins-face)
;      (coala-face 'font-lock-keyword-face 'ala-builtins-face))
;  (or (face-differs-from-default-p 'ala-decorators-face)
;      (coala-face 'ala-pseudo-keyword-face 'ala-decorators-face))
;  (or (face-differs-from-default-p 'ala-XXX-tag-face)
;      (coala-face 'font-lock-comment-face 'ala-XXX-tag-face))
;  )
;(add-hook 'font-lock-mode-hook 'ala-font-lock-mode-hook)

(defvar alamatic-font-lock-keywords
  (let ((kw1 (mapconcat 'identity
                        '("and"      "assert"   "break"     "class"
                          "continue" "func"     "del"       "elif"
                          "else"     "except"   "for"       "from"
                          "global"   "if"       "import"    "in"
                          "is"       "lambda"   "not"       "or"
                          "pass"     "raise"    "as"        "return"
                          "while"    "with"    "var"        "interface"
                          "const"
                          )
                        "\\|"))
        (kw2 (mapconcat 'identity
                        '("else:" "except:" "finally:" "try:")
                        "\\|"))
        (kw3 (mapconcat 'identity
                        ;; Don't include Ellipsis in this list, since it is
                        ;; already defined as a pseudo keyword.
                        '("__debug__"
                          "__import__" "__name__" "abs" "all" "any" "apply"
                          "basestring" "bin" "bool" "buffer" "bytearray"
                          "callable" "chr" "classmethod" "cmp" "coerce"
                          "compile" "complex" "copyright" "credits"
                          "delattr" "dict" "dir" "divmod" "enumerate" "eval"
                          "exec" "execfile" "exit" "file" "filter" "float"
                          "format" "getattr" "globals" "hasattr" "hash" "help"
                          "hex" "id" "input" "int" "intern" "isinstance"
                          "issubclass" "iter" "len" "license" "list" "locals"
                          "long" "map" "max" "memoryview" "min" "next"
                          "object" "oct" "open" "ord" "pow" "print" "property"
                          "quit" "range" "raw_input" "reduce" "reload" "repr"
                          "round" "set" "setattr" "slice" "sorted"
                          "staticmethod" "str" "sum" "super" "tuple" "type"
                          "unichr" "unicode" "vars" "xrange" "zip")
                        "\\|"))
        (kw4 (mapconcat 'identity
                        ;; Exceptions and warnings
                        '("ArithmeticError" "AssertionError"
                          "AttributeError" "BaseException" "BufferError"
                          "BytesWarning" "DeprecationWarning" "EOFError"
                          "EnvironmentError" "Exception"
                          "FloatingPointError" "FutureWarning" "GeneratorExit"
                          "IOError" "ImportError" "ImportWarning"
                          "IndentationError" "IndexError"
                          "KeyError" "KeyboardInterrupt" "LookupError"
                          "MemoryError" "NameError" "NotImplemented"
                          "NotImplementedError" "OSError" "OverflowError"
                          "PendingDeprecationWarning" "ReferenceError"
                          "RuntimeError" "RuntimeWarning" "StandardError"
                          "StopIteration" "SyntaxError" "SyntaxWarning"
                          "SystemError" "SystemExit" "TabError" "TypeError"
                          "UnboundLocalError" "UnicodeDecodeError"
                          "UnicodeEncodeError" "UnicodeError"
                          "UnicodeTranslateError" "UnicodeWarning"
                          "UserWarning" "ValueError" "Warning"
                          "ZeroDivisionError")
                        "\\|"))
        )
    (list
     '("^[ \t]*\\(@.+\\)" 1 'ala-decorators-face)
     ;; keywords
     (cons (concat "\\<\\(" kw1 "\\)\\>[ \n\t(]") 1)
     ;; builtins when they don't appear as object attributes
     (list (concat "\\([^. \t]\\|^\\)[ \t]*\\<\\(" kw3 "\\)\\>[ \n\t(]") 2
           'ala-builtins-face)
     ;; block introducing keywords with immediately following colons.
     ;; Yes "except" is in both lists.
     (cons (concat "\\<\\(" kw2 "\\)[ \n\t(]") 1)
     ;; Exceptions
     (list (concat "\\<\\(" kw4 "\\)[ \n\t:,(]") 1 'ala-builtins-face)
     ;; classes
     '("\\<class[ \t]+\\([a-zA-Z_]+[a-zA-Z0-9_]*\\)" 1 font-lock-type-face)
     ;; functions
     '("\\<def[ \t]+\\([a-zA-Z_]+[a-zA-Z0-9_]*\\)"
       1 font-lock-function-name-face)
     ;; pseudo-keywords
     '("\\<\\(self\\|Ellipsis\\|True\\|False\\|None\\)\\>"
       1 ala-pseudo-keyword-face)
     ;; XXX, TODO, and FIXME tags
     '("XXX\\|TODO\\|FIXME" 0 ala-XXX-tag-face t)
     ))
  "Additional expressions to highlight in Alamatic mode.")
(put 'alamatic-mode 'font-lock-defaults '(alamatic-font-lock-keywords))

;; have to bind ala-file-queue before installing the kill-emacs-hook
(defvar ala-file-queue nil
  "Queue of Alamatic temp files awaiting execution.
Currently-active file is at the head of the list.")

(defvar ala-pdbtrack-is-tracking-p nil)

(defvar ala-pychecker-history nil)



;; Constants

(defconst ala-stringlit-re
  (concat
   ;; These fail if backslash-quote ends the string (not worth
   ;; fixing?).  They precede the short versions so that the first two
   ;; quotes don't look like an empty short string.
   ;;
   ;; (maybe raw), long single quoted triple quoted strings (SQTQ),
   ;; with potential embedded single quotes
   "[rR]?'''[^']*\\(\\('[^']\\|''[^']\\)[^']*\\)*'''"
   "\\|"
   ;; (maybe raw), long double quoted triple quoted strings (DQTQ),
   ;; with potential embedded double quotes
   "[rR]?\"\"\"[^\"]*\\(\\(\"[^\"]\\|\"\"[^\"]\\)[^\"]*\\)*\"\"\""
   "\\|"
   "[rR]?'\\([^'\n\\]\\|\\\\.\\)*'"     ; single-quoted
   "\\|"                                ; or
   "[rR]?\"\\([^\"\n\\]\\|\\\\.\\)*\""  ; double-quoted
   )
  "Regular expression matching a Alamatic string literal.")

(defconst ala-continued-re
  ;; This is tricky because a trailing backslash does not mean
  ;; continuation if it's in a comment
  (concat
   "\\(" "[^#'\"\n\\]" "\\|" ala-stringlit-re "\\)*"
   "\\\\$")
  "Regular expression matching Alamatic backslash continuation lines.")

(defconst ala-blank-or-comment-re "[ \t]*\\($\\|#\\)"
  "Regular expression matching a blank or comment line.")

(defconst ala-outdent-re
  (concat "\\(" (mapconcat 'identity
                           '("else:"
                             "except\\(\\s +.*\\)?:"
                             "finally:"
                             "elif\\s +.*:")
                           "\\|")
          "\\)")
  "Regular expression matching statements to be dedented one level.")

(defconst ala-block-closing-keywords-re
  "\\(return\\|raise\\|break\\|continue\\|pass\\)"
  "Regular expression matching keywords which typically close a block.")

(defconst ala-no-outdent-re
  (concat
   "\\("
   (mapconcat 'identity
              (list "try:"
                    "except\\(\\s +.*\\)?:"
                    "while\\s +.*:"
                    "for\\s +.*:"
                    "if\\s +.*:"
                    "elif\\s +.*:"
                    (concat ala-block-closing-keywords-re "[ \t\n]")
                    )
              "\\|")
          "\\)")
  "Regular expression matching lines not to dedent after.")

(defvar ala-traceback-line-re
  "[ \t]+File \"\\([^\"]+\\)\", line \\([0-9]+\\)"
  "Regular expression that describes tracebacks.")

;; pdbtrack constants
(defconst ala-pdbtrack-stack-entry-regexp
;  "^> \\([^(]+\\)(\\([0-9]+\\))\\([?a-zA-Z0-9_]+\\)()"
  "^> \\(.*\\)(\\([0-9]+\\))\\([?a-zA-Z0-9_]+\\)()"
  "Regular expression pdbtrack uses to find a stack trace entry.")

(defconst ala-pdbtrack-input-prompt "\n[(<]*[Pp]db[>)]+ "
  "Regular expression pdbtrack uses to recognize a pdb prompt.")

(defconst ala-pdbtrack-track-range 10000
  "Max number of characters from end of buffer to search for stack entry.")



;; Major mode boilerplate

;; define a mode-specific abbrev table for those who use such things
(defvar alamatic-mode-abbrev-table nil
  "Abbrev table in use in `alamatic-mode' buffers.")
(define-abbrev-table 'alamatic-mode-abbrev-table nil)

(defvar alamatic-mode-hook nil
  "*Hook called by `alamatic-mode'.")

(make-obsolete-variable 'jalamatic-mode-hook 'jython-mode-hook)
(defvar jython-mode-hook nil
  "*Hook called by `jython-mode'. `jython-mode' also calls
`alamatic-mode-hook'.")

(defvar ala-shell-hook nil
  "*Hook called by `ala-shell'.")

;; In previous version of alamatic-mode.el, the hook was incorrectly
;; called ala-mode-hook, and was not defvar'd.  Deprecate its use.
(and (fboundp 'make-obsolete-variable)
     (make-obsolete-variable 'ala-mode-hook 'alamatic-mode-hook))

(defvar ala-mode-map ()
  "Keymap used in `alamatic-mode' buffers.")
(if ala-mode-map
    nil
  (setq ala-mode-map (make-sparse-keymap))
  ;; electric keys
  (define-key ala-mode-map ":" 'ala-electric-colon)
  ;; indentation level modifiers
  (define-key ala-mode-map "\C-c\C-l"  'ala-shift-region-left)
  (define-key ala-mode-map "\C-c\C-r"  'ala-shift-region-right)
  (define-key ala-mode-map "\C-c<"     'ala-shift-region-left)
  (define-key ala-mode-map "\C-c>"     'ala-shift-region-right)
  ;; subprocess commands
  (define-key ala-mode-map "\C-c\C-c"  'ala-execute-buffer)
  (define-key ala-mode-map "\C-c\C-m"  'ala-execute-import-or-reload)
  (define-key ala-mode-map "\C-c\C-s"  'ala-execute-string)
  (define-key ala-mode-map "\C-c|"     'ala-execute-region)
  (define-key ala-mode-map "\e\C-x"    'ala-execute-def-or-class)
  (define-key ala-mode-map "\C-c!"     'ala-shell)
  (define-key ala-mode-map "\C-c\C-t"  'ala-toggle-shells)
  ;; Caution!  Enter here at your own risk.  We are trying to support
  ;; several behaviors and it gets disgusting. :-( This logic ripped
  ;; largely from CC Mode.
  ;;
  ;; In XEmacs 19, Emacs 19, and Emacs 20, we use this to bind
  ;; backwards deletion behavior to DEL, which both Delete and
  ;; Backspace get translated to.  There's no way to separate this
  ;; behavior in a clean way, so deal with it!  Besides, it's been
  ;; this way since the dawn of time.
  (if (not (boundp 'delete-key-deletes-forward))
      (define-key ala-mode-map "\177" 'ala-electric-backspace)
    ;; However, XEmacs 20 actually achieved enlightenment.  It is
    ;; possible to sanely define both backward and forward deletion
    ;; behavior under X separately (TTYs are forever beyond hope, but
    ;; who cares?  XEmacs 20 does the right thing with these too).
    (define-key ala-mode-map [delete]    'ala-electric-delete)
    (define-key ala-mode-map [backspace] 'ala-electric-backspace))
  ;; Separate M-BS from C-M-h.  The former should remain
  ;; backward-kill-word.
  (define-key ala-mode-map [(control meta h)] 'ala-mark-def-or-class)
  (define-key ala-mode-map "\C-c\C-k"  'ala-mark-block)
  ;; Miscellaneous
  (define-key ala-mode-map "\C-c:"     'ala-guess-indent-offset)
  (define-key ala-mode-map "\C-c\t"    'ala-indent-region)
  (define-key ala-mode-map "\C-c\C-d"  'ala-pdbtrack-toggle-stack-tracking)
  (define-key ala-mode-map "\C-c\C-f"  'ala-sort-imports)
  (define-key ala-mode-map "\C-c\C-n"  'ala-next-statement)
  (define-key ala-mode-map "\C-c\C-p"  'ala-previous-statement)
  (define-key ala-mode-map "\C-c\C-u"  'ala-goto-block-up)
  (define-key ala-mode-map "\C-c#"     'ala-comment-region)
  (define-key ala-mode-map "\C-c?"     'ala-describe-mode)
  (define-key ala-mode-map "\C-c\C-h"  'ala-help-at-point)
  (define-key ala-mode-map "\e\C-a"    'ala-beginning-of-def-or-class)
  (define-key ala-mode-map "\e\C-e"    'ala-end-of-def-or-class)
  (define-key ala-mode-map "\C-c-"     'ala-up-exception)
  (define-key ala-mode-map "\C-c="     'ala-down-exception)
  ;; stuff that is `standard' but doesn't interface well with
  ;; alamatic-mode, which forces us to rebind to special commands
  (define-key ala-mode-map "\C-xnd"    'ala-narrow-to-defun)
  ;; information
  (define-key ala-mode-map "\C-c\C-b" 'ala-submit-bug-report)
  (define-key ala-mode-map "\C-c\C-v" 'ala-version)
  (define-key ala-mode-map "\C-c\C-w" 'ala-pychecker-run)
  ;; shadow global bindings for newline-and-indent w/ the ala- version.
  ;; BAW - this is extremely bad form, but I'm not going to change it
  ;; for now.
  (mapc #'(lambda (key)
            (define-key ala-mode-map key 'ala-newline-and-indent))
        (where-is-internal 'newline-and-indent))
  ;; Force RET to be ala-newline-and-indent even if it didn't get
  ;; mapped by the above code.  motivation: Emacs' default binding for
  ;; RET is `newline' and C-j is `newline-and-indent'.  Most Alamaticeers
  ;; expect RET to do a `ala-newline-and-indent' and any Emacsers who
  ;; dislike this are probably knowledgeable enough to do a rebind.
  ;; However, we do *not* change C-j since many Emacsers have already
  ;; swapped RET and C-j and they don't want C-j bound to `newline' to
  ;; change.
  (define-key ala-mode-map "\C-m" 'ala-newline-and-indent)
  )

(defvar ala-mode-output-map nil
  "Keymap used in *Alamatic Output* buffers.")
(if ala-mode-output-map
    nil
  (setq ala-mode-output-map (make-sparse-keymap))
  (define-key ala-mode-output-map [button2]  'ala-mouseto-exception)
  (define-key ala-mode-output-map "\C-c\C-c" 'ala-goto-exception)
  ;; TBD: Disable all self-inserting keys.  This is bogus, we should
  ;; really implement this as *Alamatic Output* buffer being read-only
  (mapc #' (lambda (key)
             (define-key ala-mode-output-map key
               #'(lambda () (interactive) (beep))))
           (where-is-internal 'self-insert-command))
  )

(defvar ala-shell-map nil
  "Keymap used in *Alamatic* shell buffers.")
;(if ala-shell-map
;    nil
;  (setq ala-shell-map (coala-keymap comint-mode-map))
;  (define-key ala-shell-map [tab]   'tab-to-tab-stop)
;  (define-key ala-shell-map "\C-c-" 'ala-up-exception)
;  (define-key ala-shell-map "\C-c=" 'ala-down-exception)
;  )

(defvar ala-mode-syntax-table nil
  "Syntax table used in `alamatic-mode' buffers.")
(when (not ala-mode-syntax-table)
  (setq ala-mode-syntax-table (make-syntax-table))
  (modify-syntax-entry ?\( "()" ala-mode-syntax-table)
  (modify-syntax-entry ?\) ")(" ala-mode-syntax-table)
  (modify-syntax-entry ?\[ "(]" ala-mode-syntax-table)
  (modify-syntax-entry ?\] ")[" ala-mode-syntax-table)
  (modify-syntax-entry ?\{ "(}" ala-mode-syntax-table)
  (modify-syntax-entry ?\} "){" ala-mode-syntax-table)
  ;; Add operator symbols misassigned in the std table
  (modify-syntax-entry ?\$ "."  ala-mode-syntax-table)
  (modify-syntax-entry ?\% "."  ala-mode-syntax-table)
  (modify-syntax-entry ?\& "."  ala-mode-syntax-table)
  (modify-syntax-entry ?\* "."  ala-mode-syntax-table)
  (modify-syntax-entry ?\+ "."  ala-mode-syntax-table)
  (modify-syntax-entry ?\- "."  ala-mode-syntax-table)
  (modify-syntax-entry ?\/ "."  ala-mode-syntax-table)
  (modify-syntax-entry ?\< "."  ala-mode-syntax-table)
  (modify-syntax-entry ?\= "."  ala-mode-syntax-table)
  (modify-syntax-entry ?\> "."  ala-mode-syntax-table)
  (modify-syntax-entry ?\| "."  ala-mode-syntax-table)
  ;; For historical reasons, underscore is word class instead of
  ;; symbol class.  GNU conventions say it should be symbol class, but
  ;; there's a natural conflict between what major mode authors want
  ;; and what users expect from `forward-word' and `backward-word'.
  ;; Guido and I have hashed this out and have decided to keep
  ;; underscore in word class.  If you're tempted to change it, try
  ;; binding M-f and M-b to ala-forward-into-nomenclature and
  ;; ala-backward-into-nomenclature instead.  This doesn't help in all
  ;; situations where you'd want the different behavior
  ;; (e.g. backward-kill-word).
  (modify-syntax-entry ?\_ "w"  ala-mode-syntax-table)
  ;; Both single quote and double quote are string delimiters
  (modify-syntax-entry ?\' "\"" ala-mode-syntax-table)
  (modify-syntax-entry ?\" "\"" ala-mode-syntax-table)
  ;; backquote is open and close paren
  (modify-syntax-entry ?\` "$"  ala-mode-syntax-table)
  ;; comment delimiters
  (modify-syntax-entry ?\# "<"  ala-mode-syntax-table)
  (modify-syntax-entry ?\n ">"  ala-mode-syntax-table)
  )

;; An auxiliary syntax table which places underscore and dot in the
;; symbol class for simplicity
(defvar ala-dotted-expression-syntax-table nil
  "Syntax table used to identify Alamatic dotted expressions.")
;(when (not ala-dotted-expression-syntax-table)
;  (setq ala-dotted-expression-syntax-table
;        (coala-syntax-table ala-mode-syntax-table))
;  (modify-syntax-entry ?_ "_" ala-dotted-expression-syntax-table)
;  (modify-syntax-entry ?. "_" ala-dotted-expression-syntax-table))



;; Utilities
(defmacro ala-safe (&rest body)
  "Safely execute BODY, return nil if an error occurred."
  `(condition-case nil
       (progn ,@ body)
     (error nil)))

(defsubst ala-keep-region-active ()
  "Keep the region active in XEmacs."
  ;; Ignore byte-compiler warnings you might see.  Also note that
  ;; FSF's Emacs 19 does it differently; its policy doesn't require us
  ;; to take explicit action.
  (and (boundp 'zmacs-region-stays)
       (setq zmacs-region-stays t)))

(defsubst ala-point (position)
  "Returns the value of point at certain commonly referenced POSITIONs.
POSITION can be one of the following symbols:

  bol  -- beginning of line
  eol  -- end of line
  bod  -- beginning of def or class
  eod  -- end of def or class
  bob  -- beginning of buffer
  eob  -- end of buffer
  boi  -- back to indentation
  bos  -- beginning of statement

This function does not modify point or mark."
  (let ((here (point)))
    (cond
     ((eq position 'bol) (beginning-of-line))
     ((eq position 'eol) (end-of-line))
     ((eq position 'bod) (ala-beginning-of-def-or-class 'either))
     ((eq position 'eod) (ala-end-of-def-or-class 'either))
     ;; Kind of funny, I know, but useful for ala-up-exception.
     ((eq position 'bob) (goto-char (point-min)))
     ((eq position 'eob) (goto-char (point-max)))
     ((eq position 'boi) (back-to-indentation))
     ((eq position 'bos) (ala-goto-initial-line))
     (t (error "Unknown buffer position requested: %s" position))
     )
    (prog1
        (point)
      (goto-char here))))

(defsubst ala-highlight-line (from to file line)
  (cond
   ((fboundp 'make-extent)
    ;; XEmacs
    (let ((e (make-extent from to)))
      (set-extent-property e 'mouse-face 'highlight)
      (set-extent-property e 'ala-exc-info (cons file line))
      (set-extent-property e 'keymap ala-mode-output-map)))
   (t
    ;; Emacs -- Please port this!
    )
   ))

(defun ala-in-literal (&optional lim)
  "Return non-nil if point is in a Alamatic literal (a comment or string).
Optional argument LIM indicates the beginning of the containing form,
i.e. the limit on how far back to scan."
  ;; This is the version used for non-XEmacs, which has a nicer
  ;; interface.
  ;;
  ;; WARNING: Watch out for infinite recursion.
  (let* ((lim (or lim (ala-point 'bod)))
         (state (parse-partial-sexp lim (point))))
    (cond
     ((nth 3 state) 'string)
     ((nth 4 state) 'comment)
     (t nil))))

;; XEmacs has a built-in function that should make this much quicker.
;; In this case, lim is ignored
(defun ala-fast-in-literal (&optional lim)
  "Fast version of `ala-in-literal', used only by XEmacs.
Optional LIM is ignored."
  ;; don't have to worry about context == 'block-comment
  (buffer-syntactic-context))

(if (fboundp 'buffer-syntactic-context)
    (defalias 'ala-in-literal 'ala-fast-in-literal))



;; Menu definitions, only relevent if you have the easymenu.el package
;; (standard in the latest Emacs 19 and XEmacs 19 distributions).
(defvar ala-menu nil
  "Menu for Alamatic Mode.
This menu will get created automatically if you have the `easymenu'
package.  Note that the latest X/Emacs releases contain this package.")

(and (ala-safe (require 'easymenu) t)
     (easy-menu-define
      ala-menu ala-mode-map "Alamatic Mode menu"
      '("Alamatic"
        ["Comment Out Region"   ala-comment-region  (mark)]
        ["Uncomment Region"     (ala-comment-region (point) (mark) '(4)) (mark)]
        "-"
        ["Mark current block"   ala-mark-block t]
        ["Mark current def"     ala-mark-def-or-class t]
        ["Mark current class"   (ala-mark-def-or-class t) t]
        "-"
        ["Shift region left"    ala-shift-region-left (mark)]
        ["Shift region right"   ala-shift-region-right (mark)]
        "-"
        ["Import/reload file"   ala-execute-import-or-reload t]
        ["Execute buffer"       ala-execute-buffer t]
        ["Execute region"       ala-execute-region (mark)]
        ["Execute def or class" ala-execute-def-or-class (mark)]
        ["Execute string"       ala-execute-string t]
        ["Start interpreter..." ala-shell t]
        "-"
        ["Go to start of block" ala-goto-block-up t]
        ["Go to start of class" (ala-beginning-of-def-or-class t) t]
        ["Move to end of class" (ala-end-of-def-or-class t) t]
        ["Move to start of def" ala-beginning-of-def-or-class t]
        ["Move to end of def"   ala-end-of-def-or-class t]
        "-"
        ["Describe mode"        ala-describe-mode t]
        )))



;; Imenu definitions
(defvar ala-imenu-class-regexp
  (concat                               ; <<classes>>
   "\\("                                ;
   "^[ \t]*"                            ; newline and maybe whitespace
   "\\(class[ \t]+[a-zA-Z0-9_]+\\)"     ; class name
                                        ; possibly multiple superclasses
   "\\([ \t]*\\((\\([a-zA-Z0-9_,. \t\n]\\)*)\\)?\\)"
   "[ \t]*:"                            ; and the final :
   "\\)"                                ; >>classes<<
   )
  "Regexp for Alamatic classes for use with the Imenu package."
  )

(defvar ala-imenu-method-regexp
  (concat                               ; <<methods and functions>>
   "\\("                                ;
   "^[ \t]*"                            ; new line and maybe whitespace
   "\\(def[ \t]+"                       ; function definitions start with def
   "\\([a-zA-Z0-9_]+\\)"                ;   name is here
                                        ;   function arguments...
;;   "[ \t]*(\\([-+/a-zA-Z0-9_=,\* \t\n.()\"'#]*\\))"
   "[ \t]*(\\([^:#]*\\))"
   "\\)"                                ; end of def
   "[ \t]*:"                            ; and then the :
   "\\)"                                ; >>methods and functions<<
   )
  "Regexp for Alamatic methods/functions for use with the Imenu package."
  )

(defvar ala-imenu-method-no-arg-parens '(2 8)
  "Indices into groups of the Alamatic regexp for use with Imenu.

Using these values will result in smaller Imenu lists, as arguments to
functions are not listed.

See the variable `ala-imenu-show-method-args-p' for more
information.")

(defvar ala-imenu-method-arg-parens '(2 7)
  "Indices into groups of the Alamatic regexp for use with imenu.
Using these values will result in large Imenu lists, as arguments to
functions are listed.

See the variable `ala-imenu-show-method-args-p' for more
information.")

;; Note that in this format, this variable can still be used with the
;; imenu--generic-function. Otherwise, there is no real reason to have
;; it.
(defvar ala-imenu-generic-expression
  (cons
   (concat
    ala-imenu-class-regexp
    "\\|"                               ; or...
    ala-imenu-method-regexp
    )
   ala-imenu-method-no-arg-parens)
  "Generic Alamatic expression which may be used directly with Imenu.
Used by setting the variable `imenu-generic-expression' to this value.
Also, see the function \\[ala-imenu-create-index] for a better
alternative for finding the index.")

;; These next two variables are used when searching for the Alamatic
;; class/definitions. Just saving some time in accessing the
;; generic-alamatic-expression, really.
(defvar ala-imenu-generic-regexp nil)
(defvar ala-imenu-generic-parens nil)


(defun ala-imenu-create-index-function ()
  "Alamatic interface function for the Imenu package.
Finds all Alamatic classes and functions/methods. Calls function
\\[ala-imenu-create-index-engine].  See that function for the details
of how this works."
  (setq ala-imenu-generic-regexp (car ala-imenu-generic-expression)
        ala-imenu-generic-parens (if ala-imenu-show-method-args-p
                                    ala-imenu-method-arg-parens
                                  ala-imenu-method-no-arg-parens))
  (goto-char (point-min))
  ;; Warning: When the buffer has no classes or functions, this will
  ;; return nil, which seems proper according to the Imenu API, but
  ;; causes an error in the XEmacs port of Imenu.  Sigh.
  (ala-imenu-create-index-engine nil))

(defun ala-imenu-create-index-engine (&optional start-indent)
  "Function for finding Imenu definitions in Alamatic.

Finds all definitions (classes, methods, or functions) in a Alamatic
file for the Imenu package.

Returns a possibly nested alist of the form

        (INDEX-NAME . INDEX-POSITION)

The second element of the alist may be an alist, producing a nested
list as in

        (INDEX-NAME . INDEX-ALIST)

This function should not be called directly, as it calls itself
recursively and requires some setup.  Rather this is the engine for
the function \\[ala-imenu-create-index-function].

It works recursively by looking for all definitions at the current
indention level.  When it finds one, it adds it to the alist.  If it
finds a definition at a greater indentation level, it removes the
previous definition from the alist. In its place it adds all
definitions found at the next indentation level.  When it finds a
definition that is less indented then the current level, it returns
the alist it has created thus far.

The optional argument START-INDENT indicates the starting indentation
at which to continue looking for Alamatic classes, methods, or
functions.  If this is not supplied, the function uses the indentation
of the first definition found."
  (let (index-alist
        sub-method-alist
        looking-p
        def-name prev-name
        cur-indent def-pos
        (class-paren (first  ala-imenu-generic-parens))
        (def-paren   (second ala-imenu-generic-parens)))
    (setq looking-p
          (re-search-forward ala-imenu-generic-regexp (point-max) t))
    (while looking-p
      (save-excursion
        ;; used to set def-name to this value but generic-extract-name
        ;; is new to imenu-1.14. this way it still works with
        ;; imenu-1.11
        ;;(imenu--generic-extract-name ala-imenu-generic-parens))
        (let ((cur-paren (if (match-beginning class-paren)
                             class-paren def-paren)))
          (setq def-name
                (buffer-substring-no-properties (match-beginning cur-paren)
                                                (match-end cur-paren))))
        (save-match-data
          (ala-beginning-of-def-or-class 'either))
        (beginning-of-line)
        (setq cur-indent (current-indentation)))
      ;; HACK: want to go to the next correct definition location.  We
      ;; explicitly list them here but it would be better to have them
      ;; in a list.
      (setq def-pos
            (or (match-beginning class-paren)
                (match-beginning def-paren)))
      ;; if we don't have a starting indent level, take this one
      (or start-indent
          (setq start-indent cur-indent))
      ;; if we don't have class name yet, take this one
      (or prev-name
          (setq prev-name def-name))
      ;; what level is the next definition on?  must be same, deeper
      ;; or shallower indentation
      (cond
       ;; Skip code in comments and strings
       ((ala-in-literal))
       ;; at the same indent level, add it to the list...
       ((= start-indent cur-indent)
        (push (cons def-name def-pos) index-alist))
       ;; deeper indented expression, recurse
       ((< start-indent cur-indent)
        ;; the point is currently on the expression we're supposed to
        ;; start on, so go back to the last expression. The recursive
        ;; call will find this place again and add it to the correct
        ;; list
        (re-search-backward ala-imenu-generic-regexp (point-min) 'move)
        (setq sub-method-alist (ala-imenu-create-index-engine cur-indent))
        (if sub-method-alist
            ;; we put the last element on the index-alist on the start
            ;; of the submethod alist so the user can still get to it.
            (let ((save-elmt (pop index-alist)))
              (push (cons prev-name
                          (cons save-elmt sub-method-alist))
                    index-alist))))
       ;; found less indented expression, we're done.
       (t
        (setq looking-p nil)
        (re-search-backward ala-imenu-generic-regexp (point-min) t)))
      ;; end-cond
      (setq prev-name def-name)
      (and looking-p
           (setq looking-p
                 (re-search-forward ala-imenu-generic-regexp
                                    (point-max) 'move))))
    (nreverse index-alist)))



(defun ala-choose-shell-by-shebang ()
  "Choose CAlamatic or Jython mode by looking at #! on the first line.
Returns the appropriate mode function.
Used by `ala-choose-shell', and similar to but distinct from
`set-auto-mode', though it uses `auto-mode-interpreter-regexp' (if available)."
  ;; look for an interpreter specified in the first line
  ;; similar to set-auto-mode (files.el)
  (let* ((re (if (boundp 'auto-mode-interpreter-regexp)
                 auto-mode-interpreter-regexp
               ;; stolen from Emacs 21.2
               "#![ \t]?\\([^ \t\n]*/bin/env[ \t]\\)?\\([^ \t\n]+\\)"))
         (interpreter (save-excursion
                        (goto-char (point-min))
                        (if (looking-at re)
                            (match-string 2)
                          "")))
         elt)
    ;; Map interpreter name to a mode.
    (setq elt (assoc (file-name-nondirectory interpreter)
                     ala-shell-alist))
    (and elt (caddr elt))))



(defun ala-choose-shell-by-import ()
  "Choose CAlamatic or Jython mode based imports.
If a file imports any packages in `ala-jython-packages', within
`ala-import-check-point-max' characters from the start of the file,
return `jython', otherwise return nil."
  (let (mode)
    (save-excursion
      (goto-char (point-min))
      (while (and (not mode)
                  (search-forward-regexp
                   "^\\(\\(from\\)\\|\\(import\\)\\) \\([^ \t\n.]+\\)"
                   ala-import-check-point-max t))
        (setq mode (and (member (match-string 4) ala-jython-packages)
                        'jython
                        ))))
    mode))


(defun ala-choose-shell ()
  "Choose CAlamatic or Jython mode. Returns the appropriate mode function.
This does the following:
 - look for an interpreter with `ala-choose-shell-by-shebang'
 - examine imports using `ala-choose-shell-by-import'
 - default to the variable `ala-default-interpreter'"
  (interactive)
  (or (ala-choose-shell-by-shebang)
      (ala-choose-shell-by-import)
      ala-default-interpreter
;      'calamatic ;; don't use to ala-default-interpreter, because default
;               ;; is only way to choose CAlamatic
      ))


;;;###autoload
(defun alamatic-mode ()
  "Major mode for editing Alamatic files.
To submit a problem report, enter `\\[ala-submit-bug-report]' from a
`alamatic-mode' buffer.  Do `\\[ala-describe-mode]' for detailed
documentation.  To see what version of `alamatic-mode' you are running,
enter `\\[ala-version]'.

This mode knows about Alamatic indentation, tokens, comments and
continuation lines.  Paragraphs are separated by blank lines only.

COMMANDS
\\{ala-mode-map}
VARIABLES

ala-indent-offset\t\tindentation increment
ala-block-comment-prefix\t\tcomment string used by `comment-region'
ala-alamatic-command\t\tshell command to invoke Alamatic interpreter
ala-temp-directory\t\tdirectory used for temp files (if needed)
ala-beep-if-tab-change\t\tring the bell if `tab-width' is changed"
  (interactive)
  ;; set up local variables
  (kill-all-local-variables)
  (make-local-variable 'font-lock-defaults)
  (make-local-variable 'paragraph-separate)
  (make-local-variable 'paragraph-start)
  (make-local-variable 'require-final-newline)
  (make-local-variable 'comment-start)
  (make-local-variable 'comment-end)
  (make-local-variable 'comment-start-skip)
  (make-local-variable 'comment-column)
  (make-local-variable 'comment-indent-function)
  (make-local-variable 'indent-region-function)
  (make-local-variable 'indent-line-function)
  (make-local-variable 'add-log-current-defun-function)
  (make-local-variable 'fill-paragraph-function)
  ;;
  (set-syntax-table ala-mode-syntax-table)
  (setq major-mode              'alamatic-mode
        mode-name               "Alamatic"
        local-abbrev-table      alamatic-mode-abbrev-table
        font-lock-defaults      '(alamatic-font-lock-keywords)
        paragraph-separate      "^[ \t]*$"
        paragraph-start         "^[ \t]*$"
        require-final-newline   t
        comment-start           "# "
        comment-end             ""
        comment-start-skip      "# *"
        comment-column          40
        comment-indent-function 'ala-comment-indent-function
        indent-region-function  'ala-indent-region
        indent-line-function    'ala-indent-line
        ;; tell add-log.el how to find the current function/method/variable
        add-log-current-defun-function 'ala-current-defun

        fill-paragraph-function 'ala-fill-paragraph
        )
  (use-local-map ala-mode-map)
  ;; add the menu
  (if ala-menu
      (easy-menu-add ala-menu))
  ;; Emacs 19 requires this
  (if (boundp 'comment-multi-line)
      (setq comment-multi-line nil))
  ;; Install Imenu if available
  (when (ala-safe (require 'imenu))
    (setq imenu-create-index-function #'ala-imenu-create-index-function)
    (setq imenu-generic-expression ala-imenu-generic-expression)
    (if (fboundp 'imenu-add-to-menubar)
        (imenu-add-to-menubar (format "%s-%s" "IM" mode-name)))
    )
  ;; Run the mode hook.  Note that ala-mode-hook is deprecated.
  (if alamatic-mode-hook
      (run-hooks 'alamatic-mode-hook)
    (run-hooks 'ala-mode-hook))
  ;; Now do the automagical guessing
  (if ala-smart-indentation
    (let ((offset ala-indent-offset))
      ;; It's okay if this fails to guess a good value
      (if (and (ala-safe (ala-guess-indent-offset))
               (<= ala-indent-offset 8)
               (>= ala-indent-offset 2))
          (setq offset ala-indent-offset))
      (setq ala-indent-offset offset)
      ;; Only turn indent-tabs-mode off if tab-width !=
      ;; ala-indent-offset.  Never turn it on, because the user must
      ;; have explicitly turned it off.
      (if (/= tab-width ala-indent-offset)
          (setq indent-tabs-mode nil))
      ))
  ;; Set the default shell if not already set
  (when (null ala-which-shell)
    (ala-toggle-shells (ala-choose-shell))))


(make-obsolete 'jalamatic-mode 'jython-mode)
(defun jython-mode ()
  "Major mode for editing Jython/Jython files.
This is a simple wrapper around `alamatic-mode'.
It runs `jython-mode-hook' then calls `alamatic-mode.'
It is added to `interpreter-mode-alist' and `ala-choose-shell'.
"
  (interactive)
  (alamatic-mode)
  (ala-toggle-shells 'jython)
  (when jython-mode-hook
      (run-hooks 'jython-mode-hook)))


;; It's handy to add recognition of Alamatic files to the
;; interpreter-mode-alist and to auto-mode-alist.  With the former, we
;; can specify different `derived-modes' based on the #! line, but
;; with the latter, we can't.  So we just won't add them if they're
;; already added.
;;;###autoload
(let ((modes '(("jython" . jython-mode)
               ("alamatic" . alamatic-mode))))
  (while modes
    (when (not (assoc (car modes) interpreter-mode-alist))
      (push (car modes) interpreter-mode-alist))
    (setq modes (cdr modes))))
;;;###autoload
(when (not (or (rassq 'alamatic-mode auto-mode-alist)
               (rassq 'jython-mode auto-mode-alist)))
  (push '("\\.ala$" . alamatic-mode) auto-mode-alist))



;; electric characters
(defun ala-outdent-p ()
  "Returns non-nil if the current line should dedent one level."
  (save-excursion
    (and (progn (back-to-indentation)
                (looking-at ala-outdent-re))
         ;; short circuit infloop on illegal construct
         (not (bobp))
         (progn (forward-line -1)
                (ala-goto-initial-line)
                (back-to-indentation)
                (while (or (looking-at ala-blank-or-comment-re)
                           (bobp))
                  (backward-to-indentation 1))
                (not (looking-at ala-no-outdent-re)))
         )))

(defun ala-electric-colon (arg)
  "Insert a colon.
In certain cases the line is dedented appropriately.  If a numeric
argument ARG is provided, that many colons are inserted
non-electrically.  Electric behavior is inhibited inside a string or
comment."
  (interactive "*P")
  (self-insert-command (prefix-numeric-value arg))
  ;; are we in a string or comment?
  (if (save-excursion
        (let ((pps (parse-partial-sexp (save-excursion
                                         (ala-beginning-of-def-or-class)
                                         (point))
                                       (point))))
          (not (or (nth 3 pps) (nth 4 pps)))))
      (save-excursion
        (let ((here (point))
              (outdent 0)
              (indent (ala-compute-indentation t)))
          (if (and (not arg)
                   (ala-outdent-p)
                   (= indent (save-excursion
                               (ala-next-statement -1)
                               (ala-compute-indentation t)))
                   )
              (setq outdent ala-indent-offset))
          ;; Don't indent, only dedent.  This assumes that any lines
          ;; that are already dedented relative to
          ;; ala-compute-indentation were put there on purpose.  It's
          ;; highly annoying to have `:' indent for you.  Use TAB, C-c
          ;; C-l or C-c C-r to adjust.  TBD: Is there a better way to
          ;; determine this???
          (if (< (current-indentation) indent) nil
            (goto-char here)
            (beginning-of-line)
            (delete-horizontal-space)
            (indent-to (- indent outdent))
            )))))


;; Alamatic subprocess utilities and filters
(defun ala-execute-file (proc filename)
  "Send to Alamatic interpreter process PROC \"execfile('FILENAME')\".
Make that process's buffer visible and force display.  Also make
comint believe the user typed this string so that
`kill-output-from-shell' does The Right Thing."
  (let ((curbuf (current-buffer))
        (procbuf (process-buffer proc))
;       (comint-scroll-to-bottom-on-output t)
        (msg (format "## working on region in file %s...\n" filename))
        ;; add some comment, so that we can filter it out of history
        (cmd (format "execfile(r'%s') # ALAMATIC-MODE\n" filename)))
    (unwind-protect
        (save-excursion
          (set-buffer procbuf)
          (goto-char (point-max))
          (move-marker (process-mark proc) (point))
          (funcall (process-filter proc) proc msg))
      (set-buffer curbuf))
    (process-send-string proc cmd)))

(defun ala-comint-output-filter-function (string)
  "Watch output for Alamatic prompt and exec next file waiting in queue.
This function is appropriate for `comint-output-filter-functions'."
  ;;remove ansi terminal escape sequences from string, not sure why they are
  ;;still around...
  (setq string (ansi-color-filter-apply string))
  (when (and (string-match ala-shell-input-prompt-1-regexp string)
                   ala-file-queue)
    (if ala-shell-switch-buffers-on-execute
      (pop-to-buffer (current-buffer)))
    (ala-safe (delete-file (car ala-file-queue)))
    (setq ala-file-queue (cdr ala-file-queue))
    (if ala-file-queue
        (let ((pyproc (get-buffer-process (current-buffer))))
          (ala-execute-file pyproc (car ala-file-queue))))
    ))

(defun ala-pdbtrack-overlay-arrow (activation)
  "Activate or de arrow at beginning-of-line in current buffer."
  ;; This was derived/simplified from edebug-overlay-arrow
  (cond (activation
         (setq overlay-arrow-position (make-marker))
         (setq overlay-arrow-string "=>")
         (set-marker overlay-arrow-position (ala-point 'bol) (current-buffer))
         (setq ala-pdbtrack-is-tracking-p t))
        (overlay-arrow-position
         (setq overlay-arrow-position nil)
         (setq ala-pdbtrack-is-tracking-p nil))
        ))

(defun ala-pdbtrack-track-stack-file (text)
  "Show the file indicated by the pdb stack entry line, in a separate window.

Activity is disabled if the buffer-local variable
`ala-pdbtrack-do-tracking-p' is nil.

We depend on the pdb input prompt matching `ala-pdbtrack-input-prompt'
at the beginning of the line.

If the traceback target file path is invalid, we look for the most
recently visited alamatic-mode buffer which either has the name of the
current function \(or class) or which defines the function \(or
class).  This is to provide for remote scripts, eg, Zope's 'Script
(Alamatic)' - put a _copy_ of the script in a buffer named for the
script, and set to alamatic-mode, and pdbtrack will find it.)"
  ;; Instead of trying to piece things together from partial text
  ;; (which can be almost useless depending on Emacs version), we
  ;; monitor to the point where we have the next pdb prompt, and then
  ;; check all text from comint-last-input-end to process-mark.
  ;;
  ;; Also, we're very conservative about clearing the overlay arrow,
  ;; to minimize residue.  This means, for instance, that executing
  ;; other pdb commands wipe out the highlight.  You can always do a
  ;; 'where' (aka 'w') command to reveal the overlay arrow.
  (let* ((origbuf (current-buffer))
         (currproc (get-buffer-process origbuf)))

    (if (not (and currproc ala-pdbtrack-do-tracking-p))
        (ala-pdbtrack-overlay-arrow nil)

      (let* ((procmark (process-mark currproc))
             (block (buffer-substring (max comint-last-input-end
                                           (- procmark
                                              ala-pdbtrack-track-range))
                                      procmark))
             target target_fname target_lineno target_buffer)

        (if (not (string-match (concat ala-pdbtrack-input-prompt "$") block))
            (ala-pdbtrack-overlay-arrow nil)

          (setq target (ala-pdbtrack-get-source-buffer block))

          (if (stringp target)
              (message "pdbtrack: %s" target)

            (setq target_lineno (car target))
            (setq target_buffer (cadr target))
            (setq target_fname (buffer-file-name target_buffer))
            (switch-to-buffer-other-window target_buffer)
            (goto-line target_lineno)
            (message "pdbtrack: line %s, file %s" target_lineno target_fname)
            (ala-pdbtrack-overlay-arrow t)
            (pop-to-buffer origbuf t)

            )))))
  )

(defun ala-pdbtrack-get-source-buffer (block)
  "Return line number and buffer of code indicated by block's traceback text.

We look first to visit the file indicated in the trace.

Failing that, we look for the most recently visited alamatic-mode buffer
with the same name or having the named function.

If we're unable find the source code we return a string describing the
problem as best as we can determine."

  (if (not (string-match ala-pdbtrack-stack-entry-regexp block))

      "Traceback cue not found"

    (let* ((filename (match-string 1 block))
           (lineno (string-to-number (match-string 2 block)))
           (funcname (match-string 3 block))
           funcbuffer)

      (cond ((file-exists-p filename)
             (list lineno (find-file-noselect filename)))

            ((setq funcbuffer (ala-pdbtrack-grub-for-buffer funcname lineno))
             (if (string-match "/Script (Alamatic)$" filename)
                 ;; Add in number of lines for leading '##' comments:
                 (setq lineno
                       (+ lineno
                          (save-excursion
                            (set-buffer funcbuffer)
                            (count-lines
                             (point-min)
                             (max (point-min)
                                  (string-match "^\\([^#]\\|#[^#]\\|#$\\)"
                                                (buffer-substring (point-min)
                                                                  (point-max)))
                                  ))))))
             (list lineno funcbuffer))

            ((= (elt filename 0) ?\<)
             (format "(Non-file source: '%s')" filename))

            (t (format "Not found: %s(), %s" funcname filename)))
      )
    )
  )

(defun ala-pdbtrack-grub-for-buffer (funcname lineno)
  "Find most recent buffer itself named or having function funcname.

We walk the buffer-list history for alamatic-mode buffers that are
named for funcname or define a function funcname."
  (let ((buffers (buffer-list))
        buf
        got)
    (while (and buffers (not got))
      (setq buf (car buffers)
            buffers (cdr buffers))
      (if (and (save-excursion (set-buffer buf)
                               (string= major-mode "alamatic-mode"))
               (or (string-match funcname (buffer-name buf))
                   (string-match (concat "^\\s-*\\(def\\|class\\)\\s-+"
                                         funcname "\\s-*(")
                                 (save-excursion
                                   (set-buffer buf)
                                   (buffer-substring (point-min)
                                                     (point-max))))))
          (setq got buf)))
    got))

(defun ala-postprocess-output-buffer (buf)
  "Highlight exceptions found in BUF.
If an exception occurred return t, otherwise return nil.  BUF must exist."
  (let (line file bol err-p)
    (save-excursion
      (set-buffer buf)
      (goto-char (point-min))
      (while (re-search-forward ala-traceback-line-re nil t)
        (setq file (match-string 1)
              line (string-to-number (match-string 2))
              bol (ala-point 'bol))
        (ala-highlight-line bol (ala-point 'eol) file line)))
    (when (and ala-jump-on-exception line)
      (beep)
      (ala-jump-to-exception file line)
      (setq err-p t))
    err-p))



;;; Subprocess commands

;; only used when (memq 'broken-temp-names ala-emacs-features)
(defvar ala-serial-number 0)
(defvar ala-exception-buffer nil)
(defvar ala-output-buffer "*Alamatic Output*")
(make-variable-buffer-local 'ala-output-buffer)

;; for toggling between CAlamatic and Jython
(defvar ala-which-shell nil)
(defvar ala-which-args  ala-alamatic-command-args)
(defvar ala-which-bufname "Alamatic")
(make-variable-buffer-local 'ala-which-shell)
(make-variable-buffer-local 'ala-which-args)
(make-variable-buffer-local 'ala-which-bufname)

(defun ala-toggle-shells (arg)
  "Toggles between the CAlamatic and Jython shells.

With positive argument ARG (interactively \\[universal-argument]),
uses the CAlamatic shell, with negative ARG uses the Jython shell, and
with a zero argument, toggles the shell.

Programmatically, ARG can also be one of the symbols `calamatic' or
`jython', equivalent to positive arg and negative arg respectively."
  (interactive "P")
  ;; default is to toggle
  (if (null arg)
      (setq arg 0))
  ;; preprocess arg
  (cond
   ((equal arg 0)
    ;; toggle
    (if (string-equal ala-which-bufname "Alamatic")
        (setq arg -1)
      (setq arg 1)))
   ((equal arg 'calamatic) (setq arg 1))
   ((equal arg 'jython) (setq arg -1)))
  (let (msg)
    (cond
     ((< 0 arg)
      ;; set to CAlamatic
      (setq ala-which-shell ala-alamatic-command
            ala-which-args ala-alamatic-command-args
            ala-which-bufname "Alamatic"
            msg "CAlamatic")
      (if (string-equal ala-which-bufname "Jython")
          (setq mode-name "Alamatic")))
     ((> 0 arg)
      (setq ala-which-shell ala-jython-command
            ala-which-args ala-jython-command-args
            ala-which-bufname "Jython"
            msg "Jython")
      (if (string-equal ala-which-bufname "Alamatic")
          (setq mode-name "Jython")))
     )
    (message "Using the %s shell" msg)
    (setq ala-output-buffer (format "*%s Output*" ala-which-bufname))))

;;;###autoload
(defun ala-shell (&optional argprompt)
  "Start an interactive Alamatic interpreter in another window.
This is like Shell mode, except that Alamatic is running in the window
instead of a shell.  See the `Interactive Shell' and `Shell Mode'
sections of the Emacs manual for details, especially for the key
bindings active in the `*Alamatic*' buffer.

With optional \\[universal-argument], the user is prompted for the
flags to pass to the Alamatic interpreter.  This has no effect when this
command is used to switch to an existing process, only when a new
process is started.  If you use this, you will probably want to ensure
that the current arguments are retained (they will be included in the
prompt).  This argument is ignored when this function is called
programmatically, or when running in Emacs 19.34 or older.

Note: You can toggle between using the CAlamatic interpreter and the
Jython interpreter by hitting \\[ala-toggle-shells].  This toggles
buffer local variables which control whether all your subshell
interactions happen to the `*Jython*' or `*Alamatic*' buffers (the
latter is the name used for the CAlamatic buffer).

Warning: Don't use an interactive Alamatic if you change sys.ps1 or
sys.ps2 from their default values, or if you're running code that
prints `>>> ' or `... ' at the start of a line.  `alamatic-mode' can't
distinguish your output from Alamatic's output, and assumes that `>>> '
at the start of a line is a prompt from Alamatic.  Similarly, the Emacs
Shell mode code assumes that both `>>> ' and `... ' at the start of a
line are Alamatic prompts.  Bad things can happen if you fool either
mode.

Warning:  If you do any editing *in* the process buffer *while* the
buffer is accepting output from Alamatic, do NOT attempt to `undo' the
changes.  Some of the output (nowhere near the parts you changed!) may
be lost if you do.  This appears to be an Emacs bug, an unfortunate
interaction between undo and process filters; the same problem exists in
non-Alamatic process buffers using the default (Emacs-supplied) process
filter."
  (interactive "P")
  ;; Set the default shell if not already set
  (when (null ala-which-shell)
    (ala-toggle-shells ala-default-interpreter))
  (let ((args ala-which-args))
    (when (and argprompt
               (interactive-p)
               (fboundp 'split-string))
      ;; TBD: Perhaps force "-i" in the final list?
      (setq args (split-string
                  (read-string (concat ala-which-bufname
                                       " arguments: ")
                               (concat
                                (mapconcat 'identity ala-which-args " ") " ")
                               ))))
    (if (not (equal (buffer-name) "*Alamatic*"))
        (switch-to-buffer-other-window
         (apply 'make-comint ala-which-bufname ala-which-shell nil args))
      (apply 'make-comint ala-which-bufname ala-which-shell nil args))
    (make-local-variable 'comint-prompt-regexp)
    (setq comint-prompt-regexp (concat ala-shell-input-prompt-1-regexp "\\|"
                                       ala-shell-input-prompt-2-regexp "\\|"
                                       "^([Pp]db) "))
    (add-hook 'comint-output-filter-functions
              'ala-comint-output-filter-function)
    ;; pdbtrack
    (add-hook 'comint-output-filter-functions 'ala-pdbtrack-track-stack-file)
    (setq ala-pdbtrack-do-tracking-p t)
    (set-syntax-table ala-mode-syntax-table)
    (use-local-map ala-shell-map)
    (run-hooks 'ala-shell-hook)
    ))

(defun ala-clear-queue ()
  "Clear the queue of temporary files waiting to execute."
  (interactive)
  (let ((n (length ala-file-queue)))
    (mapc 'delete-file ala-file-queue)
    (setq ala-file-queue nil)
    (message "%d pending files de-queued." n)))


(defun ala-execute-region (start end &optional async)
  "Execute the region in a Alamatic interpreter.

The region is first copied into a temporary file (in the directory
`ala-temp-directory').  If there is no Alamatic interpreter shell
running, this file is executed synchronously using
`shell-command-on-region'.  If the program is long running, use
\\[universal-argument] to run the command asynchronously in its own
buffer.

When this function is used programmatically, arguments START and END
specify the region to execute, and optional third argument ASYNC, if
non-nil, specifies to run the command asynchronously in its own
buffer.

If the Alamatic interpreter shell is running, the region is execfile()'d
in that shell.  If you try to execute regions too quickly,
`alamatic-mode' will queue them up and execute them one at a time when
it sees a `>>> ' prompt from Alamatic.  Each time this happens, the
process buffer is popped into a window (if it's not already in some
window) so you can see it, and a comment of the form

    \t## working on region in file <name>...

is inserted at the end.  See also the command `ala-clear-queue'."
  (interactive "r\nP")
  ;; Skip ahead to the first non-blank line
  (let* ((proc (get-process ala-which-bufname))
         (temp (if (memq 'broken-temp-names ala-emacs-features)
                   (let
                       ((sn ala-serial-number)
                        (pid (and (fboundp 'emacs-pid) (emacs-pid))))
                     (setq ala-serial-number (1+ ala-serial-number))
                     (if pid
                         (format "alamatic-%d-%d" sn pid)
                       (format "alamatic-%d" sn)))
                 (make-temp-name "alamatic-")))
         (file (concat (expand-file-name temp ala-temp-directory) ".ala"))
         (cur (current-buffer))
         (buf (get-buffer-create file))
         shell)
    ;; Write the contents of the buffer, watching out for indented regions.
    (save-excursion
      (goto-char start)
      (beginning-of-line)
      (while (and (looking-at "\\s *$")
                  (< (point) end))
        (forward-line 1))
      (setq start (point))
      (or (< start end)
          (error "Region is empty"))
      (setq ala-line-number-offset (count-lines 1 start))
      (let ((needs-if (/= (ala-point 'bol) (ala-point 'boi))))
        (set-buffer buf)
        (alamatic-mode)
        (when needs-if
          (insert "if 1:\n")
          (setq ala-line-number-offset (- ala-line-number-offset 1)))
        (insert-buffer-substring cur start end)
        ;; Set the shell either to the #! line command, or to the
        ;; ala-which-shell buffer local variable.
        (setq shell (or (ala-choose-shell-by-shebang)
                        (ala-choose-shell-by-import)
                        ala-which-shell))))
    (cond
     ;; always run the code in its own asynchronous subprocess
     (async
      ;; User explicitly wants this to run in its own async subprocess
      (save-excursion
        (set-buffer buf)
        (write-region (point-min) (point-max) file nil 'nomsg))
      (let* ((buf (generate-new-buffer-name ala-output-buffer))
             ;; TBD: a horrible hack, but why create new Custom variables?
             (arg (if (string-equal ala-which-bufname "Alamatic")
                      "-u" "")))
        (start-process ala-which-bufname buf shell arg file)
        (pop-to-buffer buf)
        (ala-postprocess-output-buffer buf)
        ;; TBD: clean up the temporary file!
        ))
     ;; if the Alamatic interpreter shell is running, queue it up for
     ;; execution there.
     (proc
      ;; use the existing alamatic shell
      (save-excursion
        (set-buffer buf)
        (write-region (point-min) (point-max) file nil 'nomsg))
      (if (not ala-file-queue)
          (ala-execute-file proc file)
        (message "File %s queued for execution" file))
      (setq ala-file-queue (append ala-file-queue (list file)))
      (setq ala-exception-buffer (cons file (current-buffer))))
     (t
      ;; TBD: a horrible hack, but why create new Custom variables?
      (let ((cmd (concat ala-which-shell (if (string-equal ala-which-bufname
                                                          "Jython")
                                            " -" ""))))
        ;; otherwise either run it synchronously in a subprocess
        (save-excursion
          (set-buffer buf)
          (shell-command-on-region (point-min) (point-max)
                                   cmd ala-output-buffer))
        ;; shell-command-on-region kills the output buffer if it never
        ;; existed and there's no output from the command
        (if (not (get-buffer ala-output-buffer))
            (message "No output.")
          (setq ala-exception-buffer (current-buffer))
          (let ((err-p (ala-postprocess-output-buffer ala-output-buffer)))
            (pop-to-buffer ala-output-buffer)
            (if err-p
                (pop-to-buffer ala-exception-buffer)))
          ))
      ))
    ;; Clean up after ourselves.
    (kill-buffer buf)))


;; Code execution commands
(defun ala-execute-buffer (&optional async)
  "Send the contents of the buffer to a Alamatic interpreter.
If the file local variable `ala-master-file' is non-nil, execute the
named file instead of the buffer's file.

If there is a *Alamatic* process buffer it is used.  If a clipping
restriction is in effect, only the accessible portion of the buffer is
sent.  A trailing newline will be supplied if needed.

See the `\\[ala-execute-region]' docs for an account of some
subtleties, including the use of the optional ASYNC argument."
  (interactive "P")
  (let ((old-buffer (current-buffer)))
    (if ala-master-file
        (let* ((filename (expand-file-name ala-master-file))
               (buffer (or (get-file-buffer filename)
                           (find-file-noselect filename))))
          (set-buffer buffer)))
    (ala-execute-region (point-min) (point-max) async)
       (pop-to-buffer old-buffer)))

(defun ala-execute-import-or-reload (&optional async)
  "Import the current buffer's file in a Alamatic interpreter.

If the file has already been imported, then do reload instead to get
the latest version.

If the file's name does not end in \".ala\", then do execfile instead.

If the current buffer is not visiting a file, do `ala-execute-buffer'
instead.

If the file local variable `ala-master-file' is non-nil, import or
reload the named file instead of the buffer's file.  The file may be
saved based on the value of `ala-execute-import-or-reload-save-p'.

See the `\\[ala-execute-region]' docs for an account of some
subtleties, including the use of the optional ASYNC argument.

This may be preferable to `\\[ala-execute-buffer]' because:

 - Definitions stay in their module rather than appearing at top
   level, where they would clutter the global namespace and not affect
   uses of qualified names (MODULE.NAME).

 - The Alamatic debugger gets line number information about the functions."
  (interactive "P")
  ;; Check file local variable ala-master-file
  (if ala-master-file
      (let* ((filename (expand-file-name ala-master-file))
             (buffer (or (get-file-buffer filename)
                         (find-file-noselect filename))))
        (set-buffer buffer)))
  (let ((file (buffer-file-name (current-buffer))))
    (if file
        (progn
          ;; Maybe save some buffers
          (save-some-buffers (not ala-ask-about-save) nil)
          (ala-execute-string
           (if (string-match "\\.ala$" file)
               (let ((f (file-name-sans-extension
                         (file-name-nondirectory file))))
                 (format "if globals().has_key('%s'):\n    reload(%s)\nelse:\n    import %s\n"
                         f f f))
             (format "execfile(r'%s')\n" file))
           async))
      ;; else
      (ala-execute-buffer async))))


(defun ala-execute-def-or-class (&optional async)
  "Send the current function or class definition to a Alamatic interpreter.

If there is a *Alamatic* process buffer it is used.

See the `\\[ala-execute-region]' docs for an account of some
subtleties, including the use of the optional ASYNC argument."
  (interactive "P")
  (save-excursion
    (ala-mark-def-or-class)
    ;; mark is before point
    (ala-execute-region (mark) (point) async)))


(defun ala-execute-string (string &optional async)
  "Send the argument STRING to a Alamatic interpreter.

If there is a *Alamatic* process buffer it is used.

See the `\\[ala-execute-region]' docs for an account of some
subtleties, including the use of the optional ASYNC argument."
  (interactive "sExecute Alamatic command: ")
  (save-excursion
    (set-buffer (get-buffer-create
                 (generate-new-buffer-name " *Alamatic Command*")))
    (insert string)
    (ala-execute-region (point-min) (point-max) async)))



(defun ala-jump-to-exception (file line)
  "Jump to the Alamatic code in FILE at LINE."
  (let ((buffer (cond ((string-equal file "<stdin>")
                       (if (consp ala-exception-buffer)
                           (cdr ala-exception-buffer)
                         ala-exception-buffer))
                      ((and (consp ala-exception-buffer)
                            (string-equal file (car ala-exception-buffer)))
                       (cdr ala-exception-buffer))
                      ((ala-safe (find-file-noselect file)))
                      ;; could not figure out what file the exception
                      ;; is pointing to, so prompt for it
                      (t (find-file (read-file-name "Exception file: "
                                                    nil
                                                    file t))))))
    ;; Fiddle about with line number
    (setq line (+ ala-line-number-offset line))

    (pop-to-buffer buffer)
    ;; Force Alamatic mode
    (if (not (eq major-mode 'alamatic-mode))
        (alamatic-mode))
    (goto-line line)
    (message "Jumping to exception in file %s on line %d" file line)))

(defun ala-mouseto-exception (event)
  "Jump to the code which caused the Alamatic exception at EVENT.
EVENT is usually a mouse click."
  (interactive "e")
  (cond
   ((fboundp 'event-point)
    ;; XEmacs
    (let* ((point (event-point event))
           (buffer (event-buffer event))
           (e (and point buffer (extent-at point buffer 'ala-exc-info)))
           (info (and e (extent-property e 'ala-exc-info))))
      (message "Event point: %d, info: %s" point info)
      (and info
           (ala-jump-to-exception (car info) (cdr info)))
      ))
   ;; Emacs -- Please port this!
   ))

(defun ala-goto-exception ()
  "Go to the line indicated by the traceback."
  (interactive)
  (let (file line)
    (save-excursion
      (beginning-of-line)
      (if (looking-at ala-traceback-line-re)
          (setq file (match-string 1)
                line (string-to-number (match-string 2)))))
    (if (not file)
        (error "Not on a traceback line"))
    (ala-jump-to-exception file line)))

(defun ala-find-next-exception (start buffer searchdir errwhere)
  "Find the next Alamatic exception and jump to the code that caused it.
START is the buffer position in BUFFER from which to begin searching
for an exception.  SEARCHDIR is a function, either
`re-search-backward' or `re-search-forward' indicating the direction
to search.  ERRWHERE is used in an error message if the limit (top or
bottom) of the trackback stack is encountered."
  (let (file line)
    (save-excursion
      (set-buffer buffer)
      (goto-char (ala-point start))
      (if (funcall searchdir ala-traceback-line-re nil t)
          (setq file (match-string 1)
                line (string-to-number (match-string 2)))))
    (if (and file line)
        (ala-jump-to-exception file line)
      (error "%s of traceback" errwhere))))

(defun ala-down-exception (&optional bottom)
  "Go to the next line down in the traceback.
With \\[univeral-argument] (programmatically, optional argument
BOTTOM), jump to the bottom (innermost) exception in the exception
stack."
  (interactive "P")
  (let* ((proc (get-process "Alamatic"))
         (buffer (if proc "*Alamatic*" ala-output-buffer)))
    (if bottom
        (ala-find-next-exception 'eob buffer 're-search-backward "Bottom")
      (ala-find-next-exception 'eol buffer 're-search-forward "Bottom"))))

(defun ala-up-exception (&optional top)
  "Go to the previous line up in the traceback.
With \\[universal-argument] (programmatically, optional argument TOP)
jump to the top (outermost) exception in the exception stack."
  (interactive "P")
  (let* ((proc (get-process "Alamatic"))
         (buffer (if proc "*Alamatic*" ala-output-buffer)))
    (if top
        (ala-find-next-exception 'bob buffer 're-search-forward "Top")
      (ala-find-next-exception 'bol buffer 're-search-backward "Top"))))


;; Electric deletion
(defun ala-electric-backspace (arg)
  "Delete preceding character or levels of indentation.
Deletion is performed by calling the function in `ala-backspace-function'
with a single argument (the number of characters to delete).

If point is at the leftmost column, delete the preceding newline.

Otherwise, if point is at the leftmost non-whitespace character of a
line that is neither a continuation line nor a non-indenting comment
line, or if point is at the end of a blank line, this command reduces
the indentation to match that of the line that opened the current
block of code.  The line that opened the block is displayed in the
echo area to help you keep track of where you are.  With
\\[universal-argument] dedents that many blocks (but not past column
zero).

Otherwise the preceding character is deleted, converting a tab to
spaces if needed so that only a single column position is deleted.
\\[universal-argument] specifies how many characters to delete;
default is 1.

When used programmatically, argument ARG specifies the number of
blocks to dedent, or the number of characters to delete, as indicated
above."
  (interactive "*p")
  (if (or (/= (current-indentation) (current-column))
          (bolp)
          (ala-continuation-line-p)
;         (not ala-honor-comment-indentation)
;         (looking-at "#[^ \t\n]")      ; non-indenting #
          )
      (funcall ala-backspace-function arg)
    ;; else indent the same as the colon line that opened the block
    ;; force non-blank so ala-goto-block-up doesn't ignore it
    (insert-char ?* 1)
    (backward-char)
    (let ((base-indent 0)               ; indentation of base line
          (base-text "")                ; and text of base line
          (base-found-p nil))
      (save-excursion
        (while (< 0 arg)
          (condition-case nil           ; in case no enclosing block
              (progn
                (ala-goto-block-up 'no-mark)
                (setq base-indent (current-indentation)
                      base-text   (ala-suck-up-leading-text)
                      base-found-p t))
            (error nil))
          (setq arg (1- arg))))
      (delete-char 1)                   ; toss the dummy character
      (delete-horizontal-space)
      (indent-to base-indent)
      (if base-found-p
          (message "Closes block: %s" base-text)))))


(defun ala-electric-delete (arg)
  "Delete preceding or following character or levels of whitespace.

The behavior of this function depends on the variable
`delete-key-deletes-forward'.  If this variable is nil (or does not
exist, as in older Emacsen and non-XEmacs versions), then this
function behaves identically to \\[c-electric-backspace].

If `delete-key-deletes-forward' is non-nil and is supported in your
Emacs, then deletion occurs in the forward direction, by calling the
function in `ala-delete-function'.

\\[universal-argument] (programmatically, argument ARG) specifies the
number of characters to delete (default is 1)."
  (interactive "*p")
  (if (or (and (fboundp 'delete-forward-p) ;XEmacs 21
               (delete-forward-p))
          (and (boundp 'delete-key-deletes-forward) ;XEmacs 20
               delete-key-deletes-forward))
      (funcall ala-delete-function arg)
    (ala-electric-backspace arg)))

;; required for pending-del and delsel modes
(put 'ala-electric-colon 'delete-selection t) ;delsel
(put 'ala-electric-colon 'pending-delete   t) ;pending-del
(put 'ala-electric-backspace 'delete-selection 'supersede) ;delsel
(put 'ala-electric-backspace 'pending-delete   'supersede) ;pending-del
(put 'ala-electric-delete    'delete-selection 'supersede) ;delsel
(put 'ala-electric-delete    'pending-delete   'supersede) ;pending-del



(defun ala-indent-line (&optional arg)
  "Fix the indentation of the current line according to Alamatic rules.
With \\[universal-argument] (programmatically, the optional argument
ARG non-nil), ignore dedenting rules for block closing statements
(e.g. return, raise, break, continue, pass)

This function is normally bound to `indent-line-function' so
\\[indent-for-tab-command] will call it."
  (interactive "P")
  (let* ((ci (current-indentation))
         (move-to-indentation-p (<= (current-column) ci))
         (need (ala-compute-indentation (not arg)))
         (cc (current-column)))
    ;; dedent out a level if previous command was the same unless we're in
    ;; column 1
    (if (and (equal last-command this-command)
             (/= cc 0))
        (progn
          (beginning-of-line)
          (delete-horizontal-space)
          (indent-to (* (/ (- cc 1) ala-indent-offset) ala-indent-offset)))
      (progn
        ;; see if we need to dedent
        (if (ala-outdent-p)
            (setq need (- need ala-indent-offset)))
        (if (or ala-tab-always-indent
                move-to-indentation-p)
            (progn (if (/= ci need)
                       (save-excursion
                       (beginning-of-line)
                       (delete-horizontal-space)
                       (indent-to need)))
                   (if move-to-indentation-p (back-to-indentation)))
            (insert-tab))))))

(defun ala-newline-and-indent ()
  "Strives to act like the Emacs `newline-and-indent'.
This is just `strives to' because correct indentation can't be computed
from scratch for Alamatic code.  In general, deletes the whitespace before
point, inserts a newline, and takes an educated guess as to how you want
the new line indented."
  (interactive)
  (let ((ci (current-indentation)))
    (if (< ci (current-column))         ; if point beyond indentation
        (newline-and-indent)
      ;; else try to act like newline-and-indent "normally" acts
      (beginning-of-line)
      (insert-char ?\n 1)
      (move-to-column ci))))

(defun ala-compute-indentation (honor-block-close-p)
  "Compute Alamatic indentation.
When HONOR-BLOCK-CLOSE-P is non-nil, statements such as `return',
`raise', `break', `continue', and `pass' force one level of
dedenting."
  (save-excursion
    (beginning-of-line)
    (let* ((bod (ala-point 'bod))
           (pps (parse-partial-sexp bod (point)))
           (boipps (parse-partial-sexp bod (ala-point 'boi)))
           placeholder)
      (cond
       ;; are we inside a multi-line string or comment?
       ((or (and (nth 3 pps) (nth 3 boipps))
            (and (nth 4 pps) (nth 4 boipps)))
        (save-excursion
          (if (not ala-align-multiline-strings-p) 0
            ;; skip back over blank & non-indenting comment lines
            ;; note: will skip a blank or non-indenting comment line
            ;; that happens to be a continuation line too
            (re-search-backward "^[ \t]*\\([^ \t\n#]\\|#[ \t\n]\\)" nil 'move)
            (back-to-indentation)
            (current-column))))
       ;; are we on a continuation line?
       ((ala-continuation-line-p)
        (let ((startpos (point))
              (open-bracket-pos (ala-nesting-level))
              endpos searching found state cind cline)
          (if open-bracket-pos
              (progn
                (setq endpos (ala-point 'bol))
                (ala-goto-initial-line)
                (setq cind (current-indentation))
                (setq cline cind)
                (dolist (bp
                         (nth 9 (save-excursion
                                  (parse-partial-sexp (point) endpos)))
                         cind)
                  (if (search-forward "\n" bp t) (setq cline cind))
                  (goto-char (1+ bp))
                  (skip-chars-forward " \t")
                  (setq cind (if (memq (following-char) '(?\n ?# ?\\))
                                 (+ cline ala-indent-offset)
                               (current-column)))))
            ;; else on backslash continuation line
            (forward-line -1)
            (if (ala-continuation-line-p) ; on at least 3rd line in block
                (current-indentation)   ; so just continue the pattern
              ;; else started on 2nd line in block, so indent more.
              ;; if base line is an assignment with a start on a RHS,
              ;; indent to 2 beyond the leftmost "="; else skip first
              ;; chunk of non-whitespace characters on base line, + 1 more
              ;; column
              (end-of-line)
              (setq endpos (point)
                    searching t)
              (back-to-indentation)
              (setq startpos (point))
              ;; look at all "=" from left to right, stopping at first
              ;; one not nested in a list or string
              (while searching
                (skip-chars-forward "^=" endpos)
                (if (= (point) endpos)
                    (setq searching nil)
                  (forward-char 1)
                  (setq state (parse-partial-sexp startpos (point)))
                  (if (and (zerop (car state)) ; not in a bracket
                           (null (nth 3 state))) ; & not in a string
                      (progn
                        (setq searching nil) ; done searching in any case
                        (setq found
                              (not (or
                                    (eq (following-char) ?=)
                                    (memq (char-after (- (point) 2))
                                          '(?< ?> ?!)))))))))
              (if (or (not found)       ; not an assignment
                      (looking-at "[ \t]*\\\\")) ; <=><spaces><backslash>
                  (progn
                    (goto-char startpos)
                    (skip-chars-forward "^ \t\n")))
              ;; if this is a continuation for a block opening
              ;; statement, add some extra offset.
              (+ (current-column) (if (ala-statement-opens-block-p)
                                      ala-continuation-offset 0)
                 1)
              ))))

       ;; not on a continuation line
       ((bobp) (current-indentation))

       ;; Dfn: "Indenting comment line".  A line containing only a
       ;; comment, but which is treated like a statement for
       ;; indentation calculation purposes.  Such lines are only
       ;; treated specially by the mode; they are not treated
       ;; specially by the Alamatic interpreter.

       ;; The rules for indenting comment lines are a line where:
       ;;   - the first non-whitespace character is `#', and
       ;;   - the character following the `#' is whitespace, and
       ;;   - the line is dedented with respect to (i.e. to the left
       ;;     of) the indentation of the preceding non-blank line.

       ;; The first non-blank line following an indenting comment
       ;; line is given the same amount of indentation as the
       ;; indenting comment line.

       ;; All other comment-only lines are ignored for indentation
       ;; purposes.

       ;; Are we looking at a comment-only line which is *not* an
       ;; indenting comment line?  If so, we assume that it's been
       ;; placed at the desired indentation, so leave it alone.
       ;; Indenting comment lines are aligned as statements down
       ;; below.
       ((and (looking-at "[ \t]*#[^ \t\n]")
             ;; NOTE: this test will not be performed in older Emacsen
             (fboundp 'forward-comment)
             (<= (current-indentation)
                 (save-excursion
                   (forward-comment (- (point-max)))
                   (current-indentation))))
        (current-indentation))

       ;; else indentation based on that of the statement that
       ;; precedes us; use the first line of that statement to
       ;; establish the base, in case the user forced a non-std
       ;; indentation for the continuation lines (if any)
       (t
        ;; skip back over blank & non-indenting comment lines note:
        ;; will skip a blank or non-indenting comment line that
        ;; happens to be a continuation line too.  use fast Emacs 19
        ;; function if it's there.
        (if (and (eq ala-honor-comment-indentation nil)
                 (fboundp 'forward-comment))
            (forward-comment (- (point-max)))
          (let ((prefix-re (concat ala-block-comment-prefix "[ \t]*"))
                done)
            (while (not done)
              (re-search-backward "^[ \t]*\\([^ \t\n#]\\|#\\)" nil 'move)
              (setq done (or (bobp)
                             (and (eq ala-honor-comment-indentation t)
                                  (save-excursion
                                    (back-to-indentation)
                                    (not (looking-at prefix-re))
                                    ))
                             (and (not (eq ala-honor-comment-indentation t))
                                  (save-excursion
                                    (back-to-indentation)
                                    (and (not (looking-at prefix-re))
                                         (or (looking-at "[^#]")
                                             (not (zerop (current-column)))
                                             ))
                                    ))
                             ))
              )))
        ;; if we landed inside a string, go to the beginning of that
        ;; string. this handles triple quoted, multi-line spanning
        ;; strings.
        (ala-goto-beginning-of-tqs (nth 3 (parse-partial-sexp bod (point))))
        ;; now skip backward over continued lines
        (setq placeholder (point))
        (ala-goto-initial-line)
        ;; we may *now* have landed in a TQS, so find the beginning of
        ;; this string.
        (ala-goto-beginning-of-tqs
         (save-excursion (nth 3 (parse-partial-sexp
                                 placeholder (point)))))
        (+ (current-indentation)
           (if (ala-statement-opens-block-p)
               ala-indent-offset
             (if (and honor-block-close-p (ala-statement-closes-block-p))
                 (- ala-indent-offset)
               0)))
        )))))

(defun ala-guess-indent-offset (&optional global)
  "Guess a good value for, and change, `ala-indent-offset'.

By default, make a buffer-local copy of `ala-indent-offset' with the
new value, so that other Alamatic buffers are not affected.  With
\\[universal-argument] (programmatically, optional argument GLOBAL),
change the global value of `ala-indent-offset'.  This affects all
Alamatic buffers (that don't have their own buffer-local copy), both
those currently existing and those created later in the Emacs session.

Some people use a different value for `ala-indent-offset' than you use.
There's no excuse for such foolishness, but sometimes you have to deal
with their ugly code anyway.  This function examines the file and sets
`ala-indent-offset' to what it thinks it was when they created the
mess.

Specifically, it searches forward from the statement containing point,
looking for a line that opens a block of code.  `ala-indent-offset' is
set to the difference in indentation between that line and the Alamatic
statement following it.  If the search doesn't succeed going forward,
it's tried again going backward."
  (interactive "P")                     ; raw prefix arg
  (let (new-value
        (start (point))
        (restart (point))
        (found nil)
        colon-indent)
    (ala-goto-initial-line)
    (while (not (or found (eobp)))
      (when (and (re-search-forward ":[ \t]*\\($\\|[#\\]\\)" nil 'move)
                 (not (ala-in-literal restart)))
        (setq restart (point))
        (ala-goto-initial-line)
        (if (ala-statement-opens-block-p)
            (setq found t)
          (goto-char restart))))
    (unless found
      (goto-char start)
      (ala-goto-initial-line)
      (while (not (or found (bobp)))
        (setq found (and
                     (re-search-backward ":[ \t]*\\($\\|[#\\]\\)" nil 'move)
                     (or (ala-goto-initial-line) t) ; always true -- side effect
                     (ala-statement-opens-block-p)))))
    (setq colon-indent (current-indentation)
          found (and found (zerop (ala-next-statement 1)))
          new-value (- (current-indentation) colon-indent))
    (goto-char start)
    (if (not found)
        (error "Sorry, couldn't guess a value for ala-indent-offset")
      (funcall (if global 'kill-local-variable 'make-local-variable)
               'ala-indent-offset)
      (setq ala-indent-offset new-value)
      (or noninteractive
          (message "%s value of ala-indent-offset set to %d"
                   (if global "Global" "Local")
                   ala-indent-offset)))
    ))

(defun ala-comment-indent-function ()
  "Alamatic version of `comment-indent-function'."
  ;; This is required when filladapt is turned off.  Without it, when
  ;; filladapt is not used, comments which start in column zero
  ;; cascade one character to the right
  (save-excursion
    (beginning-of-line)
    (let ((eol (ala-point 'eol)))
      (and comment-start-skip
           (re-search-forward comment-start-skip eol t)
           (setq eol (match-beginning 0)))
      (goto-char eol)
      (skip-chars-backward " \t")
      (max comment-column (+ (current-column) (if (bolp) 0 1)))
      )))

(defun ala-narrow-to-defun (&optional class)
  "Make text outside current defun invisible.
The defun visible is the one that contains point or follows point.
Optional CLASS is passed directly to `ala-beginning-of-def-or-class'."
  (interactive "P")
  (save-excursion
    (widen)
    (ala-end-of-def-or-class class)
    (let ((end (point)))
      (ala-beginning-of-def-or-class class)
      (narrow-to-region (point) end))))


(defun ala-shift-region (start end count)
  "Indent lines from START to END by COUNT spaces."
  (save-excursion
    (goto-char end)
    (beginning-of-line)
    (setq end (point))
    (goto-char start)
    (beginning-of-line)
    (setq start (point))
    (indent-rigidly start end count)))

(defun ala-shift-region-left (start end &optional count)
  "Shift region of Alamatic code to the left.
The lines from the line containing the start of the current region up
to (but not including) the line containing the end of the region are
shifted to the left, by `ala-indent-offset' columns.

If a prefix argument is given, the region is instead shifted by that
many columns.  With no active region, dedent only the current line.
You cannot dedent the region if any line is already at column zero."
  (interactive
   (let ((p (point))
         (m (mark))
         (arg current-prefix-arg))
     (if m
         (list (min p m) (max p m) arg)
       (list p (save-excursion (forward-line 1) (point)) arg))))
  ;; if any line is at column zero, don't shift the region
  (save-excursion
    (goto-char start)
    (while (< (point) end)
      (back-to-indentation)
      (if (and (zerop (current-column))
               (not (looking-at "\\s *$")))
          (error "Region is at left edge"))
      (forward-line 1)))
  (ala-shift-region start end (- (prefix-numeric-value
                                 (or count ala-indent-offset))))
  (ala-keep-region-active))

(defun ala-shift-region-right (start end &optional count)
  "Shift region of Alamatic code to the right.
The lines from the line containing the start of the current region up
to (but not including) the line containing the end of the region are
shifted to the right, by `ala-indent-offset' columns.

If a prefix argument is given, the region is instead shifted by that
many columns.  With no active region, indent only the current line."
  (interactive
   (let ((p (point))
         (m (mark))
         (arg current-prefix-arg))
     (if m
         (list (min p m) (max p m) arg)
       (list p (save-excursion (forward-line 1) (point)) arg))))
  (ala-shift-region start end (prefix-numeric-value
                              (or count ala-indent-offset)))
  (ala-keep-region-active))

(defun ala-indent-region (start end &optional indent-offset)
  "Reindent a region of Alamatic code.

The lines from the line containing the start of the current region up
to (but not including) the line containing the end of the region are
reindented.  If the first line of the region has a non-whitespace
character in the first column, the first line is left alone and the
rest of the region is reindented with respect to it.  Else the entire
region is reindented with respect to the (closest code or indenting
comment) statement immediately preceding the region.

This is useful when code blocks are moved or yanked, when enclosing
control structures are introduced or removed, or to reformat code
using a new value for the indentation offset.

If a numeric prefix argument is given, it will be used as the value of
the indentation offset.  Else the value of `ala-indent-offset' will be
used.

Warning: The region must be consistently indented before this function
is called!  This function does not compute proper indentation from
scratch (that's impossible in Alamatic), it merely adjusts the existing
indentation to be correct in context.

Warning: This function really has no idea what to do with
non-indenting comment lines, and shifts them as if they were indenting
comment lines.  Fixing this appears to require telepathy.

Special cases: whitespace is deleted from blank lines; continuation
lines are shifted by the same amount their initial line was shifted,
in order to preserve their relative indentation with respect to their
initial line; and comment lines beginning in column 1 are ignored."
  (interactive "*r\nP")                 ; region; raw prefix arg
  (save-excursion
    (goto-char end)   (beginning-of-line) (setq end (point-marker))
    (goto-char start) (beginning-of-line)
    (let ((ala-indent-offset (prefix-numeric-value
                             (or indent-offset ala-indent-offset)))
          (indents '(-1))               ; stack of active indent levels
          (target-column 0)             ; column to which to indent
          (base-shifted-by 0)           ; amount last base line was shifted
          (indent-base (if (looking-at "[ \t\n]")
                           (ala-compute-indentation t)
                         0))
          ci)
      (while (< (point) end)
        (setq ci (current-indentation))
        ;; figure out appropriate target column
        (cond
         ((or (eq (following-char) ?#)  ; comment in column 1
              (looking-at "[ \t]*$"))   ; entirely blank
          (setq target-column 0))
         ((ala-continuation-line-p)      ; shift relative to base line
          (setq target-column (+ ci base-shifted-by)))
         (t                             ; new base line
          (if (> ci (car indents))      ; going deeper; push it
              (setq indents (cons ci indents))
            ;; else we should have seen this indent before
            (setq indents (memq ci indents)) ; pop deeper indents
            (if (null indents)
                (error "Bad indentation in region, at line %d"
                       (save-restriction
                         (widen)
                         (1+ (count-lines 1 (point)))))))
          (setq target-column (+ indent-base
                                 (* ala-indent-offset
                                    (- (length indents) 2))))
          (setq base-shifted-by (- target-column ci))))
        ;; shift as needed
        (if (/= ci target-column)
            (progn
              (delete-horizontal-space)
              (indent-to target-column)))
        (forward-line 1))))
  (set-marker end nil))

(defun ala-comment-region (beg end &optional arg)
  "Like `comment-region' but uses double hash (`#') comment starter."
  (interactive "r\nP")
  (let ((comment-start ala-block-comment-prefix))
    (comment-region beg end arg)))

(defun ala-join-words-wrapping (words separator line-prefix line-length)
  (let ((lines ())
        (current-line line-prefix))
    (while words
      (let* ((word (car words))
             (maybe-line (concat current-line word separator)))
        (if (> (length maybe-line) line-length)
            (setq lines (cons (substring current-line 0 -1) lines)
                  current-line (concat line-prefix word separator " "))
          (setq current-line (concat maybe-line " "))))
      (setq words (cdr words)))
    (setq lines (cons (substring
                       current-line 0 (- 0 (length separator) 1)) lines))
    (mapconcat 'identity (nreverse lines) "\n")))

(defun ala-sort-imports ()
  "Sort multiline imports.
Put point inside the parentheses of a multiline import and hit
\\[ala-sort-imports] to sort the imports lexicographically"
  (interactive)
  (save-excursion
    (let ((open-paren (save-excursion (progn (up-list -1) (point))))
          (close-paren (save-excursion (progn (up-list 1) (point))))
          sorted-imports)
      (goto-char (1+ open-paren))
      (skip-chars-forward " \n\t")
      (setq sorted-imports
            (sort
             (delete-dups
              (split-string (buffer-substring
                             (point)
                             (save-excursion (goto-char (1- close-paren))
                                             (skip-chars-backward " \n\t")
                                             (point)))
                            ", *\\(\n *\\)?"))
             ;; XXX Should this sort case insensitively?
             'string-lessp))
      ;; Remove empty strings.
      (delete-region open-paren close-paren)
      (goto-char open-paren)
      (insert "(\n")
      (insert (ala-join-words-wrapping (remove "" sorted-imports) "," "    " 78))
      (insert ")")
      )))



;; Functions for moving point
(defun ala-previous-statement (count)
  "Go to the start of the COUNTth preceding Alamatic statement.
By default, goes to the previous statement.  If there is no such
statement, goes to the first statement.  Return count of statements
left to move.  `Statements' do not include blank, comment, or
continuation lines."
  (interactive "p")                     ; numeric prefix arg
  (if (< count 0) (ala-next-statement (- count))
    (ala-goto-initial-line)
    (let (start)
      (while (and
              (setq start (point))      ; always true -- side effect
              (> count 0)
              (zerop (forward-line -1))
              (ala-goto-statement-at-or-above))
        (setq count (1- count)))
      (if (> count 0) (goto-char start)))
    count))

(defun ala-next-statement (count)
  "Go to the start of next Alamatic statement.
If the statement at point is the i'th Alamatic statement, goes to the
start of statement i+COUNT.  If there is no such statement, goes to the
last statement.  Returns count of statements left to move.  `Statements'
do not include blank, comment, or continuation lines."
  (interactive "p")                     ; numeric prefix arg
  (if (< count 0) (ala-previous-statement (- count))
    (beginning-of-line)
    (let (start)
      (while (and
              (setq start (point))      ; always true -- side effect
              (> count 0)
              (ala-goto-statement-below))
        (setq count (1- count)))
      (if (> count 0) (goto-char start)))
    count))

(defun ala-goto-block-up (&optional nomark)
  "Move up to start of current block.
Go to the statement that starts the smallest enclosing block; roughly
speaking, this will be the closest preceding statement that ends with a
colon and is indented less than the statement you started on.  If
successful, also sets the mark to the starting point.

`\\[ala-mark-block]' can be used afterward to mark the whole code
block, if desired.

If called from a program, the mark will not be set if optional argument
NOMARK is not nil."
  (interactive)
  (let ((start (point))
        (found nil)
        initial-indent)
    (ala-goto-initial-line)
    ;; if on blank or non-indenting comment line, use the preceding stmt
    (if (looking-at "[ \t]*\\($\\|#[^ \t\n]\\)")
        (progn
          (ala-goto-statement-at-or-above)
          (setq found (ala-statement-opens-block-p))))
    ;; search back for colon line indented less
    (setq initial-indent (current-indentation))
    (if (zerop initial-indent)
        ;; force fast exit
        (goto-char (point-min)))
    (while (not (or found (bobp)))
      (setq found
            (and
             (re-search-backward ":[ \t]*\\($\\|[#\\]\\)" nil 'move)
             (or (ala-goto-initial-line) t) ; always true -- side effect
             (< (current-indentation) initial-indent)
             (ala-statement-opens-block-p))))
    (if found
        (progn
          (or nomark (push-mark start))
          (back-to-indentation))
      (goto-char start)
      (error "Enclosing block not found"))))

(defun ala-beginning-of-def-or-class (&optional class count)
  "Move point to start of `def' or `class'.

Searches back for the closest preceding `def'.  If you supply a prefix
arg, looks for a `class' instead.  The docs below assume the `def'
case; just substitute `class' for `def' for the other case.
Programmatically, if CLASS is `either', then moves to either `class'
or `def'.

When second optional argument is given programmatically, move to the
COUNTth start of `def'.

If point is in a `def' statement already, and after the `d', simply
moves point to the start of the statement.

Otherwise (i.e. when point is not in a `def' statement, or at or
before the `d' of a `def' statement), searches for the closest
preceding `def' statement, and leaves point at its start.  If no such
statement can be found, leaves point at the start of the buffer.

Returns t iff a `def' statement is found by these rules.

Note that doing this command repeatedly will take you closer to the
start of the buffer each time.

To mark the current `def', see `\\[ala-mark-def-or-class]'."
  (interactive "P")                     ; raw prefix arg
  (setq count (or count 1))
  (let ((at-or-before-p (<= (current-column) (current-indentation)))
        (start-of-line (goto-char (ala-point 'bol)))
        (start-of-stmt (goto-char (ala-point 'bos)))
        (start-re (cond ((eq class 'either) "^[ \t]*\\(class\\|def\\)\\>")
                        (class "^[ \t]*class\\>")
                        (t "^[ \t]*def\\>")))
        )
    ;; searching backward
    (if (and (< 0 count)
             (or (/= start-of-stmt start-of-line)
                 (not at-or-before-p)))
        (end-of-line))
    ;; search forward
    (if (and (> 0 count)
             (zerop (current-column))
             (looking-at start-re))
        (end-of-line))
    (if (re-search-backward start-re nil 'move count)
        (goto-char (match-beginning 0)))))

;; Backwards compatibility
(defalias 'beginning-of-alamatic-def-or-class 'ala-beginning-of-def-or-class)

(defun ala-end-of-def-or-class (&optional class count)
  "Move point beyond end of `def' or `class' body.

By default, looks for an appropriate `def'.  If you supply a prefix
arg, looks for a `class' instead.  The docs below assume the `def'
case; just substitute `class' for `def' for the other case.
Programmatically, if CLASS is `either', then moves to either `class'
or `def'.

When second optional argument is given programmatically, move to the
COUNTth end of `def'.

If point is in a `def' statement already, this is the `def' we use.

Else, if the `def' found by `\\[ala-beginning-of-def-or-class]'
contains the statement you started on, that's the `def' we use.

Otherwise, we search forward for the closest following `def', and use that.

If a `def' can be found by these rules, point is moved to the start of
the line immediately following the `def' block, and the position of the
start of the `def' is returned.

Else point is moved to the end of the buffer, and nil is returned.

Note that doing this command repeatedly will take you closer to the
end of the buffer each time.

To mark the current `def', see `\\[ala-mark-def-or-class]'."
  (interactive "P")                     ; raw prefix arg
  (if (and count (/= count 1))
      (ala-beginning-of-def-or-class (- 1 count)))
  (let ((start (progn (ala-goto-initial-line) (point)))
        (which (cond ((eq class 'either) "\\(class\\|def\\)")
                     (class "class")
                     (t "def")))
        (state 'not-found))
    ;; move point to start of appropriate def/class
    (if (looking-at (concat "[ \t]*" which "\\>")) ; already on one
        (setq state 'at-beginning)
      ;; else see if ala-beginning-of-def-or-class hits container
      (if (and (ala-beginning-of-def-or-class class)
               (progn (ala-goto-beyond-block)
                      (> (point) start)))
          (setq state 'at-end)
        ;; else search forward
        (goto-char start)
        (if (re-search-forward (concat "^[ \t]*" which "\\>") nil 'move)
            (progn (setq state 'at-beginning)
                   (beginning-of-line)))))
    (cond
     ((eq state 'at-beginning) (ala-goto-beyond-block) t)
     ((eq state 'at-end) t)
     ((eq state 'not-found) nil)
     (t (error "Internal error in `ala-end-of-def-or-class'")))))

;; Backwards compabitility
(defalias 'end-of-alamatic-def-or-class 'ala-end-of-def-or-class)


;; Functions for marking regions
(defun ala-mark-block (&optional extend just-move)
  "Mark following block of lines.  With prefix arg, mark structure.
Easier to use than explain.  It sets the region to an `interesting'
block of succeeding lines.  If point is on a blank line, it goes down to
the next non-blank line.  That will be the start of the region.  The end
of the region depends on the kind of line at the start:

 - If a comment, the region will include all succeeding comment lines up
   to (but not including) the next non-comment line (if any).

 - Else if a prefix arg is given, and the line begins one of these
   structures:

     if elif else try except finally for while def class

   the region will be set to the body of the structure, including
   following blocks that `belong' to it, but excluding trailing blank
   and comment lines.  E.g., if on a `try' statement, the `try' block
   and all (if any) of the following `except' and `finally' blocks
   that belong to the `try' structure will be in the region.  Ditto
   for if/elif/else, for/else and while/else structures, and (a bit
   degenerate, since they're always one-block structures) def and
   class blocks.

 - Else if no prefix argument is given, and the line begins a Alamatic
   block (see list above), and the block is not a `one-liner' (i.e.,
   the statement ends with a colon, not with code), the region will
   include all succeeding lines up to (but not including) the next
   code statement (if any) that's indented no more than the starting
   line, except that trailing blank and comment lines are excluded.
   E.g., if the starting line begins a multi-statement `def'
   structure, the region will be set to the full function definition,
   but without any trailing `noise' lines.

 - Else the region will include all succeeding lines up to (but not
   including) the next blank line, or code or indenting-comment line
   indented strictly less than the starting line.  Trailing indenting
   comment lines are included in this case, but not trailing blank
   lines.

A msg identifying the location of the mark is displayed in the echo
area; or do `\\[exchange-point-and-mark]' to flip down to the end.

If called from a program, optional argument EXTEND plays the role of
the prefix arg, and if optional argument JUST-MOVE is not nil, just
moves to the end of the block (& does not set mark or display a msg)."
  (interactive "P")                     ; raw prefix arg
  (ala-goto-initial-line)
  ;; skip over blank lines
  (while (and
          (looking-at "[ \t]*$")        ; while blank line
          (not (eobp)))                 ; & somewhere to go
    (forward-line 1))
  (if (eobp)
      (error "Hit end of buffer without finding a non-blank stmt"))
  (let ((initial-pos (point))
        (initial-indent (current-indentation))
        last-pos                        ; position of last stmt in region
        (followers
         '((if elif else) (elif elif else) (else)
           (try except finally) (except except) (finally)
           (for else) (while else)
           (def) (class) ) )
        first-symbol next-symbol)

    (cond
     ;; if comment line, suck up the following comment lines
     ((looking-at "[ \t]*#")
      (re-search-forward "^[ \t]*[^ \t#]" nil 'move) ; look for non-comment
      (re-search-backward "^[ \t]*#")   ; and back to last comment in block
      (setq last-pos (point)))

     ;; else if line is a block line and EXTEND given, suck up
     ;; the whole structure
     ((and extend
           (setq first-symbol (ala-suck-up-first-keyword) )
           (assq first-symbol followers))
      (while (and
              (or (ala-goto-beyond-block) t) ; side effect
              (forward-line -1)         ; side effect
              (setq last-pos (point))   ; side effect
              (ala-goto-statement-below)
              (= (current-indentation) initial-indent)
              (setq next-symbol (ala-suck-up-first-keyword))
              (memq next-symbol (cdr (assq first-symbol followers))))
        (setq first-symbol next-symbol)))

     ;; else if line *opens* a block, search for next stmt indented <=
     ((ala-statement-opens-block-p)
      (while (and
              (setq last-pos (point))   ; always true -- side effect
              (ala-goto-statement-below)
              (> (current-indentation) initial-indent)
              )))

     ;; else plain code line; stop at next blank line, or stmt or
     ;; indenting comment line indented <
     (t
      (while (and
              (setq last-pos (point))   ; always true -- side effect
              (or (ala-goto-beyond-final-line) t)
              (not (looking-at "[ \t]*$")) ; stop at blank line
              (or
               (>= (current-indentation) initial-indent)
               (looking-at "[ \t]*#[^ \t\n]"))) ; ignore non-indenting #
        nil)))

    ;; skip to end of last stmt
    (goto-char last-pos)
    (ala-goto-beyond-final-line)

    ;; set mark & display
    (if just-move
        ()                              ; just return
      (push-mark (point) 'no-msg)
      (forward-line -1)
      (message "Mark set after: %s" (ala-suck-up-leading-text))
      (goto-char initial-pos))))

(defun ala-mark-def-or-class (&optional class)
  "Set region to body of def (or class, with prefix arg) enclosing point.
Pushes the current mark, then point, on the mark ring (all language
modes do this, but although it's handy it's never documented ...).

In most Emacs language modes, this function bears at least a
hallucinogenic resemblance to `\\[ala-end-of-def-or-class]' and
`\\[ala-beginning-of-def-or-class]'.

And in earlier versions of Alamatic mode, all 3 were tightly connected.
Turned out that was more confusing than useful: the `goto start' and
`goto end' commands are usually used to search through a file, and
people expect them to act a lot like `search backward' and `search
forward' string-search commands.  But because Alamatic `def' and `class'
can nest to arbitrary levels, finding the smallest def containing
point cannot be done via a simple backward search: the def containing
point may not be the closest preceding def, or even the closest
preceding def that's indented less.  The fancy algorithm required is
appropriate for the usual uses of this `mark' command, but not for the
`goto' variations.

So the def marked by this command may not be the one either of the
`goto' commands find: If point is on a blank or non-indenting comment
line, moves back to start of the closest preceding code statement or
indenting comment line.  If this is a `def' statement, that's the def
we use.  Else searches for the smallest enclosing `def' block and uses
that.  Else signals an error.

When an enclosing def is found: The mark is left immediately beyond
the last line of the def block.  Point is left at the start of the
def, except that: if the def is preceded by a number of comment lines
followed by (at most) one optional blank line, point is left at the
start of the comments; else if the def is preceded by a blank line,
point is left at its start.

The intent is to mark the containing def/class and its associated
documentation, to make moving and duplicating functions and classes
pleasant."
  (interactive "P")                     ; raw prefix arg
  (let ((start (point))
        (which (cond ((eq class 'either) "\\(class\\|def\\)")
                     (class "class")
                     (t "def"))))
    (push-mark start)
    (if (not (ala-go-up-tree-to-keyword which))
        (progn (goto-char start)
               (error "Enclosing %s not found"
                      (if (eq class 'either)
                          "def or class"
                        which)))
      ;; else enclosing def/class found
      (setq start (point))
      (ala-goto-beyond-block)
      (push-mark (point))
      (goto-char start)
      (if (zerop (forward-line -1))     ; if there is a preceding line
          (progn
            (if (looking-at "[ \t]*$")  ; it's blank
                (setq start (point))    ; so reset start point
              (goto-char start))        ; else try again
            (if (zerop (forward-line -1))
                (if (looking-at "[ \t]*#") ; a comment
                    ;; look back for non-comment line
                    ;; tricky: note that the regexp matches a blank
                    ;; line, cuz \n is in the 2nd character class
                    (and
                     (re-search-backward "^[ \t]*[^ \t#]" nil 'move)
                     (forward-line 1))
                  ;; no comment, so go back
                  (goto-char start)))))))
  (exchange-point-and-mark)
  (ala-keep-region-active))

;; ripped from cc-mode
(defun ala-forward-into-nomenclature (&optional arg)
  "Move forward to end of a nomenclature section or word.
With \\[universal-argument] (programmatically, optional argument ARG),
do it that many times.

A `nomenclature' is a fancy way of saying AWordWithMixedCaseNotUnderscores."
  (interactive "p")
  (let ((case-fold-search nil))
    (if (> arg 0)
        (re-search-forward
         "\\(\\W\\|[_]\\)*\\([A-Z]*[a-z0-9]*\\)"
         (point-max) t arg)
      (while (and (< arg 0)
                  (re-search-backward
                   "\\(\\W\\|[a-z0-9]\\)[A-Z]+\\|\\(\\W\\|[_]\\)\\w+"
                   (point-min) 0))
        (forward-char 1)
        (setq arg (1+ arg)))))
  (ala-keep-region-active))

(defun ala-backward-into-nomenclature (&optional arg)
  "Move backward to beginning of a nomenclature section or word.
With optional ARG, move that many times.  If ARG is negative, move
forward.

A `nomenclature' is a fancy way of saying AWordWithMixedCaseNotUnderscores."
  (interactive "p")
  (ala-forward-into-nomenclature (- arg))
  (ala-keep-region-active))



;; pdbtrack functions
(defun ala-pdbtrack-toggle-stack-tracking (arg)
  (interactive "P")
  (if (not (get-buffer-process (current-buffer)))
      (error "No process associated with buffer '%s'" (current-buffer)))
  ;; missing or 0 is toggle, >0 turn on, <0 turn off
  (if (or (not arg)
          (zerop (setq arg (prefix-numeric-value arg))))
      (setq ala-pdbtrack-do-tracking-p (not ala-pdbtrack-do-tracking-p))
    (setq ala-pdbtrack-do-tracking-p (> arg 0)))
  (message "%sabled Alamatic's pdbtrack"
           (if ala-pdbtrack-do-tracking-p "En" "Dis")))

(defun turn-on-pdbtrack ()
  (interactive)
  (ala-pdbtrack-toggle-stack-tracking 1))

(defun turn-off-pdbtrack ()
  (interactive)
  (ala-pdbtrack-toggle-stack-tracking 0))



;; Pychecker

;; hack for FSF Emacs
(unless (fboundp 'read-shell-command)
  (defalias 'read-shell-command 'read-string))

(defun ala-pychecker-run (command)
  "*Run pychecker (default on the file currently visited)."
  (interactive
   (let ((default
           (format "%s %s %s" ala-pychecker-command
                   (mapconcat 'identity ala-pychecker-command-args " ")
                   (buffer-file-name)))
         (last (when ala-pychecker-history
                 (let* ((lastcmd (car ala-pychecker-history))
                        (cmd (cdr (reverse (split-string lastcmd))))
                        (newcmd (reverse (cons (buffer-file-name) cmd))))
                   (mapconcat 'identity newcmd " ")))))

     (list
      (if (fboundp 'read-shell-command)
          (read-shell-command "Run pychecker like this: "
                              (if last
                                  last
                                default)
                              'ala-pychecker-history)
        (read-string "Run pychecker like this: "
                     (if last
                         last
                       default)
                     'ala-pychecker-history))
        )))
  (save-some-buffers (not ala-ask-about-save) nil)
  (if (fboundp 'compilation-start)
      ;; Emacs.
      (compilation-start command)
    ;; XEmacs.
    (compile-internal command "No more errors")))



;; pydoc commands. The guts of this function is stolen from XEmacs's
;; symbol-near-point, but without the useless regexp-quote call on the
;; results, nor the interactive bit.  Also, we've added the temporary
;; syntax table setting, which Skip originally had broken out into a
;; separate function.  Note that Emacs doesn't have the original
;; function.
(defun ala-symbol-near-point ()
  "Return the first textual item to the nearest point."
  ;; alg stolen from etag.el
  (save-excursion
    (with-syntax-table ala-dotted-expression-syntax-table
      (if (or (bobp) (not (memq (char-syntax (char-before)) '(?w ?_))))
          (while (not (looking-at "\\sw\\|\\s_\\|\\'"))
            (forward-char 1)))
      (while (looking-at "\\sw\\|\\s_")
        (forward-char 1))
      (if (re-search-backward "\\sw\\|\\s_" nil t)
          (progn (forward-char 1)
                 (buffer-substring (point)
                                   (progn (forward-sexp -1)
                                          (while (looking-at "\\s'")
                                            (forward-char 1))
                                          (point))))
        nil))))

(defun ala-help-at-point ()
  "Get help from Alamatic based on the symbol nearest point."
  (interactive)
  (let* ((sym (ala-symbol-near-point))
         (base (substring sym 0 (or (search "." sym :from-end t) 0)))
         cmd)
    (if (not (equal base ""))
        (setq cmd (concat "import " base "\n")))
    (setq cmd (concat "import pydoc\n"
                      cmd
                      "try: pydoc.help('" sym "')\n"
                      "except: print 'No help available on:', \"" sym "\""))
    (message cmd)
    (ala-execute-string cmd)
    (set-buffer "*Alamatic Output*")
    ;; BAW: Should we really be leaving the output buffer in help-mode?
    (help-mode)))



;; Documentation functions

;; dump the long form of the mode blurb; does the usual doc escapes,
;; plus lines of the form ^[vc]:name$ to suck variable & command docs
;; out of the right places, along with the keys they're on & current
;; values
(defun ala-dump-help-string (str)
  (with-output-to-temp-buffer "*Help*"
    (let ((locals (buffer-local-variables))
          funckind funcname func funcdoc
          (start 0) mstart end
          keys )
      (while (string-match "^%\\([vc]\\):\\(.+\\)\n" str start)
        (setq mstart (match-beginning 0)  end (match-end 0)
              funckind (substring str (match-beginning 1) (match-end 1))
              funcname (substring str (match-beginning 2) (match-end 2))
              func (intern funcname))
        (princ (substitute-command-keys (substring str start mstart)))
        (cond
         ((equal funckind "c")          ; command
          (setq funcdoc (documentation func)
                keys (concat
                      "Key(s): "
                      (mapconcat 'key-description
                                 (where-is-internal func ala-mode-map)
                                 ", "))))
         ((equal funckind "v")          ; variable
          (setq funcdoc (documentation-property func 'variable-documentation)
                keys (if (assq func locals)
                         (concat
                          "Local/Global values: "
                          (prin1-to-string (symbol-value func))
                          " / "
                          (prin1-to-string (default-value func)))
                       (concat
                        "Value: "
                        (prin1-to-string (symbol-value func))))))
         (t                             ; unexpected
          (error "Error in ala-dump-help-string, tag `%s'" funckind)))
        (princ (format "\n-> %s:\t%s\t%s\n\n"
                       (if (equal funckind "c") "Command" "Variable")
                       funcname keys))
        (princ funcdoc)
        (terpri)
        (setq start end))
      (princ (substitute-command-keys (substring str start))))
    (print-help-return-message)))

(defun ala-describe-mode ()
  "Dump long form of alamatic-mode docs."
  (interactive)
  (ala-dump-help-string "Major mode for editing Alamatic files.
Knows about Alamatic indentation, tokens, comments and continuation lines.
Paragraphs are separated by blank lines only.

Major sections below begin with the string `@'; specific function and
variable docs begin with `->'.

@EXECUTING ALAMATIC CODE

\\[ala-execute-import-or-reload]\timports or reloads the file in the Alamatic interpreter
\\[ala-execute-buffer]\tsends the entire buffer to the Alamatic interpreter
\\[ala-execute-region]\tsends the current region
\\[ala-execute-def-or-class]\tsends the current function or class definition
\\[ala-execute-string]\tsends an arbitrary string
\\[ala-shell]\tstarts a Alamatic interpreter window; this will be used by
\tsubsequent Alamatic execution commands
%c:ala-execute-import-or-reload
%c:ala-execute-buffer
%c:ala-execute-region
%c:ala-execute-def-or-class
%c:ala-execute-string
%c:ala-shell

@VARIABLES

ala-indent-offset\tindentation increment
ala-block-comment-prefix\tcomment string used by comment-region

ala-alamatic-command\tshell command to invoke Alamatic interpreter
ala-temp-directory\tdirectory used for temp files (if needed)

ala-beep-if-tab-change\tring the bell if tab-width is changed
%v:ala-indent-offset
%v:ala-block-comment-prefix
%v:ala-alamatic-command
%v:ala-temp-directory
%v:ala-beep-if-tab-change

@KINDS OF LINES

Each physical line in the file is either a `continuation line' (the
preceding line ends with a backslash that's not part of a comment, or
the paren/bracket/brace nesting level at the start of the line is
non-zero, or both) or an `initial line' (everything else).

An initial line is in turn a `blank line' (contains nothing except
possibly blanks or tabs), a `comment line' (leftmost non-blank
character is `#'), or a `code line' (everything else).

Comment Lines

Although all comment lines are treated alike by Alamatic, Alamatic mode
recognizes two kinds that act differently with respect to indentation.

An `indenting comment line' is a comment line with a blank, tab or
nothing after the initial `#'.  The indentation commands (see below)
treat these exactly as if they were code lines: a line following an
indenting comment line will be indented like the comment line.  All
other comment lines (those with a non-whitespace character immediately
following the initial `#') are `non-indenting comment lines', and
their indentation is ignored by the indentation commands.

Indenting comment lines are by far the usual case, and should be used
whenever possible.  Non-indenting comment lines are useful in cases
like these:

\ta = b   # a very wordy single-line comment that ends up being
\t        #... continued onto another line

\tif a == b:
##\t\tprint 'panic!' # old code we've `commented out'
\t\treturn a

Since the `#...' and `##' comment lines have a non-whitespace
character following the initial `#', Alamatic mode ignores them when
computing the proper indentation for the next line.

Continuation Lines and Statements

The alamatic-mode commands generally work on statements instead of on
individual lines, where a `statement' is a comment or blank line, or a
code line and all of its following continuation lines (if any)
considered as a single logical unit.  The commands in this mode
generally (when it makes sense) automatically move to the start of the
statement containing point, even if point happens to be in the middle
of some continuation line.


@INDENTATION

Primarily for entering new code:
\t\\[indent-for-tab-command]\t indent line appropriately
\t\\[ala-newline-and-indent]\t insert newline, then indent
\t\\[ala-electric-backspace]\t reduce indentation, or delete single character

Primarily for reindenting existing code:
\t\\[ala-guess-indent-offset]\t guess ala-indent-offset from file content; change locally
\t\\[universal-argument] \\[ala-guess-indent-offset]\t ditto, but change globally

\t\\[ala-indent-region]\t reindent region to match its context
\t\\[ala-shift-region-left]\t shift region left by ala-indent-offset
\t\\[ala-shift-region-right]\t shift region right by ala-indent-offset

Unlike most programming languages, Alamatic uses indentation, and only
indentation, to specify block structure.  Hence the indentation supplied
automatically by alamatic-mode is just an educated guess:  only you know
the block structure you intend, so only you can supply correct
indentation.

The \\[indent-for-tab-command] and \\[ala-newline-and-indent] keys try to suggest plausible indentation, based on
the indentation of preceding statements.  E.g., assuming
ala-indent-offset is 4, after you enter
\tif a > 0: \\[ala-newline-and-indent]
the cursor will be moved to the position of the `_' (_ is not a
character in the file, it's just used here to indicate the location of
the cursor):
\tif a > 0:
\t    _
If you then enter `c = d' \\[ala-newline-and-indent], the cursor will move
to
\tif a > 0:
\t    c = d
\t    _
alamatic-mode cannot know whether that's what you intended, or whether
\tif a > 0:
\t    c = d
\t_
was your intent.  In general, alamatic-mode either reproduces the
indentation of the (closest code or indenting-comment) preceding
statement, or adds an extra ala-indent-offset blanks if the preceding
statement has `:' as its last significant (non-whitespace and non-
comment) character.  If the suggested indentation is too much, use
\\[ala-electric-backspace] to reduce it.

Continuation lines are given extra indentation.  If you don't like the
suggested indentation, change it to something you do like, and Alamatic-
mode will strive to indent later lines of the statement in the same way.

If a line is a continuation line by virtue of being in an unclosed
paren/bracket/brace structure (`list', for short), the suggested
indentation depends on whether the current line contains the first item
in the list.  If it does, it's indented ala-indent-offset columns beyond
the indentation of the line containing the open bracket.  If you don't
like that, change it by hand.  The remaining items in the list will mimic
whatever indentation you give to the first item.

If a line is a continuation line because the line preceding it ends with
a backslash, the third and following lines of the statement inherit their
indentation from the line preceding them.  The indentation of the second
line in the statement depends on the form of the first (base) line:  if
the base line is an assignment statement with anything more interesting
than the backslash following the leftmost assigning `=', the second line
is indented two columns beyond that `='.  Else it's indented to two
columns beyond the leftmost solid chunk of non-whitespace characters on
the base line.

Warning:  indent-region should not normally be used!  It calls \\[indent-for-tab-command]
repeatedly, and as explained above, \\[indent-for-tab-command] can't guess the block
structure you intend.
%c:indent-for-tab-command
%c:ala-newline-and-indent
%c:ala-electric-backspace


The next function may be handy when editing code you didn't write:
%c:ala-guess-indent-offset


The remaining `indent' functions apply to a region of Alamatic code.  They
assume the block structure (equals indentation, in Alamatic) of the region
is correct, and alter the indentation in various ways while preserving
the block structure:
%c:ala-indent-region
%c:ala-shift-region-left
%c:ala-shift-region-right

@MARKING & MANIPULATING REGIONS OF CODE

\\[ala-mark-block]\t mark block of lines
\\[ala-mark-def-or-class]\t mark smallest enclosing def
\\[universal-argument] \\[ala-mark-def-or-class]\t mark smallest enclosing class
\\[comment-region]\t comment out region of code
\\[universal-argument] \\[comment-region]\t uncomment region of code
%c:ala-mark-block
%c:ala-mark-def-or-class
%c:comment-region

@MOVING POINT

\\[ala-previous-statement]\t move to statement preceding point
\\[ala-next-statement]\t move to statement following point
\\[ala-goto-block-up]\t move up to start of current block
\\[ala-beginning-of-def-or-class]\t move to start of def
\\[universal-argument] \\[ala-beginning-of-def-or-class]\t move to start of class
\\[ala-end-of-def-or-class]\t move to end of def
\\[universal-argument] \\[ala-end-of-def-or-class]\t move to end of class

The first two move to one statement beyond the statement that contains
point.  A numeric prefix argument tells them to move that many
statements instead.  Blank lines, comment lines, and continuation lines
do not count as `statements' for these commands.  So, e.g., you can go
to the first code statement in a file by entering
\t\\[beginning-of-buffer]\t to move to the top of the file
\t\\[ala-next-statement]\t to skip over initial comments and blank lines
Or do `\\[ala-previous-statement]' with a huge prefix argument.
%c:ala-previous-statement
%c:ala-next-statement
%c:ala-goto-block-up
%c:ala-beginning-of-def-or-class
%c:ala-end-of-def-or-class

@LITTLE-KNOWN EMACS COMMANDS PARTICULARLY USEFUL IN ALAMATIC MODE

`\\[indent-new-comment-line]' is handy for entering a multi-line comment.

`\\[set-selective-display]' with a `small' prefix arg is ideally suited for viewing the
overall class and def structure of a module.

`\\[back-to-indentation]' moves point to a line's first non-blank character.

`\\[indent-relative]' is handy for creating odd indentation.

@OTHER EMACS HINTS

If you don't like the default value of a variable, change its value to
whatever you do like by putting a `setq' line in your .emacs file.
E.g., to set the indentation increment to 4, put this line in your
.emacs:
\t(setq  ala-indent-offset  4)
To see the value of a variable, do `\\[describe-variable]' and enter the variable
name at the prompt.

When entering a key sequence like `C-c C-n', it is not necessary to
release the CONTROL key after doing the `C-c' part -- it suffices to
press the CONTROL key, press and release `c' (while still holding down
CONTROL), press and release `n' (while still holding down CONTROL), &
then release CONTROL.

Entering Alamatic mode calls with no arguments the value of the variable
`alamatic-mode-hook', if that value exists and is not nil; for backward
compatibility it also tries `ala-mode-hook'; see the `Hooks' section of
the Elisp manual for details.

Obscure:  When alamatic-mode is first loaded, it looks for all bindings
to newline-and-indent in the global keymap, and shadows them with
local bindings to ala-newline-and-indent."))

(require 'info-look)
;; The info-look package does not always provide this function (it
;; appears this is the case with XEmacs 21.1)
(when (fboundp 'info-lookup-maybe-add-help)
  (info-lookup-maybe-add-help
   :mode 'alamatic-mode
   :regexp "[a-zA-Z0-9_]+"
   :doc-spec '(("(alamatic-lib)Module Index")
               ("(alamatic-lib)Class-Exception-Object Index")
               ("(alamatic-lib)Function-Method-Variable Index")
               ("(alamatic-lib)Miscellaneous Index")))
  )


;; Helper functions
(defvar ala-parse-state-re
  (concat
   "^[ \t]*\\(elif\\|else\\|while\\|def\\|class\\)\\>"
   "\\|"
   "^[^ #\t\n]"))

(defun ala-parse-state ()
  "Return the parse state at point (see `parse-partial-sexp' docs)."
  (save-excursion
    (let ((here (point))
          pps done)
      (while (not done)
        ;; back up to the first preceding line (if any; else start of
        ;; buffer) that begins with a popular Alamatic keyword, or a
        ;; non- whitespace and non-comment character.  These are good
        ;; places to start parsing to see whether where we started is
        ;; at a non-zero nesting level.  It may be slow for people who
        ;; write huge code blocks or huge lists ... tough beans.
        (re-search-backward ala-parse-state-re nil 'move)
        (beginning-of-line)
        ;; In XEmacs, we have a much better way to test for whether
        ;; we're in a triple-quoted string or not.  Emacs does not
        ;; have this built-in function, which is its loss because
        ;; without scanning from the beginning of the buffer, there's
        ;; no accurate way to determine this otherwise.
        (save-excursion (setq pps (parse-partial-sexp (point) here)))
        ;; make sure we don't land inside a triple-quoted string
        (setq done (or (not (nth 3 pps))
                       (bobp)))
        ;; Just go ahead and short circuit the test back to the
        ;; beginning of the buffer.  This will be slow, but not
        ;; nearly as slow as looping through many
        ;; re-search-backwards.
        (if (not done)
            (goto-char (point-min))))
      pps)))

(defun ala-nesting-level ()
  "Return the buffer position of the last unclosed enclosing list.
If nesting level is zero, return nil."
  (let ((status (ala-parse-state)))
    (if (zerop (car status))
        nil                             ; not in a nest
      (car (cdr status)))))             ; char# of open bracket

(defun ala-backslash-continuation-line-p ()
  "Return t iff preceding line ends with backslash that is not in a comment."
  (save-excursion
    (beginning-of-line)
    (and
     ;; use a cheap test first to avoid the regexp if possible
     ;; use 'eq' because char-after may return nil
     (eq (char-after (- (point) 2)) ?\\ )
     ;; make sure; since eq test passed, there is a preceding line
     (forward-line -1)                  ; always true -- side effect
     (looking-at ala-continued-re))))

(defun ala-continuation-line-p ()
  "Return t iff current line is a continuation line."
  (save-excursion
    (beginning-of-line)
    (or (ala-backslash-continuation-line-p)
        (ala-nesting-level))))

(defun ala-goto-beginning-of-tqs (delim)
  "Go to the beginning of the triple quoted string we find ourselves in.
DELIM is the TQS string delimiter character we're searching backwards
for."
  (let ((skip (and delim (make-string 1 delim)))
        (continue t))
    (when skip
      (save-excursion
        (while continue
          (ala-safe (search-backward skip))
          (setq continue (and (not (bobp))
                              (= (char-before) ?\\))))
        (if (and (= (char-before) delim)
                 (= (char-before (1- (point))) delim))
            (setq skip (make-string 3 delim))))
      ;; we're looking at a triple-quoted string
      (ala-safe (search-backward skip)))))

(defun ala-goto-initial-line ()
  "Go to the initial line of the current statement.
Usually this is the line we're on, but if we're on the 2nd or
following lines of a continuation block, we need to go up to the first
line of the block."
  ;; Tricky: We want to avoid quadratic-time behavior for long
  ;; continued blocks, whether of the backslash or open-bracket
  ;; varieties, or a mix of the two.  The following manages to do that
  ;; in the usual cases.
  ;;
  ;; Also, if we're sitting inside a triple quoted string, this will
  ;; drop us at the line that begins the string.
  (let (open-bracket-pos)
    (while (ala-continuation-line-p)
      (beginning-of-line)
      (if (ala-backslash-continuation-line-p)
          (while (ala-backslash-continuation-line-p)
            (forward-line -1))
        ;; else zip out of nested brackets/braces/parens
        (while (setq open-bracket-pos (ala-nesting-level))
          (goto-char open-bracket-pos)))))
  (beginning-of-line))

(defun ala-goto-beyond-final-line ()
  "Go to the point just beyond the fine line of the current statement.
Usually this is the start of the next line, but if this is a
multi-line statement we need to skip over the continuation lines."
  ;; Tricky: Again we need to be clever to avoid quadratic time
  ;; behavior.
  ;;
  ;; XXX: Not quite the right solution, but deals with multi-line doc
  ;; strings
  (if (looking-at (concat "[ \t]*\\(" ala-stringlit-re "\\)"))
      (goto-char (match-end 0)))
  ;;
  (forward-line 1)
  (let (state)
    (while (and (ala-continuation-line-p)
                (not (eobp)))
      ;; skip over the backslash flavor
      (while (and (ala-backslash-continuation-line-p)
                  (not (eobp)))
        (forward-line 1))
      ;; if in nest, zip to the end of the nest
      (setq state (ala-parse-state))
      (if (and (not (zerop (car state)))
               (not (eobp)))
          (progn
            (parse-partial-sexp (point) (point-max) 0 nil state)
            (forward-line 1))))))

(defun ala-statement-opens-block-p ()
  "Return t iff the current statement opens a block.
I.e., iff it ends with a colon that is not in a comment.  Point should
be at the start of a statement."
  (save-excursion
    (let ((start (point))
          (finish (progn (ala-goto-beyond-final-line) (1- (point))))
          (searching t)
          (answer nil)
          state)
      (goto-char start)
      (while searching
        ;; look for a colon with nothing after it except whitespace, and
        ;; maybe a comment
        (if (re-search-forward ":\\([ \t]\\|\\\\\n\\)*\\(#.*\\)?$"
                               finish t)
            (if (eq (point) finish)     ; note: no `else' clause; just
                                        ; keep searching if we're not at
                                        ; the end yet
                ;; sure looks like it opens a block -- but it might
                ;; be in a comment
                (progn
                  (setq searching nil)  ; search is done either way
                  (setq state (parse-partial-sexp start
                                                  (match-beginning 0)))
                  (setq answer (not (nth 4 state)))))
          ;; search failed: couldn't find another interesting colon
          (setq searching nil)))
      answer)))

(defun ala-statement-closes-block-p ()
  "Return t iff the current statement closes a block.
I.e., if the line starts with `return', `raise', `break', `continue',
and `pass'.  This doesn't catch embedded statements."
  (let ((here (point)))
    (ala-goto-initial-line)
    (back-to-indentation)
    (prog1
        (looking-at (concat ala-block-closing-keywords-re "\\>"))
      (goto-char here))))

(defun ala-goto-beyond-block ()
  "Go to point just beyond the final line of block begun by the current line.
This is the same as where `ala-goto-beyond-final-line' goes unless
we're on colon line, in which case we go to the end of the block.
Assumes point is at the beginning of the line."
  (if (ala-statement-opens-block-p)
      (ala-mark-block nil 'just-move)
    (ala-goto-beyond-final-line)))

(defun ala-goto-statement-at-or-above ()
  "Go to the start of the first statement at or preceding point.
Return t if there is such a statement, otherwise nil.  `Statement'
does not include blank lines, comments, or continuation lines."
  (ala-goto-initial-line)
  (if (looking-at ala-blank-or-comment-re)
      ;; skip back over blank & comment lines
      ;; note:  will skip a blank or comment line that happens to be
      ;; a continuation line too
      (if (re-search-backward "^[ \t]*[^ \t#\n]" nil t)
          (progn (ala-goto-initial-line) t)
        nil)
    t))

(defun ala-goto-statement-below ()
  "Go to start of the first statement following the statement containing point.
Return t if there is such a statement, otherwise nil.  `Statement'
does not include blank lines, comments, or continuation lines."
  (beginning-of-line)
  (let ((start (point)))
    (ala-goto-beyond-final-line)
    (while (and
            (or (looking-at ala-blank-or-comment-re)
                (ala-in-literal))
            (not (eobp)))
      (forward-line 1))
    (if (eobp)
        (progn (goto-char start) nil)
      t)))

(defun ala-go-up-tree-to-keyword (key)
  "Go to begining of statement starting with KEY, at or preceding point.

KEY is a regular expression describing a Alamatic keyword.  Skip blank
lines and non-indenting comments.  If the statement found starts with
KEY, then stop, otherwise go back to first enclosing block starting
with KEY.  If successful, leave point at the start of the KEY line and
return t.  Otherwise, leave point at an undefined place and return nil."
  ;; skip blanks and non-indenting #
  (ala-goto-initial-line)
  (while (and
          (looking-at "[ \t]*\\($\\|#[^ \t\n]\\)")
          (zerop (forward-line -1)))    ; go back
    nil)
  (ala-goto-initial-line)
  (let* ((re (concat "[ \t]*" key "\\>"))
         (case-fold-search nil)         ; let* so looking-at sees this
         (found (looking-at re))
         (dead nil))
    (while (not (or found dead))
      (condition-case nil               ; in case no enclosing block
          (ala-goto-block-up 'no-mark)
        (error (setq dead t)))
      (or dead (setq found (looking-at re))))
    (beginning-of-line)
    found))

(defun ala-suck-up-leading-text ()
  "Return string in buffer from start of indentation to end of line.
Prefix with \"...\" if leading whitespace was skipped."
  (save-excursion
    (back-to-indentation)
    (concat
     (if (bolp) "" "...")
     (buffer-substring (point) (progn (end-of-line) (point))))))

(defun ala-suck-up-first-keyword ()
  "Return first keyword on the line as a Lisp symbol.
`Keyword' is defined (essentially) as the regular expression
([a-z]+).  Returns nil if none was found."
  (let ((case-fold-search nil))
    (if (looking-at "[ \t]*\\([a-z]+\\)\\>")
        (intern (buffer-substring (match-beginning 1) (match-end 1)))
      nil)))

(defun ala-current-defun ()
  "Alamatic value for `add-log-current-defun-function'.
This tells add-log.el how to find the current function/method/variable."
  (save-excursion

    ;; Move back to start of the current statement.

    (ala-goto-initial-line)
    (back-to-indentation)
    (while (and (or (looking-at ala-blank-or-comment-re)
                    (ala-in-literal))
                (not (bobp)))
      (backward-to-indentation 1))
    (ala-goto-initial-line)

    (let ((scopes "")
          (sep "")
          dead assignment)

      ;; Check for an assignment.  If this assignment exists inside a
      ;; def, it will be overwritten inside the while loop.  If it
      ;; exists at top lever or inside a class, it will be preserved.

      (when (looking-at "[ \t]*\\([a-zA-Z0-9_]+\\)[ \t]*=")
        (setq scopes (buffer-substring (match-beginning 1) (match-end 1)))
        (setq assignment t)
        (setq sep "."))

      ;; Prepend the name of each outer socpe (def or class).

      (while (not dead)
        (if (and (ala-go-up-tree-to-keyword "\\(class\\|def\\)")
                 (looking-at
                  "[ \t]*\\(class\\|def\\)[ \t]*\\([a-zA-Z0-9_]+\\)[ \t]*"))
            (let ((name (buffer-substring (match-beginning 2) (match-end 2))))
              (if (and assignment (looking-at "[ \t]*def"))
                  (setq scopes name)
                (setq scopes (concat name sep scopes))
                (setq sep "."))))
        (setq assignment nil)
        (condition-case nil             ; Terminate nicely at top level.
            (ala-goto-block-up 'no-mark)
          (error (setq dead t))))
      (if (string= scopes "")
          nil
        scopes))))



(defconst ala-help-address "alamatic-mode@alamatic.org"
  "Address accepting submission of bug reports.")

(defun ala-version ()
  "Echo the current version of `alamatic-mode' in the minibuffer."
  (interactive)
  (message "Using `alamatic-mode' version %s" ala-version)
  (ala-keep-region-active))

;; only works under Emacs 19
;(eval-when-compile
;  (require 'reporter))

(defun ala-submit-bug-report (enhancement-p)
  "Submit via mail a bug report on `alamatic-mode'.
With \\[universal-argument] (programmatically, argument ENHANCEMENT-P
non-nil) just submit an enhancement request."
  (interactive
   (list (not (y-or-n-p
               "Is this a bug report (hit `n' to send other comments)? "))))
  (let ((reporter-prompt-for-summary-p (if enhancement-p
                                           "(Very) brief summary: "
                                         t)))
    (require 'reporter)
    (reporter-submit-bug-report
     ala-help-address                    ;address
     (concat "alamatic-mode " ala-version) ;pkgname
     ;; varlist
     (if enhancement-p nil
       '(ala-alamatic-command
         ala-indent-offset
         ala-block-comment-prefix
         ala-temp-directory
         ala-beep-if-tab-change))
     nil                                ;pre-hooks
     nil                                ;post-hooks
     "Dear Barry,")                     ;salutation
    (if enhancement-p nil
      (set-mark (point))
      (insert
"Please replace this text with a sufficiently large code sample\n\
and an exact recipe so that I can reproduce your problem.  Failure\n\
to do so may mean a greater delay in fixing your bug.\n\n")
      (exchange-point-and-mark)
      (ala-keep-region-active))))


(defun ala-kill-emacs-hook ()
  "Delete files in `ala-file-queue'.
These are Alamatic temporary files awaiting execution."
  (mapc #'(lambda (filename)
            (ala-safe (delete-file filename)))
        ala-file-queue))

;; arrange to kill temp files when Emacs exists
(add-hook 'kill-emacs-hook 'ala-kill-emacs-hook)
(add-hook 'comint-output-filter-functions 'ala-pdbtrack-track-stack-file)

;; Add a designator to the minor mode strings
(or (assq 'ala-pdbtrack-is-tracking-p minor-mode-alist)
    (push '(ala-pdbtrack-is-tracking-p ala-pdbtrack-minor-mode-string)
          minor-mode-alist))



;;; paragraph and string filling code from Bernhard Herzog
;;; see http://mail.alamatic.org/pipermail/alamatic-list/2002-May/103189.html

(defun ala-fill-comment (&optional justify)
  "Fill the comment paragraph around point"
  (let (;; Non-nil if the current line contains a comment.
        has-comment

        ;; If has-comment, the appropriate fill-prefix for the comment.
        comment-fill-prefix)

    ;; Figure out what kind of comment we are looking at.
    (save-excursion
      (beginning-of-line)
      (cond
       ;; A line with nothing but a comment on it?
       ((looking-at "[ \t]*#[# \t]*")
        (setq has-comment t
              comment-fill-prefix (buffer-substring (match-beginning 0)
                                                    (match-end 0))))

       ;; A line with some code, followed by a comment? Remember that the hash
       ;; which starts the comment shouldn't be part of a string or character.
       ((progn
          (while (not (looking-at "#\\|$"))
            (skip-chars-forward "^#\n\"'\\")
            (cond
             ((eq (char-after (point)) ?\\) (forward-char 2))
             ((memq (char-after (point)) '(?\" ?')) (forward-sexp 1))))
          (looking-at "#+[\t ]*"))
        (setq has-comment t)
        (setq comment-fill-prefix
              (concat (make-string (current-column) ? )
                      (buffer-substring (match-beginning 0) (match-end 0)))))))

    (if (not has-comment)
        (fill-paragraph justify)

      ;; Narrow to include only the comment, and then fill the region.
      (save-restriction
        (narrow-to-region

         ;; Find the first line we should include in the region to fill.
         (save-excursion
           (while (and (zerop (forward-line -1))
                       (looking-at "^[ \t]*#")))

           ;; We may have gone to far.  Go forward again.
           (or (looking-at "^[ \t]*#")
               (forward-line 1))
           (point))

         ;; Find the beginning of the first line past the region to fill.
         (save-excursion
           (while (progn (forward-line 1)
                         (looking-at "^[ \t]*#")))
           (point)))

        ;; Lines with only hashes on them can be paragraph boundaries.
        (let ((paragraph-start (concat paragraph-start "\\|[ \t#]*$"))
              (paragraph-separate (concat paragraph-separate "\\|[ \t#]*$"))
              (fill-prefix comment-fill-prefix))
          ;;(message "paragraph-start %S paragraph-separate %S"
          ;;paragraph-start paragraph-separate)
          (fill-paragraph justify))))
    t))


(defun ala-fill-string (start &optional justify)
  "Fill the paragraph around (point) in the string starting at start"
  ;; basic strategy: narrow to the string and call the default
  ;; implementation
  (let (;; the start of the string's contents
        string-start
        ;; the end of the string's contents
        string-end
        ;; length of the string's delimiter
        delim-length
        ;; The string delimiter
        delim
        )

    (save-excursion
      (goto-char start)
      (if (looking-at "\\('''\\|\"\"\"\\|'\\|\"\\)\\\\?\n?")
          (setq string-start (match-end 0)
                delim-length (- (match-end 1) (match-beginning 1))
                delim (buffer-substring-no-properties (match-beginning 1)
                                                      (match-end 1)))
        (error "The parameter start is not the beginning of a alamatic string"))

      ;; if the string is the first token on a line and doesn't start with
      ;; a newline, fill as if the string starts at the beginning of the
      ;; line. this helps with one line docstrings
      (save-excursion
        (beginning-of-line)
        (and (/= (char-before string-start) ?\n)
             (looking-at (concat "[ \t]*" delim))
             (setq string-start (point))))

      (forward-sexp (if (= delim-length 3) 2 1))

      ;; with both triple quoted strings and single/double quoted strings
      ;; we're now directly behind the first char of the end delimiter
      ;; (this doesn't work correctly when the triple quoted string
      ;; contains the quote mark itself). The end of the string's contents
      ;; is one less than point
      (setq string-end (1- (point))))

    ;; Narrow to the string's contents and fill the current paragraph
    (save-restriction
      (narrow-to-region string-start string-end)
      (let ((ends-with-newline (= (char-before (point-max)) ?\n)))
        (fill-paragraph justify)
        (if (and (not ends-with-newline)
                 (= (char-before (point-max)) ?\n))
            ;; the default fill-paragraph implementation has inserted a
            ;; newline at the end. Remove it again.
            (save-excursion
              (goto-char (point-max))
              (delete-char -1)))))

    ;; return t to indicate that we've done our work
    t))

(defun ala-fill-paragraph (&optional justify)
  "Like \\[fill-paragraph], but handle Alamatic comments and strings.
If any of the current line is a comment, fill the comment or the
paragraph of it that point is in, preserving the comment's indentation
and initial `#'s.
If point is inside a string, narrow to that string and fill.
"
  (interactive "P")
  ;; fill-paragraph will narrow incorrectly
  (save-restriction
    (widen)
    (let* ((bod (ala-point 'bod))
           (pps (parse-partial-sexp bod (point))))
      (cond
       ;; are we inside a comment or on a line with only whitespace before
       ;; the comment start?
       ((or (nth 4 pps)
            (save-excursion (beginning-of-line) (looking-at "[ \t]*#")))
        (ala-fill-comment justify))
       ;; are we inside a string?
       ((nth 3 pps)
        (ala-fill-string (nth 8 pps)))
       ;; are we at the opening quote of a string, or in the indentation?
       ((save-excursion
          (forward-word 1)
          (eq (ala-in-literal) 'string))
        (save-excursion
          (ala-fill-string (ala-point 'boi))))
       ;; are we at or after the closing quote of a string?
       ((save-excursion
          (backward-word 1)
          (eq (ala-in-literal) 'string))
        (save-excursion
          (ala-fill-string (ala-point 'boi))))
       ;; otherwise use the default
       (t
        (fill-paragraph justify))))))



(provide 'alamatic-mode)
;;; alamatic-mode.el ends here
