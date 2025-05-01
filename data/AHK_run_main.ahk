^l::
IfWinActive ahk_exe Code.exe
{
    ; Step 1: Open new terminal
    ToolTip, Opening new terminal...
    Send, ^+'  ; Ctrl + Shift + `
    Sleep, 400
    ToolTip

    ; Step 2: Run Python command
    ToolTip, Running main.py...
    Send, python src/main.py{Enter}
    Sleep, 300
    ToolTip
}
return

