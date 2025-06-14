#SingleInstance force

; --------------------------------------------------------------------------------------

^l::
{
    Run, %ComSpec% /c ""C:\Temp\Bluecard_v2\data\ahk_run_bluecard.bat"", , Hide
    
    ; Get screen dimensions
    SysGet, ScreenWidth, 78
    SysGet, ScreenHeight, 79
    
    ; Set tooltip text size estimate (approximate width/height)
    textWidth := 150
    textHeight := 30
    
    ; Calculate centered position
    x := (ScreenWidth // 2) - (textWidth // 2)
    y := (ScreenHeight // 2) - (textHeight // 2)
    
    ToolTip, Bluecard restarted ( Ctrl + k / Ctrl + l ) , %x%, %y%
    SetTimer, RemoveToolTip, -2000
}
return

; --------------------------------------------------------------------------------------


^k::
{
   
    SendInput, & C:/Users/Spencer/AppData/Local/Programs/Python/Python313/python.exe c:/Temp/Bluecard_v2/src/main.py
    SendInput, {Enter}
    
    ; Get screen dimensions
    SysGet, ScreenWidth, 78
    SysGet, ScreenHeight, 79
    
    ; Set tooltip text size estimate (approximate width/height)
    textWidth := 150
    textHeight := 30
    
    ; Calculate centered position
    x := (ScreenWidth // 2) - (textWidth // 2)
    y := (ScreenHeight // 2) - (textHeight // 2)
    
    ToolTip, Run Terminal... ( Ctrl + k / Ctrl + l ), %x%, %y%
    SetTimer, RemoveToolTip, -2000
}
return

; --------------------------------------------------------------------------------------

RemoveToolTip:
    ToolTip
return








