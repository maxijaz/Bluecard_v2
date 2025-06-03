^l::
IfWinActive ahk_exe Code.exe
{
    ; Step 1: Kill all terminals
    ToolTip, Killing all terminals...
    Send, ^+p
    Sleep, 300
    Send, >Terminal: Kill All Terminals
    Sleep, 500
    Send, {Enter}
    Sleep, 800
    ToolTip

    ; Step 2: Open new terminal via Command Palette
    ToolTip, Opening terminal...
    Send, ^+p
    Sleep, 300
    Send, >Terminal: Create New Terminal
    Sleep, 500
    Send, {Enter}
    Sleep, 1200
    ToolTip

    ; Step 3: Run main.py
    ToolTip, Running main.py...
    Send, python src/main.py{Enter}
    Sleep, 300
    ToolTip
}
return
