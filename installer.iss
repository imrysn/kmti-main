; Inno Setup Script for KMTI System
[Setup]
AppName=KMTI File Management System
AppVersion=1.0
DefaultDirName={pf}\KMTI
DefaultGroupName=KMTI
OutputDir=dist\installer
OutputBaseFilename=KMTI-Setup
Compression=lzma
SolidCompression=yes
SetupIconFile=assets\fms-icon.ico

[Files]
; Main executable
Source: "dist\KMTI-System.exe"; DestDir: "{app}"; Flags: ignoreversion

; Local data folder
Source: "data\*"; DestDir: "{app}\data"; Flags: recursesubdirs createallsubdirs ignoreversion

; Assets (logos, icons, etc.)
Source: "assets\*"; DestDir: "{app}\assets"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
; Start Menu shortcut
Name: "{group}\KMTI System"; Filename: "{app}\KMTI-System.exe"; IconFilename: "assets\fms-icon.ico"
; Desktop shortcut
Name: "{commondesktop}\KMTI System"; Filename: "{app}\KMTI-System.exe"; IconFilename: "assets\fms-icon.ico"

[Run]
; Auto-run after installation
Filename: "{app}\KMTI-System.exe"; Description: "Launch KMTI System"; Flags: nowait postinstall skipifsilent
